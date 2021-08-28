import os
import sys
import socket

import pandas as pd
import psutil
import streamlit as st

from sqlalchemy import create_engine

sys.path.append((os.path.dirname(os.path.dirname(__file__))))

import settings.consts as settings

import src.utils.helpers as helper_functions
from src.utils.job_names import get_job_name


@helper_functions.app_exception_handler
def homepage() -> None:
    """
    Assemble necessary UI elements and helper methods to display application homepage.
    """
    engine = create_engine(settings.APP_ENGINE_PATH, echo=False)

    st.write("# 🕙 Tasklit")
    st.text(f"A browser-based task scheduling system. Running on {socket.gethostname()}.")

    try:
        df = pd.read_sql_table("processes", con=engine)
        df["running"] = df["process id"].apply(
            lambda x: psutil.pid_exists(x) and psutil.Process(x).status() != 'zombie')
    except ValueError:
        df = pd.DataFrame(settings.FORMAT)

    try:
        df["last update"] = df["job name"].apply(lambda x: helper_functions.check_last_process_info_update(x))
    except ValueError:
        pass

    st.table(df)

    if len(df) and False in df["running"].values:
        if st.button("Remove processes that are not running."):
            running = df[df["running"]]
            running.to_sql("processes", con=engine, if_exists="replace", index=False)

            helper_functions.refresh_app()

    with st.expander("New task"):
        job_name = st.text_input("Job name", get_job_name())

        command = st.text_input("Enter command", "ping 8.8.8.8 -c 5")

        if command and st.button("Test command"):
            st.info(f"Running '{command}'")

            helper_functions.test_command_run(command)

        # Get execution frequency settings
        frequency_select_col, unit_select_col, slider_select_col = st.columns(3)
        frequency = frequency_select_col.selectbox(
            "Select Frequency", (
                settings.IMMEDIATE_FREQUENCY,
                settings.INTERVAL_FREQUENCY,
                settings.DAILY_FREQUENCY
            )
        )
        unit, quantity, weekdays = helper_functions.get_execution_interval_information(
            frequency, unit_select_col, slider_select_col
        )

        # Get execution start date
        execution_schedule_col, date_input_col, time_slider_col = st.columns(3)
        execution = execution_schedule_col.selectbox("Execution", ("Now", "Scheduled"))
        start = helper_functions.get_command_execution_start(
            execution,
            frequency,
            weekdays,
            date_input_col,
            time_slider_col
        )

        if st.button(f"Submit"):
            # Moved task ID generation here -> otherwise new task IDs are calculated on each re-render.
            new_task_id = helper_functions.get_task_id(df)

            helper_functions.submit_job(
                command,
                job_name,
                start,
                unit,
                quantity,
                weekdays,
                frequency,
                execution,
                new_task_id,
                engine,
            )

            st.success(
                f"Submitted task {job_name} with task_id {new_task_id} to execute {command}."
            )

            helper_functions.refresh_app(4)

    with st.expander("Explore task"):
        explore_task_id = st.selectbox("task_id", df["task_id"].unique())

        if explore_task_id:

            current_task_row = df[df["task_id"] == explore_task_id].iloc[0]
            current_job_name = current_task_row["job name"]
            current_task_pid = current_task_row["process id"]

            st.write("## Task execution")

            log_file = f"{settings.BASE_LOG_DIR}/{current_job_name}.txt"

            if os.path.isfile(log_file):
                st.code("".join(helper_functions.read_log(log_file)))

            st.write("## Stdout")
            log_file = f"{settings.BASE_LOG_DIR}/{current_job_name}_stdout.txt"

            if os.path.isfile(log_file):
                st.code("".join(helper_functions.read_log(log_file)))

            if st.checkbox("Kill task"):
                if st.button("Click to confirm"):
                    helper_functions.terminate_process(current_task_pid)

                    st.success(
                        f"Terminated task {current_job_name} with task_id {current_task_row['task_id']} and process id {current_task_pid}."
                    )

                    helper_functions.refresh_app(4)

    if st.button("Refresh"):
        helper_functions.refresh_app()
