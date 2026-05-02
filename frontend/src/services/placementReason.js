/**
 * placementReason — localised human-readable sub-line for an engine
 * placement reason.
 *
 * v0.70d-1: extracted from AllocationHistory.jsx so the new review
 * surface can share the same conversion. Two helpers are exported:
 *
 *   reasoningLine(meta, t)
 *     History-compatible. Returns null for `fill` (every plain
 *     placement is a fill; a "Placed to fill remaining capacity"
 *     sub-line on every history row would be noise). Same behaviour
 *     as pre-v0.70d.
 *
 *   reasoningLineExtended(meta, t)
 *     Review-surface-compatible. Returns a line for `fill` too,
 *     because on the review screen the absence of a reason reads as
 *     "missing data" rather than "nothing interesting here." Also
 *     returns a generic line for unplaced (frontend fallback —
 *     Phase 1 engine doesn't emit per-participant unplaced
 *     sub-reasons yet).
 *
 * Engine reason vocabulary (engine_service.py):
 *   group_code_cluster        — cluster fit whole into a unit
 *   group_code_cluster_split  — cluster split across units
 *   mark_cluster              — mark-based soft cluster, whole
 *   mark_cluster_split        — mark-based soft cluster, split
 *   fill                      — plain fill after cluster passes
 *   unplaced                  — (synthesised; engine doesn't emit
 *                                this today, see review surface)
 *
 * Meta shape:
 *   For committed allocation events (history): `meta.placement.reason`
 *   For in-flight proposals (review):          `meta.reason` (direct)
 *
 * Both helpers accept either shape via a small unwrap.
 */

function unwrap(meta) {
  if (!meta) return null;
  // History rows wrap the reason under `.placement`; proposal rows
  // have it at the top level.
  return meta.placement || meta;
}

/**
 * History-mode: fill → null, unknown → null.
 */
export function reasoningLine(meta, t) {
  const p = unwrap(meta);
  if (!p) return null;
  switch (p.reason) {
    case 'group_code_cluster':
      return t('history.reason.group_cluster', {
        code: p.group_code,
        n: p.cluster_placed_here,
      });
    case 'group_code_cluster_split':
      return t('history.reason.group_cluster_split', {
        code: p.group_code,
        here: p.cluster_placed_here,
        total: p.cluster_size,
      });
    case 'mark_cluster':
      return t('history.reason.mark_cluster', {
        n: p.cluster_placed_here,
      });
    case 'mark_cluster_split':
      return t('history.reason.mark_cluster_split', {
        here: p.cluster_placed_here,
        total: p.cluster_size,
      });
    case 'fill':
    default:
      return null;
  }
}

/**
 * Review-mode: fill → "placed to fill", unknown → null. Unplaced is
 * handled separately by callers (see the `unplaced` constant below)
 * since it's not a placement but rather a non-placement explanation.
 */
export function reasoningLineExtended(meta, t) {
  const p = unwrap(meta);
  if (!p) return null;
  if (p.reason === 'fill') return t('engine.reason.fill');
  return reasoningLine(meta, t);
}

/**
 * Synthetic "why wasn't this person placed?" line. v0.73a Phase 2:
 * dispatches on the engine's `unplaced_reasons[pid].reason` tag when
 * available. Falls back to the generic line for participants without
 * a tagged reason (defensive — any new engine code path that creates
 * unplaced participants without tagging should still render readably).
 *
 * Three tags emitted by v0.73a:
 *   - gender_unknown_no_mixed_unit_available — Bug 4 strict gender
 *   - cluster_oversized_split_disabled        — Bug 6 cluster-skip
 *   - no_capacity_remaining                   — catch-all
 *
 * Reason meta carries optional context (e.g. cluster_size, group_code
 * for the cluster-skip case). The current localised strings don't
 * reference these — kept on the meta in case future copy iterations
 * want to inline them.
 */
export function unplacedReasoningLine(t, meta = null) {
  const p = unwrap(meta);
  const reason = p?.reason;
  if (reason === 'gender_unknown_no_mixed_unit_available') {
    return t('alloc.unplaced.gender_unknown_no_mixed_unit_available');
  }
  if (reason === 'cluster_oversized_split_disabled') {
    return t('alloc.unplaced.cluster_oversized_split_disabled');
  }
  if (reason === 'no_capacity_remaining') {
    return t('alloc.unplaced.no_capacity_remaining');
  }
  return t('engine.reason.unplaced_generic');
}
