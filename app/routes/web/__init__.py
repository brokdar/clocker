from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import APP_PATH

templates = Jinja2Templates(APP_PATH / "templates")

index_router = APIRouter()


@index_router.get("/")
def index(request: Request) -> RedirectResponse:
    """Route for the index page."""
    return RedirectResponse("/calendar/view")
