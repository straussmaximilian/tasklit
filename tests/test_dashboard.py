"""Unittest dashboard layout."""

import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd

from tasklit.pages.dashboard import usage_dashboard
from tasklit.src.classes import app_db_handler


class DashboardTestCase(unittest.TestCase):
    """Unittests for application homepage."""

    @classmethod
    def setUpClass(cls) -> None:
        """Setup test parameters.

        test_df: pd.DataFrame
            test pandas dataframe to display stats for.
        """
        super(DashboardTestCase, cls).setUpClass()
        cls.test_df = pd.DataFrame(
            {
                "job_name": ["melancholic_strauss"],
                "command": ["ping 123"],
                "average_duration": [2],
                "executions": [1],
            }
        )

    @patch.object(app_db_handler, "load_dataframe")
    @patch("tasklit.pages.dashboard.footer")
    @patch("tasklit.pages.dashboard.header")
    def test_page_header_footer(
        self,
        mock_header: MagicMock,
        mock_footer: MagicMock,
        mock_load: MagicMock
    ):
        """Check header and footer rendered.

        WHEN 'usage_function' function is called
        THEN check that correct application header and footer are rendered.
        """
        mock_header.return_value = True
        mock_footer.return_value = True
        mock_load.return_value = self.test_df

        usage_dashboard()

        mock_header.assert_called_with(
            "# 📈 Task Statistics",
            "Dive deeper into the history of your tasks.",
        )
        mock_footer.assert_called()

    @patch("tasklit.pages.dashboard.st.markdown")
    @patch.object(app_db_handler, "load_dataframe")
    def test_displayed_values(
        self,
        mock_load: MagicMock,
        mock_markdown: MagicMock,
    ):
        """Test that correct DF values are calculated and displayed.

        GIVEN a dataframe with process stats
        WHEN 'usage_dashboard' function is called
        THEN check that correct stat values are displayed.
        """
        mock_load.return_value = self.test_df
        mock_markdown.return_value = True

        usage_dashboard()

        mock_markdown.assert_has_calls(
            [
                call(
                    "<h3 style='text-align: center;'>Tasks Run</h3>",
                    unsafe_allow_html=True,
                ),
                call(
                    "<h4 style='text-align: center; "
                    "font-size: 20px; color: #f63366;'>1</h1>",
                    unsafe_allow_html=True,
                ),
                call(
                    "<h3 style='text-align: center;'>"
                    "Total Duration (min.)</h3>",
                    unsafe_allow_html=True,
                ),
                call(
                    "<h4 style='text-align: center; "
                    "font-size: 20px; color: #f63366;'>0.03</h1>",
                    unsafe_allow_html=True,
                ),
                call(
                    "<h3 style='text-align: center;'>Top Command</h3>",
                    unsafe_allow_html=True,
                ),
                call(
                    "<h4 style='text-align: center; "
                    "font-size: 20px; color: #f63366;'>ping 123</h1>",
                    unsafe_allow_html=True,
                ),
                call("## Task History"),
            ]
        )
