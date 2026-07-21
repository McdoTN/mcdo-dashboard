"""
src/kpi/business.py

Calcul des KPI du pôle Business à partir des données DATA_Business,
avec attribution d'un statut (vert/jaune/rouge/non disponible) selon
les seuils validés avec Arnaud.
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_tendance, statut_seuil_fixe, calculer_delta

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


def calculer_delta_n1(df: pd.DataFrame, colonne: str, mois_actuel: pd.Timestamp):
    """
    Calcule le delta N-1 (vs même mois année précédente) pour un KPI donné.
    Fine couche au-dessus de calculer_delta() (utils.py) pour garder les
    noms de clés historiques ("valeur_n1") utilisés ailleurs dans ce fichier.

    Returns:
        dict {"valeur_n1": ..., "delta_points": ..., "delta_pct": ...}
        ou None si le mois N-1 n'est pas disponible.
    """
    resultat = calculer_delta(df, colonne, mois_actuel, pd.DateOffset(years=1))
    if resultat is None:
        return None
    return {
        "valeur_n1": resultat["valeur_reference"],
        "delta_points": resultat["delta_points"],
        "delta_pct": resultat["delta_pct"],
    }


def statut_comparatif_n1(delta_pct) -> str:
    """
    Détermine le statut pour un KPI en comparatif N-1 (CA, TAC).

    Règle validée : vert si > 0% vs N-1, jaune si = 0%, rouge si < 0%.
    """
    if delta_pct is None:
        return "non disponible"
    if delta_pct > 0:
        return "vert"
    elif delta_pct == 0:
        return "jaune"
    else:
        return "rouge"


def calculer_kpi_business(df: pd.DataFrame = None, mois: pd.Timestamp = None) -> dict:
    """
    Calcule l'ensemble des KPI Business pour un mois donné. Alimente les
    cartes "KPI du mois" du dashboard (statut + delta vs N-1).

    Args:
        df: DataFrame déjà chargé et nettoyé (optionnel). Si non fourni,
            charge et nettoie les données automatiquement.
        mois: mois à afficher (optionnel). Si non fourni, utilise le mois
            le plus récent disponible dans les données — comportement
            historique, conservé par défaut pour ne rien casser ailleurs.

    Returns:
        dict structuré ainsi :
        {
            "mois": Timestamp du mois demandé (ou le plus récent par défaut),
            "kpi": {
                # KPI à seuil fixe : statut vient du seuil, delta_n1 est indicatif
                "QCR": {"valeur": 19.5, "statut": "vert",
                        "valeur_n1": 20.1, "delta_n1_points": -0.6},
                # KPI en comparatif N-1 : statut vient du delta lui-même
                "CA": {"valeur": 25000, "valeur_n1": 24000,
                       "evolution_n1_pct": 4.2, "statut": "vert"},
                ...
            }
        }
    """
    if df is None:
        df = charger_donnees_business()

    mois_actuel = mois if mois is not None else df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    resultats = {}

    # KPI à seuil fixe : le statut vient du seuil, le delta N-1 est
    # seulement affiché à titre indicatif (comme sur la maquette)
    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        valeur = ligne_actuelle[colonne]
        delta = calculer_delta_n1(df, colonne, mois_actuel)
        delta_points = delta["delta_points"] if delta else None
        resultats[colonne] = {
            "valeur": valeur,
            "statut": statut_seuil_fixe(valeur, sens, seuil_vert),
            "valeur_n1": delta["valeur_n1"] if delta else None,
            "delta_n1_points": delta_points,
            # Couleur de la flèche de delta (différent du statut vs seuil !) :
            # ex: QCR qui augmente est rouge même si encore "dans l'objectif"
            "tendance_n1": statut_tendance(delta_points, sens),
        }

    # KPI en comparatif N-1 (CA, TAC) : le statut vient du delta lui-même
    for colonne in COLONNES_COMPARATIF_N1:
        delta = calculer_delta_n1(df, colonne, mois_actuel)
        evolution_pct = delta["delta_pct"] if delta else None
        resultats[colonne] = {
            "valeur": ligne_actuelle[colonne],
            "valeur_n1": delta["valeur_n1"] if delta else None,
            "evolution_n1_pct": evolution_pct,
            "statut": statut_comparatif_n1(evolution_pct),
        }

    return {"mois": mois_actuel, "kpi": resultats}


def calculer_serie_annuelle(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Retourne, pour chaque mois archivé d'une année donnée, la valeur et
    le statut de chaque KPI à seuil fixe. Sert de base commune :
    - aux graphiques d'évolution (ex: barres Coût de la hub avec ligne
      de seuil, courbe CA mensuel)
    - au tableau récapitulatif annuel (une ligne par mois, badges colorés)

    Args:
        df: DataFrame déjà chargé et nettoyé (via charger_donnees_business())
        annee: année à extraire, ex: 2025

    Returns:
        DataFrame filtré sur l'année demandée, trié par mois, avec une
        colonne supplémentaire "<KPI>_statut" pour chaque KPI à seuil fixe.
        Ne contient que les mois réellement archivés : un mois manquant
        (comme "Jun —" sur la maquette) n'apparaîtra pas dans ce DataFrame
        — c'est au dashboard de compléter l'affichage avec les mois
        manquants si besoin (hors périmètre de ce script de calcul).
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    for colonne, (sens, seuil_vert) in SEUILS_FIXES.items():
        df_annee[f"{colonne}_statut"] = df_annee[colonne].apply(
            lambda valeur: statut_seuil_fixe(valeur, sens, seuil_vert)
        )

    return df_annee