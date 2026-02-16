import streamlit as st
from src.ui.formatting import inject_base_css

st.set_page_config(page_title="Monitoring Splits", layout="wide")
inject_base_css()

if hasattr(st, "switch_page"):
    st.switch_page("pages/1_Split_View.py")

st.empty()
