"""
dashboard/pages/0_Accueil.py

Page d'accueil du dashboard.
"""

import sys
from pathlib import Path

chemin = Path(__file__).resolve().parent
while not (chemin / "src").exists():
    chemin = chemin.parent
sys.path.append(str(chemin))

import streamlit as st
from style import appliquer_style
from sidebar import construire_sidebar

st.set_page_config(page_title="Dashboard McDo", page_icon="🍔", layout="wide")
appliquer_style()
construire_sidebar("accueil")

st.title("🍔 Dashboard McDo")
st.caption("Restaurant Tours Nord")

st.markdown("---")
st.subheader("Bienvenue sur le dashboard de pilotage opérationnel")
st.write(
    "Utilise le menu à gauche pour naviguer entre les pôles : "
    "Business, Service, RH, Polyvalence, Qualité."
)