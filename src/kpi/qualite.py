"""
src/kpi/qualite.py

Calcul des KPI du pôle Qualité / Sécurité Alimentaire à partir des données
DATA_Qualité. Seule page du dashboard organisée par ANNÉE (pas de mois) :
audits interne/Siliker mois par mois + agrégat annuel, prélèvements
bactériologiques (codes Z/U/T par item et par mois — le taux annuel est
pris DIRECTEMENT depuis la colonne "Taux de prélèvement" déjà saisie dans
le Sheet, pas recalculé à partir des codes — décision de Bastien).
"""

import datetime
import pandas as pd
from src.gspread.connection import load_data_tab
from src.kpi.utils import clean_numeric_columns, statut_seuil_fixe

# Les 3 indicateurs numériques (%) du pôle
COLONNES_NUMERIQUES = ["Audit interne", "Audit Siliker", "Taux de prélèvement"]

# Les 14 items de prélèvement bactériologique (codes Z/U/T — PAS
# numériques, ne pas les passer à clean_numeric_columns ; parsés seulement
# à l'affichage, dans la page)
ITEMS_PRELEVEMENT = [
    "Chantilly", "Sundae", "Shake", "Salade", "Surfaces", "Glaçons",
    "Coupe-tomates", "Mains", "Eau", "Sandwich", "Gâteau",
    "Boissons chaudes", "Re-use", "Boissons froides",
]

# Libellés courts pour les en-têtes du tableau (14 colonnes = ne rentre
# pas en entier, comme sur la maquette)
LIBELLES_COURTS_ITEMS = {
    "Chantilly": "Chantilly",
    "Sundae": "Sundae",
    "Shake": "Shake",
    "Salade": "Salade",
    "Surfaces": "Surfaces",
    "Glaçons": "Glaçons",
    "Coupe-tomates": "C.-tomates",
    "Mains": "Mains",
    "Eau": "Eau",
    "Sandwich": "Sandwich",
    "Gâteau": "Gâteau",
    "Boissons chaudes": "B. chaudes",
    "Re-use": "Re-use",
    "Boissons froides": "B. froides",
}

SEUILS_FIXES = {
    "Audit interne": ("min", 90),        # %
    "Audit Siliker": ("min", 98),        # %, 4x/an
    "Taux de prélèvement": ("min", 98),  # %
}


def charger_donnees_qualite() -> pd.DataFrame:
    """Charge et nettoie les données du pôle Qualité. Seules les 3
    colonnes d'indicateurs numériques sont converties en float — les 14
    colonnes de prélèvement restent en texte brut (codes Z/U/T)."""
    df = load_data_tab("DATA_Qualité")
    df = clean_numeric_columns(df, COLONNES_NUMERIQUES)
    return df


def _construire_table_audit(df: pd.DataFrame, colonne: str, annee: int) -> dict:
    """
    Détail mois par mois d'un indicateur d'audit (Audit interne ou Audit
    Siliker) pour une année donnée, + agrégat annuel (moyenne des mois
    renseignés).

    Un mois SANS donnée est marqué "Pas d'audit" s'il est déjà passé, ou
    "À venir" sinon — comparé à la date réelle d'aujourd'hui, puisque
    cette page n'a pas de sélecteur de mois pour servir de référence.
    """
    sens, seuil_vert = SEUILS_FIXES[colonne]
    aujourdhui = datetime.date.today()

    df_annee = df[df["Mois"].dt.year == annee]
    valeurs_par_mois = {int(l["Mois"].month): l[colonne] for _, l in df_annee.iterrows()}

    lignes = []
    for m in range(1, 13):
        valeur = valeurs_par_mois.get(m)
        mois_est_passe = (annee, m) <= (aujourdhui.year, aujourdhui.month)

        if pd.notna(valeur):
            statut = statut_seuil_fixe(valeur, sens, seuil_vert)
            resultat = "Conforme" if statut == "vert" else "Hors objectif"
        else:
            valeur = None
            statut = "neutre"
            resultat = "Pas d'audit" if mois_est_passe else "À venir"

        lignes.append({"mois": m, "valeur": valeur, "statut": statut, "resultat": resultat})

    valeurs_valides = [l["valeur"] for l in lignes if l["valeur"] is not None]
    valeur_annuelle = round(sum(valeurs_valides) / len(valeurs_valides), 1) if valeurs_valides else None
    statut_annuel = statut_seuil_fixe(valeur_annuelle, sens, seuil_vert) if valeur_annuelle is not None else "non disponible"

    return {"lignes": lignes, "valeur_annuelle": valeur_annuelle, "statut_annuel": statut_annuel}


def calculer_kpi_qualite(df: pd.DataFrame, annee: int) -> dict:
    """
    Calcule les 3 indicateurs du pôle pour une année donnée :
    - audit_interne / audit_siliker : détail mensuel + agrégat annuel
    - prelevement : agrégat annuel = moyenne de la colonne "Taux de
      prélèvement" déjà saisie (PAS un recalcul à partir des codes Z/U/T
      des 14 items — décision de Bastien, le sujet était "à confirmer
      avec Arnaud" dans les notes de mémoire, c'est réglé)
    """
    audit_interne = _construire_table_audit(df, "Audit interne", annee)
    audit_siliker = _construire_table_audit(df, "Audit Siliker", annee)

    sens, seuil_vert = SEUILS_FIXES["Taux de prélèvement"]
    df_annee = df[df["Mois"].dt.year == annee]
    valeurs_prelevement = df_annee["Taux de prélèvement"].dropna()
    valeur_prelevement = round(valeurs_prelevement.mean(), 1) if not valeurs_prelevement.empty else None
    statut_prelevement = (
        statut_seuil_fixe(valeur_prelevement, sens, seuil_vert) if valeur_prelevement is not None else "non disponible"
    )

    return {
        "annee": annee,
        "audit_interne": audit_interne,
        "audit_siliker": audit_siliker,
        "prelevement": {"valeur_annuelle": valeur_prelevement, "statut_annuel": statut_prelevement},
    }


def extraire_table_prelevements(df: pd.DataFrame, annee: int) -> pd.DataFrame:
    """
    Sous-ensemble du DataFrame pour l'année donnée : colonne Mois + les 14
    items de prélèvement (codes bruts, ex: "1Z", "3Z 1U", ou vide) + la
    colonne "Taux de prélèvement" (%) du mois, affichée en toute dernière
    colonne du tableau — alimente le tableau "Prélèvements bactériologiques"
    de la page.
    """
    df_annee = df[df["Mois"].dt.year == annee].copy()
    return df_annee[["Mois"] + ITEMS_PRELEVEMENT + ["Taux de prélèvement"]]