from __future__ import annotations
import pandas as pd
import re

def get_splits(df: pd.DataFrame) -> list[int]:
    if "Split" not in df.columns:
        return []
    vals = df["Split"].dropna().unique().tolist()
    out = sorted([int(v) for v in vals if str(v) != "<NA>"])
    return out

def get_stations_for_split(df: pd.DataFrame, split: int) -> list[int]:
    # Regla simple: stations van de 1..split
    return list(range(1, int(split) + 1))

def _hour_sort_key(x) -> tuple[int, int, int, str]:
    # Intenta ordenar "9:00 P.M.", "4:00 A.M.", y "24 Hrs"
    if x is None:
        return (9, 99, 99, "")
    s = str(x).strip()

    if "24" in s:
        return (0, 0, 0, s)

    # parse "H:MM A.M." / "H:MM P.M."
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})\s*([AP])\.?M\.?", s, re.IGNORECASE)
    if not m:
        return (5, 99, 99, s)

    hh = int(m.group(1))
    mm = int(m.group(2))
    ap = m.group(3).upper()

    # convertir a 24h para ordenar
    if ap == "A":
        hh24 = 0 if hh == 12 else hh
    else:
        hh24 = 12 if hh == 12 else hh + 12

    # Cualquier hora A.M. se manda al final del listado.
    if ap == "A":
        return (2, hh24, mm, s)

    return (1, hh24, mm, s)

def build_split_view(df: pd.DataFrame, split: int, station: int, extended: bool) -> pd.DataFrame:
    f = df[(df["Split"] == split) & (df["Station"] == station)].copy()

    if "Hour" in f.columns:
        f = f.sort_values(by="Hour", key=lambda s: s.map(_hour_sort_key))

    if extended:
        cols = [
            "Hour","Time","Site","ID","SIG Tools","Map","Drop time","SUNDAY (D.T.)",
            "Gates","Entrances","LPR","PTZ","Important Cameras","Notes*",
        ]
    else:
        cols = ["Hour","Time","Site","ID","SIG Tools","Map","Drop time"]

    cols = [c for c in cols if c in f.columns]
    return f[cols].reset_index(drop=True)
