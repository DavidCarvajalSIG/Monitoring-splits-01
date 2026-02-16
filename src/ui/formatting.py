from __future__ import annotations
import streamlit as st

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
                }
            )

    if not excel_options:
        st.sidebar.warning("No hay archivos de Excel configurados en apps.yml.")
        st.session_state["app_key"] = None
        st.session_state["dataset_key"] = None
        return

    ids = [o["id"] for o in excel_options]
    by_id = {o["id"]: o for o in excel_options}

    current_id = f'{st.session_state.get("app_key")}::{st.session_state.get("dataset_key")}'
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
