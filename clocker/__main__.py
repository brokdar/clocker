import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from clocker.database import create_database
from clocker.routes import calendar, entries, statistics


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    try:
        await create_database()
        yield
    finally:
        print("Shutdown")


app = FastAPI(lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)
app.include_router(calendar.router)
app.include_router(entries.router)
app.include_router(statistics.router)


@app.route("/")
def index(request: Request) -> RedirectResponse:
    """Route for the index page."""
    return RedirectResponse("/calendar/view")


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=8000)
