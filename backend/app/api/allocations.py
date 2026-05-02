"""Allocation routes — categories, units, and assignments."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.allocation_category import AllocationCategory
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep
from app.services.permissions import get_event_permissions, has_write
from app.services.engine_service import run_engine, commit_proposal, clear_category_allocations
from app.services.allocation_service import (
    create_category, list_categories, update_category, delete_category,
    create_unit, list_units, get_unit, delete_unit, update_unit,
    assign_participant, move_participant, unassign_participant,
    get_allocations_by_category, get_all_allocations,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/events/{event_id}", tags=["allocations"])


async def _publish_organise_change(event_id: uuid.UUID, kind: str, **extra) -> None:
    """v1.0-pre #9: fire-and-forget broadcast on the organise:<event_id>
    topic so other admins viewing the AllocationBoard see the change
    without a refresh. `kind` is a short slug like 'allocation_assigned',
    'category_committed', 'units_reordered', etc. Extra context (e.g.
    category_id, participant_id) is included where useful but consumers
    may also choose to just re-fetch on any event.
    """
    try:
        from app.core.pubsub import broker
        await broker.publish(
            f"organise:{event_id}",
            {"type": "allocation_changed", "kind": kind, "event_id": str(event_id), **extra},
        )
    except Exception as e:
        logger.warning("organise_pubsub_publish_failed", error=str(e), kind=kind)


# ─── Schemas ───

class CategoryCreate(BaseModel):
    name: str
    item_label: str | None = None
    description: str | None = None
    rule_type: str = "exclusive"
    has_capacity: bool = False
    has_gender_restriction: bool = False  # DEPRECATED v0.74; engine ignores
    exclusive_group_codes: bool = False  # v0.74
    sort_order: int = 0
    settings: dict | None = None

class CategoryUpdate(BaseModel):
    name: str | None = None
    item_label: str | None = None
    description: str | None = None
    rule_type: str | None = None
    has_capacity: bool | None = None
    has_gender_restriction: bool | None = None  # DEPRECATED v0.74
    exclusive_group_codes: bool | None = None  # v0.74
    sort_order: int | None = None
    settings: dict | None = None

class UnitCreate(BaseModel):
    name: str
    description: str | None = None
    capacity: int  # v0.74: required (was Optional)
    gender_restriction: str | None = None
    sort_order: int = 0

class UnitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capacity: int | None = None  # optional on update (no change implies same)
    gender_restriction: str | None = None
    sort_order: int | None = None

class AssignRequest(BaseModel):
    participant_id: uuid.UUID
    unit_id: uuid.UUID

class MoveRequest(BaseModel):
    participant_id: uuid.UUID
    to_unit_id: uuid.UUID


# ─── Permission helper ───

async def _require_organise_write(db, user, event_id):
    """v0.50e-1d: per-category cat_<uuid> overrides were removed. A single
    `organise: "write"` on the assignment grants write to the whole board."""
    perms = await get_event_permissions(db, user, event_id)
    if perms is None:
        raise HTTPException(status_code=403, detail={"key": "errors.event.no_access"})
    if not has_write(perms, "organise"):
        raise HTTPException(status_code=403, detail={"key": "errors.organise.write_required"})


# ─── Categories ───

@router.get("/allocation-categories/")
async def api_list_categories(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_categories(db, event_id)


@router.get("/allocation-categories/public")
async def api_list_categories_public(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — list category names for the registration preference form."""
    cats = await list_categories(db, event_id)
    return [{"id": str(c["id"]), "name": c["name"], "item_label": c.get("item_label", "")} for c in cats]


@router.post("/allocation-categories/", status_code=201)
async def api_create_category(
    event_id: uuid.UUID,
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    payload = data.model_dump()
    # v0.58d: auto-assign sort_order to max+1 so new categories append
    # to the end rather than landing at 0 and interleaving with the
    # seeded defaults (Rooms=0, Small Groups=1). Only kicks in when the
    # caller didn't specify a sort_order explicitly.
    if payload.get("sort_order", 0) == 0:
        result = await db.execute(
            select(func.coalesce(func.max(AllocationCategory.sort_order), -1))
            .where(AllocationCategory.event_id == event_id)
        )
        max_so = result.scalar()
        payload["sort_order"] = (max_so if max_so is not None else -1) + 1
    await _publish_organise_change(event_id, "category_created")
    return await create_category(db, event_id, **payload)


@router.patch("/allocation-categories/{category_id}")
async def api_update_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    await _publish_organise_change(event_id, "category_updated")
    return await update_category(db, category_id, **data.model_dump(exclude_unset=True))


@router.delete("/allocation-categories/{category_id}", status_code=204)
async def api_delete_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    deleted = await delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"key": "errors.allocation.group_type_not_found"})
    await _publish_organise_change(event_id, "category_deleted")


# ─── v50c-3: allocation lifecycle ───

@router.post("/allocation-categories/{category_id}/confirm")
async def api_confirm_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Mark this category's allocation as Confirmed (organiser is done with it).

    Any subsequent edit to an allocation or unit in this category will
    silently revert this flag to False (§12.3 re-open rule).
    """
    from app.services.allocation_service import confirm_category
    cat = await confirm_category(db, category_id)
    logger.info(
        "allocation_category_confirmed",
        event_id=str(event_id), category_id=str(category_id), by=str(current_user.id),
    )
    await _publish_organise_change(event_id, "category_committed")
    return {
        "id": str(cat.id), "name": cat.name, "confirmed": cat.confirmed,
    }


@router.post("/allocation-categories/{category_id}/unconfirm")
async def api_unconfirm_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Explicitly flip a Confirmed category back to In Progress. Used by
    the 'Edit' CTA on a confirmed category card."""
    from app.services.allocation_service import unconfirm_category
    cat = await unconfirm_category(db, category_id)
    logger.info(
        "allocation_category_unconfirmed",
        event_id=str(event_id), category_id=str(category_id), by=str(current_user.id),
    )
    await _publish_organise_change(event_id, "category_uncommitted")
    return {
        "id": str(cat.id), "name": cat.name, "confirmed": cat.confirmed,
    }



class ReorderPayload(BaseModel):
    ordered_ids: list[uuid.UUID]


@router.post("/allocation-categories/reorder", status_code=204)
async def api_reorder_categories(
    event_id: uuid.UUID,
    data: ReorderPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Set sort_order for categories based on the provided ordered list."""
    from app.models.allocation_category import AllocationCategory
    from sqlalchemy import update as upd
    for i, cat_id in enumerate(data.ordered_ids):
        await db.execute(
            upd(AllocationCategory)
            .where(AllocationCategory.id == cat_id, AllocationCategory.event_id == event_id)
            .values(sort_order=i)
        )
    await db.flush()
    await _publish_organise_change(event_id, "categories_reordered")


@router.post("/allocation-categories/{category_id}/units/reorder", status_code=204)
async def api_reorder_units(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    data: ReorderPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    """Set sort_order for units based on the provided ordered list."""
    await _require_organise_write(db, current_user, event_id)
    from app.models.allocation_unit import AllocationUnit
    from sqlalchemy import update as upd
    for i, unit_id in enumerate(data.ordered_ids):
        await db.execute(
            upd(AllocationUnit)
            .where(AllocationUnit.id == unit_id, AllocationUnit.category_id == category_id)
            .values(sort_order=i)
        )
    await db.flush()
    await _publish_organise_change(event_id, "units_reordered")



class CommitPayload(BaseModel):
    proposed: dict  # { unit_id: [participant_id, ...] }
    # v0.60c: optional reasoning payload forwarded from the preceding
    # engine run. When present, commit_proposal writes these into the
    # `meta` JSONB column of each emitted assign event, which the
    # InsightPanel History reads back in v0.60d to explain placements.
    # Legacy clients that don't include these fields still work — the
    # commit simply writes meta=None, matching pre-v0.60c behaviour.
    placement_reasons: dict | None = None  # { participant_id: {reason: str, ...} }
    engine_run_id: str | None = None       # correlation uuid from run_engine


@router.post("/allocation-categories/{category_id}/suggest")
async def api_suggest_allocation(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    mode: str = "replace",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Run the allocation engine for a category. Returns a proposal (not committed).

    Query param `mode`:
      - replace  (default) — reallocates everyone from scratch
      - top_up   — keeps existing allocations, only places unallocated participants
    """
    if mode not in ("replace", "top_up"):
        raise HTTPException(status_code=400, detail={"key": "errors.allocation.invalid_mode"})
    result = await run_engine(db, event_id, category_id, mode=mode)
    if "error_key" in result:
        raise HTTPException(status_code=400, detail={"key": result["error_key"]})
    await _publish_organise_change(event_id, "engine_ran")
    return result


@router.post("/allocation-categories/{category_id}/clear", status_code=200)
async def api_clear_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Clear all allocations for a category."""
    # v0.60a: attribute the clear to the acting organiser.
    count = await clear_category_allocations(
        db, event_id, category_id, actor_user_id=current_user.id
    )
    await _publish_organise_change(event_id, "category_cleared")
    return {"cleared": count}


@router.post("/allocation-categories/{category_id}/commit")
async def api_commit_proposal(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    data: CommitPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    """Commit a proposed allocation — clears existing, writes new."""
    # v0.60a: attribute every event emitted by the commit (both the
    # cleared unassigns and the freshly-written assigns) to the
    # acting organiser.
    # v0.60c: forward the engine's reasoning payload (if present)
    # into commit_proposal → meta JSONB on assign events.
    result = await commit_proposal(
        db, event_id, category_id, data.proposed,
        actor_user_id=current_user.id,
        placement_reasons=data.placement_reasons,
        engine_run_id=data.engine_run_id,
    )
    await _publish_organise_change(event_id, "proposal_committed")
    return result


# ─── Units ───

@router.get("/allocation-categories/{category_id}/units/")
async def api_list_units(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_units(db, category_id)


@router.post("/allocation-categories/{category_id}/units/", status_code=201)
async def api_create_unit(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    data: UnitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    await _require_organise_write(db, current_user, event_id)
    await _publish_organise_change(event_id, "unit_created")
    return await create_unit(db, category_id, **data.model_dump())


@router.patch("/allocation-categories/{category_id}/units/{unit_id}")
async def api_update_unit(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    unit_id: uuid.UUID,
    data: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    await _require_organise_write(db, current_user, event_id)
    await _publish_organise_change(event_id, "unit_updated")
    return await update_unit(db, unit_id, **data.model_dump(exclude_unset=True))


@router.delete("/allocation-categories/{category_id}/units/{unit_id}", status_code=204)
async def api_delete_unit(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    await _require_organise_write(db, current_user, event_id)
    deleted = await delete_unit(db, unit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"key": "errors.allocation.unit_not_found"})


# ─── Assignments ───
    await _publish_organise_change(event_id, "unit_deleted")

@router.post("/allocations/assign")
async def api_assign(
    event_id: uuid.UUID,
    data: AssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    unit = await get_unit(db, data.unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail={"key": "errors.allocation.unit_not_found"})
    await _require_organise_write(db, current_user, event_id)
    result = await assign_participant(
        db, event_id, data.unit_id, data.participant_id,
        actor_user_id=current_user.id,
    )
    await _publish_organise_change(event_id, "allocation_assigned")
    return result


@router.post("/allocations/move")
async def api_move(
    event_id: uuid.UUID,
    data: MoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    unit = await get_unit(db, data.to_unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail={"key": "errors.allocation.unit_not_found"})
    await _require_organise_write(db, current_user, event_id)
    result = await move_participant(
        db, event_id, data.to_unit_id, data.participant_id,
        actor_user_id=current_user.id,
    )
    await _publish_organise_change(event_id, "allocation_moved")
    return result


@router.delete("/allocations/unassign/{unit_id}/{participant_id}", status_code=204)
async def api_unassign(
    event_id: uuid.UUID,
    unit_id: uuid.UUID,
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    unit = await get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail={"key": "errors.allocation.unit_not_found"})
    await _require_organise_write(db, current_user, event_id)
    await unassign_participant(
        db, unit_id, participant_id,
        actor_user_id=current_user.id,
    )
    await _publish_organise_change(event_id, "allocation_unassigned")


@router.get("/allocations/by-category/{category_id}")
async def api_by_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_allocations_by_category(db, category_id)


@router.get("/allocations/all")
async def api_all_allocations(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_all_allocations(db, event_id)


# ─── Audit-log read (v0.60b) ───

@router.get("/allocation-events")
async def api_list_allocation_events(
    event_id: uuid.UUID,
    participant_id: uuid.UUID | None = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Return allocation events for this event, newest first.

    v0.60b: powers the "History" section inside InsightPanel. Primary
    caller filters by ``participant_id`` to show one person's timeline.
    Left unfiltered, returns the full event-wide timeline (reserved
    for future read surfaces; not wired in the UI yet).

    Admin-only: the audit log is considered management-level
    information. Regular staff do not see it. Note that we do NOT
    call ``ensure_event_writable`` — reading the audit log of an
    archived or closed event is expected and legitimate.

    Logic lives in allocation_events_service.list_allocation_events
    so it can be unit-tested without the HTTP test client (see
    tests/test_allocation_events.py).
    """
    from app.services.allocation_events_service import list_allocation_events
    return await list_allocation_events(
        db,
        event_id=event_id,
        participant_id=participant_id,
        limit=limit,
    )
