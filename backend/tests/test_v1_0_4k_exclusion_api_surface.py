"""v1.0.4k — the API surface the exclusion UI reads.

v1.0.4i stored exclusions; v1.0.4j made them take effect; v1.0.4k is
the release an organiser can actually see, so the contracts the board
depends on are pinned here:

  1. The assign / move responses report whether the placement lifted an
     exclusion. This is the backstop for the case the board's own
     confirmation dialog cannot catch — another organiser excluded
     someone while this board was open, so the local exclusion list is
     stale and no dialog appears. `compute_manual_move_warning` runs
     after the write, by which time the exclusion is gone, so this
     field is the only place the fact survives.
  2. The exclusions list endpoint returns ids as STRINGS, which is what
     pairs with the String(p.id) cast used throughout the board.
  3. `excluded_count` reaches the category list response, which is what
     feeds the dashboard tile.
  4. The history serialiser passes `event_type` and `source` through
     unchanged, so the frontend can tell exclude / include rows from
     the assign / unassign rows they used to be rendered as.

Endpoint functions are called directly with an explicit db + user, the
way the rest of this suite exercises service-layer behaviour; the
Depends wiring itself is not what these assertions are about.
"""

import pytest

from app.api.allocations import (
    AssignRequest,
    MoveRequest,
    ExclusionRequest,
    api_assign,
    api_move,
    api_list_exclusions,
    api_add_exclusion,
    api_list_categories,
)
from app.models.allocation_event import (
    AllocationEventSource,
    AllocationEventType,
)
from app.services.allocation_service import add_exclusion, list_excluded_participant_ids
from app.services.allocation_events_service import list_allocation_events

from tests.conftest import (
    make_user,
    make_event,
    make_category,
    make_unit,
    make_participant,
)


pytestmark = pytest.mark.asyncio


async def _actor(db, ev):
    """An account with write access to the event. make_user creates a
    SUPER_ADMIN, which satisfies both the archive check and the
    organise:write check."""
    return await make_user(db, email=f"k-{ev.id.hex[:8]}@test.local")


# ─── 1. assign / move report the override ───

async def test_assign_response_reports_a_lifted_exclusion(db):
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await add_exclusion(db, cat.id, p.id, actor_user_id=user.id)

    res = await api_assign(
        event_id=ev.id,
        data=AssignRequest(participant_id=p.id, unit_id=unit.id),
        db=db,
        current_user=user,
    )
    assert res["exclusion_cleared"] is True
    # The override really happened: the exclusion is gone, not merely
    # reported.
    assert await list_excluded_participant_ids(db, cat.id) == []


async def test_assign_response_is_false_when_nothing_was_excluded(db):
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    res = await api_assign(
        event_id=ev.id,
        data=AssignRequest(participant_id=p.id, unit_id=unit.id),
        db=db,
        current_user=user,
    )
    assert res["exclusion_cleared"] is False
    # The pre-existing fields are untouched.
    assert "allocation_id" in res
    assert "warning" in res


async def test_move_response_reports_a_lifted_exclusion(db):
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit_a = await make_unit(db, category_id=cat.id, name="Room A")
    unit_b = await make_unit(db, category_id=cat.id, name="Room B")
    p = await make_participant(db, event_id=ev.id)

    await api_assign(
        event_id=ev.id,
        data=AssignRequest(participant_id=p.id, unit_id=unit_a.id),
        db=db,
        current_user=user,
    )
    # Exclude while they hold Room A; that vacates it.
    await add_exclusion(db, cat.id, p.id, actor_user_id=user.id)

    res = await api_move(
        event_id=ev.id,
        data=MoveRequest(participant_id=p.id, to_unit_id=unit_b.id),
        db=db,
        current_user=user,
    )
    assert res["exclusion_cleared"] is True


# ─── 2. the exclusions list contract ───

async def test_exclusions_endpoint_returns_string_ids(db):
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    p = await make_participant(db, event_id=ev.id)

    await api_add_exclusion(
        event_id=ev.id,
        category_id=cat.id,
        data=ExclusionRequest(participant_id=p.id),
        db=db,
        current_user=user,
    )

    res = await api_list_exclusions(
        event_id=ev.id, category_id=cat.id, db=db, current_user=user
    )
    assert res["excluded_ids"] == [str(p.id)]
    assert all(isinstance(x, str) for x in res["excluded_ids"])


# ─── 3. excluded_count on the category list ───

async def test_category_list_response_carries_excluded_count(db):
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    p1 = await make_participant(db, event_id=ev.id, first_name="Ann")
    p2 = await make_participant(db, event_id=ev.id, first_name="Ben")
    await make_participant(db, event_id=ev.id, first_name="Cid")

    await add_exclusion(db, cat.id, p1.id, actor_user_id=user.id)
    await add_exclusion(db, cat.id, p2.id, actor_user_id=user.id)

    rows = await api_list_categories(event_id=ev.id, db=db, current_user=user)
    row = next(r for r in rows if r["id"] == cat.id)
    assert row["excluded_count"] == 2


# ─── 4. the history rows reach the frontend distinguishable ───

async def test_history_passes_exclude_rows_through_unchanged(db):
    """The serialiser applies no event_type filter, so these rows have
    been reaching the frontend since v1.0.4i — where they fell into the
    catch-all branch and rendered as 'Removed from ' with a blank unit
    name. The frontend now branches on event_type and source, so both
    must survive serialisation verbatim."""
    ev = await make_event(db)
    user = await _actor(db, ev)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await api_assign(
        event_id=ev.id,
        data=AssignRequest(participant_id=p.id, unit_id=unit.id),
        db=db,
        current_user=user,
    )
    await add_exclusion(db, cat.id, p.id, actor_user_id=user.id)

    rows = await list_allocation_events(db, event_id=ev.id, participant_id=p.id)
    by_type = {r["event_type"] for r in rows}
    assert AllocationEventType.EXCLUDE in by_type

    exclude_row = next(r for r in rows if r["event_type"] == AllocationEventType.EXCLUDE)
    # No unit is involved; the frontend renders {category}, not {unit}.
    assert exclude_row["unit_id"] is None
    assert exclude_row["unit_name"] == ""
    assert exclude_row["category_name"] == "Rooms"

    cascaded = next(
        r for r in rows
        if r["event_type"] == AllocationEventType.UNASSIGN
        and r["source"] == AllocationEventSource.PARTICIPANT_EXCLUDED
    )
    assert cascaded["unit_name"] == "Room A"
