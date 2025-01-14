from collections.abc import AsyncGenerator
from datetime import date
from pathlib import Path

import yaml
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from clocker.database import CalendarRepository, engine
from clocker.services.calendar import Calendar
from clocker.services.statistics import StatisticsConfiguration, StatisticsService

CONFIG_PATH = Path("/app/data/config.yaml")

templates = Jinja2Templates(directory="clocker/templates")


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


def get_adjacent_months(current_date: date) -> tuple[date, date]:
    """Calculate the previous and next month dates for navigation.

    Handles year transitions correctly for December/January.

    Args:
        current_date (date): Reference date to calculate adjacent months for.

    Returns:
        tuple[date, date]: Tuple containing (previous_month, next_month) dates.
    """
    if current_date.month == 1:
        prev_month = date(current_date.year - 1, 12, 1)
    else:
        prev_month = date(current_date.year, current_date.month - 1, 1)

    if current_date.month == 12:
        next_month = date(current_date.year + 1, 1, 1)
    else:
        next_month = date(current_date.year, current_date.month + 1, 1)

    return prev_month, next_month
