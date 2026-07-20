"""
src/kpi/service.py

Calcul des KPI du pôle Service à partir des données DATA_Service,
avec attribution d'un statut (vert/rouge/non disponible) selon les
seuils validés avec Arnaud.
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe, statut_tendance, calculer_delta

# Colonnes du pôle Service qui sont réellement numériques
# (toutes les colonnes hors "Mois" le sont, contrairement au pôle Qualité)
COLONNES_NUMERIQUES = [
    "Temps de service R2P comptoir", "Temps de service OEPE drive",
    "% Comptoir", "% Drive", "% LAD", "% Click & Collect",
    "Anniversaires", "Note Google", "Nombre d'avis Google",
    "McDo&Moi", "Rapport balance", "Big forced",
]

# Seuils fixes : {colonne: (sens, seuil_vert)}
SEUILS_FIXES = {
    "Temps de service R2P comptoir": ("max", 300),
    "Temps de service OEPE drive": ("max", 300),
    "Anniversaires": ("min", 4),
    "Note Google": ("min", 4.2),
    "McDo&Moi": ("min", 98),
    "Rapport balance": ("min", 98),
    "Big forced": ("max", 20),
}

# Mix des canaux : simple affichage (donut chart), pas de statut vert/rouge
# — seuils "proche de X%" encore à clarifier avec Arnaud
COLONNES_MIX_CANAUX = ["% Comptoir", "% Drive", "% LAD", "% Click & Collect"]

# Nombre d'avis Google : suivi simple, comparé au MOIS PRÉCÉDENT
# (pas à N-1 comme les autres KPI — un volume d'avis se suit au fil de
# l'eau plutôt qu'en saisonnalité annuelle)
COLONNE_AVIS_GOOGLE = "Nombre d'avis Google"


def charger_donnees_service() -> pd.DataFrame:
    """
    Charge et nettoie les données du pôle Service : lecture du Sheets
    puis conversion des colonnes numériques (virgule -> point -> float).
    """
    df = load_data_tab("DATA_Service")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def calculer_kpi_service(df: pd.DataFrame = None) -> dict:
    """
    Calcule l'ensemble des KPI Service pour le mois le plus récent
    disponible dans les données.

    Returns:
        dict structuré ainsi :
        {
            "mois": Timestamp du mois courant,
            "kpi": {
                "Temps de service R2P comptoir": {
                    "valeur": 274, "statut": "vert",
                    "valeur_n1": 286, "delta_n1_points": -12,
                    "tendance_n1": "vert"  # baisse = bonne nouvelle
                },
                ...
                "Nombre d'avis Google": {
                    "valeur": 47, "valeur_mois_precedent": 43,
                    "delta_mois_precedent": 4
                    # pas de "statut" : suivi simple, pas de seuil
                },
            },
            "mix_canaux": {
                "% Comptoir": 53, "% Drive": 32, "% LAD": 9, "% Click & Collect": 6
            }
        }
    """
    if df is None:
        df = charger_donnees_service()

    mois_actuel = df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    resultats = {}

    # KPI à seuil fixe, avec delta N-1 et tendance (comme le pôle Business)
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

    # Nombre d'avis Google : comparaison au mois précédent, pas de statut
    delta_avis = calculer_delta(
        df, COLONNE_AVIS_GOOGLE, mois_actuel, pd.DateOffset(months=1)
    )
    resultats[COLONNE_AVIS_GOOGLE] = {
        "valeur": ligne_actuelle[COLONNE_AVIS_GOOGLE],
        "valeur_mois_precedent": delta_avis["valeur_reference"] if delta_avis else None,
        "delta_mois_precedent": delta_avis["delta_points"] if delta_avis else None,
    }

    # Mix des canaux du mois courant (simple affichage, pour le donut chart)
    mix_canaux = {colonne: ligne_actuelle[colonne] for colonne in COLONNES_MIX_CANAUX}

    return {"mois": mois_actuel, "kpi": resultats, "mix_canaux": mix_canaux}


def calculer_serie_annuelle(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Retourne, pour chaque mois archivé d'une année donnée, la valeur et
    le statut de chaque KPI à seuil fixe. Alimente les graphiques
    d'évolution (ex: barres Anniversaires colorées par mois, ligne
    Rapport balance avec seuil) et le tableau récapitulatif annuel.

    Args:
        df: DataFrame déjà chargé et nettoyé (via charger_donnees_service())
        annee: année à extraire, ex: 2026

    Returns:
        DataFrame filtré sur l'année, trié par mois, avec une colonne
        "<KPI>_statut" par KPI à seuil fixe. N'inclut pas les colonnes
        de mix canaux ni le nombre d'avis Google (pas de statut associé).
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        df_annee[f"{colonne}_statut"] = df_annee[colonne].apply(
            lambda valeur: statut_seuil_fixe(valeur, sens, seuil_vert)
        )

    return df_annee