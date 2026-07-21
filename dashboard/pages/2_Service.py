"""
dashboard/pages/2_Service.py

Page Service : cartes KPI du mois, graphiques d'évolution des temps de
service, répartition des canaux, satisfaction et conformité opérationnelle.
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
    titre_page, section_eyebrow, groupe_titre, MOIS_FR, MOIS_ABREGE_FR,
    formater_mois, formater_mois_n1,
)
from sidebar import construire_sidebar
from src.kpi.service import charger_donnees_service, calculer_kpi_service, calculer_serie_annuelle, SEUILS_FIXES
from src.kpi.utils import calculer_delta, statut_tendance

st.set_page_config(page_title="Service — Dashboard McDo", page_icon="🕐", layout="wide")
appliquer_style()
construire_sidebar("service")

df = charger_donnees_service()

# --- SÉLECTEUR DE MOIS (identique à Business) ---
mois_disponibles = sorted(df["Mois"].dropna().unique(), reverse=True)
mois_disponibles = [pd.Timestamp(m) for m in mois_disponibles]
options_mois = {formater_mois(m): m for m in mois_disponibles}

col_titre, col_selecteur = st.columns([5, 1])
with col_titre:
    titre_page("Service")
with col_selecteur:
    st.write("")
    mois_choisi_label = st.selectbox(
        "Mois", options=list(options_mois.keys()), index=0, label_visibility="collapsed"
    )
mois_selectionne = options_mois[mois_choisi_label]

resultats = calculer_kpi_service(df, mois=mois_selectionne)
mois_actuel = resultats["mois"]
kpi = resultats["kpi"]
mix_canaux = resultats["mix_canaux"]


def texte_seuil(nom_kpi: str, unite: str = "") -> str:
    """Construit le texte du badge à partir du vrai seuil (ex: 'Objectif : < 300s')."""
    sens, seuil = SEUILS_FIXES[nom_kpi]
    symbole = "<" if sens == "max" else "≥"
    return f"Objectif : {symbole} {seuil:g}{unite}"


def fleche_delta(valeur_delta) -> str:
    if valeur_delta is None:
        return ""
    return "▲" if valeur_delta > 0 else ("▼" if valeur_delta < 0 else "→")


# --- KPI DU MOIS ---
section_eyebrow("KPI du mois")
groupe_titre("Temps de service et satisfaction")

col1, col2, col3, col4 = st.columns(4)

with col1:
    d = kpi["Temps de service R2P comptoir"]
    delta_texte = None
    if d["delta_n1_points"] is not None:
        delta_texte = (
            f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.0f} s '
            f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.0f} s)'
        )
    carte_kpi(
        "R2P comptoir", f'{d["valeur"]:.0f} s', delta_texte, d.get("tendance_n1"),
        texte_seuil("Temps de service R2P comptoir", "s"), d["statut"],
    )

with col2:
    d = kpi["Temps de service OEPE drive"]
    delta_texte = None
    if d["delta_n1_points"] is not None:
        delta_texte = (
            f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.0f} s '
            f'vs {formater_mois_n1(mois_actuel)} ({d["valeur_n1"]:.0f} s)'
        )
    carte_kpi(
        "OEPE drive", f'{d["valeur"]:.0f} s', delta_texte, d.get("tendance_n1"),
        texte_seuil("Temps de service OEPE drive", "s"), d["statut"],
    )

with col3:
    d = kpi["McDo&Moi"]
    delta_texte = None
    if d["delta_n1_points"] is not None:
        delta_texte = (
            f'{fleche_delta(d["delta_n1_points"])} {d["delta_n1_points"]:+.1f} pts '
            f'vs {formater_mois_n1(mois_actuel)}'
        )
    carte_kpi(
        "McDo&Moi", f'{d["valeur"]:.1f}%', delta_texte, d.get("tendance_n1"),
        texte_seuil("McDo&Moi", "%"), d["statut"],
    )

with col4:
    d = kpi["Note Google"]
    # Comparaison au MOIS PRÉCÉDENT pour ce KPI (pas N-1 comme les autres),
    # à la demande de Bastien — recalcul local, ne change pas service.py
    delta_note = calculer_delta(df, "Note Google", mois_actuel, pd.DateOffset(months=1))
    delta_texte = None
    tendance_mensuelle = "non disponible"
    if delta_note is not None:
        pts = delta_note["delta_points"]
        unite_point = "point" if abs(round(pts, 1)) <= 1 else "points"
        mois_precedent = mois_actuel - pd.DateOffset(months=1)
        delta_texte = f'{fleche_delta(pts)} {pts:+.1f} {unite_point} vs {formater_mois(mois_precedent).lower()}'
        tendance_mensuelle = statut_tendance(pts, "min")
    carte_kpi(
        "Note Google", f'{d["valeur"]:.1f} / 5', delta_texte, tendance_mensuelle,
        texte_seuil("Note Google"), d["statut"],
    )


# --- ÉVOLUTION TEMPS DE SERVICE ---
annee_courante = mois_actuel.year
section_eyebrow(f"Évolution temps de service — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

serie_actuelle = calculer_serie_annuelle(df, annee_courante)
serie_precedente = calculer_serie_annuelle(df, annee_courante - 1)


def graphique_ligne_seuil(titre: str, colonne: str, seuil: float, unite: str, couleur_ligne: str):
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
        height=300,
        margin=dict(l=10, r=10, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=11)),
    )
    return fig


col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        graphique_ligne_seuil(
            f"R2P comptoir (s) — {annee_courante} vs {annee_courante - 1}",
            "Temps de service R2P comptoir", 300, "s", "#818cf8",
        ),
        use_container_width=True, config={"displayModeBar": False},
    )
with col2:
    st.plotly_chart(
        graphique_ligne_seuil(
            f"OEPE drive (s) — {annee_courante} vs {annee_courante - 1}",
            "Temps de service OEPE drive", 300, "s", "#38bdf8",
        ),
        use_container_width=True, config={"displayModeBar": False},
    )


# --- RÉPARTITION & SATISFACTION ---
groupe_titre("Répartition & satisfaction")

col1, col2, col3 = st.columns(3)

COULEURS_CANAUX = {
    "% Comptoir": "#a1a1aa",
    "% Drive": "#818cf8",
    "% LAD": "#34d399",
    "% Click & Collect": "#eab308",
}
NOMS_CANAUX = {
    "% Comptoir": "Comptoir",
    "% Drive": "Drive",
    "% LAD": "Uber Eats",
    "% Click & Collect": "Click & Collect",
}

with col1:
    fig = go.Figure(data=[go.Pie(
        labels=[NOMS_CANAUX[c] for c in mix_canaux],
        values=list(mix_canaux.values()),
        hole=0.6,
        marker=dict(colors=[COULEURS_CANAUX[c] for c in mix_canaux]),
        textinfo="none",
        showlegend=False,
        hovertemplate="%{label} : %{value:.0f}%<extra></extra>",
    )])
    fig.update_layout(
        title=dict(text=f"Mix canaux — {formater_mois(mois_actuel)}", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=250,
        margin=dict(l=10, r=10, t=55, b=10),
    )

    with st.container(key="mix_canaux_bloc"):
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Hauteur fixée en dur (et non via flex/% qui ne traverse pas les
        # wrappers imbriqués de Streamlit) pour que donut (250px) + légende
        # totalisent exactement 420px, comme les cartes Anniversaires et
        # Note Google — donc alignées en bas également, pas seulement en haut.
        HAUTEUR_LEGENDE_MIX_CANAUX = 170
        legende_html = (
            f'<div style="background-color:{COULEUR_CARTE}; '
            f'border-left:1px solid {COULEUR_CARTE_BORDURE}; border-right:1px solid {COULEUR_CARTE_BORDURE}; '
            f'border-bottom:1px solid {COULEUR_CARTE_BORDURE}; border-top:none; '
            f'border-radius: 0 0 12px 12px; padding:16px; position:relative; z-index:2; '
            f'height:{HAUTEUR_LEGENDE_MIX_CANAUX}px; display:flex; flex-direction:column; '
            f'justify-content:center; box-sizing:border-box;">'
        )
        for colonne, valeur in mix_canaux.items():
            legende_html += (
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">'
                f'<span style="width:10px; height:10px; border-radius:50%; background-color:{COULEURS_CANAUX[colonne]}; display:inline-block;"></span>'
                f'<span style="color:{COULEUR_TEXTE_SECONDAIRE}; flex:1;">{NOMS_CANAUX[colonne]}</span>'
                f'<span style="color:{COULEUR_TEXTE}; font-weight:600;">{valeur:.0f}%</span>'
                f'</div>'
            )
        legende_html += "</div>"
        st.markdown(legende_html, unsafe_allow_html=True)

    # Le conteneur devient une colonne flex de hauteur fixe (420px, alignée
    # sur les cartes Anniversaires et Note Google). Le gap reste à 0 (plus
    # besoin de marge négative pour recoller les deux blocs, cf. correctif
    # précédent) et le bloc légende s'étire (flex:1) pour occuper l'espace
    # restant sous le donut, en centrant ses lignes verticalement.
    st.markdown(
        '<style>'
        '.st-key-mix_canaux_bloc { gap: 0 !important; }'
        '.st-key-mix_canaux_bloc [data-testid="stElementContainer"] { margin: 0 !important; padding: 0 !important; }'
        # Surcharge locale du cadre global des graphiques Plotly (défini dans
        # style.py) : ici seulement, on retire l'arrondi et la bordure du bas
        # du donut pour qu'il se prolonge sans coupure dans la légende juste
        # en dessous (qui, elle, n'a pas de bordure du haut — cf plus haut).
        # La hauteur de 420px (alignée sur Anniversaires et Note Google) est
        # obtenue en fixant la hauteur de la légende en dur juste au-dessus,
        # pas via flex — donut (250px) + légende (170px) = 420px.
        '.st-key-mix_canaux_bloc [data-testid="stPlotlyChart"] { '
        '    border-radius: 12px 12px 0 0 !important; border-bottom: none !important; '
        '}'
        '</style>',
        unsafe_allow_html=True,
    )

with col2:
    serie_anniv = serie_actuelle[["Mois", "Anniversaires", "Anniversaires_statut"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=serie_anniv["Anniversaires"],
        y=[MOIS_ABREGE_FR[m - 1] for m in serie_anniv["Mois"].dt.month],
        orientation="h",
        marker_color=[COULEURS_DELTA.get(s, COULEURS_DELTA["neutre"]) for s in serie_anniv["Anniversaires_statut"]],
        text=serie_anniv["Anniversaires"],
        textposition="outside",
        width=0.5,  # barres plus fines
    ))
    fig.add_vline(x=4, line_dash="dash", line_color="#eab308")
    fig.update_layout(
        title=dict(text="Anniversaires / mois — objectif ≥ 4", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=420,  # même hauteur que la carte Note Google
        margin=dict(l=10, r=10, t=55, b=10),
        showlegend=False,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[0, 8]),
        bargap=0.4,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col3:
    d_avis = kpi["Nombre d'avis Google"]
    note = kpi["Note Google"]["valeur"]
    nb_etoiles_pleines = round(note)

    etoiles_html = ""
    for i in range(5):
        couleur = "#eab308" if i < nb_etoiles_pleines else "#3f3f46"
        etoiles_html += f'<span style="color:{couleur}; font-size:24px;">★</span>'

    delta_avis_texte = ""
    if d_avis["delta_mois_precedent"] is not None:
        fleche = fleche_delta(d_avis["delta_mois_precedent"])
        couleur_delta = COULEURS_DELTA["vert"] if d_avis["delta_mois_precedent"] >= 0 else COULEURS_DELTA["rouge"]
        mois_precedent_avis = mois_actuel - pd.DateOffset(months=1)
        delta_avis_texte = (
            f'<div style="color:{couleur_delta}; font-size:13px; margin-top:8px;">'
            f'{fleche} {d_avis["delta_mois_precedent"]:+.0f} vs {formater_mois(mois_precedent_avis).lower()} ({d_avis["valeur_mois_precedent"]:.0f})</div>'
        )

    sens_note, seuil_note = SEUILS_FIXES["Note Google"]
    html = (
        '<div class="carte-kpi" style="min-height:420px; display:flex; flex-direction:column;">'
        f'<div class="carte-titre">Note & avis Google — {formater_mois(mois_actuel)}</div>'
        '<div style="text-align:center; margin-top:12px;">'
        f'<div class="carte-valeur" style="font-size:42px;">{note:.1f}</div>'
        f'<div style="margin-bottom:12px;">{etoiles_html}</div>'
        '</div>'
        f'<div style="text-align:center;">{badge_html(f"Objectif : ≥ {seuil_note:g} / 5", kpi["Note Google"]["statut"])}</div>'
        f'<hr style="margin:20px 0; border-color:{COULEUR_CARTE_BORDURE};">'
        '<div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">'
        '<div style="color:#a1a1aa; font-size:13px;">Avis reçus ce mois</div>'
        f'<div style="font-size:22px; font-weight:700; color:{COULEUR_TEXTE};">{d_avis["valeur"]:.0f}</div>'
        f'{delta_avis_texte}'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# --- CONFORMITÉ OPÉRATIONNELLE ---
groupe_titre("Conformité opérationnelle")

col1, col2 = st.columns(2)

with col1:
    couleurs = [COULEURS_DELTA.get(s, COULEURS_DELTA["neutre"]) for s in serie_actuelle["Big forced_statut"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_actuelle["Mois"].dt.month],
        y=serie_actuelle["Big forced"],
        marker_color=couleurs,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_hline(
        y=20, line_dash="dash", line_color="#eab308",
        annotation_text="20%", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text="Big forced (%) — objectif < 20%", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=300,
        margin=dict(l=10, r=10, t=55, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[MOIS_ABREGE_FR[m - 1] for m in serie_actuelle["Mois"].dt.month],
        y=serie_actuelle["Rapport balance"],
        mode="lines+markers",
        line=dict(color="#34d399", width=3),
        showlegend=False,
    ))
    fig.add_hline(
        y=98, line_dash="dash", line_color="#eab308",
        annotation_text="98%", annotation_position="top right",
        annotation_font=dict(size=11, color="#eab308"),
    )
    fig.update_layout(
        title=dict(text="Rapport balance (%) — objectif ≥ 98%", x=0.02, xanchor="left", font=dict(size=14, color=COULEUR_TEXTE)),
        template="plotly_dark",
        paper_bgcolor=COULEUR_CARTE,
        plot_bgcolor=COULEUR_CARTE,
        height=300,
        margin=dict(l=10, r=10, t=55, b=40),
        yaxis=dict(range=[90, 100]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# --- TABLEAU RÉCAPITULATIF ANNUEL ---
section_eyebrow(f"Récapitulatif — Année {annee_courante}")
st.markdown(f'<hr style="margin:4px 0 20px 0; border-color:{COULEUR_CARTE_BORDURE};">', unsafe_allow_html=True)

colonnes_recap = [
    "Temps de service R2P comptoir", "Temps de service OEPE drive",
    "% Comptoir", "% Drive", "% LAD", "% Click & Collect",
    "McDo&Moi", "Rapport balance", "Big forced", "Anniversaires", "Note Google",
]

ENTETES_ABREGEES_SERVICE = {
    "Temps de service R2P comptoir": "R2P (s)",
    "Temps de service OEPE drive": "OEPE (s)",
    "% Comptoir": "Comptoir",
    "% Drive": "Drive",
    "% LAD": "Uber",
    "% Click & Collect": "C&C",
    "McDo&Moi": "McDo&Moi",
    "Rapport balance": "Balance",
    "Big forced": "Big forced",
    "Anniversaires": "Anniv.",
    "Note Google": "Google",
}

DECIMALES_SERVICE = {
    "Temps de service R2P comptoir": 0, "Temps de service OEPE drive": 0,
    "% Comptoir": 0, "% Drive": 0, "% LAD": 0, "% Click & Collect": 0,
    "McDo&Moi": 1, "Rapport balance": 1, "Big forced": 1,
    "Anniversaires": 0, "Note Google": 1,
}


def formater_valeur_francaise(valeur, decimales) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",")


def construire_tableau_service(serie, colonnes, annee) -> str:
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
                decimales = DECIMALES_SERVICE.get(col, 1)
                if col in ("Temps de service R2P comptoir", "Temps de service OEPE drive"):
                    unite = " s"
                elif col in ("% Comptoir", "% Drive", "% LAD", "% Click & Collect", "McDo&Moi", "Rapport balance", "Big forced"):
                    unite = "%"
                else:
                    unite = ""
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
        f'{ENTETES_ABREGEES_SERVICE.get(c, c)}</th>'
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


st.markdown(construire_tableau_service(serie_actuelle, colonnes_recap, annee_courante), unsafe_allow_html=True)