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

# @patch("tasklit.src.utils.helpers.pd.DataFrame")
# def test_save_df_to_sql(self, mock_df: MagicMock):
#     """
#     GIVEN a mocked pd.Dataframe object
#     WHEN passed to the 'save_df_to_sql' function
#     THEN check that df.to_sql method is called with correct parameters.
#     """
#     save_df_to_sql(mock_df, "engine")
#     mock_df.to_sql.assert_called_with(
#         "processes", con="engine", if_exists="append", index=False
#     )
#
# @patch("tasklit.src.utils.helpers.pd.DataFrame")
# def test_save_df_to_sql_raises_error(self, mock_df: MagicMock):
#     """
#     GIVEN a mocked pd.Dataframe object
#     WHEN passed to the 'save_df_to_sql' function
#     THEN check that an error is raised if sql file creation fails.
#     """
#     mock_df.to_sql.side_effect = OperationalError(
#         "Failed to create the sql file.", {}, ""
#     )
#     with self.assertRaises(OperationalError):
#         save_df_to_sql(mock_df, "engine")
