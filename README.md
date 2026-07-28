# Dashboard McDo — Pilotage opérationnel du restaurant

Outil de pilotage opérationnel pour restaurant franchisé McDonald's : centralisation des données d'exploitation, calcul automatisé des indicateurs de performance (KPI) et tableau de bord décisionnel.

Développé dans le cadre d'un mémoire de recherche (Master Économiste d'Entreprise, Université de Tours, 2025-2026).

## Architecture

```
Google Sheets  →  gspread  →  pandas  →  Streamlit
(saisie mensuelle)  (lecture)  (nettoyage,   (tableau de bord)
                                calcul KPI)
```

Les données sont saisies manuellement chaque mois par le directeur du restaurant dans un classeur Google Sheets structuré (un onglet par pôle : Business, Service, RH, Polyvalence, Qualité). Ce classeur est lu par des scripts Python via `gspread`, nettoyé et transformé en indicateurs avec `pandas`, puis affiché dans un tableau de bord développé avec `Streamlit`.

## Structure du dépôt

```
mcdo-dashboard/
├── data/                  # données locales temporaires (ignorées par git)
├── src/
│   ├── gspread/           # connexion et lecture du Google Sheets
│   ├── kpi/               # calcul des KPI par pôle (business, service, rh, polyvalence, qualite)
│   └── predictif/         # analyse exploratoire et régression sur le CA
├── dashboard/
│   ├── pages/             # pages du dashboard Streamlit (une par pôle)
│   └── app.py             # point d'entrée de l'application
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone <url-du-depot>
cd mcdo-dashboard
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### Configuration des accès

Ce dépôt ne contient aucun identifiant, mot de passe ou clé d'accès. La configuration des accès (connexion au Google Sheets, authentification du tableau de bord) est décrite dans le guide de passation, transmis séparément et non versionné dans ce dépôt.

## Lancer le dashboard en local

```bash
streamlit run dashboard/app.py
```

## Déploiement

Le tableau de bord est déployé sur **Streamlit Community Cloud**, gratuitement, sans serveur dédié. L'accès est protégé par authentification.

Streamlit Community Cloud met en veille les applications inactives après 7 jours. Un workflow GitHub Actions intégré au dépôt (`.github/workflows/keep-alive.yml`) visite chaque jour l'URL du dashboard pour le maintenir actif (détails dans le guide de passation).

Les données lues depuis Google Sheets sont mises en cache 24h pour limiter les appels à l'API. Un bouton de rafraîchissement manuel permet de forcer la mise à jour après la saisie mensuelle.

## KPI suivis

Quatre pôles : **Business** (CA, TAC, QCR, marges, pertes...), **Service** (temps de service, canaux de commande, satisfaction), **Ressources humaines** (masse salariale, turn-over, VPHE), **Qualité et sécurité alimentaire** (audits, analyses bactériologiques). 

## Maintenance

- Saisie mensuelle des données par le directeur dans le Google Sheets — aucune autre intervention requise de sa part.
- Maintenance technique (accès, service de supervision, dépôt de code) : voir le guide de passation.

## Contact

Projet développé par Bastien Barthélémy.