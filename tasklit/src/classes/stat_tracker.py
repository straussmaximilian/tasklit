import pandas as pd

from tasklit.src.classes.db import app_db_handler


class StatTracker:
    def __init__(self, job):
        self._db_handler = app_db_handler
        self._stats_df = self._load_stats_df()
        self._job = job

    @staticmethod
    def _load_stats_df():
        return app_db_handler.load_df_from_sql(app_db_handler.stats_table_name)

    @staticmethod
    def _save_stats_df(df: pd.DataFrame):
        return app_db_handler.save_df_to_sql(df, app_db_handler.stats_table_name)

    def _update_df_with_new_job(self):
        pass

    def _update_df_existing_job(self):
        pass

    def _update_current_stats(self, job):
        # Is job name in df?
        # Yes: do an upsert into DF, but change values in average duration and executions.
        # No: add a row to df
        pass

