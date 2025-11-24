import logging
from datetime import time, timedelta

from pydantic import ValidationError

from app.model import (
    CalendarEntry,
    CalendarEntryType,
    TimeLog,
    TimeLogType,
    validate_time_logs,
)

logger = logging.getLogger(__name__)


class TimeLogError(Exception):
    """Raised when time logging operations fail."""


def _validate_index(entry: CalendarEntry, index: int) -> None:
    """Validates if the given index is valid for the entry's time logs.

    Args:
        entry (CalendarEntry): The calendar entry to check
        index (int): The index to validate

    Raises:
        TimeLogError: If the index is invalid
    """
    if not entry.logs:
        raise TimeLogError(
            f"No time logs found for {entry.day}. Cannot access index {index}."
        )

    if index >= len(entry.logs):
        raise TimeLogError(
            f"Invalid log index {index} - only {len(entry.logs)} logs exist for {entry.day}."
        )


def add_time_log(
    entry: CalendarEntry,
    type: TimeLogType,
    start: time,
    end: time | None = None,
    pause: timedelta = timedelta(0),
) -> None:
    """Adds a new time log to the calendar entry.

    Args:
        entry (CalendarEntry): The calendar entry to add the log to
        type (TimeLogType): The type of time log
        start (time): Start time
        end (time | None, optional): End time. Defaults to None.
        pause (timedelta, optional): Pause duration. Defaults to timedelta(0).

    Raises:
        TimeLogError: If the entry type is not work or if the time log is invalid
    """
    if entry.type != CalendarEntryType.WORK:
        raise TimeLogError(
            f"Cannot add time log to {entry.type} entry. Only work entries accept time logs."
        )

    try:
        log = TimeLog(type=type, start=start, end=end, pause=pause)
        entry.logs.append(log)
        validate_time_logs(entry.logs)
        logger.info(f"Added time log to {entry.day}: {log}")
    except (ValueError, ValidationError) as e:
        raise TimeLogError(f"Invalid time log data: {str(e)}") from e


def update_time_log(
    entry: CalendarEntry,
    log_index: int,
    type: TimeLogType | None = None,
    start: time | None = None,
    end: time | None = None,
    pause: timedelta | None = None,
) -> None:
    """Updates an existing time log in the calendar entry.

    Args:
        entry (CalendarEntry): The calendar entry containing the log
        log_index (int): Index of the log to update
        type (TimeLogType | None, optional): New time log type. Defaults to None.
        start (time | None, optional): New start time. Defaults to None.
        end (time | None, optional): New end time. Defaults to None.
        pause (timedelta | None, optional): New pause duration. Defaults to None.

    Raises:
        TimeLogError: If the index is invalid or if the updated log would be invalid
    """
    _validate_index(entry, log_index)

    try:
        log = entry.logs[log_index]
        log.type = type or log.type
        log.start = start or log.start
        log.end = end or log.end
        log.pause = pause or log.pause

        validate_time_logs(entry.logs)
        logger.info(f"Updated time log [{log_index}] for {entry.day}: {log}")
    except (ValueError, ValidationError) as e:
        raise TimeLogError(f"Invalid time log update: {str(e)}") from e


def remove_time_log(entry: CalendarEntry, log_index: int) -> None:
    """Removes a time log from the calendar entry.

    Args:
        entry (CalendarEntry): The calendar entry containing the log
        log_index (int): Index of the log to remove

    Raises:
        TimeLogError: If the index is invalid
    """
    _validate_index(entry, log_index)

    try:
        log = entry.logs[log_index]
        entry.logs.remove(log)
        validate_time_logs(entry.logs)
        logger.info(f"Removed time log [{log_index}] from {entry.day}: {log}")
    except (ValueError, ValidationError) as e:
        raise TimeLogError(f"Cannot remove time log: {str(e)}") from e
