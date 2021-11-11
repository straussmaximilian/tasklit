"""Database table representation."""
from abc import ABC, abstractmethod
from typing import Any, Dict

from sqlalchemy.types import Boolean, DateTime, Integer, String


class DatabaseTable(ABC):
    """Define a standard for how database table information must look like."""

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the name of the table."""
        ...

    @property
    @abstractmethod
    def table_format(self) -> Dict[str, list]:
        """Return the format of the table."""
        ...

    @property
    @abstractmethod
    def column_dtypes(
        self,
    ) -> Dict[str, Any]:
        """Return SQLAlchemy data types for table columns."""
        ...

    def get_table_metadata(self) -> Dict[str, Any]:
        """Return table metadata.

        - format to be used to create the table
        - data types for each column
        """
        return {
            "format": self.table_format,
            "dtypes": self.column_dtypes,
        }


class ProcessTable(DatabaseTable):
    """Metadata information for table with process information."""

    table_name: str = "processes"
    table_format: Dict[str, list] = {
        "task_id": [],
        "created": [],
        "process id": [],
        "job name": [],
        "command": [],
        "last update": [],
        "running": [],
    }
    column_dtypes = {
        "task_id": Integer,
        "process id": Integer,
        "command": String,
        "job name": String,
        "created": DateTime,
        "last update": DateTime,
        "running": Boolean,
    }


class StatsTable(DatabaseTable):
    """Metadata information for table with process stats information."""

    table_name: str = "process_stats"
    table_format: Dict[str, list] = {
        "task_name": [],
        "command": [],
        "average_duration": [],
        "executions": [],
    }
    column_dtypes = {
        "task_name": String,
        "command": String,
        "average_duration": Integer,
        "executions": Integer,
    }


# Initialize a list of tables to be created in the database
tables_to_register = [ProcessTable, StatsTable]
