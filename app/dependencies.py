from collections.abc import AsyncGenerator
from pathlib import Path

import yaml
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import CalendarRepository, engine
from app.services.calendar import Calendar
from app.services.statistics import StatisticsConfiguration, StatisticsService

CONFIG_PATH = Path("/app/data/config.yaml")


def get_statistics_service() -> StatisticsService:
    """Create a new instance of the statistics service.

    Returns:
        StatisticsService: Configured service for calculating work time statistics.
    """
    config = StatisticsConfiguration()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as stream:
            data = yaml.safe_load(stream)
            config = StatisticsConfiguration.model_validate(data)
    return StatisticsService(config)


async def get_calendar() -> AsyncGenerator[Calendar, None]:
    """FastAPI dependency provider for the calendar service.

    Creates a new database session and calendar service instance for each request.
    Automatically handles session cleanup after the request is complete.

    Returns:
        AsyncGenerator[Calendar, None]: Calendar service instance.
    """
    async with AsyncSession(engine) as session:
        repository = CalendarRepository(session)
        yield Calendar(repository)
        await session.flush()
