from __future__ import annotations
import streamlit as st
import re

SEASON_LABELS = {
    "nov_mar": "NOV -> MAR",
    "mar_nov": "MAR -> NOV",
}

def _infer_dataset_season(dataset_key: str, dataset_cfg: dict) -> str | None:
    text = " ".join(
        [
            str(dataset_key or ""),
            str(dataset_cfg.get("label", "")),
            str(dataset_cfg.get("file", "")),
        ]
    ).lower()
    text = text.replace("–", "-").replace("—", "-")

    if re.search(r"\bnov\s*(?:->|to|-|a)?\s*mar\b", text):
        return "nov_mar"
    if re.search(r"\bmar\s*(?:->|to|-|a)?\s*nov\b", text):
        return "mar_nov"
    if "nov_mar" in text:
        return "nov_mar"
    if "mar_nov" in text:
        return "mar_nov"
    return None

def inject_base_css():
    st.markdown(
        """
        <style>
        .stApp { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; }
        /* Oculta la entrada raiz "app" en la navegacion multipagina de Streamlit */
        [data-testid="stSidebarNav"] ul li:first-child { display: none; }
        [data-testid="stSidebarNav"] a[href="/"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def sidebar_app_dataset_picker(cfg: dict):
    apps = cfg.get("apps", {})
    if not apps:
        st.sidebar.error("No hay apps definidas en config/apps.yml")
        return

    # Selector unico de archivo Excel (sin exponer selector de app).
    # Cada opcion representa una combinacion (app_key, dataset_key).
    excel_options = []
    for a_key, a_cfg in apps.items():
        datasets = a_cfg.get("datasets", {}) or {}
        for d_key, d_cfg in datasets.items():
            excel_options.append(
                {
                    "id": f"{a_key}::{d_key}",
                    "app_key": a_key,
                    "dataset_key": d_key,
                    "label": f'{a_cfg.get("label", a_key)} - {d_cfg.get("label", d_key)}',
                    "season": _infer_dataset_season(d_key, d_cfg),
                }
            )

    if not excel_options:
        st.sidebar.warning("No hay archivos de Excel configurados en apps.yml.")
        st.session_state["app_key"] = None
        st.session_state["dataset_key"] = None
        st.session_state["_available_dataset_seasons"] = []
        return

    ids = [o["id"] for o in excel_options]
    by_id = {o["id"]: o for o in excel_options}

    current_id = f'{st.session_state.get("app_key")}::{st.session_state.get("dataset_key")}'
    current_season = by_id.get(current_id, {}).get("season")

    available_seasons = [s for s in ["nov_mar", "mar_nov"] if any(o["season"] == s for o in excel_options)]
    if available_seasons:
        selected_season = st.session_state.get("dataset_season_filter")
        if selected_season not in available_seasons:
            selected_season = current_season if current_season in available_seasons else available_seasons[0]
            st.session_state["dataset_season_filter"] = selected_season

        excel_options = [o for o in excel_options if o["season"] == selected_season]
        ids = [o["id"] for o in excel_options]
        by_id = {o["id"]: o for o in excel_options}

        if not ids:
            st.sidebar.warning("No hay archivos configurados para el horario seleccionado.")
            st.session_state["app_key"] = None
            st.session_state["dataset_key"] = None
            st.session_state["_available_dataset_seasons"] = available_seasons
            return

    default_id = current_id if current_id in by_id else ids[0]

    # Siempre visible para el usuario en la vista principal.
    if st.session_state.get("excel_selection_id") not in by_id:
        st.session_state["excel_selection_id"] = default_id

    selected_id = st.selectbox(
        "Archivo Excel",
        ids,
        key="excel_selection_id",
        format_func=lambda option_id: by_id[option_id]["label"],
    )

    selected = by_id[selected_id]
    st.session_state["app_key"] = selected["app_key"]
    st.session_state["dataset_key"] = selected["dataset_key"]
    st.sidebar.caption(f'Archivo activo: {selected["label"]}')
    st.session_state["_available_dataset_seasons"] = available_seasons

def sidebar_season_switcher():
    available_seasons = st.session_state.get("_available_dataset_seasons", [])
    if not available_seasons:
        return
    st.sidebar.divider()
    st.sidebar.radio(
        "Opciones de horario",
        available_seasons,
        key="dataset_season_filter",
        format_func=lambda s: SEASON_LABELS.get(s, s),
    )

def download_button_df(df, filename: str):
    import pandas as pd
    if df is None or getattr(df, "empty", True):
        return
    if not isinstance(df, pd.DataFrame):
        return

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="?????? Descargar CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )
