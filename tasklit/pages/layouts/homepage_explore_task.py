import os
import sys
import streamlit as st

sys.path.append((os.path.dirname(os.path.dirname(__file__))))

import tasklit.settings.consts as settings
import tasklit.src.utils.helpers as helper_functions


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

            # Display task execution log
            st.write("## Task Execution Log")
            st.code(
                helper_functions.display_process_log_file(
                    f"{settings.BASE_LOG_DIR}/{current_job_name}.txt"
                )
            )

            # Display task STDOUT log
            st.write("## Task Stdout Log")
            st.code(
                helper_functions.display_process_log_file(
                    f"{settings.BASE_LOG_DIR}/{current_job_name}_stdout.txt"
                )
            )

            if st.checkbox("Kill task"):
                if st.button("Click to confirm"):
                    helper_functions.terminate_process(current_task_pid)

                    st.success(
                        f"Terminated task {current_job_name} with task_id {current_task_row['task_id']}"
                        f" and process id {current_task_pid}."
                    )

                    helper_functions.refresh_app(4)
