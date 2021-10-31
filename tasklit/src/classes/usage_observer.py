"""Classes responsible for handling app usage statistics."""
from collections import namedtuple
from inspect import signature
from time import time

from tasklit.src.classes import app_db_handler
from tasklit.src.classes.storage_repositories import DataRepository


class UsageObserver:
    """Placeholder."""

    def __init__(self, func):
        """Class initialization."""
        self._db_handler: DataRepository = app_db_handler
        self._job_name = "job_name"
        self._command = "command"
        self._function_to_track = func
        self._signature = self._get_function_signature(self._function_to_track)
        self._statistics_to_collect = [self._command, self._job_name]
        self._function_argument_order = self._get_argument_position()

        if not self._function_argument_order:
            raise ValueError

        self.JobInfo = namedtuple("Job", "name command duration executions")

    @staticmethod
    def _get_function_signature(func):
        try:
            return signature(func)
        except ValueError as exc:
            raise exc

    def _get_argument_position(self):
        return {
            param: idx
            for idx, param in enumerate(self._signature.parameters.keys())
            if param in self._statistics_to_collect
        }

    def _get_argument(self, arg_name, args):
        return args[self._function_argument_order[arg_name]]

    def __call__(self, *args, **kwargs):
        """Placeholder."""
        job_name = self._get_argument(self._job_name, args)
        command = self._get_argument(self._command, args)

        start_time = time()

        result = self._function_to_track(*args, **kwargs)

        end_time = time()

        job_duration = end_time - start_time

        job = self.JobInfo(job_name, command, job_duration, 1)
        print(job)

        return result
