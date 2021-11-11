"""Handle update of task statistics information in the database."""
from dataclasses import asdict

import numpy as np
import pandas as pd

from tasklit.settings.consts import TaskInformation
from tasklit.src.classes import app_db_handler
from tasklit.src.classes.data_repository import DataRepository


class TaskStatisticsTracker:
    """Calculate and update changes to task usage statistics.

    Parameters:
    ___________
    _task_info: TaskInformation
        task specific information, e.g. name, duration, etc.
    _db_handler: DataRepository
        data repository implementation to handle DB save / load operations.
    _stats_df: pd.Dataframe
        pandas dataframe with process stat info.

    Methods:
    ________
    _load_stats_df()
        load stats dataframe from a database table.
    _save_stats_df()
        save stats dataframe to a database table.
    _task_exists()
        check if this is a new task or not.
    _add_new_task()
        add a new task to the list of tasks.
    _update_existing_task()
        update an existing task in the list of tasks.
    update_task_stats()
        update task information in the database.
    """

    def __init__(self, task: TaskInformation):
        """Initialize TaskStatisticsTracker."""
        self._task_info = task
        self._db_handler: DataRepository = app_db_handler
        self._stats_df = self._load_stats_df()

    def _load_stats_df(self) -> pd.DataFrame:
        """Load task stats dataframe from the corresponding DB table.

        Returns:
            pd.Dataframe: dataframe with stats info for all tasks.
        """
        return self._db_handler.load_dataframe(DataRepository.stats_table_name)

    def _save_stats_df(self, df: pd.DataFrame) -> None:
        """Save task stats dataframe to the corresponding DB table."""
        return self._db_handler.save_dataframe(
            df, DataRepository.stats_table_name, if_exists="replace"
        )

    def _task_exists(self) -> bool:
        """Check whether this is a new task.

        Returns:
            bool: result of the check.
        """
        return self._task_info.task_name in self._stats_df.task_name.values

    def _add_new_task(self) -> None:
        """Append a new task to the dataframe with current tasks."""
        self._stats_df = self._stats_df.append(
            asdict(self._task_info), ignore_index=True
        )

    def _get_idx_row_to_update(self) -> np.int64:
        """Get index of the dataframe row that must be updated.

        Returns:
            row index value.

        Raises:
            IndexError: in case there are no rows in the dataframe.
        """
        try:
            return self._stats_df[
                self._stats_df["task_name"] == self._task_info.task_name
            ].index[0]
        except IndexError:
            raise IndexError("Failed to find a task to update.")

    def _update_existing_task(self) -> None:
        """Update stat information of an existing task.

        To update:
            -> number of times the task was executed
            -> average duration of the task
        """
        df_idx_row_to_update = self._get_idx_row_to_update()

        init_count_exec = self._stats_df.at[df_idx_row_to_update, "executions"]
        updated_count_exec = init_count_exec + self._task_info.executions

        init_avg_duration = self._stats_df.at[
            df_idx_row_to_update, "average_duration"
        ]

        # Update number of executions
        self._stats_df.at[
            df_idx_row_to_update, "executions"
        ] = updated_count_exec

        # Update average duration
        combined_time_for_prev_executions = init_count_exec * init_avg_duration

        self._stats_df.at[df_idx_row_to_update, "average_duration"] = round(
            (
                combined_time_for_prev_executions
                + self._task_info.average_duration
            )
            / updated_count_exec,
            2,
        )

    def update_task_stats(self) -> None:
        """Update historical information with the new task."""
        if not self._task_exists():
            self._add_new_task()
        else:
            self._update_existing_task()
        self._save_stats_df(self._stats_df)
