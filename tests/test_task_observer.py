"""Unittests for TaskObserver."""

import unittest
from inspect import signature
from unittest.mock import MagicMock, patch

from tasklit.src.classes.exceptions import ObserverArgumentsMissing
from tasklit.src.classes.observers import TaskObserver, TaskStatisticsTracker


class TaskObserverTestCase(unittest.TestCase):
    """Test custom task observer decorator implementation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters."""
        super(TaskObserverTestCase, cls).setUpClass()

        cls.func_arg_values = ("arg1", "job1", "arg2", "cool_command")
        cls.observer_correct_args = TaskObserver(cls.observed_func)

    @classmethod
    def observed_func(cls, random_arg_1, job_name, random_arg_2, command):
        """Sample function to test task observer decorator."""
        return f"{random_arg_1} - {job_name} - {random_arg_2} - {command}"

    def test_function_signature(self):
        """Test observer identifies callable signature.

        GIVEN a callable
        WHEN passed to the observer decorator
        THEN check that the signature of the callable is
            correctly identified.
        """
        self.assertEqual(
            self.observer_correct_args._signature,
            signature(self.observed_func),
        )

    def test_function_argument_order(self):
        """Test observer identifies arg order.

        GIVEN a callable
        WHEN passed to the observer decorator
        THEN check that callable argument order is
            correctly identified
        """
        self.assertEqual(
            self.observer_correct_args._function_argument_order,
            {"job_name": 1, "command": 3},
        )

    def test_check_arguments_found(self):
        """Test TaskObserver._check_arguments_found().

        GIVEN a callable
        WHEN passed to the observer decorator
        THEN check that no error is thrown if the arguments
            have been found.
        """
        self.observer_correct_args._check_arguments_found()

    def test_check_arguments_found_raises_error(self):
        """Test TaskObserver._check_arguments_found().

        GIVEN a callable
        WHEN passed to the observer decorator
        THEN check that an error is thrown if the arguments
            have NOT been found ('job_name' is missing).
        """
        with self.assertRaises(ObserverArgumentsMissing):
            TaskObserver(
                lambda random_arg_1, random_arg_2, command: (
                    f"{random_arg_1} - {random_arg_2} - {command}"
                )
            )

    def test_get_argument(self):
        """Test TaskObserver._get_argument().

        GIVEN function argument order
        WHEN _get_argument() is called
        THEN check that correct arg name is returned.
        """
        self.assertEqual(
            self.observer_correct_args._get_argument(
                "job_name", self.func_arg_values
            ),
            "job1",
        )

    @patch.object(TaskStatisticsTracker, "update_task_stats")
    @patch.object(TaskStatisticsTracker, "_load_stats_df")
    def test_extract_task_details(self,
                                  mock_load: MagicMock,
                                  mock_update: MagicMock):
        """Test TaskObserver.__call__().

        GIVEN a decorated callable
        WHEN called
        THEN check that correct task details
            are extracted by the decorator.
        """
        mock_load.return_value = True
        mock_update.return_value = True

        self.observer_correct_args.__call__(
            "arg1", "job1", "arg2", "cool_command"
        )

        self.assertEqual(
            self.observer_correct_args._task.task_name,
            "job1",
        )

        self.assertEqual(
            self.observer_correct_args._task.command,
            "cool_command",
        )

        self.assertEqual(
            self.observer_correct_args._task.average_duration,
            0.0,
        )

        self.assertEqual(
            self.observer_correct_args._task.executions,
            1,
        )

    @patch.object(TaskStatisticsTracker, "_load_stats_df")
    @patch.object(TaskObserver, "_run_task_tracker")
    def test_tast_tracker_call(self, mock_run: MagicMock, mock_load: MagicMock):
        """Test TaskObserver._run_task_tracker().

        GIVEN a decorated callable
        WHEN called
        THEN check that the task tracker is called.
        """
        mock_run.return_value = True
        mock_load.return_value = True

        self.observer_correct_args.__call__(
            "arg1", "job1", "arg2", "cool_command"
        )

        mock_run.assert_called_once()
