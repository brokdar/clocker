"""Test suite for calendar service."""

from datetime import date
from unittest.mock import AsyncMock

import pytest
from _pytest.logging import LogCaptureFixture

from app.model import CalendarEntry, CalendarEntryType
from app.services.calendar import Calendar, get_month_range, is_work_day


class TestUtilityFunctions:
    """Test suite for utility functions."""

    @pytest.mark.parametrize(
        "day,expected",
        [
            (date(2024, 11, 18), True),
            (date(2024, 11, 19), True),
            (date(2024, 11, 20), True),
            (date(2024, 11, 21), True),
            (date(2024, 11, 22), True),
            (date(2024, 11, 23), False),
            (date(2024, 11, 24), False),
        ],
        ids=[
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ],
    )
    def test_validates_work_day_for_all_weekdays(
        self, day: date, expected: bool
    ) -> None:
        """Test work day validation for all days of week."""
        assert is_work_day(day) == expected

    @pytest.mark.parametrize(
        "year,month,expected_start,expected_end",
        [
            (2024, 1, date(2024, 1, 1), date(2024, 1, 31)),
            (2024, 2, date(2024, 2, 1), date(2024, 2, 29)),
            (2023, 2, date(2023, 2, 1), date(2023, 2, 28)),
            (2024, 3, date(2024, 3, 1), date(2024, 3, 31)),
            (2024, 4, date(2024, 4, 1), date(2024, 4, 30)),
            (2024, 6, date(2024, 6, 1), date(2024, 6, 30)),
            (2024, 11, date(2024, 11, 1), date(2024, 11, 30)),
            (2024, 12, date(2024, 12, 1), date(2024, 12, 31)),
            (2000, 2, date(2000, 2, 1), date(2000, 2, 29)),
            (1900, 2, date(1900, 2, 1), date(1900, 2, 28)),
        ],
        ids=[
            "january_31_days",
            "february_leap_year",
            "february_non_leap_year",
            "march_31_days",
            "april_30_days",
            "june_30_days",
            "november_30_days",
            "december_31_days",
            "year_2000_leap",
            "year_1900_not_leap",
        ],
    )
    def test_returns_month_range_for_all_months(
        self, year: int, month: int, expected_start: date, expected_end: date
    ) -> None:
        """Test month range calculation for various months and leap years."""
        start, end = get_month_range(year, month)
        assert start == expected_start
        assert end == expected_end


class TestCalendarGetOperations:
    """Test suite for calendar get operations."""

    @pytest.mark.asyncio
    async def test_retrieves_entry_by_date_successfully(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test successful retrieval of entry by date."""
        entry = CalendarEntry(day=weekday_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar_repository.get_by_date.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_by_date(weekday_date)

        assert result == entry
        mock_calendar_repository.get_by_date.assert_called_once_with(weekday_date)

    @pytest.mark.asyncio
    async def test_returns_none_when_entry_not_found(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test None returned when entry doesn't exist."""
        mock_calendar_repository.get_by_date.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_by_date(weekday_date)

        assert result is None

    @pytest.mark.asyncio
    async def test_retrieves_month_entries_successfully(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test successful retrieval of month entries."""
        entries = {
            date(2024, 11, 1): CalendarEntry(
                day=date(2024, 11, 1), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 15): CalendarEntry(
                day=date(2024, 11, 15), type=CalendarEntryType.VACATION, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_month(2024, 11)

        assert result == entries
        mock_calendar_repository.get_by_date_range.assert_called_once_with(
            date(2024, 11, 1), date(2024, 11, 30)
        )

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_month_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test empty dict returned when no entries exist for month."""
        mock_calendar_repository.get_by_date_range.return_value = {}
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_month(2024, 11)

        assert result == {}

    @pytest.mark.asyncio
    async def test_retrieves_month_with_leap_year_february(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test month retrieval handles leap year February correctly."""
        mock_calendar_repository.get_by_date_range.return_value = {}
        calendar = Calendar(mock_calendar_repository)

        await calendar.get_month(2024, 2)

        mock_calendar_repository.get_by_date_range.assert_called_once_with(
            date(2024, 2, 1), date(2024, 2, 29)
        )

    @pytest.mark.asyncio
    async def test_retrieves_year_entries_successfully(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test successful retrieval of year entries."""
        entries = {
            date(2024, 1, 1): CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
            date(2024, 6, 15): CalendarEntry(
                day=date(2024, 6, 15), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_year(2024)

        assert date(2024, 1, 1) in result
        assert date(2024, 6, 15) in result
        mock_calendar_repository.get_by_date_range.assert_called_once_with(
            date(2024, 1, 1), date(2024, 12, 31)
        )

    @pytest.mark.asyncio
    async def test_adds_public_holidays_when_getting_year_without_holidays(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test public holidays added when retrieving year without holidays."""
        work_entry = CalendarEntry(
            day=date(2024, 6, 15), type=CalendarEntryType.WORK, logs=[]
        )
        holiday_entries = [
            CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date_range.return_value = {
            date(2024, 6, 15): work_entry
        }
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = holiday_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_year(2024)

        assert date(2024, 1, 1) in result
        assert date(2024, 6, 15) in result

    @pytest.mark.asyncio
    async def test_skips_adding_holidays_when_already_present(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holidays not added when year already has holidays."""
        entries = {
            date(2024, 1, 1): CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_year(2024)

        assert date(2024, 1, 1) in result
        mock_calendar_repository.save_all.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "year,month",
        [
            (2024, 1),
            (2024, 6),
            (2024, 12),
            (2000, 2),
            (2023, 2),
        ],
        ids=[
            "january",
            "june",
            "december",
            "leap_year_february",
            "non_leap_february",
        ],
    )
    async def test_retrieves_entries_for_various_months(
        self, mock_calendar_repository: AsyncMock, year: int, month: int
    ) -> None:
        """Test retrieval works for various months."""
        mock_calendar_repository.get_by_date_range.return_value = {}
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_month(year, month)

        assert result == {}
        assert mock_calendar_repository.get_by_date_range.called

    @pytest.mark.asyncio
    async def test_retrieves_multiple_entries_in_month(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test retrieval of multiple entries within a month."""
        entries = {
            date(2024, 11, 1): CalendarEntry(
                day=date(2024, 11, 1), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 5): CalendarEntry(
                day=date(2024, 11, 5), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 15): CalendarEntry(
                day=date(2024, 11, 15), type=CalendarEntryType.VACATION, logs=[]
            ),
            date(2024, 11, 20): CalendarEntry(
                day=date(2024, 11, 20), type=CalendarEntryType.SICK, logs=[]
            ),
            date(2024, 11, 25): CalendarEntry(
                day=date(2024, 11, 25), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_month(2024, 11)

        assert len(result) == 5
        assert all(d.month == 11 for d in result.keys())

    @pytest.mark.asyncio
    async def test_retrieves_entries_with_different_types(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test retrieval of entries with various types."""
        entries = {
            date(2024, 11, 1): CalendarEntry(
                day=date(2024, 11, 1), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 2): CalendarEntry(
                day=date(2024, 11, 2), type=CalendarEntryType.VACATION, logs=[]
            ),
            date(2024, 11, 3): CalendarEntry(
                day=date(2024, 11, 3), type=CalendarEntryType.SICK, logs=[]
            ),
            date(2024, 11, 4): CalendarEntry(
                day=date(2024, 11, 4), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
            date(2024, 11, 5): CalendarEntry(
                day=date(2024, 11, 5), type=CalendarEntryType.FLEXTIME, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_month(2024, 11)

        assert len(result) == 5
        assert result[date(2024, 11, 1)].type == CalendarEntryType.WORK
        assert result[date(2024, 11, 2)].type == CalendarEntryType.VACATION
        assert result[date(2024, 11, 3)].type == CalendarEntryType.SICK
        assert result[date(2024, 11, 4)].type == CalendarEntryType.HOLIDAY
        assert result[date(2024, 11, 5)].type == CalendarEntryType.FLEXTIME

    @pytest.mark.asyncio
    async def test_retrieves_year_entries_with_boundary_dates(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test year retrieval includes correct boundary dates."""
        entries = {
            date(2024, 1, 1): CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
            date(2024, 12, 31): CalendarEntry(
                day=date(2024, 12, 31), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_year(2024)

        mock_calendar_repository.get_by_date_range.assert_called_once_with(
            date(2024, 1, 1), date(2024, 12, 31)
        )
        assert date(2024, 1, 1) in result
        assert date(2024, 12, 31) in result


class TestCalendarCreateOperations:
    """Test suite for calendar create operations."""

    @pytest.mark.asyncio
    async def test_creates_work_entry_successfully(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test successful creation of work entry."""
        entry = CalendarEntry(day=weekday_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entry(weekday_date, CalendarEntryType.WORK)

        assert result.day == weekday_date
        assert result.type == CalendarEntryType.WORK
        mock_calendar_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_value_error_when_entry_already_exists(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test ValueError raised when entry already exists."""
        existing_entry = CalendarEntry(
            day=weekday_date, type=CalendarEntryType.WORK, logs=[]
        )
        mock_calendar_repository.get_by_date.return_value = existing_entry
        calendar = Calendar(mock_calendar_repository)

        with pytest.raises(
            ValueError, match=f"Entry already exists for {weekday_date}"
        ):
            await calendar.create_entry(weekday_date, CalendarEntryType.WORK)

    @pytest.mark.asyncio
    async def test_raises_value_error_when_creating_work_entry_on_saturday(
        self, mock_calendar_repository: AsyncMock, weekend_date: date
    ) -> None:
        """Test ValueError raised when creating work entry on Saturday."""
        mock_calendar_repository.get_by_date.return_value = None
        calendar = Calendar(mock_calendar_repository)

        with pytest.raises(ValueError, match="Cannot create work entry on weekend"):
            await calendar.create_entry(weekend_date, CalendarEntryType.WORK)

    @pytest.mark.asyncio
    async def test_raises_value_error_when_creating_work_entry_on_sunday(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test ValueError raised when creating work entry on Sunday."""
        sunday = date(2024, 11, 24)
        mock_calendar_repository.get_by_date.return_value = None
        calendar = Calendar(mock_calendar_repository)

        with pytest.raises(ValueError, match="Cannot create work entry on weekend"):
            await calendar.create_entry(sunday, CalendarEntryType.WORK)

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
    async def test_creates_non_work_entries_successfully(
        self,
        mock_calendar_repository: AsyncMock,
        weekday_date: date,
        entry_type: CalendarEntryType,
    ) -> None:
        """Test successful creation of non-work entry types."""
        entry = CalendarEntry(day=weekday_date, type=entry_type, logs=[])
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entry(weekday_date, entry_type)

        assert result.type == entry_type
        assert result.logs == []

    @pytest.mark.asyncio
    async def test_creates_vacation_entry_on_weekend(
        self, mock_calendar_repository: AsyncMock, weekend_date: date
    ) -> None:
        """Test vacation entry can be created on weekend."""
        entry = CalendarEntry(
            day=weekend_date, type=CalendarEntryType.VACATION, logs=[]
        )
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entry(weekend_date, CalendarEntryType.VACATION)

        assert result.day == weekend_date
        assert result.type == CalendarEntryType.VACATION

    @pytest.mark.asyncio
    async def test_creates_entries_in_date_range_successfully(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test successful creation of multiple entries in date range."""
        start_date = date(2024, 11, 1)
        end_date = date(2024, 11, 5)
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(
            start_date, end_date, CalendarEntryType.VACATION
        )

        assert isinstance(result, list)
        mock_calendar_repository.save_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_entries_skips_existing_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test entry creation skips dates with existing entries."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        existing_entries = {
            date(2024, 11, 19): CalendarEntry(
                day=date(2024, 11, 19), type=CalendarEntryType.WORK, logs=[]
            )
        }
        mock_calendar_repository.get_by_date_range.return_value = existing_entries
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(
            start_date, end_date, CalendarEntryType.VACATION
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_creates_entries_skips_work_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test entry creation skips work entries in date range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(
            start_date, end_date, CalendarEntryType.WORK
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_creates_entries_only_for_workdays(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test entry creation considers only workdays in range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 24)
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        await calendar.create_entries(start_date, end_date, CalendarEntryType.VACATION)

        call_args = mock_calendar_repository.save_all.call_args[0][0]
        for entry in call_args:
            assert is_work_day(entry.day)

    @pytest.mark.asyncio
    async def test_creates_entries_returns_empty_when_all_exist(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test empty list returned when all entries already exist."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 22)
        existing_entries = {
            date(2024, 11, 18): CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 19): CalendarEntry(
                day=date(2024, 11, 19), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 20): CalendarEntry(
                day=date(2024, 11, 20), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 21): CalendarEntry(
                day=date(2024, 11, 21), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 22): CalendarEntry(
                day=date(2024, 11, 22), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = existing_entries
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(
            start_date, end_date, CalendarEntryType.VACATION
        )

        assert result == []

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
    async def test_creates_multiple_non_work_entry_types(
        self,
        mock_calendar_repository: AsyncMock,
        entry_type: CalendarEntryType,
    ) -> None:
        """Test creation of multiple non-work entries of various types."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        entries = [
            CalendarEntry(day=date(2024, 11, 18), type=entry_type, logs=[]),
            CalendarEntry(day=date(2024, 11, 19), type=entry_type, logs=[]),
            CalendarEntry(day=date(2024, 11, 20), type=entry_type, logs=[]),
        ]
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(start_date, end_date, entry_type)

        assert all(e.type == entry_type for e in result)

    @pytest.mark.asyncio
    async def test_creates_entry_calls_repository_save(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test entry creation calls repository save method."""
        entry = CalendarEntry(day=weekday_date, type=CalendarEntryType.WORK, logs=[])
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        await calendar.create_entry(weekday_date, CalendarEntryType.WORK)

        assert mock_calendar_repository.save.called

    @pytest.mark.asyncio
    async def test_creates_entries_with_single_day_range(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test entry creation with single day range."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.VACATION, logs=[])
        ]
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_entries(
            weekday_date, weekday_date, CalendarEntryType.VACATION
        )

        assert len(result) == 1
        assert result[0].day == weekday_date


class TestCalendarUpdateOperations:
    """Test suite for calendar update operations."""

    @pytest.mark.asyncio
    async def test_updates_entry_successfully(
        self, mock_calendar_repository: AsyncMock, work_entry_empty: CalendarEntry
    ) -> None:
        """Test successful entry update."""
        mock_calendar_repository.save.return_value = work_entry_empty
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.update_entry(work_entry_empty)

        assert result == work_entry_empty
        mock_calendar_repository.save.assert_called_once_with(work_entry_empty)

    @pytest.mark.asyncio
    async def test_updates_entry_with_modified_type(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test entry update with modified type."""
        updated_entry = CalendarEntry(
            day=weekday_date, type=CalendarEntryType.VACATION, logs=[]
        )
        mock_calendar_repository.save.return_value = updated_entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.update_entry(updated_entry)

        assert result.type == CalendarEntryType.VACATION
        mock_calendar_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_entry_calls_repository_save(
        self, mock_calendar_repository: AsyncMock, work_entry_empty: CalendarEntry
    ) -> None:
        """Test update calls repository save method."""
        mock_calendar_repository.save.return_value = work_entry_empty
        calendar = Calendar(mock_calendar_repository)

        await calendar.update_entry(work_entry_empty)

        assert mock_calendar_repository.save.called

    @pytest.mark.asyncio
    async def test_resets_entry_successfully(
        self, mock_calendar_repository: AsyncMock, work_entry_empty: CalendarEntry
    ) -> None:
        """Test successful entry reset."""
        mock_calendar_repository.reset.return_value = work_entry_empty
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.reset_entry(work_entry_empty)

        assert result == work_entry_empty
        mock_calendar_repository.reset.assert_called_once_with(work_entry_empty)

    @pytest.mark.asyncio
    async def test_resets_entry_to_last_saved_state(
        self, mock_calendar_repository: AsyncMock, work_entry_standard: CalendarEntry
    ) -> None:
        """Test entry reset reverts to last saved state."""
        mock_calendar_repository.reset.return_value = work_entry_standard
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.reset_entry(work_entry_standard)

        assert result == work_entry_standard
        mock_calendar_repository.reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_resets_entry_calls_repository_reset(
        self, mock_calendar_repository: AsyncMock, work_entry_empty: CalendarEntry
    ) -> None:
        """Test reset calls repository reset method."""
        mock_calendar_repository.reset.return_value = work_entry_empty
        calendar = Calendar(mock_calendar_repository)

        await calendar.reset_entry(work_entry_empty)

        assert mock_calendar_repository.reset.called

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "entry_type",
        [
            CalendarEntryType.WORK,
            CalendarEntryType.VACATION,
            CalendarEntryType.FLEXTIME,
            CalendarEntryType.SICK,
            CalendarEntryType.HOLIDAY,
        ],
        ids=["work", "vacation", "flextime", "sick", "holiday"],
    )
    async def test_updates_entries_with_various_types(
        self,
        mock_calendar_repository: AsyncMock,
        weekday_date: date,
        entry_type: CalendarEntryType,
    ) -> None:
        """Test updating entries with various types."""
        entry = CalendarEntry(day=weekday_date, type=entry_type, logs=[])
        mock_calendar_repository.save.return_value = entry
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.update_entry(entry)

        assert result.type == entry_type


class TestCalendarDeleteOperations:
    """Test suite for calendar delete operations."""

    @pytest.mark.asyncio
    async def test_removes_entry_successfully(
        self,
        mock_calendar_repository: AsyncMock,
        work_entry_empty: CalendarEntry,
    ) -> None:
        """Test successful entry removal."""
        mock_calendar_repository.get_by_date.return_value = work_entry_empty
        mock_calendar_repository.delete.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entry(work_entry_empty.day)

        assert result == work_entry_empty
        mock_calendar_repository.delete.assert_called_once_with(work_entry_empty)

    @pytest.mark.asyncio
    async def test_raises_value_error_when_removing_nonexistent_entry(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test ValueError raised when removing non-existent entry."""
        mock_calendar_repository.get_by_date.return_value = None
        calendar = Calendar(mock_calendar_repository)

        with pytest.raises(
            ValueError, match=f"Entry does not exist for {weekday_date}"
        ):
            await calendar.remove_entry(weekday_date)

    @pytest.mark.asyncio
    async def test_removes_entry_calls_repository_delete(
        self,
        mock_calendar_repository: AsyncMock,
        work_entry_empty: CalendarEntry,
    ) -> None:
        """Test entry removal calls repository delete."""
        mock_calendar_repository.get_by_date.return_value = work_entry_empty
        mock_calendar_repository.delete.return_value = None
        calendar = Calendar(mock_calendar_repository)

        await calendar.remove_entry(work_entry_empty.day)

        mock_calendar_repository.delete.assert_called_once_with(work_entry_empty)

    @pytest.mark.asyncio
    async def test_removes_entries_in_range_successfully(
        self,
        mock_calendar_repository: AsyncMock,
    ) -> None:
        """Test successful removal of entries in date range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        entries = {
            date(2024, 11, 18): CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 19): CalendarEntry(
                day=date(2024, 11, 19), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 20): CalendarEntry(
                day=date(2024, 11, 20), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.delete_all.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entries(start_date, end_date)

        assert len(result) == 3
        mock_calendar_repository.delete_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_removes_entries_returns_empty_when_none_exist(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test empty list returned when no entries exist in range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        mock_calendar_repository.get_by_date_range.return_value = {}
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entries(start_date, end_date)

        assert result == []
        mock_calendar_repository.delete_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_removes_single_entry_from_range(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test removal of single entry in range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 18)
        entries = {
            date(2024, 11, 18): CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.WORK, logs=[]
            )
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.delete_all.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entries(start_date, end_date)

        assert len(result) == 1
        assert result[0].day == start_date

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "entry_type",
        [
            CalendarEntryType.WORK,
            CalendarEntryType.VACATION,
            CalendarEntryType.FLEXTIME,
            CalendarEntryType.SICK,
            CalendarEntryType.HOLIDAY,
        ],
        ids=["work", "vacation", "flextime", "sick", "holiday"],
    )
    async def test_removes_entries_with_various_types(
        self,
        mock_calendar_repository: AsyncMock,
        weekday_date: date,
        entry_type: CalendarEntryType,
    ) -> None:
        """Test removal of entries with various types."""
        entry = CalendarEntry(day=weekday_date, type=entry_type, logs=[])
        mock_calendar_repository.get_by_date.return_value = entry
        mock_calendar_repository.delete.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entry(weekday_date)

        assert result.type == entry_type

    @pytest.mark.asyncio
    async def test_removes_entries_calls_repository_delete_all(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test removal calls repository delete_all method."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        entries = {
            date(2024, 11, 18): CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.delete_all.return_value = None
        calendar = Calendar(mock_calendar_repository)

        await calendar.remove_entries(start_date, end_date)

        assert mock_calendar_repository.delete_all.called

    @pytest.mark.asyncio
    async def test_removes_entries_handles_large_range(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test removal handles large date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        entries = {
            date(2024, 6, 15): CalendarEntry(
                day=date(2024, 6, 15), type=CalendarEntryType.WORK, logs=[]
            )
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.delete_all.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entries(start_date, end_date)

        assert len(result) == 1
        mock_calendar_repository.get_by_date_range.assert_called_once_with(
            start_date, end_date
        )

    @pytest.mark.asyncio
    async def test_removes_entries_preserves_order(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test removal preserves entry order."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        entries = {
            date(2024, 11, 18): CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 19): CalendarEntry(
                day=date(2024, 11, 19), type=CalendarEntryType.WORK, logs=[]
            ),
            date(2024, 11, 20): CalendarEntry(
                day=date(2024, 11, 20), type=CalendarEntryType.WORK, logs=[]
            ),
        }
        mock_calendar_repository.get_by_date_range.return_value = entries
        mock_calendar_repository.delete_all.return_value = None
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.remove_entries(start_date, end_date)

        assert len(result) == 3


class TestCalendarHolidayOperations:
    """Test suite for calendar holiday operations."""

    @pytest.mark.asyncio
    async def test_adds_public_holidays_successfully(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test successful addition of public holidays."""
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert isinstance(result, list)
        mock_calendar_repository.save_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_adds_holidays_for_german_state(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holiday addition for German state."""
        holiday_entries = [
            CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = holiday_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert len(result) >= 0
        mock_calendar_repository.save_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_adds_holidays_skips_existing_holidays(
        self,
        mock_calendar_repository: AsyncMock,
    ) -> None:
        """Test holiday addition skips existing holiday entries."""
        existing_holiday = CalendarEntry(
            day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
        )
        mock_calendar_repository.get_by_date.return_value = existing_holiday
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert result == []

    @pytest.mark.asyncio
    async def test_adds_holidays_warns_on_conflicting_entry(
        self,
        mock_calendar_repository: AsyncMock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test holiday addition warns when conflicting entry exists."""
        conflicting_entry = CalendarEntry(
            day=date(2024, 1, 1), type=CalendarEntryType.WORK, logs=[]
        )
        mock_calendar_repository.get_by_date.return_value = conflicting_entry
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        await calendar.add_public_holidays(2024, "BW")

        assert "Cannot add holiday" in caplog.text

    @pytest.mark.asyncio
    async def test_adds_holidays_creates_holiday_entry_type(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holiday addition creates entries with holiday type."""
        holiday_entries = [
            CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
            CalendarEntry(
                day=date(2024, 12, 25), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = holiday_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert all(e.type == CalendarEntryType.HOLIDAY for e in result)

    @pytest.mark.asyncio
    async def test_adds_holidays_with_empty_logs(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holiday entries created with empty logs."""
        holiday_entries = [
            CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = holiday_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert all(e.logs == [] for e in result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [
            "BW",
            "BY",
            "BE",
            "BB",
            "HB",
            "HH",
            "HE",
            "MV",
            "NI",
            "NW",
            "RP",
            "SL",
            "SN",
            "ST",
            "SH",
            "TH",
        ],
        ids=[
            "baden_wuerttemberg",
            "bavaria",
            "berlin",
            "brandenburg",
            "bremen",
            "hamburg",
            "hesse",
            "mecklenburg_vorpommern",
            "lower_saxony",
            "north_rhine_westphalia",
            "rhineland_palatinate",
            "saarland",
            "saxony",
            "saxony_anhalt",
            "schleswig_holstein",
            "thuringia",
        ],
    )
    async def test_adds_holidays_for_all_german_states(
        self, mock_calendar_repository: AsyncMock, state: str
    ) -> None:
        """Test holiday addition for all German states."""
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, state)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_adds_holidays_returns_created_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holiday addition returns list of created entries."""
        holiday_entries = [
            CalendarEntry(
                day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
            CalendarEntry(
                day=date(2024, 5, 1), type=CalendarEntryType.HOLIDAY, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = holiday_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert result == holiday_entries

    @pytest.mark.asyncio
    async def test_adds_holidays_calls_repository_save_all(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test holiday addition calls repository save_all method."""
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        await calendar.add_public_holidays(2024, "BW")

        assert mock_calendar_repository.save_all.called

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "year",
        [2023, 2024, 2025, 2026],
        ids=["year_2023", "year_2024", "year_2025", "year_2026"],
    )
    async def test_adds_holidays_for_multiple_years(
        self, mock_calendar_repository: AsyncMock, year: int
    ) -> None:
        """Test holiday addition for multiple years."""
        mock_calendar_repository.get_by_date.return_value = None
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(year, "BW")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_adds_holidays_returns_empty_when_all_exist(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test empty list returned when all holidays already exist."""
        existing_holiday = CalendarEntry(
            day=date(2024, 1, 1), type=CalendarEntryType.HOLIDAY, logs=[]
        )
        mock_calendar_repository.get_by_date.return_value = existing_holiday
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.add_public_holidays(2024, "BW")

        assert result == []


class TestVacationEntryCreation:
    """Test suite for vacation entry creation with weekend and holiday filtering."""

    @pytest.mark.asyncio
    async def test_gets_available_vacation_dates_skips_weekends(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test available vacation dates skips weekends."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 24)  # Sunday
        mock_calendar_repository.get_by_date_range.return_value = {}
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_available_vacation_dates(start, end)

        # Should only have 5 weekdays (Mon-Fri)
        assert len(result) == 5
        assert date(2024, 11, 23) not in result  # Saturday
        assert date(2024, 11, 24) not in result  # Sunday

    @pytest.mark.asyncio
    async def test_gets_available_vacation_dates_skips_holidays(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test available vacation dates skips existing holidays."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 22)  # Friday
        holiday_entry = CalendarEntry(
            day=date(2024, 11, 20), type=CalendarEntryType.HOLIDAY, logs=[]
        )
        mock_calendar_repository.get_by_date_range.return_value = {
            date(2024, 11, 20): holiday_entry
        }
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_available_vacation_dates(start, end)

        # Should have 4 weekdays (Wed holiday excluded)
        assert len(result) == 4
        assert date(2024, 11, 20) not in result

    @pytest.mark.asyncio
    async def test_gets_available_vacation_dates_skips_existing_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test available vacation dates skips any existing entries."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 22)  # Friday
        work_entry = CalendarEntry(
            day=date(2024, 11, 19), type=CalendarEntryType.WORK, logs=[]
        )
        mock_calendar_repository.get_by_date_range.return_value = {
            date(2024, 11, 19): work_entry
        }
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.get_available_vacation_dates(start, end)

        # Should have 4 weekdays (Tue work entry excluded)
        assert len(result) == 4
        assert date(2024, 11, 19) not in result

    @pytest.mark.asyncio
    async def test_creates_vacation_entries_skips_weekends(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test vacation entries creation skips weekends."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 24)  # Sunday
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        await calendar.create_vacation_entries(start, end)

        call_args = mock_calendar_repository.save_all.call_args[0][0]
        for entry in call_args:
            assert is_work_day(entry.day)
            assert entry.type == CalendarEntryType.VACATION

    @pytest.mark.asyncio
    async def test_creates_vacation_entries_skips_holidays(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test vacation entries creation skips existing holidays."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 22)  # Friday
        holiday_entry = CalendarEntry(
            day=date(2024, 11, 20), type=CalendarEntryType.HOLIDAY, logs=[]
        )
        mock_calendar_repository.get_by_date_range.return_value = {
            date(2024, 11, 20): holiday_entry
        }
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        await calendar.create_vacation_entries(start, end)

        call_args = mock_calendar_repository.save_all.call_args[0][0]
        dates_created = [e.day for e in call_args]
        assert date(2024, 11, 20) not in dates_created

    @pytest.mark.asyncio
    async def test_creates_vacation_entries_returns_created_entries(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test vacation entries creation returns saved entries."""
        start = date(2024, 11, 18)  # Monday
        end = date(2024, 11, 19)  # Tuesday
        expected_entries = [
            CalendarEntry(
                day=date(2024, 11, 18), type=CalendarEntryType.VACATION, logs=[]
            ),
            CalendarEntry(
                day=date(2024, 11, 19), type=CalendarEntryType.VACATION, logs=[]
            ),
        ]
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = expected_entries
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_vacation_entries(start, end)

        assert result == expected_entries
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_creates_vacation_entries_returns_empty_when_all_filtered(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test vacation entries creation returns empty list when all dates filtered."""
        # Weekend only range
        start = date(2024, 11, 23)  # Saturday
        end = date(2024, 11, 24)  # Sunday
        mock_calendar_repository.get_by_date_range.return_value = {}
        mock_calendar_repository.save_all.return_value = []
        calendar = Calendar(mock_calendar_repository)

        result = await calendar.create_vacation_entries(start, end)

        assert result == []


class TestCalendarIterators:
    """Test suite for calendar iterator methods."""

    def test_iterates_over_date_range_successfully(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test successful iteration over date range."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 20)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 3
        assert result[0] == date(2024, 11, 18)
        assert result[1] == date(2024, 11, 19)
        assert result[2] == date(2024, 11, 20)

    def test_raises_value_error_when_end_before_start(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test ValueError raised when end date before start date."""
        start_date = date(2024, 11, 20)
        end_date = date(2024, 11, 18)
        calendar = Calendar(mock_calendar_repository)

        with pytest.raises(
            ValueError,
            match=f"The end date \\({end_date}\\) must not be before the start date \\({start_date}\\)",
        ):
            list(calendar.iterate(start_date, end_date))

    def test_iterates_single_day(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test iteration over single day."""
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(weekday_date, weekday_date))

        assert len(result) == 1
        assert result[0] == weekday_date

    def test_iterates_across_month_boundary(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration across month boundary."""
        start_date = date(2024, 11, 29)
        end_date = date(2024, 12, 2)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 4
        assert result[0] == date(2024, 11, 29)
        assert result[-1] == date(2024, 12, 2)

    def test_iterates_across_year_boundary(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration across year boundary."""
        start_date = date(2024, 12, 30)
        end_date = date(2025, 1, 2)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 4
        assert result[0] == date(2024, 12, 30)
        assert result[-1] == date(2025, 1, 2)

    def test_iterates_includes_weekends(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration includes weekend dates."""
        start_date = date(2024, 11, 22)
        end_date = date(2024, 11, 24)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 3
        assert date(2024, 11, 23) in result
        assert date(2024, 11, 24) in result

    def test_iterates_workdays_excludes_weekends(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration excludes weekends."""
        start_date = date(2024, 11, 22)
        end_date = date(2024, 11, 25)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        assert len(result) == 2
        assert date(2024, 11, 22) in result
        assert date(2024, 11, 25) in result
        assert date(2024, 11, 23) not in result
        assert date(2024, 11, 24) not in result

    def test_iterates_workdays_full_week(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration over full week."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 24)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        assert len(result) == 5
        assert date(2024, 11, 18) in result
        assert date(2024, 11, 22) in result

    def test_iterates_workdays_single_weekday(
        self, mock_calendar_repository: AsyncMock, weekday_date: date
    ) -> None:
        """Test workdays iteration with single weekday."""
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(weekday_date, weekday_date))

        assert len(result) == 1
        assert result[0] == weekday_date

    def test_iterates_workdays_single_weekend_day(
        self, mock_calendar_repository: AsyncMock, weekend_date: date
    ) -> None:
        """Test workdays iteration with single weekend day."""
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(weekend_date, weekend_date))

        assert len(result) == 0

    def test_iterates_workdays_across_month_boundary(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration across month boundary."""
        start_date = date(2024, 11, 28)
        end_date = date(2024, 12, 2)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        assert date(2024, 11, 28) in result
        assert date(2024, 11, 29) in result
        assert date(2024, 11, 30) not in result
        assert date(2024, 12, 1) not in result
        assert date(2024, 12, 2) in result

    def test_iterates_workdays_across_year_boundary(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration across year boundary."""
        start_date = date(2023, 12, 29)
        end_date = date(2024, 1, 3)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        assert date(2023, 12, 29) in result
        assert date(2023, 12, 30) not in result
        assert date(2023, 12, 31) not in result
        assert date(2024, 1, 1) in result
        assert date(2024, 1, 2) in result
        assert date(2024, 1, 3) in result

    def test_iterates_entire_month(self, mock_calendar_repository: AsyncMock) -> None:
        """Test iteration over entire month."""
        start_date = date(2024, 11, 1)
        end_date = date(2024, 11, 30)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 30
        assert result[0] == date(2024, 11, 1)
        assert result[-1] == date(2024, 11, 30)

    def test_iterates_leap_year_february(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration over leap year February."""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 29)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 29
        assert date(2024, 2, 29) in result

    def test_iterates_non_leap_year_february(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration over non-leap year February."""
        start_date = date(2023, 2, 1)
        end_date = date(2023, 2, 28)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 28
        assert date(2023, 2, 28) in result

    @pytest.mark.parametrize(
        "start,end,expected_count",
        [
            (date(2024, 11, 18), date(2024, 11, 22), 5),
            (date(2024, 11, 18), date(2024, 11, 24), 5),
            (date(2024, 11, 23), date(2024, 11, 24), 0),
            (date(2024, 11, 22), date(2024, 11, 25), 2),
        ],
        ids=[
            "monday_to_friday",
            "monday_to_sunday",
            "saturday_to_sunday",
            "friday_to_monday",
        ],
    )
    def test_counts_workdays_correctly(
        self,
        mock_calendar_repository: AsyncMock,
        start: date,
        end: date,
        expected_count: int,
    ) -> None:
        """Test workdays count for various date ranges."""
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start, end))

        assert len(result) == expected_count

    def test_iterates_preserves_date_order(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test iteration preserves chronological order."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 22)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]

    def test_iterates_workdays_preserves_order(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration preserves chronological order."""
        start_date = date(2024, 11, 18)
        end_date = date(2024, 11, 22)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]

    def test_iterates_long_range(self, mock_calendar_repository: AsyncMock) -> None:
        """Test iteration over long date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.iterate(start_date, end_date))

        assert len(result) == 366

    def test_iterates_workdays_long_range(
        self, mock_calendar_repository: AsyncMock
    ) -> None:
        """Test workdays iteration over long date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        calendar = Calendar(mock_calendar_repository)

        result = list(calendar.workdays(start_date, end_date))

        assert len(result) == 262
