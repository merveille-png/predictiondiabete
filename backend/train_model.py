"""
Entraîne un modèle de régression logistique pour estimer le risque de diabète,
à partir du Pima Indians Diabetes Dataset.

Usage :
    python train_model.py

Produit :
    model.joblib  -> le modèle entraîné, prêt à être chargé par l'API (app.py)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, recall_score
import joblib

DATA_PATH = "pima-indians-diabetes.csv"
MODEL_PATH = "model.joblib"

# Colonnes où un 0 signifie en réalité "donnée manquante" (voir le cahier des charges)
ZERO_AS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df[ZERO_AS_MISSING] = df[ZERO_AS_MISSING].replace(0, np.nan)
    return df


def main():
    df = load_data()
    X = df.drop(columns=["Outcome"])
    y = df["Outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline : imputation des valeurs manquantes -> standardisation -> régression logistique
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("=== Évaluation du modèle ===")
    print(classification_report(y_test, y_pred, target_names=["Non diabétique", "Diabétique"]))
    print(f"Sensibilité (recall diabétiques) : {recall_score(y_test, y_pred):.2f}")
    print("-> La sensibilité est la métrique prioritaire : elle mesure la part des")
    print("   vrais diabétiques correctement détectés par le modèle.")

    joblib.dump({"model": model, "columns": list(X.columns)}, MODEL_PATH)
    print(f"\nModèle sauvegardé dans {MODEL_PATH}")


if __name__ == "__main__":
    main()
