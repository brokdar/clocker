from datetime import date, time, timedelta


def _timedelta_to_str(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}"


class DisplayService:
    """Utility service for formatting and displaying date/time values.

    Provides static methods for consistent date and time formatting across the application,
    including special handling for weekends and time duration displays.
    """

    @staticmethod
    def is_weekend(day: date) -> bool:
        """Check if a given date falls on a weekend.

        Args:
            day (date): The date to check.

        Returns:
            bool: True if the date is Saturday or Sunday, False otherwise.
        """
        return day.weekday() >= 5

    @staticmethod
    def get_weekday_name(day: date) -> str:
        """Get the full name of the weekday for a given date.

        Args:
            day (date): The date to get the weekday name for.

        Returns:
            str: Full weekday name (e.g., "Monday", "Tuesday", etc.).
        """
        return day.strftime("%A")

    @staticmethod
    def month_name(day: date) -> str:
        """Get the formatted month and year string for a given date.

        Args:
            day (date): The date to format.

        Returns:
            str: Formatted string like "January 2024".
        """
        return day.strftime("%B %Y")

    @staticmethod
    def format_time(time: time | None) -> str:
        """Format a time value in 24-hour format.

        Args:
            time (time | None): The time to format, or None.

        Returns:
            str: Time formatted as "HH:MM" or empty string if None.
        """
        if not time:
            return ""
        return time.strftime("%H:%M")

    @staticmethod
    def format_timedelta(duration: timedelta | None) -> str:
        """Format a duration in hours and minutes.

        Handles negative durations by adding a minus sign.

        Args:
            duration (timedelta | None): The duration to format, or None.

        Returns:
            str: Duration formatted as "HH:MM" or "-HH:MM" for negative values, empty string if None.
        """
        if duration is None:
            return ""

        if duration < timedelta(0):
            return f"-{_timedelta_to_str(-duration)}"
        return _timedelta_to_str(duration)
