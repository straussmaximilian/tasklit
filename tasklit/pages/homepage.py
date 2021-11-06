"""Application homepage layout and logic."""
import socket

import streamlit as st

import tasklit.src.utils.helpers as helper_functions
from tasklit.pages.layouts.footer import footer
from tasklit.pages.layouts.header import header
from tasklit.pages.layouts.homepage_explore_task import (
    layout_homepage_explore_task,
)
from tasklit.pages.layouts.homepage_new_task import (
    layout_homepage_define_new_task,
)
from tasklit.src.classes import app_db_handler
from tasklit.src.classes.data_repository import DataRepository


@helper_functions.app_exception_handler
def homepage() -> None:
    """UI logic to display application homepage."""
    header(
        "# 🕙 Tasklit",
        f"A browser-based task scheduling system. "
        f"Running on {socket.gethostname()}.",
    )

    # Prepare and display process dataframe
    process_df = app_db_handler.load_dataframe(
        DataRepository.process_table_name
    )
    helper_functions.update_process_status_info(process_df)
    helper_functions.update_df_process_last_update_info(process_df)
    st.table(process_df)

    # In case process df has any processes that are no longer running
    # (but still alive) provide user an option to remove them.
    if False in process_df["running"].values:
        if st.button("Remove processes that are not running."):
            running = process_df[process_df["running"]]
            app_db_handler.save_dataframe(
                running, app_db_handler.process_table_name, if_exists="replace"
            )

            helper_functions.refresh_app()

    # Render and handle UI elements for defining new tasks
    layout_homepage_define_new_task(process_df)

    # Render and handle UI elements for exploring existing tasks
    layout_homepage_explore_task(process_df)

    footer()
