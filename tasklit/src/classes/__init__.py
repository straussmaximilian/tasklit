"""Initialize application database handler."""

from tasklit.settings.consts import SQLITE_APP_ENGINE
from tasklit.settings.database_tables import tables_to_register
from tasklit.src.classes.storage_repositories import SQLDataRepository

app_db_handler = SQLDataRepository(SQLITE_APP_ENGINE, tables_to_register)
