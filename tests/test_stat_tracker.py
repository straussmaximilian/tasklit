"""Unittests for TaskStatisticsTracker."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from tasklit.settings.consts import TaskInformation
from tasklit.src.classes.stat_tracker import TaskStatisticsTracker


class TaskStatisticsTrackerTestCase(unittest.TestCase):
    """Unittests for application UI layout elements."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters.

        engine_uri (str): mock engine URI path.
        table_name (str): sample table name.
        tables (List[MagicMock]): list of mock objects representing
            DB tables.
        sql_repository (SQLDataRepository): instantiated sql repository object.
        """
        super(TaskStatisticsTrackerTestCase, cls).setUpClass()
        cls.task = TaskInformation("sample_job", "echo 'Max is awesome!'", 0.1)
        cls.empty_task_dataframe = pd.DataFrame()
        cls.non_empty_task_dataframe = pd.DataFrame()

        with patch(
            "tasklit.src.classes.stat_tracker.app_db_handler"
        ) as mock_db_handler:
            mock_db_handler.load_dataframe.return_value = (
                cls.empty_task_dataframe
            )
            mock_db_handler.save_dataframe.return_value = True
            cls.task_tracker = TaskStatisticsTracker(cls.task)

    def test_print_stats_df(self):
        print(self.task_tracker._stats_df)
