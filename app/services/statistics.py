from collections.abc import Iterable
from datetime import date, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field

from app.model import (
    CalendarEntry,
    CalendarEntryType,
    TimeLogType,
)


class ViolationType(StrEnum):
    """Types of compliance violations that can occur."""

    MAX_HOURS = "max_work_hours_exceeded"
    BREAK_TIME = "break_time_violation"
    REST_PERIOD = "insufficient_rest_period"


class ComplianceViolation(BaseModel):
    """Represents a single compliance violation."""

    day: date
    type: ViolationType
    details: str


class TypeCount(BaseModel):
    """Count of different calendar entry types."""

    work: int = 0
    flex_days: int = 0
    vacation: int = 0
    holiday: int = 0
    sick: int = 0
    travel: int = 0


class Statistics(BaseModel):
    """Complete statistics for calendar entries."""

    entry_counts: TypeCount
    total_work_hours: timedelta
    flextime_balance: timedelta
    compliance_violations: list[ComplianceViolation]


class StatisticsConfiguration(BaseModel):
    """Configuration for statistics calculation."""

    standard_work_hours: timedelta = Field(default=timedelta(hours=8))
    max_work_hours: timedelta = Field(default=timedelta(hours=10))
    min_break_threshold: timedelta = Field(default=timedelta(hours=6))
    min_break_duration: timedelta = Field(default=timedelta(minutes=30))
    max_break_threshold: timedelta = Field(default=timedelta(hours=9))
    max_break_duration: timedelta = Field(default=timedelta(minutes=45))
    min_rest_period: timedelta = Field(default=timedelta(hours=11))


class StatisticsService:
    """Service for calculating statistics from calendar entries."""

    def __init__(self, config: StatisticsConfiguration):
        """Initialize the statistics service with configuration settings.

        Args:
            config (StatisticsConfiguration): Configuration object containing work hour rules
                and compliance thresholds.
        """
        self.config = config

    def calculate_flextime(self, entry: CalendarEntry) -> timedelta | None:
        """Calculate the flextime of the entry.

        Args:
            entry (CalendarEntry): entry to calculate the flextime.

        Returns:
            timedelta | None: flextime balance if available.
        """
        if (
            entry.type not in {CalendarEntryType.WORK, CalendarEntryType.FLEXTIME}
            or entry.duration is None
        ):
            return None

        if entry.type == CalendarEntryType.FLEXTIME:
            return -self.config.standard_work_hours

        return entry.duration - self.config.standard_work_hours

    def compliance_check(
        self, entry: CalendarEntry, previous_entry: CalendarEntry | None = None
    ) -> list[ComplianceViolation]:
        """Check calendar entry for compliance violations.

        Args:
            entry (CalendarEntry): The calendar entry to check for violations
            previous_entry (CalendarEntry | None, optional): Previous day's entry for
                checking rest period violations. Defaults to None.

        Returns:
            list[ComplianceViolation]: List of detected compliance violations
        """
        violations: list[ComplianceViolation] = []
        if entry.type != CalendarEntryType.WORK:
            return violations

        violations.extend(self._check_daily_compliance(entry))
        if previous_entry:
            rest_violation = self._check_rest_period(previous_entry, entry)
            if rest_violation:
                violations.append(rest_violation)
        return violations

    def calculate_statistics(self, entries: Iterable[CalendarEntry]) -> Statistics:
        """Calculate comprehensive statistics in a single pass through entries.

        Args:
            entries (Sequence[CalendarEntry]): Sequence of calendar entries to analyze.

        Returns:
            Statistics: Complete statistics including entry counts, work hours,
                flextime balance and compliance violations.
        """
        type_counts = TypeCount()
        total_work_time = timedelta(0)
        work_days = 0
        violations: list[ComplianceViolation] = []
        previous_entry: CalendarEntry | None = None

        for entry in entries:
            # Count entry types
            match entry.type:
                case CalendarEntryType.WORK:
                    type_counts.work += 1
                case CalendarEntryType.FLEXTIME:
                    type_counts.flex_days += 1
                case CalendarEntryType.VACATION:
                    type_counts.vacation += 1
                case CalendarEntryType.HOLIDAY:
                    type_counts.holiday += 1
                case CalendarEntryType.SICK:
                    type_counts.sick += 1

            # Count travel days
            if any(log.type == TimeLogType.TRAVEL for log in entry.logs):
                type_counts.travel += 1

            # Calculate work time and check compliance
            if entry.type in {CalendarEntryType.WORK, CalendarEntryType.FLEXTIME}:
                work_days += 1
                if entry.duration:
                    total_work_time += entry.duration
                    violations.extend(self.compliance_check(entry, previous_entry))

            previous_entry = entry

        # Calculate flextime balance
        expected_work = work_days * self.config.standard_work_hours
        flextime_balance = total_work_time - expected_work

        return Statistics(
            entry_counts=type_counts,
            total_work_hours=total_work_time,
            flextime_balance=flextime_balance,
            compliance_violations=violations,
        )

    def _check_daily_compliance(
        self, entry: CalendarEntry
    ) -> list[ComplianceViolation]:
        """Check all daily compliance rules in one go.

        Args:
            entry (CalendarEntry): Calendar entry to check.

        Returns:
            list[ComplianceViolation]: List of detected violations.
        """
        violations = []
        daily_work = entry.duration or timedelta(0)
        break_duration = entry.pause_time or timedelta(0)

        # Check maximum work hours
        if daily_work > self.config.max_work_hours:
            violations.append(
                ComplianceViolation(
                    day=entry.day,
                    type=ViolationType.MAX_HOURS,
                    details=f"Worked {daily_work} exceeding maximum of {self.config.max_work_hours}",
                )
            )

        # Check break requirements
        if daily_work >= self.config.max_break_threshold:
            if break_duration < self.config.max_break_duration:
                violations.append(
                    ComplianceViolation(
                        day=entry.day,
                        type=ViolationType.BREAK_TIME,
                        details=f"Insufficient extended break {break_duration} for duration {daily_work}",
                    )
                )
        elif daily_work >= self.config.min_break_threshold:
            if break_duration < self.config.min_break_duration:
                violations.append(
                    ComplianceViolation(
                        day=entry.day,
                        type=ViolationType.BREAK_TIME,
                        details=f"Insufficient break {break_duration} for duration {daily_work}",
                    )
                )

        return violations

    def _check_rest_period(
        self, previous_entry: CalendarEntry, current_entry: CalendarEntry
    ) -> ComplianceViolation | None:
        """Check if minimum rest period between work days is maintained.

        Args:
            previous_entry (CalendarEntry): Previous day's calendar entry.
            current_entry (CalendarEntry): Current day's calendar entry.

        Returns:
            ComplianceViolation | None: Violation if rest period is insufficient
                or cannot be determined, None otherwise.
        """
        previous_work_logs = [
            log for log in previous_entry.logs if log.type == TimeLogType.WORK
        ]
        current_work_logs = [
            log for log in current_entry.logs if log.type == TimeLogType.WORK
        ]

        if previous_work_logs and current_work_logs:
            last_log = previous_work_logs[-1]
            first_log = current_work_logs[0]

            if last_log.end is None:
                return ComplianceViolation(
                    day=previous_entry.day,
                    type=ViolationType.REST_PERIOD,
                    details="Cannot check rest period: Previous work day has an open-ended work log",
                )
            else:
                previous_end_time = datetime.combine(previous_entry.day, last_log.end)
                current_start_time = datetime.combine(
                    current_entry.day, first_log.start
                )
                rest_period = current_start_time - previous_end_time

                if rest_period < self.config.min_rest_period:
                    return ComplianceViolation(
                        day=current_entry.day,
                        type=ViolationType.REST_PERIOD,
                        details=f"Rest period of {rest_period} is less than required {self.config.min_rest_period}",
                    )

        return None
