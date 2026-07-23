"""
dashboard/pages/4_Polyvalence.py

Page Polyvalence : cartes KPI du mois (effectif, taux global, poste le
mieux/le moins maîtrisé), radar + classement des 10 postes sur le mois
sélectionné, évolution annuelle du taux global. Pas de tableau
récapitulatif sur cette page (décision de Bastien).
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
    appliquer_style, COULEURS_DELTA, COULEUR_CARTE, COULEUR_CARTE_BORDURE,
    COULEUR_TEXTE, COULEUR_TEXTE_SECONDAIRE, selecteur_mois, section_eyebrow,
    groupe_titre, formater_mois, formater_mois_n1,
)
from sidebar import construire_sidebar
from src.kpi.polyvalence import (
    charger_donnees_polyvalence, calculer_kpi_polyvalence, calculer_serie_annuelle,
    POSTES, LIBELLES_POSTES, SEUIL_POLYVALENCE,
)
from src.kpi.utils import calculer_delta, statut_tendance

st.set_page_config(page_title="Polyvalence — Dashboard McDo", page_icon="🔄", layout="wide")
appliquer_style()
construire_sidebar("polyvalence")

df = charger_donnees_polyvalence()

# --- SÉLECTEUR DE MOIS (persistant entre les pages) ---
mois_selectionne = selecteur_mois(df, "Polyvalence")

resultats = calculer_kpi_polyvalence(df, mois=mois_selectionne)
mois_actuel = resultats["mois"]
taux_global = resultats["taux_global"]
postes = resultats["postes"]
nombre_equipiers = resultats["nombre_equipiers"]
poste_mieux_maitrise = resultats["poste_mieux_maitrise"]
poste_moins_maitrise = resultats["poste_moins_maitrise"]

sens_poly, seuil_poly = SEUIL_POLYVALENCE


def fleche_delta(valeur_delta) -> str:
    if valeur_delta is None:
        return ""
    return "▲" if valeur_delta > 0 else ("▼" if valeur_delta < 0 else "→")


# Couleurs des cartes "mise en avant" (fond plein, pas le style carte-kpi
# habituel à fond sombre + badge) — variante propre à cette page, pour
# coller à la maquette (cartes Équipiers / Polyvalence générale / Poste +
# / Poste -)
FONDS_CARTE_POLY = {
    "vert": "#1c5c46",
    "rouge": "#6b2020",
    "neutre": COULEUR_CARTE,
}
BORDURES_CARTE_POLY = {
    "vert": "#2f8c68",
    "rouge": "#a33a3a",
    "neutre": COULEUR_CARTE_BORDURE,
}


def carte_polyvalence(titre: str, valeur: str, sous_titre: str = None, delta_texte: str = None, delta_couleur: str = None, statut: str = "neutre"):
    """Carte KPI à fond plein (vert/rouge) ou normal (neutre), variante
    locale à cette page — distincte de style.carte_kpi() qui reste à fond
    sombre + badge. `statut` pilote le fond de la carte ; `delta_couleur`
    pilote la couleur du texte de delta indépendamment (utile quand la
    carte reste neutre mais qu'on veut quand même colorer la tendance)."""
    fond = FONDS_CARTE_POLY.get(statut, COULEUR_CARTE)
    bordure = BORDURES_CARTE_POLY.get(statut, COULEUR_CARTE_BORDURE)
    colore = statut in ("vert", "rouge")

    couleur_titre = "rgba(255,255,255,0.75)" if colore else COULEUR_TEXTE_SECONDAIRE
    couleur_valeur = "#ffffff" if colore else COULEUR_TEXTE
    couleur_sous_titre = "rgba(255,255,255,0.65)" if colore else COULEUR_TEXTE_SECONDAIRE
    if colore:
        couleur_delta = "#bbf7d0" if statut == "vert" else "#fecaca"
    else:
        couleur_delta = COULEURS_DELTA.get(delta_couleur, COULEURS_DELTA["neutre"])

    html = (
        f'<div class="carte-poly" style="background-color:{fond}; border:1px solid {bordure}; '
        f'border-radius:12px; padding:20px; margin-bottom:12px; box-sizing:border-box;">'
        f'<div style="color:{couleur_titre}; font-size:13px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:0.03em; margin-bottom:10px;">{titre}</div>'
        f'<div style="color:{couleur_valeur}; font-size:28px; font-weight:700; line-height:1.2; margin-bottom:6px;">{valeur}</div>'
    )
    if sous_titre:
        html += f'<div style="color:{couleur_sous_titre}; font-size:13px; margin-bottom:4px;">{sous_titre}</div>'
    if delta_texte:
        html += f'<div style="color:{couleur_delta}; font-size:13px;">{delta_texte}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# --- KPI DU MOIS ---
section_eyebrow("KPI du mois")
groupe_titre("Effectif et taux de maîtrise")

with st.container(key="poly_kpi_mois"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        carte_polyvalence("Équipiers", str(int(nombre_equipiers)), "effectif total", statut="neutre")

    with col2:
        # Comparaison au MOIS PRÉCÉDENT (pas N-1), à la demande de Bastien —
        # recalcul local, ne change pas src/kpi/polyvalence.py. Carte laissée
        # en neutre (pas de fond coloré), sans sous-titre.
        delta_mensuel = calculer_delta(df, "Taux de polyvalence", mois_actuel, pd.DateOffset(months=1))
        delta_texte = None
        tendance_mensuelle = "non disponible"
        if delta_mensuel is not None:
            pts = delta_mensuel["delta_points"]
            mois_precedent = mois_actuel - pd.DateOffset(months=1)
            delta_texte = f'{fleche_delta(pts)} {pts:+.1f} pts vs {formater_mois(mois_precedent).lower()}'
            tendance_mensuelle = statut_tendance(pts, sens_poly)
        carte_polyvalence(
            "Polyvalence générale", f'{taux_global["valeur"]:.1f}%', None,
            delta_texte, tendance_mensuelle, statut="neutre",
        )

    with col3:
        if poste_mieux_maitrise is not None:
            d = postes[poste_mieux_maitrise]
            carte_polyvalence(
                "Poste le + maîtrisé", LIBELLES_POSTES[poste_mieux_maitrise],
                f'{d["valeur"]:.1f}% de maîtrise', statut="vert",
            )
        else:
            carte_polyvalence("Poste le + maîtrisé", "—", "aucune donnée ce mois", statut="neutre")

    with col4:
        if poste_moins_maitrise is not None:
            d = postes[poste_moins_maitrise]
            carte_polyvalence(
                "Poste le - maîtrisé", LIBELLES_POSTES[poste_moins_maitrise],
                f'{d["valeur"]:.1f}% de maîtrise', statut="rouge",
            )
        else:
            carte_polyvalence("Poste le - maîtrisé", "—", "aucune donnée ce mois", statut="neutre")

st.markdown(
    '<style>.st-key-poly_kpi_mois .carte-poly { min-height: 150px; }</style>',
    unsafe_allow_html=True,
)


# --- MAÎTRISE PAR POSTE (mois sélectionné) ---
section_eyebrow(f"Maîtrise par poste — {formater_mois(mois_actuel)}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    labels = [LIBELLES_POSTES[c] for c in POSTES]
    valeurs = [postes[c]["valeur"] for c in POSTES]
    # Ferme la boucle du radar (revient au premier point)
    labels_fermes = labels + [labels[0]]
    valeurs_fermes = valeurs + [valeurs[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valeurs_fermes, theta=labels_fermes, fill="toself",
        fillcolor="rgba(52, 211, 153, 0.25)",
        line=dict(color="#34d399", width=2),
        marker=dict(size=5, color="#34d399"),
        name="Taux actuel",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[seuil_poly] * len(labels_fermes), theta=labels_fermes, mode="lines",
        line=dict(color="#eab308", width=1.5, dash="dash"),
        name=f"Objectif {seuil_poly:g}%",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=COULEUR_CARTE,
            radialaxis=dict(range=[0, 100], showticklabels=True, tickfont=dict(size=9, color=COULEUR_TEXTE_SECONDAIRE), gridcolor=COULEUR_CARTE_BORDURE),
            angularaxis=dict(tickfont=dict(size=11, color=COULEUR_TEXTE), gridcolor=COULEUR_CARTE_BORDURE),
        ),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        height=400,
        margin=dict(l=40, r=40, t=55, b=40),
        title=dict(
            text=f"Taux de maîtrise par poste — objectif ≥ {seuil_poly:g}%",
            x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5, font=dict(size=10)),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    # Classement croissant (poste le moins maîtrisé en premier), comme sur
    # la maquette — chaque ligne : libellé + barre horizontale colorée
    # (vert/rouge selon le seuil de 45%) + valeur, avec un repère vertical
    # fixe à 45% commun à toutes les barres
    postes_valides = [(c, d) for c, d in postes.items() if pd.notna(d["valeur"])]
    postes_tries = sorted(postes_valides, key=lambda item: item[1]["valeur"])

    lignes_html = ""
    for colonne, d in postes_tries:
        libelle = LIBELLES_POSTES[colonne]
        valeur = d["valeur"]
        couleur = COULEURS_DELTA.get(d["statut"], COULEURS_DELTA["neutre"])
        largeur_pct = max(0, min(100, valeur))
        lignes_html += (
            f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">'
            f'<div style="width:80px; color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; flex-shrink:0;">{libelle}</div>'
            f'<div style="flex:1; position:relative; height:18px; background-color:{COULEUR_CARTE_BORDURE}; border-radius:4px;">'
            f'<div style="position:absolute; top:0; left:0; height:100%; width:{largeur_pct}%; background-color:{couleur}; border-radius:4px;"></div>'
            f'<div style="position:absolute; top:-2px; left:{seuil_poly}%; width:2px; height:22px; background-color:#eab308;"></div>'
            f'</div>'
            f'<div style="width:50px; text-align:right; color:{couleur}; font-weight:600; font-size:13px; flex-shrink:0;">{valeur:.1f}%</div>'
            f'</div>'
        )

    html_classement = (
        '<div class="carte-graphique" style="padding-bottom:16px; height:400px; box-sizing:border-box; overflow:auto;">'
        f'<div class="carte-titre" style="margin-bottom:14px;">Classement des postes — {formater_mois(mois_actuel)}</div>'
        f'{lignes_html}'
        f'<div style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:11px; margin-top:8px;">'
        f'Trait vertical = objectif {seuil_poly:g}%. Vert = au-dessus, rouge = en dessous.</div>'
        '</div>'
    )
    st.markdown(html_classement, unsafe_allow_html=True)


# --- ÉVOLUTION TAUX GLOBAL ---
annee_courante = mois_actuel.year
section_eyebrow(f"Évolution taux global — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

serie_actuelle = calculer_serie_annuelle(df, annee_courante)
serie_precedente = calculer_serie_annuelle(df, annee_courante - 1)

MOIS_ABREGE_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[MOIS_ABREGE_FR[m - 1] for m in serie_actuelle["Mois"].dt.month],
    y=serie_actuelle["Taux de polyvalence"],
    mode="lines+markers",
    name=str(annee_courante),
    line=dict(color="#34d399", width=3),
))
if not serie_precedente.empty:
    fig.add_trace(go.Scatter(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_precedente["Mois"].dt.month],
        y=serie_precedente["Taux de polyvalence"],
        mode="lines",
        name=str(annee_courante - 1),
        line=dict(color="#71717a", width=2, dash="dash"),
    ))
fig.add_hline(
    y=seuil_poly, line_dash="dash", line_color="#eab308",
    annotation_text=f"{seuil_poly:g}%", annotation_position="top right",
    annotation_font=dict(size=11, color="#eab308"),
)
fig.update_layout(
    title=dict(
        text=f"Taux de polyvalence global (%) — objectif ≥ {seuil_poly:g}% — {annee_courante} vs {annee_courante - 1}",
        x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE),
    ),
    template="plotly_dark",
    paper_bgcolor=COULEUR_CARTE,
    plot_bgcolor=COULEUR_CARTE,
    height=330,
    margin=dict(l=10, r=10, t=55, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=11)),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})