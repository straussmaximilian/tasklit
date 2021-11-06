"""Classes responsible for handling data storage.

Use the repository pattern to invert dependency between application logic
and lower level database operations. Enables flexibility to add multiple
storage repositories, working with different storage types,
e.g. sql, feather, hdf, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type

import pandas as pd
from sqlalchemy import create_engine, engine, inspect
from sqlalchemy.exc import OperationalError

from tasklit.settings.database_tables import DatabaseTable


class DataRepository(ABC):
    """Define key methods for loading and storing dataframe objects.

    Parameters:
    ___________
    process_table_name: str
        name of the table with related process information, e.g.
            pid, status, etc.
    process_stats: str
        name of the table with related process execution stats, e.g.
            execution count, etc.
    """

    process_table_name: str = "processes"
    stats_table_name: str = "process_stats"

    @abstractmethod
    def save_dataframe(self, *args: Any, **kwargs: Any) -> None:
        """Convert a dataframe to a specific storage format."""
        raise NotImplementedError

    @abstractmethod
    def load_dataframe(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Load a dataframe from a specific storage format."""
        raise NotImplementedError


class SQLDataRepository(DataRepository):
    """Convert dataframes to / from SQL.

    Parameters:
    ___________
    _db_name: str
        database name.
    _engine_path: str
        string indicating and the type of and path to the database file.
    _sql_engine: sqlalchemy.engine
        sql alchemy engine to use to create the database.

    Methods:
    ________
    _table_exists()
        check if a table exists in the DB.
    create_tables_on_init()
        create DB tables on app init.
    save_dataframe()
        implementation of the abstract interface method: save a dataframe to
            an SQLite database file.
    load_dataframe()
        implementation of the abstract interface method: load a dataframe from
            an SQLite database file.
    """

    def __init__(self, sql_engine_uri: str, tables: List[Type[DatabaseTable]]):
        """Initialization method."""
        self._db_name = "process.db"
        self._tables = tables
        self._sql_engine: engine = create_engine(sql_engine_uri, echo=False)

    @staticmethod
    def _table_exists(sql_alchemy_engine: engine, table_name: str) -> bool:
        """Check if an SQL Alchemy table exists in the database."""
        sql_alchemy_inspect = inspect(sql_alchemy_engine)

        return sql_alchemy_inspect.dialect.has_table(
            sql_alchemy_engine.connect(), table_name
        )

    def create_tables_on_init(self) -> None:
        """Create tables in the database if they don't already exist."""
        for table in self._tables:
            if not self._table_exists(self._sql_engine, table.table_name):
                self.save_dataframe(
                    pd.DataFrame(table.table_format),
                    table.table_name,
                    col_data_types=table.column_dtypes,
                )

    def save_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        col_data_types: Dict[str, Any] = None,
    ) -> None:
        """Save a dataframe to an sql file.

        Args:
            df (pd.DataFrame): process information df.
            table_name (str): name of the SQL table to write to.
            if_exists (str): indicate what to do if the table already exists,
                e.g. append, replace.
            col_data_types (Dict[str, Any]): data types to use for
                columns when creating the SQL schema.

        Raises:
            OperationalError: if any sqlalchemy errors are thrown.
        """
        try:
            df.to_sql(
                table_name,
                con=self._sql_engine,
                if_exists=if_exists,
                index=False,
                dtype=col_data_types,
            )
        except OperationalError as exc:
            raise exc

    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        """Load a dataframe from an sql file.

        Args:
            table_name: name of the database table to use.
        """
        return pd.read_sql_table(table_name, con=self._sql_engine)
