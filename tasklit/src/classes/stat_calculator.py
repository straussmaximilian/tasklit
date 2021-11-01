from dataclasses import asdict

import pandas as pd

from tasklit.settings.consts import JobInformation
from tasklit.src.classes.storage_repositories import DataRepository


class JobStatCalculator:
    def __init__(self, job: JobInformation, db_handler: DataRepository):
        self._db_handler = db_handler
        self._stats_df = self._load_stats_df()
        self._job_info = job
        self.update_current_stats()

    def _load_stats_df(self) -> pd.DataFrame:
        return self._db_handler.load_dataframe(DataRepository.stats_table_name)

    def _save_stats_df(self, df: pd.DataFrame) -> None:
        return self._db_handler.save_dataframe(
            df, DataRepository.stats_table_name, if_exists="replace"
        )

    def _job_exists(self):
        return self._job_info.job_name in self._stats_df.job_name.values

    def _add_new_job(self):
        self._stats_df = self._stats_df.append(
            asdict(self._job_info), ignore_index=True
        )

    def _update_existing_job(self):
        df_row_to_update = self._stats_df[
            self._stats_df["job_name"] == self._job_info.job_name
        ].index[0]

        init_count_exec = self._stats_df.at[df_row_to_update, "executions"]
        updated_count_exec = init_count_exec + 1

        init_avg_duration = self._stats_df.at[
            df_row_to_update, "average_duration"
        ]

        # Update number of executions
        self._stats_df.at[df_row_to_update, "executions"] = updated_count_exec

        # Update average duration
        combined_time_for_prev_executions = init_count_exec * init_avg_duration

        self._stats_df.at[df_row_to_update, "average_duration"] = round(
            (
                combined_time_for_prev_executions
                + self._job_info.average_duration
            )
            / updated_count_exec,
            2,
        )

    def update_current_stats(self) -> None:
        if not self._job_exists():
            self._add_new_job()
        else:
            self._update_existing_job()
        self._save_stats_df(self._stats_df)
