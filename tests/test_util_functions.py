import unittest

from datetime import datetime
from unittest.mock import (
    create_autospec,
    mock_open,
    patch,
    MagicMock
)

import pandas as pd
import psutil

from pandas.testing import assert_frame_equal
from sqlalchemy.exc import OperationalError
from streamlit.script_runner import RerunException

from app.src.utils.helpers import (
    get_task_id,
    check_last_process_info_update,
    read_log,
    terminate_child_processes,
    terminate_process,
    match_weekday,
    refresh_app,
    launch_command_process,
    display_process_log_file,
    update_df_process_last_update_info,
    get_process_df,
    update_process_status_info,
    submit_job,
    start_process,
    save_df_to_sql
)
from app.settings.consts import WEEK_DAYS, FORMAT


class UtilFunctionsTestCase(unittest.TestCase):
    """
    Unittests for application utility functions.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super(UtilFunctionsTestCase, cls).setUpClass()
        cls.test_log_filename = "sample_logfile.txt"
        cls.log_readlines_output = ["Line of text"]
        cls.test_job_name = "infallible_strauss"
        cls.test_process_id = 12345
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
        cls.test_command = "ping 8.8.8.8 -c 5"

    def test_get_task_id(self):
        """
        GIVEN a dataframe with process information and related task IDs
        WHEN passed to the 'get_task_id' function
        THEN check that returned ID == the largest ID in column + 1.
        """
        self.assertEqual(get_task_id(self.test_df), max(self.task_ids) + 1)

    @patch('os.path.getmtime')
    def test_check_last_process_info_update(self,
                                            mock_getmtime: MagicMock):
        """
        GIVEN a job name that corresponds to a job log file
        WHEN passed to the 'check_last_process_info_update' function
        THEN check that correct edit timestamp is identified.
        """
        mock_getmtime.return_value = 1629554559
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.return_value = "2018-12-25 09:27:53"

            self.assertEqual(check_last_process_info_update(
                self.test_job_name
            ), mock_datetime.fromtimestamp.return_value)

            mock_getmtime.assert_called()
            mock_datetime.fromtimestamp.assert_called()

    @patch('os.path.getmtime')
    def test_check_last_process_info_update(self,
                                            mock_getmtime: MagicMock):
        """
        GIVEN a job name that corresponds to a missing job log file
        WHEN passed to the 'check_last_process_info_update' function
        THEN check that OS Error is raised and the function returns None.
        """
        mock_getmtime.side_effect = OSError("An error happened.")
        self.assertEqual(
            check_last_process_info_update(self.test_job_name),
            None
        )

    def test_read_log_file_exists(self):
        """
        GIVEN a path to an existing log file
        WHEN passed to the 'read_log' function
        THEN check that correct read output is returned.
        """
        with patch('builtins.open', mock_open(read_data="Line of text")) as mock_file:
            self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)
            mock_file.assert_called_with(self.test_log_filename, 'r', encoding='utf-8')

    def test_read_log_raises(self):
        """
        GIVEN a path to a missing lof file
        WHEN passed to the 'read_log' function
        THEN check that FileNotFoundError is raised.
        """
        with patch('builtins.open') as mock_open_raises:
            mock_open_raises.side_effect = FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                self.assertEqual(read_log(self.test_log_filename), self.log_readlines_output)

    @patch('psutil.wait_procs')
    def test_terminate_child_processes_processes_found(self,
                                                       mock_wait_procs: MagicMock):
        """
        GIVEN a parent process object that has spawned child processes
        WHEN passed to the 'terminate_child_processes' function
        THEN check that related process termination methods are called.
        """
        parent_process = MagicMock()
        parent_process.children.return_value = [
            MagicMock(
                name="Child Proc 1",
                terminate=lambda: True
            ),
            MagicMock(
                name="Child Proc 2",
                terminate=lambda: True
            )
        ]
        mock_wait_procs.return_value = ([], [
            MagicMock(return_value=lambda: True),
            MagicMock(return_value=lambda: True)
        ])

        # Check that process.terminate() is being called on child processes
        for child_process in parent_process.children.return_value:
            mock_terminate = create_autospec(child_process.teminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_called()
            mock_terminate.assert_called()

        # Check that process.terminate() is being called on any child processes
        # that might have been left alive.
        for alive_process in mock_wait_procs.return_value[1]:
            mock_terminate = create_autospec(alive_process.terminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_called()
            mock_terminate.assert_called()

    @patch('psutil.wait_procs')
    def test_terminate_child_processes_processes_not_found(self,
                                                           mock_wait_procs: MagicMock):
        """
        GIVEN a parent process object that has NOT spawned child processes
        WHEN passed to the 'terminate_child_processes' function
        THEN check that related process termination methods are NOT called.
        """
        parent_process = MagicMock()
        parent_process.children.return_value = []
        mock_wait_procs.return_value = ([], [])

        # Check that process.terminate() is not called
        for child_process in parent_process.children.return_value:
            mock_terminate = create_autospec(child_process.teminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_not_called()
            mock_terminate.assert_not_called()

        # Check that process.terminate() is not called
        for alive_process in mock_wait_procs.return_value[1]:
            mock_terminate = create_autospec(alive_process.terminate, return_value=True)

            terminate_child_processes(parent_process)

            mock_wait_procs.assert_not_called()
            mock_terminate.assert_not_called()

    @patch('app.src.utils.helpers.terminate_child_processes')
    def test_terminate_process_with_child_processes(self,
                                                    mock_terminate_child_procs: MagicMock):
        """
        GIVEN an ID of an existing process
        WHEN passed to the 'terminate_process' function
        THEN check that related process termination methods have been called.
        """
        with patch('app.src.utils.helpers.psutil.Process') as mock_psutil_process:
            mock_psutil_process.return_value = MagicMock()
            mock_terminate_child_procs.return_value = True
            mock_psutil_process.terminate.return_value = lambda: True
            mock_terminate = create_autospec(mock_psutil_process.terminate, return_value=True)

            mock_psutil_process.kill.return_value = lambda: True
            mock_kill = create_autospec(mock_psutil_process.kill, return_value=True)

            terminate_process(self.test_process_id)

            mock_terminate_child_procs.assert_called()
            mock_terminate.assert_called()
            mock_kill.assert_called()

    def test_terminate_process_raises_error(self):
        """
        GIVEN an ID of a test process that does not exist
        WHEN passed to the 'terminate_process' function
        THEN check that psutil.NoSuchProcess error is raised.
        """
        with patch('app.src.utils.helpers.psutil.Process') as mock_psutil_process:
            mock_psutil_process.side_effect = psutil.NoSuchProcess("Cannot find the process.")
            with self.assertRaises(psutil.NoSuchProcess):
                terminate_process(self.test_process_id)

    def test_match_weekday(self):
        """
        GIVEN a number corresponding to a day of the week and a list of select weekdays
        WHEN passed to the 'function_should_execute' function
        THEN check that correct decision is made to execute a function if the days are mapped.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            for day_number, day in WEEK_DAYS.items():
                mock_datetime.now.weekday.return_value = day_number
                self.assertEqual(match_weekday(
                    mock_datetime.now,
                    list(WEEK_DAYS.values())
                ), True)

    def test_match_weekday(self):
        """
        GIVEN only a number representing today's date
        WHEN passed to the 'function_should_execute' function
        THEN check that correct decision is made to execute a function.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            self.assertEqual(
                match_weekday(
                    mock_datetime.now,
                    []
                ), True)

    def test_match_weekday(self):
        """
        GIVEN a number corresponding to a day of the week and a list of select weekdays
        WHEN passed to the 'function_should_execute' function
        THEN check that correct decision is made to NOT execute a function if the days cannot be mapped.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            for day_number, day in WEEK_DAYS.items():
                mock_datetime.now.weekday.return_value = day_number
                self.assertEqual(
                    match_weekday(
                        mock_datetime.now,
                        ["Uknown Day"]
                    ), False)

    def test_match_weekday(self):
        """
        GIVEN a number corresponding to a day of the week and a list of select weekdays
        WHEN passed to the 'function_should_execute' function
        THEN check that an error is raised if the number is missing in the app settings day mapping.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            for day_number, day in WEEK_DAYS.items():
                mock_datetime.now.weekday.return_value = day_number

                with patch('app.settings.consts.WEEK_DAYS') as mocked_weekdays:
                    mocked_weekdays.__getitem__.side_effect = KeyError("Failed to map the day.")

                    with self.assertRaises(KeyError):
                        match_weekday(
                            mock_datetime.now,
                            list(WEEK_DAYS.values())
                        )

    @patch('time.sleep')
    @patch('app.src.utils.helpers.st.empty')
    @patch('app.src.utils.helpers.st.script_request_queue.RerunData')
    def test_refresh_app(self,
                         mock_rerun_data: MagicMock,
                         mock_st_empty: MagicMock,
                         mock_sleep: MagicMock):
        """
        GIVEN an optional amount of time to wait in seconds
        WHEN passed to the 'refresh_app' function
        THEN check that Streamlit methods for writing log output and refreshing the app are called.
        """
        mock_st_empty.write.return_value = True
        mock_rerun_data.return_value = True

        with self.assertRaises(RerunException):
            refresh_app(5)

            mock_st_empty.empty.write.assert_called()
            mock_rerun_data.assert_called()
            mock_sleep.assert_called()

    @patch('time.sleep')
    @patch('app.src.utils.helpers.st.empty')
    @patch('app.src.utils.helpers.st.script_request_queue.RerunData')
    def test_refresh_app(self,
                         mock_rerun_data: MagicMock,
                         mock_st_empty: MagicMock,
                         mock_sleep: MagicMock):
        """
        GIVEN no time to wait in seconds
        WHEN passed to the 'refresh_app' function
        THEN check that only Streamlit methods for refreshing the app are called.
        """
        with self.assertRaises(RerunException):
            refresh_app()

            mock_st_empty.assert_not_called()
            mock_sleep.assert_not_called()
            mock_rerun_data.assert_called()

    @patch('app.src.utils.helpers.Popen')
    def test_launch_command_process(self,
                                    mock_popen: MagicMock):
        """
        GIVEN a command to execute and a respective job name
        WHEN passed to the 'run_job' function
        THEN check that correct object type is returned.
        """
        mock_popen.return_value = MagicMock()
        with patch('builtins.open', mock_open(read_data=self.test_command)) as mock_file:
            self.assertEqual(
                launch_command_process(self.test_command, self.test_log_filename),
                mock_popen.return_value
            )
            mock_file.assert_called_with(self.test_log_filename, 'w')

    @patch('app.src.utils.helpers.Popen')
    def test_launch_command_process(self,
                                    mock_popen: MagicMock):
        """
        GIVEN a command to execute and a respective job name
        WHEN passed to the 'run_job' function
        THEN check that an error is raised if log file creation fails.
        """
        mock_popen.side_effect = OSError("File creation failed.")
        with patch('builtins.open', mock_open(read_data=self.test_command)):
            with self.assertRaises(OSError):
                launch_command_process(self.test_command, self.test_log_filename)

    @patch('app.src.utils.helpers.st.write')
    @patch('app.src.utils.helpers.st.code')
    @patch('app.src.utils.helpers.read_log')
    def test_display_process_log_file_exists(self,
                                             mock_read_log: MagicMock,
                                             mock_st_code: MagicMock,
                                             mock_st_write: MagicMock):
        """
        GIVEN a name of an existing log file
        WHEN passed to the 'display_process_log_file' function
        THEN check that the file is read and file contents are displayed.
        """
        mock_st_code.return_value = True
        mock_st_write.return_value = True
        mock_read_log.return_value = self.log_readlines_output

        display_process_log_file(self.test_log_filename)

        mock_read_log.assert_called()
        mock_st_code.assert_called_with("Line of text")
        mock_st_write.assert_not_called()

    @patch('app.src.utils.helpers.st.write')
    @patch('app.src.utils.helpers.st.code')
    @patch('app.src.utils.helpers.read_log')
    def test_display_process_log_file_missing(self,
                                              mock_read_log: MagicMock,
                                              mock_st_code: MagicMock,
                                              mock_st_write: MagicMock):
        """
        GIVEN a name of a log file that doesn't exist
        WHEN passed to the 'display_process_log_file' function
        THEN check that FileNotFoundError is triggered and an error message is logged.
        """
        mock_st_code.return_value = True
        mock_st_write.return_value = True
        mock_read_log.side_effect = FileNotFoundError("Log file is missing.")

        display_process_log_file(self.test_log_filename)

        mock_read_log.assert_called()
        mock_st_code.assert_not_called()
        mock_st_write.assert_called_with("sample_logfile.txt does not exist.")

    @patch('app.src.utils.helpers.check_last_process_info_update')
    def test_update_df_process_last_update_info(self,
                                                mock_check_update: MagicMock):
        """
        GIVEN a pandas dataframe with a 'last update' column
        WHEN passed to the 'update_df_process_last_update_info' function
        THEN check that 'last update' column is correctly populated.
        """
        last_update_date = "2021-01-01"
        mock_check_update.return_value = last_update_date

        update_df_process_last_update_info(self.test_df)

        self.assertEqual(self.test_df.at[0, "last update"], last_update_date)

    @patch('app.src.utils.helpers.pd.read_sql_table')
    def test_get_process_df_no_error_raised(self,
                                            mock_pd_read_sql_table: MagicMock):
        """
        GIVEN an sql engine for reading an SQL file with a pandas DF
        WHEN passed to the 'get_process_df' function
        THEN check that correct version of the dataframe is returned.
        """
        # Case 1: SQL file present -> DF is read.
        mock_pd_read_sql_table.return_value = self.test_df

        assert_frame_equal(get_process_df("sql_engine"), self.test_df)

        # Case 2: SQL file is missing -> empty formatted DF is returned.
        mock_pd_read_sql_table.side_effect = ValueError("Dataframe file is missing.")
        assert_frame_equal(get_process_df("sql_engine"), pd.DataFrame(FORMAT))

    @patch('app.src.utils.helpers.pd.read_sql_table')
    def test_get_process_df_error_is_raised(self,
                                            mock_pd_read_sql_table: MagicMock):
        """
        GIVEN an sql engine for reading an SQL file with a pandas DF
        WHEN passed to the 'get_process_df' function
        THEN check that OperationalError is raised if the file is missing.
        """
        mock_pd_read_sql_table.side_effect = OperationalError("Couldn't process DF.", {}, "")
        with self.assertRaises(OperationalError):
            get_process_df("sql_engine")

    @patch.object(psutil.Process, "status")
    @patch('app.src.utils.helpers.psutil.pid_exists')
    def test_update_process_status_info(self,
                                        mock_pid_exists: MagicMock,
                                        mock_process_status: MagicMock):
        """
        GIVEN a dataframe with information for an existing running process
        WHEN passed to the 'update_process_status_info' function
        THEN check that process status is correctly identified as 'running'.
        """
        mock_pid_exists.return_value = True
        mock_process_status.return_value = "running"

        update_process_status_info(self.test_df)

        self.assertEqual(self.test_df.at[0, "running"], True)

    @patch.object(psutil.Process, "status")
    @patch('app.src.utils.helpers.psutil.pid_exists')
    def test_update_process_status_info(self,
                                        mock_pid_exists: MagicMock,
                                        mock_process_status: MagicMock):
        """
        GIVEN a dataframe with information for an existing zombie process
        WHEN passed to the 'update_process_status_info' function
        THEN check that process status is correctly identified as not 'running'.
        """
        mock_pid_exists.return_value = True
        mock_process_status.return_value = "zombie"

        update_process_status_info(self.test_df)

        self.assertEqual(self.test_df.at[0, "running"], False)

    @patch.object(psutil.Process, "status")
    @patch('app.src.utils.helpers.psutil.pid_exists')
    def test_update_process_status_info(self,
                                        mock_pid_exists: MagicMock,
                                        mock_process_status: MagicMock):
        """
        GIVEN a dataframe with information for a process that does not exist
        WHEN passed to the 'update_process_status_info' function
        THEN check that process status is correctly identified as not 'running'.
        """
        mock_pid_exists.return_value = False

        update_process_status_info(self.test_df)

        self.assertEqual(self.test_df.at[0, "running"], False)

    @patch('app.src.utils.helpers.save_df_to_sql')
    @patch('app.src.utils.helpers.create_process_info_dataframe')
    @patch('app.src.utils.helpers.start_process')
    def test_submit_job(self,
                        mock_start_process: MagicMock,
                        mock_create_df: MagicMock,
                        mock_save_df: MagicMock):
        """
        GIVEN job execution parameters
        WHEN passed to the 'submit_job' function
        THEN check that job execution functions are called.
        """
        mock_start_process.return_value = True
        mock_create_df.return_value = True
        mock_save_df.return_value = True

        submit_job(
            "test",
            "test",
            datetime(2020, 1, 1),
            None,
            None,
            None,
            "test",
            "test",
            1,
            "test"
        )

        mock_start_process.assert_called_with(
            'test',
            'test',
            datetime(2020, 1, 1, 0, 0),
            None,
            None,
            None,
            'test',
            'test'
        )
        mock_create_df.assert_called_with(
            'test',
            'test',
            True,
            1
        )
        mock_save_df.assert_called_with(
            True,
            'test'
        )

    @patch('app.src.utils.helpers.Process')
    def test_start_process(self,
                           mock_process: MagicMock):
        """
        GIVEN job execution parameters
        WHEN passed to the 'start_process' function
        THEN check that a process is started and related process ID is returned.
        """
        process_mock = MagicMock()
        process_mock.start = lambda: True
        process_mock.pid = 123
        mock_process.return_value = process_mock

        self.assertEqual(start_process(
            "test",
            "test",
            datetime(2020, 1, 1),
            None,
            None,
            None,
            "test",
            "test"
        ), process_mock.pid)
