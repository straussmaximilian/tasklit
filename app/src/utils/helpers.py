import os
import sys
import time

from datetime import datetime, timedelta
from multiprocessing import Process
from pathlib import Path
from subprocess import Popen
from typing import (
    Callable,
    List,
    Optional,
    Tuple
)

import pandas as pd
import psutil
import streamlit as st

from sqlalchemy import engine
from sqlalchemy.exc import OperationalError
from streamlit.delta_generator import DeltaGenerator

sys.path.append(os.path.dirname((os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

import app.settings.consts as settings


def app_exception_handler(func: Callable) -> Callable:
    """
    Decorator function to streamline error handling within the app.
    The idea is to have a wrapper around the app that is responsible for displaying
    error messages. Individual helper methods only raise errors that 'bubble' up to this layer
    and get processed.

    Args:
        func: function that returns an application view, e.g. app homepage.

    Returns:
        resolves the inner function.
    """

    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as exc:
            st.error(f"An error was caught: {exc}")
            refresh_app(5)

    return inner


def launch_command_process(command: str, log_filepath: str) -> Popen:
    """
    Start a subprocess for a given command and save
    'stdout' and 'stderr' logs to a respective log file.

    Args:
        command: command to be executed.
        log_filepath: path to the respective log file.

    Raises:
        OSError if log file cannot be created.

    Returns:
        a child process running the given command.
    """
    try:
        with open(log_filepath, "w") as out:
            return Popen(command.split(" "), stdout=out, stderr=out)
    except OSError:
        raise


def terminate_child_processes(parent_process: psutil.Process) -> None:
    """
    Check for any child processes spawned by the parent process and
    - if found - terminate them.

    Args:
        parent_process: parent process object.
    """
    if child_processes := parent_process.children(recursive=True):

        for child_process in child_processes:
            child_process.terminate()

        gone, alive = psutil.wait_procs(child_processes, timeout=3)

        for process in alive:
            process.terminate()


def terminate_process(pid: int) -> None:
    """
    Terminate a running process and any child processes that
    have been spawned by it.

    Raises:
        psutil.NoSuchProcess if related process cannot be found.
    """
    try:
        parent = psutil.Process(pid)
        terminate_child_processes(parent)
        parent.terminate()
        parent.kill()
    except psutil.NoSuchProcess:
        raise


def create_folder_if_not_exists(folder_name: str) -> None:
    """
    Check if a folder exists and create one if not.

    Args:
        folder_name: name of the folder to be checked.
    """
    if not os.path.exists(folder_name):
        Path(folder_name).mkdir(parents=True, exist_ok=True)


def test_command_run(command: str) -> None:
    """
    Utility function to test command execution. Open a subprocess with
    the given command and log output to the default log file.
    The log file will be read and displayed via Streamlit.

    Args:
        command: command to be executed by the process.
    """
    create_folder_if_not_exists(settings.BASE_LOG_DIR)

    test_command_process = launch_command_process(command, settings.DEFAULT_LOG_DIR_OUT)

    stdout = st.empty()
    stop = st.checkbox("Stop")

    while True:
        poll = test_command_process.poll()

        stdout.code("".join(read_log(settings.DEFAULT_LOG_DIR_OUT)))

        if stop or poll is not None:
            terminate_process(test_command_process.pid)
            break


def get_time_interval_info(unit_col: DeltaGenerator,
                           slider_col: DeltaGenerator) -> Tuple[Optional[str], Optional[int]]:
    """
    Get execution frequency information from UI inputs.

    Args:
        unit_col: Streamlit column with UI element to select the corresponding
            execution time interval, e.g. 'minutes', 'hours', etc.
        slider_col: Streamlit column with UI element to select the quantity
            of execution time intervals.

    Returns:
        selected time interval and related execution frequency.
    """
    time_unit = unit_col.selectbox("Select Unit", ("Minutes", "Hours", "Days", "Weeks"))
    time_unit_quantity = slider_col.slider(
        f"Every x {time_unit}", min_value=1, max_value=settings.TIME_VALUES[time_unit]
    )

    return time_unit, time_unit_quantity


def select_weekdays(unit_col: DeltaGenerator) -> Optional[List[str]]:
    """
    Select weekdays on which the process must be executed.

    Args:
        unit_col: Streamlit column with UI multi-select element
            to select appropriate weekdays.

    Returns:
        list strings representing selected weekdays.
    """
    return unit_col.multiselect(
        "Select weekdays:",
        options=list(settings.WEEK_DAYS.values()),
        default=list(settings.WEEK_DAYS.values()),
    )


def get_execution_interval_information(
        execution_frequency: str,
        unit_col: DeltaGenerator,
        slider_col: DeltaGenerator
) -> Tuple[Optional[str], Optional[int], Optional[List[str]]]:
    """
    Get command execution interval information, including time interval (e.g. hours, weeks, etc.),
    related quantity and execution weekdays.

    Args:
        execution_frequency: string indicating execution frequency.
        unit_col: Streamlit column with UI element to select the corresponding
            execution time interval, e.g. 'minutes', 'hours', etc.
        slider_col: Streamlit column with UI element to select the quantity
            of execution time intervals.

    Returns:
        tuple with information about time interval, interval quantity and selected weekdays.
    """
    time_unit = time_unit_quantity = weekdays = None

    if execution_frequency == "Interval":
        time_unit, time_unit_quantity = get_time_interval_info(unit_col, slider_col)

    if execution_frequency == "Daily":
        weekdays = select_weekdays(unit_col)

    return time_unit, time_unit_quantity, weekdays


def calculate_execution_start(date_input_col: DeltaGenerator,
                              time_slider_col: DeltaGenerator) -> datetime:
    """
    Calculate the start datetime of command execution.

    Args:
        date_input_col: Streamlit column with UI element to select execution date.
        time_slider_col:  Streamlit column with UI (slider) element to select hr:min of execution.

    Returns:
        datetime object with the start date & time of execution.
    """
    input_date = date_input_col.date_input("Starting date", datetime.now())
    selected_time = time_slider_col.slider(
        "Timepoint",
        min_value=datetime(2020, 1, 1, 00, 00),
        max_value=datetime(2020, 1, 1, 23, 59),
        value=datetime(2020, 1, 1, 12, 00),
        format="HH:mm",
    )

    execution_date = datetime(input_date.year, input_date.month, input_date.day)
    time_difference = selected_time - datetime(2020, 1, 1, 00, 00, 00)

    return execution_date + time_difference


def get_command_execution_start(
        execution_type: str,
        execution_frequency: str,
        weekdays: Optional[List[str]],
        date_col: DeltaGenerator,
        slider_col: DeltaGenerator
) -> datetime:
    """
    Get the start datetime of command execution.

    Args:
        execution_type: type of execution schedule: is execution "Scheduled" or not.
        execution_frequency: frequency of execution: "Interval" / "Daily"
        weekdays: (optional) list with selected weekdays.
        date_col: Streamlit column with UI element to select execution date.
        slider_col: Streamlit column with UI (slider) element to select hr:min of execution.

    Returns:
        datetime object with the start date & time of execution.
    """
    start = datetime.now()

    if execution_type == "Scheduled":
        start = calculate_execution_start(date_col, slider_col)

        if execution_frequency == "Daily":
            while settings.WEEK_DAYS[start.weekday()] not in weekdays:
                start += timedelta(days=1)

    st.text(f"First execution on {start.strftime(settings.DATE_FORMAT)}.")

    return start


def refresh_app(to_wait: int = 0) -> None:
    """
    (Optionally) wait for a given amount of time (in seconds)
    and trigger Streamlit app refresh.

    Args:
        to_wait: integer indicating amount of seconds to wait.

    Raises:
        RerunException that stops and re-runs the app script.
    """
    if to_wait:
        empty_slot = st.empty()

        for i in range(to_wait):
            empty_slot.write(f"Refreshing in {to_wait - i} seconds...")
            time.sleep(1)

    raise st.script_runner.RerunException(st.script_request_queue.RerunData())


def match_weekday(now: datetime,
                  weekdays: Optional[List[str]]) -> bool:
    """
    Determine if 'today' is the day when a function must be executed.

    Args:
        now: datetime object representing current timestamp.
        weekdays: optional list of ints from 0 to 6 corresponding to different days of the week,
            e.g. 0 for Monday, etc.

    Returns:
        True/False based on the result of the check.
    """
    today = now.weekday()

    try:
        if not weekdays or settings.WEEK_DAYS[today] in weekdays:
            return True
    except KeyError:
        raise

    return False


def match_duration(now: datetime, start: datetime, duration: timedelta) -> bool:
    """
    Check whether the sum of process start date and interval timedelta is less
    than current datetime. If yes -> process must be executed.

    Args:
        now: datetime.now() object.
        start: datetime object with process start date.
        duration: interval timedelta to check whether schedule has been met.

    Returns:
        True/False based on the result of the check.
    """
    return now > (start + duration)


def process_should_execute(now: datetime,
                           start: datetime,
                           duration: timedelta,
                           weekdays: Optional[List[str]]) -> bool:
    """
    Determine whether the process should execute or not:
        -> is it the correct day of the week?
        -> is it the correct scheduled interval?

    Args:
        now: datetime.now()
        start: datetime object with process start date.
        duration: interval timedelta to check whether schedule has been met.
        weekdays: optional list with selected weekdays.

    Returns:
        True/False based on the result of the check.
    """
    return match_weekday(now, weekdays) and match_duration(now, start, duration)


def write_job_execution_log(job_name: str, command: str, now: datetime, msg: str) -> None:
    """
    Save information on job execution to a log file.

    Args:
        job_name: name of the job for which to write the log.
        command: command that was executed.
        now: datetime object with current timestamp.
        msg: message to be logged.

    Raises:
        OSError if log file creation fails.
    """
    now_str = now.strftime(settings.DATE_FORMAT)

    for suffix in [".txt", "_stdout.txt"]:
        try:
            with open(f"{settings.BASE_LOG_DIR}/{job_name}{suffix}", "a") as file:
                if suffix == "_stdout.txt":
                    file.write(f"\n{'=' * 70} \n")
                file.write(f"{now_str} {msg} {command}\n")
        except OSError:
            raise


def scheduler_process(
        command: str,
        job_name: str,
        start: datetime,
        time_unit: Optional[str],
        time_unit_quantity: Optional[int],
        weekdays: Optional[List[str]],
        execution_frequency: str,
        execution_type: str,
) -> None:
    """
    Create an event loop that handles process execution.
    Checks for current date. If date criterion is met -> start the process with command execution.
    Args:
        command: command to be executed.
        job_name: name allocated for the process job.
        start: execution datetime.
        time_unit: (optional) unit of execution time interval, e.g. 'hours', 'days', etc.
        time_unit_quantity: (optional) amount of time interval units.
        weekdays: (optional) list with selected weekdays.
        execution_frequency: frequency of execution: "Interval" / "Daily"
        execution_type: type of execution schedule: is execution "Scheduled" or not.
    """
    filename = f"{settings.BASE_LOG_DIR}/{job_name}_stdout.txt"

    if execution_frequency == "Once":
        launch_command_process(command, filename)
        write_job_execution_log(job_name, command, datetime.now(), "Executed")
        return

    interval_duration = timedelta(days=1) if weekdays else settings.DATE_TRANSLATION[time_unit] * time_unit_quantity

    # If process must be executed now, decrease start date by interval timedelta:
    # this way 'match_duration' will return True in the process_should_execute check.
    if execution_type == "Now":
        start -= interval_duration

    while True:
        now = datetime.now()
        if process_should_execute(now, start, interval_duration, weekdays):
            write_job_execution_log(job_name, command, now, "Executed")
            launched_process = launch_command_process(command, filename)
            launched_process.wait()
            start += interval_duration
        else:
            time.sleep(1)


def create_process_info_dataframe(command: str,
                                  job_name: str,
                                  pid: int,
                                  task_id: int) -> pd.DataFrame:
    """
    Generate a dataframe with process information in the following format:

    {
        'task_id': [],
        'created': [],
        'process id': [],
        'job name': [],
        'command': [],
        'last update': [],
        'running': []
    }.

    Args:
        command: command executed by the process.
        job_name: job name allocated for the process.
        pid: process ID.
        task_id: task ID.

    Returns:
        pandas DF with process related information.
    """
    created = datetime.now()

    return pd.DataFrame(
        {
            "task_id": [task_id],
            "created": [created],
            "process id": [pid],
            "job name": [job_name],
            "command": [command],
            "last update": [None],
            "running": [None],
        }
    )


def save_df_to_sql(df: pd.DataFrame, sql_engine: engine) -> None:
    """
    Save dataframe with process information to a local sql alchemy DB file.

    Args:
        df: process information df.
        sql_engine: sql alchemy engine to use.

    Raises:
        OperationalError: if any sqlalchemy errors have been thrown.
    """
    try:
        df.to_sql("processes", con=sql_engine, if_exists="append", index=False)
    except OperationalError:
        raise


def start_process(command: str, job_name: str, start: datetime,
                  time_unit: Optional[str], time_unit_quantity: Optional[int], weekdays: Optional[List[str]],
                  execution_frequency: str, execution_type: str) -> int:
    """
    Run a process with the selected parameters.

    Args:
        command: command to be executed.
        job_name: name allocated for the process job.
        start: execution datetime.
        time_unit: (optional) unit of execution time interval, e.g. 'hours', 'days', etc.
        time_unit_quantity: (optional) amount of time interval units.
        weekdays: (optional) list with selected weekdays.
        execution_frequency: frequency of execution: "Interval" / "Daily"
        execution_type: type of execution schedule: is execution "Scheduled" or not.

    Returns:
        ID of the started process.
    """
    process = Process(
        target=scheduler_process,
        args=(
            command,
            job_name,
            start,
            time_unit,
            time_unit_quantity,
            weekdays,
            execution_frequency,
            execution_type
        )
    )

    process.start()

    return process.pid


def submit_job(command: str, job_name: str, start: datetime,
               time_unit: Optional[str], time_unit_quantity: Optional[int], weekdays: Optional[List[str]],
               execution_frequency: str, execution_type: str, task_id: int,
               sql_engine: engine) -> None:
    """
    Run a process job and save related process information to an SQL alchemy file.

    Args:
        command: command executed by the process.
        job_name: job name allocated for the process.
        start: start date of the job.
        time_unit: (optional) unit of execution time interval, e.g. 'hours', 'days', etc.
        time_unit_quantity: (optional) amount of time interval units.
        weekdays: (optional) list with selected weekdays.
        execution_frequency: frequency of execution: "Interval" / "Daily"
        execution_type: type of execution schedule: is execution "Scheduled" or not.
        task_id: task ID.
        sql_engine: sql engine to use for saving DF information to sql.
    """
    started_process_id = start_process(command, job_name, start, time_unit, time_unit_quantity,
                                       weekdays, execution_frequency, execution_type)
    process_df = create_process_info_dataframe(command, job_name, started_process_id, task_id)
    save_df_to_sql(process_df, sql_engine)


def read_log(filename: str) -> List[str]:
    """
    Utility function to read a logfile.

    Args:
        filename: name of the log file to be read.

    Raises:
        FileNotFoundError if respective log file is missing.

    Returns:
        list of strings, with each string representing a line.
    """
    try:
        with open(filename, "r", encoding="utf-8") as reader:
            return reader.readlines()
    except FileNotFoundError:
        raise


def get_task_id(df: pd.DataFrame) -> int:
    """
    Generate an ID for a new task:
        -> check for the last used ID
        -> increment by 1

    Args:
        df: dataframe with process information and related task IDs.

    Returns:
        int: new task ID.
    """
    return df["task_id"].max() + 1 if df["task_id"].values else 1


def check_last_process_info_update(job_name: str) -> Optional[datetime]:
    """
    Use 'last modified' timestamp of the job log file to check
    when job and related process information has been updated last.

    Args:
        job_name: name of the job for which to perform the check.

    Raises:
        OSError if the file does not exist or is inaccessible.
        OSError is raised by os.path.getmtime.

    Returns:
        datetime: last modified timestamp.
    """
    filename = f"{settings.BASE_LOG_DIR}/{job_name}.txt"

    try:
        return datetime.fromtimestamp(os.path.getmtime(filename))
    except OSError:
        return None
