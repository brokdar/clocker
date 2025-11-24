"""Test suite for entries API routes."""

from datetime import date, time, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.model import CalendarEntry, CalendarEntryType, TimeLog, TimeLogType
from app.routes.api.entries import (
    CalendarEntryCreate,
    CalendarEntryUpdate,
    TimeLogCreate,
    TimeLogUpdate,
    create_entry,
    copy_entry,
    delete_entry,
    get_entry,
    list_entries,
    update_entry,
)
from app.services.calendar import Calendar
from app.services.time_logger import TimeLogError


@pytest.fixture
def mock_calendar() -> AsyncMock:
    """Mock Calendar service for testing."""
    mock = AsyncMock(spec=Calendar)
    return mock


@pytest.fixture
def sample_date() -> date:
    """Provide sample date for testing."""
    return date(2024, 11, 15)


@pytest.fixture
def sample_work_entry(sample_date: date) -> CalendarEntry:
    """Provide sample work entry with time logs."""
    return CalendarEntry(
        day=sample_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                id=1,
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(17, 0),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def sample_vacation_entry(sample_date: date) -> CalendarEntry:
    """Provide sample vacation entry without logs."""
    return CalendarEntry(
        day=sample_date,
        type=CalendarEntryType.VACATION,
        logs=[],
    )


class TestListEntries:
    """Test suite for list_entries endpoint."""

    @pytest.mark.asyncio
    async def test_lists_entries_with_default_params(
        self, mock_calendar: AsyncMock
    ) -> None:
        """Test listing entries with default year and month."""
        today = date.today()
        test_date = date(today.year, today.month, 15)
        entry = CalendarEntry(day=test_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar.get_month.return_value = {test_date: entry}

        result = await list_entries(
            year=today.year, month=today.month, calendar=mock_calendar
        )

        assert len(result) == 1
        assert result[0].day == test_date
        mock_calendar.get_month.assert_called_once_with(today.year, today.month)

    @pytest.mark.asyncio
    async def test_lists_entries_with_specific_year_and_month(
        self, mock_calendar: AsyncMock
    ) -> None:
        """Test listing entries for specific year and month."""
        test_date = date(2023, 5, 10)
        entry = CalendarEntry(day=test_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar.get_month.return_value = {test_date: entry}

        result = await list_entries(year=2023, month=5, calendar=mock_calendar)

        assert len(result) == 1
        assert result[0].day == test_date
        mock_calendar.get_month.assert_called_once_with(2023, 5)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_entries(
        self, mock_calendar: AsyncMock
    ) -> None:
        """Test empty list returned when no entries exist."""
        today = date.today()
        mock_calendar.get_month.return_value = {}

        result = await list_entries(
            year=today.year, month=today.month, calendar=mock_calendar
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_lists_multiple_entries(self, mock_calendar: AsyncMock) -> None:
        """Test listing multiple entries for a month."""
        entries = {
            date(2024, 1, 10): CalendarEntry(
                day=date(2024, 1, 10), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 1, 15): CalendarEntry(
                day=date(2024, 1, 15), type=CalendarEntryType.VACATION, logs=[]
            ),
            date(2024, 1, 20): CalendarEntry(
                day=date(2024, 1, 20), type=CalendarEntryType.SICK, logs=[]
            ),
        }
        mock_calendar.get_month.return_value = entries

        result = await list_entries(year=2024, month=1, calendar=mock_calendar)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_raises_500_when_calendar_service_fails(
        self, mock_calendar: AsyncMock
    ) -> None:
        """Test HTTP 500 raised when calendar service throws exception."""
        today = date.today()
        mock_calendar.get_month.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await list_entries(
                year=today.year, month=today.month, calendar=mock_calendar
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "year,month",
        [
            (2000, 1),
            (2024, 12),
            (2025, 2),
            (9999, 6),
        ],
        ids=[
            "year_2000_january",
            "year_2024_december",
            "year_2025_february",
            "year_9999_june",
        ],
    )
    async def test_handles_boundary_years_and_months(
        self, mock_calendar: AsyncMock, year: int, month: int
    ) -> None:
        """Test handling of boundary year and month values."""
        mock_calendar.get_month.return_value = {}

        result = await list_entries(year=year, month=month, calendar=mock_calendar)

        assert result == []
        mock_calendar.get_month.assert_called_once_with(year, month)


class TestGetEntry:
    """Test suite for get_entry endpoint."""

    @pytest.mark.asyncio
    async def test_retrieves_existing_entry(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry
    ) -> None:
        """Test retrieving existing calendar entry."""
        mock_calendar.get_by_date.return_value = sample_work_entry

        result = await get_entry(date=sample_work_entry.day, calendar=mock_calendar)

        assert result.day == sample_work_entry.day
        assert result.type == CalendarEntryType.WORK
        assert len(result.logs) == 1
        mock_calendar.get_by_date.assert_called_once_with(sample_work_entry.day)

    @pytest.mark.asyncio
    async def test_retrieves_entry_with_no_logs(
        self, mock_calendar: AsyncMock, sample_vacation_entry: CalendarEntry
    ) -> None:
        """Test retrieving entry with empty logs list."""
        mock_calendar.get_by_date.return_value = sample_vacation_entry

        result = await get_entry(date=sample_vacation_entry.day, calendar=mock_calendar)

        assert result.day == sample_vacation_entry.day
        assert result.type == CalendarEntryType.VACATION
        assert len(result.logs) == 0

    @pytest.mark.asyncio
    async def test_raises_404_when_entry_not_found(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 404 raised when entry doesn't exist."""
        mock_calendar.get_by_date.return_value = None

        with pytest.raises(Exception, match=f"No entry found for day {sample_date}"):
            await get_entry(date=sample_date, calendar=mock_calendar)

    @pytest.mark.asyncio
    async def test_retrieves_entry_with_multiple_logs(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test retrieving entry with multiple time logs."""
        entry = CalendarEntry(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    id=1,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(12, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    id=2,
                    type=TimeLogType.WORK,
                    start=time(13, 0),
                    end=time(17, 0),
                    pause=timedelta(minutes=15),
                ),
            ],
        )
        mock_calendar.get_by_date.return_value = entry

        result = await get_entry(date=sample_date, calendar=mock_calendar)

        assert len(result.logs) == 2
        assert result.logs[0].id == 1
        assert result.logs[1].id == 2


class TestCreateEntry:
    """Test suite for create_entry endpoint."""

    @pytest.mark.asyncio
    async def test_creates_work_entry_with_no_logs(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test creating work entry without time logs."""
        mock_calendar.get_by_date.return_value = None
        new_entry = CalendarEntry(day=sample_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar.create_entry.return_value = new_entry
        mock_calendar.update_entry.return_value = new_entry

        data = CalendarEntryCreate(
            day=sample_date, type=CalendarEntryType.WORK, logs=[]
        )
        result = await create_entry(date=sample_date, data=data, calendar=mock_calendar)

        assert result.day == sample_date
        assert result.type == CalendarEntryType.WORK
        assert len(result.logs) == 0
        mock_calendar.create_entry.assert_called_once_with(
            sample_date, CalendarEntryType.WORK
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "entry_type",
        [
            CalendarEntryType.VACATION,
            CalendarEntryType.FLEXTIME,
            CalendarEntryType.SICK,
            CalendarEntryType.HOLIDAY,
        ],
        ids=["vacation", "flextime", "sick", "holiday"],
    )
    async def test_creates_non_work_entries(
        self, mock_calendar: AsyncMock, sample_date: date, entry_type: CalendarEntryType
    ) -> None:
        """Test creating non-work entry types."""
        mock_calendar.get_by_date.return_value = None
        new_entry = CalendarEntry(day=sample_date, type=entry_type, logs=[])
        mock_calendar.create_entry.return_value = new_entry
        mock_calendar.update_entry.return_value = new_entry

        data = CalendarEntryCreate(day=sample_date, type=entry_type, logs=[])
        result = await create_entry(date=sample_date, data=data, calendar=mock_calendar)

        assert result.type == entry_type
        assert len(result.logs) == 0

    @pytest.mark.asyncio
    async def test_raises_409_when_entry_already_exists(
        self,
        mock_calendar: AsyncMock,
        sample_date: date,
        sample_work_entry: CalendarEntry,
    ) -> None:
        """Test HTTP 409 raised when entry already exists."""
        mock_calendar.get_by_date.return_value = sample_work_entry

        data = CalendarEntryCreate(
            day=sample_date, type=CalendarEntryType.WORK, logs=[]
        )

        with pytest.raises(
            Exception, match=f"Entry already exists for date {sample_date}"
        ):
            await create_entry(date=sample_date, data=data, calendar=mock_calendar)

    @pytest.mark.asyncio
    async def test_raises_400_when_time_log_validation_fails(
        self, mock_calendar: AsyncMock, sample_date: date, mocker: Any
    ) -> None:
        """Test HTTP 400 raised and entry removed on TimeLogError."""
        mock_calendar.get_by_date.return_value = None
        new_entry = CalendarEntry(day=sample_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar.create_entry.return_value = new_entry

        mocker.patch(
            "app.routes.api.entries.time_logger.add_time_log",
            side_effect=TimeLogError("Invalid time log data"),
        )

        data = CalendarEntryCreate(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLogCreate(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )

        with pytest.raises(Exception, match="Invalid time log data"):
            await create_entry(date=sample_date, data=data, calendar=mock_calendar)

        mock_calendar.remove_entry.assert_called_once_with(sample_date)


class TestUpdateEntry:
    """Test suite for update_entry endpoint."""

    @pytest.mark.asyncio
    async def test_raises_404_when_entry_not_found(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 404 raised when entry doesn't exist."""
        mock_calendar.get_by_date.return_value = None

        data = CalendarEntryUpdate(
            day=sample_date, type=CalendarEntryType.WORK, logs=[]
        )

        with pytest.raises(Exception, match=f"No entry found for date {sample_date}"):
            await update_entry(date=sample_date, data=data, calendar=mock_calendar)

    @pytest.mark.asyncio
    async def test_changes_work_to_vacation_and_clears_logs(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry
    ) -> None:
        """Test changing entry type from WORK to VACATION clears logs."""
        mock_calendar.get_by_date.return_value = sample_work_entry
        updated_entry = CalendarEntry(
            day=sample_work_entry.day, type=CalendarEntryType.VACATION, logs=[]
        )
        mock_calendar.update_entry.return_value = updated_entry

        data = CalendarEntryUpdate(
            day=sample_work_entry.day, type=CalendarEntryType.VACATION, logs=[]
        )
        result = await update_entry(
            date=sample_work_entry.day, data=data, calendar=mock_calendar
        )

        assert result.type == CalendarEntryType.VACATION
        assert len(result.logs) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "new_type",
        [
            CalendarEntryType.VACATION,
            CalendarEntryType.FLEXTIME,
            CalendarEntryType.SICK,
            CalendarEntryType.HOLIDAY,
        ],
        ids=["to_vacation", "to_flextime", "to_sick", "to_holiday"],
    )
    async def test_changes_work_to_other_types_clears_logs(
        self,
        mock_calendar: AsyncMock,
        sample_work_entry: CalendarEntry,
        new_type: CalendarEntryType,
    ) -> None:
        """Test changing from WORK to other types clears logs."""
        mock_calendar.get_by_date.return_value = sample_work_entry
        updated_entry = CalendarEntry(day=sample_work_entry.day, type=new_type, logs=[])
        mock_calendar.update_entry.return_value = updated_entry

        data = CalendarEntryUpdate(day=sample_work_entry.day, type=new_type, logs=[])
        result = await update_entry(
            date=sample_work_entry.day, data=data, calendar=mock_calendar
        )

        assert result.type == new_type
        assert len(result.logs) == 0

    @pytest.mark.asyncio
    async def test_adds_new_time_log_to_entry(
        self, mock_calendar: AsyncMock, sample_date: date, mocker: Any
    ) -> None:
        """Test adding new time log to existing entry."""
        entry = CalendarEntry(day=sample_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar.get_by_date.return_value = entry

        new_log = TimeLog(
            id=1,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
            pause=timedelta(0),
        )
        entry_with_log = CalendarEntry(
            day=sample_date, type=CalendarEntryType.WORK, logs=[new_log]
        )
        mock_calendar.update_entry.return_value = entry_with_log

        mock_add = mocker.patch("app.routes.api.entries.time_logger.add_time_log")

        data = CalendarEntryUpdate(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLogUpdate(
                    id=None,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        await update_entry(date=sample_date, data=data, calendar=mock_calendar)

        mock_add.assert_called_once()
        mock_calendar.update_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_time_log(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry, mocker: Any
    ) -> None:
        """Test updating existing time log."""
        mock_calendar.get_by_date.return_value = sample_work_entry
        mock_calendar.update_entry.return_value = sample_work_entry

        mock_update = mocker.patch("app.routes.api.entries.time_logger.update_time_log")

        data = CalendarEntryUpdate(
            day=sample_work_entry.day,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLogUpdate(
                    id=1,
                    type=TimeLogType.WORK,
                    start=time(10, 0),
                    end=time(18, 0),
                    pause=timedelta(minutes=45),
                )
            ],
        )
        await update_entry(
            date=sample_work_entry.day, data=data, calendar=mock_calendar
        )

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_removes_time_log_from_entry(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry
    ) -> None:
        """Test removing time log from entry."""
        mock_calendar.get_by_date.return_value = sample_work_entry
        updated_entry = CalendarEntry(
            day=sample_work_entry.day, type=CalendarEntryType.WORK, logs=[]
        )
        mock_calendar.update_entry.return_value = updated_entry

        data = CalendarEntryUpdate(
            day=sample_work_entry.day, type=CalendarEntryType.WORK, logs=[]
        )
        result = await update_entry(
            date=sample_work_entry.day, data=data, calendar=mock_calendar
        )

        assert len(result.logs) == 0

    @pytest.mark.asyncio
    async def test_removes_one_log_and_modifies_another(
        self, mock_calendar: AsyncMock, sample_date: date, mocker: Any
    ) -> None:
        """Test removing one log while modifying another in same request."""
        entry = CalendarEntry(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    id=1,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(12, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    id=2,
                    type=TimeLogType.WORK,
                    start=time(13, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        mock_calendar.get_by_date.return_value = entry
        mock_calendar.update_entry.return_value = entry

        mock_update = mocker.patch("app.routes.api.entries.time_logger.update_time_log")

        data = CalendarEntryUpdate(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLogUpdate(
                    id=1,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        await update_entry(date=sample_date, data=data, calendar=mock_calendar)

        assert len(entry.logs) == 1
        assert entry.logs[0].id == 1
        mock_update.assert_called_once()
        mock_calendar.update_entry.assert_called_once_with(entry)

    @pytest.mark.asyncio
    async def test_raises_400_and_resets_on_time_log_error(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry, mocker: Any
    ) -> None:
        """Test HTTP 400 raised and entry reset on TimeLogError."""
        mock_calendar.get_by_date.return_value = sample_work_entry
        mock_calendar.reset_entry.return_value = sample_work_entry

        mocker.patch(
            "app.routes.api.entries.time_logger.add_time_log",
            side_effect=TimeLogError("Overlapping time logs"),
        )

        data = CalendarEntryUpdate(
            day=sample_work_entry.day,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLogUpdate(
                    id=None,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )

        with pytest.raises(Exception, match="Overlapping time logs"):
            await update_entry(
                date=sample_work_entry.day, data=data, calendar=mock_calendar
            )

        mock_calendar.reset_entry.assert_called_once()


class TestCopyEntry:
    """Test suite for copy_entry endpoint."""

    @pytest.mark.asyncio
    async def test_raises_404_when_source_not_found(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 404 raised when source entry doesn't exist."""
        mock_calendar.get_by_date.return_value = None
        target_date = date(2024, 11, 20)

        with pytest.raises(
            Exception, match=f"No entry found for source date {sample_date}"
        ):
            await copy_entry(
                target_date=target_date, source_date=sample_date, calendar=mock_calendar
            )

    @pytest.mark.asyncio
    async def test_copies_work_entry_with_logs(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry, mocker: Any
    ) -> None:
        """Test copying work entry with time logs."""
        target_date = date(2024, 11, 20)
        target_entry = CalendarEntry(
            day=target_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    id=2,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(minutes=30),
                )
            ],
        )

        mock_calendar.get_by_date.return_value = sample_work_entry
        mock_calendar.create_entry.return_value = target_entry
        mock_calendar.update_entry.return_value = target_entry

        mock_add = mocker.patch("app.routes.api.entries.time_logger.add_time_log")

        result = await copy_entry(
            target_date=target_date,
            source_date=sample_work_entry.day,
            calendar=mock_calendar,
        )

        assert result.day == target_date
        assert result.type == CalendarEntryType.WORK
        mock_add.assert_called_once()
        mock_calendar.create_entry.assert_called_once_with(
            target_date, CalendarEntryType.WORK
        )

    @pytest.mark.asyncio
    async def test_copies_vacation_entry_without_logs(
        self, mock_calendar: AsyncMock, sample_vacation_entry: CalendarEntry
    ) -> None:
        """Test copying vacation entry without logs."""
        target_date = date(2024, 11, 20)
        target_entry = CalendarEntry(
            day=target_date, type=CalendarEntryType.VACATION, logs=[]
        )

        mock_calendar.get_by_date.return_value = sample_vacation_entry
        mock_calendar.create_entry.return_value = target_entry
        mock_calendar.update_entry.return_value = target_entry

        result = await copy_entry(
            target_date=target_date,
            source_date=sample_vacation_entry.day,
            calendar=mock_calendar,
        )

        assert result.day == target_date
        assert result.type == CalendarEntryType.VACATION
        assert len(result.logs) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "entry_type",
        [
            CalendarEntryType.FLEXTIME,
            CalendarEntryType.SICK,
            CalendarEntryType.HOLIDAY,
        ],
        ids=["flextime", "sick", "holiday"],
    )
    async def test_copies_various_entry_types(
        self, mock_calendar: AsyncMock, sample_date: date, entry_type: CalendarEntryType
    ) -> None:
        """Test copying various entry types."""
        source_entry = CalendarEntry(day=sample_date, type=entry_type, logs=[])
        target_date = date(2024, 11, 20)
        target_entry = CalendarEntry(day=target_date, type=entry_type, logs=[])

        mock_calendar.get_by_date.return_value = source_entry
        mock_calendar.create_entry.return_value = target_entry
        mock_calendar.update_entry.return_value = target_entry

        result = await copy_entry(
            target_date=target_date, source_date=sample_date, calendar=mock_calendar
        )

        assert result.type == entry_type

    @pytest.mark.asyncio
    async def test_raises_400_on_value_error(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry
    ) -> None:
        """Test HTTP 400 raised when ValueError occurs during copy."""
        target_date = date(2024, 11, 23)
        mock_calendar.get_by_date.return_value = sample_work_entry
        mock_calendar.create_entry.side_effect = ValueError(
            "Cannot create work entry on weekend"
        )

        with pytest.raises(Exception, match="Cannot create work entry on weekend"):
            await copy_entry(
                target_date=target_date,
                source_date=sample_work_entry.day,
                calendar=mock_calendar,
            )

    @pytest.mark.asyncio
    async def test_raises_500_on_unexpected_exception(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 500 raised on unexpected exception."""
        mock_calendar.get_by_date.side_effect = Exception("Unexpected error")
        target_date = date(2024, 11, 20)

        with pytest.raises(Exception, match="Unexpected error"):
            await copy_entry(
                target_date=target_date, source_date=sample_date, calendar=mock_calendar
            )


class TestDeleteEntry:
    """Test suite for delete_entry endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_existing_entry(
        self, mock_calendar: AsyncMock, sample_work_entry: CalendarEntry
    ) -> None:
        """Test deleting existing calendar entry."""
        mock_calendar.remove_entry.return_value = sample_work_entry

        result = await delete_entry(date=sample_work_entry.day, calendar=mock_calendar)

        assert result.day == sample_work_entry.day
        assert result.type == CalendarEntryType.WORK
        mock_calendar.remove_entry.assert_called_once_with(sample_work_entry.day)

    @pytest.mark.asyncio
    async def test_raises_404_when_entry_not_found(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 404 raised when entry doesn't exist."""
        mock_calendar.remove_entry.side_effect = ValueError(
            f"Entry does not exist for {sample_date}"
        )

        with pytest.raises(Exception, match=f"Entry does not exist for {sample_date}"):
            await delete_entry(date=sample_date, calendar=mock_calendar)

    @pytest.mark.asyncio
    async def test_deletes_entry_with_no_logs(
        self, mock_calendar: AsyncMock, sample_vacation_entry: CalendarEntry
    ) -> None:
        """Test deleting entry with empty logs list."""
        mock_calendar.remove_entry.return_value = sample_vacation_entry

        result = await delete_entry(
            date=sample_vacation_entry.day, calendar=mock_calendar
        )

        assert len(result.logs) == 0
        assert result.type == CalendarEntryType.VACATION

    @pytest.mark.asyncio
    async def test_deletes_entry_with_multiple_logs(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test deleting entry with multiple time logs."""
        entry = CalendarEntry(
            day=sample_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    id=1,
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(12, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    id=2,
                    type=TimeLogType.WORK,
                    start=time(13, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        mock_calendar.remove_entry.return_value = entry

        result = await delete_entry(date=sample_date, calendar=mock_calendar)

        assert len(result.logs) == 2

    @pytest.mark.asyncio
    async def test_raises_500_on_unexpected_exception(
        self, mock_calendar: AsyncMock, sample_date: date
    ) -> None:
        """Test HTTP 500 raised on unexpected exception."""
        mock_calendar.remove_entry.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await delete_entry(date=sample_date, calendar=mock_calendar)
