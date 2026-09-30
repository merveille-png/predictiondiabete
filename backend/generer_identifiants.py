"""
Génère (ou régénère) les identifiants superuser et la clé de session,
et les écrit dans backend/.env (jamais commité dans git).

Usage :
    python generer_identifiants.py

Le mot de passe généré n'est affiché qu'une seule fois, à l'écran :
note-le tout de suite, il n'est stocké nulle part en clair ensuite
(seulement son hash bcrypt, dans .env).
"""

import os
import secrets
import string

import bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")


def generer_mot_de_passe(longueur: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(longueur))


def main():
    nom_utilisateur = "admin"
    mot_de_passe = generer_mot_de_passe()
    hash_mdp = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cle_secrete = secrets.token_hex(32)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(f"SUPERUSER_NOM_UTILISATEUR={nom_utilisateur}\n")
        f.write(f"SUPERUSER_MOT_DE_PASSE_HASH={hash_mdp}\n")
        f.write(f"CLE_SECRETE_SESSION={cle_secrete}\n")

    print("=== Identifiants superuser générés ===")
    print(f"Nom d'utilisateur : {nom_utilisateur}")
    print(f"Mot de passe      : {mot_de_passe}")
    print()
    print("Note ce mot de passe maintenant : il n'est écrit nulle part en clair,")
    print(f"seul son hash a été sauvegardé dans {ENV_PATH}")


if __name__ == "__main__":
    main()
