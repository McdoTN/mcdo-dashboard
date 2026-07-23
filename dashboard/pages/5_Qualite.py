"""
dashboard/pages/5_Qualite.py

Page Qualité / Sécurité Alimentaire : seule page du dashboard organisée
par ANNÉE (pas de sélecteur de mois) — indicateurs annuels, détail des
prélèvements bactériologiques par item et par mois (codes Z/U/T), et
détail des audits interne/Siliker mois par mois. Pas de marqueur de mois
"◀" sur cette page (pas de notion de mois sélectionné).
"""

import sys
import datetime
from pathlib import Path

chemin = Path(__file__).resolve().parent
while not (chemin / "src").exists():
    chemin = chemin.parent
sys.path.append(str(chemin))

import streamlit as st
import pandas as pd

from style import (
    appliquer_style, carte_kpi, badge_html, COULEURS_STATUT,
    COULEUR_CARTE, COULEUR_CARTE_BORDURE, COULEUR_TEXTE, COULEUR_TEXTE_SECONDAIRE,
    titre_page, section_eyebrow, groupe_titre, MOIS_FR, MOIS_ABREGE_FR,
)
from sidebar import construire_sidebar
from src.kpi.qualite import (
    charger_donnees_qualite, calculer_kpi_qualite, extraire_table_prelevements,
    ITEMS_PRELEVEMENT, LIBELLES_COURTS_ITEMS, SEUILS_FIXES,
)

st.set_page_config(page_title="Qualité — Dashboard McDo", page_icon="🛡️", layout="wide")
appliquer_style()
construire_sidebar("qualite")

df = charger_donnees_qualite()

# --- SÉLECTEUR D'ANNÉE (pas de mois sur cette page) ---
annees_disponibles = sorted(df["Mois"].dropna().dt.year.unique().tolist(), reverse=True)

col_titre, col_selecteur = st.columns([5, 1])
with col_titre:
    titre_page("Qualité / Sécurité Alimentaire")
with col_selecteur:
    st.write("")
    annee_selectionnee = st.selectbox(
        "Année", options=annees_disponibles, index=0, label_visibility="collapsed",
    )

resultats = calculer_kpi_qualite(df, annee_selectionnee)
audit_interne = resultats["audit_interne"]
audit_siliker = resultats["audit_siliker"]
prelevement = resultats["prelevement"]


def texte_seuil(nom_kpi: str) -> str:
    sens, seuil = SEUILS_FIXES[nom_kpi]
    symbole = "≤" if sens == "max" else "≥"
    return f"Objectif : {symbole} {seuil:g}%"


# --- INDICATEURS DE L'ANNÉE ---
section_eyebrow("KPI du mois")
groupe_titre(f"Résultats annuels — {annee_selectionnee}")

with st.container(key="qualite_kpi_annee"):
    col1, col2, col3 = st.columns(3)
    with col1:
        valeur = audit_interne["valeur_annuelle"]
        carte_kpi(
            f"Audit interne — {annee_selectionnee}",
            f"{valeur:.1f}%" if valeur is not None else "—",
            None, None, texte_seuil("Audit interne"), audit_interne["statut_annuel"],
        )
    with col2:
        valeur = audit_siliker["valeur_annuelle"]
        carte_kpi(
            f"Audit Siliker — {annee_selectionnee}",
            f"{valeur:.1f}%" if valeur is not None else "—",
            None, None, texte_seuil("Audit Siliker"), audit_siliker["statut_annuel"],
        )
    with col3:
        valeur = prelevement["valeur_annuelle"]
        carte_kpi(
            f"Prélèvements — {annee_selectionnee}",
            f"{valeur:.1f}%" if valeur is not None else "—",
            None, None, texte_seuil("Taux de prélèvement"), prelevement["statut_annuel"],
        )

st.markdown(
    '<style>.st-key-qualite_kpi_annee .carte-kpi { min-height: 130px !important; box-sizing: border-box; }</style>',
    unsafe_allow_html=True,
)


# --- PRÉLÈVEMENTS BACTÉRIOLOGIQUES : détail par item et par mois ---
section_eyebrow(f"Prélèvements bactériologiques — {annee_selectionnee}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

# Couleurs des codes Z/U/T — palette pastel cohérente avec COULEURS_STATUT,
# étendue avec un jaune/orange pour U (pas dans la palette de base, qui ne
# connaît que vert/rouge/neutre)
COULEURS_CODE = {
    "Z": {"bg": "#eaf3de", "texte": "#2b530e"},
    "U": {"bg": "#fef3c7", "texte": "#92400e"},
    "T": {"bg": "#fce7f3", "texte": "#9d174d"},
}


def badges_codes(cellule) -> str:
    """
    Rend chaque code d'une cellule comme un petit badge coloré, côte à
    côte. Une cellule peut contenir plusieurs codes séparés par un espace
    (ex: "3Z 1U") — ça arrive réellement dans les données, donc on les
    affiche tels quels, sans les fusionner ni les recalculer.
    """
    if not isinstance(cellule, str) or not cellule.strip():
        return f'<span style="color:{COULEUR_TEXTE_SECONDAIRE};">—</span>'

    badges = ""
    for token in cellule.strip().split():
        lettre = token[-1].upper()
        couleurs = COULEURS_CODE.get(lettre, COULEURS_STATUT["neutre"])
        badges += (
            f'<span style="display:inline-block; padding:2px 7px; border-radius:5px; '
            f'font-size:12px; font-weight:600; background-color:{couleurs["bg"]}; '
            f'color:{couleurs["texte"]}; margin-right:3px;">{token}</span>'
        )
    return badges


table_prelevements = extraire_table_prelevements(df, annee_selectionnee)
prelevements_par_mois = {int(l["Mois"].month): l for _, l in table_prelevements.iterrows()}

# Bordure verticale entre les colonnes d'items, propre à ce tableau (pas
# ajoutée à la classe .tableau-recap partagée, pour ne pas affecter les
# tableaux récap des autres pages)
# box-shadow (et non border) : la classe partagée .tableau-recap force
# "border: none !important" sur th/td, ce qui écrase systématiquement un
# border-right même avec !important en second (les deux déclarations sont
# dans la même règle, donc pas de conflit de spécificité à gagner). Le
# box-shadow est une propriété différente, jamais touchée par cette règle.
BORDURE_VERTICALE = f"box-shadow: inset -1px 0 0 {COULEUR_CARTE_BORDURE};"

# Mois réel d'aujourd'hui (pas de sélecteur de mois sur cette page) : sa
# ligne est légèrement assombrie dans le tableau, sans flèche ni marqueur
# — juste pour repérer "où on en est" visuellement
aujourdhui = datetime.date.today()
mois_reel_dans_annee = aujourdhui.month if annee_selectionnee == aujourdhui.year else None

lignes_html = ""
for m in range(1, 13):
    nom_mois = MOIS_ABREGE_FR[m - 1]
    fond_ligne = "background-color:rgba(255,255,255,0.04);" if m == mois_reel_dans_annee else ""
    lignes_html += (
        f'<tr style="{fond_ligne}"><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE}; '
        f'white-space:nowrap; {BORDURE_VERTICALE}">{nom_mois}</td>'
    )
    if m in prelevements_par_mois:
        ligne = prelevements_par_mois[m]
        for item in ITEMS_PRELEVEMENT:
            lignes_html += (
                f'<td style="padding:8px; white-space:nowrap; text-align:center; '
                f'{BORDURE_VERTICALE}">{badges_codes(ligne[item])}</td>'
            )
        # Taux de prélèvement du mois, en toute dernière colonne — affiché
        # seulement s'il y a effectivement eu un prélèvement ce mois-ci
        taux_mois = ligne["Taux de prélèvement"]
        texte_taux = f'{taux_mois:.1f}%' if pd.notna(taux_mois) else "—"
        couleur_taux = COULEUR_TEXTE if pd.notna(taux_mois) else COULEUR_TEXTE_SECONDAIRE
        lignes_html += (
            f'<td style="padding:8px; text-align:center; font-weight:600; '
            f'color:{couleur_taux};">{texte_taux}</td>'
        )
    else:
        for _ in ITEMS_PRELEVEMENT:
            lignes_html += (
                f'<td style="padding:8px; text-align:center; color:{COULEUR_TEXTE_SECONDAIRE}; '
                f'{BORDURE_VERTICALE}">—</td>'
            )
        lignes_html += f'<td style="padding:8px; text-align:center; color:{COULEUR_TEXTE_SECONDAIRE};">—</td>'
    lignes_html += "</tr>"

entetes = "".join(
    f'<th style="padding:8px; text-align:center; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; '
    f'font-weight:600; white-space:nowrap; {BORDURE_VERTICALE}">{LIBELLES_COURTS_ITEMS[item]}</th>'
    for item in ITEMS_PRELEVEMENT
)
entetes += (
    f'<th style="padding:8px; text-align:center; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; '
    f'font-weight:600; white-space:nowrap;">Taux</th>'
)

# overflow-x:auto en local (pas dans style.py) : 14 colonnes ne rentrent
# pas à l'écran, contrairement aux autres tableaux récap du dashboard qui
# n'ont jamais eu besoin de défilement horizontal
html_table = f"""
<div class="carte-graphique tableau-recap" style="padding-bottom:16px; overflow-x:auto;">
<table>
    <tr><th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600; {BORDURE_VERTICALE}">Mois</th>{entetes}</tr>
    {lignes_html}
</table>
</div>
"""
st.markdown(html_table, unsafe_allow_html=True)

# Légende Z/U/T
legende_html = '<div style="display:flex; align-items:center; gap:20px; margin-top:8px; margin-bottom:24px; flex-wrap:wrap;">'
for lettre, texte in [("Z", "Satisfaisant"), ("U", "Non satisfaisant N1"), ("T", "Non satisfaisant N2")]:
    couleurs = COULEURS_CODE[lettre]
    legende_html += (
        f'<div style="display:flex; align-items:center; gap:6px;">'
        f'<span style="display:inline-block; padding:2px 7px; border-radius:5px; font-size:12px; font-weight:600; '
        f'background-color:{couleurs["bg"]}; color:{couleurs["texte"]};">{lettre}</span>'
        f'<span style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px;">— {texte}</span>'
        f'</div>'
    )
legende_html += "</div>"
st.markdown(legende_html, unsafe_allow_html=True)


# --- AUDITS : détail mensuel interne / Siliker ---
section_eyebrow(f"Audits — {annee_selectionnee}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)


def construire_table_audit_html(titre: str, table: dict) -> str:
    lignes = ""
    for ligne in table["lignes"]:
        nom_mois = MOIS_FR[ligne["mois"] - 1]
        if ligne["valeur"] is not None:
            score = f'{ligne["valeur"]:.0f}%'
            resultat = badge_html(ligne["resultat"], ligne["statut"])
        else:
            score = "—"
            # Réutilise la classe .badge (fond transparent) plutôt qu'un
            # simple <span> : les deux ont alors exactement le même padding
            # et la même hauteur de ligne, donc plus de décalage progressif
            # entre les tableaux selon leur proportion de lignes avec/sans
            # badge réel.
            resultat = (
                f'<span class="badge" style="background-color:transparent; '
                f'color:{COULEUR_TEXTE_SECONDAIRE};">{ligne["resultat"]}</span>'
            )
        lignes += (
            f'<tr><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE};">{nom_mois}</td>'
            f'<td style="padding:8px; color:{COULEUR_TEXTE};">{score}</td>'
            f'<td style="padding:8px;">{resultat}</td></tr>'
        )

    valeur_annuelle = table["valeur_annuelle"]
    score_total = f'{valeur_annuelle:.1f}%' if valeur_annuelle is not None else "—"
    badge_total = ""
    if valeur_annuelle is not None:
        texte_badge = "Dans l'objectif" if table["statut_annuel"] == "vert" else "Hors objectif"
        badge_total = badge_html(texte_badge, table["statut_annuel"])

    return f"""
    <div class="carte-graphique tableau-recap" style="padding-bottom:8px; box-sizing:border-box; min-height:610px;">
    <div class="carte-titre" style="margin-bottom:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{titre}</div>
    <table>
        <tr>
            <th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600;">Mois</th>
            <th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600;">Score</th>
            <th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600;">Résultat</th>
        </tr>
        {lignes}
        <tr style="background-color:rgba(255,255,255,0.04);">
            <td style="padding:8px; font-weight:700; color:{COULEUR_TEXTE}; border-top:2px solid {COULEUR_CARTE_BORDURE} !important;">Total {annee_selectionnee}</td>
            <td style="padding:8px; font-weight:700; color:{COULEUR_TEXTE}; border-top:2px solid {COULEUR_CARTE_BORDURE} !important;">{score_total}</td>
            <td style="padding:8px; border-top:2px solid {COULEUR_CARTE_BORDURE} !important;">{badge_total}</td>
        </tr>
    </table>
    </div>
    """


col1, col2 = st.columns(2)
with col1:
    st.markdown(
        construire_table_audit_html(
            f"Audit interne — objectif {texte_seuil('Audit interne').replace('Objectif : ', '')}", audit_interne,
        ),
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        construire_table_audit_html(
            f"Audit Siliker — objectif {texte_seuil('Audit Siliker').replace('Objectif : ', '')} — 4×/an", audit_siliker,
        ),
        unsafe_allow_html=True,
    )