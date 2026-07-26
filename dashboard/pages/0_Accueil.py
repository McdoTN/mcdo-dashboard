"""
dashboard/pages/0_Accueil.py

Page d'accueil / vue d'ensemble : message de bienvenue, CA net cumulé sur
l'année (vs période équivalente N-1) + avancement de l'année, puis un
résumé compact des items importants de chaque pôle (Business, Service,
RH, Polyvalence, Qualité) avec un point vert/rouge par item. Pas de
section "Alertes du mois" (décision de Bastien, on garde ça simple pour
l'instant). Toute la page arrive en fondu au chargement.
"""

import sys
from pathlib import Path

chemin = Path(__file__).resolve().parent
while not (chemin / "src").exists():
    chemin = chemin.parent
sys.path.append(str(chemin))

import streamlit as st
import pandas as pd

from style import (
    appliquer_style, COULEURS_DELTA, COULEUR_CARTE, COULEUR_CARTE_BORDURE,
    COULEUR_TEXTE, COULEUR_TEXTE_SECONDAIRE, titre_page, selecteur_mois,
)
from sidebar import construire_sidebar

from src.kpi.utils import statut_seuil_fixe
from src.kpi.business import charger_donnees_business, calculer_kpi_business, SEUILS_FIXES as SEUILS_BUSINESS
from src.kpi.service import charger_donnees_service, calculer_kpi_service, SEUILS_FIXES as SEUILS_SERVICE
from src.kpi.rh import charger_donnees_rh, calculer_kpi_rh, SEUILS_FIXES as SEUILS_RH
from src.kpi.polyvalence import (
    charger_donnees_polyvalence, calculer_kpi_polyvalence, LIBELLES_POSTES, SEUIL_POLYVALENCE,
)
from src.kpi.qualite import charger_donnees_qualite, calculer_kpi_qualite, SEUILS_FIXES as SEUILS_QUALITE

st.set_page_config(page_title="Dashboard McDo", page_icon="🍔", layout="wide")
appliquer_style()
construire_sidebar("accueil")

# --- CHARGEMENT DE TOUS LES PÔLES ---
# Fait AVANT le conteneur animé ci-dessous : la première fois (cache
# Google Sheets pas encore rempli), ce chargement peut prendre quelques
# secondes et affiche son propre spinner "Running load_data_tab(...)".
# En le mettant à l'intérieur du conteneur animé, le fade se jouait sur
# ce spinner (qui disparaît ensuite) et était déjà terminé quand le vrai
# contenu du dashboard s'affichait enfin — le fade n'était donc jamais
# visible sur le contenu lui-même.
df_business = charger_donnees_business()
df_service = charger_donnees_service()
df_rh = charger_donnees_rh()
df_polyvalence = charger_donnees_polyvalence()
df_qualite = charger_donnees_qualite()


def formater_euros(valeur) -> str:
    return f'{valeur:,.0f} €'.replace(",", " ")


def statut_avec_egalite(valeur, seuil, statut):
    """
    Point orange si la valeur tombe PILE sur le seuil d'objectif (cas
    limite, à la demande de Bastien) — sinon on garde le statut vert/rouge
    déjà calculé par le module KPI d'origine. Ne s'applique qu'aux KPI à
    seuil fixe (CA/TAC restent sur leur propre logique de tendance N-1,
    pas concernés par cette règle).
    """
    if valeur is not None and seuil is not None and abs(valeur - seuil) < 1e-9:
        return "orange"
    return statut


# COULEURS_DELTA (partagé, style.py) n'a que vert/rouge/neutre — le point
# orange est une couleur locale à cette page uniquement, pas ajoutée au
# dict partagé pour ne pas affecter les autres pages
COULEUR_POINT_ORANGE = "#f59e0b"


def carte_apercu(titre: str, icone: str, couleur: str, items: list) -> str:
    """
    items : liste de tuples (label, valeur_texte, statut) — statut est
    "vert"/"rouge"/"orange"/None. None = pas de point (purement
    informatif). Orange seulement pour l'égalité pile sur le seuil
    (statut_avec_egalite) — pas de 3e couleur pour un vrai écart.
    """
    html = (
        '<div class="carte-graphique" style="padding:16px 16px 8px 16px; height:100%; box-sizing:border-box;">'
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">'
        f'<span style="font-size:16px;">{icone}</span>'
        f'<span style="font-weight:700; color:{COULEUR_TEXTE}; font-size:15px;">{titre}</span>'
        f'</div>'
    )
    for label, valeur, statut in items:
        if statut == "orange":
            couleur_point = COULEUR_POINT_ORANGE
        else:
            couleur_point = COULEURS_DELTA.get(statut) if statut else None
        point_html = (
            f'<span style="display:inline-block; width:8px; height:8px; border-radius:50%; '
            f'background-color:{couleur_point}; margin-left:8px; flex-shrink:0;"></span>'
            if couleur_point else ""
        )
        html += (
            f'<div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; '
            f'border-bottom:1px solid {COULEUR_CARTE_BORDURE};">'
            f'<span style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px;">{label}</span>'
            f'<span style="display:flex; align-items:center;">'
            f'<span style="color:{COULEUR_TEXTE}; font-weight:600; font-size:14px;">{valeur}</span>'
            f'{point_html}'
            f'</span>'
            f'</div>'
        )
    html += "</div>"
    return html


# Animation de fondu à l'ouverture de la page — appliquée uniquement au
# conteneur "accueil_fade" ci-dessous (pas globalement dans style.py),
# donc n'affecte pas les autres pages. Depuis que auth.py utilise
# st.switch_page() (vraie navigation) plutôt que st.rerun() pour arriver
# ici après le mot de passe, ce conteneur est remonté à neuf comme lors
# d'un changement d'onglet classique.
st.markdown(
    """
    <style>
    @keyframes fondu_accueil {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .st-key-accueil_fade {
        animation: fondu_accueil 0.9s ease-in;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="accueil_fade"):
    # --- SÉLECTEUR DE MOIS (partagé avec les autres pages ; comme il n'y a
    # rien en mémoire au tout premier lancement, il retombe automatiquement
    # sur le mois le plus récent de Business — comportement voulu). Le titre
    # "Vue d'ensemble" est remplacé par "Bienvenue Arnaud" (réutilise le
    # style .page-titre de selecteur_mois, plus gros que l'ancien texte de
    # bienvenue séparé).
    mois_selectionne = selecteur_mois(df_business, "Bienvenue Arnaud")
    annee_selectionnee = mois_selectionne.year
    mois_num = mois_selectionne.month

    # --- TOUT LE CALCUL D'ABORD, AUCUN RENDU ENTRE-TEMPS ---
    # Auparavant, le calcul des 5 pôles (calculer_kpi_business, etc.) se
    # faisait APRÈS avoir déjà affiché la carte CA — le temps de calcul
    # entre les deux créait un blanc visible, et l'animation de fondu du
    # conteneur (qui tourne sur un chronomètre depuis son tout premier
    # élément affiché) était déjà terminée quand les cartes des pôles
    # arrivaient enfin : elles apparaissaient donc d'un coup ("pop"), sans
    # fondu. En calculant TOUT en premier (rien à l'écran entre-temps) puis
    # en enchaînant les affichages sans aucun calcul entre eux, tout le
    # contenu arrive groupé pendant que l'animation est encore en cours.

    # --- CA NET CUMULÉ + AVANCEMENT DE L'ANNÉE ---
    ca_cumule = df_business[
        (df_business["Mois"].dt.year == annee_selectionnee) & (df_business["Mois"].dt.month <= mois_num)
    ]["CA"].sum()
    ca_cumule_n1 = df_business[
        (df_business["Mois"].dt.year == annee_selectionnee - 1) & (df_business["Mois"].dt.month <= mois_num)
    ]["CA"].sum()

    evolution_pct = None
    if ca_cumule_n1:
        evolution_pct = (ca_cumule - ca_cumule_n1) / ca_cumule_n1 * 100

    delta_ca_html = ""
    if evolution_pct is not None:
        fleche = "▲" if evolution_pct >= 0 else "▼"
        couleur_delta = COULEURS_DELTA["vert"] if evolution_pct >= 0 else COULEURS_DELTA["rouge"]
        delta_ca_html = (
            f'<div style="color:{couleur_delta}; font-size:13px;">'
            f'{fleche} {evolution_pct:+.1f}% vs {annee_selectionnee - 1} à période égale ({formater_euros(ca_cumule_n1)})</div>'
        )

    pourcentage_annee = round(mois_num / 12 * 100)

    html_ca = f"""
    <div class="carte-graphique" style="padding:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:24px;">
        <div>
            <div style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:13px; margin-bottom:6px;">CA net — année {annee_selectionnee}</div>
            <div style="color:{COULEUR_TEXTE}; font-size:34px; font-weight:700; margin-bottom:4px;">{formater_euros(ca_cumule)}</div>
            {delta_ca_html}
        </div>
        <div style="min-width:240px;">
            <div style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:12px; margin-bottom:6px;">Avancement année ({mois_num} mois / 12)</div>
            <div style="background-color:{COULEUR_CARTE_BORDURE}; border-radius:6px; height:8px; overflow:hidden;">
                <div style="background-color:#818cf8; width:{pourcentage_annee}%; height:100%;"></div>
            </div>
            <div style="color:{COULEUR_TEXTE_SECONDAIRE}; font-size:12px; margin-top:6px;">{pourcentage_annee}% de l'année écoulée</div>
        </div>
    </div>
    """

    # --- Business : CA, TAC, Marge P&L, Pertes, E/R ---
    if mois_selectionne in df_business["Mois"].values:
        kb = calculer_kpi_business(df_business, mois=mois_selectionne)["kpi"]
        _, seuil_marge = SEUILS_BUSINESS["Marge P&L"]
        _, seuil_pertes = SEUILS_BUSINESS["Pertes"]
        _, seuil_er = SEUILS_BUSINESS["Écart de rendement"]
        items_business = [
            # CA/TAC : statut de tendance vs N-1 (pas de seuil fixe -> pas de
            # point orange possible ici, logique différente)
            ("CA", formater_euros(kb["CA"]["valeur"]), kb["CA"]["statut"]),
            ("TAC", f'{kb["TAC"]["valeur"]:,.0f}'.replace(",", " "), kb["TAC"]["statut"]),
            ("Marge P&L", f'{kb["Marge P&L"]["valeur"]:.1f}%', statut_avec_egalite(kb["Marge P&L"]["valeur"], seuil_marge, kb["Marge P&L"]["statut"])),
            ("Pertes", f'{kb["Pertes"]["valeur"]:.2f}%', statut_avec_egalite(kb["Pertes"]["valeur"], seuil_pertes, kb["Pertes"]["statut"])),
            ("E/R", f'{kb["Écart de rendement"]["valeur"]:.2f}%', statut_avec_egalite(kb["Écart de rendement"]["valeur"], seuil_er, kb["Écart de rendement"]["statut"])),
        ]
    else:
        items_business = [(label, "—", None) for label in ["CA", "TAC", "Marge P&L", "Pertes", "E/R"]]

    # --- Service : R2P, OEPE, Note Google, McDo&Moi, Rapport balance ---
    if mois_selectionne in df_service["Mois"].values:
        ks = calculer_kpi_service(df_service, mois=mois_selectionne)["kpi"]
        _, seuil_r2p = SEUILS_SERVICE["Temps de service R2P comptoir"]
        _, seuil_oepe = SEUILS_SERVICE["Temps de service OEPE drive"]
        _, seuil_note = SEUILS_SERVICE["Note Google"]
        _, seuil_mcdomoi = SEUILS_SERVICE["McDo&Moi"]
        items_service = [
            ("R2P comptoir", f'{ks["Temps de service R2P comptoir"]["valeur"]:.0f} s', statut_avec_egalite(ks["Temps de service R2P comptoir"]["valeur"], seuil_r2p, ks["Temps de service R2P comptoir"]["statut"])),
            ("OEPE drive", f'{ks["Temps de service OEPE drive"]["valeur"]:.0f} s', statut_avec_egalite(ks["Temps de service OEPE drive"]["valeur"], seuil_oepe, ks["Temps de service OEPE drive"]["statut"])),
            ("Note Google", f'{ks["Note Google"]["valeur"]:.1f} / 5', statut_avec_egalite(ks["Note Google"]["valeur"], seuil_note, ks["Note Google"]["statut"])),
            ("McDo&Moi", f'{ks["McDo&Moi"]["valeur"]:.1f}%', statut_avec_egalite(ks["McDo&Moi"]["valeur"], seuil_mcdomoi, ks["McDo&Moi"]["statut"])),
        ]
        # Rapport balance n'est pas dans les cartes KPI-du-mois de la page
        # Service (seulement dans son graphique d'évolution), donc pas dans le
        # dict "kpi" retourné par calculer_kpi_service — on lit la valeur brute
        # directement, seuil ≥98% repris du graphique de la page Service.
        ligne_service = df_service.loc[df_service["Mois"] == mois_selectionne].iloc[0]
        valeur_balance = ligne_service["Rapport balance"]
        statut_balance = statut_seuil_fixe(valeur_balance, "min", 98)
        items_service.append(("Rapport balance", f'{valeur_balance:.1f}%', statut_avec_egalite(valeur_balance, 98, statut_balance)))
    else:
        items_service = [(label, "—", None) for label in ["R2P comptoir", "OEPE drive", "Note Google", "McDo&Moi", "Rapport balance"]]

    # --- RH : les 5 KPI ---
    if mois_selectionne in df_rh["Mois"].values:
        kr = calculer_kpi_rh(df_rh, mois=mois_selectionne)["kpi"]
        _, seuil_mofdc = SEUILS_RH["MO FDC"]
        _, seuil_mopl = SEUILS_RH["MO P&L"]
        _, seuil_vphe = SEUILS_RH["VPHE"]
        _, seuil_pac = SEUILS_RH["PAC"]
        _, seuil_to = SEUILS_RH["Turn-Over"]
        items_rh = [
            ("MO FDC", f'{kr["MO FDC"]["valeur"]:.1f}%', statut_avec_egalite(kr["MO FDC"]["valeur"], seuil_mofdc, kr["MO FDC"]["statut"])),
            ("MO P&L", f'{kr["MO P&L"]["valeur"]:.1f}%', statut_avec_egalite(kr["MO P&L"]["valeur"], seuil_mopl, kr["MO P&L"]["statut"])),
            ("VPHE", f'{kr["VPHE"]["valeur"]:.1f} €', statut_avec_egalite(kr["VPHE"]["valeur"], seuil_vphe, kr["VPHE"]["statut"])),
            ("PAC", f'{kr["PAC"]["valeur"]:.1f}%', statut_avec_egalite(kr["PAC"]["valeur"], seuil_pac, kr["PAC"]["statut"])),
            ("Turn-Over", f'{kr["Turn-Over"]["valeur"]:.1f}%', statut_avec_egalite(kr["Turn-Over"]["valeur"], seuil_to, kr["Turn-Over"]["statut"])),
        ]
    else:
        items_rh = [(label, "—", None) for label in ["MO FDC", "MO P&L", "VPHE", "PAC", "Turn-Over"]]

    # --- Polyvalence : taux global, poste +/- maîtrisé (statut réel basé sur
    # le seuil, PAS le rouge/vert forcé utilisé sur la page Polyvalence
    # elle-même pour ces deux cartes — décision de Bastien). Équipiers retiré
    # (pas un KPI à statut, décision de Bastien).
    if mois_selectionne in df_polyvalence["Mois"].values:
        rp = calculer_kpi_polyvalence(df_polyvalence, mois=mois_selectionne)
        poste_mieux = rp["poste_mieux_maitrise"]
        poste_moins = rp["poste_moins_maitrise"]
        _, seuil_poly = SEUIL_POLYVALENCE
        items_polyvalence = [
            ("Taux global", f'{rp["taux_global"]["valeur"]:.1f}%', statut_avec_egalite(rp["taux_global"]["valeur"], seuil_poly, rp["taux_global"]["statut"])),
        ]
        if poste_mieux is not None:
            d = rp["postes"][poste_mieux]
            items_polyvalence.append((f"Poste + maîtrisé ({LIBELLES_POSTES[poste_mieux]})", f'{d["valeur"]:.1f}%', statut_avec_egalite(d["valeur"], seuil_poly, d["statut"])))
        else:
            items_polyvalence.append(("Poste + maîtrisé", "—", None))
        if poste_moins is not None:
            d = rp["postes"][poste_moins]
            items_polyvalence.append((f"Poste - maîtrisé ({LIBELLES_POSTES[poste_moins]})", f'{d["valeur"]:.1f}%', statut_avec_egalite(d["valeur"], seuil_poly, d["statut"])))
        else:
            items_polyvalence.append(("Poste - maîtrisé", "—", None))
    else:
        items_polyvalence = [
            ("Taux global", "—", None), ("Poste + maîtrisé", "—", None), ("Poste - maîtrisé", "—", None),
        ]

    # --- Qualité : agrégats ANNUELS (comme sur la page Qualité elle-même,
    # pas de notion de mois pour ce pôle) — calculer_kpi_qualite() gère déjà
    # tout seul le cas d'une année sans données, pas besoin de vérif préalable.
    # Libellé avec l'année réelle plutôt que "(année)" générique.
    kq = calculer_kpi_qualite(df_qualite, annee_selectionnee)
    audit_interne_annuel = kq["audit_interne"]["valeur_annuelle"]
    audit_siliker_annuel = kq["audit_siliker"]["valeur_annuelle"]
    prelevement_annuel = kq["prelevement"]["valeur_annuelle"]
    _, seuil_audit_interne = SEUILS_QUALITE["Audit interne"]
    _, seuil_audit_siliker = SEUILS_QUALITE["Audit Siliker"]
    _, seuil_prelevement = SEUILS_QUALITE["Taux de prélèvement"]
    items_qualite = [
        (
            f"Audit interne {annee_selectionnee}",
            f'{audit_interne_annuel:.1f}%' if audit_interne_annuel is not None else "—",
            statut_avec_egalite(audit_interne_annuel, seuil_audit_interne, kq["audit_interne"]["statut_annuel"]) if audit_interne_annuel is not None else None,
        ),
        (
            f"Audit Siliker {annee_selectionnee}",
            f'{audit_siliker_annuel:.1f}%' if audit_siliker_annuel is not None else "—",
            statut_avec_egalite(audit_siliker_annuel, seuil_audit_siliker, kq["audit_siliker"]["statut_annuel"]) if audit_siliker_annuel is not None else None,
        ),
        (
            f"Prélèvement {annee_selectionnee}",
            f'{prelevement_annuel:.1f}%' if prelevement_annuel is not None else "—",
            statut_avec_egalite(prelevement_annuel, seuil_prelevement, kq["prelevement"]["statut_annuel"]) if prelevement_annuel is not None else None,
        ),
    ]

    # Couleurs et icônes alignées sur celles de la sidebar, pour la cohérence
    html_business = carte_apercu("Business", "📊", "#eab308", items_business)
    html_service = carte_apercu("Service", "🕐", "#38bdf8", items_service)
    html_rh = carte_apercu("RH", "👥", "#f472b6", items_rh)
    html_polyvalence = carte_apercu("Polyvalence", "🔄", "#34d399", items_polyvalence)
    html_qualite = carte_apercu("Qualité", "🛡️", "#f87171", items_qualite)

    # --- À PARTIR D'ICI : QUE DE L'AFFICHAGE, ENCHAÎNÉ SANS CALCUL ---
    st.markdown(html_ca, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(html_business, unsafe_allow_html=True)
    with col2:
        st.markdown(html_service, unsafe_allow_html=True)
    with col3:
        st.markdown(html_rh, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(html_polyvalence, unsafe_allow_html=True)
    with col2:
        st.markdown(html_qualite, unsafe_allow_html=True)