import os
import sys
import time

from datetime import datetime, timedelta
from multiprocessing import Process
from pathlib import Path
from subprocess import Popen
from typing import (
    List,
    Union,
    Optional
)

import pandas as pd
import psutil
import streamlit as st

from sqlalchemy.exc import OperationalError

sys.path.append(os.path.dirname((os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

import app.settings.consts as settings


def app_exception_handler(func):
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


def select_date() :
    """
    Get process scheduling information from UI inputs.
    """

    col1, col2, col3 = st.columns(3)

    frequency = col1.selectbox("Select Frequency", ("Once", "Interval", "Daily"))

    if frequency == "Interval":
        unit = col2.selectbox("Select Unit", ("Minutes", "Hours", "Days", "Weeks"))
        quantity = col3.slider(
            f"Every x {unit}", min_value=1, max_value=settings.TIME_VALUES[unit]
        )
    else:
        unit = None
        quantity = None

    if frequency == "Daily":
        weekdays = col2.multiselect(
            "Select weekdays:",
            options=list(settings.WEEK_DAYS.values()),
            default=list(settings.WEEK_DAYS.values()),
        )
    else:
        weekdays = None

    c1, c2, c3 = st.columns(3)

    execution = c1.selectbox("Execution", ("Now", "Scheduled"))

    if execution == "Scheduled":
        date = c2.date_input("Starting date", datetime.now())
        time = c3.slider(
            "Timepoint",
            min_value=datetime(2020, 1, 1, 00, 00),
            max_value=datetime(2020, 1, 1, 23, 59),
            value=datetime(2020, 1, 1, 12, 00),
            format="HH:mm",
        )
        date = datetime(date.year, date.month, date.day)
        td_ = time - datetime(2020, 1, 1, 00, 00, 00)
        start = date + td_
        if frequency == "Daily":
            while settings.WEEK_DAYS[start.weekday()] not in weekdays:
                start += timedelta(days=1)
    else:
        start = datetime.now()

    start_dt = start.strftime(settings.DATE_FORMAT)
    st.text(f"Scheduled first execution {start_dt}")

    return start, unit, quantity, weekdays, frequency, execution


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

    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


def function_should_execute(now: datetime,
                            weekdays: Union[List[str], None]) -> bool:
    """
    Determine if 'today' is the day when a function must be executed.

    Args:
        now: datetime object representing current timestamp.
        weekdays: list of ints from 0 to 6 corresponding to different days of the week,
            e.g. 0 for Monday, etc.

    Returns:
        True/False depending on the check..
    """
    today = now.weekday()

    try:
        if not weekdays or settings.WEEK_DAYS[today] in weekdays:
            return True
    except KeyError:
        raise

    return False


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
        unit: str,
        quantity: int,
        weekdays: list,
        frequency: str,
        execution: str,
):
    """
    Scheduling process.
    Creates an event loop that updates very second and checks for the date.
    Executes command if date criterion is met.
    """
    filename = f"{settings.BASE_LOG_DIR}/{job_name}_stdout.txt"

    if frequency == "Once":
        write_job_execution_log(job_name, command, datetime.now(), "Executed")
        p = launch_command_process(command, filename)
    else:
        if weekdays is not None:
            duration = timedelta(days=1)
        else:
            duration = settings.DATE_TRANSLATION[unit] * quantity

        if execution == "Now":
            start -= duration

        while True:
            now = datetime.now()
            if function_should_execute(now, weekdays) and (now > (start + duration)):
                # Write Execution
                write_job_execution_log(job_name, command, now, "Executed")
                p = launch_command_process(command, filename)
                p.wait()
                start += timedelta
            else:
                time.sleep(1)


def create_process_info_dataframe(command, job_name, pid, task_id, engine):
    """
    # FORMAT = {'task_id':[],'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}
    Args:
        command:
        job_name:
        pid:
        task_id:
        engine:

    Returns:

    """
    created = datetime.now()

    df = pd.DataFrame(
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

    try:
        df.to_sql("processes", con=engine, if_exists="append", index=False)
    except OperationalError:
        raise


def run_process(command: str, job_name: str, start: datetime, unit: str,
                quantity: int, weekdays: list, frequency: str, execution: str):
    process = Process(
        target=scheduler_process,
        args=(
            command,
            job_name,
            start,
            unit,
            quantity,
            weekdays,
            frequency,
            execution
        )
    )

    process.start()

    return process.pid


def submit_job(command, job_name, start, unit, quantity, weekdays,
               frequency, execution, task_id, engine):
    started_process_id = run_process(command, job_name, start, unit,
                                     quantity, weekdays, frequency, execution)
    create_process_info_dataframe(command, job_name, started_process_id,
                                  task_id, engine)


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
