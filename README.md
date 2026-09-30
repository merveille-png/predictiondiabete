# Prototype — Dépistage du diabète

Ce dossier contient le squelette du prototype décrit dans le cahier des charges : Module 3 (collecte des données), Module 4 (calcul du risque / modèle IA), et une interface minimale pour tester le tout.

## Comment démarrer, étape par étape

### 1. Ouvrir le dossier dans VS Code

Ouvre VS Code, puis `Fichier > Ouvrir le dossier...` et sélectionne ce dossier `diabetes-app`.

### 2. Créer un environnement Python (dans le terminal de VS Code)

```bash
cd backend
python -m venv venv
```

Puis active l'environnement :

- **Windows** : `venv\Scripts\activate`
- **Mac/Linux** : `source venv/bin/activate`

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Générer tes identifiants de connexion (Module 2)

```bash
python generer_identifiants.py
```

Ça crée un fichier `backend/.env` (jamais envoyé sur GitHub, voir `.gitignore`) contenant le hash de ton mot de passe et la clé de session. Le mot de passe en clair ne s'affiche **qu'une seule fois**, à l'écran — note-le tout de suite, il n'est stocké nulle part ensuite.

### 5. Entraîner le modèle

```bash
python train_model.py
```

Cela affiche les métriques du modèle (sensibilité, etc.) et crée un fichier `model.joblib` — c'est le "cerveau" entraîné sur le dataset.

### 6. Démarrer l'application

```bash
uvicorn app:app --reload
```

Ouvre ensuite **`http://127.0.0.1:8000/`** dans ton navigateur : tu seras redirigé vers la page de connexion (utilise les identifiants générés à l'étape 4), puis vers l'application complète (formulaire + résultat), servie directement par le serveur. Pas besoin d'ouvrir un fichier HTML séparément.

`http://127.0.0.1:8000/docs` donne l'interface Swagger automatique, pratique pour tester l'API seule sans passer par le formulaire (les routes protégées y demandent quand même une session valide).

## Structure du projet

```
diabetes-app/
├── backend/
│   ├── app.py               <- l'API (Module 4 : calcul du risque) + les routes de connexion
│   ├── auth.py               <- Module 2 : vérification des identifiants, session
│   ├── generer_identifiants.py <- crée backend/.env (mot de passe + clé de session)
│   ├── .env.example          <- modèle du fichier .env (sans secrets)
│   ├── train_model.py       <- entraîne le modèle sur le dataset
│   ├── pima-indians-diabetes.csv
│   └── requirements.txt
├── frontend/
│   ├── index.html           <- interface principale (Module 1), protégée par connexion
│   ├── connexion.html       <- page de connexion (Module 2)
│   └── assets/
│       ├── css/style.css
│       └── js/main.js
├── notebooks/
│   └── pima-indians-diabetes-database.ipynb   <- notebook d'exploration (référence, non utilisé par l'app)
└── README.md
```

## Ce qui manque encore (pour un futur développeur)

Module 2 (authentification) n'a qu'un seul compte superuser (pas de gestion multi-utilisateurs, pas d'inscription, pas d'écran pour changer le mot de passe une fois généré — il faut relancer `generer_identifiants.py`). Module 5 (base de données persistante), Module 6 (tableau de bord) et Module 7 (sécurité avancée) ne sont pas encore implémentés — voir le cahier des charges pour le détail de chacun.

Ce prototype garde le reste en mémoire ; en dehors de la session de connexion, rien n'est encore sauvegardé de façon permanente.
