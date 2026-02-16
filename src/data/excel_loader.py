from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import pandas as pd
import streamlit as st

BASE_COLS = [
    "Key","Split","Station","Hour","Time","Site","Drop time","SIG Tools","Map",
    "SUNDAY (D.T.)","Notes*","Gates","Entrances","LPR","PTZ","Important Cameras","ID"
]
HA_COLS = ["Split","Station","Hour","Time","Site","Drop time","SUNDAY (D.T.)","Notes*"]

def _normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for c in ["Split", "Station"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    if "ID" in df.columns:
        df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")

    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype(str).str.strip()
            df[c] = df[c].replace({"nan": None, "None": None, "NaT": None})

    return df

@st.cache_data(show_spinner=False)
def _read_excel(file_abs: str, sheet_name: str, header: int):
    # header=0 para hojas normales, header=1 para HA
    try:
        return pd.read_excel(file_abs, sheet_name=sheet_name, header=header)
    except PermissionError as direct_err:
        src = Path(file_abs)
        # Fallback: copiar primero el archivo y leer desde copia temporal.
        # En algunos entornos de OneDrive/Excel esto evita bloqueos de acceso directo.
        try:
            with tempfile.NamedTemporaryFile(prefix="msplits_", suffix=src.suffix, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            shutil.copy2(src, tmp_path)
            try:
                return pd.read_excel(tmp_path, sheet_name=sheet_name, header=header)
            finally:
                tmp_path.unlink(missing_ok=True)
        except Exception as fallback_err:
            raise PermissionError(
                f"No se pudo abrir el Excel '{file_abs}'. "
                "Cierra el archivo en Excel, espera que OneDrive termine de sincronizar "
                "y vuelve a intentar. "
                f"Detalle original: {direct_err}. "
                f"Detalle fallback: {fallback_err}"
            ) from fallback_err

def load_dataset_tables(cfg: dict, app_key: str, dataset_key: str) -> dict:
    from src.config import resolve_dataset

    ds = resolve_dataset(cfg, app_key, dataset_key)
    file_abs = ds["file_abs"]

    if not Path(file_abs).exists():
        raise FileNotFoundError(f"No existe el Excel: {file_abs}")

    base_sheet = ds.get("base_sheet", "Flat Base")
    ha_sheet = ds.get("ha_sheet", " (H.A.) Flat Base")
    ha_header_row = int(ds.get("ha_header_row", 1))
    important_sheet = ds.get("important_info_sheet")

    # ✅ Flat Base SIEMPRE con header=0
    base = _read_excel(file_abs, base_sheet, header=0)
    base = base[[c for c in BASE_COLS if c in base.columns]].copy()
    base = _normalize_types(base)

    # ✅ HA con header=1 (según tus excels)
    ha = _read_excel(file_abs, ha_sheet, header=ha_header_row)
    ha = ha[[c for c in HA_COLS if c in ha.columns]].copy()
    ha = _normalize_types(ha)

    important = None
    if important_sheet:
        try:
            # ✅ Important Info! también con header=0
            important = _read_excel(file_abs, important_sheet, header=0)
            important.columns = [str(c).strip() for c in important.columns]
        except Exception:
            important = None

    return {"base": base, "ha": ha, "important_info": important}
