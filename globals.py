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

time_values = {}
time_values["Minutes"] = 59
time_values["Hours"] = 59
time_values["Days"] = 364
time_values["Weeks"] = 51

date_translation = {}
date_translation["Days"] = timedelta(days=1)
date_translation["Hours"] = timedelta(hours=1)
date_translation["Minutes"] = timedelta(minutes=1)
date_translation["Weeks"] = timedelta(weeks=1)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

day_lookup = {i: _ for i, _ in enumerate(days)}

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BASE_LOG_DIR = "./logs/"
DEFAULT_LOG_DIR_OUT = f"{BASE_LOG_DIR}stdout.txt"
