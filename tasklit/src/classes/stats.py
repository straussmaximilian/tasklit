"""
Define classes responsible for gathering and storing app usage statistics:
    -> total number of executed tasks
    -> number of executions per job
"""
from inspect import signature
from time import time

import pandas as pd


class UsageTracker:
    def __init__(self, func):
        """
        Statistics per job:
        {'job_name': {
            'command': '',
            'executions': 0,
            'average_duration (sec)': 0
        }}
        """
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

        self._total_jobs_executed = 0
        self._statistics_per_job = {}
        self._job_stats = pd.DataFrame(
            columns=[
                'job_name',
                'command',
                'executions',
                'average_duration (seconds)'
            ]
        )

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

    def _increment_total_submitted_jobs(self):
        self._total_jobs_executed += 1

    def _save_job_information(, duration):
        self._statistics_per_job[args[2]] = {
            'command': command,
            'executions': self._statistics_per_job[job_name].get('executions', 0) + 1,
            'average_duration': (duration + self._statistics_per_job[job_name].get('average_duration', 0)) /
                                self._statistics_per_job['executions']
        }

    def __call__(self, *args, **kwargs):
        job_name = self._get_argument(self._job_name, args)
        command = self._get_argument(self._command, args)

        self._increment_total_submitted_jobs()

        start_time = time()

        result = self._function_to_track(*args, **kwargs)

        end_time = time()

        job_duration = end_time - start_time

        print(job_duration)
        return result
