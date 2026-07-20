"""
src/kpi/qualite.py

Calcul des KPI du pôle Qualité / Sécurité Alimentaire à partir des
données DATA_Qualite.

Ce pôle fonctionne différemment des autres :
- Pas de vue "mois courant" : les 3 taux (Audit interne, Audit Siliker,
  Taux de prélèvement) sont MOYENNÉS sur l'année, en ignorant les mois
  sans donnée (mois vides = normal, pas une erreur)
- Les 14 items de prélèvement bactériologique contiennent des codes
  alphanumériques (Z/U/T), pas des nombres — jamais de clean_numeric_columns
  dessus. Une cellule peut contenir plusieurs codes (ex: "3Z 1U")
- "Taux de prélèvement" est déjà calculé côté Google Sheets (colonne dédiée),
  on le lit tel quel, sans le recalculer à partir des items
"""

import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe, parse_codes_bacterio

# Les 3 taux du pôle, avec leur objectif propre — tous sens "min"
# (vert si au-dessus du seuil)
SEUILS_TAUX = {
    "Audit interne": ("min", 90),
    "Audit Siliker": ("min", 98),
    "Taux de prélèvement": ("min", 98),
}

# Les 14 items de prélèvement bactériologique — codes alphanumériques,
# ne JAMAIS passer dans clean_numeric_columns()
ITEMS_PRELEVEMENT = [
    "Chantilly", "Sundae", "Shake", "Salade", "Surfaces", "Glaçons",
    "Coupe-tomates", "Mains", "Eau", "Sandwich", "Gâteau",
    "Boissons chaudes", "Re-use", "Boissons froides",
]


def charger_donnees_qualite() -> pd.DataFrame:
    """
    Charge et nettoie les données du pôle Qualité. Seuls les 3 taux
    (Audit interne, Audit Siliker, Taux de prélèvement) sont convertis
    en numérique — les 14 items de prélèvement restent en texte brut,
    pour être parsés ensuite via parse_codes_bacterio().
    """
    df = load_data_tab("DATA_Qualité")
    df = clean_numeric_columns(df, list(SEUILS_TAUX.keys()))
    return df


def calculer_moyennes_annuelles(df: pd.DataFrame, annee: int) -> dict:
    """
    Calcule, pour une année donnée, la moyenne de chacun des 3 taux
    (Audit interne, Audit Siliker, Taux de prélèvement), en ignorant
    les mois sans donnée (cas normal : audit Siliker 4x/an seulement,
    par exemple).

    Returns:
        dict structuré ainsi :
        {
            "Audit interne": {"valeur": 90.5, "statut": "vert"},
            "Audit Siliker": {"valeur": 98.5, "statut": "vert"},
            "Taux de prélèvement": {"valeur": 93.3, "statut": "rouge"},
        }
        "valeur" est None et "statut" est "non disponible" si aucun mois
        de l'année n'a de donnée pour ce taux.
    """
    df_annee = df[df["Mois"].dt.year == annee]

    resultats = {}
    for colonne, (sens, seuil_vert) in SEUILS_TAUX.items():
        valeurs_valides = df_annee[colonne].dropna()

        if valeurs_valides.empty:
            resultats[colonne] = {"valeur": None, "statut": "non disponible"}
            continue

        moyenne = valeurs_valides.mean()
        resultats[colonne] = {
            "valeur": moyenne,
            "statut": statut_seuil_fixe(moyenne, sens, seuil_vert),
        }

    return resultats


def construire_tableau_prelevements(df: pd.DataFrame, annee: int) -> dict:
    """
    Construit le gros tableau de prélèvements bactériologiques (mois x item)
    pour une année donnée, avec les codes déjà parsés.

    Returns:
        dict {Timestamp du mois: {item: [(nombre, lettre), ...]}}
        Chaque mois de l'année apparaît, même sans aucun prélèvement
        (liste vide pour tous les items ce mois-là — cas normal).
        Un item peut avoir plusieurs résultats dans le même mois
        (ex: [(3, "Z"), (1, "U")] pour une cellule "3Z 1U").
    """
    df_annee = df[df["Mois"].dt.year == annee].sort_values("Mois")

    tableau = {}
    for _, ligne in df_annee.iterrows():
        tableau[ligne["Mois"]] = {
            item: parse_codes_bacterio(ligne[item]) for item in ITEMS_PRELEVEMENT
        }

    return tableau


def calculer_serie_audits(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Retourne, pour chaque mois archivé d'une année donnée, les valeurs
    et statuts d'Audit interne et Audit Siliker — pour le tableau
    récapitulatif mensuel de fin de page (le seul tableau récap de ce
    pôle, contrairement aux autres pôles qui en ont un plus complet).

    Un statut "non disponible" pour un mois signifie "Pas d'audit ce
    mois-là" (cas normal, notamment pour Siliker qui n'a lieu que 4x/an) —
    à traduire ainsi côté dashboard plutôt que comme une anomalie.
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    df_annee = df_annee.sort_values("Mois").reset_index(drop=True)

    for colonne in ("Audit interne", "Audit Siliker"):
        sens, seuil_vert = SEUILS_TAUX[colonne]
        df_annee[f"{colonne}_statut"] = df_annee[colonne].apply(
            lambda valeur: statut_seuil_fixe(valeur, sens, seuil_vert)
        )

    return df_annee[
        ["Mois", "Audit interne", "Audit interne_statut",
         "Audit Siliker", "Audit Siliker_statut"]
    ]