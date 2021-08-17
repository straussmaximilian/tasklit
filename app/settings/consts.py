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

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DAY_LOOKUP = {i: _ for i, _ in enumerate(DAYS)}

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BASE_LOG_DIR = "./logs/"
DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}stdout.txt"
