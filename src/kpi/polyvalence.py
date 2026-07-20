"""
src/kpi/polyvalence.py

Calcul des KPI du pôle Polyvalence à partir des données DATA_Polyvalence.

Particularités de ce pôle par rapport aux autres :
- Un seul objectif (45%), appliqué à la fois au taux global ET à chaque poste
- "Nombre d'équipiers" est un simple compteur, sans seuil
- Pas de tableau récapitulatif annuel : seul le taux global a une série
  mensuelle (pour le graphique d'évolution 2025 vs 2024)
- Les postes "le + / - maîtrisé" ne sont pas fixes : ils sont déterminés
  dynamiquement chaque mois en comparant les valeurs de tous les postes
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe, statut_tendance, calculer_delta

# Colonne du taux global, et liste des 10 postes individuels
COLONNE_TAUX_GLOBAL = "Taux de polyvalence"
POSTES = [
    "% Frites", "% Salle", "% B/D", "% Verif", "% Pass drive",
    "% PDC", "% Inic", "% UHC", "% Viandes", "% FCN",
]
COLONNE_EFFECTIF = "Nombre d'équipiers"

COLONNES_NUMERIQUES = [COLONNE_TAUX_GLOBAL] + POSTES + [COLONNE_EFFECTIF]

# Objectif unique, appliqué au taux global et à chaque poste (sens "min" :
# vert si au-dessus, rouge si en dessous — cf. légende de ta maquette)
OBJECTIF_POLYVALENCE = 45


def charger_donnees_polyvalence() -> pd.DataFrame:
    """
    Charge et nettoie les données du pôle Polyvalence : lecture du Sheets
    puis conversion des colonnes numériques (virgule -> point -> float).
    """
    df = load_data_tab("DATA_Polyvalence")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def calculer_kpi_polyvalence(df: pd.DataFrame = None) -> dict:
    """
    Calcule les KPI Polyvalence pour le mois le plus récent disponible.

    Returns:
        dict structuré ainsi :
        {
            "mois": Timestamp du mois courant,
            "effectif": 32,  # Nombre d'équipiers, simple valeur
            "taux_global": {
                "valeur": 46.1, "statut": "vert",
                "valeur_n1": 43.7, "delta_n1_points": 2.4,
                "tendance_n1": "vert"
            },
            "postes": {
                "% Frites": {"valeur": 46, "statut": "vert"},
                "% Verif": {"valeur": 36, "statut": "rouge"},
                ...  # un par poste, statut vs le même objectif 45%
            },
            "poste_plus_maitrise": {"nom": "% PDC", "valeur": 56, "statut": "vert"},
            "poste_moins_maitrise": {"nom": "% Verif", "valeur": 36, "statut": "rouge"},
        }
    """
    if df is None:
        df = charger_donnees_polyvalence()

    mois_actuel = df["Mois"].max()
    ligne_actuelle = df[df["Mois"] == mois_actuel].iloc[0]

    # Taux global : seuil + delta N-1 + tendance, comme les autres pôles
    valeur_globale = ligne_actuelle[COLONNE_TAUX_GLOBAL]
    delta = calculer_delta(df, COLONNE_TAUX_GLOBAL, mois_actuel, pd.DateOffset(years=1))
    delta_points = delta["delta_points"] if delta else None
    taux_global = {
        "valeur": valeur_globale,
        "statut": statut_seuil_fixe(valeur_globale, "min", OBJECTIF_POLYVALENCE),
        "valeur_n1": delta["valeur_reference"] if delta else None,
        "delta_n1_points": delta_points,
        "tendance_n1": statut_tendance(delta_points, "min"),
    }

    # Chaque poste comparé au même objectif de 45%
    postes = {}
    for colonne in POSTES:
        valeur = ligne_actuelle[colonne]
        postes[colonne] = {
            "valeur": valeur,
            "statut": statut_seuil_fixe(valeur, "min", OBJECTIF_POLYVALENCE),
        }

    # Poste le + / - maîtrisé du mois : déterminés dynamiquement,
    # pas de poste fixe (contrairement à ce qu'une maquette d'exemple
    # pourrait laisser penser)
    postes_valides = {
        nom: data for nom, data in postes.items() if pd.notna(data["valeur"])
    }
    nom_poste_plus = max(postes_valides, key=lambda nom: postes_valides[nom]["valeur"])
    nom_poste_moins = min(postes_valides, key=lambda nom: postes_valides[nom]["valeur"])

    poste_plus_maitrise = {"nom": nom_poste_plus, **postes_valides[nom_poste_plus]}
    poste_moins_maitrise = {"nom": nom_poste_moins, **postes_valides[nom_poste_moins]}

    return {
        "mois": mois_actuel,
        "effectif": ligne_actuelle[COLONNE_EFFECTIF],
        "taux_global": taux_global,
        "postes": postes,
        "poste_plus_maitrise": poste_plus_maitrise,
        "poste_moins_maitrise": poste_moins_maitrise,
    }


def calculer_serie_taux_global(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Retourne, pour chaque mois archivé d'une année donnée, le taux de
    polyvalence global et son statut. Alimente uniquement le graphique
    "Évolution taux global — 2025 vs 2024" (appelé une fois par année
    à superposer). Contrairement aux autres pôles, il n'y a pas de série
    par poste ni de tableau récapitulatif annuel pour ce pôle.
    """
    df_annee = df[df["Mois"].dt.year == annee][["Mois", COLONNE_TAUX_GLOBAL]].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    df_annee[f"{COLONNE_TAUX_GLOBAL}_statut"] = df_annee[COLONNE_TAUX_GLOBAL].apply(
        lambda valeur: statut_seuil_fixe(valeur, "min", OBJECTIF_POLYVALENCE)
    )

    return df_annee