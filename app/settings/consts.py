from datetime import timedelta


FORMAT = {
    "task_id": [],
    "created": [],
    "process id": [],
    "job name": [],
    "command": [],
    "last update": [],
    "running": [],
}

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

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BASE_LOG_DIR = "./app/logs"

DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}/stdout.txt"
