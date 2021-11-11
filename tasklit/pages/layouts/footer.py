import streamlit as st

from tasklit.src.utils.helpers import refresh_app


def footer() -> None:
    """Render footer UI elements."""
    if st.button("Refresh"):
        refresh_app()
