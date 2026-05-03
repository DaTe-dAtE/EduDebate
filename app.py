from flask import Flask, render_template, request, redirect, session, flash, url_for
from datetime import datetime, timedelta
import sqlite3
from database import (init_db, ajouter_debat, recuperer_debats, recuperer_debat, 
                      ajouter_argument, recuperer_arguments, creer_utilisateur, 
                      verifier_utilisateur, ajouter_vote, clore_debat, date_dernier_argument)

app = Flask(__name__)
app.secret_key = "cle_secrete_super_securisee" 
init_db()

def calculer_acceptabilite(arguments_db):
    arbre = {}
    
    for arg in arguments_db:
        arg_id, relation, parent_id, score_votes = arg[0], arg[2], arg[5], arg[6] or 0
        arbre[arg_id] = {
            "relation": relation,
            "parent_id": parent_id,
            "poids_initial": max(1, 1 + score_votes),
            "enfants": [],
            "force": 0.0
        }

    arbre[0] = {"relation": -1, "parent_id": None, "poids_initial": 1.0, "enfants": [], "force": 0.0}

    for arg_id, data in arbre.items():
        if arg_id != 0:
            parent = data["parent_id"] if data["parent_id"] is not None else 0
            if parent in arbre:
                arbre[parent]["enfants"].append(arg_id)

    def evaluer_noeud(noeud_id):
        noeud = arbre[noeud_id]
        s_soutiens = 0.0
        s_attaques = 0.0

        for enfant_id in noeud["enfants"]:
            f_enfant = evaluer_noeud(enfant_id)
            if arbre[enfant_id]["relation"] == 1:
                s_soutiens += f_enfant
            else:
                s_attaques += f_enfant

        noeud["force"] = (noeud["poids_initial"] + s_soutiens) / (1.0 + s_attaques)
        return noeud["force"]

    evaluer_noeud(0)
    return {arg_id: round(data["force"], 2) for arg_id, data in arbre.items()}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form.get("form_type") == "nouveau_debat":
            q = request.form.get("nouveau_debat")
            n = request.form.get("niveau")
            nid = ajouter_debat(q, n)
            return redirect(f"/debat/{nid}")

    return render_template("index.html", debats=recuperer_debats(), user=session.get("user"))

@app.route("/debat/<int:debat_id>", methods=["GET", "POST"])
def debat(debat_id):
    user = session.get("user") 
    debat_info = recuperer_debat(debat_id)
    
    if not debat_info:
        return "Débat introuvable", 404
        
    statut_debat = debat_info[3] if len(debat_info) > 3 else 'ouvert'

    if statut_debat == 'ouvert':
        try:
            d_msg = date_dernier_argument(debat_id)
            if d_msg:
                d_date = datetime.strptime(d_msg, '%Y-%m-%d %H:%M:%S')
                if datetime.utcnow() - d_date > timedelta(hours=3):
                    clore_debat(debat_id)
                    statut_debat = 'clos'
        except Exception:
            pass

    if request.method == "POST":
        if statut_debat == 'clos':
            flash("Ce débat est clos.")
            return redirect(f"/debat/{debat_id}")
            
        if request.form.get("form_type") == "argument":
            texte = request.form.get("texte")
            relation = int(request.form.get("relation", 0))
            role = "professeur" if user and user["statut"] == "Professeur" else request.form.get("role", "étudiant")
            auteur = user["username"] if user else "Anonyme"
            
            c_id = request.form.get("cible_id")
            parent_id = int(c_id) if c_id and c_id.isdigit() else None
            
            try:
                ajouter_argument(texte, relation, role, debat_id, parent_id, auteur)
            except Exception as e:
                flash(f"Erreur technique (DB à recréer) : {str(e)}")
            
        return redirect(f"/debat/{debat_id}")

    try:
        arguments = recuperer_arguments(debat_id)
        scores_algo = calculer_acceptabilite(arguments)
    except Exception:
        arguments = []
        scores_algo = {0: 0}
        flash("La BDD est obsolète. Supprimez arguments.db.")

    return render_template("debat.html", arguments=arguments, question=debat_info[1], debat_id=debat_id, user=user, scores_algo=scores_algo, statut_debat=statut_debat)

@app.route("/vote/<int:argument_id>", methods=["POST"])
def vote(argument_id):
    user = session.get("user")
    debat_id = request.form.get("debat_id")
    debat_info = recuperer_debat(debat_id)
    statut_debat = debat_info[3] if debat_info and len(debat_info) > 3 else 'ouvert'

    if statut_debat == 'clos':
        flash("Débat clos.")
        return redirect(f"/debat/{debat_id}")
    
    if not user or "id" not in user:
        flash("Connectez-vous pour voter.")
        return redirect(f"/debat/{debat_id}")
        
    val = int(request.form.get("valeur", 0))
    if -2 <= val <= 2:
        ajouter_vote(argument_id, user["id"], val)
        
    return redirect(f"/debat/{debat_id}")

@app.route("/api/user_info/<username>")
def user_info(username):
    try:
        with sqlite3.connect("arguments.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT statut FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            statut = user_row['statut'] if user_row else "Membre"
            
            cursor.execute("""
                SELECT IFNULL(SUM(v.valeur), 0) FROM votes v
                JOIN arguments a ON v.argument_id = a.id WHERE a.auteur = ?
            """, (username,))
            likes_row = cursor.fetchone()
            t_likes = likes_row[0] if likes_row else 0
            
            cursor.execute("SELECT COUNT(*) FROM arguments WHERE auteur = ?", (username,))
            c_row = cursor.fetchone()
            t_comments = c_row[0] if c_row else 0
            
            return {"statut": statut, "likes": t_likes, "comments": t_comments}
    except Exception as e:
        return {"statut": "Erreur", "likes": 0, "comments": 0}, 500

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        un = request.form['username']
        pw = request.form['password']
        st = request.form['statut']
        if creer_utilisateur(un, pw, st):
            flash("Compte créé avec succès !")
            return redirect(url_for('login'))
        else:
            flash("Nom d'utilisateur indisponible.")
    return render_template("create.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        un = request.form['first'] 
        pw = request.form['password']
        u_data = verifier_utilisateur(un, pw)
        if u_data:
            session["user"] = {"id": u_data[0], "username": u_data[1], "statut": u_data[3]}
            return redirect(url_for('index'))
        else:
            flash("Identifiants incorrects.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)