import os

from datetime import timedelta


# Home dir
HOME_DIR = os.path.join(os.path.expanduser('~'), '.tasklit')

if not os.path.isdir(HOME_DIR):
    os.mkdir(HOME_DIR)

# Database parameters
BASE_DATA_DIR = os.path.join(HOME_DIR, "data")
SQLITE_APP_ENGINE = f"sqlite:///{BASE_DATA_DIR}/process.db"

# Formats
PROCESS_DF_FORMAT = {
    "task_id": [],
    "created": [],
    "process id": [],
    "job name": [],
    "command": [],
    "last update": [],
    "running": [],
}
STATS_DF_FORMAT = {
    "job_name": [],
    "command": [],
    "avg. duration": [],
    "executions": []
}
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Execution frequencies
IMMEDIATE_FREQUENCY = "Once"
INTERVAL_FREQUENCY = "Interval"
DAILY_FREQUENCY = "Daily"

# Datetime values and translation settings
TIME_VALUES = {"Minutes": 59, "Hours": 59, "Days": 364, "Weeks": 51}
DATE_TRANSLATION = {"Days": timedelta(days=1), "Hours": timedelta(hours=1), "Minutes": timedelta(minutes=1),
                    "Weeks": timedelta(weeks=1)}
WEEK_DAYS = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun"
}

# Log directories
BASE_LOG_DIR = os.path.join(HOME_DIR, "logs")
DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}/stdout.txt"

DEFAULT_TEST_COMMAND = 'ping 8.8.8.8' if os.name == 'nt' else 'ping 8.8.8.8 -c 5'

