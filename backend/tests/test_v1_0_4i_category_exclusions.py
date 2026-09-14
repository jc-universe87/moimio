"""v1.0.4i — allocation_category_exclusions: storage, cascades, counts, history.

Covers:
  1. UNIQUE (allocation_category_id, participant_id) at the DB layer.
  2. ON DELETE CASCADE from allocation_categories.
  3. ON DELETE CASCADE from participants.
  4. list_categories() reports excluded_count per category.
  5. add_exclusion / remove_exclusion each write one allocation_events
     row: event_type exclude / include, source manual, no unit.
  6. add is idempotent and remove of a missing exclusion is a no-op;
     neither writes a second history entry.

Service-layer only. The endpoints are thin wrappers over these calls
with the same auth as the neighbouring category writes.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.services.allocation_service import (
    add_exclusion,
    remove_exclusion,
    list_excluded_participant_ids,
    list_categories,
    delete_category,
)

from tests.conftest import (
    make_user,
    make_event,
    make_category,
    make_participant,
)


pytestmark = pytest.mark.asyncio


async def _count_exclusions(db, category_id) -> int:
    result = await db.execute(
        select(func.count(AllocationCategoryExclusion.id))
        .where(AllocationCategoryExclusion.allocation_category_id == category_id)
    )
    return result.scalar_one()


async def _events(db, event_id) -> list[AllocationEvent]:
    result = await db.execute(
        select(AllocationEvent)
        .where(AllocationEvent.event_id == event_id)
        .order_by(AllocationEvent.occurred_at, AllocationEvent.id)
    )
    return list(result.scalars().all())


# ─── 1. unique constraint ───

async def test_duplicate_exclusion_rejected_by_unique_constraint(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    p = await make_participant(db, event_id=ev.id)

    db.add(AllocationCategoryExclusion(allocation_category_id=cat.id, participant_id=p.id))
    await db.flush()
    db.add(AllocationCategoryExclusion(allocation_category_id=cat.id, participant_id=p.id))
    with pytest.raises(IntegrityError):
        await db.flush()
    await db.rollback()


# ─── 2. cascade on category delete ───

async def test_category_delete_cascades_to_exclusions(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    other = await make_category(db, event_id=ev.id, name="Small Groups")
    p = await make_participant(db, event_id=ev.id)

    await add_exclusion(db, cat.id, p.id)
    await add_exclusion(db, other.id, p.id)
    assert await _count_exclusions(db, cat.id) == 1

    assert await delete_category(db, cat.id) is True

    assert await _count_exclusions(db, cat.id) == 0
    # The sibling category's exclusion is untouched.
    assert await _count_exclusions(db, other.id) == 1


# ─── 3. cascade on participant delete ───

async def test_participant_delete_cascades_to_exclusions(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    p = await make_participant(db, event_id=ev.id, first_name="Alice")
    q = await make_participant(db, event_id=ev.id, first_name="Bob")

    await add_exclusion(db, cat.id, p.id)
    await add_exclusion(db, cat.id, q.id)
    assert await _count_exclusions(db, cat.id) == 2

    await db.delete(p)
    await db.flush()

    assert await list_excluded_participant_ids(db, cat.id) == [q.id]


# ─── 4. excluded_count ───

async def test_list_categories_reports_excluded_count(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    other = await make_category(db, event_id=ev.id, name="Small Groups")
    p = await make_participant(db, event_id=ev.id, first_name="Alice")
    q = await make_participant(db, event_id=ev.id, first_name="Bob")

    await add_exclusion(db, cat.id, p.id)
    await add_exclusion(db, cat.id, q.id)

    by_name = {c["name"]: c for c in await list_categories(db, ev.id)}
    assert by_name["Rooms"]["excluded_count"] == 2
    assert by_name["Small Groups"]["excluded_count"] == 0
    # The other aggregates are unaffected by exclusions.
    assert by_name["Rooms"]["allocated_count"] == 0
    assert by_name["Rooms"]["unit_count"] == 0


# ─── 5. history entries ───

async def test_add_exclusion_writes_exclude_event(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    p = await make_participant(db, event_id=ev.id)

    row = await add_exclusion(db, cat.id, p.id, actor_user_id=user.id)
    assert row.created_by == user.id

    events = await _events(db, ev.id)
    assert len(events) == 1
    e = events[0]
    assert e.event_type == AllocationEventType.EXCLUDE
    assert e.source == AllocationEventSource.MANUAL
    assert e.participant_id == p.id
    assert e.category_id == cat.id
    assert e.actor_user_id == user.id
    assert e.unit_id is None
    assert e.unit_name_snapshot == ""
    assert e.category_name_snapshot == "Rooms"


async def test_remove_exclusion_writes_include_event(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    p = await make_participant(db, event_id=ev.id)

    await add_exclusion(db, cat.id, p.id, actor_user_id=user.id)
    assert await remove_exclusion(db, cat.id, p.id, actor_user_id=user.id) is True
    assert await _count_exclusions(db, cat.id) == 0

    events = await _events(db, ev.id)
    assert [e.event_type for e in events] == [
        AllocationEventType.EXCLUDE,
        AllocationEventType.INCLUDE,
    ]
    e = events[1]
    assert e.source == AllocationEventSource.MANUAL
    assert e.participant_id == p.id
    assert e.category_id == cat.id
    assert e.actor_user_id == user.id
    assert e.unit_id is None
    assert e.category_name_snapshot == "Rooms"


# ─── 6. idempotency ───

async def test_add_twice_keeps_one_row_and_one_event(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    p = await make_participant(db, event_id=ev.id)

    first = await add_exclusion(db, cat.id, p.id)
    second = await add_exclusion(db, cat.id, p.id)
    assert first.id == second.id
    assert await _count_exclusions(db, cat.id) == 1
    assert len(await _events(db, ev.id)) == 1


async def test_remove_missing_exclusion_is_noop(db):
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    p = await make_participant(db, event_id=ev.id)

    assert await remove_exclusion(db, cat.id, p.id) is False
    assert await _events(db, ev.id) == []


async def test_participant_from_other_event_is_not_found(db):
    from app.core.exceptions import MoimioAppError

    ev = await make_event(db)
    other_ev = await make_event(db, name="Other")
    cat = await make_category(db, event_id=ev.id)
    stranger = await make_participant(db, event_id=other_ev.id)

    with pytest.raises(MoimioAppError):
        await add_exclusion(db, cat.id, stranger.id)
    assert await _count_exclusions(db, cat.id) == 0
