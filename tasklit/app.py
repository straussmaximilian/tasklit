"""Render the application."""
import streamlit as st

import tasklit.settings.consts as settings
import tasklit.src.utils.helpers as helper_functions
from tasklit.pages.dashboard import usage_dashboard
from tasklit.pages.homepage import homepage
from tasklit.src.classes import app_db_handler

# Create application resource folders, e.g. logs, data, etc.
for folder in (settings.BASE_DATA_DIR, settings.BASE_LOG_DIR):
    helper_functions.create_folder_if_not_exists(folder)

app_db_handler.create_tables_on_init()

# Define selection of pages and render the sidebar
application_pages = {"Home": homepage, "Job Stats": usage_dashboard}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Navigate to", list(application_pages.keys()))
page = application_pages[selection]
page()
