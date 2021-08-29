import os
import sys
import socket

import psutil
import streamlit as st

from sqlalchemy import create_engine

sys.path.append((os.path.dirname(os.path.dirname(__file__))))

import settings.consts as settings
import src.utils.helpers as helper_functions

from pages.layouts.homepage_new_task import layout_homepage_define_new_task
from pages.layouts.homepage_explore_task import layout_homepage_explore_task


@helper_functions.app_exception_handler
def homepage() -> None:
    """
    Assemble necessary UI elements and helper methods to display application homepage.
    """
    # Initialize sql alchemy engine to access process information
    engine = create_engine(settings.APP_ENGINE_PATH, echo=False)

    # Set app headers
    st.write("# 🕙 Tasklit")
    st.text(f"A browser-based task scheduling system. Running on {socket.gethostname()}.")

    # Prepare and display process dataframe
    process_df = helper_functions.get_process_df(engine)
    helper_functions.update_process_status_info(process_df)
    helper_functions.update_df_process_last_update_info(process_df)
    st.table(process_df)

    # In case process df has any processes that are no longer running (but still alive)
    # provide user an option to remove them.
    if len(process_df) and False in process_df["running"].values:
        if st.button("Remove processes that are not running."):
            running = process_df[process_df["running"]]
            running.to_sql("processes", con=engine, if_exists="replace", index=False)

            helper_functions.refresh_app()

    # Render and handle UI elements for defining new tasks
    layout_homepage_define_new_task(process_df, engine)

    # Render and handle UI elements for exploring existing tasks
    layout_homepage_explore_task(process_df)

    # Handle user triggered app refresh
    if st.button("Refresh"):
        helper_functions.refresh_app()
