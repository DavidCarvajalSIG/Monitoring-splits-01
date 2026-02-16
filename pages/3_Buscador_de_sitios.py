import streamlit as st
import re
from src.config import load_apps_config
from src.ui.formatting import inject_base_css, sidebar_app_dataset_picker, sidebar_season_switcher, download_button_df
from src.data.excel_loader import load_dataset_tables
from src.logic.site_search import suggest_sites, search_site_exact, enrich_with_important_info
from src.logic.split_view import get_splits, get_stations_for_split

st.set_page_config(page_title="Buscador de sitios", layout="wide")
inject_base_css()

cfg = load_apps_config()
sidebar_app_dataset_picker(cfg)

st.title("Buscador de sitios")

app_key = st.session_state.get("app_key")
dataset_key = st.session_state.get("dataset_key")

if not app_key or not dataset_key:
    st.warning("Selecciona un archivo Excel para continuar.")
    st.stop()

tables = load_dataset_tables(cfg, app_key, dataset_key)
df = tables["base"]
important = tables.get("important_info")

splits = get_splits(df)
if not splits:
    st.error("No se encontraron splits en el dataset seleccionado.")
    st.stop()

if st.session_state.get("search_split") not in splits:
    st.session_state["search_split"] = splits[0]

selected_split = st.sidebar.selectbox(
    "Split (# operadores)",
    splits,
    key="search_split",
)

stations = get_stations_for_split(df, selected_split)
if not stations:
    st.error("No hay estaciones para el split seleccionado.")
    st.stop()

if st.session_state.get("search_station") not in stations:
    st.session_state["search_station"] = stations[0]

selected_station = st.sidebar.selectbox(
    "Tu estacion actual",
    stations,
    key="search_station",
)
sidebar_season_switcher()

st.caption(
    f"Contexto actual: split {selected_split}, tu estacion {selected_station}. "
    "Escribe parte del nombre (ej: West) y selecciona el sitio exacto."
)

query = st.text_input("Buscar sitio (texto parcial o exacto)", value="").strip()

if not query:
    st.info("Escribe un texto para buscar. Ej: 'Audi', 'Atwell', '(AS)', etc.")
    st.stop()

search_df = df
if "Split" in search_df.columns:
    search_df = search_df[search_df["Split"] == selected_split]

site_options = suggest_sites(search_df, query=query, limit=200)
using_fallback = False
if not site_options:
    site_options = suggest_sites(df, query=query, limit=200)
    using_fallback = True

if not site_options:
    st.warning(f"No se encontraron coincidencias para '{query}' en el archivo seleccionado.")
    st.stop()

if using_fallback:
    st.info(
        f"No hubo coincidencias para '{query}' en el split {selected_split}. "
        "Se muestran coincidencias del resto del archivo."
    )

selected_site = st.selectbox(
    "Coincidencias de sitio (elige una)",
    site_options,
    index=0,
)

matches = search_site_exact(search_df, site_name=selected_site, limit=1)
if matches.empty:
    st.warning(
        f"El sitio '{selected_site}' existe en el archivo, "
        f"pero no aparece en el split {selected_split}."
    )
    alt = search_site_exact(df, site_name=selected_site, limit=500)
    if not alt.empty and {"Split", "Station"}.issubset(set(alt.columns)):
        where = (
            alt[["Split", "Station"]]
            .dropna()
            .drop_duplicates()
            .sort_values(["Split", "Station"])
            .reset_index(drop=True)
        )
        st.caption("El sitio si aparece en:")
        st.dataframe(where, use_container_width=False, hide_index=True)
    st.stop()

if important is not None:
    matches = enrich_with_important_info(matches, important)

found_stations = []
if "Station" in matches.columns:
    found_stations = sorted(
        {
            int(v)
            for v in matches["Station"].dropna().tolist()
            if str(v) != "<NA>"
        }
    )

if found_stations:
    stations_txt = ", ".join(str(s) for s in found_stations)
    st.success(f"Sitio '{selected_site}': en split {selected_split} aparece en estacion(es): {stations_txt}.")
    if selected_station in found_stations:
        st.info("Tu estacion actual si monitorea ese sitio en este split.")
    else:
        st.warning("Tu estacion actual no monitorea ese sitio en este split.")

st.title("Resultado de tu busqueda:")
result_cols = [c for c in ["Site", "ID", "Split", "Station"] if c in matches.columns]
st.dataframe(matches[result_cols], use_container_width=True, hide_index=True)

