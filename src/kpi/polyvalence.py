"""
src/kpi/polyvalence.py

Calcul des KPI du pôle Polyvalence à partir des données DATA_POLYVALENCE.

Un seul seuil pour tout le pôle (45%, sens "min") : il s'applique au taux
global ET, implicitement, à chacun des 10 postes (code couleur du radar et
du classement de la page), sans qu'un badge "Objectif : ..." séparé soit
répété sur chaque poste — validé avec Bastien.
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe, statut_tendance, calculer_delta

# Les 10 postes du pôle Polyvalence (noms de postes McDo réels)
POSTES = [
    "% Frites", "% Salle", "% B/D", "% Verif", "% Pass drive",
    "% PDC", "% Inic", "% UHC", "% Viandes", "% FCN",
]

# Libellés courts affichés sur le dashboard (radar, classement) — sans le
# préfixe "% ", pour rester lisible sur des petits axes/labels
LIBELLES_POSTES = {
    "% Frites": "Frites",
    "% Salle": "Salle",
    "% B/D": "B/D",
    "% Verif": "Verif",
    "% Pass drive": "Pass Drive",
    "% PDC": "PDC",
    "% Inic": "Inic",
    "% UHC": "UHC",
    "% Viandes": "Viandes",
    "% FCN": "FCN",
}

COLONNES_NUMERIQUES = ["Taux de polyvalence"] + POSTES + ["Nombre d'équipiers"]

# Seuil unique pour tout le pôle
SEUIL_POLYVALENCE = ("min", 45)  # %


def charger_donnees_polyvalence() -> pd.DataFrame:
    """Charge et nettoie les données du pôle Polyvalence."""
    df = load_data_tab("DATA_Polyvalence")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def calculer_kpi_polyvalence(df: pd.DataFrame = None, mois: pd.Timestamp = None) -> dict:
    """
    Calcule les KPI Polyvalence pour un mois donné (ou le plus récent
    disponible si non précisé).

    Returns:
        dict :
        {
            "mois": Timestamp,
            "taux_global": {"valeur", "statut", "valeur_n1",
                             "delta_n1_points", "tendance_n1"},
            "postes": {"% Frites": {"valeur", "statut"}, ...},
            "nombre_equipiers": valeur brute (informatif, pas de statut),
            "poste_mieux_maitrise": nom de colonne (ex: "% Frites") ou None,
            "poste_moins_maitrise": nom de colonne ou None,
        }
    """
    if df is None:
        df = charger_donnees_polyvalence()

    mois_actuel = mois if mois is not None else df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    sens, seuil_vert = SEUIL_POLYVALENCE

    valeur_globale = ligne_actuelle["Taux de polyvalence"]
    delta = calculer_delta(df, "Taux de polyvalence", mois_actuel, pd.DateOffset(years=1))
    delta_points = delta["delta_points"] if delta else None
    taux_global = {
        "valeur": valeur_globale,
        "statut": statut_seuil_fixe(valeur_globale, sens, seuil_vert),
        "valeur_n1": delta["valeur_reference"] if delta else None,
        "delta_n1_points": delta_points,
        "tendance_n1": statut_tendance(delta_points, sens),
    }

    postes = {}
    for colonne in POSTES:
        valeur = ligne_actuelle[colonne]
        postes[colonne] = {
            "valeur": valeur,
            "statut": statut_seuil_fixe(valeur, sens, seuil_vert),
        }

    # Poste le mieux / le moins maîtrisé du mois (on ignore les postes sans
    # donnée saisie ce mois-ci)
    postes_valides = {c: v["valeur"] for c, v in postes.items() if pd.notna(v["valeur"])}
    poste_mieux_maitrise = max(postes_valides, key=postes_valides.get) if postes_valides else None
    poste_moins_maitrise = min(postes_valides, key=postes_valides.get) if postes_valides else None

    return {
        "mois": mois_actuel,
        "taux_global": taux_global,
        "postes": postes,
        "nombre_equipiers": ligne_actuelle["Nombre d'équipiers"],
        "poste_mieux_maitrise": poste_mieux_maitrise,
        "poste_moins_maitrise": poste_moins_maitrise,
    }


def calculer_serie_annuelle(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Série annuelle du TAUX GLOBAL uniquement (les 10 postes n'ont pas de
    graphique d'évolution sur cette page — ils sont montrés sur le mois
    sélectionné uniquement, via le radar et le classement).
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    sens, seuil_vert = SEUIL_POLYVALENCE
    df_annee["Taux de polyvalence_statut"] = df_annee["Taux de polyvalence"].apply(
        lambda v: statut_seuil_fixe(v, sens, seuil_vert)
    )
    return df_annee