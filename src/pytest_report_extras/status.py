from enum import StrEnum


class Status(StrEnum):
    """
    Enum to hold test execution status.
    """

    UNKNOWN = "unknown"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAILED = "xfailed"
    XPASSED = "xpassed"
    ERROR = "error"
