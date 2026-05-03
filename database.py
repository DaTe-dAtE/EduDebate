import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "arguments.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS debats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            niveau TEXT,
            statut TEXT DEFAULT 'ouvert'
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS arguments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texte TEXT NOT NULL,
            relation INTEGER,
            role TEXT NOT NULL,
            debat_id INTEGER NOT NULL,
            parent_id INTEGER,
            auteur TEXT DEFAULT 'Anonyme',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debat_id) REFERENCES debats(id),
            FOREIGN KEY (parent_id) REFERENCES arguments(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            argument_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            valeur INTEGER NOT NULL,
            FOREIGN KEY (argument_id) REFERENCES arguments(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(argument_id, user_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            statut TEXT NOT NULL
        )
        """)
        conn.commit()

def ajouter_debat(question, niveau=None):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO debats (question, niveau) VALUES (?, ?)", (question, niveau))
        conn.commit()
        return cursor.lastrowid

def recuperer_debats():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM debats")
        return cursor.fetchall()

def recuperer_debat(debat_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM debats WHERE id = ?", (debat_id,))
        return cursor.fetchone()

def clore_debat(debat_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE debats SET statut = 'clos' WHERE id = ?", (debat_id,))
        conn.commit()

def date_dernier_argument(debat_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date_creation FROM arguments WHERE debat_id = ? ORDER BY date_creation DESC LIMIT 1", (debat_id,))
        res = cursor.fetchone()
        return res[0] if res else None

def ajouter_argument(texte, relation, role, debat_id, parent_id=None, auteur="Anonyme"):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO arguments (texte, relation, role, debat_id, parent_id, auteur)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (texte, relation, role, debat_id, parent_id, auteur))
        conn.commit()

def recuperer_arguments(debat_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.texte, a.relation, a.role, a.debat_id, a.parent_id, IFNULL(SUM(v.valeur), 0) as score, a.auteur
            FROM arguments a
            LEFT JOIN votes v ON a.id = v.argument_id
            WHERE a.debat_id = ?
            GROUP BY a.id
        """, (debat_id,))
        return cursor.fetchall()

def ajouter_vote(argument_id, user_id, valeur):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM votes WHERE argument_id = ? AND user_id = ?", (argument_id, user_id))
        vote_existant = cursor.fetchone()
        
        if vote_existant:
            cursor.execute("UPDATE votes SET valeur = ? WHERE id = ?", (valeur, vote_existant[0]))
        else:
            cursor.execute("INSERT INTO votes (argument_id, user_id, valeur) VALUES (?, ?, ?)", (argument_id, user_id, valeur))
        conn.commit()

def creer_utilisateur(username, password, statut):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password, statut) VALUES (?, ?, ?)", (username, hashed_pw, statut))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def verifier_utilisateur(username, password):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            return user
        return None