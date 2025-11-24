"""Test suite for display service."""

from datetime import date, time, timedelta

import pytest

from app.services.display import DisplayService, _timedelta_to_str


class TestTimedeltaToStr:
    """Test suite for _timedelta_to_str helper function."""

    @pytest.mark.parametrize(
        "delta,expected",
        [
            (timedelta(hours=0, minutes=0), "00:00"),
            (timedelta(hours=1, minutes=30), "01:30"),
            (timedelta(hours=8, minutes=0), "08:00"),
            (timedelta(hours=23, minutes=59), "23:59"),
            (timedelta(hours=24, minutes=0), "24:00"),
            (timedelta(hours=30, minutes=45), "30:45"),
            (timedelta(hours=0, minutes=5), "00:05"),
            (timedelta(hours=0, minutes=45), "00:45"),
            (timedelta(seconds=90), "00:01"),
            (timedelta(seconds=3661), "01:01"),
            (timedelta(hours=100, minutes=30), "100:30"),
        ],
        ids=[
            "zero_duration",
            "standard_duration",
            "eight_hours",
            "end_of_day",
            "exactly_24_hours",
            "over_24_hours",
            "only_five_minutes",
            "only_45_minutes",
            "seconds_rounded_down",
            "hour_with_seconds",
            "three_digit_hours",
        ],
    )
    def test_formats_timedelta_to_string(self, delta: timedelta, expected: str) -> None:
        """Test timedelta formatting to HH:MM string."""
        result = _timedelta_to_str(delta)
        assert result == expected


class TestIsWeekend:
    """Test suite for DisplayService.is_weekend."""

    @pytest.mark.parametrize(
        "test_date,expected",
        [
            (date(2024, 11, 18), False),
            (date(2024, 11, 19), False),
            (date(2024, 11, 20), False),
            (date(2024, 11, 21), False),
            (date(2024, 11, 22), False),
            (date(2024, 11, 23), True),
            (date(2024, 11, 24), True),
            (date(2024, 1, 1), False),
            (date(2024, 2, 29), False),
            (date(2024, 12, 31), False),
        ],
        ids=[
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "new_year_monday",
            "leap_day_thursday",
            "year_end_tuesday",
        ],
    )
    def test_detects_weekend_correctly(self, test_date: date, expected: bool) -> None:
        """Test weekend detection for various days of the week."""
        result = DisplayService.is_weekend(test_date)
        assert result == expected


class TestGetWeekdayName:
    """Test suite for DisplayService.get_weekday_name."""

    @pytest.mark.parametrize(
        "test_date,expected",
        [
            (date(2024, 11, 18), "Monday"),
            (date(2024, 11, 19), "Tuesday"),
            (date(2024, 11, 20), "Wednesday"),
            (date(2024, 11, 21), "Thursday"),
            (date(2024, 11, 22), "Friday"),
            (date(2024, 11, 23), "Saturday"),
            (date(2024, 11, 24), "Sunday"),
            (date(2024, 1, 1), "Monday"),
            (date(2024, 2, 29), "Thursday"),
            (date(2024, 12, 25), "Wednesday"),
        ],
        ids=[
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "new_year",
            "leap_day",
            "christmas",
        ],
    )
    def test_returns_weekday_name(self, test_date: date, expected: str) -> None:
        """Test weekday name extraction for all days of the week."""
        result = DisplayService.get_weekday_name(test_date)
        assert result == expected


class TestMonthName:
    """Test suite for DisplayService.month_name."""

    @pytest.mark.parametrize(
        "test_date,expected",
        [
            (date(2024, 1, 15), "January 2024"),
            (date(2024, 2, 1), "February 2024"),
            (date(2024, 3, 31), "March 2024"),
            (date(2024, 4, 10), "April 2024"),
            (date(2024, 5, 20), "May 2024"),
            (date(2024, 6, 15), "June 2024"),
            (date(2024, 7, 4), "July 2024"),
            (date(2024, 8, 25), "August 2024"),
            (date(2024, 9, 30), "September 2024"),
            (date(2024, 10, 1), "October 2024"),
            (date(2024, 11, 18), "November 2024"),
            (date(2024, 12, 25), "December 2024"),
            (date(2025, 6, 15), "June 2025"),
            (date(2023, 11, 18), "November 2023"),
            (date(2024, 2, 29), "February 2024"),
        ],
        ids=[
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "different_year",
            "previous_year",
            "leap_year_february",
        ],
    )
    def test_formats_month_and_year(self, test_date: date, expected: str) -> None:
        """Test month and year formatting for all months."""
        result = DisplayService.month_name(test_date)
        assert result == expected


class TestFormatTime:
    """Test suite for DisplayService.format_time."""

    @pytest.mark.parametrize(
        "test_time,expected",
        [
            (time(0, 0), "00:00"),
            (time(9, 0), "09:00"),
            (time(12, 30), "12:30"),
            (time(17, 45), "17:45"),
            (time(23, 59), "23:59"),
            (time(1, 5), "01:05"),
            (time(0, 1), "00:01"),
            (time(12, 0), "12:00"),
            (time(15, 15), "15:15"),
            (None, ""),
        ],
        ids=[
            "midnight",
            "morning",
            "afternoon",
            "evening",
            "end_of_day",
            "early_morning",
            "one_minute_past_midnight",
            "noon",
            "quarter_past_three",
            "none_value",
        ],
    )
    def test_formats_time_to_string(
        self, test_time: time | None, expected: str
    ) -> None:
        """Test time formatting with various times including None."""
        result = DisplayService.format_time(test_time)
        assert result == expected

    def test_returns_empty_string_for_none(self) -> None:
        """Test that None returns empty string."""
        result = DisplayService.format_time(None)
        assert result == ""


class TestFormatTimedelta:
    """Test suite for DisplayService.format_timedelta."""

    @pytest.mark.parametrize(
        "duration,expected",
        [
            (timedelta(hours=0, minutes=0), "00:00"),
            (timedelta(hours=1, minutes=30), "01:30"),
            (timedelta(hours=8, minutes=0), "08:00"),
            (timedelta(hours=23, minutes=59), "23:59"),
            (timedelta(hours=24, minutes=0), "24:00"),
            (timedelta(hours=-1, minutes=-30), "-01:30"),
            (timedelta(hours=-8, minutes=0), "-08:00"),
            (timedelta(hours=-23, minutes=-59), "-23:59"),
            (timedelta(seconds=-3661), "-01:01"),
            (timedelta(hours=0, minutes=5), "00:05"),
            (timedelta(hours=0, minutes=45), "00:45"),
            (timedelta(hours=30, minutes=15), "30:15"),
            (timedelta(seconds=90), "00:01"),
            (timedelta(seconds=3661), "01:01"),
            (None, ""),
            (timedelta(hours=-0, minutes=-5), "-00:05"),
            (timedelta(hours=-30, minutes=-45), "-30:45"),
            (timedelta(hours=100, minutes=0), "100:00"),
        ],
        ids=[
            "zero_duration",
            "positive_standard",
            "eight_hours",
            "end_of_day_duration",
            "exactly_24_hours",
            "negative_standard",
            "negative_eight_hours",
            "negative_end_of_day",
            "negative_with_seconds",
            "five_minutes",
            "45_minutes",
            "over_24_hours",
            "seconds_rounded_down",
            "hour_with_seconds",
            "none_value",
            "negative_five_minutes",
            "negative_over_24_hours",
            "three_digit_hours",
        ],
    )
    def test_formats_duration_to_string(
        self, duration: timedelta | None, expected: str
    ) -> None:
        """Test duration formatting including negative values and None."""
        result = DisplayService.format_timedelta(duration)
        assert result == expected
