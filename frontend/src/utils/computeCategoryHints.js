/**
 * computeCategoryHints — pure compute layer for AllocationBoard system hints.
 *
 * v0.72 surfaces two computed quality signals to the organiser on each
 * unconfirmed category header:
 *
 *   1. Mark cluster splits — "Swahili speakers split: 3 in Group A,
 *      2 in Group C." Surfaces fragmentation of a mark across units
 *      so the organiser can decide whether to consolidate.
 *
 *   2. Unallocated count — "12 not yet assigned." (Already computed
 *      as `unassigned.length` in AllocationBoard scope; this module
 *      does NOT recompute it. The component wires it through.)
 *
 * This module owns the mark-split logic only. It is a pure function
 * over explicit inputs — no React, no API access, no closures over
 * AllocationBoard state. That keeps it testable by inspection and
 * by Node-level smoke runs.
 *
 * Definition of "split": a mark is split when ≥2 placed participants
 * share that mark AND those placed participants are spread across
 * ≥2 distinct units within the current category. Marks with 0 or 1
 * placed participant cannot be split. Marks where all placed
 * participants share a single unit are NOT split (they are intact).
 *
 * Unassigned participants with the mark are deliberately excluded.
 * The signal is "your placements are fragmenting the mark," not
 * "you have unplaced people who carry this mark." Unassigned counts
 * are surfaced separately by the component layer.
 *
 * Usage:
 *   const splits = computeMarkSplits({
 *     allMembers: { 'unit-1': [{participant_id: 'p1'}, ...], ... },
 *     units: [{id: 'unit-1', name: 'Group A'}, ...],
 *     markAssignments: [{mark_id: 'm1', participant_id: 'p1'}, ...],
 *     markDefs: [{id: 'm1', name: 'Swahili speakers'}, ...],
 *   });
 *   //  → [{
 *   //      markId: 'm1',
 *   //      markName: 'Swahili speakers',
 *   //      distribution: [
 *   //        {unitId: 'unit-1', unitName: 'Group A', count: 3},
 *   //        {unitId: 'unit-3', unitName: 'Group C', count: 2},
 *   //      ],
 *   //    }, ...]
 *
 * Returns an empty array when there are no splits. Output is sorted
 * by mark name for deterministic rendering. Within each split, the
 * distribution is sorted by count descending (largest cluster first)
 * with unit name as a stable tiebreaker.
 */

/**
 * Compute mark cluster splits for a single category.
 *
 * @param {Object} args
 * @param {Object<string, Array<{participant_id: (string|number)}>>} args.allMembers
 *        Map of unitId → array of placement records. Source of truth
 *        for "who is in which unit." Keys are unit IDs as strings;
 *        each value is the list of placement rows from the
 *        allocations API.
 * @param {Array<{id: (string|number), name: string}>} args.units
 *        Unit definitions for the current category. Used to resolve
 *        unitId → unitName for human-readable output. Units missing
 *        from this array are silently dropped from the distribution
 *        (defensive; should not happen in practice).
 * @param {Array<{mark_id: (string|number), participant_id: (string|number)}>} args.markAssignments
 *        Flat array of mark↔participant assignments for the event.
 * @param {Array<{id: (string|number), name: string}>} args.markDefs
 *        Mark definitions for the event. Used to resolve markId →
 *        markName. Marks without a name are skipped (a nameless mark
 *        is a data-integrity issue we refuse to render).
 *
 * @returns {Array<{markId: string, markName: string, distribution: Array<{unitId: string, unitName: string, count: number}>}>}
 *          Empty array if no splits exist. Sorted by markName ascending;
 *          within each split, distribution sorted by count descending.
 */
export function computeMarkSplits({
  allMembers,
  units,
  markAssignments,
  markDefs,
}) {
  // Defensive: any missing input → no signals to render.
  if (
    !allMembers ||
    !Array.isArray(units) ||
    !Array.isArray(markAssignments) ||
    !Array.isArray(markDefs)
  ) {
    return [];
  }

  // 1. Build unitId → unitName lookup. String-keyed for consistency
  //    with the rest of the codebase (which uses String(p.id) coercion).
  const unitNameById = new Map();
  for (const u of units) {
    if (u && u.id != null) {
      unitNameById.set(String(u.id), u.name || '');
    }
  }

  // 2. Build participantId → unitId map for participants placed in
  //    this category. Iterate allMembers, which is already scoped
  //    to the current category by the caller.
  const placedParticipantToUnit = new Map();
  for (const [unitId, members] of Object.entries(allMembers)) {
    if (!Array.isArray(members)) continue;
    if (!unitNameById.has(String(unitId))) continue; // unknown unit → skip
    for (const m of members) {
      if (m && m.participant_id != null) {
        placedParticipantToUnit.set(String(m.participant_id), String(unitId));
      }
    }
  }

  // Early-out: nobody placed → no splits possible.
  if (placedParticipantToUnit.size === 0) return [];

  // 3. Build markId → markName lookup, skipping nameless marks.
  const markNameById = new Map();
  for (const d of markDefs) {
    if (d && d.id != null && d.name && d.name.trim()) {
      markNameById.set(String(d.id), d.name);
    }
  }

  // 4. For each mark, gather the placed participants and their units.
  //    Group structure: markId → Map(unitId → count).
  const distributionByMark = new Map();
  for (const a of markAssignments) {
    if (!a || a.mark_id == null || a.participant_id == null) continue;
    const markId = String(a.mark_id);
    const participantId = String(a.participant_id);
    if (!markNameById.has(markId)) continue; // unknown / nameless mark
    const unitId = placedParticipantToUnit.get(participantId);
    if (!unitId) continue; // participant not placed in this category
    let perUnit = distributionByMark.get(markId);
    if (!perUnit) {
      perUnit = new Map();
      distributionByMark.set(markId, perUnit);
    }
    perUnit.set(unitId, (perUnit.get(unitId) || 0) + 1);
  }

  // 5. Filter to splits only (≥2 distinct units), shape the output,
  //    sort distributions by count desc + unit name asc tiebreaker.
  const splits = [];
  for (const [markId, perUnit] of distributionByMark) {
    if (perUnit.size < 2) continue; // not split
    const distribution = [];
    for (const [unitId, count] of perUnit) {
      distribution.push({
        unitId,
        unitName: unitNameById.get(unitId) || '',
        count,
      });
    }
    distribution.sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count;
      return a.unitName.localeCompare(b.unitName);
    });
    splits.push({
      markId,
      markName: markNameById.get(markId),
      distribution,
    });
  }

  // 6. Sort output by mark name for deterministic render order.
  splits.sort((a, b) => a.markName.localeCompare(b.markName));
  return splits;
}
