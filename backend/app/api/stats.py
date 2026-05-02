"""Stats routes — aggregate numbers for the Reports page.

v0.50g: provides pre-computed stats so the Reports page loads with a
single request instead of the client re-computing from allocation +
participant + category lists.

Permission:
  - admin OR staff with `reports: read`

The shape is deliberately narrow and aggregate — no PII, no per-participant
data — so that this is a natural home for the reports permission.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.participant import Participant, RegistrationStatus
from app.api.deps import get_current_user
from app.services.event_service import get_event_by_id
from app.services.allocation_service import list_categories
from app.services.permissions import get_event_permissions, has_read

router = APIRouter(prefix="/api/events/{event_id}", tags=["stats"])


async def _require_reports_read(db: AsyncSession, user: User, event_id: uuid.UUID):
    """Admin OR staff with `reports: read`."""
    if user.role == UserRole.SUPER_ADMIN:
        return
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or not has_read(perms, "reports"):
        raise HTTPException(status_code=403, detail={"key": "errors.stats.read_required"})


@router.get("/stats")
async def event_stats(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate stats for the Reports page.

    Returns:
      {
        "registration": {
          "confirmed": int,
          "pending": int,
          "cancelled": int,
          "total_active": int,     # confirmed + pending (what you'd normally "count")
        },
        "checkin": {
          "checked_in": int,
          "not_checked_in": int,
          "percent": int,          # 0–100, rounded
        },
        "allocation": {
          "category_count": int,
          "total_capacity": int,
          "total_occupied": int,
          "percent": int,          # 0–100, rounded, across ALL categories
          "per_category": [
            {
              "id": str, "name": str,
              "unit_count": int, "capacity": int, "occupied": int,
              "percent": int,
            },
            ...
          ],
        },
      }
    """
    await _require_reports_read(db, current_user, event_id)

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})

    # ─── Registration counts ────────────────────────────────────────────
    # Count active (non-soft-deleted) participants by status. Using
    # GROUP BY here keeps it to one query regardless of how many status
    # values exist.
    status_q = await db.execute(
        select(Participant.registration_status, func.count(Participant.id))
        .where(
            Participant.event_id == event_id,
            Participant.deleted_at.is_(None),
        )
        .group_by(Participant.registration_status)
    )
    status_counts = {status: n for status, n in status_q.all()}
    confirmed = status_counts.get(RegistrationStatus.CONFIRMED, 0)
    pending = status_counts.get(RegistrationStatus.PENDING, 0)
    cancelled = status_counts.get(RegistrationStatus.CANCELLED, 0)
    total_active = confirmed + pending

    # ─── Check-in counts ────────────────────────────────────────────────
    # Only counts confirmed+pending participants — cancelled shouldn't
    # contribute to the check-in progress bar.
    checkin_q = await db.execute(
        select(
            func.count(Participant.id).filter(Participant.checked_in == True),
        )
        .where(
            Participant.event_id == event_id,
            Participant.deleted_at.is_(None),
            Participant.registration_status != RegistrationStatus.CANCELLED,
        )
    )
    checked_in = checkin_q.scalar() or 0
    not_checked_in = max(0, total_active - checked_in)
    checkin_percent = round((checked_in / total_active) * 100) if total_active > 0 else 0

    # ─── Allocation progress per category ───────────────────────────────
    # v0.57b F4 fix: list_categories already returns total_capacity,
    # allocated_count, and unit_count (from the v0.57 aggregated rewrite),
    # so the per-category list_units() call is redundant. Query count
    # drops from (1 + 2N) to just the list_categories call.
    # v0.89 #29: add a participant-coverage metric — what fraction of
    # active (= confirmed + pending) registrants are allocated in this
    # category. This is the more meaningful headline number for the
    # Reports page; capacity-based % was easy to misread as "of
    # participants" when it's actually "of bed/seat slots".
    categories = await list_categories(db, event_id)
    per_category = []
    total_cap = 0
    total_occ = 0
    # Distinct participant ids that are placed somewhere across ALL
    # categories — used for the headline overall "% of participants
    # allocated" metric. Each pid counts once even if they're in
    # multiple categories.
    all_placed_pids: set[str] = set()

    # Pre-fetch allocations once per category (cheap with current schema).
    from app.services.allocation_service import get_allocations_by_category
    for cat in categories:
        cap = cat.get("total_capacity") or 0
        occ = cat.get("allocated_count", 0)
        # When a unit has no explicit capacity set, capacity-based percent
        # is meaningless. Default to 0 in that case; the UI can show "—".
        cap_pct = round((occ / cap) * 100) if cap > 0 else 0
        # Distinct participants placed in this category.
        cat_alloc = await get_allocations_by_category(db, cat["id"])
        cat_pids: set[str] = set()
        for unit_id, members in cat_alloc.items():
            for m in members:
                cat_pids.add(str(m["participant_id"]))
        all_placed_pids.update(cat_pids)
        # Participant-coverage % = distinct placed / active total.
        cov_pct = round((len(cat_pids) / total_active) * 100) if total_active > 0 else 0
        per_category.append({
            "id": str(cat["id"]),
            "name": cat["name"],
            "unit_count": cat.get("unit_count", 0),
            "capacity": cap,
            "occupied": occ,
            "percent": cap_pct,                     # capacity-based %
            "participants_placed": len(cat_pids),   # distinct placed in this cat
            "coverage_percent": cov_pct,            # distinct placed / total_active
        })
        total_cap += cap
        total_occ += occ

    overall_pct = round((total_occ / total_cap) * 100) if total_cap > 0 else 0
    # v0.89 #29: overall participant-coverage. % of active participants
    # placed in AT LEAST ONE category. The meaningful "are we done with
    # allocations?" metric for the Reports headline.
    coverage_overall_pct = (
        round((len(all_placed_pids) / total_active) * 100)
        if total_active > 0 else 0
    )

    return {
        "registration": {
            "confirmed": confirmed,
            "pending": pending,
            "cancelled": cancelled,
            "total_active": total_active,
        },
        "checkin": {
            "checked_in": checked_in,
            "not_checked_in": not_checked_in,
            "percent": checkin_percent,
        },
        "allocation": {
            "category_count": len(categories),
            "total_capacity": total_cap,
            "total_occupied": total_occ,
            "percent": overall_pct,
            # v0.89 #29: new participant-coverage fields.
            "participants_placed": len(all_placed_pids),
            "participants_total": total_active,
            "coverage_percent": coverage_overall_pct,
            "per_category": per_category,
        },
    }
