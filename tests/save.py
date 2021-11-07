# @patch("tasklit.src.utils.helpers.pd.read_sql_table")
# def test_get_process_df_no_error_raised(
#     self, mock_pd_read_sql_table: MagicMock
# ):
#     """
#     GIVEN an sql engine for reading an SQL file
#     WHEN passed to the 'get_process_df' function
#     THEN check that a pandas dataframe with all the rows is returned.
#     """
#     mock_pd_read_sql_table.return_value = self.test_df
#
#     assert_frame_equal(get_process_df("sql_engine"), self.test_df)
#
# @patch("tasklit.src.utils.helpers.pd.read_sql_table")
# def test_get_process_df_returns_empty_df(
#     self, mock_pd_read_sql_table: MagicMock
# ):
#     """
#     GIVEN an sql engine for reading an SQL file
#     WHEN passed to the 'get_process_df' function
#     THEN check that - if the file is missing - an empty dataframe is returned.
#     """
#     mock_pd_read_sql_table.side_effect = ValueError(
#         "Dataframe file is missing."
#     )
#     assert_frame_equal(get_process_df("sql_engine"), pd.DataFrame(FORMAT))


# @patch("tasklit.src.utils.helpers.pd.read_sql_table")
# def test_get_process_df_raises_error(self, mock_pd_read_sql_table: MagicMock):
#     """
#     GIVEN an sql engine for reading an SQL file with a pandas DF
#     WHEN passed to the 'get_process_df' function
#     THEN check that OperationalError is raised if the file is missing.
#     """
#     mock_pd_read_sql_table.side_effect = OperationalError(
#         "Couldn't process DF.", {}, ""
#     )
#     with self.assertRaises(OperationalError):
#         get_process_df("sql_engine")
