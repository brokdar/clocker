from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import SQLModel

from app.dependencies import get_calendar
from app.model import (
    CalendarEntryBase,
    CalendarEntryType,
    TimeLogBase,
)
from app.services import time_logger
from app.services.calendar import Calendar
from app.services.time_logger import TimeLogError


class TimeLogResponse(TimeLogBase):
    """Response model of a time log."""

    id: int


class TimeLogCreate(TimeLogBase):
    """Query model for creating a time log."""


class TimeLogUpdate(TimeLogBase):
    """Query model for updating a time log."""

    id: int | None = None


class CalendarEntryResponse(CalendarEntryBase):
    """Response model of a calendar entry."""

    logs: list[TimeLogResponse]


class CalendarEntryCreate(CalendarEntryBase):
    """Query model for creating a calendar entry."""

    logs: list[TimeLogCreate] = []


class CalendarEntryUpdate(CalendarEntryBase):
    """Query model for updating a calendar entry."""

    logs: list[TimeLogUpdate] = []


class VacationRangeRequest(SQLModel):
    """Request model for batch vacation creation."""

    start_date: date
    end_date: date


class VacationRangePreview(SQLModel):
    """Response model for vacation range preview."""

    available_count: int
    available_dates: list[date]


class BatchCreationResult(SQLModel):
    """Response model for batch creation results."""

    created_count: int
    created_entries: list[CalendarEntryResponse]


router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/")
async def list_entries(
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default_factory=lambda: date.today().month),
    calendar: Calendar = Depends(get_calendar),
) -> list[CalendarEntryResponse]:
    """Retrieve all calendar entries for a specific month.

    Args:
        year (int): The year to fetch entries for. Defaults to current year.
        month (int): The month to fetch entries for (1-12). Defaults to current month.
        calendar (Calendar): Calendar service for data access.

    Returns:
        list[CalendarEntryResponse]: JSON containing all entries for the specified month.
    """
    try:
        entries = await calendar.get_month(year, month)
        return [
            CalendarEntryResponse.model_validate(entry) for entry in entries.values()
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{date}")
async def get_entry(
    date: date,
    calendar: Calendar = Depends(get_calendar),
) -> CalendarEntryResponse:
    """Retrieve a single calendar entry by date.

    Args:
        date (date): The date of the entry to retrieve.
        calendar (Calendar): Calendar service for data access.

    Returns:
        CalendarEntryResponse: JSON containing the calendar entry.
    """
    entry = await calendar.get_by_date(date)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No entry found for day {date}",
        )

    return CalendarEntryResponse.model_validate(entry)


@router.post("/{date}")
async def create_entry(
    date: date,
    data: CalendarEntryCreate,
    calendar: Calendar = Depends(get_calendar),
) -> CalendarEntryResponse:
    """Create a new calendar entry for a specific date.

    Args:
        date (date): The date for the new entry.
        data (CalendarEntryCreate): The entry data including type and time logs.
        calendar (Calendar): Calendar service for data access.

    Returns:
        CalendarEntryResponse: JSON containing the created entry or error details.
    """
    existing_entry = await calendar.get_by_date(date)
    if existing_entry is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entry already exists for date {date}",
        )

    try:
        entry = await calendar.create_entry(date, data.type)
        for log in data.logs:
            time_logger.add_time_log(entry, log.type, log.start, log.end, log.pause)
        entry = await calendar.update_entry(entry)
        return CalendarEntryResponse.model_validate(entry)
    except TimeLogError as e:
        await calendar.remove_entry(date)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.patch("/{date}")
async def update_entry(
    date: date,
    data: CalendarEntryUpdate,
    calendar: Calendar = Depends(get_calendar),
) -> CalendarEntryResponse:
    """Update an existing calendar entry.

    Args:
        date (date): The date of the entry to update.
        data (CalendarEntryUpdate): Updated entry data including type and time logs.
        calendar (Calendar): Calendar service for data access.

    Returns:
        CalendarEntryResponse: JSON containing the updated entry or error details.
    """
    entry = await calendar.get_by_date(date)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No entry found for date {date}",
        )

    if entry.type != data.type:
        entry.type = data.type
        if entry.type != CalendarEntryType.WORK:
            entry.logs = []
            entry = await calendar.update_entry(entry)
            return CalendarEntryResponse.model_validate(entry)

    try:
        existing_logs = {log.id: log for log in entry.logs if log.id is not None}
        log_ids_in_request = {log.id for log in data.logs if log.id is not None}

        # Handle all removed time logs first
        for existing_log in list(existing_logs.values()):
            if existing_log.id not in log_ids_in_request:
                entry.logs.remove(existing_log)

        # Then handle updates and additions
        for log in data.logs:
            if log.id and log.id in existing_logs:
                # Handle updated existing time logs
                log_index = entry.logs.index(existing_logs[log.id])
                time_logger.update_time_log(
                    entry, log_index, log.type, log.start, log.end, log.pause
                )
            else:
                # Handle new time logs
                time_logger.add_time_log(entry, log.type, log.start, log.end, log.pause)

        entry = await calendar.update_entry(entry)
        return CalendarEntryResponse.model_validate(entry)
    except TimeLogError as e:
        await calendar.reset_entry(entry)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{target_date}/copy")
async def copy_entry(
    target_date: date,
    source_date: date = Query(..., description="The date to copy from"),
    calendar: Calendar = Depends(get_calendar),
) -> CalendarEntryResponse:
    """Copy a calendar entry from source date to target date.

    Args:
        target_date (date): The date to copy the entry to.
        source_date (date): The date to copy the entry from.
        calendar (Calendar): Calendar service for data access.

    Returns:
        CalendarEntryResponse: JSON containing the copied entry or error details.
    """
    try:
        entry = await calendar.get_by_date(source_date)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entry found for source date {source_date}",
            )

        # Extract log data while still in async context to avoid lazy loading issues
        log_data = [(log.type, log.start, log.end, log.pause) for log in entry.logs]

        new_entry = await calendar.create_entry(target_date, entry.type)
        for log_type, start, end, pause in log_data:
            time_logger.add_time_log(new_entry, log_type, start, end, pause)

        new_entry = await calendar.update_entry(new_entry)
        return CalendarEntryResponse.model_validate(new_entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.delete("/{date}")
async def delete_entry(
    date: date,
    calendar: Calendar = Depends(get_calendar),
) -> CalendarEntryResponse:
    """Delete a calendar entry for a specific date.

    Args:
        date (date): The date of the entry to delete.
        calendar (Calendar): Calendar service for data access.

    Returns:
        CalendarEntryResponse: JSON containing the deleted entry or error details.
    """
    try:
        entry = await calendar.remove_entry(date)
        return CalendarEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/batch/vacation/preview")
async def preview_vacation_range(
    start_date: date = Query(..., description="Start date of vacation range"),
    end_date: date = Query(..., description="End date of vacation range"),
    calendar: Calendar = Depends(get_calendar),
) -> VacationRangePreview:
    """Preview available dates for vacation range.

    Returns the count and list of dates that would receive vacation entries,
    excluding weekends, holidays, and existing entries.

    Args:
        start_date (date): The start date of the vacation range.
        end_date (date): The end date of the vacation range.
        calendar (Calendar): Calendar service for data access.

    Returns:
        VacationRangePreview: Preview showing available dates and count.
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must not be before start date",
        )

    available_dates = await calendar.get_available_vacation_dates(start_date, end_date)
    return VacationRangePreview(
        available_count=len(available_dates),
        available_dates=available_dates,
    )


@router.post("/batch/vacation")
async def create_vacation_range(
    data: VacationRangeRequest,
    calendar: Calendar = Depends(get_calendar),
) -> BatchCreationResult:
    """Create vacation entries for a date range.

    Automatically skips weekends, holidays, and dates with existing entries.

    Args:
        data (VacationRangeRequest): The vacation range request data.
        calendar (Calendar): Calendar service for data access.

    Returns:
        BatchCreationResult: Result containing created entries.
    """
    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must not be before start date",
        )

    entries = await calendar.create_vacation_entries(data.start_date, data.end_date)
    return BatchCreationResult(
        created_count=len(entries),
        created_entries=[CalendarEntryResponse.model_validate(e) for e in entries],
    )
