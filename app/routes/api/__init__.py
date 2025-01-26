from fastapi import APIRouter

from . import entries, statistics

API_VERSION = "v1"
API_PATH = f"/api/{API_VERSION}"

router = APIRouter(prefix=API_PATH)
router.include_router(entries.router)
router.include_router(statistics.router)
