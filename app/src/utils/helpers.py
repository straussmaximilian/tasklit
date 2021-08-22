import os
import sys
import time

from datetime import datetime, timedelta
from multiprocessing import Process
from pathlib import Path
from subprocess import Popen
from typing import List, Union

import pandas as pd
import psutil
import sqlalchemy
import streamlit as st

sys.path.append(os.path.dirname((os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

import app.settings.consts as settings


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
        st.write(f"Process {pid} not found.")
        raise psutil.NoSuchProcess(f"Process {pid} not found.")


def try_cmd(command: str):
    """
    Utility function to test command line execution
    Will open a subprocess with the given command and log to a default file.
    The log file will be read and displayed via streamlit.
    """
    st.info(f"Running '{command}'")

    if not os.path.exists(settings.BASE_LOG_DIR):
        Path(settings.BASE_LOG_DIR).mkdir(parents=True, exist_ok=True)

    with open(settings.DEFAULT_LOG_DIR_OUT, "w") as out:
        p = Popen(command.split(" "), stdout=out, stderr=out)
    stdout = st.empty()
    stop = st.checkbox("Stop")
    while True:
        poll = p.poll()
        stdout.code("".join(read_log(settings.DEFAULT_LOG_DIR_OUT)))
        if stop or poll is not None:
            terminate_process(p.pid)
            break


def select_date():
    """
    Utility function to select scheduling information.
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


def run_job(command: str, job_name: str) -> Popen:
    """
    Start a subprocess for a given command and save
    'stdout' and 'stderr' logs to a respective log file.

    Args:
        command: command to be executed.
        job_name: name of the job to be used for log file creation.

    Raises:
        OSError if log file cannot be created.

    Returns:
        a child process running the given command.
    """
    filename = f"{settings.BASE_LOG_DIR}/{job_name}_stdout.txt"

    try:
        with open(filename, "ab") as out:
            return Popen(command.split(" "), stdout=out, stderr=out)
    except OSError:
        raise OSError(f"Failed to create the log file: {filename}.")


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
        raise KeyError(f"Failed to map {today} to a corresponding week day.")

    return False


def write_execution_log(job_name: str, command: str, now: datetime, msg: str):
    """
    Utility function to write execution time to log.
    """
    now_str = now.strftime(settings.DATE_FORMAT)
    for suffix in [".txt", "_stdout.txt"]:
        with open(f"{settings.BASE_LOG_DIR}/{job_name}{suffix}", "a") as file:
            if suffix == "_stdout.txt":
                file.write(f"\n{'=' * 70} \n")
            file.write(f"{now_str} {msg} {command}\n")


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

    if frequency == "Once":
        write_execution_log(job_name, command, datetime.now(), "Executed")
        p = run_job(command, job_name)
    else:
        if weekdays is not None:
            timedelta = timedelta(days=1)
        else:
            timedelta = settings.DATE_TRANSLATION[unit] * quantity

        if execution == "Now":
            start -= timedelta

        while True:
            now = datetime.now()
            if function_should_execute(now, weekdays) and (now > (start + timedelta)):
                # Write Execution
                write_execution_log(job_name, command, now, "Executed")
                p = run_job(command, job_name)
                p.wait()
                start += timedelta
            else:
                time.sleep(1)


def run_process(
        command: str,
        job_name: str,
        start: datetime,
        unit: str,
        quantity: int,
        weekdays: list,
        frequency: str,
        execution: str,
        task_id: int,
        engine: sqlalchemy.engine.base.Engine,
):
    # st.write(command, job_name, start, unit, quantity, weekdays, frequency, task_id)
    created = datetime.now()  # .strftime("%d_%m_%Y %H:%M:%S")
    # FORMAT = {'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}

    p = Process(
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
        ),
    )
    p.start()
    df = pd.DataFrame(
        {
            "task_id": [task_id],
            "created": [created],
            "process id": [p.pid],
            "job name": [job_name],
            "command": [command],
            "last update": [None],
            "running": [None],
        }
    )
    df.to_sql("processes", con=engine, if_exists="append", index=False)
    # FORMAT = {'task_id':[],'created':[], 'process id' : [], 'job name': [], 'command': [], 'last update': [], 'running': []}


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
        raise FileNotFoundError(f"Log file {filename} is missing.")


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
    return df["task_id"].max() + 1


def check_last_process_info_update(job_name: str) -> datetime:
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
    except OSError as exc:
        raise OSError(f"Processing log file {filename} caused {exc}.")
