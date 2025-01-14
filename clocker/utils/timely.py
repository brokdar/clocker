"""Service that handles time objects."""

from datetime import datetime, time, timedelta


def delta(start: time, end: time) -> timedelta:
    """Returns the time delta between the start and end time.

    Args:
        start (time): start time.
        end (time): end time.

    Returns:
        timedelta: time delta.
    """
    today = datetime.today()
    return datetime.combine(today, end) - datetime.combine(today, start)
