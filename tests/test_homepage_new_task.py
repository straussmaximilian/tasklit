import unittest

from unittest.mock import (
    patch,
    MagicMock
)

import pandas as pd

from app.pages.layouts.homepage_new_task import layout_homepage_define_new_task


class HomepageNewTaskTestCase(unittest.TestCase):
    """
    Unittests for application homepage 'new task' layout.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        test_df: pd.DataFrame
            Sample dataframe to mimic df with process information.
        """
        super(HomepageNewTaskTestCase, cls).setUpClass()
        cls.command = "ping me 123"
        cls.test_df = pd.DataFrame(
            {
                "task_id": [1],
                "created": ["2020-01-01 00:00:00"],
                "process id": [123],
                "job name": ["nostalgic_strauss"],
                "command": ["ping 123"],
                "last update": [None],
                "running": [False],
            }
        )

    @patch('app.pages.layouts.homepage_new_task.helper_functions.refresh_app')
    @patch('app.pages.layouts.homepage_new_task.helper_functions.submit_job')
    @patch('app.pages.homepage.st.info')
    @patch('app.pages.layouts.homepage_new_task.helper_functions.test_command_run')
    @patch('app.pages.layouts.homepage_new_task.get_job_name')
    @patch('app.pages.homepage.st.button')
    @patch('app.pages.homepage.st.text_input')
    def test_app_running_test_command(self,
                                      mock_st_input: MagicMock,
                                      mock_st_button: MagicMock,
                                      mock_get_job_name: MagicMock,
                                      mock_test_command_run: MagicMock,
                                      mock_st_info: MagicMock,
                                      mock_submit: MagicMock,
                                      mock_refresh: MagicMock):
        """
        GIVEN a job name and a command to execute
        WHEN test command execution is requested
        THEN check that related test command run methods are executed.
        """
        mock_get_job_name.return_value = "sleepy_strauss"
        mock_st_input.side_effect = [
            mock_get_job_name.return_value,
            self.command
        ]
        mock_st_button.return_value = True

        layout_homepage_define_new_task(self.test_df, "sql_engine")

        mock_st_info.assert_called_with(f"Running '{self.command}'")
        mock_test_command_run.assert_called_with(self.command)
        
