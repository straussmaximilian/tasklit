"""Custom application exceptions."""
from typing import Set


class ObserverArgumentsMissing(Exception):
    """Exception raised for errors in the JobObserver class.

    Parameters:
    ___________
    args: List[str]
        list of argument names that couldn't be identified
            in the function definition.
    _message: str
        error explanation.
    """

    def __init__(
        self,
        arguments: Set[str],
        message: str = "Required arguments are missing: ",
    ):
        self._message = f"{message}{', '.join([arg for arg in arguments])}."
        super().__init__(self._message)

    def __str__(self):
        return f"{self._message}"
