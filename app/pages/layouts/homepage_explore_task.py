import os
import sys
import streamlit as st

sys.path.append((os.path.dirname(os.path.dirname(__file__))))

import settings.consts as settings
import src.utils.helpers as helper_functions


def layout_homepage_explore_task(process_df) -> None:
    """
    Render and process homepage UI layout for exploring an existing task.

    Args:
        process_df: df with current process information.
    """
    with st.expander("Explore task"):
        explore_task_id = st.selectbox("task_id", process_df["task_id"].unique())

        if explore_task_id:

            current_task_row = process_df[process_df["task_id"] == explore_task_id].iloc[0]
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
                        f"Terminated task {current_job_name} with task_id {current_task_row['task_id']}"
                        f" and process id {current_task_pid}."
                    )

                    helper_functions.refresh_app(4)
