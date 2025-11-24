"""Test suite for time_logger service."""

from datetime import time, timedelta

import pytest

from app.model import CalendarEntry, TimeLogType
from app.services.time_logger import (
    TimeLogError,
    _validate_index,
    add_time_log,
    remove_time_log,
    update_time_log,
)


class TestValidateIndex:
    """Test suite for _validate_index helper function."""

    def test_validates_index_successfully(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test successful index validation with valid index."""
        _validate_index(work_entry_standard, 0)

    def test_raises_error_when_no_logs_exist(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when entry has no logs."""
        with pytest.raises(
            TimeLogError,
            match=f"No time logs found for {work_entry_empty.day}. Cannot access index 0.",
        ):
            _validate_index(work_entry_empty, 0)

    def test_raises_error_when_index_out_of_bounds(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when index exceeds log count."""
        with pytest.raises(
            TimeLogError,
            match=f"Invalid log index 5 - only 1 logs exist for {work_entry_standard.day}.",
        ):
            _validate_index(work_entry_standard, 5)

    def test_allows_negative_index(self, work_entry_standard: CalendarEntry) -> None:
        """Test negative index is allowed for accessing logs from end."""
        _validate_index(work_entry_standard, -1)


class TestAddTimeLog:
    """Test suite for add_time_log function."""

    def test_adds_work_log_to_empty_work_entry(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding work log to work entry with no logs."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
            pause=timedelta(minutes=30),
        )

        assert len(work_entry_empty.logs) == 1
        assert work_entry_empty.logs[0].type == TimeLogType.WORK
        assert work_entry_empty.logs[0].start == time(9, 0)
        assert work_entry_empty.logs[0].end == time(17, 0)
        assert work_entry_empty.logs[0].pause == timedelta(minutes=30)

    def test_adds_travel_log_to_work_entry(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding travel log to work entry."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.TRAVEL,
            start=time(8, 0),
            end=time(9, 0),
            pause=timedelta(0),
        )

        assert len(work_entry_empty.logs) == 1
        assert work_entry_empty.logs[0].type == TimeLogType.TRAVEL

    def test_adds_open_ended_work_log(self, work_entry_empty: CalendarEntry) -> None:
        """Test adding open-ended work log without end time."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=None,
            pause=timedelta(0),
        )

        assert len(work_entry_empty.logs) == 1
        assert work_entry_empty.logs[0].end is None

    def test_adds_log_with_zero_pause(self, work_entry_empty: CalendarEntry) -> None:
        """Test adding log with zero pause duration."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
        )

        assert work_entry_empty.logs[0].pause == timedelta(0)

    def test_adds_second_log_to_existing_logs(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test adding second log to entry with existing log."""
        add_time_log(
            work_entry_standard,
            type=TimeLogType.WORK,
            start=time(18, 0),
            end=time(20, 0),
            pause=timedelta(0),
        )

        assert len(work_entry_standard.logs) == 2

    @pytest.mark.parametrize(
        "entry_fixture",
        ["vacation_entry", "holiday_entry", "sick_entry", "flextime_entry"],
        ids=["vacation", "holiday", "sick", "flextime"],
    )
    def test_raises_error_when_adding_to_non_work_entry(
        self, entry_fixture: str, request: pytest.FixtureRequest
    ) -> None:
        """Test TimeLogError raised when adding log to non-work entry."""
        entry: CalendarEntry = request.getfixturevalue(entry_fixture)

        with pytest.raises(
            TimeLogError,
            match=f"Cannot add time log to {entry.type} entry. Only work entries accept time logs.",
        ):
            add_time_log(
                entry,
                type=TimeLogType.WORK,
                start=time(9, 0),
                end=time(17, 0),
            )

    def test_adds_log_with_start_after_end(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding log where start time is after end time succeeds."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(17, 0),
            end=time(9, 0),
        )

        assert len(work_entry_empty.logs) == 1

    def test_adds_log_with_pause_exceeding_duration(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding log where pause exceeds duration succeeds."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(10, 0),
            pause=timedelta(hours=2),
        )

        assert len(work_entry_empty.logs) == 1

    def test_adds_travel_log_with_no_end(self, work_entry_empty: CalendarEntry) -> None:
        """Test adding travel log without end time succeeds."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.TRAVEL,
            start=time(8, 0),
            end=None,
        )

        assert len(work_entry_empty.logs) == 1

    def test_raises_error_when_logs_overlap(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when adding overlapping log."""
        with pytest.raises(
            TimeLogError, match="Invalid time log data:.*Time logs overlap"
        ):
            add_time_log(
                work_entry_standard,
                type=TimeLogType.WORK,
                start=time(16, 0),
                end=time(18, 0),
            )

    def test_raises_error_when_multiple_open_ended_logs(
        self, work_entry_open_ended: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when adding second open-ended log."""
        with pytest.raises(
            TimeLogError,
            match="Invalid time log data:.*Multiple open-ended time logs detected",
        ):
            add_time_log(
                work_entry_open_ended,
                type=TimeLogType.WORK,
                start=time(13, 0),
                end=None,
            )

    def test_adds_log_with_minimal_valid_pause(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding log with minimal pause duration."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
            pause=timedelta(minutes=1),
        )

        assert work_entry_empty.logs[0].pause == timedelta(minutes=1)

    def test_adds_log_with_maximum_valid_pause(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding log with pause equal to duration."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
            pause=timedelta(hours=8),
        )

        assert work_entry_empty.logs[0].pause == timedelta(hours=8)

    def test_adds_multiple_non_overlapping_logs(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding multiple non-overlapping logs successfully."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(12, 0),
        )
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(13, 0),
            end=time(17, 0),
        )

        assert len(work_entry_empty.logs) == 2


class TestUpdateTimeLog:
    """Test suite for update_time_log function."""

    def test_updates_log_type_from_work_to_travel(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating log type from WORK to TRAVEL."""
        update_time_log(work_entry_standard, 0, type=TimeLogType.TRAVEL)

        assert work_entry_standard.logs[0].type == TimeLogType.TRAVEL

    def test_updates_start_time(self, work_entry_standard: CalendarEntry) -> None:
        """Test updating log start time."""
        update_time_log(work_entry_standard, 0, start=time(8, 0))

        assert work_entry_standard.logs[0].start == time(8, 0)

    def test_updates_end_time(self, work_entry_standard: CalendarEntry) -> None:
        """Test updating log end time."""
        update_time_log(work_entry_standard, 0, end=time(18, 0))

        assert work_entry_standard.logs[0].end == time(18, 0)

    def test_updates_pause_duration(self, work_entry_standard: CalendarEntry) -> None:
        """Test updating log pause duration."""
        update_time_log(work_entry_standard, 0, pause=timedelta(minutes=45))

        assert work_entry_standard.logs[0].pause == timedelta(minutes=45)

    def test_updates_multiple_fields_simultaneously(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating multiple fields in single call."""
        update_time_log(
            work_entry_standard,
            0,
            start=time(8, 0),
            end=time(18, 0),
            pause=timedelta(minutes=45),
        )

        assert work_entry_standard.logs[0].start == time(8, 0)
        assert work_entry_standard.logs[0].end == time(18, 0)
        assert work_entry_standard.logs[0].pause == timedelta(minutes=45)

    def test_updates_second_log_in_multiple_logs(
        self, work_entry_multiple_logs: CalendarEntry
    ) -> None:
        """Test updating second log when multiple logs exist."""
        update_time_log(work_entry_multiple_logs, 1, start=time(14, 0))

        assert work_entry_multiple_logs.logs[1].start == time(14, 0)

    def test_preserves_existing_type_when_none(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test existing type preserved when None passed."""
        original_type = work_entry_standard.logs[0].type
        update_time_log(work_entry_standard, 0, type=None, start=time(8, 0))

        assert work_entry_standard.logs[0].type == original_type

    def test_preserves_existing_start_when_none(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test existing start time preserved when None passed."""
        original_start = work_entry_standard.logs[0].start
        update_time_log(work_entry_standard, 0, start=None, end=time(18, 0))

        assert work_entry_standard.logs[0].start == original_start

    def test_preserves_existing_end_when_none(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test existing end time preserved when None passed."""
        original_end = work_entry_standard.logs[0].end
        update_time_log(work_entry_standard, 0, end=None, start=time(8, 0))

        assert work_entry_standard.logs[0].end == original_end

    def test_preserves_existing_pause_when_none(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test existing pause preserved when None passed."""
        original_pause = work_entry_standard.logs[0].pause
        update_time_log(work_entry_standard, 0, pause=None, start=time(8, 0))

        assert work_entry_standard.logs[0].pause == original_pause

    def test_raises_error_when_index_invalid(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when index out of bounds."""
        with pytest.raises(
            TimeLogError,
            match=f"Invalid log index 5 - only 1 logs exist for {work_entry_standard.day}.",
        ):
            update_time_log(work_entry_standard, 5, start=time(8, 0))

    def test_raises_error_when_no_logs_exist(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when entry has no logs."""
        with pytest.raises(
            TimeLogError,
            match=f"No time logs found for {work_entry_empty.day}. Cannot access index 0.",
        ):
            update_time_log(work_entry_empty, 0, start=time(9, 0))

    def test_updates_log_to_invalid_range(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating log to create invalid time range succeeds."""
        update_time_log(work_entry_standard, 0, start=time(20, 0))

        assert work_entry_standard.logs[0].start == time(20, 0)

    def test_updates_log_with_excessive_pause(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating log with pause exceeding duration succeeds."""
        update_time_log(work_entry_standard, 0, pause=timedelta(hours=10))

        assert work_entry_standard.logs[0].pause == timedelta(hours=10)

    def test_raises_error_when_update_causes_overlap(
        self, work_entry_multiple_logs: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when update creates overlapping logs."""
        with pytest.raises(
            TimeLogError, match="Invalid time log update:.*Time logs overlap"
        ):
            update_time_log(work_entry_multiple_logs, 0, end=time(14, 0))

    def test_updates_open_ended_log_to_closed(
        self, work_entry_open_ended: CalendarEntry
    ) -> None:
        """Test updating open-ended log to have end time."""
        update_time_log(work_entry_open_ended, 0, end=time(17, 0))

        assert work_entry_open_ended.logs[0].end == time(17, 0)

    def test_updates_open_ended_work_to_travel(
        self, work_entry_open_ended: CalendarEntry
    ) -> None:
        """Test updating open-ended work log to travel succeeds."""
        update_time_log(work_entry_open_ended, 0, type=TimeLogType.TRAVEL)

        assert work_entry_open_ended.logs[0].type == TimeLogType.TRAVEL


class TestRemoveTimeLog:
    """Test suite for remove_time_log function."""

    def test_removes_single_log_from_entry(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test removing only log from work entry."""
        remove_time_log(work_entry_standard, 0)

        assert len(work_entry_standard.logs) == 0

    def test_removes_first_log_from_multiple_logs(
        self, work_entry_multiple_logs: CalendarEntry
    ) -> None:
        """Test removing first log when multiple logs exist."""
        original_second_log = work_entry_multiple_logs.logs[1]
        remove_time_log(work_entry_multiple_logs, 0)

        assert len(work_entry_multiple_logs.logs) == 1
        assert work_entry_multiple_logs.logs[0].start == original_second_log.start

    def test_removes_second_log_from_multiple_logs(
        self, work_entry_multiple_logs: CalendarEntry
    ) -> None:
        """Test removing second log when multiple logs exist."""
        original_first_log = work_entry_multiple_logs.logs[0]
        remove_time_log(work_entry_multiple_logs, 1)

        assert len(work_entry_multiple_logs.logs) == 1
        assert work_entry_multiple_logs.logs[0].start == original_first_log.start

    def test_removes_open_ended_log(self, work_entry_open_ended: CalendarEntry) -> None:
        """Test removing open-ended log successfully."""
        remove_time_log(work_entry_open_ended, 0)

        assert len(work_entry_open_ended.logs) == 0

    def test_raises_error_when_index_invalid(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when index out of bounds."""
        with pytest.raises(
            TimeLogError,
            match=f"Invalid log index 5 - only 1 logs exist for {work_entry_standard.day}.",
        ):
            remove_time_log(work_entry_standard, 5)

    def test_raises_error_when_no_logs_exist(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test TimeLogError raised when entry has no logs."""
        with pytest.raises(
            TimeLogError,
            match=f"No time logs found for {work_entry_empty.day}. Cannot access index 0.",
        ):
            remove_time_log(work_entry_empty, 0)

    def test_removes_log_with_negative_index(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test removing log with negative index succeeds."""
        remove_time_log(work_entry_standard, -1)

        assert len(work_entry_standard.logs) == 0

    def test_removes_travel_log(self, work_entry_empty: CalendarEntry) -> None:
        """Test removing travel log successfully."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.TRAVEL,
            start=time(8, 0),
            end=time(9, 0),
        )
        remove_time_log(work_entry_empty, 0)

        assert len(work_entry_empty.logs) == 0

    def test_removes_log_with_pause(self, work_entry_standard: CalendarEntry) -> None:
        """Test removing log that has pause duration."""
        original_count = len(work_entry_standard.logs)
        remove_time_log(work_entry_standard, 0)

        assert len(work_entry_standard.logs) == original_count - 1

    def test_validates_remaining_logs_after_removal(
        self, work_entry_multiple_logs: CalendarEntry
    ) -> None:
        """Test remaining logs are validated after removal."""
        remove_time_log(work_entry_multiple_logs, 0)

        assert len(work_entry_multiple_logs.logs) == 1

    def test_removes_middle_log_from_three_logs(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test removing middle log from three logs."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(12, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(13, 0), time(15, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(16, 0), time(18, 0))

        remove_time_log(work_entry_empty, 1)

        assert len(work_entry_empty.logs) == 2
        assert work_entry_empty.logs[0].start == time(9, 0)
        assert work_entry_empty.logs[1].start == time(16, 0)

    def test_removes_last_log_from_three_logs(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test removing last log from three logs."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(12, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(13, 0), time(15, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(16, 0), time(18, 0))

        remove_time_log(work_entry_empty, 2)

        assert len(work_entry_empty.logs) == 2


class TestTimeLogError:
    """Test suite for TimeLogError exception."""

    def test_creates_error_with_message(self) -> None:
        """Test creating TimeLogError with custom message."""
        error = TimeLogError("Custom error message")

        assert str(error) == "Custom error message"

    def test_raises_error_with_match(self) -> None:
        """Test TimeLogError can be caught with pytest match."""
        with pytest.raises(TimeLogError, match="test message"):
            raise TimeLogError("test message")

    def test_inherits_from_exception(self) -> None:
        """Test TimeLogError inherits from Exception."""
        error = TimeLogError("test")

        assert isinstance(error, Exception)


class TestIntegration:
    """Test suite for integration scenarios."""

    def test_adds_updates_and_removes_log(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test complete workflow of adding, updating, and removing log."""
        add_time_log(
            work_entry_empty,
            type=TimeLogType.WORK,
            start=time(9, 0),
            end=time(17, 0),
            pause=timedelta(minutes=30),
        )
        assert len(work_entry_empty.logs) == 1

        update_time_log(work_entry_empty, 0, end=time(18, 0))
        assert work_entry_empty.logs[0].end == time(18, 0)

        remove_time_log(work_entry_empty, 0)
        assert len(work_entry_empty.logs) == 0

    def test_adds_multiple_logs_and_removes_specific(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding multiple logs and removing specific one."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(12, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(13, 0), time(17, 0))
        assert len(work_entry_empty.logs) == 2

        remove_time_log(work_entry_empty, 0)
        assert len(work_entry_empty.logs) == 1
        assert work_entry_empty.logs[0].start == time(13, 0)

    def test_adds_open_ended_updates_to_closed(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding open-ended log then updating to closed."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), end=None)
        assert work_entry_empty.logs[0].end is None

        update_time_log(work_entry_empty, 0, end=time(17, 0))
        assert work_entry_empty.logs[0].end == time(17, 0)

    def test_adds_work_and_travel_logs_together(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding both work and travel logs to same entry."""
        add_time_log(work_entry_empty, TimeLogType.TRAVEL, time(8, 0), time(9, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(17, 0))

        assert len(work_entry_empty.logs) == 2
        assert work_entry_empty.logs[0].type == TimeLogType.TRAVEL
        assert work_entry_empty.logs[1].type == TimeLogType.WORK


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_adds_log_at_midnight_start(self, work_entry_empty: CalendarEntry) -> None:
        """Test adding log starting at midnight."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(0, 0), time(8, 0))

        assert work_entry_empty.logs[0].start == time(0, 0)

    def test_adds_log_ending_at_midnight(self, work_entry_empty: CalendarEntry) -> None:
        """Test adding log ending at midnight."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(16, 0), time(23, 59))

        assert work_entry_empty.logs[0].end == time(23, 59)

    def test_adds_log_with_single_minute_duration(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding log with one minute duration."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(9, 1))

        assert len(work_entry_empty.logs) == 1

    def test_updates_log_to_minimum_duration(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating log to minimum valid duration."""
        update_time_log(work_entry_standard, 0, start=time(9, 0), end=time(9, 1))

        assert work_entry_standard.logs[0].end == time(9, 1)

    def test_adds_adjacent_logs_without_gap(
        self, work_entry_empty: CalendarEntry
    ) -> None:
        """Test adding logs that are adjacent with no gap."""
        add_time_log(work_entry_empty, TimeLogType.WORK, time(9, 0), time(12, 0))
        add_time_log(work_entry_empty, TimeLogType.WORK, time(12, 0), time(15, 0))

        assert len(work_entry_empty.logs) == 2

    def test_updates_log_preserves_all_none_parameters(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test updating with all None parameters preserves original."""
        original_start = work_entry_standard.logs[0].start
        original_end = work_entry_standard.logs[0].end

        update_time_log(
            work_entry_standard, 0, type=None, start=None, end=None, pause=None
        )

        assert work_entry_standard.logs[0].start == original_start
        assert work_entry_standard.logs[0].end == original_end

    def test_removes_and_re_adds_log_at_same_index(
        self, work_entry_standard: CalendarEntry
    ) -> None:
        """Test removing and re-adding log maintains entry integrity."""
        remove_time_log(work_entry_standard, 0)
        assert len(work_entry_standard.logs) == 0

        add_time_log(work_entry_standard, TimeLogType.WORK, time(10, 0), time(18, 0))
        assert len(work_entry_standard.logs) == 1
        assert work_entry_standard.logs[0].start == time(10, 0)
