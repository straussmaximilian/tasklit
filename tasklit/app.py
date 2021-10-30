"""Render the application."""

import tasklit.settings.consts as settings
import tasklit.src.utils.helpers as helper_functions
from tasklit.pages.homepage import homepage
from tasklit.src.classes import app_db_handler

# Create application resource folders, e.g. logs, data, etc.
for folder in (settings.BASE_DATA_DIR, settings.BASE_LOG_DIR):
    helper_functions.create_folder_if_not_exists(folder)

app_db_handler.create_tables_on_init()

# Render application homepage
homepage()
