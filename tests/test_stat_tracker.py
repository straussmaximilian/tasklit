"""Unittests for TaskStatisticsTracker."""

import unittest
from dataclasses import asdict
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

        task_df_columns: List[str]
            task DF columns.
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
        cls.task_df_columns = [
            "task_name",
            "command",
            "average_duration",
            "executions",
        ]
        cls.task = TaskInformation("sample_job", "echo 'Max is awesome!'", 1.2)
        cls.new_task = TaskInformation(
            "sample_job", "echo 'Max is awesome!'", 2.3
        )
        cls.missing_task = TaskInformation(
            "great_job", "echo 'Max is awesomer!'", 2.3
        )
        cls.empty_task_dataframe = pd.DataFrame(columns=cls.task_df_columns)
        cls.non_empty_task_dataframe = pd.DataFrame(
            columns=cls.task_df_columns
        )

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
        assert_frame_equal(
            self.task_tracker._load_stats_df(), self.empty_task_dataframe
        )

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

        assert_frame_equal(df_call[0][0], self.empty_task_dataframe)
        self.assertEqual(expected_call, (df_call[0][1], df_call[1]))

    def test_task_exists_missing_task(self):
        """Unittest for TaskStatisticsTracker._task_exists().

        GIVEN task information and an empty task dataframe
        WHEN _task_exists() method is called
        THEN check that the task is identified as missing.
        """
        self.task_tracker._stats_df = self.empty_task_dataframe

        self.assertEqual(self.task_tracker._task_exists(), False)

    def test_task_exists_existing_task(self):
        """Unittest for TaskStatisticsTracker._task_exists().

        GIVEN task information and a dataframe with the same task
        WHEN _task_exists() method is called
        THEN check that the task is identified as existing.
        """
        self.task_tracker._add_new_task()

        self.assertEqual(self.task_tracker._task_exists(), True)

    def test_add_new_task(self):
        """Unittest for TaskStatisticsTracker._add_new_task().

        GIVEN task information and a task dataframe
        WHEN _add_new_task() method is called
        THEN check that a new row has been added to the dataframe.
        """
        expected_df = self.empty_task_dataframe.append(
            asdict(self.task), ignore_index=True
        )

        self.task_tracker._add_new_task()

        assert_frame_equal(expected_df, self.task_tracker._stats_df)

    def test_get_idx_row_to_update(self):
        """Unittest for TaskStatisticsTracker._get_idx_row_to_update().

        GIVEN task information and a task dataframe
        WHEN _get_idx_row_to_update() method is called
        THEN check correct row index is returned.
        """
        self.assertEqual(self.task_tracker._get_idx_row_to_update(), 0)

    def test_get_idx_row_to_update_raises_error(self):
        """Unittest for TaskStatisticsTracker._get_idx_row_to_update().

        GIVEN task information and a task dataframe
        WHEN _get_idx_row_to_update() method is called
        THEN that correct error is raised in case we failed to find the task.
        """
        self.task_tracker._task_info = self.missing_task

        with self.assertRaises(IndexError):
            self.task_tracker._get_idx_row_to_update()

    def test_update_existing_task(self):
        """Unittest for TaskStatisticsTracker._update_existing_task().

        GIVEN task information and a task dataframe
        WHEN _update_existing_task() method is called
        THEN check existing task information is correctly updated.
        """
        self.task_tracker._task_info = self.task
        self.task_tracker._add_new_task()
        self.task_tracker._task_info = self.new_task

        self.task_tracker._update_existing_task()

        self.assertEqual(
            self.task_tracker._stats_df.at[0, "average_duration"], 1.75
        )
        self.assertEqual(self.task_tracker._stats_df.at[0, "executions"], 2)
        self.assertEqual(
            self.task_tracker._stats_df.at[0, "task_name"],
            self.new_task.task_name,
        )
        self.assertEqual(
            self.task_tracker._stats_df.at[0, "command"],
            self.new_task.command,
        )

    @patch.object(TaskStatisticsTracker, "_add_new_task")
    @patch.object(TaskStatisticsTracker, "_task_exists")
    def test_update_task_stats_add_new(
        self, mock_exists: MagicMock, mock_add: MagicMock
    ):
        """Unittest for TaskStatisticsTracker.update_task_stats().

        GIVEN task information and a task dataframe
        WHEN update_task_stats() method is called
        THEN check that correct decision is made to add a new task.
        """
        mock_exists.return_value = False
        mock_add.return_value = True

        self.task_tracker.update_task_stats()

        mock_exists.assert_called_once()
        mock_add.assert_called_once()

    @patch.object(TaskStatisticsTracker, "_save_stats_df")
    @patch.object(TaskStatisticsTracker, "_task_exists")
    def test_update_task_stats_add_new(
        self, mock_exists: MagicMock, mock_save: MagicMock
    ):
        """Unittest for TaskStatisticsTracker.update_task_stats().

        GIVEN task information and a task dataframe
        WHEN update_task_stats() method is called
        THEN check that correct decision is made to update the task.
        """
        mock_exists.return_value = False
        mock_save.return_value = True

        self.task_tracker.update_task_stats()

        mock_exists.assert_called_once()
        mock_save.assert_called_once()
