import calendar
from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.dependencies import get_calendar, get_statistics_service
from app.model import CalendarEntry
from app.services.calendar import Calendar
from app.services.display import DisplayService
from app.services.statistics import StatisticsService

from . import templates

router = APIRouter(prefix="/statistics")


@dataclass
class DayData:
    """Represents a single day's data in the statistics view.

    Contains all necessary information to display a day cell in the statistics grid,
    including whether it's a weekend and the associated calendar entry if it exists.
    """

    day: int
    date: date
    entry_type: CalendarEntry | None = None
    is_weekend: bool = False


@dataclass
class MonthData:
    """Container for monthly statistics grid data.

    Holds calendar grid information for a single month, including empty cells
    needed for proper grid alignment.
    """

    name: str
    number: int
    days: list[DayData | None]  # None represents empty cells for alignment


@router.get("/view", response_class=HTMLResponse)
@router.get("/{year}/view", response_class=HTMLResponse)
async def view_statistics(
    request: Request,
    year: int | None = None,
    calendar: Calendar = Depends(get_calendar),
    statistics_service: StatisticsService = Depends(get_statistics_service),
) -> HTMLResponse:
    """Render the yearly statistics view HTML page.

    Displays a grid of all months in the year with their entries and calculates
    yearly statistics.

    Args:
        request (Request): The incoming request object.
        year (int | None): The year to display statistics for. Defaults to current year.
        calendar (Calendar): Calendar service for data access.
        statistics_service (StatisticsService): Service for calculating statistics.

    Returns:
        HTMLResponse: Rendered HTML template with yearly statistics overview.
    """
    if year is None:
        year = date.today().year

    entries = await calendar.get_year(year)
    statistics = statistics_service.calculate_statistics(entries.values())
    display = DisplayService()
    months = _get_all_month(year, entries)

    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "year": year,
            "months": months,
            "statistics": statistics,
            "display_service": display,
        },
    )


def _get_all_month(year: int, entries: dict[date, CalendarEntry]) -> list[MonthData]:
    """Generate month grid data for the entire year.

    Creates a list of MonthData objects containing properly aligned calendar grids
    with entry information for each month of the year.

    Args:
        year (int): The year to generate month data for.
        entries (dict[date, CalendarEntry]): Dictionary of all entries for the year.

    Returns:
        list[MonthData]: List of 12 MonthData objects with complete calendar information.
    """
    months: list[MonthData] = []
    for month in range(1, 13):
        days: list[DayData | None] = []
        month_name = date(year, month, 1).strftime("%B %Y")

        # Get first weekday (0-6) and number of days in one call
        first_weekday, days_in_month = calendar.monthrange(year, month)
        days.extend([None] * first_weekday)

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            entry = entries.get(current_date)
            days.append(
                DayData(
                    day=day,
                    date=current_date,
                    entry_type=entry or None,
                    is_weekend=current_date.weekday() >= 5,
                )
            )

        months.append(MonthData(name=month_name, number=month, days=days))
    return months
