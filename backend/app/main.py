"""Moimio — FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import MoimioAppError
from app.core.logging import setup_logging, get_logger
from app.core.middleware import CorrelationIDMiddleware
from app.core.database import engine
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.participants import router as participants_router
from app.api.allocations import router as allocations_router
from app.api.custom_fields import router as custom_fields_router
from app.api.export import router as export_router, restore_router
from app.api.user_preferences import router as preferences_router
from app.api.notes import router as notes_router
from app.api.checkin import router as checkin_router
from app.api.marks import router as marks_router
from app.api.stats import router as stats_router
from app.api.setup import router as setup_router
from app.api.users import router as users_router
from app.api.event_assignments import router as assignments_router
from app.api.preferences import router as pref_router
from app.api.streams import router as streams_router

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    setup_logging()
    logger.info("moimio_starting", version="0.2.0", log_level=settings.log_level)
    yield
    await engine.dispose()
    logger.info("moimio_stopped")


app = FastAPI(
    title="Moimio",
    description="Participant allocation platform — register, organise, allocate.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware (order matters: last added = first executed) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIDMiddleware)

# ─── Exception handlers ───
# v0.70d-3c-2: services raise MoimioAppError (carries i18n key + params + status_code).
# A global handler converts to JSONResponse with the dict-detail shape that
# matches v0.70d-3b's auth/participants/events convention. Per-site try/except
# is no longer required at the api layer — the handler runs once, centrally.
@app.exception_handler(MoimioAppError)
async def moimio_app_error_handler(request: Request, exc: MoimioAppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.to_detail()},
    )

# ─── Routers ───
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(participants_router)
app.include_router(allocations_router)
app.include_router(custom_fields_router)
app.include_router(export_router)
app.include_router(restore_router)
app.include_router(preferences_router)
app.include_router(notes_router)
app.include_router(checkin_router)
app.include_router(marks_router)
app.include_router(stats_router)
app.include_router(setup_router)
app.include_router(users_router)
app.include_router(assignments_router)
app.include_router(pref_router)
app.include_router(streams_router)
