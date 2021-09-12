import unittest

from unittest.mock import (
    call,
    patch,
    MagicMock
)

import pandas as pd

from app.pages.layouts.homepage_explore_task import layout_homepage_explore_task


class HomepageExploreTaskTestCase(unittest.TestCase):
    """
    Unittests for application homepage 'explore task' layout.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        test_df: pd.DataFrame
            Sample dataframe to mimic df with process information.
        """
        super(HomepageExploreTaskTestCase, cls).setUpClass()
        cls.task_id = 1
        cls.process_id = 123
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

    @patch('app.pages.layouts.homepage_explore_task.helper_functions.refresh_app')
    @patch('app.pages.layouts.homepage_explore_task.helper_functions.st.success')
    @patch('app.pages.layouts.homepage_explore_task.helper_functions.terminate_process')
    @patch('app.pages.layouts.homepage_explore_task.st.button')
    @patch('app.pages.layouts.homepage_explore_task.st.checkbox')
    @patch('app.pages.layouts.homepage_explore_task.helper_functions.display_process_log_file')
    @patch('app.pages.layouts.homepage_explore_task.st.code')
    @patch('app.pages.layouts.homepage_explore_task.st.write')
    @patch('app.pages.layouts.homepage_explore_task.st.selectbox')
    @patch('app.pages.layouts.homepage_explore_task.st.expander')
    def test_app_terminate_process_job(self,
                                       mock_st_expander: MagicMock,
                                       mock_st_selectbox: MagicMock,
                                       mock_st_write: MagicMock,
                                       mock_st_code: MagicMock,
                                       mock_display_log: MagicMock,
                                       mock_st_checkbox: MagicMock,
                                       mock_st_button: MagicMock,
                                       mock_terminate: MagicMock,
                                       mock_st_success: MagicMock,
                                       mock_refresh: MagicMock):
        """
        GIVEN process ID and task ID
        WHEN task ID is selected in the 'explore task' tab
        THEN check related task info methods are called.
        """
        mock_st_expander.return_value.__enter__.return_value = True
        mock_st_selectbox.return_value = self.task_id
        mock_st_checkbox.return_value = True
        mock_st_button.return_value = True
        mock_display_log.side_effect = ["Execution Log", "Stdout log"]

        layout_homepage_explore_task(self.test_df)

        mock_st_write.assert_has_calls([
            call('## Task Execution Log'),
            call('## Task Stdout Log')
        ])

        mock_st_code.assert_has_calls([
            call('Execution Log'),
            call('Stdout log')
        ])

        mock_terminate.assert_called_with(self.process_id)
        mock_st_success.assert_called_with(
            f'Terminated task nostalgic_strauss with task_id {self.task_id} '
            f'and process id {self.process_id}.'
        )
        mock_refresh.assert_called()





