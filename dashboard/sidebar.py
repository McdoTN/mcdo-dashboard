"""
dashboard/sidebar.py

Sidebar personnalisée : logo/titre en haut, puis navigation manuelle
(via st.page_link) avec icône et couleur de surlignage propre à chaque
pôle — remplace la navigation automatique de Streamlit, qui ne permet
pas ce niveau de personnalisation (pas de logo au-dessus, pas de couleur
par page, pas de surlignage pleine largeur).

À appeler en tout début de chaque page, juste après appliquer_style() :

    from sidebar import construire_sidebar
    construire_sidebar("business")  # id de la page actuelle
"""

import streamlit as st
from pathlib import Path

# Une entrée par page : id (utilisé pour savoir quelle page est active),
# libellé affiché, icône, chemin du fichier (relatif à app.py, comme
# attendu par st.page_link), et couleur de surlignage propre au pôle.
PAGES = [
    {"id": "accueil", "label": "Accueil", "icon": ":material/dashboard:", "path": "pages/0_Accueil.py", "couleur": "#818cf8"},
    {"id": "business", "label": "Business", "icon": ":material/money_bag:", "path": "pages/1_Business.py", "couleur": "#eab308"},
    {"id": "service", "label": "Service", "icon": ":material/schedule:", "path": "pages/2_Service.py", "couleur": "#38bdf8"},
    {"id": "rh", "label": "RH", "icon": ":material/group:", "path": "pages/3_RH.py", "couleur": "#f472b6"},
    {"id": "polyvalence", "label": "Polyvalence", "icon": ":material/sync:", "path": "pages/4_Polyvalence.py", "couleur": "#34d399"},
    {"id": "qualite", "label": "Qualité", "icon": ":material/verified_user:", "path": "pages/5_Qualite.py", "couleur": "#f87171"},
]

# Couleur de fond du surlignage plein-largeur de la page active
FOND_ACTIF = "#323238"


def construire_sidebar(page_active: str):
    """
    Construit la sidebar personnalisée et masque la navigation automatique
    de Streamlit (remplacée par celle-ci).

    Args:
        page_active: id de la page actuellement affichée (ex: "business"),
            un des "id" définis dans PAGES ci-dessus — détermine quel lien
            est mis en surbrillance.
    """
    st.markdown(
        '<style>'
        # Empêche complètement de fermer/réduire la sidebar
        '[data-testid="stSidebarCollapseButton"] {display: none !important;}'
        # Bordure visible entre la sidebar et le contenu principal
        'section[data-testid="stSidebar"] {'
        '    border-right: 1px solid #3f3f46;'
        '}'
        # Trouvé via l'inspecteur : ce conteneur (ajouté par Streamlit
        # avec le bouton de réduction, déjà masqué) a un margin-bottom de
        # 16px par défaut, responsable de l'espace vide en haut. On
        # remet un tout petit espace (8px) plutôt que 0, pour ne pas
        # coller le contenu tout en haut de la page.
        '[data-testid="stSidebarHeader"] {'
        '    margin-bottom: 0 !important;'
        '    margin-top: 0 !important;'
        '    padding: 0 !important;'
        '    height: 8px !important;'
        '    min-height: 8px !important;'
        '}'
        # Conteneur individuel que Streamlit ajoute autour de CHAQUE
        # élément (chaque st.markdown, st.container...) — source probable
        # du petit espace résiduel à droite des liens, non identifiée par
        # l'inspection précédente (qui montrait stSidebarContent à 0)
        '[data-testid="stElementContainer"] {'
        '    padding: 0 !important;'
        '    margin: 0 !important;'
        '}'
        # Neutralise TOUT fond résiduel à l'intérieur du lien (Streamlit
        # applique parfois un fond clair par défaut plus profondément que
        # le simple data-testid, ce "*" ratisse tous les enfants)
        '[data-testid="stPageLink"], [data-testid="stPageLink"] * {'
        '    background-color: transparent !important;'
        '}'
        # Retire le padding par défaut de Streamlit sur tout le contenu de
        # la sidebar (plusieurs sélecteurs ciblés, au cas où certains ne
        # matcheraient pas selon la version installée) : nécessaire pour
        # que le surlignage puisse aller jusqu'aux bords, pas juste au milieu.
        '[data-testid="stSidebarUserContent"], '
        '[data-testid="stSidebarUserContent"] > div, '
        '[data-testid="stSidebarUserContent"] .block-container, '
        '[data-testid="stSidebarContent"], '
        'section[data-testid="stSidebar"], '
        'section[data-testid="stSidebar"] > div, '
        'section[data-testid="stSidebar"] > div > div, '
        '[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {'
        '    padding-left: 0 !important;'
        '    padding-right: 0 !important;'
        '    padding-top: 0 !important;'
        '    margin-top: 0 !important;'
        '    gap: 0.15rem !important;'
        '}'
        # Réduit l'espacement automatique que Streamlit met entre les
        # éléments empilés (gap), en plus de nos propres marges
        '[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {'
        '    gap: 0.15rem !important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            '<div style="padding: 4px 20px 12px 20px;">'
            '<div style="font-weight:700; font-size:18px; color:#e4e4e7;">Dashboard McDo</div>'
            '<div style="font-size:13px; color:#a1a1aa;">Restaurant Tours Nord</div>'
            '</div>'
            '<hr style="margin: 0 0 16px 0; border-color: #323238;">',
            unsafe_allow_html=True,
        )

        # Dossier dashboard/ (où vit ce fichier), utilisé pour vérifier
        # qu'une page existe vraiment avant d'en faire un lien cliquable
        dossier_dashboard = Path(__file__).resolve().parent

        for page in PAGES:
            page_existe = (dossier_dashboard / page["path"]).exists()
            est_active = page["id"] == page_active

            if page_existe:
                with st.container(key=f"nav_{page['id']}"):
                    st.page_link(page["path"], label=page["label"], icon=page["icon"])

                couleur_bordure = page["couleur"] if est_active else "transparent"
                fond = FOND_ACTIF if est_active else "transparent"
                st.markdown(
                    f'<style>'
                    # Le conteneur porte le fond et la bordure gauche
                    # colorée. Seul le côté DROIT déborde (débordement
                    # négatif) pour compenser le padding restant de
                    # Streamlit — le côté gauche reste à sa position
                    # d'origine, déjà correctement aligné.
                    f'.st-key-nav_{page["id"]} {{'
                    f'    border-left: 4px solid {couleur_bordure};'
                    f'    background-color: {fond};'
                    f'    width: calc(100% + 2.5rem) !important;'
                    f'    margin-left: 0 !important;'
                    f'    margin-right: -2.5rem !important;'
                    f'    margin-top: 0 !important;'
                    f'    margin-bottom: 1px !important;'
                    f'}}'
                    f'.st-key-nav_{page["id"]} [data-testid="stPageLink"] {{'
                    f'    padding-left: 16px !important;'
                    f'    padding-top: 10px !important;'
                    f'    padding-bottom: 10px !important;'
                    f'    width: 100% !important;'
                    f'}}'
                    f'</style>',
                    unsafe_allow_html=True,
                )
            else:
                # Page pas encore construite : affichage grisé, non cliquable.
                # Icône affichée via un st.markdown SANS unsafe_allow_html
                # (les icônes Material ne s'affichent pas correctement
                # autrement — bug connu de Streamlit), le style grisé est
                # appliqué à part via une classe CSS ciblée.
                with st.container(key=f"nav_todo_{page['id']}"):
                    st.markdown(f"{page['icon']} {page['label']} *(à venir)*")
                st.markdown(
                    f'<style>.st-key-nav_todo_{page["id"]} p {{'
                    f'    color: #71717a !important;'
                    f'    padding-left: 20px;'
                    f'    padding-top: 10px;'
                    f'    padding-bottom: 10px;'
                    f'    margin-bottom: 0;'
                    f'}}</style>',
                    unsafe_allow_html=True,
                )