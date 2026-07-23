"""
dashboard/style.py

Palette de couleurs et composants HTML réutilisables pour reproduire le
style sombre de la maquette (cartes arrondies, badges de statut colorés)
de façon cohérente sur toutes les pages du dashboard.
"""

import streamlit as st
import pandas as pd

# Palette extraite de la maquette
COULEUR_FOND = "#141413"
COULEUR_SIDEBAR = "#262624"
COULEUR_CARTE = "#262624"
COULEUR_CARTE_BORDURE = "#323238"
COULEUR_TEXTE = "#e4e4e7"
COULEUR_TEXTE_SECONDAIRE = "#a1a1aa"

# Mois en français, réutilisables sur toutes les pages (sélecteur de mois,
# axes des graphiques, tableaux récap) — évite de les redéfinir à chaque fois
MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
MOIS_ABREGE_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
]


def formater_mois(ts) -> str:
    """Formate un Timestamp en 'Mois Année' français (ex: 'Juillet 2026')."""
    return f"{MOIS_FR[ts.month - 1]} {ts.year}"


def formater_mois_n1(mois_actuel) -> str:
    """Formate le mois N-1 en minuscules pour l'affichage dans les deltas (ex: 'mai 2024')."""
    mois_n1 = mois_actuel - pd.DateOffset(years=1)
    return f"{MOIS_FR[mois_n1.month - 1].lower()} {mois_n1.year}"

# Couleurs des BADGES (pill "Objectif : ..." et cellules du tableau récap) : fond pastel + texte foncé
COULEURS_STATUT = {
    "vert": {"bg": "#eaf3de", "texte": "#2b530e"},
    "rouge": {"bg": "#fcebeb", "texte": "#761a1a"},
    "neutre": {"bg": "#27272a", "texte": "#d4d4d8"},
    "non disponible": {"bg": "#27272a", "texte": "#71717a"},
}

# Couleurs du TEXTE DE COMPARATIF (deltas "▲ +0,01 pts...") et des GRAPHIQUES
# (barres) : couleurs vives, distinctes de la palette pastel des badges
COULEURS_DELTA = {
    "vert": "#208d6a",
    "rouge": "#c74746",
    "neutre": "#d4d4d8",
    "non disponible": "#71717a",
}


def appliquer_style():
    """
    Injecte le CSS global du dashboard. À appeler une fois, en tout début
    de chaque page — juste après verifier_mot_de_passe().
    """
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {COULEUR_FOND};
        }}
        [data-testid="stHeader"] {{
            background-color: {COULEUR_FOND};
        }}
        [data-testid="stSidebar"] {{
            background-color: {COULEUR_SIDEBAR};
        }}
        .carte-kpi {{
            background-color: {COULEUR_CARTE};
            border: 1px solid {COULEUR_CARTE_BORDURE};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            height: 100%;
        }}
        .carte-titre {{
            color: {COULEUR_TEXTE_SECONDAIRE};
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }}
        .carte-valeur {{
            color: {COULEUR_TEXTE};
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 4px;
            line-height: 1.2;
        }}
        .carte-delta {{
            font-size: 13px;
            margin-bottom: 10px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }}
        .block-container {{
            padding-top: 2.5rem;
        }}
        .page-titre {{
            color: {COULEUR_TEXTE};
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .section-eyebrow {{
            color: {COULEUR_TEXTE_SECONDAIRE};
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-top: 28px;
            margin-bottom: 6px;
        }}
        .groupe-titre {{
            color: {COULEUR_TEXTE};
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            padding-bottom: 6px;
            margin-top: 16px;
            margin-bottom: 12px;
            border-bottom: 1px solid {COULEUR_CARTE_BORDURE};
        }}
        /* Sélecteur de mois : même couleur que les cartes + léger liseré blanc */
        div[data-baseweb="select"] > div {{
            background-color: {COULEUR_CARTE} !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            border-radius: 8px !important;
        }}
        .carte-graphique {{
            background-color: {COULEUR_CARTE};
            border: 1px solid {COULEUR_CARTE_BORDURE};
            border-radius: 12px;
            padding: 16px 16px 4px 16px;
            margin-bottom: 16px;
        }}
        .carte-graphique .carte-titre {{
            margin-bottom: 4px;
        }}
        /* Cadre automatique de Streamlit autour des graphiques Plotly :
           on le stylise directement plutôt que d'en rajouter un par-dessus */
        [data-testid="stPlotlyChart"] {{
            background-color: {COULEUR_CARTE};
            border: 1px solid {COULEUR_CARTE_BORDURE} !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }}
        /* Reset des bordures par défaut de Streamlit sur les tableaux HTML,
           remplacées par une hairline discrète horizontale uniquement */
        .tableau-recap table {{
            border-collapse: collapse;
            width: 100%;
        }}
        .tableau-recap th, .tableau-recap td {{
            border: none !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
        }}
        /* Streamlit enveloppe automatiquement le contenu HTML rendu par
           st.markdown dans un conteneur avec défilement — on le désactive
           ici, sinon une mini barre de défilement parasite apparaît */
        [data-testid="stMarkdownContainer"] {{
            overflow: visible !important;
        }}
        </style>
    """, unsafe_allow_html=True)


def titre_page(texte: str):
    """Titre principal de la page (ex: "Business"), plus compact que st.title()."""
    st.markdown(f'<div class="page-titre">{texte}</div>', unsafe_allow_html=True)


def selecteur_mois(df, titre: str):
    """
    Affiche la ligne titre de page + sélecteur de mois, et retourne le
    Timestamp du mois choisi.

    Le mois sélectionné est mémorisé dans st.session_state (clé partagée
    entre TOUTES les pages) : si on choisit "Avril 2026" sur Business puis
    qu'on bascule sur Service ou RH, le sélecteur repart sur "Avril 2026"
    au lieu de revenir sur le mois le plus récent à chaque changement de
    page — comportement attendu, demandé par Bastien.

    Si le mois mémorisé n'existe pas dans les données de la page actuelle
    (ex: historique plus court sur un pôle que sur un autre), on retombe
    silencieusement sur le mois le plus récent disponible ICI.

    Args:
        df: DataFrame de la page (doit avoir une colonne "Mois")
        titre: titre de la page (ex: "Ressources humaines")

    Returns:
        Timestamp du mois sélectionné
    """
    mois_disponibles = sorted(df["Mois"].dropna().unique(), reverse=True)
    mois_disponibles = [pd.Timestamp(m) for m in mois_disponibles]
    options_mois = {formater_mois(m): m for m in mois_disponibles}

    mois_memorise = st.session_state.get("mois_selectionne_global")
    mois_par_defaut = mois_memorise if mois_memorise in mois_disponibles else mois_disponibles[0]
    index_par_defaut = mois_disponibles.index(mois_par_defaut)

    col_titre, col_selecteur = st.columns([5, 1])
    with col_titre:
        titre_page(titre)
    with col_selecteur:
        st.write("")  # petit espace pour aligner verticalement avec le titre
        mois_choisi_label = st.selectbox(
            "Mois", options=list(options_mois.keys()), index=index_par_defaut,
            label_visibility="collapsed",
        )
    mois_selectionne = options_mois[mois_choisi_label]
    st.session_state["mois_selectionne_global"] = mois_selectionne
    return mois_selectionne


def section_eyebrow(texte: str):
    """Petit libellé de section en majuscules (ex: "KPI DU MOIS")."""
    st.markdown(f'<div class="section-eyebrow">{texte.upper()}</div>', unsafe_allow_html=True)


def groupe_titre(texte: str):
    """Sous-titre de groupe de cartes, avec ligne de séparation (ex: "VENTES")."""
    st.markdown(f'<div class="groupe-titre">{texte.upper()}</div>', unsafe_allow_html=True)


def badge_html(texte: str, statut: str) -> str:
    """
    Génère le HTML d'un badge coloré (ex: "Dans l'objectif" en vert).

    Args:
        texte: texte affiché dans le badge
        statut: "vert", "rouge", "neutre", ou "non disponible"
    """
    couleurs = COULEURS_STATUT.get(statut, COULEURS_STATUT["neutre"])
    return (
        f'<span class="badge" style="background-color:{couleurs["bg"]}; '
        f'color:{couleurs["texte"]};">{texte}</span>'
    )


def carte_kpi(
    titre: str,
    valeur: str,
    delta_texte: str = None,
    delta_couleur: str = None,
    badge_texte: str = None,
    badge_statut: str = None,
):
    """
    Affiche une carte KPI complète (titre, valeur, delta optionnel,
    badge de statut optionnel), stylée comme la maquette.

    Args:
        titre: nom du KPI (ex: "CA")
        valeur: valeur déjà formatée en texte (ex: "184 k€")
        delta_texte: texte du delta (ex: "▲ +2,1% vs N-1 (180 k€)")
        delta_couleur: "vert" ou "rouge" — couleur du texte du delta
        badge_texte: texte du badge de statut (ex: "Dans l'objectif")
        badge_statut: "vert" ou "rouge" — couleur du badge
    """
    html = '<div class="carte-kpi">'
    html += f'<div class="carte-titre">{titre}</div>'
    html += f'<div class="carte-valeur">{valeur}</div>'

    if delta_texte:
        couleur = COULEURS_DELTA.get(delta_couleur, COULEURS_DELTA["neutre"])
        html += f'<div class="carte-delta" style="color:{couleur};">{delta_texte}</div>'

    if badge_texte:
        html += badge_html(badge_texte, badge_statut)

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)