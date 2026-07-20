"""
src/kpi/utils.py

Fonctions utilitaires partagées pour le calcul des KPI, notamment le
nettoyage des colonnes numériques issues du Google Sheets (format français,
virgule décimale) et le parsing des codes bactériologiques.
"""

import pandas as pd


def clean_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Convertit une liste de colonnes texte (format français, ex: "0,69")
    en colonnes numériques (float), sur une copie du DataFrame.

    À utiliser uniquement sur les colonnes réellement numériques.
    Ne pas utiliser sur les colonnes de codes alphanumériques
    (ex: pôle Qualité, valeurs type "1Z", "2U", "1T") — utiliser
    parse_code_bacterio() à la place pour celles-là.

    Args:
        df: DataFrame source (ex: retourné par load_data_tab)
        columns: liste des noms de colonnes à convertir

    Returns:
        Nouveau DataFrame avec les colonnes indiquées converties en float.
        Les valeurs non convertibles deviennent NaN (plutôt que de
        planter tout le traitement).
    """
    df = df.copy()
    for col in columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
            .replace("", None)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def statut_tendance(delta, sens: str) -> str:
    """
    Détermine si un delta (évolution d'un mois à l'autre, ou vs N-1)
    représente une bonne ou une mauvaise nouvelle, selon le sens du KPI.

    Contrairement à statut_seuil_fixe() (qui compare une valeur à un seuil
    fixe), cette fonction ne juge que la DIRECTION du changement :
    - sens "max" (ex: temps de service, Pertes — plus bas = mieux) :
      delta négatif (baisse) -> "vert", delta positif (hausse) -> "rouge"
    - sens "min" (ex: Marge P&L — plus haut = mieux) :
      delta positif (hausse) -> "vert", delta négatif (baisse) -> "rouge"

    Args:
        delta: variation numérique (peut être None si N-1 indisponible)
        sens: "max" ou "min", même convention que dans SEUILS_FIXES

    Returns:
        "vert", "rouge", "neutre" (delta exactement à 0), ou "non disponible"
    """
    if delta is None or pd.isna(delta):
        return "non disponible"
    if delta == 0:
        return "neutre"

    if sens == "max":
        return "vert" if delta < 0 else "rouge"
    else:  # sens == "min"
        return "vert" if delta > 0 else "rouge"


def parse_code_bacterio(value: str) -> tuple[int, str] | None:
    """
    Parse un code de prélèvement bactériologique au format "1Z", "2U", "1T".

    Codification :
        Z = Satisfaisant
        U = Non satisfaisant N1
        T = Non satisfaisant N2

    Args:
        value: chaîne brute issue du Sheet, ex: "1Z", "" (mois sans prélèvement)

    Returns:
        Tuple (nombre, code) ex: (1, "Z"), ou None si vide/non parsable.
    """
    value = value.strip().upper() if isinstance(value, str) else ""
    if not value:
        return None  # mois sans prélèvement, cas normal

    # Sépare la partie numérique de la lettre finale
    lettre = value[-1]
    nombre_str = value[:-1]

    if lettre not in ("Z", "U", "T") or not nombre_str.isdigit():
        return None  # format inattendu, à investiguer

    return int(nombre_str), lettre