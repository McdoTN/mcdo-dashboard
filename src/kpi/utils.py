"""
src/kpi/utils.py

Fonctions utilitaires partagées pour le calcul des KPI.
"""

import pandas as pd


def clean_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
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


def parse_code_bacterio(value: str) -> tuple[int, str] | None:
    value = value.strip().upper() if isinstance(value, str) else ""
    if not value:
        return None

    lettre = value[-1]
    nombre_str = value[:-1]

    if lettre not in ("Z", "U", "T") or not nombre_str.isdigit():
        return None

    return int(nombre_str), lettre