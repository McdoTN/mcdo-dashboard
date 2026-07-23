"""
dashboard/app.py

Point d'entrée et routeur central du dashboard. Construit la navigation
via st.navigation/st.Page, ce qui permet de décider dynamiquement quelles
pages existent selon l'état d'authentification. Ne contient plus aucun
contenu de page lui-même — Accueil vit désormais dans
dashboard/pages/0_Accueil.py, comme toutes les autres pages, pour que
st.page_link puisse y faire référence depuis n'importe quel fichier.
"""

import sys
from pathlib import Path

chemin = Path(__file__).resolve().parent
while not (chemin / "src").exists():
    chemin = chemin.parent
sys.path.append(str(chemin))

import streamlit as st
from auth import verifier_mot_de_passe
from style import appliquer_style


def page_connexion():
    """Écran de connexion — seule page existante tant qu'on n'est pas authentifié."""
    st.set_page_config(page_title="Dashboard McDo", page_icon="🍔", layout="wide")
    appliquer_style()
    verifier_mot_de_passe()


if not st.session_state.get("authentifie", False):
    # Pas encore connecté : la liste des pages ne contient QUE l'écran de
    # connexion — aucune autre page n'existe pour Streamlit à ce stade,
    # impossible d'y accéder même en tapant une URL directement.
    pg = st.navigation([st.Page(page_connexion, title="Connexion")], position="hidden")
else:
    # Connecté : la vraie liste de pages apparaît — toutes les pages du
    # dashboard sont maintenant construites.
    pg = st.navigation(
        [
            st.Page("pages/0_Accueil.py", title="Accueil", icon=":material/dashboard:", default=True),
            st.Page("pages/1_Business.py", title="Business", icon=":material/money_bag:"),
            st.Page("pages/2_Service.py", title="Service", icon=":material/schedule:"),
            st.Page("pages/3_RH.py", title="RH", icon=":material/group:"),
            st.Page("pages/4_Polyvalence.py", title="Polyvalence", icon=":material/sync:"),
            st.Page("pages/5_Qualite.py", title="Qualité", icon=":material/verified_user:"),
        ],
        position="hidden",
    )

pg.run()
