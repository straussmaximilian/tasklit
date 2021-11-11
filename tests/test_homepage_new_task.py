import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pandas as pd

from tasklit.pages.layouts.homepage_new_task import (
    layout_homepage_define_new_task,
)


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
        cls.job_name = "sleepy_strauss"

    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.refresh_app"
    )
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.submit_job"
    )
    @patch("tasklit.pages.homepage.st.info")
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.test_command_run"
    )
    @patch("tasklit.pages.layouts.homepage_new_task.get_job_name")
    @patch("tasklit.pages.homepage.st.button")
    @patch("tasklit.pages.homepage.st.text_input")
    def test_app_running_test_command(
        self,
        mock_st_input: MagicMock,
        mock_st_button: MagicMock,
        mock_get_job_name: MagicMock,
        mock_test_command_run: MagicMock,
        mock_st_info: MagicMock,
        mock_submit: MagicMock,
        mock_refresh: MagicMock,
    ):
        """
        GIVEN a job name and a command to execute
        WHEN test command execution is requested
        THEN check that related test command run methods are executed.
        """
        mock_get_job_name.return_value = "sleepy_strauss"
        mock_st_input.side_effect = [
            mock_get_job_name.return_value,
            self.command,
        ]
        mock_st_button.return_value = True

        layout_homepage_define_new_task(self.test_df)

        mock_st_info.assert_called_with(f"Running '{self.command}'")
        mock_test_command_run.assert_called_with(self.command)

    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.refresh_app"
    )
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.submit_job"
    )
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.get_command_execution_start"
    )
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.get_interval_duration"
    )
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.get_execution_interval_information"
    )
    @patch("tasklit.pages.layouts.homepage_new_task.st.columns")
    @patch("tasklit.pages.homepage.st.info")
    @patch(
        "tasklit.pages.layouts.homepage_new_task.helper_functions.test_command_run"
    )
    @patch("tasklit.pages.layouts.homepage_new_task.get_job_name")
    @patch("tasklit.pages.homepage.st.text_input")
    @patch("tasklit.pages.homepage.st.button")
    def test_app_submit_command(
        self,
        mock_st_button: MagicMock,
        mock_st_input: MagicMock,
        mock_get_job_name: MagicMock,
        mock_test_command_run: MagicMock,
        mock_st_info: MagicMock,
        mock_st_cols: MagicMock,
        mock_get_interval_info: MagicMock,
        mock_get_duration: MagicMock,
        mock_execution_start: MagicMock,
        mock_submit: MagicMock,
        mock_refresh: MagicMock,
    ):
        """
        GIVEN job execution parameters
        WHEN job 'submit' button is clicked
        THEN check that the job is submitted with correct parameters.
        """
        col1 = col2 = col3 = MagicMock()
        mock_st_button.return_value = True
        mock_get_job_name.return_value = self.job_name
        mock_st_input.side_effect = [
            mock_get_job_name.return_value,
            self.command,
        ]
        mock_st_cols.return_value = (col1, col2, col3)
        col3.selectbox.side_effect = ["Weekly", "Now"]
        mock_get_interval_info.return_value = (None, None, ["Tue"])
        mock_get_duration.return_value = timedelta(days=1)
        mock_execution_start.return_value = "2020-02-01 00:00:00"

        layout_homepage_define_new_task(self.test_df)

        mock_submit.assert_called_with(
            self.command,
            self.job_name,
            mock_execution_start.return_value,
            timedelta(days=1),
            ["Tue"],
            "Weekly",
            "Now",
            2,
        )
        mock_refresh.assert_called()
