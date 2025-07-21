from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.dependencies import get_calendar, get_statistics_service
from app.services.calendar import Calendar
from app.services.display import DisplayService
from app.services.statistics import ComplianceViolation, StatisticsService

from . import templates

router = APIRouter(prefix="/entries")


@router.get("/{date}/view", response_class=HTMLResponse)
async def view_entry(
    request: Request,
    date: date,
    calendar: Calendar = Depends(get_calendar),
    statistic_service: StatisticsService = Depends(get_statistics_service),
) -> HTMLResponse:
    """Render the HTML view for a specific calendar entry.

    Args:
        request (Request): The incoming request object.
        date (date): The date of the entry to view.
        calendar (Calendar): Calendar service for data access.
        statistic_service (StatisticsService): Service for compliance checks.

    Returns:
        HTMLResponse: Rendered HTML template with entry details and compliance status.
    """
    compliance_violations: list[ComplianceViolation] = []
    entry = await calendar.get_by_date(date)
    if entry:
        previous_entry = await calendar.get_by_date(date - timedelta(days=1))
        compliance_violations = statistic_service.compliance_check(
            entry, previous_entry
        )

    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "date": date,
            "entry": entry or None,
            "compliance_violations": compliance_violations,
            "display_service": DisplayService(),
        },
    )
