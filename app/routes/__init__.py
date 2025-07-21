from fastapi import APIRouter

from .api import router as api_router
from .web import calendar, entries, index_router, statistics

web_router = APIRouter(tags=["web"])
web_router.include_router(index_router)
web_router.include_router(calendar.router)
web_router.include_router(entries.router)
web_router.include_router(statistics.router)

__all__ = ["web_router", "api_router"]
