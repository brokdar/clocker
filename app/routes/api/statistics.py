from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.dependencies import get_calendar, get_statistics_service
from app.model import CalendarEntryResponse
from app.services.calendar import Calendar
from app.services.statistics import StatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/")
async def get_statistics(
    year: int = Query(default_factory=lambda: date.today().year),
    calendar: Calendar = Depends(get_calendar),
    statistics_service: StatisticsService = Depends(get_statistics_service),
) -> JSONResponse:
    """Retrieve statistics data for an entire year.

    Calculates comprehensive statistics for all entries in the specified year.

    Args:
        year (int): The year to calculate statistics for. Defaults to current year.
        calendar (Calendar): Calendar service for data access.
        statistics_service (StatisticsService): Service for calculating statistics.

    Returns:
        JSONResponse: JSON containing yearly entries, statistics and metadata.
    """
    try:
        entries = await calendar.get_year(year)
        statistics = statistics_service.calculate_statistics(entries.values())
        items: dict[str, CalendarEntryResponse] = {}
        for day, entry in entries.items():
            items[day.isoformat()] = CalendarEntryResponse.model_validate(entry)

        return JSONResponse(
            {
                "success": True,
                "data": {
                    "entries": jsonable_encoder(items),
                    "statistics": jsonable_encoder(statistics),
                    "metadata": {"year": year, "total_entries": len(entries)},
                },
                "message": f"Successfully retrieved statistics for {year}",
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": "SERVER_ERROR", "message": str(e)},
            },
        )
