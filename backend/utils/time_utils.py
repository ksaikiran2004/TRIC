"""
TRIC - Time Utilities

FILE: backend/utils/time_utils.py

Responsibility:
Provide standardized time-related utility functions.
"""

import time
from typing import Optional


def current_timestamp() -> float:
    """
    Get the current system timestamp.

    Returns:
        Current time in seconds (float)
    """
    return time.time()


def time_diff(t1: float, t2: float) -> float:
    """
    Compute absolute time difference between two timestamps.

    Args:
        t1: Timestamp 1
        t2: Timestamp 2

    Returns:
        Non-negative time difference
    """
    return abs(t1 - t2)


def is_expired(
    timestamp: float,
    max_age: float,
    current_time: Optional[float] = None
) -> bool:
    """
    Check if a timestamp is expired based on max_age.

    Args:
        timestamp: Original timestamp
        max_age: Maximum allowed age (seconds)
        current_time: Optional current time override

    Returns:
        True if expired, else False
    """
    now = current_time if current_time is not None else current_timestamp()
    return (now - timestamp) > max_age