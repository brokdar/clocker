from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from clocker.model import CalendarEntry

DATABASE_PATH = Path("/app/data/clocker.db")
DATABASE_URL = (
    f"sqlite+aiosqlite:///{DATABASE_PATH}"
    if DATABASE_PATH.parent.exists()
    else "sqlite+aiosqlite:///clocker.db"
)

engine = create_async_engine(DATABASE_URL, future=True)


class CalendarRepository:
    """Repository class for managing calendar entries in the database."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session (AsyncSession): The SQLAlchemy async session for database operations
        """
        self._session = session

    async def get_by_date(self, day: date) -> CalendarEntry | None:
        """Retrieve a calendar entry for a specific date.

        Args:
            day (date): The date to lookup

        Returns:
            CalendarEntry | None: The calendar entry if found, None otherwise
        """
        result = await self._session.get(CalendarEntry, day)
        return result

    async def get_by_date_range(
        self, start: date, end: date
    ) -> dict[date, CalendarEntry]:
        """Retrieve calendar entries within a date range.

        Args:
            start (date): The start date of the range (inclusive)
            end (date): The end date of the range (inclusive)

        Returns:
            dict[date, CalendarEntry]: Dictionary mapping dates to calendar entries
        """
        result = await self._session.exec(
            select(CalendarEntry)
            .where(CalendarEntry.day >= start)
            .where(CalendarEntry.day <= end)
        )
        return {entry.day: entry for entry in result}

    async def save(self, entry: CalendarEntry) -> CalendarEntry:
        """Save a single calendar entry to the database.

        Args:
            entry (CalendarEntry): The calendar entry to save

        Returns:
            CalendarEntry: The saved calendar entry with updated database state
        """
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def save_all(self, entries: list[CalendarEntry]) -> list[CalendarEntry]:
        """Save multiple calendar entries to the database.

        Args:
            entries (list[CalendarEntry]): List of calendar entries to save

        Returns:
            list[CalendarEntry]: The saved calendar entries with updated database state
        """
        if not entries:
            return []

        self._session.add_all(entries)
        await self._session.commit()
        await self._session.flush()
        for entry in entries:
            await self._session.refresh(entry)
        return entries

    async def delete(self, entry: CalendarEntry) -> None:
        """Delete a single calendar entry from the database.

        Args:
            entry (CalendarEntry): The calendar entry to delete
        """
        await self._session.delete(entry)
        await self._session.commit()

    async def delete_all(self, entries: list[CalendarEntry]) -> None:
        """Delete multiple calendar entries from the database.

        Args:
            entries (list[CalendarEntry]): List of calendar entries to delete
        """
        if not entries:
            return

        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()

    async def reset(self, entry: CalendarEntry) -> CalendarEntry:
        """Refresh a calendar entry with its current database state.

        Args:
            entry (CalendarEntry): The calendar entry to refresh

        Returns:
            CalendarEntry: The calendar entry with refreshed data from the database
        """
        await self._session.refresh(entry)
        return entry


async def create_database() -> None:
    """Initialize the database by creating all required tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
