import streamlit as st
import subprocess
import psutil
import pandas as pd
import time
from multiprocessing import Process
from datetime import datetime
from globals import (
    DATE_FORMAT,
    time_values,
    day_lookup,
    BASE_LOG_DIR,
    DEFAULT_LOG_DIR_OUT,
    date_translation,
)
import sqlalchemy
from typing import Union
import os


def try_cmd(command: str):
    """
    Utility function to test command line execution
    Will open a subprocess with the given command and log to a default file.
    The log file will be read and displayed via streamlit.
    """
    st.info(f"Running '{command}'")
    with open(DEFAULT_LOG_DIR_OUT, "wb") as out:
        p = subprocess.Popen(command.split(" "), stdout=out, stderr=out)
    stdout = st.empty()
    stop = st.checkbox("Stop")
    while True:
        poll = p.poll()
        stdout.code("".join(read_log(DEFAULT_LOG_DIR_OUT)))
        if stop or poll is not None:
            terminate_process(p.pid)
            break


def select_date():
    """
    Utility function to select scheduling information.
    """

    col1, col2, col3 = st.beta_columns(3)

    frequency = col1.selectbox("Select Frequency", ("Once", "Interval", "Daily"))

    if frequency == "Interval":
        unit = col2.selectbox("Select Unit", ("Minutes", "Hours", "Days", "Weeks"))
        quantity = col3.slider(
            f"Every x {unit}", min_value=1, max_value=time_values[unit]
        )
    else:
        unit = None
        quantity = None

    if frequency == "Daily":
        weekdays = col2.multiselect(
            "Select weekdays:",
            options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        )
    else:
        weekdays = None

    c1, c2, c3 = st.beta_columns(3)

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
            while day_lookup[start.weekday()] not in weekdays:
                start += timedelta(days=1)
    else:
        start = datetime.now()

    start_dt = start.strftime(DATE_FORMAT)
    st.text(f"Scheduled first execution {start_dt}")

    return start, unit, quantity, weekdays, frequency, execution


def run_job(command: str, job_name: str) -> Process:
    """
    Starts a subprocess for a given command and logs to file.
    """
    with open(f"{BASE_LOG_DIR}{job_name}_stdout.txt", "ab") as out:
        p = subprocess.Popen(command.split(" "), stdout=out, stderr=out)
        return p


def refresh(to_wait: int):
    """
    Utility function that waits for a given amount and then restarts streamlit.
    """
    ref = st.empty()
    for i in range(to_wait):
        ref.write(f"Refreshing in {to_wait-i} s")
        time.sleep(1)
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


def check_weekday(now: datetime, weekdays: list) -> bool:
    """
    Check if function should be executed based on the weekday
    """
    if weekdays is None:
        return True  # Always execute if this is none
    else:
        if day_lookup[now.weekday()] in weekdays:
            return True
        else:
            return False


def write_execution_log(job_name: str, command: str, now: datetime, msg: str):
    """
    Utility function to write execution time to log.
    """
    now_str = now.strftime(DATE_FORMAT)
    for suffix in [".txt", "_stdout.txt"]:
        with open(f"{BASE_LOG_DIR}{job_name}{suffix}", "a") as file:
            if suffix == "_stdout.txt":
                file.write(f"\n{'='*70} \n")
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
    task_id: int,
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
            timedelta = datetime.timedelta(days=1)
        else:
            timedelta = date_translation[unit] * quantity

        if execution == "Now":
            start -= timedelta

        while True:
            now = datetime.now()
            if check_weekday(now, weekdays) and (now > (start + timedelta)):
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
            execution,
            task_id,
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


def write_st_log(file: str):
    """
    Utility function to read a logfile and print in streamlit.
    """
    with open(file, "r", encoding="utf-8") as reader:
        log = reader.readlines()
        st.code("".join(log))


def read_log(file: str) -> list:
    """
    Utility function to read a logfile.
    """
    with open(file, "r", encoding="utf-8") as reader:
        log = reader.readlines()
        return log


def get_task_id(df: pd.DataFrame) -> int:
    """
    Returns a unique task_id based on existing task ids.
    """
    task_id = 1
    while task_id in df["task_id"].to_list():
        task_id += 1

    return task_id


def terminate_process(pid: int):
    """
    Function to terminate a process.
    """
    try:
        parent = psutil.Process(pid)
        procs = parent.children(recursive=True)
        for p in procs:
            p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=3)
        for p in alive:
            p.kill()

        parent.terminate()
        parent.kill()
    except psutil.NoSuchProcess:
        st.write(f"Process {pid} not found.")


def get_stamp(x: str) -> Union[datetime, None]:
    """
    Return the timestamp for a process name.
    """
    file = f"{BASE_LOG_DIR}{x}.txt"
    if os.path.isfile(file):
        return datetime.fromtimestamp(os.path.getmtime(file))
    else:
        return None
