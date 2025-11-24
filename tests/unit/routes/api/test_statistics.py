"""Test suite for statistics API routes."""

from datetime import date, time, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from app.model import CalendarEntry, CalendarEntryType, TimeLog, TimeLogType
from app.routes.api.statistics import get_statistics
from app.services.calendar import Calendar
from app.services.statistics import (
    ComplianceViolation,
    Statistics,
    StatisticsService,
    TypeCount,
    ViolationType,
)


@pytest.fixture
def mock_calendar() -> AsyncMock:
    """Mock Calendar service for testing."""
    mock = AsyncMock(spec=Calendar)
    return mock


@pytest.fixture
def mock_statistics_service() -> Mock:
    """Mock StatisticsService for testing."""
    mock = Mock(spec=StatisticsService)
    return mock


@pytest.fixture
def sample_work_entry() -> CalendarEntry:
    """Provide sample work entry with time logs."""
    return CalendarEntry(
        day=date(2024, 1, 15),
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
def sample_vacation_entry() -> CalendarEntry:
    """Provide sample vacation entry without logs."""
    return CalendarEntry(
        day=date(2024, 1, 16),
        type=CalendarEntryType.VACATION,
        logs=[],
    )


@pytest.fixture
def sample_statistics() -> Statistics:
    """Provide sample Statistics object."""
    return Statistics(
        entry_counts=TypeCount(
            work=20, vacation=5, holiday=10, sick=2, flex_days=1, travel=0
        ),
        total_work_hours=timedelta(hours=160),
        flextime_balance=timedelta(hours=0),
        compliance_violations=[],
    )


@pytest.fixture
def sample_statistics_with_violations() -> Statistics:
    """Provide Statistics object with compliance violations."""
    return Statistics(
        entry_counts=TypeCount(
            work=20, vacation=0, holiday=0, sick=0, flex_days=0, travel=0
        ),
        total_work_hours=timedelta(hours=200),
        flextime_balance=timedelta(hours=40),
        compliance_violations=[
            ComplianceViolation(
                day=date(2024, 1, 15),
                type=ViolationType.MAX_HOURS,
                details="Worked 10:30:00 exceeding maximum of 10:00:00",
            ),
            ComplianceViolation(
                day=date(2024, 1, 20),
                type=ViolationType.BREAK_TIME,
                details="Insufficient break 0:20:00 for duration 9:30:00",
            ),
        ],
    )


class TestGetStatistics:
    """Test suite for get_statistics endpoint."""

    @pytest.mark.asyncio
    async def test_retrieves_statistics_for_current_year(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_work_entry: CalendarEntry,
        sample_statistics: Statistics,
    ) -> None:
        """Test retrieving statistics with default current year."""
        current_year = date.today().year
        mock_calendar.get_year.return_value = {sample_work_entry.day: sample_work_entry}
        mock_statistics_service.calculate_statistics.return_value = sample_statistics

        result = await get_statistics(
            year=current_year,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result.entry_counts.work == 20
        assert result.total_work_hours == timedelta(hours=160)
        mock_calendar.get_year.assert_called_once_with(current_year)

    @pytest.mark.asyncio
    async def test_retrieves_statistics_for_specific_year(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_work_entry: CalendarEntry,
        sample_statistics: Statistics,
    ) -> None:
        """Test retrieving statistics for specific year."""
        mock_calendar.get_year.return_value = {sample_work_entry.day: sample_work_entry}
        mock_statistics_service.calculate_statistics.return_value = sample_statistics

        result = await get_statistics(
            year=2023,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result == sample_statistics
        mock_calendar.get_year.assert_called_once_with(2023)

    @pytest.mark.asyncio
    async def test_returns_empty_statistics_for_year_with_no_entries(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test empty statistics returned when no entries exist."""
        empty_statistics = Statistics(
            entry_counts=TypeCount(),
            total_work_hours=timedelta(0),
            flextime_balance=timedelta(0),
            compliance_violations=[],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = empty_statistics

        result = await get_statistics(
            year=2023,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result.entry_counts.work == 0
        assert result.total_work_hours == timedelta(0)
        assert result.flextime_balance == timedelta(0)
        assert len(result.compliance_violations) == 0

    @pytest.mark.asyncio
    async def test_calculates_statistics_for_mixed_entry_types(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_work_entry: CalendarEntry,
        sample_vacation_entry: CalendarEntry,
    ) -> None:
        """Test statistics calculation with mixed entry types."""
        entries = {
            sample_work_entry.day: sample_work_entry,
            sample_vacation_entry.day: sample_vacation_entry,
        }
        mixed_statistics = Statistics(
            entry_counts=TypeCount(
                work=15, vacation=5, holiday=5, sick=2, flex_days=3, travel=1
            ),
            total_work_hours=timedelta(hours=120),
            flextime_balance=timedelta(hours=-8),
            compliance_violations=[],
        )
        mock_calendar.get_year.return_value = entries
        mock_statistics_service.calculate_statistics.return_value = mixed_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result.entry_counts.work == 15
        assert result.entry_counts.vacation == 5
        assert result.entry_counts.holiday == 5
        assert result.entry_counts.sick == 2
        assert result.entry_counts.flex_days == 3
        assert result.entry_counts.travel == 1

    @pytest.mark.asyncio
    async def test_includes_compliance_violations(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_work_entry: CalendarEntry,
        sample_statistics_with_violations: Statistics,
    ) -> None:
        """Test statistics includes compliance violations."""
        mock_calendar.get_year.return_value = {sample_work_entry.day: sample_work_entry}
        mock_statistics_service.calculate_statistics.return_value = (
            sample_statistics_with_violations
        )

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert len(result.compliance_violations) == 2
        assert result.compliance_violations[0].type == ViolationType.MAX_HOURS
        assert result.compliance_violations[1].type == ViolationType.BREAK_TIME

    @pytest.mark.asyncio
    async def test_raises_500_when_calendar_service_fails(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test HTTP 500 raised when calendar service throws exception."""
        mock_calendar.get_year.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await get_statistics(
                year=2024,
                calendar=mock_calendar,
                statistics_service=mock_statistics_service,
            )

    @pytest.mark.asyncio
    async def test_raises_500_when_statistics_service_fails(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test HTTP 500 raised when statistics service throws exception."""
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.side_effect = Exception(
            "Calculation error"
        )

        with pytest.raises(Exception, match="Calculation error"):
            await get_statistics(
                year=2024,
                calendar=mock_calendar,
                statistics_service=mock_statistics_service,
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "year",
        [1, 2000, 2024, 2025, 9999],
        ids=["year_1", "year_2000", "year_2024", "year_2025", "year_9999"],
    )
    async def test_handles_boundary_years(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_statistics: Statistics,
        year: int,
    ) -> None:
        """Test handling of boundary year values."""
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = sample_statistics

        result = await get_statistics(
            year=year,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        mock_calendar.get_year.assert_called_once_with(year)
        assert isinstance(result, Statistics)

    @pytest.mark.asyncio
    async def test_calculates_correct_flextime_balance(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test flextime balance calculation accuracy."""
        flextime_statistics = Statistics(
            entry_counts=TypeCount(work=20),
            total_work_hours=timedelta(hours=170),
            flextime_balance=timedelta(hours=10),
            compliance_violations=[],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = flextime_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result.flextime_balance == timedelta(hours=10)

    @pytest.mark.asyncio
    async def test_passes_entries_to_statistics_service(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_work_entry: CalendarEntry,
        sample_statistics: Statistics,
    ) -> None:
        """Test entries correctly passed to statistics service."""
        entries = {sample_work_entry.day: sample_work_entry}
        mock_calendar.get_year.return_value = entries
        mock_statistics_service.calculate_statistics.return_value = sample_statistics

        await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        mock_statistics_service.calculate_statistics.assert_called_once()
        call_args = mock_statistics_service.calculate_statistics.call_args[0][0]
        assert list(call_args) == [sample_work_entry]

    @pytest.mark.asyncio
    async def test_returns_valid_statistics_json(
        self,
        mock_calendar: AsyncMock,
        mock_statistics_service: Mock,
        sample_statistics: Statistics,
    ) -> None:
        """Test response is valid Statistics JSON."""
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = sample_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert isinstance(result, Statistics)
        assert isinstance(result.entry_counts, TypeCount)
        assert isinstance(result.total_work_hours, timedelta)
        assert isinstance(result.flextime_balance, timedelta)
        assert isinstance(result.compliance_violations, list)

    @pytest.mark.asyncio
    async def test_handles_negative_flextime_balance(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test handling of negative flextime balance."""
        negative_flextime_statistics = Statistics(
            entry_counts=TypeCount(work=20),
            total_work_hours=timedelta(hours=150),
            flextime_balance=timedelta(hours=-10),
            compliance_violations=[],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = (
            negative_flextime_statistics
        )

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert result.flextime_balance == timedelta(hours=-10)

    @pytest.mark.asyncio
    async def test_handles_max_hours_violation(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test detection of max hours exceeded violation."""
        violation_statistics = Statistics(
            entry_counts=TypeCount(work=1),
            total_work_hours=timedelta(hours=11),
            flextime_balance=timedelta(hours=3),
            compliance_violations=[
                ComplianceViolation(
                    day=date(2024, 1, 15),
                    type=ViolationType.MAX_HOURS,
                    details="Worked 11:00:00 exceeding maximum of 10:00:00",
                )
            ],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = violation_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert len(result.compliance_violations) == 1
        assert result.compliance_violations[0].type == ViolationType.MAX_HOURS
        assert "exceeding maximum" in result.compliance_violations[0].details

    @pytest.mark.asyncio
    async def test_handles_break_time_violation(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test detection of insufficient break time violation."""
        violation_statistics = Statistics(
            entry_counts=TypeCount(work=1),
            total_work_hours=timedelta(hours=9),
            flextime_balance=timedelta(hours=1),
            compliance_violations=[
                ComplianceViolation(
                    day=date(2024, 1, 15),
                    type=ViolationType.BREAK_TIME,
                    details="Insufficient break 0:20:00 for duration 9:00:00",
                )
            ],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = violation_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert len(result.compliance_violations) == 1
        assert result.compliance_violations[0].type == ViolationType.BREAK_TIME
        assert "Insufficient break" in result.compliance_violations[0].details

    @pytest.mark.asyncio
    async def test_handles_rest_period_violation(
        self, mock_calendar: AsyncMock, mock_statistics_service: Mock
    ) -> None:
        """Test detection of insufficient rest period violation."""
        violation_statistics = Statistics(
            entry_counts=TypeCount(work=2),
            total_work_hours=timedelta(hours=16),
            flextime_balance=timedelta(hours=0),
            compliance_violations=[
                ComplianceViolation(
                    day=date(2024, 1, 16),
                    type=ViolationType.REST_PERIOD,
                    details="Rest period of 10:00:00 is less than required 11:00:00",
                )
            ],
        )
        mock_calendar.get_year.return_value = {}
        mock_statistics_service.calculate_statistics.return_value = violation_statistics

        result = await get_statistics(
            year=2024,
            calendar=mock_calendar,
            statistics_service=mock_statistics_service,
        )

        assert len(result.compliance_violations) == 1
        assert result.compliance_violations[0].type == ViolationType.REST_PERIOD
        assert "Rest period" in result.compliance_violations[0].details
