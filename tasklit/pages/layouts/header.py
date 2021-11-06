"""Header UI element."""
import streamlit as st


def header(title: str, sub_title: str) -> None:
    """Generate a basic UI header element for an application page."""
    st.write(title)
    st.text(sub_title)
