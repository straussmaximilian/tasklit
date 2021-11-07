import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd
from sqlalchemy.types import Boolean, Integer, String

from tasklit.src.classes.data_repository import SQLDataRepository


class SQLDataRepositoryTestCase(unittest.TestCase):
    """Unittests for application UI layout elements."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters."""
        super(SQLDataRepositoryTestCase, cls).setUpClass()
        cls.engine_uri = "test-engine-uri"
        cls.tables = [
            MagicMock(
                table_name="Table 1",
                table_format={
                    "col1": [],
                    "col2": [],
                    "col3": [],
                },
                column_dtypes={
                    "col1": Integer,
                    "col2": String,
                    "col3": Boolean,
                },
            ),
            MagicMock(
                table_name="Table 2",
                table_format={
                    "col4": [],
                    "col5": [],
                    "col6": [],
                },
                column_dtypes={
                    "col4": String,
                    "col5": Boolean,
                    "col6": Integer,
                },
            ),
        ]
        with patch(
            "tasklit.src.classes.data_repository.create_engine"
        ) as mock_create_engine:
            mock_create_engine.return_value = True
            cls.sql_repository = SQLDataRepository(cls.engine_uri, cls.tables)

    @patch("tasklit.src.classes.data_repository.inspect")
    def test_table_exists(self, mock_inspect: MagicMock):
        """Unittest for '_table_exists()'

        GIVEN a name of a table that already exists in the DB
        WHEN repository._table_exists() method is called
        THEN check that correct value is returned.
        """
        table_name = self.tables[0].table_name
        mock_inspect.return_value.dialect.has_table = lambda x, y: True

        mock_engine = MagicMock()
        mock_engine.connect.return_value = lambda: True

        self.assertEqual(
            self.sql_repository._table_exists(mock_engine, table_name), True
        )

    @patch(
        "tasklit.src.classes.data_repository.SQLDataRepository.save_dataframe"
    )
    @patch(
        "tasklit.src.classes.data_repository.SQLDataRepository._table_exists"
    )
    def test_create_tables_on_init(
        self,
        mock_exists: MagicMock,
        mock_save: MagicMock,
    ):
        """Unittest for 'create_tables_on_init()'.

        GIVEN a name of a table that already exists in the DB
        WHEN repository._table_exists() method is called
        THEN check that correct value is returned.
        """
        mock_exists.side_effect = [True, False]

        self.sql_repository.create_tables_on_init()

        mock_save.assert_called_once()
