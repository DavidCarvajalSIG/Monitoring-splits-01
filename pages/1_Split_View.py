import streamlit as st
from src.config import load_apps_config
from src.ui.formatting import inject_base_css, sidebar_app_dataset_picker, sidebar_season_switcher
from src.data.excel_loader import load_dataset_tables
from src.logic.split_view import get_splits, get_stations_for_split, build_split_view

def _url_or_none(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s or s in {"-", "None", "nan", "NaT"}:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return None

st.set_page_config(page_title="Split View", layout="wide")
inject_base_css()

cfg = load_apps_config()
sidebar_app_dataset_picker(cfg)

st.title("Split View")

app_key = st.session_state.get("app_key")
dataset_key = st.session_state.get("dataset_key")

if not app_key or not dataset_key:
    st.warning("Selecciona un archivo Excel para continuar.")
    st.stop()

extended = st.sidebar.checkbox("Vista extendida", value=True)

tables = load_dataset_tables(cfg, app_key, dataset_key)
df = tables["base"]

splits = get_splits(df)
if not splits:
    st.error("No se encontraron splits en el dataset.")
    st.stop()

split = st.sidebar.selectbox("Split (# operadores)", splits, index=0)
stations = get_stations_for_split(df, split)
station = st.sidebar.selectbox("Station", stations, index=0)
sidebar_season_switcher()

view = build_split_view(df, split=split, station=station, extended=extended)

left, right = st.columns([1, 1])
with left:
    st.metric("Station", station)
with right:
    st.metric("Split seleccionado", split)

display = view.copy()
for url_col in ["SIG Tools", "Map"]:
    if url_col in display.columns:
        display[url_col] = display[url_col].map(_url_or_none)

column_config = {
    "Hour": st.column_config.TextColumn("Hour", width="small"),
    "Time": st.column_config.TextColumn("Time", width="small"),
    "Site": st.column_config.TextColumn("Site", width="large"),
    "Drop time": st.column_config.TextColumn("Drop time", width="small"),
    "SUNDAY (D.T.)": st.column_config.TextColumn("SUNDAY (D.T.)", width="small"),
    "Gates": st.column_config.TextColumn("Gates", width="small"),
    "Entrances": st.column_config.TextColumn("Entrances", width="small"),
    "LPR": st.column_config.TextColumn("LPR", width="small"),
    "PTZ": st.column_config.TextColumn("PTZ", width="small"),
    "Important Cameras": st.column_config.TextColumn("Important Cameras", width="medium"),
    "Notes*": st.column_config.TextColumn("Notes*", width="small"),
    "ID": st.column_config.NumberColumn("ID", width="small"),
}
if "SIG Tools" in display.columns:
    column_config["SIG Tools"] = st.column_config.LinkColumn("SIG Tools", display_text="Abrir", width="small")
if "Map" in display.columns:
    column_config["Map"] = st.column_config.LinkColumn("Map", display_text="Abrir", width="small")

table_height = min(880, max(320, 34 * (len(display) + 1)))
st.caption("Haz clic en 'Abrir' en SIG Tools o Map para entrar directo al link .")
st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    height=table_height,
    column_config={k: v for k, v in column_config.items() if k in display.columns},
)
