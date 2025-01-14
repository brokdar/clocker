from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse

from clocker.model import (
    CalendarEntryCreate,
    CalendarEntryResponse,
    CalendarEntryType,
    CalendarEntryUpdate,
)
from clocker.routes import get_calendar, get_statistics_service, templates
from clocker.services import time_logger
from clocker.services.calendar import Calendar, get_month_range
from clocker.services.display import DisplayService
from clocker.services.statistics import ComplianceViolation, StatisticsService
from clocker.services.time_logger import TimeLogError

router = APIRouter(prefix="/entries")


@router.get("/")
async def list_entries(
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default_factory=lambda: date.today().month),
    calendar: Calendar = Depends(get_calendar),
    statistic_service: StatisticsService = Depends(get_statistics_service),
) -> JSONResponse:
    """Retrieve all calendar entries for a specific month.

    Args:
        year (int): The year to fetch entries for. Defaults to current year.
        month (int): The month to fetch entries for (1-12). Defaults to current month.
        calendar (Calendar): Calendar service for data access.
        statistic_service (StatisticsService): Service for calculating statistics.

    Returns:
        JSONResponse: JSON containing entries, statistics and metadata for the month.
    """
    try:
        entries = await calendar.get_month(year, month)
        start, end = get_month_range(year, month)

        statistics = statistic_service.calculate_statistics(entries.values())
        items: dict[str, CalendarEntryResponse] = {}
        for day in calendar.iterate(start, end):
            if day in entries:
                items[day.isoformat()] = CalendarEntryResponse.model_validate(
                    entries[day]
                )

        return JSONResponse(
            {
                "success": True,
                "data": {
                    "entries": jsonable_encoder(items),
                    "statistics": jsonable_encoder(statistics),
                    "metadata": {
                        "year": year,
                        "month": month,
                        "total_entries": len(items),
                    },
                },
                "message": f"Successfully retrieved entries for {year}-{month}",
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
            "entry": CalendarEntryResponse.model_validate(entry) if entry else None,
            "compliance_violations": compliance_violations,
            "display_service": DisplayService(),
        },
    )


@router.get("/{date}")
async def get_entry(
    date: date,
    calendar: Calendar = Depends(get_calendar),
    statistic_service: StatisticsService = Depends(get_statistics_service),
) -> JSONResponse:
    """Retrieve a single calendar entry by date.

    Args:
        date (date): The date of the entry to retrieve.
        calendar (Calendar): Calendar service for data access.
        statistic_service (StatisticsService): Service for compliance checks.

    Returns:
        JSONResponse: JSON containing the entry data and compliance violations if found.
    """
    entry = await calendar.get_by_date(date)
    if not entry:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"No entry found for day {date}",
                },
            },
        )

    previous_entry = await calendar.get_by_date(date - timedelta(days=1))
    compliance_violations = statistic_service.compliance_check(entry, previous_entry)
    entry_response = CalendarEntryResponse.model_validate(entry)
    return JSONResponse(
        {
            "success": True,
            "data": {
                "entry": jsonable_encoder(entry_response),
                "compliance_violations": jsonable_encoder(compliance_violations),
            },
            "message": "Entry retrieved successfully",
        }
    )


@router.post("/{date}")
async def create_entry(
    date: date,
    data: CalendarEntryCreate,
    calendar: Calendar = Depends(get_calendar),
) -> JSONResponse:
    """Create a new calendar entry for a specific date.

    Args:
        date (date): The date for the new entry.
        data (CalendarEntryCreate): The entry data including type and time logs.
        calendar (Calendar): Calendar service for data access.

    Returns:
        JSONResponse: JSON containing the created entry or error details.
    """
    existing_entry = await calendar.get_by_date(date)
    if existing_entry is not None:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {
                    "code": "ENTRY_EXISTS",
                    "message": f"Entry already exists for date {date}",
                },
            },
        )

    try:
        entry = await calendar.create_entry(date, data.type)
        for log in data.logs:
            time_logger.add_time_log(entry, log.type, log.start, log.end, log.pause)
        entry = await calendar.update_entry(entry)
        entry_response = CalendarEntryResponse.model_validate(entry)
        return JSONResponse(
            {
                "success": True,
                "data": jsonable_encoder(entry_response),
                "message": "Entry created successfully",
            }
        )

    except TimeLogError as e:
        await calendar.remove_entry(date)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "TIME_LOG_ERROR", "message": str(e)},
            },
        )


@router.patch("/{date}")
async def update_entry(
    date: date,
    data: CalendarEntryUpdate,
    calendar: Calendar = Depends(get_calendar),
) -> JSONResponse:
    """Update an existing calendar entry.

    Args:
        date (date): The date of the entry to update.
        data (CalendarEntryUpdate): Updated entry data including type and time logs.
        calendar (Calendar): Calendar service for data access.

    Returns:
        JSONResponse: JSON containing the updated entry or error details.
    """
    entry = await calendar.get_by_date(date)
    if not entry:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"No entry found for date {date}",
                },
            },
        )

    if entry.type != data.type:
        entry.type = data.type
        if entry.type != CalendarEntryType.WORK:
            entry.logs = []
            entry = await calendar.update_entry(entry)
            entry_response = CalendarEntryResponse.model_validate(entry)
            return JSONResponse(
                {
                    "success": True,
                    "data": jsonable_encoder(entry_response),
                    "message": "Entry updated successfully",
                }
            )

    try:
        existing_logs = {log.id: log for log in entry.logs if log.id is not None}
        for log in data.logs:
            if log.id and log.id in existing_logs:
                # Handle updated existing time logs
                log_index = entry.logs.index(existing_logs[log.id])
                time_logger.update_time_log(
                    entry, log_index, log.type, log.start, log.end, log.pause
                )
                del existing_logs[log.id]  # mark as handled
            else:
                # Handle new time logs
                time_logger.add_time_log(entry, log.type, log.start, log.end, log.pause)

        # Handle all removed time logs
        for existing_log in existing_logs.values():
            entry.logs.remove(existing_log)

        entry = await calendar.update_entry(entry)
        entry_response = CalendarEntryResponse.model_validate(entry)
        return JSONResponse(
            {
                "success": True,
                "data": jsonable_encoder(entry_response),
                "message": "Entry updated successfully",
            }
        )
    except TimeLogError as e:
        await calendar.reset_entry(entry)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "TIME_LOG_ERROR", "message": str(e)},
            },
        )


@router.delete("/{date}")
async def delete_entry(
    date: date,
    calendar: Calendar = Depends(get_calendar),
) -> JSONResponse:
    """Delete a calendar entry for a specific date.

    Args:
        date (date): The date of the entry to delete.
        calendar (Calendar): Calendar service for data access.

    Returns:
        JSONResponse: JSON containing the deleted entry or error details.
    """
    try:
        entry = await calendar.remove_entry(date)
        entry_response = CalendarEntryResponse.model_validate(entry)
        return JSONResponse(
            {
                "success": True,
                "data": jsonable_encoder(entry_response),
                "message": f"Successfully deleted {entry.type} entry for {date}",
            }
        )
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "NOT_FOUND", "message": str(e)},
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": "SERVER_ERROR", "message": str(e)},
            },
        )
