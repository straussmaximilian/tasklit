"""Unittests for TaskStatisticsTracker."""

import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd
from pandas.util.testing import assert_frame_equal

from tasklit.settings.consts import TaskInformation
from tasklit.src.classes.stat_tracker import TaskStatisticsTracker


class TaskStatisticsTrackerTestCase(unittest.TestCase):
    """Unittests for application UI layout elements."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters.

        task: TaskInformation
            sample task information.
        empty_task_dataframe: pd.DataFrame
            empty DF to test adding a new task row.
        non_empty_task_dataframe: pd.DataFrame
            non-empty DF to test updating a task row.
        task_tracker: TaskStatisticsTracker
            instantiated task tracker with an empty DF.
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

    def test_load_stats_df(self):
        """Unittest for TaskStatisticsTracker._load_stats_df().

        GIVEN a table name
        WHEN _load_stats_df() method is called
        THEN check that correct dataframe output is returned.
        """
        assert_frame_equal(self.task_tracker._load_stats_df(), pd.DataFrame())

        self.task_tracker._db_handler.assert_has_calls(
            [
                call.load_dataframe("process_stats"),
            ]
        )

    def test_save_stats_df_append(self):
        """Unittest for TaskStatisticsTracker._save_stats_df().

        GIVEN a dataframe with task information
        WHEN _save_stats_df() method is called
        THEN check that related database handler method is called.
        """
        expected_call = ("process_stats", {"if_exists": "replace"})
        self.task_tracker._save_stats_df(self.empty_task_dataframe)

        df_call = self.task_tracker._db_handler.save_dataframe.call_args_list[
            0
        ]

        assert_frame_equal(df_call[0][0], pd.DataFrame())
        self.assertEqual(expected_call, (df_call[0][1], df_call[1]))
