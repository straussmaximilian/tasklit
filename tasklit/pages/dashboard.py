"""UI logic and elements to display task dashboard."""
import streamlit as st

from tasklit.pages.layouts.footer import footer
from tasklit.pages.layouts.header import header
from tasklit.settings.consts import H4_CSS_STYLE
from tasklit.src.classes import app_db_handler
from tasklit.src.utils.helpers import calculate_total_task_duration


def usage_dashboard() -> None:
    """Layout and logic for the usage dashboard page."""
    header(
        "# 📈 Task Statistics", "Dive deeper into the history of your tasks."
    )

    stats_df = app_db_handler.load_dataframe(app_db_handler.stats_table_name)

    total_execs_col, total_duration_col, top_command_col = st.columns(3)

    with total_execs_col:
        st.markdown(
            "<h3 style='text-align: center;'>Tasks Run</h3>",
            unsafe_allow_html=True,
        )
        total_runs = stats_df["executions"].sum()
        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>{total_runs}</h1>",
            unsafe_allow_html=True,
        )

    with total_duration_col:
        st.markdown(
            "<h3 style='text-align: center;'>Total Duration (min.)</h3>",
            unsafe_allow_html=True,
        )
        duration = stats_df["average_duration"].values
        executions = stats_df["executions"].values
        total = calculate_total_task_duration(duration, executions)

        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>{total}</h1>",
            unsafe_allow_html=True,
        )

    with top_command_col:
        st.markdown(
            "<h3 style='text-align: center;'>Top Command</h3>",
            unsafe_allow_html=True,
        )

        # What if multiple commands have the same max? ->
        # we auto pick the first one. Alternative could be to show multiple.
        try:
            top_execs_row_idx = stats_df[
                stats_df["executions"] == stats_df["executions"].max()
            ].index[0]
            top_command = stats_df.at[top_execs_row_idx, "command"]
        except IndexError:
            # Index error will happen if the dataframe is empty =>
            # no tasks have been run yet.
            top_command = "no task runs"

        st.markdown(
            f"<h4 style='{H4_CSS_STYLE}'>" f"{top_command}</h1>",
            unsafe_allow_html=True,
        )

    st.markdown("## Task History")
    # Prepare stats DF for display
    st.table(
        stats_df.sort_values(by=["executions"], ascending=False).style.format(
            {"average_duration": "{:.2f}"}
        )
    )

    footer()
