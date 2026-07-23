"""
dashboard/pages/3_RH.py

Page RH : cartes KPI du mois (MO FDC, MO P&L, VPHE, PAC, Turn-Over),
graphiques d'évolution main d'œuvre et tableau récapitulatif annuel.
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

from style import (
    appliquer_style, carte_kpi, badge_html, COULEURS_STATUT, COULEURS_DELTA,
    COULEUR_CARTE, COULEUR_CARTE_BORDURE, COULEUR_TEXTE, COULEUR_TEXTE_SECONDAIRE,
    titre_page, selecteur_mois, section_eyebrow, groupe_titre, MOIS_FR, MOIS_ABREGE_FR,
    formater_mois, formater_mois_n1,
)
from sidebar import construire_sidebar
from src.kpi.rh import charger_donnees_rh, calculer_kpi_rh, calculer_serie_annuelle, SEUILS_FIXES

st.set_page_config(page_title="RH — Dashboard McDo", page_icon="👥", layout="wide")
appliquer_style()
construire_sidebar("rh")

df = charger_donnees_rh()

# --- SÉLECTEUR DE MOIS (persistant entre les pages via st.session_state) ---
mois_selectionne = selecteur_mois(df, "Ressources humaines")

resultats = calculer_kpi_rh(df, mois=mois_selectionne)
mois_actuel = resultats["mois"]
kpi = resultats["kpi"]


def texte_seuil(nom_kpi: str) -> str:
    """Construit le texte du badge à partir du vrai seuil (ex: 'Objectif : ≤ 9%').
    VPHE est en €, tous les autres KPI RH sont des %. Toujours en <= ou >=
    (jamais < ou >), cohérent avec la logique inclusive de statut_seuil_fixe()
    (max -> valeur <= seuil, min -> valeur >= seuil)."""
    sens, seuil = SEUILS_FIXES[nom_kpi]
    symbole = "≤" if sens == "max" else "≥"
    unite = " €" if nom_kpi == "VPHE" else "%"
    return f"Objectif : {symbole} {seuil:g}{unite}"


def fleche_delta(valeur_delta) -> str:
    if valeur_delta is None:
        return ""
    return "▲" if valeur_delta > 0 else ("▼" if valeur_delta < 0 else "→")


# --- KPI DU MOIS ---
section_eyebrow("KPI du mois")

# Conteneur clé pour forcer les 5 cartes à la même hauteur : MO FDC et
# MO P&L ont une ligne de delta en plus (vs VPHE/PAC/Turn-Over qui n'en
# ont pas), donc sans ce correctif elles seraient plus hautes que les 3
# autres — cf. .carte-kpi { min-height } scopé ci-dessous.
with st.container(key="rh_kpi_mois"):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        d = kpi["MO FDC"]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
                f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.1f}%)'
            )
        carte_kpi(
            "MO FDC", f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
            texte_seuil("MO FDC"), d["statut"],
        )

    with col2:
        d = kpi["MO P&L"]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
                f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.1f}%)'
            )
        carte_kpi(
            "MO P&L", f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
            texte_seuil("MO P&L"), d["statut"],
        )

    with col3:
        # VPHE en € (vente par heure employé) — delta en € (pas en "pts",
        # qui n'a pas de sens pour un montant)
        d = kpi["VPHE"]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} € '
                f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.1f} €)'
            )
        carte_kpi(
            "VPHE", f'{d["valeur"]:.1f} €', delta_texte, d.get("tendance_n1"),
            texte_seuil("VPHE"), d["statut"],
        )

    with col4:
        d = kpi["PAC"]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
                f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.1f}%)'
            )
        carte_kpi(
            "PAC", f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
            texte_seuil("PAC"), d["statut"],
        )

    with col5:
        d = kpi["Turn-Over"]
        delta_texte = None
        if d["delta_n1_points"] is not None:
            delta_texte = (
                f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
                f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.1f}%)'
            )
        carte_kpi(
            "Turn-Over", f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
            texte_seuil("Turn-Over"), d["statut"],
        )

st.markdown(
    '<style>.st-key-rh_kpi_mois .carte-kpi { min-height: 165px; box-sizing: border-box; }</style>',
    unsafe_allow_html=True,
)


# --- ÉVOLUTION MAIN D'ŒUVRE ---
annee_courante = mois_actuel.year
section_eyebrow(f"Évolution main d'œuvre — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

serie_actuelle = calculer_serie_annuelle(df, annee_courante)
serie_precedente = calculer_serie_annuelle(df, annee_courante - 1)


def graphique_ligne_seuil(titre: str, colonne: str, seuil: float, unite: str, couleur_ligne: str, plage_y: tuple = None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_actuelle["Mois"].dt.month],
        y=serie_actuelle[colonne],
        mode="lines+markers",
        name=str(annee_courante),
        line=dict(color=couleur_ligne, width=3),
    ))
    if not serie_precedente.empty:
        fig.add_trace(go.Scatter(
            x=[MOIS_ABREGE_FR[m - 1] for m in serie_precedente["Mois"].dt.month],
            y=serie_precedente[colonne],
            mode="lines",
            name=str(annee_courante - 1),
            line=dict(color=couleur_ligne, width=2, dash="dash"),
            opacity=0.6,
        ))
    fig.add_hline(
        y=seuil, line_dash="dash", line_color="#eab308",
        annotation_text=f"{seuil:g}{unite}", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text=titre, x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=330,
        margin=dict(l=10, r=10, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=11)),
    )
    if plage_y is not None:
        fig.update_layout(yaxis=dict(range=list(plage_y)))
    return fig


col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        graphique_ligne_seuil(
            f"MO FDC (%) — objectif ≤ 9% — {annee_courante} vs {annee_courante - 1}",
            "MO FDC", 9, "%", "#f472b6", plage_y=(4, 14),
        ),
        use_container_width=True, config={"displayModeBar": False},
    )
with col2:
    st.plotly_chart(
        graphique_ligne_seuil(
            f"MO P&L (%) — objectif ≤ 12% — {annee_courante} vs {annee_courante - 1}",
            "MO P&L", 12, "%", "#ec4899", plage_y=(8, 18),
        ),
        use_container_width=True, config={"displayModeBar": False},
    )


# --- VPHE, PAC & TURN-OVER ---
groupe_titre(f"VPHE, PAC & Turn-Over — Année {annee_courante}")

col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(
        graphique_ligne_seuil(
            f"VPHE (€) — objectif ≥ 85€ — {annee_courante} vs {annee_courante - 1}",
            "VPHE", 85, " €", "#818cf8", plage_y=(40, 130),
        ),
        use_container_width=True, config={"displayModeBar": False},
    )

with col2:
    # On ne garde que les mois où PAC est réellement renseigné, sinon les
    # lignes vides (mois pas encore saisis) affichent une barre fantôme
    # avec le texte "NaN%" au-dessus
    serie_pac = serie_actuelle[serie_actuelle["PAC"].notna()]
    couleurs = [COULEURS_DELTA.get(s, COULEURS_DELTA["neutre"]) for s in serie_pac["PAC_statut"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_pac["Mois"].dt.month],
        y=serie_pac["PAC"],
        marker_color=couleurs,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_hline(
        y=36, line_dash="dash", line_color="#eab308",
        annotation_text="36%", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text="PAC (%) — objectif ≤ 36%", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=330,
        margin=dict(l=10, r=10, t=55, b=40),
        showlegend=False,
        yaxis=dict(range=[0, 42]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col3:
    # Même filtre que PAC : on ignore les mois pas encore saisis pour
    # éviter les barres fantômes avec "NaN%"
    serie_to = serie_actuelle[serie_actuelle["Turn-Over"].notna()]
    couleurs = [COULEURS_DELTA.get(s, COULEURS_DELTA["neutre"]) for s in serie_to["Turn-Over_statut"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_to["Mois"].dt.month],
        y=serie_to["Turn-Over"],
        marker_color=couleurs,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_hline(
        y=5, line_dash="dash", line_color="#eab308",
        annotation_text="5%", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text="Turn-Over (%) — objectif ≤ 5%", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=330,
        margin=dict(l=10, r=10, t=55, b=40),
        showlegend=False,
        yaxis=dict(range=[0, 8]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# --- TABLEAU RÉCAPITULATIF ANNUEL ---
section_eyebrow(f"Récapitulatif — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

colonnes_recap = ["MO FDC", "MO P&L", "VPHE", "PAC", "Turn-Over"]

ENTETES_ABREGEES_RH = {
    "MO FDC": "MO FDC",
    "MO P&L": "MO P&L",
    "VPHE": "VPHE",
    "PAC": "PAC",
    "Turn-Over": "Turn-Over",
}

DECIMALES_RH = {
    "MO FDC": 1, "MO P&L": 1, "VPHE": 1, "PAC": 1, "Turn-Over": 1,
}


def formater_valeur_francaise(valeur, decimales) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",")


def construire_tableau_rh(serie, colonnes, annee) -> str:
    serie_par_mois = {int(ligne["Mois"].month): ligne for _, ligne in serie.iterrows()}

    lignes_html = ""
    for numero_mois in range(1, 13):
        nom_mois = MOIS_ABREGE_FR[numero_mois - 1]

        if numero_mois in serie_par_mois:
            ligne = serie_par_mois[numero_mois]
            lignes_html += f'<tr><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE};">{nom_mois}</td>'
            for col in colonnes:
                valeur = ligne[col]
                statut_col = f"{col}_statut"
                decimales = DECIMALES_RH.get(col, 1)
                unite = " €" if col == "VPHE" else "%"
                texte_valeur = f"{formater_valeur_francaise(valeur, decimales)}{unite}"
                if statut_col in serie.columns:
                    statut = ligne[statut_col]
                    lignes_html += f'<td style="padding:8px;">{badge_html(texte_valeur, statut)}</td>'
                else:
                    lignes_html += f'<td style="padding:8px; color:{COULEUR_TEXTE};">{texte_valeur}</td>'
            lignes_html += "</tr>"
        else:
            cellules_vides = "".join(
                f'<td style="padding:8px; color:{COULEUR_TEXTE_SECONDAIRE};">—</td>' for _ in colonnes
            )
            lignes_html += (
                f'<tr><td style="padding:8px; font-weight:600; color:{COULEUR_TEXTE_SECONDAIRE};">'
                f'{nom_mois}</td>{cellules_vides}</tr>'
            )

    entetes = "".join(
        f'<th style="padding:8px; text-align:left; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; font-weight:600;">'
        f'{ENTETES_ABREGEES_RH.get(c, c)}</th>'
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


st.markdown(construire_tableau_rh(serie_actuelle, colonnes_recap, annee_courante), unsafe_allow_html=True)