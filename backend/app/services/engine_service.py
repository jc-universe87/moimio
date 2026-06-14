"""Allocation engine — proposes a full allocation for a category in one shot.

Algorithm (v0.74 5-pass)
------------------------
PASS 1 — Group_code clusters
  Sort by size DESC; for each cluster (size >= 2):
    • Try smallest single unit that fits.
    • If no single fit, find smallest set of N units (N=2,3,...)
      whose combined remaining cap >= cluster size; split cluster
      evenly across that set (ceil(N/M) + floor(N/M)).
    • If exclusive_group_codes=true on the category: claim the
      unit fully (no other participants placed there even if
      leftover capacity remains).
    • If split_oversized_groups=false and no single fit: whole
      cluster -> unplaced with cluster_oversized_split_disabled,
      AND members are added to held_back so PASS 4 cannot pick
      them up as individuals (v1.0.0o — pre-1.0.0o the tag was
      advisory only and PASS 4a's gender_drain dissolved the
      cluster).
    • If no eligible unit exists at all (e.g. mixed-gender cluster
      vs gendered-only rooms) AND split_oversized_groups=false:
      whole cluster -> unplaced with cluster_no_eligible_unit,
      held_back populated. Metadata carries the cluster's gender
      mix and the unit restrictions in the category so the UI can
      render an actionable diagnostic (v1.0.0o).
  v0.74a: singletons (cluster of 1) skip PASS 1 — a "cluster of
  one" has no togetherness to preserve. They flow into PASS 4b
  alongside uncoded individuals.

PASS 2 — Mark "together" clusters
  For each mark in mark_priorities order with
  cluster_behaviour='together': form sub-cluster from participants
  with this primary mark (priority order resolves overlaps;
  group_code wins over marks). Place using same packing logic as
  PASS 1 but never trigger exclusive claim.

PASS 3 — Mark "split-evenly" pre-distribution
  For each mark in mark_priorities order with cluster_behaviour='split':
  find unplaced participants with this primary mark. Distribute
  evenly across eligible units (gender-permitting).

PASS 4a — Drain gender-restricted units
  For each restricted unit (cap ASC): pull eligible-gender
  participants from remaining pool until the unit fills or the
  pool is exhausted. Genderless cannot enter restricted units
  (v0.73a Bug 4 strict gender preserved).

PASS 4b — Round-robin remaining individuals
  Cap-ASC cursor walks unrestricted units; one cursor advance per
  placement. Skip ineligible/full units.

PASS 5 — Classify unplaced
  Anyone not placed gets a reason tag (cluster_oversized_split_disabled,
  gender_unknown_no_mixed_unit_available, or no_capacity_remaining).

Hard constraints (never violated):
  - Gender restriction on unit (matching unit.gender_restriction)
  - Capacity on unit (cap NOT NULL since v0.74)

Soft constraints (best-effort, in priority order):
  - Keep group_code clusters together (PASS 1)
  - Mark "together" clusters (PASS 2)
  - Mark "split-evenly" distribution (PASS 3)
  - Fair fill across remaining units (PASS 4)

Imbalance at small event scale — by design
------------------------------------------
v0.74's algorithm preserves cluster cohesion at the cost of room
balance. With a 9-person group_code cluster and 16 singletons across
2 rooms, the cluster lands in one room and round-robin distributes
the singletons 8/8 across both, producing a 17 / 8 final state.

This is mathematically correct and matches the design intent: the
whole point of a group_code cluster is "keep these people together."
At small event scale (<50 participants) a single cluster can produce
visible imbalance; at typical Moimio scale (>100 participants) the
imbalance dilutes into noise.

Organisers who want balance even at the cost of cluster togetherness
should use a mark with cluster_behaviour='split' instead of a
group_code. Group_code = "definitely keep together." Mark split =
"distribute evenly across rooms."

Output
------
{
  "proposed": { "unit_id": ["participant_id", ...], ... },
  "unplaced": ["participant_id", ...],
  "stats": {
    "total": int, "placed": int, "unplaced": int,
    "clusters_total": int, "clusters_kept_whole": int,
    "clusters_split": int, "mark_clusters": int,
    "mode": str, "already_allocated": int,
    "gender_unknown_placements": int,           # 0 in v0.74 (strict gender)
    "gender_unknown_placement_ids": list[str],  # [] in v0.74
  },
  "placement_reasons": { "participant_id": {reason, ...meta}, ... },
  "unplaced_reasons":  { "participant_id": {reason, ...meta}, ... },
  "run_id": str,
}
"""

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant, RegistrationStatus
from app.models.allocation_unit import AllocationUnit
from app.models.allocation_category import AllocationCategory
from app.models.allocation import Allocation
from app.models.allocation_event import AllocationEventSource, AllocationEventType
from app.models.mark import MarkAssignment
from app.services.allocation_events_service import record_allocation_event
from app.services.webhook_service import queue_event


DEFAULT_ENGINE_SETTINGS = {
    "use_group_codes": True,          # honour group_code clusters
    "group_remaining_by_gender": True, # prefer same gender when placing uncoded participants
    "split_oversized_groups": True,    # split clusters that don't fit one unit
    "mark_priorities": [],             # ordered list of mark definition UUIDs for soft grouping
    # v0.73b: include participants whose registration_status is PENDING
    # (haven't confirmed their email yet) in the engine's input. Default
    # ON because organisers seeing "25/29 zugewiesen" with 4 invisible
    # pending participants is the UX bug this setting addresses. Toggle
    # OFF to revert to confirmed-only allocation if the organiser
    # explicitly wants to wait for confirmations before allocating.
    "include_pending_in_allocation": True,
    # v1.0.0e: after the rule-based passes, run a final equalising sweep
    # that moves whole clusters between units to even out occupancies
    # (proportional to capacity). Hard rules — group codes, marks,
    # gender restrictions — are never overridden by this pass; only
    # clusters whose constraints are still satisfied at the
    # destination move. The pass touches `fill` singletons,
    # whole-placed group_code clusters, and whole-placed mark_together
    # clusters; it leaves split clusters, mark_split, and gender_drain
    # placements alone. Default ON; togglable per category.
    "equalise_after_allocation": True,
}


async def run_engine(
    db: AsyncSession,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    mode: str = "replace",  # "replace" | "top_up"
) -> dict:
    """Run the allocation engine for one category. Returns proposal dict.

    v0.74: rewritten as a 5-pass pass-based algorithm:

      PASS 1 — Group_code clusters (largest first, smallest fitting set,
               even split if no single-unit fit, exclusive flag respected)
      PASS 2 — Mark "together" clusters (priority order, same packing)
      PASS 3 — Mark "split-evenly" pre-distribution
      PASS 4a — Drain gender-restricted units with eligible-gender pool
      PASS 4b — Round-robin remaining individuals
                (per-eligibility-class cursor, cap ASC visit order)
      PASS 5 — Anyone unplaced → unplaced bucket with reason tag

    mode="replace"  — clears existing and reallocates everyone (default)
    mode="top_up"   — keeps existing allocations, only places unallocated
                      participants

    Returns a dict with the same shape as pre-v0.74 callers expect:
      proposed: {unit_id: [pid, ...]}
      unplaced: [pid, ...]
      stats: {total, placed, unplaced, ...}
      placement_reasons: {pid: {reason: str, ...tags}}
      unplaced_reasons: {pid: {reason: str, ...tags}}
      run_id: correlation uuid for this engine invocation

    Stats keys preserved for backward-compat:
      gender_unknown_placements, gender_unknown_placement_ids — both
      always 0/[] in v0.74 because strict-gender (v0.73a Bug 4) means
      genderless never enter restricted units.
    """

    # v0.60c: stable correlation id for every event this engine run
    # produces. Carries through into meta on each assign event.
    run_id = str(uuid.uuid4())

    # Per-participant reasoning. Populated by each placement.
    placement_reasons: dict[str, dict] = {}
    unplaced_reasons: dict[str, dict] = {}
    # v1.0.0o: cluster members tagged as "do not place individually".
    # Populated when a group_code cluster is rejected in PASS 1 under
    # split_oversized_groups=false (either no eligible unit at all, or
    # no single-unit fit and combos disabled). PASS 4a/4b filter
    # against this set so the engine actually honours the docstring
    # promise of "whole cluster -> unplaced". Pre-1.0.0o the tag went
    # only into unplaced_reasons (purely advisory) — PASS 4a would
    # then pick the members up as individuals via gender_drain.
    held_back: set[str] = set()

    # ── Setup: load category, units, settings, participants, marks ──

    cat_q = await db.execute(
        select(AllocationCategory).where(AllocationCategory.id == category_id)
    )
    cat = cat_q.scalar_one_or_none()
    if not cat:
        return {"error_key": "errors.allocation.group_type_not_found"}

    cat_settings = (cat.settings or {}).get("engine", {})
    use_group_codes = cat_settings.get("use_group_codes", DEFAULT_ENGINE_SETTINGS["use_group_codes"])
    group_by_gender = cat_settings.get("group_remaining_by_gender", DEFAULT_ENGINE_SETTINGS["group_remaining_by_gender"])
    split_groups = cat_settings.get("split_oversized_groups", DEFAULT_ENGINE_SETTINGS["split_oversized_groups"])
    # v1.0-pre #23: mark_priorities is normalised to a list of UUID strings
    # for the engine's priority-order semantics, plus a parallel
    # `mark_behaviour_overrides` dict for per-category cluster behaviour.
    # Two on-disk shapes are accepted for backward compatibility:
    #   - Legacy:  ["uuid1", "uuid2", ...]
    #     Behaviour comes from MarkDefinition.cluster_behaviour (global).
    #   - New:     [{"id": "uuid1", "behaviour": "together"}, ...]
    #     Behaviour from the entry overrides the global; entries without
    #     a behaviour key fall back to the global.
    raw_priorities = cat_settings.get("mark_priorities", []) or []
    mark_priorities: list[str] = []
    mark_behaviour_overrides: dict[str, str] = {}
    for entry in raw_priorities:
        if isinstance(entry, str):
            mark_priorities.append(entry)
        elif isinstance(entry, dict) and entry.get("id"):
            mid = str(entry["id"])
            mark_priorities.append(mid)
            beh = entry.get("behaviour")
            if beh in ("together", "split", "none"):
                mark_behaviour_overrides[mid] = beh
        # Anything else (None, empty, malformed) is silently skipped.
    include_pending = cat_settings.get(
        "include_pending_in_allocation",
        DEFAULT_ENGINE_SETTINGS["include_pending_in_allocation"],
    )
    # v1.0.0e: equalise sweep toggle (default ON).
    equalise_after_allocation = cat_settings.get(
        "equalise_after_allocation",
        DEFAULT_ENGINE_SETTINGS["equalise_after_allocation"],
    )
    # v0.74: per-category toggle. When True, group_code clusters claim
    # the entire unit they land in (no other participants placed there).
    exclusive_clusters = bool(getattr(cat, "exclusive_group_codes", False))

    units_q = await db.execute(
        select(AllocationUnit)
        .where(AllocationUnit.category_id == category_id)
        .order_by(AllocationUnit.sort_order, AllocationUnit.created_at)
    )
    units = list(units_q.scalars().all())
    if not units:
        return {"error_key": "errors.allocation.no_units"}

    if include_pending:
        eligible_statuses = [RegistrationStatus.CONFIRMED, RegistrationStatus.PENDING]
    else:
        eligible_statuses = [RegistrationStatus.CONFIRMED]
    parts_q = await db.execute(
        select(Participant).where(
            Participant.event_id == event_id,
            Participant.registration_status.in_(eligible_statuses),
            Participant.deleted_at.is_(None),
        )
    )
    participants = list(parts_q.scalars().all())

    if not participants:
        return _empty_return(units, mode, run_id)

    cat_id_str = str(category_id)

    # Mark assignments — load only when there are mark_priorities to honour.
    # participant_marks: pid → set of mark_ids (only marks in priorities list)
    participant_marks: dict[str, set[str]] = defaultdict(set)
    if mark_priorities:
        marks_q = await db.execute(
            select(MarkAssignment).where(
                MarkAssignment.event_id == event_id,
            )
        )
        for ma in marks_q.scalars().all():
            mid = str(ma.mark_id)
            if mid in mark_priorities:
                participant_marks[str(ma.participant_id)].add(mid)

    # Load mark definitions for cluster_behaviour lookup. Only need the
    # definitions for marks that appear in priorities.
    # v1.0-pre #23: per-category overrides from mark_behaviour_overrides
    # (set above from the new mark_priorities object shape) take precedence
    # over the global MarkDefinition.cluster_behaviour. This lets the same
    # mark drive different engine behaviours in different categories
    # (e.g. "Leader" = Keep together for Rooms, Spread evenly for Groups).
    mark_behaviours: dict[str, str] = {}
    if mark_priorities:
        from app.models.mark import MarkDefinition
        defs_q = await db.execute(
            select(MarkDefinition).where(
                MarkDefinition.event_id == event_id,
                MarkDefinition.id.in_([uuid.UUID(m) for m in mark_priorities]),
            )
        )
        for md in defs_q.scalars().all():
            mark_behaviours[str(md.id)] = getattr(md, "cluster_behaviour", None) or "none"
        # Apply per-category overrides on top.
        for mid, beh in mark_behaviour_overrides.items():
            mark_behaviours[mid] = beh

    # ── Initialise placement state ──
    # unit_slots[unit_id] = list of pids placed there
    unit_slots: dict[str, list[str]] = {str(u.id): [] for u in units}
    # exclusively-claimed unit IDs (PASS 1 may set these); excluded from later passes
    exclusive_units: set[str] = set()

    # top_up mode: load existing, seed unit_slots, filter pool
    already_allocated_pids: set[str] = set()
    if mode == "top_up":
        existing_q = await db.execute(
            select(Allocation).where(
                Allocation.event_id == event_id,
                Allocation.unit_id.in_([u.id for u in units]),
            )
        )
        for existing in existing_q.scalars().all():
            uid = str(existing.unit_id)
            pid = str(existing.participant_id)
            if uid in unit_slots:
                unit_slots[uid].append(pid)
            already_allocated_pids.add(pid)
        participants = [p for p in participants if str(p.id) not in already_allocated_pids]
        if not participants:
            return _everyone_already_allocated_return(unit_slots, already_allocated_pids, mode, run_id)

    # Helpers used across passes ─────────────────────────────────────

    def remaining_cap(unit_id: str) -> int:
        unit = _unit_by_id(units, unit_id)
        return unit.capacity - len(unit_slots[unit_id])

    def gender_eligible(unit: AllocationUnit, participant_gender: str | None) -> bool:
        """v0.74: read unit-level gender_restriction directly. The
        category-level has_gender_restriction toggle is deprecated and
        ignored. v0.73a Bug 4 strict gender preserved: unknown gender
        cannot enter restricted units.
        """
        if not unit.gender_restriction:
            return True  # mixed unit accepts anyone
        if not participant_gender:
            return False  # restricted + unknown → reject (Bug 4)
        return participant_gender.lower() == unit.gender_restriction.lower()

    def cluster_gender_eligible(unit: AllocationUnit, cluster_genders: list[str | None]) -> bool:
        """A cluster fits a unit only if every member can enter it."""
        return all(gender_eligible(unit, g) for g in cluster_genders)

    # ── PASS 1: group_code clusters ──
    clusters_total = 0
    clusters_kept_whole = 0
    clusters_split = 0
    placed_ids: set[str] = set()

    if use_group_codes:
        # Build clusters: group_code → list of participants.
        # Participants without group_code (or with group_code applied to
        # other categories) are skipped here; they go to PASS 4.
        clusters: dict[str, list[Participant]] = defaultdict(list)
        for p in participants:
            gc = (p.group_code or "").strip()
            if not gc:
                continue
            # Honour group_code_categories scope if set; default = all categories
            scope = p.group_code_categories
            if scope and cat_id_str not in [str(s) for s in scope]:
                continue
            clusters[gc].append(p)

        # v0.74a: filter out singletons (cluster-of-1). A cluster of one
        # has no togetherness to preserve — the whole point of PASS 1 is
        # keeping multi-person groups in the same unit. Treating
        # singletons as clusters causes starvation: PASS 1 places them
        # via "smallest-fitting unit" which devolves into "most-filled
        # non-full unit" for size-1 clusters, piling them all into the
        # first unit. Filtering here lets singletons flow into PASS 4b
        # round-robin alongside uncoded individuals, where the cap-ASC
        # cursor distributes them fairly.
        clusters = {gc: members for gc, members in clusters.items() if len(members) >= 2}

        # Sort by size desc; stable by group_code for deterministic order
        cluster_list = sorted(clusters.items(), key=lambda x: (-len(x[1]), x[0]))
        clusters_total = len(cluster_list)

        for gc, members in cluster_list:
            placed_in_cluster, was_split = _place_cluster(
                cluster_members=members,
                cluster_id=gc,
                cluster_kind="group_code",
                units=units,
                unit_slots=unit_slots,
                exclusive_units=exclusive_units,
                exclusive_flag=exclusive_clusters,
                split_groups=split_groups,
                placed_ids=placed_ids,
                placement_reasons=placement_reasons,
                unplaced_reasons=unplaced_reasons,
                held_back=held_back,
                gender_eligible=gender_eligible,
                cluster_gender_eligible=cluster_gender_eligible,
                remaining_cap=remaining_cap,
                units_by_id={str(u.id): u for u in units},
            )
            if placed_in_cluster:
                if was_split:
                    clusters_split += 1
                else:
                    clusters_kept_whole += 1

    # ── Determine each remaining participant's "primary mark" for PASS 2/3 ──
    # Primary mark = highest-priority mark (in mark_priorities order) that
    # the participant has AND that has cluster_behaviour != 'none'.
    # Group_code wins: if participant was placed in PASS 1, they're skipped.
    primary_mark: dict[str, str | None] = {}
    for p in participants:
        pid = str(p.id)
        if pid in placed_ids:
            continue  # group_code took priority
        marks_for_p = participant_marks.get(pid, set())
        chosen = None
        for prio_mid in mark_priorities:  # priority order
            if prio_mid in marks_for_p and mark_behaviours.get(prio_mid, "none") != "none":
                chosen = prio_mid
                break
        primary_mark[pid] = chosen

    # ── PASS 2: mark "together" clusters in priority order ──
    mark_clusters_count = 0
    for prio_mid in mark_priorities:
        if mark_behaviours.get(prio_mid) != "together":
            continue
        # Gather participants whose primary mark is this one.
        members = [
            p for p in participants
            if str(p.id) not in placed_ids
            and primary_mark.get(str(p.id)) == prio_mid
        ]
        if not members:
            continue
        mark_clusters_count += 1
        _place_cluster(
            cluster_members=members,
            cluster_id=f"mark:{prio_mid}",
            cluster_kind="mark_together",
            units=units,
            unit_slots=unit_slots,
            exclusive_units=exclusive_units,
            exclusive_flag=False,  # marks never trigger exclusive
            split_groups=split_groups,
            placed_ids=placed_ids,
            placement_reasons=placement_reasons,
            unplaced_reasons=unplaced_reasons,
            held_back=held_back,
            gender_eligible=gender_eligible,
            cluster_gender_eligible=cluster_gender_eligible,
            remaining_cap=remaining_cap,
            units_by_id={str(u.id): u for u in units},
        )

    # ── PASS 3: mark "split-evenly" pre-distribution ──
    for prio_mid in mark_priorities:
        if mark_behaviours.get(prio_mid) != "split":
            continue
        members = [
            p for p in participants
            if str(p.id) not in placed_ids
            and primary_mark.get(str(p.id)) == prio_mid
        ]
        if not members:
            continue
        # Eligible units: not exclusive-claimed, has remaining cap.
        # Per-participant gender eligibility checked when picking.
        # Sort eligible units cap ASC (small units fill first).
        eligible_units = sorted(
            [u for u in units if str(u.id) not in exclusive_units and remaining_cap(str(u.id)) > 0],
            key=lambda u: (u.capacity, u.sort_order, u.created_at),
        )
        if not eligible_units:
            continue
        # Distribute round-robin across eligible_units. Each member is
        # placed in the next eligible unit (gender + cap permitting).
        unit_cursor = 0
        for participant in members:
            placed_here = False
            for _ in range(len(eligible_units)):
                u = eligible_units[unit_cursor % len(eligible_units)]
                unit_cursor += 1
                if remaining_cap(str(u.id)) > 0 and gender_eligible(u, participant.gender):
                    unit_slots[str(u.id)].append(str(participant.id))
                    placed_ids.add(str(participant.id))
                    placement_reasons[str(participant.id)] = {
                        "reason": "mark_split",
                        "mark_id": prio_mid,
                    }
                    placed_here = True
                    break
            if not placed_here:
                # No eligible unit had room — falls to PASS 4 logic
                # which will try restricted-drain or round-robin again,
                # OR end up unplaced with no_capacity_remaining.
                pass

    # ── PASS 4a: drain gender-restricted units ──
    # For each restricted unit (cap ASC), pull eligible-gender participants
    # from the remaining pool until the unit is full or the gender pool
    # is exhausted.
    restricted_units = sorted(
        [u for u in units if u.gender_restriction and str(u.id) not in exclusive_units],
        key=lambda u: (u.capacity, u.sort_order, u.created_at),
    )
    remaining = [
        p for p in participants
        if str(p.id) not in placed_ids
        and str(p.id) not in held_back  # v1.0.0o: cluster rejected → keep out
    ]
    for u in restricted_units:
        rest = u.gender_restriction.lower()
        free = remaining_cap(str(u.id))
        if free <= 0:
            continue
        # Eligible: participant gender matches the unit's restriction
        eligible = [p for p in remaining if p.gender and p.gender.lower() == rest]
        # Take up to `free` of them
        take = eligible[:free]
        for p in take:
            unit_slots[str(u.id)].append(str(p.id))
            placed_ids.add(str(p.id))
            placement_reasons[str(p.id)] = {
                "reason": "gender_drain",
                "unit_id": str(u.id),
                "unit_name": u.name,
                "gender_restriction": rest,
            }
        # Remove placed from `remaining`
        remaining = [p for p in remaining if str(p.id) not in placed_ids]

    # ── PASS 4b: round-robin remaining into unrestricted units ──
    # Per-eligibility-class cursor: separate cursor for each gender bucket
    # over its eligible units. Eligible = unrestricted (no gender_restriction)
    # AND not exclusive-claimed. (Gender bucket = participant's gender; the
    # set of eligible units is the same for all because we're past restricted
    # units now.)
    unrestricted_units = sorted(
        [u for u in units if not u.gender_restriction and str(u.id) not in exclusive_units],
        key=lambda u: (u.capacity, u.sort_order, u.created_at),
    )

    # Process remaining in interleaved gender order if group_by_gender,
    # else in input order.
    if group_by_gender:
        male_pool = [p for p in remaining if p.gender and p.gender.lower() == "male"]
        female_pool = [p for p in remaining if p.gender and p.gender.lower() == "female"]
        other_pool = [p for p in remaining if not p.gender or p.gender.lower() not in ("male", "female")]
        remaining = _interleave(male_pool, female_pool, other_pool)

    # Per-eligibility-class cursors. For unrestricted units, the eligible
    # set is the same regardless of participant gender (all unrestricted
    # accept any gender, including unknown). One shared cursor suffices.
    cursor = 0
    for participant in remaining:
        if not unrestricted_units:
            break
        placed_here = False
        # Walk unit list at most once
        for _ in range(len(unrestricted_units)):
            u = unrestricted_units[cursor % len(unrestricted_units)]
            cursor += 1
            if remaining_cap(str(u.id)) > 0 and gender_eligible(u, participant.gender):
                unit_slots[str(u.id)].append(str(participant.id))
                placed_ids.add(str(participant.id))
                placement_reasons[str(participant.id)] = {
                    "reason": "fill",
                    "unit_id": str(u.id),
                }
                placed_here = True
                break
        if not placed_here:
            # No unrestricted unit available; will fall to unplaced.
            pass

    # ── PASS 4c (v1.0.0e): equalising sweep ──
    # After all rule-based passes, optionally rebalance unit
    # occupancies by moving whole clusters from over-full units to
    # under-full ones. The sweep operates on CLUSTERS (groups of
    # participants the engine treats as one unit of placement) so
    # that members are never separated by this pass:
    #
    #   - cluster-of-one: any participant placed via `fill` in PASS 4b
    #   - whole group_code cluster: PASS 1 reason `group_code` (not split)
    #   - whole mark_together cluster: PASS 2 reason `mark_together` (not split)
    #
    # NOT moved: split clusters (`*_split`), `mark_split` (PASS 2
    # spread participants — already intentionally distributed),
    # `gender_drain` (PASS 4a — moving them would undo the engine's
    # capacity-fill of restricted units).
    #
    # Constraints honoured at every candidate move:
    #   - destination unit has remaining capacity
    #   - destination unit's gender restriction (if any) accepts every
    #     cluster member's gender
    #   - destination unit is not exclusively claimed by another cluster
    #
    # Greedy heuristic: while an improving move exists,
    #   1. find the most over-target unit O (highest occupancy ratio)
    #   2. find the most under-target unit U (lowest occupancy ratio)
    #   3. find the smallest movable cluster in O whose move to U
    #      shrinks the gap between their two ratios
    #   4. apply the move; loop until no improvement is found
    #
    # The pass terminates either when no improving move exists or when
    # an iteration cap is hit (defensive — should never engage on
    # well-formed inputs but prevents pathological loops).
    #
    # Audit trail: when a cluster is moved, every member's
    # placement_reason is rewritten to:
    #
    #   {"reason": "equalise",
    #    "from_unit_id": "<original>",
    #    "to_unit_id":   "<new>",
    #    "previous": {<the original placement_reason dict>}}
    #
    # The `previous` payload preserves WHY the participant was
    # originally clustered there, so the (i) panel and review
    # popover can show both lines: "placed with group SMITH (4
    # people)" and "moved to even out unit sizes".
    if equalise_after_allocation:
        _equalise_sweep(
            units=units,
            unit_slots=unit_slots,
            exclusive_units=exclusive_units,
            placement_reasons=placement_reasons,
            participants=participants,
            gender_eligible=gender_eligible,
            cluster_gender_eligible=cluster_gender_eligible,
        )

    # ── PASS 5: classify unplaced ──
    all_ids = {str(p.id) for p in participants}
    unplaced_ids = list(all_ids - placed_ids)

    if unplaced_ids:
        participant_by_id = {str(p.id): p for p in participants}
        any_mixed_unit_in_category = any(not u.gender_restriction for u in units)
        for pid in unplaced_ids:
            if pid in unplaced_reasons:
                continue  # cluster path may have tagged earlier
            p = participant_by_id.get(pid)
            if p is None:
                continue
            if not p.gender and not any_mixed_unit_in_category:
                unplaced_reasons[pid] = {
                    "reason": "gender_unknown_no_mixed_unit_available",
                }
            else:
                unplaced_reasons[pid] = {
                    "reason": "no_capacity_remaining",
                }

    # ── Build return ──
    return {
        "proposed": unit_slots,
        "unplaced": unplaced_ids,
        "stats": {
            "total": len(participants) + len(already_allocated_pids),
            "placed": len(placed_ids) + len(already_allocated_pids),
            "unplaced": len(unplaced_ids),
            "clusters_total": clusters_total,
            "clusters_kept_whole": clusters_kept_whole,
            "clusters_split": clusters_split,
            "mark_clusters": mark_clusters_count,
            "mode": mode,
            "already_allocated": len(already_allocated_pids),
            # v0.74: strict gender means 0 fallback placements; preserved
            # for backward-compat with stats consumers.
            "gender_unknown_placements": 0,
            "gender_unknown_placement_ids": [],
        },
        "placement_reasons": placement_reasons,
        "unplaced_reasons": unplaced_reasons,
        "run_id": run_id,
    }


# ── Helper functions for run_engine ─────────────────────────────────


def _unit_by_id(units: list, unit_id: str):
    """Linear lookup; units is small (typically <50)."""
    for u in units:
        if str(u.id) == unit_id:
            return u
    return None


def _interleave(*pools):
    """Round-robin through the given pools, yielding one from each in
    rotation. Empty pools are skipped.
    """
    pools = [list(p) for p in pools]
    out = []
    while any(pools):
        for p in pools:
            if p:
                out.append(p.pop(0))
    return out


def _empty_return(units, mode, run_id):
    """Stats dict shape for the no-participants early return."""
    return {
        "proposed": {str(u.id): [] for u in units},
        "unplaced": [],
        "stats": {
            "total": 0, "placed": 0, "unplaced": 0,
            "clusters_total": 0, "clusters_kept_whole": 0,
            "clusters_split": 0, "mark_clusters": 0,
            "mode": mode, "already_allocated": 0,
            "gender_unknown_placements": 0,
            "gender_unknown_placement_ids": [],
        },
        "placement_reasons": {},
        "unplaced_reasons": {},
        "run_id": run_id,
    }


def _everyone_already_allocated_return(unit_slots, already_allocated_pids, mode, run_id):
    """Stats dict shape for the top_up everyone-allocated early return."""
    return {
        "proposed": unit_slots,
        "unplaced": [],
        "stats": {
            "total": len(already_allocated_pids),
            "placed": len(already_allocated_pids),
            "unplaced": 0,
            "clusters_total": 0,
            "clusters_kept_whole": 0,
            "clusters_split": 0,
            "mark_clusters": 0,
            "mode": mode,
            "already_allocated": len(already_allocated_pids),
            "gender_unknown_placements": 0,
            "gender_unknown_placement_ids": [],
        },
        "placement_reasons": {},
        "unplaced_reasons": {},
        "run_id": run_id,
    }


def _place_cluster(
    *,
    cluster_members,
    cluster_id,
    cluster_kind,  # "group_code" or "mark_together"
    units,
    unit_slots,
    exclusive_units,
    exclusive_flag,  # if True, claim the unit exclusively
    split_groups,
    placed_ids,
    placement_reasons,
    unplaced_reasons,
    held_back,  # v1.0.0o: members tagged here are kept out of PASS 4
    gender_eligible,
    cluster_gender_eligible,
    remaining_cap,
    units_by_id=None,  # v1.0.0o: lookup for restriction inventory in error meta
):
    """Place a single cluster (group_code or mark_together) per the
    v0.74 spec:
      1. Try smallest single unit that fits.
      2. If no single fit, try smallest set of N units (N=2,3,...) whose
         combined remaining cap >= cluster size.
      3. Within a chosen set, split cluster as evenly as possible
         (⌈N/M⌉ and ⌊N/M⌋).
      4. If no combo of any size fits AND split_groups is False:
         whole cluster → unplaced with cluster_oversized_split_disabled.
      5. If split_groups is True but no combo fits: place as much as
         possible into the largest available combo; remainder unplaced
         with no_capacity_remaining.

    Returns (placed_anyone: bool, was_split: bool).
    """
    cluster_size = len(cluster_members)
    cluster_genders = [p.gender for p in cluster_members]
    # v1.0.0e: pre-compute the cluster member snapshot ONCE per cluster
    # call. Carried into every placement_reasons entry below so the
    # frontend can render "with X, Y, Z" on hover/tap (live surfaces)
    # and inline in audit-trail history rows. Names are PII but get
    # the same treatment as unit_name_snapshot in allocation_events:
    # snapshotted into the JSONB meta where they survive as audit
    # forensics. Right-to-erasure cascades to NULL the FK on the
    # outer event row; the snapshot inside JSONB persists, matching
    # the existing snapshot policy. Including `id` lets future UI
    # link back to the participant when they still exist.
    cluster_member_snapshot = [
        {
            "id": str(m.id),
            "name": f"{m.first_name or ''} {m.last_name or ''}".strip(),
        }
        for m in cluster_members
    ]

    # Eligible units: not exclusive-claimed by another cluster, gender-fits
    # the cluster as a whole.
    candidate_units = [
        u for u in units
        if str(u.id) not in exclusive_units
        and cluster_gender_eligible(u, cluster_genders)
    ]
    if not candidate_units:
        # No unit can hold this cluster. Tag and return.
        # v1.0.0o: distinguish "no unit is eligible at all" (e.g. mixed-
        # gender cluster vs gendered-only rooms) from the original
        # "oversized vs any single unit" meaning. The new reason tag
        # surfaces the actionable signal: cluster genders vs available
        # restrictions. Both branches populate held_back so PASS 4
        # cannot pick the cluster members up as individuals.
        if cluster_kind == "group_code" and not split_groups:
            # Build a snapshot of unit restrictions for the error UI.
            if units_by_id is not None:
                restrictions_seen = sorted({
                    (u.gender_restriction or "").lower()
                    for u in units_by_id.values()
                    if (u.gender_restriction or "").strip()
                })
            else:
                restrictions_seen = []
            cluster_gender_snapshot = sorted({
                (g or "unknown").lower() for g in cluster_genders
            })
            for p in cluster_members:
                unplaced_reasons[str(p.id)] = {
                    "reason": "cluster_no_eligible_unit",
                    "cluster_size": cluster_size,
                    "group_code": cluster_id,
                    "cluster_genders": cluster_gender_snapshot,
                    "available_restrictions": restrictions_seen,
                }
                held_back.add(str(p.id))
        else:
            for p in cluster_members:
                unplaced_reasons[str(p.id)] = {
                    "reason": "no_capacity_remaining",
                }
        return False, False

    # Try single-unit fit: smallest cap >= size, then most-perfect-fit.
    single_fits = sorted(
        [u for u in candidate_units if remaining_cap(str(u.id)) >= cluster_size],
        key=lambda u: (u.capacity, remaining_cap(str(u.id)), u.sort_order, u.created_at),
    )
    if single_fits:
        u = single_fits[0]
        for p in cluster_members:
            unit_slots[str(u.id)].append(str(p.id))
            placed_ids.add(str(p.id))
            placement_reasons[str(p.id)] = {
                "reason": cluster_kind,
                "cluster_id": cluster_id,
                "cluster_size": cluster_size,
                "cluster_placed_here": cluster_size,
                "unit_id": str(u.id),
                "cluster_members": cluster_member_snapshot,
            }
        if exclusive_flag:
            exclusive_units.add(str(u.id))
        return True, False  # placed; not split

    # Try multi-unit combos starting from N=2.
    if not split_groups and cluster_kind == "group_code":
        # v1.0.0o: whole cluster → unplaced AND held back from PASS 4.
        # This is the original meaning of cluster_oversized_split_disabled:
        # eligible units exist, but no single one is large enough, and
        # the organiser has opted out of multi-unit splits.
        for p in cluster_members:
            unplaced_reasons[str(p.id)] = {
                "reason": "cluster_oversized_split_disabled",
                "cluster_size": cluster_size,
                "group_code": cluster_id,
            }
            held_back.add(str(p.id))
        return False, False

    for n in range(2, len(candidate_units) + 1):
        combo = _smallest_set_that_fits(candidate_units, cluster_size, n, remaining_cap)
        if combo:
            # Split cluster evenly across combo.
            shares = _even_split(cluster_size, len(combo))
            idx = 0
            for u, share in zip(combo, shares):
                # Cap share to actual remaining capacity (defensive)
                share = min(share, remaining_cap(str(u.id)))
                for _ in range(share):
                    if idx >= cluster_size:
                        break
                    p = cluster_members[idx]
                    unit_slots[str(u.id)].append(str(p.id))
                    placed_ids.add(str(p.id))
                    placement_reasons[str(p.id)] = {
                        "reason": f"{cluster_kind}_split",
                        "cluster_id": cluster_id,
                        "cluster_size": cluster_size,
                        "cluster_placed_here": share,
                        "unit_id": str(u.id),
                        "cluster_members": cluster_member_snapshot,
                    }
                    idx += 1
                if exclusive_flag:
                    exclusive_units.add(str(u.id))
            # Anyone left over (shouldn't happen if combo math was right)
            # gets unplaced with no_capacity_remaining.
            while idx < cluster_size:
                p = cluster_members[idx]
                unplaced_reasons[str(p.id)] = {
                    "reason": "no_capacity_remaining",
                }
                idx += 1
            return True, True  # placed; split

    # No combo of any size fits — split_groups=true but pool exceeds total cap.
    # Place as much as possible across all candidate units.
    sorted_for_overflow = sorted(
        candidate_units,
        key=lambda u: (-remaining_cap(str(u.id)), u.sort_order, u.created_at),
    )
    idx = 0
    for u in sorted_for_overflow:
        free = remaining_cap(str(u.id))
        for _ in range(free):
            if idx >= cluster_size:
                break
            p = cluster_members[idx]
            unit_slots[str(u.id)].append(str(p.id))
            placed_ids.add(str(p.id))
            placement_reasons[str(p.id)] = {
                "reason": f"{cluster_kind}_split",
                "cluster_id": cluster_id,
                "cluster_size": cluster_size,
                "cluster_placed_here": free,
                "unit_id": str(u.id),
                "cluster_members": cluster_member_snapshot,
            }
            idx += 1
        if exclusive_flag:
            exclusive_units.add(str(u.id))
        if idx >= cluster_size:
            break
    while idx < cluster_size:
        p = cluster_members[idx]
        unplaced_reasons[str(p.id)] = {
            "reason": "no_capacity_remaining",
        }
        idx += 1
    return idx > 0, True


def _smallest_set_that_fits(units, cluster_size, n, remaining_cap):
    """Find the N-unit combo with smallest total remaining cap that
    still >= cluster_size. Returns the combo list, or None if no combo
    of size N fits.

    For the typical Moimio scale (≤30 units per category), the
    combinatorial cost is acceptable. For larger N this would need a
    smarter algorithm, but the 5-pass spec uses this only for
    oversized clusters which are rare.
    """
    from itertools import combinations
    sorted_units = sorted(units, key=lambda u: u.capacity)
    best = None
    best_total = None
    for combo in combinations(sorted_units, n):
        total = sum(remaining_cap(str(u.id)) for u in combo)
        if total >= cluster_size:
            if best_total is None or total < best_total:
                best = list(combo)
                best_total = total
    return best


def _even_split(total, parts):
    """Split `total` across `parts` slots as evenly as possible.
    Returns a list of length `parts` summing to `total` where each
    element is ⌈total/parts⌉ or ⌊total/parts⌋.
    Larger shares come first.
    """
    base = total // parts
    rem = total % parts
    return [base + 1] * rem + [base] * (parts - rem)


# ── PASS 4c equalising sweep helpers (v1.0.0e) ─────────────────────────


# Iteration cap on the equalise loop. Each iteration moves at most one
# cluster, so a category with N units bounded by reasonable cluster
# sizes converges in O(N) iterations. The cap is defensive against
# pathological loops; production should converge in tens of iterations.
_EQUALISE_MAX_ITERATIONS = 200

# Reasons that mark a placement as "movable as a single unit" by the
# equalising sweep. `fill` is treated as a cluster of one.
_EQUALISE_MOVABLE_REASONS = frozenset({"fill", "group_code", "mark_together"})


def _equalise_sweep(
    *,
    units,
    unit_slots: dict[str, list[str]],
    exclusive_units: set[str],
    placement_reasons: dict[str, dict],
    participants,
    gender_eligible,
    cluster_gender_eligible,
):
    """v1.0.0e PASS 4c — even out unit occupancies by moving whole
    movable clusters from over-target to under-target units.

    Operates in-place on ``unit_slots`` and ``placement_reasons``.
    Honours every hard constraint already enforced by earlier passes;
    the sweep is purely an evenness improvement and never violates
    capacity, gender restriction, or exclusive-cluster rules.

    Movable cluster = the set of pids that share the same
    ``placement_reason.cluster_id`` (for whole group_code or
    mark_together clusters) OR a single pid with reason `fill`.
    Split clusters, mark_split, and gender_drain are NOT eligible
    for movement — see module-level discussion in PASS 4c.
    """
    if not units:
        return

    # Build participant lookup once for gender eligibility checks.
    participant_by_id = {str(p.id): p for p in participants}

    # Helper: is this unit's projected occupancy (after a hypothetical
    # cluster move of `delta`) within capacity? Capacity may be 0/None
    # for non-capacitated categories — in which case no upper bound,
    # but we still skip moves that would worsen evenness purely on
    # occupant count.
    def fits_capacity(unit, current_count: int, delta: int) -> bool:
        if not unit.capacity:
            return True
        return (current_count + delta) <= unit.capacity

    # Build cluster index from placement_reasons.
    # Returns dict: cluster_key → {pids: [...], unit_id, kind, reason_payload}
    # cluster_key is `(reason, cluster_id)` for clusters or
    # `("fill", pid)` for solo fills.
    def build_cluster_index() -> dict:
        clusters: dict[tuple, dict] = {}
        # Index unit each pid is in
        pid_to_unit: dict[str, str] = {}
        for uid, pids in unit_slots.items():
            for pid in pids:
                pid_to_unit[pid] = uid

        for pid, reason_payload in placement_reasons.items():
            reason = reason_payload.get("reason")
            if reason not in _EQUALISE_MOVABLE_REASONS:
                continue
            uid = pid_to_unit.get(pid)
            if uid is None:
                continue  # Defensive: should never happen.
            if reason == "fill":
                key = ("fill", pid)
                clusters[key] = {
                    "pids": [pid],
                    "unit_id": uid,
                    "kind": "fill",
                    "previous": dict(reason_payload),
                }
                continue
            cluster_id = reason_payload.get("cluster_id")
            if cluster_id is None:
                continue  # Whole cluster reasons should always carry cluster_id.
            key = (reason, cluster_id)
            entry = clusters.setdefault(
                key,
                {
                    "pids": [],
                    "unit_id": uid,
                    "kind": reason,
                    "previous": dict(reason_payload),
                },
            )
            # All members of a whole cluster share a unit by construction
            # (a "split" cluster carries `*_split`, which is not movable).
            # Defensive: if we see a different unit for the same cluster
            # key, the cluster has already been split — skip it.
            if entry["unit_id"] != uid:
                entry["_inconsistent"] = True
            entry["pids"].append(pid)

        # Drop clusters that were split across units (defensive).
        return {
            k: v for k, v in clusters.items()
            if not v.get("_inconsistent") and v["pids"]
        }

    # Compute occupancy ratio for a unit. For uncapacitated categories,
    # treat each unit as having capacity = (sum of all occupants /
    # number of units) so they normalise to an even-fill target.
    total_capacity = sum((u.capacity or 0) for u in units)
    use_proportional = total_capacity > 0

    def ratio(unit) -> float:
        count = len(unit_slots[str(unit.id)])
        if use_proportional and unit.capacity:
            return count / unit.capacity
        if not use_proportional:
            return float(count)
        # Capacity-mixed: capacitated units normalised, uncapacitated
        # treated as full (don't move into them).
        return 1.0 if not unit.capacity else (count / unit.capacity)

    # Pre-compute cluster genders for eligibility tests against
    # destination units.
    def cluster_genders(pids: list[str]) -> list:
        out = []
        for pid in pids:
            p = participant_by_id.get(pid)
            out.append(p.gender if p else None)
        return out

    iterations = 0
    while iterations < _EQUALISE_MAX_ITERATIONS:
        iterations += 1
        clusters = build_cluster_index()
        if not clusters:
            return

        # Sort units by current ratio. Source candidates: high → low.
        # Destination candidates: low → high.
        units_sorted_high = sorted(units, key=ratio, reverse=True)
        units_sorted_low = sorted(units, key=ratio)

        moved = False
        for src_unit in units_sorted_high:
            src_uid = str(src_unit.id)
            src_ratio = ratio(src_unit)
            if src_ratio <= 0:
                break  # Source pile is empty or below — nothing useful left.

            # Eligible source clusters: those that live in this unit
            # and have movable kind. Sort by size ascending — smaller
            # clusters move more cheaply and produce finer-grained
            # rebalancing.
            src_clusters = [
                (key, info) for key, info in clusters.items()
                if info["unit_id"] == src_uid
            ]
            src_clusters.sort(key=lambda kv: len(kv[1]["pids"]))

            for cluster_key, cluster_info in src_clusters:
                cl_size = len(cluster_info["pids"])
                cl_genders = cluster_genders(cluster_info["pids"])

                for dst_unit in units_sorted_low:
                    dst_uid = str(dst_unit.id)
                    if dst_uid == src_uid:
                        continue
                    if dst_uid in exclusive_units:
                        continue
                    if not cluster_gender_eligible(dst_unit, cl_genders):
                        continue
                    dst_count = len(unit_slots[dst_uid])
                    if not fits_capacity(dst_unit, dst_count, cl_size):
                        continue
                    # Improvement check: does the move bring src_ratio
                    # and dst_ratio closer together? Compute projected
                    # ratios after the hypothetical move.
                    src_count_after = len(unit_slots[src_uid]) - cl_size
                    dst_count_after = dst_count + cl_size
                    if use_proportional and src_unit.capacity and dst_unit.capacity:
                        new_src = src_count_after / src_unit.capacity
                        new_dst = dst_count_after / dst_unit.capacity
                    else:
                        new_src = float(src_count_after)
                        new_dst = float(dst_count_after)
                    dst_ratio = ratio(dst_unit)
                    # Strict improvement: reduce the gap between this
                    # source–destination pair, AND don't overshoot
                    # (after the move, the destination shouldn't be
                    # MORE over-target than the source was before, or
                    # we just swapped the imbalance).
                    if abs(new_src - new_dst) >= abs(src_ratio - dst_ratio):
                        continue
                    if new_dst > src_ratio:
                        continue
                    # Apply the move.
                    pids = list(cluster_info["pids"])
                    for pid in pids:
                        unit_slots[src_uid].remove(pid)
                        unit_slots[dst_uid].append(pid)
                        # Rewrite placement_reason: wrap the original
                        # reason in `previous`. If the placement was
                        # already an equalise (shouldn't happen this
                        # round, defensive against future passes), peel
                        # one layer to keep `previous` pointing at the
                        # original cluster reason — never nest.
                        prior = cluster_info["previous"]
                        if prior.get("reason") == "equalise":
                            prior = prior.get("previous") or prior
                        placement_reasons[pid] = {
                            "reason": "equalise",
                            "from_unit_id": src_uid,
                            "to_unit_id": dst_uid,
                            "previous": prior,
                        }
                    moved = True
                    break  # Break inner dst loop — re-evaluate state.
                if moved:
                    break
            if moved:
                break

        if not moved:
            return  # Converged.




async def clear_category_allocations(
    db: AsyncSession,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
    source: str = AllocationEventSource.CLEAR_CATEGORY,
) -> int:
    """Delete all allocations in a category. Returns count deleted.

    v0.60a: emits an `unassign` AllocationEvent per deleted row. The
    `source` parameter distinguishes the two callers:

      - API manual-clear endpoint: ``source=CLEAR_CATEGORY`` (default)
      - ``commit_proposal`` (engine path): passes ``source=ENGINE_COMMIT``

    Unit + category names are snapshotted from the joined query, so
    the audit log survives subsequent renames or deletion of the
    category itself.
    """
    # v50c-3: clearing is an edit → revert confirmed if applicable.
    from app.services.allocation_service import _unconfirm_category_if_confirmed
    await _unconfirm_category_if_confirmed(db, category_id)

    # Fetch category once for its name snapshot.
    cat_q = await db.execute(
        select(AllocationCategory).where(AllocationCategory.id == category_id)
    )
    cat = cat_q.scalar_one_or_none()
    # If the category has vanished we still delete the rows but use a
    # placeholder name — this path shouldn't fire in practice.
    category_name = cat.name if cat else "[deleted category]"

    # Load allocations + their unit (for unit_name snapshot) in one query.
    result = await db.execute(
        select(Allocation, AllocationUnit)
        .join(AllocationUnit, Allocation.unit_id == AllocationUnit.id)
        .where(
            AllocationUnit.category_id == category_id,
            Allocation.event_id == event_id,
        )
    )
    rows = result.all()
    count = len(rows)
    for alloc, unit in rows:
        await record_allocation_event(
            db,
            event_id=event_id,
            participant_id=alloc.participant_id,
            unit_id=unit.id,
            category_id=category_id,
            unit_name_snapshot=unit.name,
            category_name_snapshot=category_name,
            event_type=AllocationEventType.UNASSIGN,
            source=source,
            actor_user_id=actor_user_id,
        )
        await db.delete(alloc)
    await db.flush()
    return count


async def commit_proposal(
    db: AsyncSession,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    proposed: dict[str, list[str]],
    *,
    actor_user_id: uuid.UUID | None = None,
    placement_reasons: dict[str, dict] | None = None,
    engine_run_id: str | None = None,
) -> dict:
    """Clear category and write the proposed allocation. Returns counts.

    v0.60a: both the clearing pass and the writing pass emit
    AllocationEvent rows with source=engine_commit. Unit and category
    name snapshots are resolved in a single upfront query and reused
    across all writes in this commit.

    v0.60c: ``placement_reasons`` and ``engine_run_id`` are written
    into the ``meta`` JSONB column of each emitted assign event.
    Shape per assign:

        {"run_id": "<uuid>", "placement": {"reason": "...", ...}}

    Fields are optional — commit_proposal called without them (e.g.
    legacy clients that don't send the reasoning payload, or tests
    exercising the write path independently) writes meta=None, which
    matches pre-v0.60c behaviour exactly. The clear-pass unassigns
    don't carry meta; they're correlated to the assign burst via
    adjacent occurred_at timestamps and shared source=engine_commit.
    """
    # Pre-fetch category + all target units for name snapshots. We
    # load every unit in the category (not just targets in the
    # proposal) because a typical engine commit fills most units, and
    # one query is cheaper than branching.
    cat_q = await db.execute(
        select(AllocationCategory).where(AllocationCategory.id == category_id)
    )
    cat = cat_q.scalar_one_or_none()
    category_name = cat.name if cat else "[deleted category]"

    units_q = await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == category_id)
    )
    # Key by str(uuid) because `proposed` dict keys are strings.
    unit_map: dict[str, AllocationUnit] = {
        str(u.id): u for u in units_q.scalars().all()
    }

    # Clear existing allocations — each emits an unassign event with
    # source=engine_commit so the engine commit reads as a paired
    # "clear + fill" in the timeline.
    cleared = await clear_category_allocations(
        db,
        event_id,
        category_id,
        actor_user_id=actor_user_id,
        source=AllocationEventSource.ENGINE_COMMIT,
    )

    reasons = placement_reasons or {}

    created = 0
    for unit_id_str, participant_ids in proposed.items():
        unit_id = uuid.UUID(unit_id_str)
        unit = unit_map.get(unit_id_str)
        unit_name = unit.name if unit else "[unknown unit]"
        for pid_str in participant_ids:
            pid = uuid.UUID(pid_str)
            a = Allocation(
                event_id=event_id,
                unit_id=unit_id,
                participant_id=pid,
            )
            db.add(a)
            # v0.60c: compose meta from run_id + per-pid reason.
            # Either component may be absent — omit it from the dict
            # entirely rather than writing a null sub-field, keeping
            # the JSONB clean and queries simple (e.g. filtering on
            # meta->>'run_id' returns null cleanly when absent).
            meta: dict | None = None
            pid_reason = reasons.get(pid_str)
            if engine_run_id or pid_reason:
                meta = {}
                if engine_run_id:
                    meta["run_id"] = engine_run_id
                if pid_reason:
                    meta["placement"] = pid_reason

            await record_allocation_event(
                db,
                event_id=event_id,
                participant_id=pid,
                unit_id=unit_id,
                category_id=category_id,
                unit_name_snapshot=unit_name,
                category_name_snapshot=category_name,
                event_type=AllocationEventType.ASSIGN,
                source=AllocationEventSource.ENGINE_COMMIT,
                actor_user_id=actor_user_id,
                meta=meta,
            )
            created += 1
    # v1.0.0y: emit event.allocated — an engine allocation run was just
    # finalised for this event. Queued in the SAME transaction as the
    # commit (queue_event only inserts a PENDING delivery row; it does not
    # commit), so the signal and the allocation land together or roll back
    # together. The business event id rides in data.event_id; the envelope
    # event_id is a per-message idempotency key, NOT this (see
    # webhook_service / docs/webhooks.md). GDPR-minimal: no counts, no
    # participant data. A no-op for self-hosters with no endpoint configured.
    # Fires on engine commits only — manual per-participant assigns are edits,
    # not a "run". Multiple commits across an event's categories is by design;
    # the control plane correlates them on data.event_id.
    await queue_event(
        db,
        event_type="event.allocated",
        data={"event_id": str(event_id)},
    )

    await db.flush()
    return {"cleared": cleared, "created": created}
