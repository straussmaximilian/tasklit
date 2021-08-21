import unittest

from unittest.mock import (
    mock_open,
    patch,
    MagicMock
)

import pandas as pd

from app.src.utils.helpers import *


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
        WHEN it is passed to the get_task_id function
        THEN check that the newly returned ID is equal to
        the largest ID in the list + 1.
        """
        self.assertEqual(get_task_id(self.test_df), max(self.task_ids) + 1)

    @patch('os.path.getmtime')
    def test_check_last_process_info_update(self,
                                            mock_getmtime: MagicMock):
        """
        GIVEN a job name that corresponds to a job log file
        WHEN it is passed to the check_last_process_info_update function
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
        WHEN it is passed to the read_log function
        THEN check that the function  returns a list of lines from the file.
        """
        with patch('builtins.open', mock_open(read_data="Line of text")):
            self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)

        with patch('builtins.open') as mock_open_raises:
            mock_open_raises.side_effect = FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)

    @patch('psutil.wait_procs')
    @patch.object(psutil.Process, 'kill')
    @patch.object(psutil.Process, 'terminate')
    @patch('psutil.Process')
    def test_terminate_process(self,
                               mock_psutil_process: MagicMock,
                               mock_psutil_terminate: MagicMock,
                               mock_psutil_kill: MagicMock,
                               mock_wait_procs: MagicMock):
        # Case 1: Process doesn't have any child processes
        mock_psutil_process.return_value = MagicMock()
        mock_psutil_process.children.return_value = []
        mock_wait_procs.return_value = ([], [])
        mock_psutil_terminate.terminate.return_value = True
        mock_psutil_kill.kill.return_value = True

        terminate_process(self.test_process_id)

        mock_psutil_terminate.assert_called()
        mock_psutil_kill.assert_called()




























