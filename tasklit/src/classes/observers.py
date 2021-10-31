"""Classes responsible for handling app usage statistics."""
from inspect import signature
from time import time
from typing import Any, Callable, Dict, Set, Tuple

from tasklit.settings.consts import JobInformation
from tasklit.src.classes.exceptions import ObserverArgumentsMissing


class JobObserver:
    """Class responsible for gathering job usage stats.

    Parameters:
    ___________
    _function_to_track: Callable
        function that is being decorated.
    _arg_job_name: str
        name of the function argument that signifies the job name.
    _arg_command: str
        name of the function argument that signifies the command
            to be executed.
    _args_to_find: Set[str]
        set of arguments which we want to track.
    _signature: signature
        function signature object containing information on function
            definition and arguments used.
    _function_argument_order: Dict[str, int]
        function argument and respective order in the function definition,
            e.g. {'job_name': 1}.
    job: JobInfo
        container for storing job information, e.g. name, duration, etc.

    Methods:
    ________
    _get_function_signature()
        retrieve function signature object.
    _get_argument_position()
        retrieve position of arguments in function definition.
    _get_argument()
        retrieve respective argument value.
    __call__()
        main decorator entrypoint.
    job_statistics()
        retrieve job information.
    """

    def __init__(self, func: Callable):
        """Initialize the class."""
        self._function_to_track = func
        self._arg_job_name = "job_name"
        self._arg_command = "command"
        self._args_to_find: Set[str] = {self._arg_command, self._arg_job_name}
        self._signature: signature = self._get_function_signature(
            self._function_to_track
        )
        self._function_argument_order: Dict[
            str, int
        ] = self._get_argument_position()
        self.job: JobInformation = JobInformation("", "", 0)
        self._check_arguments_found()

    @staticmethod
    def _get_function_signature(func) -> signature:
        """Get the signature of the decorated function.

        Returns:
            function signature object.
        Raises:
              ValueError: if accessing function signature fails.
        """
        try:
            return signature(func)
        except ValueError as exc:
            raise exc

    def _get_argument_position(self) -> Dict[str, int]:
        """Get position of searched for arguments in function definition.

        Returns:
            Dict[str, int] with key standing for argument name,
                value for position (starting from 1).
        Example:
            Case 1: arguments are present

            def f(job_name, command):
                pass
            >>> print(self._get_argument_position(f))
                {'job_name': 1, 'command': 2}

            Case 2: arguments are missing

            def f():
                pass
            >>> print(self._get_argument_position(f))
                {}
        """
        return {
            param: idx
            for idx, param in enumerate(self._signature.parameters.keys())
            if param in self._args_to_find
        }

    def _check_arguments_found(self):
        """Validation check to see if we managed to find the arguments.

        Raises:
            ObserverArgumentsMissing: if some of the arguments could not
                be found.
        """
        missing_arguments = self._args_to_find - set(
            self._function_argument_order.keys()
        )

        if missing_arguments:
            raise ObserverArgumentsMissing(missing_arguments)

    def _get_argument(self, arg_name: str, args: Tuple[str]) -> str:
        """Retrieve value of a given argument from the function."""
        return args[self._function_argument_order[arg_name]]

    def __call__(self, *args, **kwargs) -> Any:
        """Main decorator method.

        Collect information about the job:
            -> job name
            -> command
            -> duration
        """
        # Grab the name of the job and the command
        # to be executed from job arguments.
        job_name = self._get_argument(self._arg_job_name, args)
        command = self._get_argument(self._arg_command, args)

        # Time job execution and update internal job state.
        start_time = time()

        result = self._function_to_track(*args, **kwargs)

        end_time = time()

        job_duration = round(end_time - start_time, 2)

        self.job.name = job_name
        self.job.command = command
        self.job.duration = job_duration

        return result

    @property
    def job_statistics(self) -> JobInformation:
        """Retrieve information about the executed job."""
        return self.job
