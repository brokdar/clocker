from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from clocker.model import CalendarEntry

DATABASE_PATH = Path("/app/data/clocker.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
engine = create_async_engine(DATABASE_URL, future=True)


class CalendarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_date(self, day: date) -> CalendarEntry | None:
        result = await self._session.get(CalendarEntry, day)
        return result

    async def get_by_date_range(
        self, start: date, end: date
    ) -> dict[date, CalendarEntry]:
        result = await self._session.exec(
            select(CalendarEntry)
            .where(CalendarEntry.day >= start)
            .where(CalendarEntry.day <= end)
        )
        return {entry.day: entry for entry in result}

    async def save(self, entry: CalendarEntry) -> CalendarEntry:
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def save_all(self, entries: list[CalendarEntry]) -> list[CalendarEntry]:
        if not entries:
            return []

        self._session.add_all(entries)
        await self._session.commit()
        for entry in entries:
            await self._session.refresh(entry)
        return entries

    async def delete(self, entry: CalendarEntry) -> None:
        await self._session.delete(entry)
        await self._session.commit()

    async def delete_all(self, entries: list[CalendarEntry]) -> None:
        if not entries:
            return

        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()

    async def reset(self, entry: CalendarEntry) -> CalendarEntry:
        await self._session.refresh(entry)
        return entry


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
