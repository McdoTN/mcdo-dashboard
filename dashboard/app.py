"""
dashboard/app.py

Point d'entrée et routeur central du dashboard. Construit la navigation
via st.navigation/st.Page. Toutes les pages sont désormais TOUJOURS
déclarées ici, authentifié ou non (contrairement à avant, où seul
l'écran de connexion existait tant qu'on n'était pas connecté) : c'est
nécessaire pour que st.switch_page("pages/0_Accueil.py"), appelé depuis
auth.py juste après la saisie du mot de passe, puisse cibler une page —
st.switch_page exige que la page visée soit déjà déclarée dans l'appel
st.navigation() du run en cours, sinon il lève une erreur (constaté).

La protection ne vient donc plus du fait que les autres pages n'existent
pas côté routeur, mais de verifier_mot_de_passe() ci-dessous, appelé
AVANT pg.run() : tant qu'on n'est pas connecté, aucune page ne s'exécute
jamais, quelle que soit l'URL tapée directement dans le navigateur.
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

st.set_page_config(page_title="Dashboard McDo", page_icon="🍔", layout="wide")
appliquer_style()

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

# Bloque ici (st.stop() à l'intérieur) tant que le mot de passe n'a pas
# été saisi correctement — aucune page ci-dessus ne s'exécute avant ça.
verifier_mot_de_passe()

pg.run()