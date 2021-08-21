import unittest

from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd

from app.src.utils.helpers import *


class UtilFunctionsTestCase(unittest.TestCase):
    """
    Unittests for application utility functions.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super(UtilFunctionsTestCase, cls).setUpClass()
        cls.test_job_name = "infallible_strauss"
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

    def test_get_task_id(self) -> None:
        """
        GIVEN a dataframe with process information and related task IDs
        WHEN it is passed to the get_task_id function
        THEN check that the newly returned ID is equal to
        the largest ID in the list + 1.
        """
        self.assertEqual(get_task_id(self.test_df), max(self.task_ids) + 1)

    @patch('os.path.getmtime')
    def test_check_last_process_info_update(self,
                                            mock_getmtime: MagicMock) -> None:
        # Case 1: file is present and getmtime does not raise OSError
        mock_getmtime.return_value = 1629554559
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.return_value = "2018-12-25 09:27:53"

            self.assertEqual(check_last_process_info_update(
                self.test_job_name
            ), mock_datetime.fromtimestamp.return_value)

        # Case 2: file operation fails -> OSError is raised
        mock_getmtime.side_effect = OSError("Oopsy daisies")
        with self.assertRaises(OSError):
            check_last_process_info_update(self.test_job_name)


























