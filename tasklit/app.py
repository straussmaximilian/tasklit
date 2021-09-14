from sqlalchemy import create_engine

import tasklit.settings.consts as settings
import tasklit.src.utils.helpers as helper_functions

from tasklit.pages.homepage import homepage


# Create application resource folders, e.g. logs, data, etc.
for folder in (settings.BASE_DATA_DIR, settings.BASE_LOG_DIR):
    helper_functions.create_folder_if_not_exists(folder)

# Initialize sql alchemy engine to access process information
sql_engine = create_engine(settings.APP_ENGINE_PATH, echo=False)

# Render application homepage
homepage(sql_engine)
