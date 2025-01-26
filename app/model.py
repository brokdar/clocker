"""Module that contains all data models for the clocker application."""

from collections.abc import Sequence
from datetime import date, time, timedelta
from enum import StrEnum
from itertools import combinations
from typing import NamedTuple, Self

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel

from app.utils import timely


class CalendarEntryType(StrEnum):
    """The type of a calendar entry."""

    WORK = "work"
    FLEXTIME = "flextime"
    VACATION = "vacation"
    HOLIDAY = "holiday"
    SICK = "sick"


class TimeLogType(StrEnum):
    """The type of a time log."""

    WORK = "work"
    TRAVEL = "travel"


class TimeLogBase(SQLModel):
    """Base model of a time log."""

    type: TimeLogType
    start: time
    end: time | None = None
    pause: timedelta = timedelta(0)

    @model_validator(mode="after")
    def validate_log(self) -> Self:
        """Validates a time log.

        Raises:
            ValueError: on open-ended time logs that aren't of type work.
            ValueError: if start time is more advanced than end time.
            ValueError: if pause time exceeds the time log duration.

        Returns:
            Self: validated time log.
        """
        if self.end is None:
            if self.type != TimeLogType.WORK:
                raise ValueError(
                    f"Time logs of type '{self.type}' must have an end time. "
                    "Only work logs can be open-ended."
                )
            return self

        if self.start > self.end:
            raise ValueError(
                f"Invalid time range: Start time ({self.start:%H:%M}) is later than "
                f"end time ({self.end})"
            )

        delta = timely.delta(self.start, self.end)
        if self.pause > delta:
            raise ValueError(
                f"Invalid pause duration: Pause ({self.pause}) is longer than the total "
                f"time period ({self.start:%H:%M} - {self.end:%H:%M} = {delta})"
            )

        return self

    def __str__(self) -> str:  # pragma: no cover
        """Returns the string-representation."""
        return (
            f"type={self.type.capitalize()}, start={self.start}"
            f", end={self.end}, pause={self.pause}"
        )

    @property
    def duration(self) -> timedelta:
        """Returns the duration of the time log.

        Returns:
            timedelta: duration of the time log.
        """
        if self.end is None:
            return timedelta(0)

        delta = timely.delta(self.start, self.end)
        return delta - self.pause


class TimeLog(TimeLogBase, table=True):
    """Database model of time log."""

    __tablename__ = "time_log"

    id: int | None = Field(default=None, primary_key=True)
    day: date | None = Field(default=None, foreign_key="calendar_entry.day")


class TimeLogResponse(TimeLogBase):
    """Response model of a time log."""

    id: int


class TimeLogCreate(TimeLogBase):
    """Query model for creating a time log."""


class TimeLogUpdate(TimeLogBase):
    """Query model for updating a time log."""

    id: int | None = None


class CalendarEntryBase(SQLModel):
    """Base model of a calendar entry."""

    day: date = Field(primary_key=True)
    type: CalendarEntryType


class CalendarEntry(CalendarEntryBase, table=True):
    """Representation of calendar entry."""

    __tablename__ = "calendar_entry"

    logs: list[TimeLog] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )

    @field_validator("logs", check_fields=False)
    @classmethod
    def validate_logs(cls, logs: list[TimeLog]) -> list[TimeLog]:
        """Validates the time logs."""
        return validate_time_logs(logs)

    def __str__(self) -> str:  # pragma: no cover
        """Returns the string-representation."""
        logs = [f"({log})" for log in self.logs]
        return (
            f"date={self.day}, type={self.type.capitalize()}, logs=[{', '.join(logs)}]"
        )

    @property
    def duration(self) -> timedelta | None:
        """Returns the total duration of work logs on the calendar entry."""
        return calculate_duration(self.logs, self.type)

    @property
    def pause_time(self) -> timedelta | None:
        """Returns the total pause time of the calendar entry."""
        return calculate_pause_time(self.logs, self.type)


class CalendarEntryResponse(CalendarEntryBase):
    """Response model of a calendar entry."""

    logs: list[TimeLogResponse]

    @field_validator("logs", check_fields=False)
    @classmethod
    def validate_logs(cls, logs: list[TimeLog]) -> list[TimeLog]:
        """Validates the time logs."""
        return validate_time_logs(logs)

    @property
    def duration(self) -> timedelta | None:
        """Returns the total duration of the calendar entry."""
        return calculate_duration(self.logs, self.type)

    @property
    def pause_time(self) -> timedelta | None:
        """Returns the total pause time of the calendar entry."""
        return calculate_pause_time(self.logs, self.type)


class CalendarEntryCreate(CalendarEntryBase):
    """Query model for creating a calendar entry."""

    logs: list[TimeLogCreate] = []


class CalendarEntryUpdate(CalendarEntryBase):
    """Query model for updating a calendar entry."""

    logs: list[TimeLogUpdate] = []


class TimePair(NamedTuple):
    """Class that represents a time pair."""

    start: time
    end: time


def is_overlapping(left: TimePair, right: TimePair) -> bool:
    """Checks if two time pairs are overlapping."""
    return (
        (left.end > right.start and left.end < right.end)
        or (left.start > right.start and left.start < right.end)
        or (left.start <= right.start and left.end >= right.end)
    )


def validate_time_logs(logs: list[TimeLog]) -> list[TimeLog]:
    """Validates a list of time logs.

    - Checks for multiple open-ended time logs.
    - Checks for overlapping time logs.

    Args:
        logs (list[TimeLog]): time logs to check.

    Raises:
        ValueError: on multiple open-ended time logs.
        ValueError: on overlapping time logs.

    Returns:
        list[TimeLog]: sorted time logs.
    """
    if len(logs) == 1:
        return logs

    logs.sort(key=lambda x: x.start)
    for left, right in combinations(logs, 2):
        if left.end is None or right.end is None:
            raise ValueError(
                "Multiple open-ended time logs detected. Please set an end time for "
                f"the log starting at {left.start:%H:%M} or {right.start:%H:%M}"
            )

        if is_overlapping(
            TimePair(left.start, left.end), TimePair(right.start, right.end)
        ):
            raise ValueError(
                f"Time logs overlap: {left.start:%H:%M}-{left.end:%H:%M} overlaps with "
                f"{right.start:%H:%M}-{right.end:%H:%M}"
            )

    return logs


def calculate_duration(
    logs: Sequence[TimeLogBase], entry_type: CalendarEntryType
) -> timedelta | None:
    """Calculate the total duration of work logs for a calendar entry."""
    if entry_type != CalendarEntryType.WORK:
        return None

    total_duration = timedelta(0)
    for log in logs:
        if log.type == TimeLogType.WORK:
            total_duration += log.duration
    return total_duration


def calculate_pause_time(
    logs: Sequence[TimeLogBase], entry_type: CalendarEntryType
) -> timedelta | None:
    """Calculate the total pause time from a sequence of time logs.

    Args:
        logs (Sequence[TimeLogBase]): The sequence of time logs to calculate pause time from.
        entry_type (CalendarEntryType): The type of the calendar entry.

    Returns:
        timedelta | None: The total pause time for entries of type work, otherwise None.
    """
    if entry_type != CalendarEntryType.WORK:
        return None

    work_logs = [log for log in logs if log.type == TimeLogType.WORK]

    # Sum explicit pause times from logs
    total_pause_time = sum((log.pause for log in work_logs), start=timedelta(0))

    # Add gaps between work logs
    if len(work_logs) > 1:
        for i, current_log in enumerate(work_logs[1:]):
            previous_log = work_logs[i]
            if previous_log.end and previous_log.end != current_log.start:
                total_pause_time += timely.delta(previous_log.end, current_log.start)

    return total_pause_time
