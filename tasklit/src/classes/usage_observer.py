"""
Define classes responsible for gathering and storing app usage statistics:
    -> UsageObserver decorator to track function execution
    -> StatTracker to perform calculations and hold data
"""


from collections import namedtuple
from inspect import signature
from time import time


class UsageObserver:
    def __init__(self, func):
        self._job_name = 'job_name'
        self._command = 'command'
        self._function_to_track = func
        self._signature = self._get_function_signature(self._function_to_track)
        self._statistics_to_collect = [
            self._command, self._job_name
        ]
        self._function_argument_order = self._get_argument_position()

        if not self._function_argument_order:
            # We couldn't match parameters to track in the function signature
            raise ValueError

        self.JobInfo = namedtuple("Job", "name command duration executions")

    @staticmethod
    def _get_function_signature(func):
        try:
            return signature(func)
        except ValueError as exc:
            raise exc

    def _get_argument_position(self):
        result = {}

        for idx, param in enumerate(self._signature.parameters.keys()):
            if param in self._statistics_to_collect:
                result[param] = idx

        return result

    def _get_argument(self, arg_name, args):
        return args[self._function_argument_order[arg_name]]

    def __call__(self, *args, **kwargs):
        job_name = self._get_argument(self._job_name, args)
        command = self._get_argument(self._command, args)

        start_time = time()

        result = self._function_to_track(*args, **kwargs)

        end_time = time()

        job_duration = end_time - start_time

        job = self.JobInfo(job_name, command, job_duration, 1)

        return result
