"""
src/kpi/rh.py

Calcul des KPI du pôle RH à partir des données DATA_RH.

Pôle volontairement traité simplement (moins prioritaire pour Arnaud).
Les seuils utilisés ici sont les seuils initiaux fournis par Bastien ;
PAC notamment utilise un seuil provisoire (≤36%) en attendant confirmation
de sa définition exacte avec Arnaud — à ajuster le jour venu, une simple
modification dans SEUILS_FIXES suffira.
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe, statut_tendance, calculer_delta

# Colonnes du pôle RH, toutes numériques (pas de code alphanumérique ici)
# Attention : VPHE est un montant en € (vente par heure employé), pas un %,
# contrairement à MO FDC, MO P&L et Turn-Over qui sont bien des pourcentages.
COLONNES_NUMERIQUES = ["MO FDC", "MO P&L", "VPHE", "PAC", "Turn-Over"]

# Seuils fixes du pôle RH — seuils initiaux fournis par Bastien, à ajuster
# une fois confirmés avec Arnaud (notamment PAC, dont la définition exacte
# reste à valider : en attendant, on applique ≤36% par défaut).
SEUILS_FIXES = {
    "MO FDC": ("max", 9),        # %
    "MO P&L": ("max", 12),       # %
    "VPHE": ("min", 85),         # € par heure employé, pas un %
    "Turn-Over": ("max", 5),     # %
    "PAC": ("max", 36),          # % — seuil provisoire, à confirmer avec Arnaud
}


def charger_donnees_rh() -> pd.DataFrame:
    """
    Charge et nettoie les données du pôle RH : lecture du Sheets puis
    conversion des colonnes numériques (virgule -> point -> float).
    """
    df = load_data_tab("DATA_RH")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def calculer_kpi_rh(df: pd.DataFrame = None, mois: pd.Timestamp = None) -> dict:
    """
    Calcule l'ensemble des KPI RH pour un mois donné (ou, par défaut, pour
    le mois le plus récent disponible — comportement d'origine inchangé).

    Args:
        df: DataFrame source (si None, rechargé automatiquement)
        mois: mois à calculer (ex: valeur issue du sélecteur de mois de la
            page) ; si None, utilise le mois le plus récent disponible

    Returns:
        dict structuré ainsi :
        {
            "mois": Timestamp du mois calculé,
            "kpi": {
                "MO FDC": {"valeur": 8.7, "statut": "vert",
                           "valeur_n1": None, "delta_n1_points": None,
                           "tendance_n1": "non disponible"},
                "PAC": {"valeur": 34.1, "statut": "vert", ...},
                # même structure pour tous les KPI, y compris PAC
                # (seuil provisoire ≤36%, à confirmer avec Arnaud)
                ...
            }
        }
    """
    if df is None:
        df = charger_donnees_rh()

    mois_actuel = mois if mois is not None else df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    resultats = {}

    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        valeur = ligne_actuelle[colonne]
        delta = calculer_delta(df, colonne, mois_actuel, pd.DateOffset(years=1))
        delta_points = delta["delta_points"] if delta else None
        resultats[colonne] = {
            "valeur": valeur,
            "statut": statut_seuil_fixe(valeur, sens, seuil_vert),
            "valeur_n1": delta["valeur_reference"] if delta else None,
            "delta_n1_points": delta_points,
            "tendance_n1": statut_tendance(delta_points, sens),
        }

    return {"mois": mois_actuel, "kpi": resultats}


def calculer_serie_annuelle(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Retourne, pour chaque mois archivé d'une année donnée, la valeur et
    le statut des KPI RH à seuil fixe (y compris PAC, sur son seuil
    provisoire ≤36%). Alimente les graphiques d'évolution et le tableau
    récapitulatif annuel.
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        df_annee[f"{colonne}_statut"] = df_annee[colonne].apply(
            lambda valeur: statut_seuil_fixe(valeur, sens, seuil_vert)
        )

    return df_annee