from __future__ import annotations
import pandas as pd

def compare_splits_for_station(df: pd.DataFrame, split_a: int, split_b: int, station: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Devuelve:
      added: sitios que aparecen en Split B y no en Split A (para la misma station)
      removed: sitios que aparecen en Split A y no en Split B
    """
    a = df[(df["Split"] == split_a) & (df["Station"] == station)].copy()
    b = df[(df["Split"] == split_b) & (df["Station"] == station)].copy()

    # Normalizar Site (por si hay espacios)
    a_sites = set(a["Site"].dropna().astype(str).str.strip().tolist()) if "Site" in a.columns else set()
    b_sites = set(b["Site"].dropna().astype(str).str.strip().tolist()) if "Site" in b.columns else set()

    added_sites = sorted(list(b_sites - a_sites))
    removed_sites = sorted(list(a_sites - b_sites))

    # Crear dataframes bonitos con columnas mínimas
    added = b[b["Site"].astype(str).str.strip().isin(added_sites)].copy() if added_sites else b.iloc[0:0].copy()
    removed = a[a["Site"].astype(str).str.strip().isin(removed_sites)].copy() if removed_sites else a.iloc[0:0].copy()

    keep_cols = [c for c in ["Hour","Time","Site","Drop time","ID","Notes*"] if c in df.columns]
    return added[keep_cols].reset_index(drop=True), removed[keep_cols].reset_index(drop=True)
