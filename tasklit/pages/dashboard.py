"""UI logic and elements to display task dashboard."""
from functools import reduce

import streamlit as st

from tasklit.pages.layouts.footer import footer
from tasklit.settings.consts import H4_CSS_STYLE
from tasklit.src.classes import app_db_handler


def usage_dashboard() -> None:
    """Layout and logic for the usage dashboard page."""
    st.markdown("# Task Execution Statistics")
    st.text("Dive deeper into the history of your tasks.")

    stats_df = app_db_handler.load_dataframe(app_db_handler.stats_table_name)

    total_execs_col, total_duration_col, top_command_col = st.columns(3)

    with total_execs_col:
        st.markdown(
            f"<h3 style='text-align: center;'>" f"Tasks Run</h3>",
            unsafe_allow_html=True,
        )
        total_runs = stats_df["executions"].sum()
        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>{total_runs}</h1>",
            unsafe_allow_html=True,
        )

    with total_duration_col:
        st.markdown(
            f"<h3 style='text-align: center;'>" f"Total Duration (min.)</h3>",
            unsafe_allow_html=True,
        )
        duration = stats_df["average_duration"].values
        execs = stats_df["executions"].values
        total = reduce(
            lambda t, tup: t + tup[0] * tup[1], zip(duration, execs), 0
        )

        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>{round(total / 60, 2)}</h1>",
            unsafe_allow_html=True,
        )

    with top_command_col:
        st.markdown(
            f"<h3 style='text-align: center;'>Top Command</h3>",
            unsafe_allow_html=True,
        )

        # What if multiple commands have the same max? ->
        # we auto pick the first one. Alternative could be to show multiple.
        top_execs_row = stats_df[
            stats_df["executions"] == stats_df["executions"].max()
        ].index

        top_command = (
            stats_df.at[top_execs_row[0], "command"]
            if top_execs_row.any()
            else "No tasks scheduled"
        )
        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>" f"{top_command}</h1>",
            unsafe_allow_html=True,
        )

    st.markdown("## Task History")
    # Prepare stats DF for display
    stats_df.reset_index(drop=True, inplace=True)
    st.table(
        stats_df.sort_values(by=["executions"], ascending=False).style.format(
            {"average_duration": "{:.2f}"}
        )
    )

    footer()
