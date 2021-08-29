import unittest

from unittest.mock import (
    create_autospec,
    mock_open,
    patch,
    MagicMock
)

from app.pages.homepage import homepage


class HomepageTestCase(unittest.TestCase):
    """
    Unittests for application homepage.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super(HomepageTestCase, cls).setUpClass()

    @patch('app.pages.homepage.layout_homepage_explore_task')
    @patch('app.pages.homepage.layout_homepage_define_new_task')
    @patch('app.pages.homepage.st.table')
    @patch('app.pages.homepage.st.text')
    @patch('app.pages.homepage.st.write')
    def test_static_layout_elements_generated(self,
                                              mock_st_write: MagicMock,
                                              mock_st_text: MagicMock,
                                              mock_st_table: MagicMock,
                                              mock_define_task: MagicMock,
                                              mock_explore_task: MagicMock):
        pass

    @patch('app.src.utils.helpers.refresh_app')
    @patch('app.pages.homepage.st.button')
    def test_refresh_called_on_button_click(self,
                                            mock_st_button: MagicMock,
                                            mock_refresh: MagicMock):
        pass

    def test_button_remove_inactive_procs_present(self):
        pass
