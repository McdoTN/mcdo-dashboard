"""
src/kpi/business.py

Calcul des KPI du pôle Business à partir des données DATA_Business,
avec attribution d'un statut (vert/jaune/rouge/non disponible) selon
les seuils validés avec Arnaud.
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns

# Colonnes du pôle Business qui sont réellement numériques
# (contrairement au pôle Qualité, ici toutes les colonnes hors "Mois" le sont)
COLONNES_NUMERIQUES = [
    "CA", "TAC", "QCR", "Pertes", "Repas employés", "Bulk",
    "Écart de rendement", "Marge P&L", "Marge TH",
    "Taux modif commandes", "Coût de la hub", "Taux de remboursement",
]

# Seuils fixes : {colonne: (sens, seuil_vert)}
# sens "max"  -> vert si valeur <= seuil (ex: Pertes < 0,7%)
# sens "min"  -> vert si valeur >= seuil (ex: Marge P&L > 75%)
SEUILS_FIXES = {
    "QCR": ("max", 20.5),
    "Pertes": ("max", 0.7),
    "Repas employés": ("max", 0.4),
    "Bulk": ("max", 1.5),
    "Écart de rendement": ("max", 0.7),
    "Marge P&L": ("min", 75),
    "Marge TH": ("min", 75),
    "Taux modif commandes": ("max", 10),
    "Coût de la hub": ("max", 4000),
    # TODO : seuils jaune/rouge exacts à clarifier avec Arnaud.
    # En attendant, seul le seuil vert est appliqué (rouge = tout le reste).
    "Taux de remboursement": ("max", 0.02),
}

# KPI qui fonctionnent par comparatif N-1 plutôt que par seuil fixe
COLONNES_COMPARATIF_N1 = ["CA", "TAC"]


def charger_donnees_business() -> pd.DataFrame:
    """
    Charge et nettoie les données du pôle Business : lecture du Sheets
    puis conversion des colonnes numériques (virgule -> point -> float).
    """
    df = load_data_tab("DATA_Business")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def statut_seuil_fixe(valeur, sens: str, seuil_vert: float) -> str:
    """
    Détermine le statut (vert/rouge/non disponible) pour un KPI à seuil fixe.

    Args:
        valeur: valeur du KPI pour le mois considéré (peut être NaN)
        sens: "max" (vert si valeur <= seuil) ou "min" (vert si valeur >= seuil)
        seuil_vert: seuil de référence

    Returns:
        "vert", "rouge", ou "non disponible" si la valeur est manquante
    """
    if pd.isna(valeur):
        return "non disponible"

    if sens == "max":
        return "vert" if valeur <= seuil_vert else "rouge"
    else:  # sens == "min"
        return "vert" if valeur >= seuil_vert else "rouge"


def calculer_comparatif_n1(df: pd.DataFrame, colonne: str, mois_actuel: pd.Timestamp):
    """
    Calcule l'évolution en % d'un KPI entre le mois donné et le même mois
    de l'année précédente (N-1).

    Returns:
        float (évolution en %) ou None si le mois N-1 n'est pas disponible
        dans les données (historique insuffisant, cas normal en début de projet).
    """
    mois_n1 = mois_actuel - pd.DateOffset(years=1)
    ligne_n1 = df[df["Mois"] == mois_n1]

    if ligne_n1.empty:
        return None  # pas encore assez d'historique pour comparer

    valeur_n1 = ligne_n1[colonne].values[0]
    valeur_actuelle = df.loc[df["Mois"] == mois_actuel, colonne].values[0]

    if pd.isna(valeur_n1) or pd.isna(valeur_actuelle) or valeur_n1 == 0:
        return None

    return (valeur_actuelle - valeur_n1) / valeur_n1 * 100


def statut_comparatif_n1(evolution) -> str:
    """
    Détermine le statut pour un KPI en comparatif N-1.

    Règle validée : vert si > 0% vs N-1, jaune si = 0%, rouge si < 0%.
    """
    if evolution is None:
        return "non disponible"
    if evolution > 0:
        return "vert"
    elif evolution == 0:
        return "jaune"
    else:
        return "rouge"


def calculer_kpi_business(df: pd.DataFrame = None) -> dict:
    """
    Calcule l'ensemble des KPI Business pour le mois le plus récent
    disponible dans les données.

    Args:
        df: DataFrame déjà chargé et nettoyé (optionnel). Si non fourni,
            charge et nettoie les données automatiquement.

    Returns:
        dict structuré ainsi :
        {
            "mois": Timestamp du mois courant,
            "kpi": {
                "CA": {"valeur": 25000, "evolution_n1": 3.2, "statut": "vert"},
                "QCR": {"valeur": 19.5, "statut": "vert"},
                ...
            }
        }
    """
    if df is None:
        df = charger_donnees_business()

    mois_actuel = df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    resultats = {}

    # KPI à seuil fixe
    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        valeur = ligne_actuelle[colonne]
        resultats[colonne] = {
            "valeur": valeur,
            "statut": statut_seuil_fixe(valeur, sens, seuil_vert),
        }

    # KPI en comparatif N-1
    for colonne in COLONNES_COMPARATIF_N1:
        evolution = calculer_comparatif_n1(df, colonne, mois_actuel)
        resultats[colonne] = {
            "valeur": ligne_actuelle[colonne],
            "evolution_n1": evolution,
            "statut": statut_comparatif_n1(evolution),
        }

    return {"mois": mois_actuel, "kpi": resultats}