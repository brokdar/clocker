"""Test suite for statistics service."""

from datetime import date, time, timedelta

import pytest

from app.model import CalendarEntry, CalendarEntryType, TimeLog, TimeLogType
from app.services.statistics import (
    ComplianceViolation,
    Statistics,
    StatisticsConfiguration,
    StatisticsService,
    TypeCount,
    ViolationType,
)


@pytest.fixture
def statistics_service(
    default_statistics_config: StatisticsConfiguration,
) -> StatisticsService:
    """Provide StatisticsService instance with default configuration."""
    return StatisticsService(default_statistics_config)


@pytest.fixture
def custom_statistics_service(
    custom_statistics_config: StatisticsConfiguration,
) -> StatisticsService:
    """Provide StatisticsService instance with custom configuration."""
    return StatisticsService(custom_statistics_config)


@pytest.fixture
def work_entry_six_hours(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 6 hours (no break required)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(15, 0),
                pause=timedelta(0),
            )
        ],
    )


@pytest.fixture
def work_entry_six_hours_thirty_minutes(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 6.5 hours (30min break required)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(16, 0),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def work_entry_nine_hours(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 9 hours (45min break required)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(8, 0),
                end=time(17, 45),
                pause=timedelta(minutes=45),
            )
        ],
    )


@pytest.fixture
def work_entry_eleven_hours(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 11 hours (exceeds max)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(7, 0),
                end=time(19, 0),
                pause=timedelta(minutes=60),
            )
        ],
    )


@pytest.fixture
def work_entry_with_travel(weekday_date: date) -> CalendarEntry:
    """Provide work entry with both work and travel logs."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.TRAVEL,
                start=time(8, 0),
                end=time(9, 0),
                pause=timedelta(0),
            ),
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(17, 0),
                pause=timedelta(minutes=30),
            ),
        ],
    )


@pytest.fixture
def work_entry_insufficient_break_six_hours(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 6.5 hours but insufficient break."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(15, 45),
                pause=timedelta(minutes=15),
            )
        ],
    )


@pytest.fixture
def work_entry_insufficient_break_nine_hours(weekday_date: date) -> CalendarEntry:
    """Provide work entry with 9 hours but insufficient break."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(8, 0),
                end=time(17, 30),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def work_entry_zero_duration(weekday_date: date) -> CalendarEntry:
    """Provide work entry with zero duration (same start and end)."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(9, 0),
                pause=timedelta(0),
            )
        ],
    )


@pytest.fixture
def work_entry_late_night(weekday_date: date) -> CalendarEntry:
    """Provide work entry ending late at night."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(14, 0),
                end=time(23, 30),
                pause=timedelta(minutes=30),
            )
        ],
    )


@pytest.fixture
def work_entry_early_morning(weekday_date: date) -> CalendarEntry:
    """Provide work entry starting very early."""
    return CalendarEntry(
        day=weekday_date,
        type=CalendarEntryType.WORK,
        logs=[
            TimeLog(
                type=TimeLogType.WORK,
                start=time(6, 0),
                end=time(14, 30),
                pause=timedelta(minutes=30),
            )
        ],
    )


class TestStatisticsConfiguration:
    """Test suite for StatisticsConfiguration."""

    def test_creates_configuration_with_default_values(self) -> None:
        """Test configuration creation with default values."""
        config = StatisticsConfiguration()

        assert config.standard_work_hours == timedelta(hours=8)
        assert config.max_work_hours == timedelta(hours=10)
        assert config.min_break_threshold == timedelta(hours=6)
        assert config.min_break_duration == timedelta(minutes=30)
        assert config.max_break_threshold == timedelta(hours=9)
        assert config.max_break_duration == timedelta(minutes=45)
        assert config.min_rest_period == timedelta(hours=11)

    def test_creates_configuration_with_custom_values(self) -> None:
        """Test configuration creation with custom values."""
        config = StatisticsConfiguration(
            standard_work_hours=timedelta(hours=7),
            max_work_hours=timedelta(hours=9),
            min_rest_period=timedelta(hours=12),
        )

        assert config.standard_work_hours == timedelta(hours=7)
        assert config.max_work_hours == timedelta(hours=9)
        assert config.min_rest_period == timedelta(hours=12)

    def test_validates_configuration_model_structure(self) -> None:
        """Test configuration model structure validation."""
        config = StatisticsConfiguration(
            standard_work_hours=timedelta(hours=8),
            max_work_hours=timedelta(hours=10),
            min_break_threshold=timedelta(hours=6),
            min_break_duration=timedelta(minutes=30),
            max_break_threshold=timedelta(hours=9),
            max_break_duration=timedelta(minutes=45),
            min_rest_period=timedelta(hours=11),
        )

        assert isinstance(config.standard_work_hours, timedelta)
        assert isinstance(config.max_work_hours, timedelta)
        assert isinstance(config.min_break_threshold, timedelta)
        assert isinstance(config.min_break_duration, timedelta)
        assert isinstance(config.max_break_threshold, timedelta)
        assert isinstance(config.max_break_duration, timedelta)
        assert isinstance(config.min_rest_period, timedelta)


class TestStatisticsServiceInitialization:
    """Test suite for StatisticsService initialization."""

    def test_initializes_service_with_configuration(
        self, default_statistics_config: StatisticsConfiguration
    ) -> None:
        """Test service initialization with configuration."""
        service = StatisticsService(default_statistics_config)

        assert service.config == default_statistics_config

    def test_initializes_service_with_custom_configuration(
        self, custom_statistics_config: StatisticsConfiguration
    ) -> None:
        """Test service initialization with custom configuration."""
        service = StatisticsService(custom_statistics_config)

        assert service.config == custom_statistics_config
        assert service.config.standard_work_hours == timedelta(hours=7, minutes=30)


class TestCalculateFlextime:
    """Test suite for calculate_flextime method."""

    def test_calculates_positive_flextime_for_overtime(
        self,
        statistics_service: StatisticsService,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test positive flextime calculation for overtime work."""
        flextime = statistics_service.calculate_flextime(work_entry_overtime)

        assert flextime == timedelta(hours=2, minutes=30)

    def test_calculates_negative_flextime_for_undertime(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test negative flextime calculation for undertime work."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(15, 0),
                    pause=timedelta(0),
                )
            ],
        )
        flextime = statistics_service.calculate_flextime(entry)

        assert flextime == timedelta(hours=-2)

    def test_calculates_zero_flextime_for_standard_hours(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
    ) -> None:
        """Test zero flextime for exactly standard work hours."""
        flextime = statistics_service.calculate_flextime(work_entry_standard)

        assert flextime == timedelta(0)

    def test_returns_none_for_vacation_entry(
        self,
        statistics_service: StatisticsService,
        vacation_entry: CalendarEntry,
    ) -> None:
        """Test None returned for vacation entry."""
        flextime = statistics_service.calculate_flextime(vacation_entry)

        assert flextime is None

    def test_returns_none_for_holiday_entry(
        self,
        statistics_service: StatisticsService,
        holiday_entry: CalendarEntry,
    ) -> None:
        """Test None returned for holiday entry."""
        flextime = statistics_service.calculate_flextime(holiday_entry)

        assert flextime is None

    def test_returns_none_for_sick_entry(
        self, statistics_service: StatisticsService, sick_entry: CalendarEntry
    ) -> None:
        """Test None returned for sick entry."""
        flextime = statistics_service.calculate_flextime(sick_entry)

        assert flextime is None

    def test_calculates_negative_standard_hours_for_flextime_entry(
        self, statistics_service: StatisticsService, flextime_entry: CalendarEntry
    ) -> None:
        """Test flextime entry returns None when no duration."""
        flextime = statistics_service.calculate_flextime(flextime_entry)

        assert flextime is None

    def test_returns_none_when_entry_duration_is_none(
        self, statistics_service: StatisticsService, work_entry_empty: CalendarEntry
    ) -> None:
        """Test negative standard hours returned when work entry has zero duration."""
        flextime = statistics_service.calculate_flextime(work_entry_empty)

        assert flextime == timedelta(hours=-8)

    def test_calculates_flextime_with_custom_configuration(
        self,
        custom_statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
    ) -> None:
        """Test flextime calculation with custom standard hours."""
        flextime = custom_statistics_service.calculate_flextime(work_entry_standard)

        assert flextime == timedelta(minutes=30)

    def test_calculates_flextime_for_very_long_workday(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test flextime calculation for very long workday."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(22, 0),
                    pause=timedelta(hours=1),
                )
            ],
        )
        flextime = statistics_service.calculate_flextime(entry)

        assert flextime == timedelta(hours=7)


class TestCheckDailyCompliance:
    """Test suite for _check_daily_compliance method."""

    def test_returns_empty_list_for_compliant_work_entry(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
    ) -> None:
        """Test no violations for compliant work entry."""
        violations = statistics_service._check_daily_compliance(work_entry_standard)

        assert violations == []

    def test_detects_max_hours_violation(
        self,
        statistics_service: StatisticsService,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test detection of maximum work hours violation."""
        violations = statistics_service._check_daily_compliance(work_entry_overtime)

        assert len(violations) == 2
        violation_types = {v.type for v in violations}
        assert ViolationType.MAX_HOURS in violation_types
        assert ViolationType.BREAK_TIME in violation_types

    def test_detects_break_time_violation_for_six_hour_threshold(
        self,
        statistics_service: StatisticsService,
        work_entry_insufficient_break_six_hours: CalendarEntry,
    ) -> None:
        """Test detection of break time violation at 6-hour threshold."""
        violations = statistics_service._check_daily_compliance(
            work_entry_insufficient_break_six_hours
        )

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME
        assert "Insufficient break" in violations[0].details

    def test_detects_break_time_violation_for_nine_hour_threshold(
        self,
        statistics_service: StatisticsService,
        work_entry_insufficient_break_nine_hours: CalendarEntry,
    ) -> None:
        """Test detection of break time violation at 9-hour threshold."""
        violations = statistics_service._check_daily_compliance(
            work_entry_insufficient_break_nine_hours
        )

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME
        assert "Insufficient extended break" in violations[0].details

    def test_detects_multiple_violations(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test detection of multiple violations in single entry."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(8, 0),
                    end=time(19, 0),
                    pause=timedelta(minutes=15),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 2
        violation_types = {v.type for v in violations}
        assert ViolationType.MAX_HOURS in violation_types
        assert ViolationType.BREAK_TIME in violation_types

    def test_accepts_six_hour_work_without_break(
        self,
        statistics_service: StatisticsService,
        work_entry_six_hours: CalendarEntry,
    ) -> None:
        """Test violation for 6-hour work without break."""
        violations = statistics_service._check_daily_compliance(work_entry_six_hours)

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME

    def test_accepts_six_hour_thirty_minutes_with_thirty_minute_break(
        self,
        statistics_service: StatisticsService,
        work_entry_six_hours_thirty_minutes: CalendarEntry,
    ) -> None:
        """Test no violation for 6.5-hour work with 30-minute break."""
        violations = statistics_service._check_daily_compliance(
            work_entry_six_hours_thirty_minutes
        )

        assert violations == []

    def test_accepts_nine_hour_work_with_forty_five_minute_break(
        self,
        statistics_service: StatisticsService,
        work_entry_nine_hours: CalendarEntry,
    ) -> None:
        """Test no violation for 9-hour work with 45-minute break."""
        violations = statistics_service._check_daily_compliance(work_entry_nine_hours)

        assert violations == []

    def test_returns_empty_list_for_zero_duration_work(
        self,
        statistics_service: StatisticsService,
        work_entry_zero_duration: CalendarEntry,
    ) -> None:
        """Test no violations for zero duration work entry."""
        violations = statistics_service._check_daily_compliance(
            work_entry_zero_duration
        )

        assert violations == []

    def test_uses_custom_configuration_for_max_hours(
        self,
        custom_statistics_service: StatisticsService,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test custom max hours configuration affects violation detection."""
        violations = custom_statistics_service._check_daily_compliance(
            work_entry_overtime
        )

        assert len(violations) >= 1
        assert any(v.type == ViolationType.MAX_HOURS for v in violations)

    def test_handles_entry_with_no_pause_time(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of entry with zero pause time."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(15, 30),
                    pause=timedelta(0),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME

    def test_validates_exact_boundary_at_six_hours(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exact 6-hour boundary requires 30-minute break."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(15, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME

    def test_validates_exact_boundary_at_nine_hours(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exact 9-hour boundary requires 45-minute break."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(8, 0),
                    end=time(17, 30),
                    pause=timedelta(minutes=30),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME


class TestCheckRestPeriod:
    """Test suite for _check_rest_period method."""

    def test_returns_none_for_sufficient_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test no violation when rest period is sufficient."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None

    def test_detects_insufficient_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test detection of insufficient rest period."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(22, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(14, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is not None
        assert violation.type == ViolationType.REST_PERIOD
        assert "8:00:00" in violation.details

    def test_returns_violation_for_open_ended_previous_log(
        self,
        statistics_service: StatisticsService,
        work_entry_open_ended: CalendarEntry,
        work_entry_standard: CalendarEntry,
    ) -> None:
        """Test violation when previous entry has open-ended log."""
        violation = statistics_service._check_rest_period(
            work_entry_open_ended, work_entry_standard
        )

        assert violation is not None
        assert violation.type == ViolationType.REST_PERIOD
        assert "open-ended" in violation.details

    def test_returns_none_when_previous_has_no_work_logs(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test no violation when previous entry has no work logs."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None

    def test_returns_none_when_current_has_no_work_logs(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test no violation when current entry has no work logs."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None

    def test_checks_exact_minimum_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exact 11-hour rest period is acceptable."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(18, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(5, 0),
                    end=time(13, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None

    def test_uses_custom_rest_period_configuration(
        self,
        custom_statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        weekday_date: date,
    ) -> None:
        """Test custom rest period configuration affects violation detection."""
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(5, 0),
                    end=time(14, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = custom_statistics_service._check_rest_period(
            work_entry_standard, current
        )

        assert violation is not None
        assert violation.type == ViolationType.REST_PERIOD

    def test_uses_last_work_log_of_previous_day(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test uses last work log when previous day has multiple logs."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(8, 0),
                    end=time(12, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(13, 0),
                    end=time(22, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(14, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is not None

    def test_uses_first_work_log_of_current_day(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test uses first work log when current day has multiple logs."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(22, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(10, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(14, 0),
                    end=time(18, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is not None

    def test_ignores_travel_logs_in_rest_period_calculation(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test travel logs are ignored in rest period calculation."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.TRAVEL,
                    start=time(17, 30),
                    end=time(18, 30),
                    pause=timedelta(0),
                ),
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.TRAVEL,
                    start=time(8, 0),
                    end=time(9, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None


class TestComplianceCheck:
    """Test suite for compliance_check method."""

    def test_returns_empty_list_for_non_work_entry(
        self,
        statistics_service: StatisticsService,
        vacation_entry: CalendarEntry,
    ) -> None:
        """Test no violations for non-work entry type."""
        violations = statistics_service.compliance_check(vacation_entry)

        assert violations == []

    def test_checks_daily_compliance_without_previous_entry(
        self,
        statistics_service: StatisticsService,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test daily compliance check without previous entry."""
        violations = statistics_service.compliance_check(work_entry_overtime)

        assert len(violations) >= 1
        assert any(v.type == ViolationType.MAX_HOURS for v in violations)

    def test_checks_both_daily_and_rest_period_compliance(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test both daily and rest period compliance checks."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(22, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(20, 0),
                    pause=timedelta(minutes=30),
                )
            ],
        )
        violations = statistics_service.compliance_check(current, previous)

        assert len(violations) >= 2
        violation_types = {v.type for v in violations}
        assert ViolationType.MAX_HOURS in violation_types
        assert ViolationType.REST_PERIOD in violation_types

    def test_returns_empty_list_for_fully_compliant_entries(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        weekday_date: date,
    ) -> None:
        """Test no violations for fully compliant entries."""
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
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
        violations = statistics_service.compliance_check(current, work_entry_standard)

        assert violations == []

    def test_handles_none_previous_entry(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
    ) -> None:
        """Test handling of None previous entry."""
        violations = statistics_service.compliance_check(work_entry_standard, None)

        assert violations == []


class TestCalculateStatistics:
    """Test suite for calculate_statistics method."""

    def test_calculates_statistics_for_empty_list(
        self, statistics_service: StatisticsService
    ) -> None:
        """Test statistics calculation for empty entry list."""
        stats = statistics_service.calculate_statistics([])

        assert stats.entry_counts.work == 0
        assert stats.entry_counts.vacation == 0
        assert stats.total_work_hours == timedelta(0)
        assert stats.flextime_balance == timedelta(0)
        assert stats.compliance_violations == []

    def test_counts_work_entries_correctly(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        weekday_date: date,
    ) -> None:
        """Test correct counting of work entries."""
        entries = [
            work_entry_standard,
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 2

    def test_counts_vacation_entries_correctly(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test correct counting of vacation entries."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.VACATION, logs=[]),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.vacation == 2

    def test_counts_holiday_entries_correctly(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test correct counting of holiday entries."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.HOLIDAY, logs=[]),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.HOLIDAY,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.holiday == 2

    def test_counts_sick_entries_correctly(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test correct counting of sick entries."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.SICK, logs=[]),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.sick == 1

    def test_counts_flextime_entries_correctly(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test correct counting of flextime entries."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.FLEXTIME, logs=[]),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.flex_days == 1

    def test_counts_travel_days_correctly(
        self,
        statistics_service: StatisticsService,
        work_entry_with_travel: CalendarEntry,
    ) -> None:
        """Test correct counting of days with travel."""
        stats = statistics_service.calculate_statistics([work_entry_with_travel])

        assert stats.entry_counts.travel == 1

    def test_calculates_total_work_hours_correctly(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        weekday_date: date,
    ) -> None:
        """Test correct calculation of total work hours."""
        entries = [
            work_entry_standard,
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(15, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.total_work_hours == timedelta(hours=14)

    def test_calculates_flextime_balance_correctly(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test correct calculation of flextime balance."""
        stats = statistics_service.calculate_statistics(
            [work_entry_standard, work_entry_overtime]
        )

        assert stats.flextime_balance == timedelta(hours=2, minutes=30)

    def test_detects_compliance_violations(
        self,
        statistics_service: StatisticsService,
        work_entry_overtime: CalendarEntry,
    ) -> None:
        """Test detection of compliance violations during calculation."""
        stats = statistics_service.calculate_statistics([work_entry_overtime])

        assert len(stats.compliance_violations) >= 1

    def test_handles_mixed_entry_types(
        self,
        statistics_service: StatisticsService,
        work_entry_standard: CalendarEntry,
        vacation_entry: CalendarEntry,
        weekday_date: date,
    ) -> None:
        """Test handling of mixed entry types."""
        entries = [
            work_entry_standard,
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=2),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 2
        assert stats.entry_counts.vacation == 1

    def test_ignores_entries_without_duration(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test proper handling of entries without duration."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.total_work_hours == timedelta(0)

    def test_calculates_negative_flextime_balance(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test calculation of negative flextime balance."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(15, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.flextime_balance == timedelta(hours=-2)

    def test_checks_rest_period_between_consecutive_work_days(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test rest period checking between consecutive work days."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(22, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(6, 0),
                        end=time(14, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        rest_violations = [
            v
            for v in stats.compliance_violations
            if v.type == ViolationType.REST_PERIOD
        ]
        assert len(rest_violations) > 0

    def test_does_not_check_rest_period_for_non_consecutive_work_days(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test rest period not checked for non-consecutive work days."""
        entries = [
            CalendarEntry(
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
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=2),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 30),
                        pause=timedelta(minutes=30),
                    )
                ],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.compliance_violations == []

    def test_counts_multiple_entry_types_in_single_calculation(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test counting of multiple entry types in single calculation."""
        entries = [
            CalendarEntry(day=weekday_date, type=CalendarEntryType.WORK, logs=[]),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=2),
                type=CalendarEntryType.HOLIDAY,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=3),
                type=CalendarEntryType.SICK,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=4),
                type=CalendarEntryType.FLEXTIME,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 1
        assert stats.entry_counts.vacation == 1
        assert stats.entry_counts.holiday == 1
        assert stats.entry_counts.sick == 1
        assert stats.entry_counts.flex_days == 1

    def test_uses_custom_configuration_in_calculation(
        self, custom_statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test custom configuration affects statistics calculation."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
        ]
        stats = custom_statistics_service.calculate_statistics(entries)

        assert stats.flextime_balance == timedelta(minutes=30)


class TestViolationTypeEnum:
    """Test suite for ViolationType enum."""

    def test_has_max_hours_violation_type(self) -> None:
        """Test MAX_HOURS violation type exists."""
        assert ViolationType.MAX_HOURS.value == "max_work_hours_exceeded"

    def test_has_all_required_violation_types(self) -> None:
        """Test all required violation types exist."""
        assert ViolationType.MAX_HOURS.value == "max_work_hours_exceeded"
        assert ViolationType.BREAK_TIME.value == "break_time_violation"
        assert ViolationType.REST_PERIOD.value == "insufficient_rest_period"


class TestComplianceViolationModel:
    """Test suite for ComplianceViolation model."""

    def test_creates_violation_with_all_fields(self) -> None:
        """Test violation creation with all required fields."""
        violation = ComplianceViolation(
            day=date(2024, 11, 18),
            type=ViolationType.MAX_HOURS,
            details="Worked too many hours",
        )

        assert violation.day == date(2024, 11, 18)
        assert violation.type == ViolationType.MAX_HOURS
        assert violation.details == "Worked too many hours"

    def test_validates_violation_model_structure(self) -> None:
        """Test violation model structure validation."""
        violation = ComplianceViolation(
            day=date(2024, 11, 18),
            type=ViolationType.BREAK_TIME,
            details="Insufficient break",
        )

        assert isinstance(violation.day, date)
        assert isinstance(violation.type, ViolationType)
        assert isinstance(violation.details, str)

    def test_creates_violation_for_each_type(self) -> None:
        """Test violation creation for each violation type."""
        test_date = date(2024, 11, 18)
        violations = [
            ComplianceViolation(
                day=test_date, type=ViolationType.MAX_HOURS, details="Max hours"
            ),
            ComplianceViolation(
                day=test_date, type=ViolationType.BREAK_TIME, details="Break time"
            ),
            ComplianceViolation(
                day=test_date, type=ViolationType.REST_PERIOD, details="Rest period"
            ),
        ]

        assert len(violations) == 3
        assert all(isinstance(v, ComplianceViolation) for v in violations)


class TestTypeCountModel:
    """Test suite for TypeCount model."""

    def test_creates_type_count_with_default_values(self) -> None:
        """Test TypeCount creation with default zero values."""
        counts = TypeCount()

        assert counts.work == 0
        assert counts.flex_days == 0
        assert counts.vacation == 0
        assert counts.holiday == 0
        assert counts.sick == 0
        assert counts.travel == 0

    def test_creates_type_count_with_custom_values(self) -> None:
        """Test TypeCount creation with custom values."""
        counts = TypeCount(work=5, flex_days=2, vacation=3, holiday=1, sick=1, travel=2)

        assert counts.work == 5
        assert counts.flex_days == 2
        assert counts.vacation == 3
        assert counts.holiday == 1
        assert counts.sick == 1
        assert counts.travel == 2


class TestStatisticsModel:
    """Test suite for Statistics model."""

    def test_creates_statistics_with_all_fields(self) -> None:
        """Test Statistics creation with all required fields."""
        stats = Statistics(
            entry_counts=TypeCount(work=5),
            total_work_hours=timedelta(hours=40),
            flextime_balance=timedelta(0),
            compliance_violations=[],
        )

        assert stats.entry_counts.work == 5
        assert stats.total_work_hours == timedelta(hours=40)
        assert stats.flextime_balance == timedelta(0)
        assert stats.compliance_violations == []

    def test_validates_statistics_model_structure(self) -> None:
        """Test Statistics model structure validation."""
        stats = Statistics(
            entry_counts=TypeCount(),
            total_work_hours=timedelta(hours=40),
            flextime_balance=timedelta(hours=-2),
            compliance_violations=[
                ComplianceViolation(
                    day=date(2024, 11, 18),
                    type=ViolationType.MAX_HOURS,
                    details="Test",
                )
            ],
        )

        assert isinstance(stats.entry_counts, TypeCount)
        assert isinstance(stats.total_work_hours, timedelta)
        assert isinstance(stats.flextime_balance, timedelta)
        assert isinstance(stats.compliance_violations, list)


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_handles_very_long_workday(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of very long workday (16+ hours)."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(23, 0),
                    pause=timedelta(hours=1),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) >= 1
        assert any(v.type == ViolationType.MAX_HOURS for v in violations)

    def test_handles_midnight_crossing_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test rest period calculation across midnight."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(14, 0),
                    end=time(23, 59),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(0, 0),
                    end=time(8, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is not None
        assert violation.type == ViolationType.REST_PERIOD

    def test_handles_one_minute_work_duration(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of one-minute work duration."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(9, 1),
                    pause=timedelta(0),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert violations == []

    def test_handles_exactly_max_work_hours(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exactly max work hours does not violate."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(8, 0),
                    end=time(18, 30),
                    pause=timedelta(minutes=30),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        max_hours_violations = [
            v for v in violations if v.type == ViolationType.MAX_HOURS
        ]
        assert len(max_hours_violations) == 0

    def test_handles_one_second_over_max_work_hours(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test one second over max work hours triggers violation."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(8, 0),
                    end=time(18, 30),
                    pause=timedelta(minutes=29, seconds=59),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        max_hours_violations = [
            v for v in violations if v.type == ViolationType.MAX_HOURS
        ]
        assert len(max_hours_violations) == 1

    def test_handles_exactly_minimum_break_duration(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exactly 30-minute break at 6-hour threshold is acceptable."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(15, 30),
                    pause=timedelta(minutes=30),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert violations == []

    def test_handles_one_minute_less_than_required_break(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test one minute less than required break triggers violation."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(15, 59),
                    pause=timedelta(minutes=29),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 1
        assert violations[0].type == ViolationType.BREAK_TIME

    def test_handles_exactly_minimum_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test exactly 11-hour rest period is acceptable."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(20, 0),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(7, 0),
                    end=time(15, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is None

    def test_handles_one_minute_less_than_minimum_rest_period(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test one minute less than minimum rest period triggers violation."""
        previous = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(20, 1),
                    pause=timedelta(0),
                )
            ],
        )
        current = CalendarEntry(
            day=weekday_date + timedelta(days=1),
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(7, 0),
                    end=time(15, 0),
                    pause=timedelta(0),
                )
            ],
        )
        violation = statistics_service._check_rest_period(previous, current)

        assert violation is not None
        assert violation.type == ViolationType.REST_PERIOD

    def test_handles_work_entry_with_only_travel_logs(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test work entry with only travel logs has zero work duration."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.TRAVEL,
                    start=time(8, 0),
                    end=time(10, 0),
                    pause=timedelta(0),
                )
            ],
        )
        stats = statistics_service.calculate_statistics([entry])

        assert stats.total_work_hours == timedelta(0)

    def test_handles_multiple_violations_in_single_day(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test multiple violations detected in single day."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(6, 0),
                    end=time(22, 0),
                    pause=timedelta(minutes=15),
                )
            ],
        )
        violations = statistics_service._check_daily_compliance(entry)

        assert len(violations) == 2
        violation_types = {v.type for v in violations}
        assert ViolationType.MAX_HOURS in violation_types
        assert ViolationType.BREAK_TIME in violation_types

    def test_handles_large_number_of_entries(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of large number of entries (100+ days)."""
        entries = [
            CalendarEntry(
                day=weekday_date + timedelta(days=i),
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 0),
                        pause=timedelta(0),
                    )
                ],
            )
            for i in range(100)
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 100
        assert stats.total_work_hours == timedelta(hours=800)

    def test_handles_alternating_work_and_vacation_days(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of alternating work and vacation days."""
        entries = []
        for i in range(10):
            if i % 2 == 0:
                entries.append(
                    CalendarEntry(
                        day=weekday_date + timedelta(days=i),
                        type=CalendarEntryType.WORK,
                        logs=[
                            TimeLog(
                                type=TimeLogType.WORK,
                                start=time(9, 0),
                                end=time(17, 0),
                                pause=timedelta(0),
                            )
                        ],
                    )
                )
            else:
                entries.append(
                    CalendarEntry(
                        day=weekday_date + timedelta(days=i),
                        type=CalendarEntryType.VACATION,
                        logs=[],
                    )
                )
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 5
        assert stats.entry_counts.vacation == 5

    def test_handles_flextime_entry_affecting_balance(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test flextime entry properly affects flextime balance."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(19, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.FLEXTIME,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.flextime_balance == timedelta(hours=-6)

    def test_handles_consecutive_flextime_entries(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test handling of consecutive flextime entries."""
        entries = [
            CalendarEntry(
                day=weekday_date + timedelta(days=i),
                type=CalendarEntryType.FLEXTIME,
                logs=[],
            )
            for i in range(3)
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.flex_days == 3
        assert stats.flextime_balance == timedelta(hours=-24)

    def test_handles_work_day_with_multiple_work_and_travel_logs(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test day with multiple work and travel logs mixed."""
        entry = CalendarEntry(
            day=weekday_date,
            type=CalendarEntryType.WORK,
            logs=[
                TimeLog(
                    type=TimeLogType.TRAVEL,
                    start=time(8, 0),
                    end=time(9, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(9, 0),
                    end=time(12, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.TRAVEL,
                    start=time(12, 0),
                    end=time(13, 0),
                    pause=timedelta(0),
                ),
                TimeLog(
                    type=TimeLogType.WORK,
                    start=time(13, 0),
                    end=time(17, 0),
                    pause=timedelta(0),
                ),
            ],
        )
        stats = statistics_service.calculate_statistics([entry])

        assert stats.entry_counts.travel == 1
        assert stats.total_work_hours == timedelta(hours=7)

    def test_handles_all_entry_types_in_week(
        self, statistics_service: StatisticsService, weekday_date: date
    ) -> None:
        """Test week containing all possible entry types."""
        entries = [
            CalendarEntry(
                day=weekday_date,
                type=CalendarEntryType.WORK,
                logs=[
                    TimeLog(
                        type=TimeLogType.WORK,
                        start=time(9, 0),
                        end=time(17, 0),
                        pause=timedelta(0),
                    )
                ],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=1),
                type=CalendarEntryType.FLEXTIME,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=2),
                type=CalendarEntryType.VACATION,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=3),
                type=CalendarEntryType.HOLIDAY,
                logs=[],
            ),
            CalendarEntry(
                day=weekday_date + timedelta(days=4),
                type=CalendarEntryType.SICK,
                logs=[],
            ),
        ]
        stats = statistics_service.calculate_statistics(entries)

        assert stats.entry_counts.work == 1
        assert stats.entry_counts.flex_days == 1
        assert stats.entry_counts.vacation == 1
        assert stats.entry_counts.holiday == 1
        assert stats.entry_counts.sick == 1
