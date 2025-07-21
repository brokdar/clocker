from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import APP_PATH
from app.database import create_database
from app.routes import api_router, web_router


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
    StaticFiles(directory=APP_PATH / "static"),
    name="static",
)
app.include_router(api_router)
app.include_router(web_router)
