from __future__ import annotations
import pandas as pd

COLS_PREF = ["Split","Station","Hour","Time","Site","Drop time","ID","Notes*","SIG Tools","Map"]

def _project_search_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in COLS_PREF if c in df.columns]
    return df[cols] if cols else df

def suggest_sites(df: pd.DataFrame, query: str, limit: int = 30) -> list[str]:
    q = query.strip().lower()
    if not q or "Site" not in df.columns:
        return []

    sites = df["Site"].dropna().astype(str).str.strip()
    mask = sites.str.lower().str.contains(q, na=False, regex=False)
    unique = list(dict.fromkeys(sites[mask].tolist()))
    return unique[:limit]

def search_site_exact(df: pd.DataFrame, site_name: str, limit: int = 50) -> pd.DataFrame:
    name = site_name.strip().lower()
    if not name or "Site" not in df.columns:
        return df.iloc[0:0].copy()

    f = df.copy()
    f["__site_norm__"] = f["Site"].astype(str).str.lower().str.strip()
    matches = f[f["__site_norm__"] == name].copy()
    matches = _project_search_cols(matches).head(limit).reset_index(drop=True)
    return matches

def search_sites_in_base(df: pd.DataFrame, query: str, limit: int = 50) -> pd.DataFrame:
    q = query.strip().lower()
    if not q or "Site" not in df.columns:
        return df.iloc[0:0].copy()

    f = df.copy()
    f["__site_norm__"] = f["Site"].astype(str).str.lower().str.strip()
    matches = f[f["__site_norm__"].str.contains(q, na=False, regex=False)].copy()
    matches = _project_search_cols(matches).head(limit).reset_index(drop=True)
    return matches

def enrich_with_important_info(matches: pd.DataFrame, important: pd.DataFrame) -> pd.DataFrame:
    """
    Important Info! usa columnas tipo:
      SITES, GATES, ENTRANCES, LPR GATES, PTZ, IMPORTANT CAMERAS, NOTES, ID, SIG TOOLS...
    """
    if important is None or important.empty or "SITES" not in important.columns:
        return matches

    imp = important.copy()
    imp.columns = [str(c).strip() for c in imp.columns]
    imp["__site_norm__"] = imp["SITES"].astype(str).str.strip()

    # Merge por nombre de site (string exacto)
    out = matches.copy()
    out["__site_norm__"] = out["Site"].astype(str).str.strip()

    merged = out.merge(imp, how="left", on="__site_norm__", suffixes=("", "_IMP"))

    # Limpiar
    merged = merged.drop(columns=["__site_norm__"], errors="ignore")
    return merged
