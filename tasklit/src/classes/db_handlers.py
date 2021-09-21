"""
Classes responsible for handling data storage. Implement dependency inversion principle
by inheriting from an abstract class, e.g. in the future we could have multiple database handlers,
working with different types of storage, e.g. sql, feather, hdf, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError


class DatabaseHandler(ABC):
    """
    An abstract class to define key methods for loading and storing
    dataframe objects that every database handler must have.
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


class SQLDatabaseHandler(DatabaseHandler):
    """
    Class responsible for dataframe conversion to/from SQL.
    Type of the SQL database is defined by the sqlalchemy engine URI.

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

    def __init__(self, sql_engine_uri: str, tables: Dict[str, pd.DataFrame]):
        self._db_name = "process.db"
        self._tables = tables
        self._sql_engine = create_engine(sql_engine_uri, echo=False)
        self.process_table_name = 'processes'
        self.stats_table_name = 'process_stats'

    @staticmethod
    def _table_exists(engine, table_name) -> bool:
        ins = inspect(engine)
        return ins.dialect.has_table(engine.connect(), table_name)

    def create_tables_on_init(self):
        for table_name, table_format in self._tables.items():
            if not self._table_exists(self._sql_engine, self.process_table_name):
                self.save_dataframe(pd.DataFrame(table_format), table_name)

    def save_dataframe(self, df: pd.DataFrame, table_name: str,
                       if_exists: str = "append") -> None:
        """
        Save a dataframe with process related information to an sql file.

        Args:
            df: process information df.
            table_name: name of the SQL table to write to.
            if_exists: string indicating what to do if table already exists, e.g. append, replace.

        Raises:
            OperationalError: if any sqlalchemy errors are thrown.
        """
        try:
            df.to_sql(
                table_name,
                con=self._sql_engine,
                if_exists=if_exists,
                index=False
            )
        except OperationalError as exc:
            raise exc

    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        Load a dataframe with process related information from an sql file.

        Args:
            table_name: name of the database table to use.
        """
        try:
            return pd.read_sql_table(table_name, con=self._sql_engine)
        except ValueError:
            pass
