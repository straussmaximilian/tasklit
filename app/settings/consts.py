from datetime import timedelta


# DB Path
APP_ENGINE_PATH = "sqlite:///app/process_data.db"

# Formats
FORMAT = {
    "task_id": [],
    "created": [],
    "process id": [],
    "job name": [],
    "command": [],
    "last update": [],
    "running": [],
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
BASE_LOG_DIR = "./app/logs"
DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}/stdout.txt"
