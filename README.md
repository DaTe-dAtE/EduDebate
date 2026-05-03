# 🎓 EduDebate - Plateforme de Débat et d'Aide à la Décision

**Projet Universitaire - L2 Informatique**
**Groupe 5 :** Garv, Rayan, Stephane, Alassane, Yanis.

---

## 📝 Description du Projet
EduDebate est une application web développée en Python (Flask) permettant de structurer des débats en ligne sous forme de graphes d'argumentation bipolaires (Mind Maps). 

L'objectif principal du projet n'est pas seulement de collecter des opinions, mais de fournir un **outil d'aide à la décision**. Pour cela, la plateforme intègre un algorithme de sémantique graduelle qui évalue mathématiquement la force de chaque argument pour déterminer l'issue du débat de manière impartiale.

## ✨ Fonctionnalités Principales

### 👤 Gestion des Utilisateurs et Sécurité
* **Rôles :** Inscription en tant qu'Étudiant ou Professeur.
* **Sécurité :** Hachage des mots de passe via `werkzeug.security` (scrypt) et gestion sécurisée des sessions.
* **Profils Dynamiques :** API interne (`/api/user_info/`) permettant d'afficher une carte de profil au survol (Hover Card) avec les statistiques en temps réel de l'utilisateur (rôle, nombre de likes reçus, nombre d'arguments postés).

### 🌳 Arbre d'Argumentation (Mind Map)
* **Structure hiérarchique :** Ajout d'arguments de "Soutien" ou d' "Attaque" rattachés à un nœud parent spécifique ou directement à la racine du débat.
* **Interface dynamique :** Génération de l'arbre en JavaScript (DOM manipulation) basé sur les données structurées par Jinja2. Modale de réponse intégrée pour une meilleure ergonomie.
* **Système de Votes :** Évaluation des arguments par la communauté (+1, 0, -1), modifiant le poids initial de l'argument dans le graphe.

### ⚙️ Moteur Algorithmique & Délibération
* **Argumentation Computationnelle :** Implémentation d'une fonction de catégorisation pondérée bipolaire (inspirée des modèles de Besnard & Hunter). Le système évalue récursivement la "force" de chaque argument en fonction de son poids (votes) et des attaques/soutiens qu'il subit.
* **Clôture Automatique (Lazy Evaluation) :** Un débat se ferme automatiquement après 3 heures d'inactivité (absence de nouveaux arguments). Cette vérification est faite de manière paresseuse au chargement de la page pour économiser les ressources serveur.
* **Lutte contre le Biais de Conformité :** Les scores algorithmiques et le verdict final sont strictement masqués tant que le débat est "en cours" pour ne pas influencer les votants. Ils sont révélés à la clôture.

### 🌱 Éco-conception & Tests
* **Mesure de l'Empreinte Carbone :** Intégration d'un pipeline de test avec `pytest` et `codecarbon` pour profiler la consommation énergétique (CPU, RAM, GPU) de l'algorithme récursif d'évaluation, générant un rapport `emissions.csv`.

---

## 🛠️ Technologies Utilisées
* **Backend :** Python 3, Flask
* **Base de données :** SQLite3 (requêtes paramétrées anti-injections SQL)
* **Frontend :** HTML5, CSS3 (Flexbox), JavaScript (Vanilla)
* **Tests & Éco-conception :** Pytest, CodeCarbon

---

## 🚀 Installation et Lancement

### 1. Cloner le dépôt
```bash
git clone [https://gitlabsu.sorbonne-universite.fr/lu2in013/fev2026/gr3/groupe-5.git](https://gitlabsu.sorbonne-universite.fr/lu2in013/fev2026/gr3/groupe-5.git)
cd groupe-5
```

### 2. Installer les dépendances
Assurez-vous d'avoir Python installé, puis exécutez :
```bash
pip install flask werkzeug pytest codecarbon pandas
```

### 3. Lancer l'application
*(Note : Si une ancienne version de la base de données est présente, supprimez le fichier `arguments.db` avant de lancer le serveur pour garantir la création du nouveau schéma).*

```bash
python app.py
```
Le serveur démarrera sur `http://127.0.0.1:5000/`.

---

## 🧪 Tests et Profiling Carbone

Pour exécuter le test d'intégration de l'algorithme et générer le rapport d'émissions carbone :
```bash
pytest test_app.py
```
Un fichier `emissions.csv` sera généré à la racine du projet, contenant les données de consommation énergétique (en kWh) et l'équivalent CO2 de l'exécution algorithmique.

---

## 📂 Structure du Projet
```text
groupe-5/
├── app.py                 # Serveur Flask, routes web et algorithme récursif
├── database.py            # Fonctions d'interaction avec SQLite3
├── test_app.py            # Tests d'intégration et profiling CodeCarbon
├── requirements.txt       # Dépendances du projet
├── static/
│   └── style.css          # Feuille de style principale
└── templates/
    ├── create.html        # Page d'inscription
    ├── login.html         # Page de connexion
    ├── index.html         # Accueil et liste des débats
    └── debat.html         # Interface principale de la Mind Map et de la délibération
```