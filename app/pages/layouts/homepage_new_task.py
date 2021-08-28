import os
import sys
import streamlit as st

sys.path.append((os.path.dirname(os.path.dirname(__file__))))

import settings.consts as settings
import src.utils.helpers as helper_functions
from src.utils.job_names import get_job_name


def layout_homepage_define_new_task(process_df, sql_engine) -> None:
    """
    Render and process homepage UI layout for defining a new task.

    Args:
        process_df: df with current process information.
        sql_engine: sql engine for saving df into sql.
    """
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

        # Get execution start date settings
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
            new_task_id = helper_functions.get_task_id(process_df)

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
                sql_engine,
            )

            st.success(
                f"Submitted task {job_name} with task_id {new_task_id} to execute {command}."
            )

            helper_functions.refresh_app(4)