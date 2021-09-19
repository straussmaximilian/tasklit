from dataclasses import dataclass

import pandas as pd

from tasklit.settings.consts import PROCESS_DF_FORMAT, STATS_DF_FORMAT


@dataclass(frozen=True)
class ApplicationDataframes:
    process_df = pd.DataFrame(PROCESS_DF_FORMAT)
    stats_df = pd.DataFrame(STATS_DF_FORMAT)


app_dataframes = ApplicationDataframes()
