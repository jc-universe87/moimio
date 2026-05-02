"""Pytest configuration and shared fixtures.

Two flavours of fixture live here:

  • `client` — ASGI test client for HTTP integration tests.
  • `db`     — SQLAlchemy AsyncSession backed by a real Postgres test
               database, for unit-testing service-layer code that
               doesn't sensibly mock. Tables are truncated between
               tests so order doesn't matter.

The `db` path requires a Postgres instance reachable via
TEST_DATABASE_URL (default assumes a local socket as used in the
build sandbox). In the Docker compose setup, point this at the
test schema on the `db` service. Tests that use `db` are skipped
gracefully if the DB isn't reachable.
"""

import os
import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base
from app.main import app

# Import all models so Base.metadata is fully populated before create_all.
import app.models  # noqa: F401


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres@/moimio_test?host=/var/run/postgresql",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for API integration tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── DB fixtures ──────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Session-scoped engine + schema. Creates all tables once at start,
    drops and recreates public schema to guarantee a clean slate.
    """
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        pytest.skip(f"Postgres test DB not reachable: {e}")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine):
    """Per-test session. Truncates all tables before each test so
    ordering doesn't matter and each test starts from empty.
    """
    # Truncate between tests. TRUNCATE ... CASCADE handles FKs.
    async with db_engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' "
            "AND tablename != 'alembic_version'"
        ))
        tables = [row[0] for row in result.fetchall()]
        if tables:
            await conn.execute(text(
                f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"
            ))

    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


# ─── Factory helpers ──────────────────────────────────────────────────
#
# Lightweight convenience constructors for the service-layer tests.
# They commit-flush the object and return it populated with its
# generated UUID so downstream builders can reference it.

from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.models.participant import Participant, RegistrationStatus
from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.mark import MarkDefinition, MarkAssignment


async def make_user(db: AsyncSession, email: str = "admin@test.local") -> User:
    u = User(
        email=email,
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Admin",
        role=UserRole.SUPER_ADMIN,
    )
    db.add(u)
    await db.flush()
    return u


async def make_event(db: AsyncSession, name: str = "Test Event") -> Event:
    user = await make_user(db, email=f"admin-{uuid.uuid4().hex[:8]}@test.local")
    ev = Event(
        name=name,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        status=EventStatus.OPEN,
        created_by=user.id,
    )
    db.add(ev)
    await db.flush()
    return ev


async def make_category(
    db: AsyncSession,
    event_id: uuid.UUID,
    name: str = "Rooms",
    has_capacity: bool = False,
    has_gender_restriction: bool = False,
    exclusive_group_codes: bool = False,
    settings: dict | None = None,
) -> AllocationCategory:
    cat = AllocationCategory(
        event_id=event_id,
        name=name,
        has_capacity=has_capacity,
        has_gender_restriction=has_gender_restriction,
        exclusive_group_codes=exclusive_group_codes,
        settings=settings,
    )
    db.add(cat)
    await db.flush()
    return cat


async def make_unit(
    db: AsyncSession,
    category_id: uuid.UUID,
    name: str,
    capacity: int = 999,  # v0.74: required (NOT NULL); default = "effectively unlimited" for legacy tests
    gender_restriction: str | None = None,
) -> AllocationUnit:
    u = AllocationUnit(
        category_id=category_id,
        name=name,
        capacity=capacity,
        gender_restriction=gender_restriction,
    )
    db.add(u)
    await db.flush()
    return u


async def make_participant(
    db: AsyncSession,
    event_id: uuid.UUID,
    first_name: str = "Alice",
    last_name: str = "Test",
    gender: str | None = None,
    group_code: str | None = None,
    group_code_categories: list | None = None,
    status: RegistrationStatus = RegistrationStatus.CONFIRMED,
    email: str | None = None,
) -> Participant:
    p = Participant(
        event_id=event_id,
        first_name=first_name,
        last_name=last_name,
        email=email or f"{first_name.lower()}-{uuid.uuid4().hex[:6]}@test.local",
        gender=gender,
        group_code=group_code,
        group_code_categories=group_code_categories,
        registration_status=status,
        gdpr_consent=True,
    )
    db.add(p)
    await db.flush()
    return p


async def make_mark(
    db: AsyncSession,
    event_id: uuid.UUID,
    name: str = "TestMark",
    cluster_behaviour: str = "none",
    colour: str = "#4682B4",
) -> MarkDefinition:
    """v0.74: create a mark definition with optional cluster_behaviour."""
    m = MarkDefinition(
        event_id=event_id,
        name=name,
        colour=colour,
        visible_in=["allocation", "people", "checkin"],
        cluster_behaviour=cluster_behaviour,
    )
    db.add(m)
    await db.flush()
    return m


async def assign_mark(
    db: AsyncSession,
    event_id: uuid.UUID,
    mark_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> MarkAssignment:
    """v0.74: assign a mark to a participant."""
    a = MarkAssignment(
        event_id=event_id,
        mark_id=mark_id,
        participant_id=participant_id,
    )
    db.add(a)
    await db.flush()
    return a
