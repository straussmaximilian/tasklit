"""Unittests for TaskObserver."""

import unittest
from inspect import signature
from unittest.mock import MagicMock, patch

from tasklit.src.classes.exceptions import ObserverArgumentsMissing
from tasklit.src.classes.observers import TaskObserver


class TaskObserverTestCase(unittest.TestCase):
    """Test custom task observer decorator implementation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters."""
        super(TaskObserverTestCase, cls).setUpClass()

        with patch(
            "tasklit.src.classes.stat_tracker.TaskStatisticsTracker"
        ) as mock_tracker:
            mock_tracker.update_task_stats.return_value = True
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
        pass
