from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_calendar, get_statistics_service
from app.services.calendar import Calendar
from app.services.statistics import Statistics, StatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/")
async def get_statistics(
    year: int = Query(default_factory=lambda: date.today().year),
    calendar: Calendar = Depends(get_calendar),
    statistics_service: StatisticsService = Depends(get_statistics_service),
) -> Statistics:
    """Retrieve statistics data for an entire year.

    Calculates comprehensive statistics for all entries in the specified year.

    Args:
        year (int): The year to calculate statistics for. Defaults to current year.
        calendar (Calendar): Calendar service for data access.
        statistics_service (StatisticsService): Service for calculating statistics.

    Returns:
        Statistics: JSON containing statistics data for the specified year.
    """
    try:
        entries = await calendar.get_year(year)
        return statistics_service.calculate_statistics(entries.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
