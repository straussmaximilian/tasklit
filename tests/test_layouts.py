import unittest
from unittest.mock import MagicMock, patch

from tasklit.pages.layouts.footer import footer
from tasklit.pages.layouts.header import header


class PageLayoutsTestCase(unittest.TestCase):
    """Unittests for application UI layout elements."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters.

        title (str): header title.
        subtitle (str): header subtitle.
        """
        super(PageLayoutsTestCase, cls).setUpClass()
        cls.title = "# 🕙 Sample Title"
        cls.subtitle = "Sample subtitle"

    @patch("tasklit.pages.homepage.st.text")
    @patch("tasklit.pages.homepage.st.write")
    def test_header(
        self,
        mock_st_write: MagicMock,
        mock_st_text: MagicMock,
    ):
        """Test header().

        GIVEN title and subtitle
        WHEN 'header' function is called
        THEN check that correct application header is rendered.
        """
        header(self.title, self.subtitle)

        mock_st_write.assert_called_with(self.title)
        mock_st_text.assert_called_with(self.subtitle)

    @patch("tasklit.pages.layouts.footer.refresh_app")
    @patch("tasklit.pages.homepage.st.button")
    def test_footer_btn_clicked(
        self, mock_st_btn: MagicMock, mock_refresh: MagicMock
    ):
        """Test footer().

        GIVEN a footer UI element
        WHEN 'refresh' button is clicked
        THEN check that app refresh function is called.
        """
        mock_st_btn.return_value = True

        footer()

        mock_refresh.assert_called()

    @patch("tasklit.pages.layouts.footer.refresh_app")
    @patch("tasklit.pages.homepage.st.button")
    def test_footer_btn_not_clicked(
        self, mock_st_btn: MagicMock, mock_refresh: MagicMock
    ):
        """Test footer().

        GIVEN a footer UI element
        WHEN 'refresh' button is not clicked
        THEN check that app refresh function is not called.
        """
        mock_st_btn.return_value = False

        footer()

        mock_refresh.assert_not_called()
