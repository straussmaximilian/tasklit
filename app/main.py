import os
import socket

import pandas as pd
import psutil
import streamlit as st

from sqlalchemy import create_engine

import settings.consts as settings

from src.utils.helpers import (
    try_cmd,
    select_date,
    get_task_id,
    terminate_process,
    read_log,
    run_process,
    refresh_app,
    check_last_process_info_update,
)
from src.utils.job_names import get_job_name


# Main interface
engine = create_engine("sqlite:///app/data.db", echo=False)

st.write("# 🕙 Tasklit")
st.text(f"A browser-based task scheduling system. Running on {socket.gethostname()}")

try:
    df = pd.read_sql_table("processes", con=engine)
    df["running"] = df["process id"].apply(lambda x: psutil.pid_exists(x) and psutil.Process(x).status() != 'zombie')
except ValueError:
    df = pd.DataFrame(settings.FORMAT)

try:
    df["last update"] = df["job name"].apply(lambda x: check_last_process_info_update(x))
except ValueError:
    pass

st.table(df)

if (len(df) > 0) and (df["running"] == False).sum() > 0:
    if st.button("Remove processes that are not running."):
        running = df[df["running"]]
        running.to_sql("processes", con=engine, if_exists="replace", index=False)

        refresh_app()

with st.expander("New task"):
    job_name = st.text_input("Job name", get_job_name())
    command = st.text_input("Enter command", "ping 8.8.8.8 -c 5")

    if (command != "") and st.button("Test command"):
        try_cmd(command)

    start, unit, quantity, weekdays, frequency, execution = select_date()

    task_id = get_task_id(df)

    if st.button(f"Submit"):
        p = run_process(
            command,
            job_name,
            start,
            unit,
            quantity,
            weekdays,
            frequency,
            execution,
            task_id,
            engine,
        )

        st.success(
            f"Submitted task {job_name} with task_id {task_id} to execute {command}."
        )

        refresh_app(4)

with st.expander("Explore task"):
    t_id = st.selectbox("task_id", df["task_id"].unique())

    if t_id:

        row = df[df["task_id"] == t_id].iloc[0]
        job_name = row["job name"]
        p_id = row["process id"]

        st.write("## Task execution")

        log_file = f"{settings.BASE_LOG_DIR}{job_name}.txt"
        if os.path.isfile(log_file):
            st.code("".join(read_log(log_file)))

        st.write("## Stdout")
        log_file = f"{settings.BASE_LOG_DIR}/{job_name}_stdout.txt"
        if os.path.isfile(log_file):
            st.code("".join(read_log(log_file)))

        if st.checkbox("Kill task"):
            if st.button("Click to confirm"):
                terminate_process(p_id)

                st.success(
                    f"Terminated task {job_name} with task_id {row['task_id']} and process id {p_id}."
                )

                refresh_app(4)


if st.button("Refresh"):
    refresh_app()
