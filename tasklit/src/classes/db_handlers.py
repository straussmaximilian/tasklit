import pandas as pd

from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from tasklit.settings.consts import BASE_DATA_DIR


class DatabaseHandler(ABC):
    """
    An abstract class to define key methods for loading and storing
    dataframe objects that every database handler must have.

    Implements dependency inversion principle, e.g.
    in the future we could have multiple database handlers, working with
    different types of storage, e.g. sql, feather, hdf, etc.
    """

    @abstractmethod
    def save_dataframe(self, *args, **kwargs):
        """
        Abstract method responsible for converting a dataframe
        to a specific storage format.
        """
        pass

    @abstractmethod
    def load_dataframe(self, *args, **kwargs):
        """
        Abstract method responsible for loading a dataframe
        from a specific storage format.
        """
        pass


class SQLiteDatabaseHandler(DatabaseHandler):
    """
    Class responsible for dataframe conversion to/from SQLite.

    Parameters:
    ___________
    _db_name: str
        database name.
    _engine_path: str
        string indicating and the type of and path to the database file.
    _sql_engine: sqlalchemy.engine
        sql alchemy engine to use to create the database.
    process_table_name: str
        name of the table with directly related process information, e.g. pid, status, etc.
    process_stats: str
        name of the table with related process execution stats, e.g. execution count, etc.

    Methods:
    ________
    save_dataframe()
        implementation of the abstract interface method: save a dataframe to an SQLite database file.
    load_dataframe()
        implementation of the abstract interface method: load a dataframe from an SQLite database file.
    """
    def __init__(self):
        self._db_name = "process.db"
        self._db_type = "sqlite"
        self._engine_path = f"{self._db_type}:///{BASE_DATA_DIR}/{self._db_name}"
        self._sql_engine = create_engine(self._engine_path, echo=False)
        self.process_table_name = 'processes'
        self.stats_table_name = 'process_stats'

    def save_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Save dataframe with process information to a local sql alchemy DB file.

        Args:
            df: process information df.
            table_name: name of the SQL table to write to.

        Raises:
            OperationalError: if any sqlalchemy errors are thrown.
        """
        try:
            df.to_sql(
                table_name,
                con=self._sql_engine,
                if_exists="append",
                index=False
            )
        except OperationalError as exc:
            raise exc

    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql_table(table_name, con=self._sql_engine)
