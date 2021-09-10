import unittest

from datetime import datetime, timedelta
from unittest.mock import (
    create_autospec,
    mock_open,
    patch,
    MagicMock,
    call
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
    save_df_to_sql,
    create_process_info_dataframe,
    write_job_execution_log,
    process_should_execute,
    app_exception_handler,
    create_folder_if_not_exists,
    test_command_run,
    get_time_interval_info,
    select_weekdays,
    get_execution_interval_information,
    calculate_execution_start,
    get_command_execution_start,
    match_duration
)
from app.settings.consts import WEEK_DAYS, FORMAT, DEFAULT_LOG_DIR_OUT


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

    @staticmethod
    @app_exception_handler
    def decorated_test_func(should_raise=False):
        if should_raise:
            raise ValueError("Exception was raised.")
        return None

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
    def test_check_last_process_info_update_raises_error(self,
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

    def test_read_log_raises_error(self):
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

    def test_match_weekday_day_matched(self):
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

    def test_match_weekday_no_weekdays_provided(self):
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

    def test_match_weekday_no_execution(self):
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

    def test_match_weekday_raises_error(self):
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
    def test_refresh_app_raises_error(self,
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
    def test_launch_command_process_raises_error(self,
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
        GIVEN an sql engine for reading an SQL file
        WHEN passed to the 'get_process_df' function
        THEN check that a pandas dataframe with all the rows is returned.
        """
        mock_pd_read_sql_table.return_value = self.test_df

        assert_frame_equal(get_process_df("sql_engine"), self.test_df)

    @patch('app.src.utils.helpers.pd.read_sql_table')
    def test_get_process_df_returns_empty_df(self,
                                             mock_pd_read_sql_table: MagicMock):
        """
        GIVEN an sql engine for reading an SQL file
        WHEN passed to the 'get_process_df' function
        THEN check that - if the file is missing - an empty dataframe is returned.
        """
        mock_pd_read_sql_table.side_effect = ValueError("Dataframe file is missing.")
        assert_frame_equal(get_process_df("sql_engine"), pd.DataFrame(FORMAT))

    @patch('app.src.utils.helpers.pd.read_sql_table')
    def test_get_process_df_raises_error(self,
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
    def test_update_process_status_info_running_process(self,
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
    def test_update_process_status_info_zombie_process(self,
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

    @patch('app.src.utils.helpers.psutil.pid_exists')
    def test_update_process_status_info_missing_process(self,
                                                        mock_pid_exists: MagicMock):
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

    @patch('app.src.utils.helpers.pd.DataFrame')
    def test_save_df_to_sql(self,
                            mock_df: MagicMock):
        """
        GIVEN a mocked pd.Dataframe object
        WHEN passed to the 'save_df_to_sql' function
        THEN check that df.to_sql method is called with correct parameters.
        """
        save_df_to_sql(mock_df, "engine")
        mock_df.to_sql.assert_called_with('processes', con='engine', if_exists='append', index=False)

    @patch('app.src.utils.helpers.pd.DataFrame')
    def test_save_df_to_sql_raises_error(self,
                                         mock_df: MagicMock):
        """
        GIVEN a mocked pd.Dataframe object
        WHEN passed to the 'save_df_to_sql' function
        THEN check that an error is raised if sql file creation fails.
        """
        mock_df.to_sql.side_effect = OperationalError("Failed to create the sql file.", {}, "")
        with self.assertRaises(OperationalError):
            save_df_to_sql(mock_df, "engine")

    def test_create_process_info_dataframe(self):
        """
        GIVEN parameters related to a specific job (e.g. name, command, etc.)
        WHEN passed to the 'create_process_info_dataframe' function
        THEN check that a dataframe with these parameters is returned.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.return_value = None
            test_df_copy = self.test_df.copy()
            test_df_copy["created"] = mock_datetime.now.return_value
            assert_frame_equal(
                create_process_info_dataframe(
                    None,
                    self.test_job_name,
                    None,
                    self.task_ids[0]
                ),
                self.test_df
            )

    def test_write_job_execution_log(self):
        """
        GIVEN job info that should be logged (e.g. job name, command, etc.)
        WHEN passed to the 'write_job_execution_log' function
        THEN check that correct log file information is logged.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.strftime.return_value = '2021-01-01 00:00:00'

            with patch('builtins.open', mock_open()) as mock_file:
                write_job_execution_log(
                    self.test_job_name,
                    self.test_command,
                    mock_datetime.now,
                    "Executed"
                )

                mock_file.return_value.write.assert_has_calls([
                    # 1 call for '*.txt' log write
                    call('2021-01-01 00:00:00 Executed ping 8.8.8.8 -c 5\n'),
                    # 2 calls for '*_stdout.txt' log write
                    call(f"\n{'=' * 70} \n"),
                    call('2021-01-01 00:00:00 Executed ping 8.8.8.8 -c 5\n')
                ])

                mock_file.assert_called_with('./app/logs/infallible_strauss_stdout.txt', 'a')

    def test_write_job_execution_log_raises_error(self):
        """
        GIVEN job info that should be logged (e.g. job name, command, etc.)
        WHEN passed to the 'write_job_execution_log' function
        THEN check that an error is raised if the log file cannot be accessed.
        """
        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.strftime.return_value = '2021-01-01 00:00:00'

            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.side_effect = OSError

                with self.assertRaises(OSError):
                    write_job_execution_log(
                        self.test_job_name,
                        self.test_command,
                        mock_datetime.now,
                        "Executed"
                    )

    @patch('app.src.utils.helpers.match_duration')
    @patch('app.src.utils.helpers.match_weekday')
    def test_process_should_execute(self,
                                    mock_match_weekday: MagicMock,
                                    mock_match_duration: MagicMock):
        """
        GIVEN current daytime information
        WHEN passed to the 'test_process_should_execute' function
        THEN check that a decision is made to execute the process
        if both checks pass.
        """
        mock_match_weekday.return_value = True
        mock_match_duration.return_value = True

        self.assertEqual(process_should_execute(
            datetime.now(),
            datetime.now(),
            timedelta(1),
            []
        ),
            True
        )

    @patch('app.src.utils.helpers.match_duration')
    @patch('app.src.utils.helpers.match_weekday')
    def test_process_should_not_execute(self,
                                        mock_match_weekday: MagicMock,
                                        mock_match_duration: MagicMock):
        """
        GIVEN current daytime information
        WHEN passed to the 'test_process_should_execute' function
        THEN check that a decision is made to NOT execute the process if
        at least one of the checks fails.
        """
        mock_match_weekday.return_value = True
        mock_match_duration.return_value = False

        self.assertEqual(process_should_execute(
            datetime.now(),
            datetime.now(),
            timedelta(1),
            []
        ),
            False
        )

    @patch('app.src.utils.helpers.st.error')
    @patch('app.src.utils.helpers.refresh_app')
    def test_app_exception_handler_not_raises_error(self,
                                                    mock_refresh_app: MagicMock,
                                                    mock_st_error: MagicMock):
        """
        GIVEN a function defined with the exception handler decorator
        WHEN this function is called without triggering an exception
        THEN check that decorator exception handling methods are not called.
        """
        mock_refresh_app.return_value = True
        mock_st_error.return_value = True

        self.decorated_test_func()

        mock_refresh_app.assert_not_called()
        mock_st_error.assert_not_called()

    @patch('app.src.utils.helpers.st.error')
    @patch('app.src.utils.helpers.refresh_app')
    def test_app_exception_handler_raises_error(self,
                                                mock_refresh_app: MagicMock,
                                                mock_st_error: MagicMock):
        """
        GIVEN a function defined with the exception handler decorator
        WHEN this function is called with triggering an exception
        THEN check that decorator exception handling methods are called.
        """
        mock_refresh_app.return_value = True
        mock_st_error.return_value = True

        self.decorated_test_func(True)

        mock_refresh_app.assert_called_with(5)
        mock_st_error.assert_called_with('An error was caught: Exception was raised.')

    @patch('pathlib.Path.mkdir')
    @patch('os.path.exists')
    def test_create_folder_if_not_exists(self,
                                                        mock_path_exists: MagicMock,
                                                        mock_create: MagicMock):
        """
        GIVEN a filepath to a missing folder
        WHEN passed to the 'create_folder_if_not_exists' function
        THEN check that related folder creation methods are called.
        """
        mock_path_exists.return_value = False

        create_folder_if_not_exists("test_folder")

        mock_path_exists.assert_called()
        mock_create.assert_called()

    @patch('pathlib.Path.mkdir')
    @patch('os.path.exists')
    def test_create_folder_if_not_exists_folder_exists(self,
                                                       mock_path_exists: MagicMock,
                                                       mock_create: MagicMock):
        """
        GIVEN a filepath to an existing folder
        WHEN passed to the 'create_folder_if_not_exists' function
        THEN check that related folder creation methods are NOT called.
        """
        mock_path_exists.return_value = True

        create_folder_if_not_exists("test_folder")

        mock_path_exists.assert_called()
        mock_create.assert_not_called()

    @patch('app.src.utils.helpers.st.checkbox')
    @patch('app.src.utils.helpers.st.empty')
    @patch('app.src.utils.helpers.read_log')
    @patch('app.src.utils.helpers.terminate_process')
    @patch('app.src.utils.helpers.launch_command_process')
    def test_test_command_run(self,
                              mock_launch_process: MagicMock,
                              mock_terminate_process: MagicMock,
                              mock_read_log: MagicMock,
                              mock_st_empty: MagicMock,
                              mock_st_checkbox: MagicMock):
        """
        GIVEN a command to test
        WHEN passed to the 'test_command_run' function
        THEN check that related test commands are called and
        the test process is terminated when the 'stop' button is pressed.
        """
        mock_st_checkbox.return_value = True
        mock_launch_process.poll.return_value = None
        mock_launch_process.return_value.pid = 123
        mock_read_log.return_value = ["Log file", " Contents"]
        mock_st_empty.return_value.code.return_value = lambda x: x

        test_command_run(self.test_command)

        mock_st_empty.assert_called()
        mock_st_checkbox.assert_called()
        mock_read_log.assert_called_with(DEFAULT_LOG_DIR_OUT)
        mock_st_empty.return_value.code.assert_called_with(
            "".join(mock_read_log.return_value)
        )
        mock_terminate_process.assert_called_with(
            mock_launch_process.return_value.pid
        )

    def test_get_time_interval_info(self):
        """
        GIVEN mocked Streamlit column widgets
        WHEN passed to the 'get_time_interval_info' function
        THEN check that correct time values are returned.
        """
        unit_col = MagicMock()
        quantity_col = MagicMock()
        unit_col.selectbox.return_value = "Minutes"
        quantity_col.slider.return_value = 5

        selected_time, selected_quantity = get_time_interval_info(unit_col, quantity_col)

        self.assertEqual(selected_time, unit_col.selectbox.return_value)
        self.assertEqual(selected_quantity, quantity_col.slider.return_value)

    def test_select_weekdays(self):
        """
        GIVEN mocked Streamlit column widget
        WHEN passed to the 'select_weekdays' function
        THEN check that correct day of the week selection is returned.
        """
        unit_col = MagicMock()
        unit_col.multiselect.return_value = "Tue"

        self.assertEqual(select_weekdays(unit_col), unit_col.multiselect.return_value)

    @patch('app.src.utils.helpers.select_weekdays')
    @patch('app.src.utils.helpers.get_time_interval_info')
    def test_get_execution_interval_information_interval(self,
                                                         mock_time_info: MagicMock,
                                                         mock_select: MagicMock):
        """
        GIVEN job execution 'Interval' frequency
        WHEN passed to the 'get_execution_interval_information' function
        THEN check that returned time interval information matches expected values.
        """
        frequency = "Interval"
        unit_col = MagicMock()
        quantity_col = MagicMock()
        mock_time_info.return_value = ("Weekly", 5)

        unit, quantity, weekdays = get_execution_interval_information(
            frequency,
            unit_col,
            quantity_col
        )

        mock_time_info.assert_called_with(unit_col, quantity_col)
        mock_select.assert_not_called()

        self.assertEqual(
            unit,
            mock_time_info.return_value[0]
        )

        self.assertEqual(
            quantity,
            mock_time_info.return_value[1]
        )

        self.assertEqual(
            weekdays,
            None
        )

    @patch('app.src.utils.helpers.select_weekdays')
    @patch('app.src.utils.helpers.get_time_interval_info')
    def test_get_execution_interval_information_daily(self,
                                                      mock_time_info: MagicMock,
                                                      mock_select: MagicMock):
        """
        GIVEN job execution 'Daily' frequency
        WHEN passed to the 'get_execution_interval_information' function
        THEN check that returned time interval information matches expected values.
        """
        frequency = "Daily"
        unit_col = MagicMock()
        quantity_col = MagicMock()
        mock_select.return_value = ["Tue"]

        unit, quantity, weekdays = get_execution_interval_information(
            frequency,
            unit_col,
            quantity_col
        )
        mock_time_info.assert_not_called()
        mock_select.assert_called_with(unit_col)

        self.assertEqual(
            unit,
            None
        )

        self.assertEqual(
            quantity,
            None
        )

        self.assertEqual(
            weekdays,
            mock_select.return_value
        )

    def test_calculate_execution_start(self):
        """
        GIVEN Streamlit widgets for selecting execution date and time
        WHEN passed to the 'calculate_execution_start' function
        THEN check that returned execution start datetime matches expected value.
        """
        date_col = MagicMock()
        date_col.date_input.return_value = datetime(2020, 1, 1, 00, 00)
        time_slider_col = MagicMock()
        time_slider_col.slider.return_value = datetime(2020, 1, 1, 23, 59)

        self.assertEqual(
            calculate_execution_start(date_col, time_slider_col),
            datetime(2020, 1, 1, 23, 59)
        )

    @patch('app.src.utils.helpers.st.text')
    @patch('app.src.utils.helpers.calculate_execution_start')
    def test_get_command_execution_start_scheduled(self,
                                                   mock_calculate_start: MagicMock,
                                                   mock_st_text: MagicMock):
        """
        GIVEN an execution type with no execution frequency
        WHEN passed to the 'get_command_execution_start' function
        THEN check that correct execution start value is returned.
        """
        execution_type = "Scheduled"
        execution_frequency = ""
        date_col = MagicMock()
        slider_col = MagicMock()
        result = '2020-01-01 23:59:00'
        mock_calculate_start.return_value = datetime(2021, 1, 1, 00, 00)

        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.return_value = result
            mock_datetime.strftime.return_value = '2020-01-01 00:00:00'

            start_date = get_command_execution_start(
                execution_type,
                execution_frequency,
                [],
                date_col,
                slider_col
            )

            mock_calculate_start.assert_called_with(date_col, slider_col)
            mock_st_text.assert_called_with('First execution on 2021-01-01 00:00:00.')

            self.assertEqual(start_date, mock_calculate_start.return_value)

    @patch('app.src.utils.helpers.st.text')
    @patch('app.src.utils.helpers.calculate_execution_start')
    def test_get_command_execution_start_daily_frequency(self,
                                                         mock_calculate_start: MagicMock,
                                                         mock_st_text: MagicMock):
        """
        GIVEN specific execution type and execution frequency
        WHEN passed to the 'get_command_execution_start' function
        THEN check correct execution start value is returned.
        """
        mock_st_text.return_value = True
        execution_type = "Scheduled"
        execution_frequency = "Daily"
        weekdays = ["Tue"]
        date_col = MagicMock()
        slider_col = MagicMock()
        mock_calculate_start.return_value = datetime(2021, 1, 1, 00, 00)

        with patch('app.src.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2021, 1, 1, 00, 00)
            mock_datetime.strftime.return_value = '2020-01-01 00:00:00'
            mock_datetime.weekday.return_value = 1

            start_date = get_command_execution_start(
                execution_type,
                execution_frequency,
                weekdays,
                date_col,
                slider_col
            )

            self.assertEqual(start_date, datetime(2021, 1, 5, 0, 0))

    def test_match_duration_unmatched(self):
        """
        GIVEN current datetime that does not exceed scheduling parameters
        WHEN passed to the 'match_duration' function
        THEN check decision is made to not execute the job.
        """
        now = datetime(2021, 1, 1, 00, 00)
        start = datetime(2021, 1, 2, 00, 00)
        duration = timedelta(1)

        self.assertEqual(match_duration(now, start, duration), False)

    def test_match_duration_matched(self):
        """
        GIVEN current datetime that exceeds scheduling parameters
        WHEN passed to the 'get_command_execution_start' function
        THEN check decision is made to execute the job.
        """
        now = datetime(2021, 1, 10, 00, 00)
        start = datetime(2021, 1, 8, 00, 00)
        duration = timedelta(1)

        self.assertEqual(match_duration(now, start, duration), True)















