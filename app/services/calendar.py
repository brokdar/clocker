import logging
from calendar import FRIDAY, monthrange
from collections.abc import Iterator
from datetime import date, timedelta

import holidays

from app.database import CalendarRepository
from app.model import (
    CalendarEntry,
    CalendarEntryType,
)

logger = logging.getLogger(__name__)


def is_work_day(day: date) -> bool:
    """Checks if the day is a weekday.

    Args:
        day (date): day to be checked.

    Returns:
        bool: True if weekday, otherwise False.
    """
    return day.weekday() <= FRIDAY


def get_month_range(year: int, month: int) -> tuple[date, date]:
    """Returns the first and last date of the specified month.

    Args:
        year (int): year number.
        month (int): month number (1-12).

    Returns:
        tuple[date, date]: tuple containing first and last date of the month.
    """
    _, last_day_of_month = monthrange(year, month)
    return (date(year, month, 1), date(year, month, last_day_of_month))


class Calendar:
    """Calendar management service for handling work time entries.

    Provides functionality to create, read, update and delete calendar entries,
    as well as utilities for handling public holidays and date iterations.
    """

    def __init__(self, repository: CalendarRepository) -> None:
        """Initialize calendar service with a repository.

        Args:
            repository (CalendarRepository): Repository for calendar entry persistence.
        """
        self._repository = repository

    async def get_by_date(self, day: date) -> CalendarEntry | None:
        """Retrieve a calendar entry for a specific date.

        Args:
            day (date): The date to retrieve the entry for.

        Returns:
            CalendarEntry | None: The calendar entry if found, None otherwise.
        """
        return await self._repository.get_by_date(day)

    async def get_month(self, year: int, month: int) -> dict[date, CalendarEntry]:
        """Retrieve all calendar entries for a specific month.

        Args:
            year (int): The year to get entries for.
            month (int): The month to get entries for (1-12).

        Returns:
            dict[date, CalendarEntry]: Dictionary mapping dates to their entries.
        """
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        entries = await self._repository.get_by_date_range(start_date, end_date)
        logger.debug(
            f"Retrieved calendar entries of {year}/{month}", extra={"entries": entries}
        )
        return entries

    async def get_year(self, year: int) -> dict[date, CalendarEntry]:
        """Retrieve all calendar entries for an entire year.

        Args:
            year (int): The year to get entries for.

        Returns:
            dict[date, CalendarEntry]: Dictionary mapping dates to their entries.
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        entries = await self._repository.get_by_date_range(start_date, end_date)
        if not any(
            entry.type == CalendarEntryType.HOLIDAY for entry in entries.values()
        ):
            holiday_entries = await self.add_public_holidays(year, "BW")
            entries.update({entry.day: entry for entry in holiday_entries})

        logger.debug(
            f"Retrieved calendar entries of {year}", extra={"entries": entries}
        )
        return entries

    async def create_entry(self, day: date, type: CalendarEntryType) -> CalendarEntry:
        """Create a new calendar entry for a specific date.

        Args:
            day (date): The date for the new entry.
            type (CalendarEntryType): The type of entry to create.

        Raises:
            ValueError: If an entry already exists or if trying to create a work entry on a weekend.

        Returns:
            CalendarEntry: The newly created calendar entry.
        """
        if await self._repository.get_by_date(day):
            raise ValueError(f"Entry already exists for {day}")

        if type == CalendarEntryType.WORK and not is_work_day(day):
            raise ValueError("Cannot create work entry on weekend")

        entry = CalendarEntry(day=day, type=type, logs=[])
        return await self._repository.save(entry)

    async def create_entries(
        self, start: date, end: date, type: CalendarEntryType
    ) -> list[CalendarEntry]:
        """Create multiple calendar entries for a date range.

        Skips dates that already have entries and weekends for work entries.

        Args:
            start (date): Start date of the range (inclusive).
            end (date): End date of the range (inclusive).
            type (CalendarEntryType): The type of entries to create.

        Returns:
            list[CalendarEntry]: List of newly created calendar entries.
        """
        existing_entries = await self._repository.get_by_date_range(start, end)
        entries: list[CalendarEntry] = []

        for day in self.workdays(start, end):
            if day in existing_entries:
                continue
            if type == CalendarEntryType.WORK:
                continue
            entries.append(CalendarEntry(day=day, type=type, logs=[]))

        return await self._repository.save_all(entries)

    async def update_entry(self, entry: CalendarEntry) -> CalendarEntry:
        """Save changes to an existing calendar entry.

        Args:
            entry (CalendarEntry): The modified entry to save.

        Returns:
            CalendarEntry: The updated calendar entry.
        """
        return await self._repository.save(entry)

    async def reset_entry(self, entry: CalendarEntry) -> CalendarEntry:
        """Reset an entry to its last saved state.

        Args:
            entry (CalendarEntry): The entry to reset.

        Returns:
            CalendarEntry: The reset calendar entry.
        """
        return await self._repository.reset(entry)

    async def remove_entry(self, day: date) -> CalendarEntry:
        """Delete a calendar entry for a specific date.

        Args:
            day (date): The date of the entry to delete.

        Raises:
            ValueError: If no entry exists for the given date.

        Returns:
            CalendarEntry: The deleted calendar entry.
        """
        entry = await self._repository.get_by_date(day)
        if not entry:
            raise ValueError(f"Entry does not exist for {day}")

        await self._repository.delete(entry)
        logger.info(
            f"Removed calendar entry: {entry}", extra=entry.model_dump(mode="json")
        )

        return entry

    async def remove_entries(self, start: date, end: date) -> list[CalendarEntry]:
        """Delete all calendar entries within a date range.

        Args:
            start (date): Start date of the range (inclusive).
            end (date): End date of the range (inclusive).

        Returns:
            list[CalendarEntry]: List of deleted calendar entries.
        """
        existing_entries = await self._repository.get_by_date_range(start, end)
        if not existing_entries:
            return []

        entries_to_delete = list(existing_entries.values())
        await self._repository.delete_all(entries_to_delete)
        for entry in existing_entries.values():
            logger.info(
                f"Removed calendar entry: {entry}",
                extra=entry.model_dump(mode="json"),
            )

        return entries_to_delete

    async def add_public_holidays(self, year: int, state: str) -> list[CalendarEntry]:
        """Add German public holidays for a specific state and year.

        Existing holiday entries are skipped. Warns if trying to add a holiday
        on a date that already has a different type of entry.

        Args:
            year (int): The year to add holidays for.
            state (str): The German state code (e.g., 'BY' for Bavaria).

        Returns:
            list[CalendarEntry]: List of newly created holiday entries.
        """
        entries: list[CalendarEntry] = []
        holidays_dict = holidays.country_holidays("DE", state, year, language="de")

        for day, name in holidays_dict.items():
            existing = await self._repository.get_by_date(day)
            if existing:
                if existing.type != CalendarEntryType.HOLIDAY:
                    logger.warning(f"Cannot add holiday '{name}' to {day}")
                continue

            entry = CalendarEntry(day=day, type=CalendarEntryType.HOLIDAY, logs=[])
            entries.append(entry)

        return await self._repository.save_all(entries)

    def iterate(self, start: date, end: date) -> Iterator[date]:
        """Iterate over all dates in a range.

        Args:
            start (date): Start date of the range (inclusive).
            end (date): End date of the range (inclusive).

        Raises:
            ValueError: If end date is before start date.

        Yields:
            Iterator[date]: Each date in the range.
        """
        if end < start:
            raise ValueError(
                f"The end date ({end}) must not be before the start date ({start})"
            )

        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            yield day

    def workdays(self, start: date, end: date) -> Iterator[date]:
        """Iterate over workdays (Monday-Friday) in a date range.

        Args:
            start (date): Start date of the range (inclusive).
            end (date): End date of the range (inclusive).

        Yields:
            Iterator[date]: Each workday in the range.
        """
        for day in self.iterate(start, end):
            if is_work_day(day):
                yield day
