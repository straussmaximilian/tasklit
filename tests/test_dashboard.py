"""Unittests for database table logic."""

import unittest

from tasklit.src.classes.exceptions import ObserverArgumentsMissing


class ObserverArgumentsMissingTestCase(unittest.TestCase):
    """Test custom exception implementation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Test class parameters.

        missing_arguments: Set[str]
            missing arguments that threw the exception.
        """
        super(ObserverArgumentsMissingTestCase, cls).setUpClass()
        cls.missing_arguments = {"arg1", "arg2"}

    def test_exception_raises(self):
        """Check raising custom exception."""
        with self.assertRaises(ObserverArgumentsMissing):
            raise ObserverArgumentsMissing(self.missing_arguments)

    def test_exception_representation(self):
        """Check exception error message."""
        self.assertIn(
            "arg1",
            ObserverArgumentsMissing(self.missing_arguments).__str__(),
        )

        self.assertIn(
            "arg2",
            ObserverArgumentsMissing(self.missing_arguments).__str__(),
        )
