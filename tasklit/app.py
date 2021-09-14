from sqlalchemy import create_engine

import tasklit.settings.consts as settings
import tasklit.src.utils.helpers as helper_functions

from tasklit.pages.homepage import homepage

# Check if the log folder exists and - if not - create one.
helper_functions.create_folder_if_not_exists(settings.BASE_LOG_DIR)

# Initialize sql alchemy engine to access process information
sql_engine = create_engine(settings.APP_ENGINE_PATH, echo=False)

# Render application homepage
homepage(sql_engine)
