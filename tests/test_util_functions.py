import random
import unittest

from unittest.mock import (
    create_autospec,
    mock_open,
    patch,
    MagicMock
)

import pandas as pd
import psutil

from app.src.utils.helpers import *
from app.settings.consts import WEEK_DAYS


class UtilFunctionsTestCase(unittest.TestCase):
    """
    Unittests for application utility functions.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super(UtilFunctionsTestCase, cls).setUpClass()
        cls.test_log_filename = "sample_logfile.txt"
        cls.log_readlines_output = ["Line of text"]
        cls.test_job_name = "infallible_strauss"
        cls.test_process_id = 12345
        cls.task_ids = [1]
        cls.test_df = pd.DataFrame(
            {
                "task_id": cls.task_ids,
                "created": [None],
                "process id": [None],
                "job name": [cls.test_job_name],
                "command": [None],
                "last update": [None],
                "running": [None],
            }
        )

    def test_get_task_id(self):
        """
        GIVEN a dataframe with process information and related task IDs
        WHEN it is passed to the 'get_task_id' function
        THEN check that the newly returned ID is equal to
        the largest ID in the list + 1.
        """
        self.assertEqual(get_task_id(self.test_df), max(self.task_ids) + 1)

    @patch('os.path.getmtime')
    def test_check_last_process_info_update(self,
                                            mock_getmtime: MagicMock):
        """
        GIVEN a job name that corresponds to a job log file
        WHEN it is passed to the 'check_last_process_info_update' function
        THEN check that for correct outputs are produced.
        """
        # Case 1: file is present and getmtime does not raise OSError
        mock_getmtime.return_value = 1629554559
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.return_value = "2018-12-25 09:27:53"

            self.assertEqual(check_last_process_info_update(
                self.test_job_name
            ), mock_datetime.fromtimestamp.return_value)

            mock_getmtime.assert_called()
            mock_datetime.fromtimestamp.assert_called()

        # Case 2: file operation fails -> OSError is raised
        mock_getmtime.side_effect = OSError("Oopsy daisies")
        with self.assertRaises(OSError):
            check_last_process_info_update(self.test_job_name)

    def test_read_log(self):
        """
        GIVEN a path to a file
        WHEN it is passed to 'read_log' function
        THEN check that the function  returns a list of lines from the file.
        """
        with patch('builtins.open', mock_open(read_data="Line of text")):
            self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)

        with patch('builtins.open') as mock_open_raises:
            mock_open_raises.side_effect = FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)

    @patch('psutil.wait_procs')
    def test_terminate_child_processes_processes_found(self,
                                                       mock_wait_procs: MagicMock):
        """
        GIVEN an object of a parent process that has spawned child processes
        WHEN it is passed to 'terminate_child_processes' function
        THEN check that the related process termination methods are called.
        """
        parent_process = MagicMock()
        parent_process.children.return_value = [
            MagicMock(
                name="Child Proc 1",
                terminate=lambda: True
            ),
            MagicMock(
                name="Child Proc 2",
                terminate=lambda: True
            )
        ]
        mock_wait_procs.return_value = ([], [
            MagicMock(return_value=lambda: True),
            MagicMock(return_value=lambda: True)
        ])

        # Check that process.terminate() is being called on child processes
        for child_process in parent_process.children.return_value:
            mock_terminate = create_autospec(child_process.teminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_called()
            mock_terminate.assert_called()

        # Check that process.terminate() is being called on any child processes
        # that might have been left alive.
        for alive_process in mock_wait_procs.return_value[1]:
            mock_terminate = create_autospec(alive_process.terminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_called()
            mock_terminate.assert_called()

    @patch('psutil.wait_procs')
    def test_terminate_child_processes_processes_not_found(self,
                                                           mock_wait_procs: MagicMock):
        """
        GIVEN an object of a parent process that has NOT spawned child processes
        WHEN it is passed to 'terminate_child_processes' function
        THEN check that the related process termination methods are NOT called.
        """
        parent_process = MagicMock()
        parent_process.children.return_value = []
        mock_wait_procs.return_value = ([], [])

        # Check that process.terminate() is not called
        for child_process in parent_process.children.return_value:
            mock_terminate = create_autospec(child_process.teminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_not_called()
            mock_terminate.assert_not_called()

        # Check that process.terminate() is not called
        for alive_process in mock_wait_procs.return_value[1]:
            mock_terminate = create_autospec(alive_process.terminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_not_called()
            mock_terminate.assert_not_called()

    @patch('app.src.utils.helpers.terminate_child_processes')
    def test_terminate_process_with_child_processes(self,
                                                    mock_terminate_child_procs: MagicMock):
        """
        GIVEN an ID of an existing test process
        WHEN it is passed to 'terminate_process' function
        THEN check that the related process termination methods have been called.
        """
        with patch('app.src.utils.helpers.psutil.Process') as mock_psutil_process:
            mock_psutil_process.return_value = MagicMock()
            mock_terminate_child_procs.return_value = True
            mock_psutil_process.terminate.return_value = lambda: True
            mock_terminate = create_autospec(mock_psutil_process.terminate, return_value=True)

            mock_psutil_process.kill.return_value = lambda: True
            mock_kill = create_autospec(mock_psutil_process.kill, return_value=True)

            terminate_process(self.test_process_id)

            mock_terminate_child_procs.assert_called()
            mock_terminate.assert_called()
            mock_kill.assert_called()

    def test_terminate_process_raises_error(self):
        """
        GIVEN an ID of a test process that does not exist
        WHEN it is passed to 'terminate_process' function
        THEN check that an error is raised.
        """
        with patch('app.src.utils.helpers.psutil.Process') as mock_psutil_process:
            mock_psutil_process.side_effect = psutil.NoSuchProcess("Cannot find the process.")
            with self.assertRaises(psutil.NoSuchProcess):
                terminate_process(self.test_process_id)

    def test_check_weekday(self):
        """
        GIVEN a datetime object representing today's date
        WHEN it is passed to 'function_should_execute' function
        THEN check that correct decision is made.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            for day_number, day in WEEK_DAYS.items():
                mock_datetime.now.weekday.return_value = day_number
                # Case 1: Check that function returns 'True' today is
                # in the list of days of the week.
                self.assertEqual(function_should_execute(
                    mock_datetime.now,
                    list(WEEK_DAYS.values())
                ), True)

                # Case 2: Check that function returns 'True' if a list of days
                # of the week has not been provided at all.
                self.assertEqual(
                    function_should_execute(
                        mock_datetime.now,
                        []
                    ), True)

                # Case 3: Check that function returns 'False' if today is not
                # in the list of days of the week.
                self.assertEqual(
                    function_should_execute(
                        mock_datetime.now,
                        ["Uknown Day"]
                    ), False)

                # Case 4: Check that a KeyError is raised if day number is missing
                # in the mapping of day numbers to days.
                with patch('app.settings.consts.WEEK_DAYS') as mocked_weekdays:
                    mocked_weekdays.__getitem__.side_effect = KeyError("Failed to map the day.")
                    with self.assertRaises(KeyError):
                        function_should_execute(
                            mock_datetime.now,
                            list(WEEK_DAYS.values())
                        )
