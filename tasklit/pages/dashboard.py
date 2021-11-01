import streamlit as st

from tasklit.settings.consts import H4_CSS_STYLE
from tasklit.src.classes import app_db_handler
from tasklit.src.utils.helpers import refresh_app


def usage_dashboard() -> None:
    """Layout and logic for the usage dashboard page."""
    st.markdown("# Task Execution Statistics")
    st.text("Dive deeper into the history of your tasks.")

    # Prepare and display process stats dataframe
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
        sum_duration = stats_df["average_duration"].sum()
        total_duration = round(round(total_runs * sum_duration, 2) / 60, 1)
        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>{total_duration}</h1>",
            unsafe_allow_html=True,
        )

    with top_command_col:
        st.markdown(
            f"<h3 style='text-align: center;'>Top Command</h3>",
            unsafe_allow_html=True,
        )

        top_execs_row = stats_df[
            stats_df["executions"] == stats_df["executions"].max()
        ].index

        top_command = (
            stats_df.at[top_execs_row[0], "command"]
            if top_execs_row.any()
            else "No jobs scheduled"
        )
        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>" f"{top_command}</h1>",
            unsafe_allow_html=True,
        )

    st.markdown("## All jobs")
    stats_df.reset_index(drop=True, inplace=True)
    st.table(stats_df.sort_values(by=["executions"], ascending=False))

    # Handle user triggered app refresh
    if st.button("Refresh"):
        refresh_app()
