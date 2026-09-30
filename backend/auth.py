"""
Authentification minimale (Module 2 du cahier des charges).

Un seul compte "superuser" pour ce prototype : il n'y a pas encore de
base de données persistante pour gérer plusieurs comptes (voir Module 5).
Le mot de passe n'est jamais stocké en clair, seulement son hash bcrypt.

Les secrets (hash du mot de passe, clé de session) vivent dans le fichier
`.env` local (jamais commité, voir `.gitignore`) et pas dans ce fichier,
pour pouvoir publier le code sur un dépôt public sans rien divulguer.
Voir `.env.example` pour le format, et `generer_identifiants.py` pour
créer/regénérer un mot de passe.
"""

import os
import sys

import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, Request

load_dotenv()

SUPERUSER_NOM_UTILISATEUR = os.environ.get("SUPERUSER_NOM_UTILISATEUR", "admin")
SUPERUSER_MOT_DE_PASSE_HASH = os.environ.get("SUPERUSER_MOT_DE_PASSE_HASH")
CLE_SECRETE_SESSION = os.environ.get("CLE_SECRETE_SESSION")

if not SUPERUSER_MOT_DE_PASSE_HASH or not CLE_SECRETE_SESSION:
    sys.exit(
        "Configuration manquante : SUPERUSER_MOT_DE_PASSE_HASH et CLE_SECRETE_SESSION "
        "doivent être définis dans backend/.env.\n"
        "Lance d'abord : python generer_identifiants.py"
    )


def verifier_identifiants(nom_utilisateur: str, mot_de_passe: str) -> bool:
    if nom_utilisateur != SUPERUSER_NOM_UTILISATEUR:
        return False
    return bcrypt.checkpw(mot_de_passe.encode("utf-8"), SUPERUSER_MOT_DE_PASSE_HASH.encode("utf-8"))


def exiger_connexion(request: Request) -> None:
    """Dépendance FastAPI : lève une 401 si personne n'est connecté."""
    if not request.session.get("connecte"):
        raise HTTPException(status_code=401, detail="Connexion requise.")
