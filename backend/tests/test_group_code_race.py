"""v1.0.1d-1 — group-code allocation race.

`_allocate_unique_group_code` now takes a per-event Postgres advisory
transaction lock so two registrants who each START a group with the
same surname cannot both claim the same STEM-NNN code. These tests
prove:

  1. uniqueness still holds for sequential same-stem allocations, and
  2. a concurrent second allocation BLOCKS until the first transaction
     commits, then observes the first code and picks a different one.

Both need the Postgres test DB (the shared ``db_engine`` fixture) and
skip automatically when it is unreachable.
"""

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.participant_service import _allocate_unique_group_code
from tests.conftest import make_event, make_participant


def _independent_sessions(db_engine):
    """A maker bound to the test engine, for genuinely separate
    connections (each session = its own connection = its own
    transaction, which is what an advisory-lock test requires)."""
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.mark.asyncio
async def test_sequential_allocations_are_unique(db, db_engine):
    """Baseline: with one code already saved, the next allocation for the
    same stem must avoid it. (Regression guard for the SELECT check.)"""
    ev = await make_event(db)
    await db.commit()

    maker = _independent_sessions(db_engine)
    async with maker() as s:
        code1 = await _allocate_unique_group_code(s, ev.id, "KIM")
        await make_participant(s, ev.id, last_name="Kim", group_code=code1)
        await s.commit()

    async with maker() as s:
        code2 = await _allocate_unique_group_code(s, ev.id, "KIM")

    assert code1.startswith("KIM-") and code2.startswith("KIM-")
    assert code1 != code2


@pytest.mark.asyncio
async def test_concurrent_allocation_is_serialised_by_lock(db, db_engine):
    """The race itself: session A allocates + holds its transaction open;
    session B tries the same allocation and must block on the advisory
    lock until A commits, then pick a different code."""
    ev = await make_event(db)
    await db.commit()

    maker = _independent_sessions(db_engine)

    # A: allocate (acquires the per-event advisory lock) and write a
    # holding row, but DO NOT commit — the lock is held on A's txn.
    sa = maker()
    code_a = await _allocate_unique_group_code(sa, ev.id, "KIM")
    await make_participant(sa, ev.id, last_name="Kim", group_code=code_a)

    # B: same stem, separate connection. Its advisory-lock call must block.
    sb = maker()
    task_b = asyncio.create_task(_allocate_unique_group_code(sb, ev.id, "KIM"))

    try:
        await asyncio.sleep(0.5)
        assert not task_b.done(), (
            "B completed while A held the lock — allocation is NOT serialised"
        )

        # Release A. B unblocks, its SELECT now sees A's committed code.
        await sa.commit()
        code_b = await asyncio.wait_for(task_b, timeout=5)

        assert code_b != code_a, "B reused the code A had already committed"
        assert code_b.startswith("KIM-")
    finally:
        if not task_b.done():
            task_b.cancel()
        await sb.rollback()
        await sa.close()
        await sb.close()
