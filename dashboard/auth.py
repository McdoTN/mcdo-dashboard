"""
dashboard/auth.py

Protection du dashboard par un simple mot de passe partagé (pas
d'identifiant individuel). Plus simple que streamlit-authenticator,
suffisant pour un usage interne à un seul restaurant.

Le mot de passe est stocké dans st.secrets, jamais en clair dans le code
(cohérent avec le reste du projet, repo public oblige).

Format attendu dans secrets.toml :

    app_password = "le_mot_de_passe_choisi"
"""

import streamlit as st


def verifier_mot_de_passe():
    """
    Bloque l'affichage de la page tant que le bon mot de passe n'a pas
    été saisi. À appeler en tout premier, avant tout autre contenu,
    dans app.py ET dans chaque page de dashboard/pages/.

    Utilise st.session_state pour mémoriser l'authentification le temps
    de la session du navigateur : une fois connecté sur une page, pas
    besoin de ressaisir le mot de passe en changeant de page.
    """
    if st.session_state.get("authentifie", False):
        return  # déjà connecté sur cette session, on laisse passer

    # Plus besoin de masquer la sidebar manuellement ici : avec
    # st.navigation (voir app.py), la page de connexion est la SEULE
    # page qui existe tant qu'on n'est pas authentifié — il n'y a donc
    # rien à masquer, la navigation native n'est jamais générée.

    st.title("🔒 Dashboard McDo")
    st.caption("Restaurant Tours Nord — accès protégé")

    mot_de_passe_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if mot_de_passe_saisi == st.secrets["app_password"]:
            st.session_state["authentifie"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

    # Empêche le reste de la page de s'exécuter tant qu'on n'est pas connecté
    st.stop()