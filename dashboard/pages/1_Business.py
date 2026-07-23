"""
dashboard/pages/1_Business.py

Page Business : cartes KPI du mois, graphiques d'évolution 2025 vs 2024,
tableau récapitulatif annuel — reproduit le style de la maquette.
"""

import sys
from pathlib import Path

chemin = Path(__file__).resolve().parent
while not (chemin / "src").exists():
    chemin = chemin.parent
sys.path.append(str(chemin))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from style import appliquer_style, carte_kpi, badge_html, COULEURS_STATUT, COULEURS_DELTA, COULEUR_CARTE, COULEUR_CARTE_BORDURE, COULEUR_TEXTE, COULEUR_TEXTE_SECONDAIRE, titre_page, selecteur_mois, section_eyebrow, groupe_titre
from sidebar import construire_sidebar
from src.kpi.business import charger_donnees_business, calculer_kpi_business, calculer_serie_annuelle, SEUILS_FIXES

st.set_page_config(page_title="Business — Dashboard McDo", page_icon="📊", layout="wide")
appliquer_style()
construire_sidebar("business")

df = charger_donnees_business()

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
MOIS_ABREGE_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
]


def abrege_mois_fr(colonne_mois: pd.Series) -> list:
    """Convertit une colonne de dates en libellés de mois abrégés FRANÇAIS
    (ex: "Avr", pas "Apr") pour les axes des graphiques."""
    return [MOIS_ABREGE_FR[m - 1] for m in colonne_mois.dt.month]


def formater_mois(ts: pd.Timestamp) -> str:
    return f"{MOIS_FR[ts.month - 1]} {ts.year}"


# --- SÉLECTEUR DE MOIS (persistant entre les pages via st.session_state) ---
mois_selectionne = selecteur_mois(df, "Business")

resultats = calculer_kpi_business(df, mois=mois_selectionne)
mois_actuel = resultats["mois"]
kpi = resultats["kpi"]


def texte_seuil(nom_kpi: str) -> tuple[str, str]:
    """
    Construit le texte du badge à partir du VRAI seuil du KPI
    (ex: "≤ 75%", "≥ 20.5%"), plutôt qu'un texte générique
    "Dans l'objectif" / "Hors objectif". Toujours en <= ou >=
    (jamais < ou >), cohérent avec la logique inclusive de
    statut_seuil_fixe() (max -> valeur <= seuil, min -> valeur >= seuil).
    """
    sens, seuil = SEUILS_FIXES[nom_kpi]
    symbole = "≤" if sens == "max" else "≥"
    # :g retire les zéros inutiles (75.0 -> "75", 0.70 -> "0.7")
    return f"Objectif : {symbole} {seuil:g}%"


def mois_n1_texte(mois: pd.Timestamp) -> str:
    """Formate le mois N-1 en minuscules pour l'affichage dans les deltas (ex: "mai 2024")."""
    mois_n1 = mois - pd.DateOffset(years=1)
    return f"{MOIS_FR[mois_n1.month - 1].lower()} {mois_n1.year}"


def fleche_delta(valeur_delta) -> str:
    if valeur_delta is None:
        return ""
    return "▲" if valeur_delta > 0 else ("▼" if valeur_delta < 0 else "→")


# --- KPI DU MOIS ---
section_eyebrow("KPI du mois")

groupe_titre("Ventes")
col1, col2 = st.columns(2)
with col1:
    d = kpi["CA"]
    delta_texte = None
    if d["evolution_n1_pct"] is not None:
        delta_texte = (
            f'{fleche_delta(d["evolution_n1_pct"])} {d["evolution_n1_pct"]:+.1f}% '
            f'vs {mois_n1_texte(mois_actuel)} ({d["valeur_n1"]:,.0f} €)'.replace(",", " ")
        )
    carte_kpi("CA", f'{d["valeur"]:,.0f} €'.replace(",", " "), delta_texte, d["statut"])
with col2:
    d = kpi["TAC"]
    delta_texte = None
    if d["evolution_n1_pct"] is not None:
        delta_texte = (
            f'{fleche_delta(d["evolution_n1_pct"])} {d["evolution_n1_pct"]:+.1f}% '
            f'vs {mois_n1_texte(mois_actuel)} ({d["valeur_n1"]:,.0f})'.replace(",", " ")
        )
    carte_kpi("TAC — transactions", f'{d["valeur"]:,.0f}'.replace(",", " "), delta_texte, d["statut"])

groupe_titre("Marges")
col1, col2 = st.columns(2)
for col, nom in zip([col1, col2], ["Marge P&L", "Marge TH"]):
    with col:
        d = kpi[nom]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
                f'vs {mois_n1_texte(mois_actuel)} ({d["valeur_n1"]:.1f}%)'
            )
        carte_kpi(
            nom, f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
            texte_seuil(nom), d["statut"],
        )

groupe_titre("Coûts produits")
noms_couts = ["QCR", "Pertes", "Écart de rendement", "Bulk", "Repas employés", "Taux de remboursement"]
# Trois cartes par ligne, puis retour à la ligne (au lieu de tout caser sur une seule rangée)
for debut in range(0, len(noms_couts), 3):
    colonnes = st.columns(3)
    for col, nom in zip(colonnes, noms_couts[debut:debut + 3]):
        with col:
            d = kpi[nom]
            delta_texte = None
            if d["delta_n1_points"] is not None:
                delta_texte = (
                    f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.2f} pts '
                    f'vs {mois_n1_texte(mois_actuel)}'
                )
            carte_kpi(
                nom, f'{d["valeur"]:.2f}%', delta_texte, d.get("tendance_n1"),
                texte_seuil(nom), d["statut"],
            )

# --- GRAPHIQUES D'ÉVOLUTION ---
annee_courante = mois_actuel.year
section_eyebrow(f"Évolution — Ventes — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

serie_actuelle = calculer_serie_annuelle(df, annee_courante)
serie_precedente = calculer_serie_annuelle(df, annee_courante - 1)


def graphique_ligne(titre: str, colonne: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=abrege_mois_fr(serie_actuelle["Mois"]),
        y=serie_actuelle[colonne],
        mode="lines+markers",
        name=str(annee_courante),
        line=dict(color="#818cf8", width=3),
    ))
    if not serie_precedente.empty:
        fig.add_trace(go.Scatter(
            x=abrege_mois_fr(serie_precedente["Mois"]),
            y=serie_precedente[colonne],
            mode="lines",
            name=str(annee_courante - 1),
            line=dict(color="#71717a", width=2, dash="dash"),
        ))
    fig.update_layout(
        title=dict(text=titre, x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=300,
        margin=dict(l=10, r=10, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=11)),
    )
    return fig


col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        graphique_ligne(f"CA mensuel (k€) — {annee_courante} vs {annee_courante - 1}", "CA"),
        use_container_width=True, config={"displayModeBar": False},
    )
with col2:
    st.plotly_chart(
        graphique_ligne(f"TAC — transactions mensuelles — {annee_courante} vs {annee_courante - 1}", "TAC"),
        use_container_width=True, config={"displayModeBar": False},
    )

groupe_titre("Coûts")


def graphique_barres(titre: str, colonne: str, colonne_statut: str, seuil: float, unite: str = "", format_texte: str = "%{y:.0f}"):
    couleurs = [
        COULEURS_DELTA.get(s, COULEURS_DELTA["neutre"])
        for s in serie_actuelle[colonne_statut]
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=abrege_mois_fr(serie_actuelle["Mois"]),
        y=serie_actuelle[colonne],
        marker_color=couleurs,
        texttemplate=format_texte,
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_hline(
        y=seuil, line_dash="dash", line_color="#eab308",
        annotation_text=f"{seuil}{unite}", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text=titre, x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=300,
        margin=dict(l=10, r=10, t=55, b=40),
        showlegend=False,
    )
    return fig


col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        graphique_barres("Coût de la hub (€)", "Coût de la hub", "Coût de la hub_statut", 4000, " €", "%{y:.0f} €"),
        use_container_width=True, config={"displayModeBar": False},
    )
with col2:
    st.plotly_chart(
        graphique_barres("Taux modif. commandes (%)", "Taux modif commandes", "Taux modif commandes_statut", 10, "%", "%{y:.0f}%"),
        use_container_width=True, config={"displayModeBar": False},
    )

# --- TABLEAU RÉCAPITULATIF ANNUEL ---
section_eyebrow(f"Récapitulatif — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

colonnes_recap = ["CA", "TAC", "Marge P&L", "Marge TH", "QCR", "Pertes", "Écart de rendement", "Bulk", "Repas employés", "Taux de remboursement"]

# En-têtes abrégés pour un tableau plus compact, comme sur la maquette
ENTETES_ABREGEES = {
    "CA": "CA",
    "TAC": "TAC",
    "Marge P&L": "M. P&L",
    "Marge TH": "M. TH",
    "QCR": "QCR",
    "Pertes": "Pertes",
    "Écart de rendement": "E/R",
    "Bulk": "Bulk",
    "Repas employés": "Rep. emp.",
    "Taux de remboursement": "Rembours.",
}

# Nombre de décimales par colonne (le Taux de remboursement a des valeurs
# très petites, ex: 0,015% — 1 seule décimale les afficherait comme "0,0%")
DECIMALES_PAR_COLONNE = {
    "Marge P&L": 1, "Marge TH": 1,
    "QCR": 1, "Pertes": 2, "Écart de rendement": 2,
    "Bulk": 1, "Repas employés": 2, "Taux de remboursement": 3,
}


def formater_valeur_francaise(valeur: float, decimales: int) -> str:
    """Formate un nombre en français : virgule décimale au lieu du point."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def construire_tableau_html(serie, colonnes, annee) -> str:
    # Index rapide : numéro du mois (1-12) -> ligne de données correspondante
    serie_par_mois = {int(ligne["Mois"].month): ligne for _, ligne in serie.iterrows()}

    lignes_html = ""
    for numero_mois in range(1, 13):
        nom_mois = MOIS_ABREGE_FR[numero_mois - 1]

        if numero_mois in serie_par_mois:
            ligne = serie_par_mois[numero_mois]
            lignes_html += (
                f'<tr><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE};">{nom_mois}</td>'
            )
            for col in colonnes:
                valeur = ligne[col]
                statut_col = f"{col}_statut"

                if col == "CA":
                    texte_valeur = f'{valeur / 1000:,.0f} k€'.replace(",", " ")
                    lignes_html += f'<td style="padding:8px; color:{COULEUR_TEXTE};">{texte_valeur}</td>'
                elif statut_col in serie.columns:
                    decimales = DECIMALES_PAR_COLONNE.get(col, 2)
                    texte_valeur = f"{formater_valeur_francaise(valeur, decimales)}%"
                    statut = ligne[statut_col]
                    lignes_html += f'<td style="padding:8px;">{badge_html(texte_valeur, statut)}</td>'
                else:
                    texte_valeur = f'{valeur:,.0f}'.replace(",", " ")
                    lignes_html += f'<td style="padding:8px; color:{COULEUR_TEXTE};">{texte_valeur}</td>'
            lignes_html += "</tr>"
        else:
            # Mois pas encore archivé : tirets sur toute la ligne
            cellules_vides = "".join(
                f'<td style="padding:8px; color:{COULEUR_TEXTE_SECONDAIRE};">—</td>' for _ in colonnes
            )
            lignes_html += (
                f'<tr><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE_SECONDAIRE};">'
                f'{nom_mois}</td>{cellules_vides}</tr>'
            )

    entetes = "".join(
        f'<th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; '
        f'font-size:13px; font-weight:600;">{ENTETES_ABREGEES.get(c, c)}</th>'
        for c in colonnes
    )
    return f"""
    <div class="carte-graphique tableau-recap" style="padding-bottom:16px;">
    <table>
        <tr><th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600;">Mois</th>{entetes}</tr>
        {lignes_html}
    </table>
    </div>
    """


st.markdown(
    construire_tableau_html(serie_actuelle, colonnes_recap, annee_courante),
    unsafe_allow_html=True,
)