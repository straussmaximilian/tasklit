from tasklit.settings.consts import SQLITE_APP_ENGINE
from tasklit.src.classes.db_handlers import SQLDatabaseHandler


app_db_handler = SQLDatabaseHandler(SQLITE_APP_ENGINE)
