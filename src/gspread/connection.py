"""
src/gspread/connection.py

Connexion au Google Sheets du dashboard McDonald's via un compte de service
(Service Account), et lecture des onglets DATA_ en DataFrame pandas.

IMPORTANT — Le dépôt GitHub est PUBLIC (contrainte de déploiement Streamlit
Community Cloud). Aucune credential ne doit donc jamais être committée.
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


@st.cache_resource
def get_gspread_client() -> gspread.Client:
    credentials_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(
        credentials_dict, scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    return client


@st.cache_data(ttl=86400)
def load_data_tab(tab_name: str, mois_column: str = "Mois") -> pd.DataFrame:
    client = get_gspread_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]

    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(tab_name)

    all_values = worksheet.get_all_values()

    headers = all_values[0]
    data_rows = all_values[2:]

    df = pd.DataFrame(data_rows, columns=headers)
    df = df[df[mois_column].str.strip() != ""].copy()
    df[mois_column] = pd.to_datetime(df[mois_column], format="%m/%Y")
    df = df.sort_values(mois_column).reset_index(drop=True)

    return df


def refresh_data():
    load_data_tab.clear()