"""
Application web de dépistage du diabète.

FastAPI sert à la fois l'API et l'interface (frontend/) : tout tourne
sur une seule adresse, pas besoin d'ouvrir un fichier HTML séparément.

Endpoint principal :
    POST /api/evaluer-risque

Pour démarrer :
    uvicorn app:app --reload
Puis ouvrir : http://127.0.0.1:8000/ pour utiliser l'application,
ou http://127.0.0.1:8000/docs pour tester l'API directement (Swagger).

Le modèle doit avoir été entraîné au préalable avec train_model.py
(fichier attendu : model.joblib, dans le même dossier).
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Tuple
import pandas as pd
import joblib
import os

from auth import (
    CLE_SECRETE_SESSION,
    SUPERUSER_NOM_UTILISATEUR,
    exiger_connexion,
    verifier_identifiants,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI(title="API de dépistage du diabète")

# Conservé pour permettre les appels depuis une autre origine si besoin
# (ex : tests, ou frontend hébergé ailleurs).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session de connexion (cookie signé, voir auth.py pour les identifiants).
# max_age de 30 jours : la session survit à la fermeture du navigateur,
# pour aller avec la case "Se souvenir de moi" du formulaire de connexion.
app.add_middleware(
    SessionMiddleware,
    secret_key=CLE_SECRETE_SESSION,
    session_cookie="diacheck_session",
    same_site="lax",
    max_age=60 * 60 * 24 * 30,
)

app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

_bundle = None


def get_model():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                "Modèle introuvable. Lance d'abord : python train_model.py"
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


class DonneesPatient(BaseModel):
    """Champs alignés avec le Module 3 du cahier des charges."""
    age: int = Field(..., ge=0, le=120)
    grossesses: int = Field(0, ge=0, description="Nombre de grossesses")
    glycemie: Optional[float] = Field(None, description="Glycémie (mg/dL)")
    tension_systolique: Optional[float] = Field(None, description="Tension artérielle systolique (mm Hg)")
    epaisseur_peau: Optional[float] = Field(None, description="Épaisseur du pli cutané (mm)")
    insuline: Optional[float] = Field(None, description="Insuline sérique (mu U/mL)")
    imc: Optional[float] = Field(None, description="Indice de masse corporelle")
    antecedents_familiaux: float = Field(
        0.2, description="Score d'hérédité du diabète (0 = aucun antécédent connu, plus haut = antécédents marqués)"
    )


class ResultatRisque(BaseModel):
    risque_pourcentage: float
    categorie: str
    recommandation: str


def categoriser(risque: float) -> Tuple[str, str]:
    if risque < 30:
        return "faible", "Aucune action urgente ; un suivi de routine reste recommandé."
    if risque < 60:
        return "modéré", "Consulter un professionnel de santé pour un bilan complémentaire."
    return "élevé", "Consulter un professionnel de santé dès que possible."


class Identifiants(BaseModel):
    nom_utilisateur: str
    mot_de_passe: str


@app.get("/")
def accueil(request: Request):
    if not request.session.get("connecte"):
        return RedirectResponse("/connexion")
    # no-cache : évite qu'un ancien design reste affiché après une mise à jour
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/connexion")
def page_connexion():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "connexion.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.post("/api/connexion")
def connexion(identifiants: Identifiants, request: Request):
    if not verifier_identifiants(identifiants.nom_utilisateur, identifiants.mot_de_passe):
        raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect.")
    request.session["connecte"] = True
    request.session["utilisateur"] = identifiants.nom_utilisateur
    return {"message": "Connexion réussie."}


@app.post("/api/deconnexion")
def deconnexion(request: Request):
    request.session.clear()
    return {"message": "Déconnecté."}


@app.get("/api/moi")
def moi(request: Request):
    if not request.session.get("connecte"):
        return {"connecte": False}
    return {"connecte": True, "utilisateur": request.session.get("utilisateur", SUPERUSER_NOM_UTILISATEUR)}


@app.get("/api/sante")
def sante():
    return {"message": "API de dépistage du diabète en fonctionnement."}


@app.post("/api/evaluer-risque", response_model=ResultatRisque, dependencies=[Depends(exiger_connexion)])
def evaluer_risque(donnees: DonneesPatient):
    bundle = get_model()
    model = bundle["model"]
    columns = bundle["columns"]

    ligne = {
        "Pregnancies": donnees.grossesses,
        "Glucose": donnees.glycemie,
        "BloodPressure": donnees.tension_systolique,
        "SkinThickness": donnees.epaisseur_peau,
        "Insulin": donnees.insuline,
        "BMI": donnees.imc,
        "DiabetesPedigreeFunction": donnees.antecedents_familiaux,
        "Age": donnees.age,
    }

    X = pd.DataFrame([ligne])[columns]

    try:
        proba = model.predict_proba(X)[0][1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du modèle : {e}")

    risque_pourcentage = round(proba * 100, 1)
    categorie, recommandation = categoriser(risque_pourcentage)

    return ResultatRisque(
        risque_pourcentage=risque_pourcentage,
        categorie=categorie,
        recommandation=recommandation,
    )
