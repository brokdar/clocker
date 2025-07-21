from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.dependencies import get_calendar, get_statistics_service
from app.model import CalendarEntry
from app.services.calendar import Calendar, get_month_range
from app.services.display import DisplayService
from app.services.statistics import Statistics, StatisticsService

from . import templates

router = APIRouter(prefix="/calendar")


@dataclass
class MonthView:
    """Container for calendar month view data.

    Holds all necessary data to render a monthly calendar view including
    entries for each day, navigation dates, and monthly statistics.
    """

    days: dict[date, CalendarEntry | None]
    current_month: date
    prev_month: date
    next_month: date
    statistics: Statistics


@router.get("/view", response_class=HTMLResponse)
@router.get("/{year}/{month}/view", response_class=HTMLResponse)
async def view_calendar(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    calendar: Calendar = Depends(get_calendar),
    statistics_service: StatisticsService = Depends(get_statistics_service),
) -> HTMLResponse:
    """Render the calendar month view HTML page.

    Args:
        request (Request): The incoming request object.
        year (int | None): The year to display. Defaults to current year.
        month (int | None): The month to display (1-12). Defaults to current month.
        calendar (Calendar): Calendar service for data access.
        statistics_service (StatisticsService): Service for calculating statistics.

    Returns:
        HTMLResponse: Rendered HTML template with calendar grid and monthly statistics.
    """
    if year and month:
        requested_date = date(year, month, 1)
    else:
        requested_date = date.today()
        year = requested_date.year
        month = requested_date.month

    prev_month, next_month = get_adjacent_months(requested_date)
    start, end = get_month_range(year, month)

    entries = await calendar.get_month(year, month)
    days_of_month: dict[date, CalendarEntry | None] = {}
    for day in calendar.iterate(start, end):
        entry = entries.get(day)
        days_of_month[day] = entry or None

    statistics = statistics_service.calculate_statistics(entries.values())

    view = MonthView(
        days=days_of_month,
        current_month=requested_date,
        prev_month=prev_month,
        next_month=next_month,
        statistics=statistics,
    )

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "view": view,
            "display_service": DisplayService(),
            "statistics_service": statistics_service,
        },
    )


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
