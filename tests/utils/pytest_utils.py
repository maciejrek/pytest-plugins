import pytest


def add_marks(*args):  # type: ignore
    """Add multiple marks to test."""

    def _(f):  # type: ignore
        for mark in args:
            f = getattr(pytest.mark, mark)(f)
        return f

    return _


class MockResponse:
    """Mock response object in external_api tests."""

    def __init__(self, json_data, status_code, url=""):
        """Init method of MockResponse class.
        Args:
            json_data: Mocked data
            status_code: Mocked status code
            url: mocked url..
        """
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Return mocked data.
        Returns:
            Dict: return mocked data as dict.
        """
        return self.json_data
