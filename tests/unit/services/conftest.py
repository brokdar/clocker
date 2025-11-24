"""Shared fixtures for service layer tests."""

from datetime import date, time, timedelta
from unittest.mock import AsyncMock

import pytest

from app.database import CalendarRepository
from app.model import CalendarEntry, CalendarEntryType, TimeLog, TimeLogType
from app.services.statistics import StatisticsConfiguration


@pytest.fixture
def weekday_date() -> date:
    """Provide a Monday date for testing."""
    return date(2024, 11, 18)


@pytest.fixture
def weekend_date() -> date:
    """Provide a Saturday date for testing."""
    return date(2024, 11, 23)


@pytest.fixture
def friday_date() -> date:
    """Provide a Friday date for testing."""
    return date(2024, 11, 22)


@pytest.fixture
def work_entry_empty(weekday_date: date) -> CalendarEntry:
    """Provide work entry with no logs."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[],
    )


@pytest.fixture
def work_entry_standard(weekday_date: date) -> CalendarEntry:
    """Provide work entry with standard 8-hour log."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(17, 30),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def work_entry_multiple_logs(weekday_date: date) -> CalendarEntry:
    """Provide work entry with multiple logs."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(12, 0),
                pause=timedelta(0),
            ),
            TimeLog(
                type=TimeLogType.WORK,
                start=time(13, 0),
                end=time(17, 0),
                pause=timedelta(minutes=15),
            ),
        ],
    )


@pytest.fixture
def work_entry_open_ended(weekday_date: date) -> CalendarEntry:
    """Provide work entry with open-ended log."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=None,
                pause=timedelta(0),
            )
        ],
    )


@pytest.fixture
def work_entry_overtime(weekday_date: date) -> CalendarEntry:
    """Provide work entry with overtime (10+ hours)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(8, 0),
                end=time(19, 0),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def vacation_entry(weekday_date: date) -> CalendarEntry:
    """Provide vacation entry (cannot have logs)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.VACATION,
        logs=[],
    )


@pytest.fixture
def holiday_entry(weekday_date: date) -> CalendarEntry:
    """Provide holiday entry."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.HOLIDAY,
        logs=[],
    )


@pytest.fixture
def sick_entry(weekday_date: date) -> CalendarEntry:
    """Provide sick entry."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.SICK,
        logs=[],
    )


@pytest.fixture
def flextime_entry(weekday_date: date) -> CalendarEntry:
    """Provide flextime entry."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.FLEXTIME,
        logs=[],
    )


@pytest.fixture
def standard_work_log() -> TimeLog:
    """Provide standard 9-5 work log with 30min break."""
    return TimeLog(
        type=TimeLogType.WORK,
        start=time(9, 0),
        end=time(17, 0),
        pause=timedelta(minutes=30),
    )


@pytest.fixture
def travel_log() -> TimeLog:
    """Provide travel log."""
    return TimeLog(
        type=TimeLogType.TRAVEL,
        start=time(8, 0),
        end=time(9, 0),
        pause=timedelta(0),
    )


@pytest.fixture
def mock_calendar_repository() -> AsyncMock:
    """Provide mocked CalendarRepository for testing."""
    mock = AsyncMock(spec=CalendarRepository)
    return mock


@pytest.fixture
def default_statistics_config() -> StatisticsConfiguration:
    """Provide default statistics configuration."""
    return StatisticsConfiguration()


@pytest.fixture
def custom_statistics_config() -> StatisticsConfiguration:
    """Provide custom statistics configuration for testing."""
    return StatisticsConfiguration(
        standard_work_hours=timedelta(hours=7, minutes=30),
        max_work_hours=timedelta(hours=9),
        min_rest_period=timedelta(hours=12),
    )
