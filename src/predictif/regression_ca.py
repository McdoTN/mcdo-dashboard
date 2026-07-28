"""
src/predictif/regression_ca.py

Amorce d'analyse prédictive : régression linéaire simple du chiffre
d'affaires (CA) en fonction du temps, à partir des données du pôle
Business. Sert de base à la section 3.2 du mémoire.

Limite assumée : le faible nombre de mois disponibles restreint la
robustesse statistique de cette régression. Elle sert avant tout à
illustrer la démarche, pas à produire une prévision fiable.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.kpi.business import charger_donnees_business


def calculer_regression_ca(df: pd.DataFrame = None) -> dict:
    if df is None:
        df = charger_donnees_business()

    df = df.sort_values("Mois").reset_index(drop=True)

    # Forcer la conversion numerique et reperer les valeurs manquantes/invalides
    df["CA"] = pd.to_numeric(df["CA"], errors="coerce")
    lignes_invalides = df[df["CA"].isna()]
    if not lignes_invalides.empty:
        print("Mois avec un CA manquant ou invalide, exclus de la regression :")
        print(lignes_invalides[["Mois", "CA"]])
        df = df.dropna(subset=["CA"]).reset_index(drop=True)

    x = np.arange(len(df))
    y = df["CA"].values.astype(float)

    pente, ordonnee_origine = np.polyfit(x, y, deg=1)
    ca_predit = pente * x + ordonnee_origine

    ss_res = np.sum((y - ca_predit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    return {
        "pente": pente,
        "ordonnee_origine": ordonnee_origine,
        "r2": r2,
        "mois": df["Mois"].tolist(),
        "ca_observe": y.tolist(),
        "ca_predit": ca_predit.tolist(),
    }


def tracer_regression_ca(resultat: dict, chemin_sortie: str = "fig08_regression_ca.png"):
    plt.figure(figsize=(8, 5))
    plt.plot(resultat["mois"], resultat["ca_observe"], "o-", label="CA observé")
    plt.plot(resultat["mois"], resultat["ca_predit"], "--", label="Régression linéaire")
    plt.xticks(rotation=45)
    plt.ylabel("Chiffre d'affaires (€)")
    plt.title("Évolution du CA et régression linéaire")
    plt.legend()
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=200)
    print(f"Graphique enregistré : {chemin_sortie}")


if __name__ == "__main__":
    resultat = calculer_regression_ca()
    print(f"Pente : {resultat['pente']:.2f} €/mois")
    print(f"Ordonnée à l'origine : {resultat['ordonnee_origine']:.2f} €")
    print(f"R² : {resultat['r2']:.3f}")
    tracer_regression_ca(resultat)