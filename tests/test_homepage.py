import unittest

from unittest.mock import (
    patch,
    MagicMock
)

import pandas as pd

from tasklit.pages.homepage import homepage


class HomepageTestCase(unittest.TestCase):
    """
    Unittests for application homepage.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        last_update: str
            Process logfile last update timestamp.
        running: bool
            Indicate process status.
        test_df: pd.DataFrame
            Sample dataframe to mimic df with process information.
        """
        super(HomepageTestCase, cls).setUpClass()
        cls.last_update = "2020-01-01 12:00:00"
        cls.running = True
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

    @patch('tasklit.pages.homepage.socket.gethostname')
    @patch('tasklit.pages.homepage.st.text')
    @patch('tasklit.pages.homepage.st.write')
    def test_app_header(self,
                        mock_st_write: MagicMock,
                        mock_st_text: MagicMock,
                        mock_get_hostname: MagicMock):
        """
        WHEN 'homepage' function is called
        THEN check that correct application header is rendered.
        """
        mock_get_hostname.return_value = "Tasklit.pc"

        homepage("")

        mock_st_write.assert_called_with('# 🕙 Tasklit')
        mock_st_text.assert_called_with('A browser-based task scheduling system. Running on Tasklit.pc.')

    @patch('tasklit.pages.homepage.st.table')
    @patch('tasklit.pages.homepage.helper_functions.update_df_process_last_update_info')
    @patch('tasklit.pages.homepage.helper_functions.update_process_status_info')
    @patch('tasklit.pages.homepage.helper_functions.get_process_df')
    def test_display_process_df(self,
                                mock_get_df: MagicMock,
                                mock_update_status: MagicMock,
                                mock_update_last_edit: MagicMock,
                                mock_st_table: MagicMock):
        """
        GIVEN a dataframe with process information
        WHEN 'homepage' function is called
        THEN check that correct version of the dataframe is rendered.
        """
        test_df_copy = self.test_df.copy()
        mock_get_df.return_value = test_df_copy
        test_df_copy["last update"] = self.last_update
        mock_update_last_edit.return_value = test_df_copy
        test_df_copy["running"] = self.running
        mock_update_status.return_value = test_df_copy

        homepage("")

        mock_st_table.assert_called_with(test_df_copy)

    @patch('tasklit.pages.homepage.layout_homepage_explore_task')
    @patch('tasklit.pages.homepage.layout_homepage_define_new_task')
    @patch('tasklit.pages.homepage.helper_functions.refresh_app')
    @patch.object(pd.DataFrame, 'to_sql')
    @patch('tasklit.pages.homepage.st.button')
    @patch('tasklit.pages.homepage.st.table')
    @patch('tasklit.pages.homepage.helper_functions.update_df_process_last_update_info')
    @patch('tasklit.pages.homepage.helper_functions.update_process_status_info')
    @patch('tasklit.pages.homepage.helper_functions.get_process_df')
    def test_remove_inactive_processes(self,
                                       mock_get_df: MagicMock,
                                       mock_update_status: MagicMock,
                                       mock_update_last_edit: MagicMock,
                                       mock_st_table: MagicMock,
                                       mock_st_button: MagicMock,
                                       mock_df_to_sql: MagicMock,
                                       mock_refresh: MagicMock,
                                       mock_new_task: MagicMock,
                                       mock_explore_task: MagicMock):
        """
        GIVEN a dataframe with information of an inactive process
        WHEN 'homepage' function is called
        THEN check that DataFrame information is saved to sql.
        """
        mock_get_df.return_value = mock_update_status.return_value = \
            mock_update_last_edit.return_value = mock_st_table.return_value = self.test_df
        mock_st_button.return_value = True

        homepage("")

        mock_df_to_sql.assert_called_with('processes', con='', if_exists='replace', index=False)
        mock_refresh.assert_called()

    @patch('tasklit.pages.homepage.layout_homepage_explore_task')
    @patch('tasklit.pages.homepage.layout_homepage_define_new_task')
    @patch('tasklit.pages.homepage.helper_functions.get_process_df')
    def test_static_layouts(self,
                            mock_get_df: MagicMock,
                            mock_new_task: MagicMock,
                            mock_explore_task: MagicMock):
        """
        GIVEN a dataframe with process information
        WHEN 'homepage' function is called
        THEN check that related static layout functions are called.
        """
        mock_get_df.return_value = self.test_df

        homepage("sql_engine")

        mock_new_task.assert_called_with(self.test_df, "sql_engine")
        mock_explore_task.assert_called_with(self.test_df)



