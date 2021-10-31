"""Application settings and constants."""

import os
from datetime import timedelta
from typing import Dict

HOME_DIR: str = os.path.join(os.path.expanduser("~"), ".tasklit")

if not os.path.isdir(HOME_DIR):
    os.mkdir(HOME_DIR)

# Database parameters
BASE_DATA_DIR: str = os.path.join(HOME_DIR, "data")
SQLITE_APP_ENGINE: str = f"sqlite:///{BASE_DATA_DIR}/process.db"

DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Execution frequencies
IMMEDIATE_FREQUENCY: str = "Once"
INTERVAL_FREQUENCY: str = "Interval"
DAILY_FREQUENCY: str = "Daily"

# Datetime values and translation settings
TIME_VALUES: Dict[str, int] = {
    "Minutes": 59,
    "Hours": 59,
    "Days": 364,
    "Weeks": 51,
}
DATE_TRANSLATION: Dict[str, timedelta] = {
    "Days": timedelta(days=1),
    "Hours": timedelta(hours=1),
    "Minutes": timedelta(minutes=1),
    "Weeks": timedelta(weeks=1),
}
WEEK_DAYS: Dict[int, str] = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}

# Log directories
BASE_LOG_DIR: str = os.path.join(HOME_DIR, "logs")
DEFAULT_LOG_DIR_OUT: str = f"{BASE_LOG_DIR}/stdout.txt"

DEFAULT_TEST_COMMAND: str = (
    "ping 8.8.8.8" if os.name == "nt" else "ping 8.8.8.8 -c 5"
)
