/**
 * placementReason — localised human-readable sub-line for an engine
 * placement reason.
 *
 * v0.70d-1: extracted from AllocationHistory.jsx so the new review
 * surface can share the same conversion.
 *
 * v1.0.0e: realigned to the engine's actual reason vocabulary. The
 * pre-v1.1 dispatcher switched on `group_code_cluster`,
 * `mark_cluster`, etc. — names that were never emitted by the engine
 * (which writes `group_code`, `mark_together`, `mark_split`,
 * `gender_drain`, `fill`). The mismatch silently disabled every
 * placement popover except `fill`. Vocabulary now matches the engine
 * end-to-end. Existing v1.0.0 commits are unaffected — their stored
 * `meta.placement.reason` already uses the engine vocab; v1.0.0e just
 * starts rendering them again.
 *
 * Two helpers exported:
 *
 *   reasoningLine(meta, t)
 *     History-compatible. Returns null for `fill` (every plain
 *     placement is a fill; a "Placed to fill remaining capacity"
 *     sub-line on every history row would be noise).
 *
 *   reasoningLineExtended(meta, t)
 *     Review-surface-compatible. Returns a line for `fill` too,
 *     because on the review screen the absence of a reason reads as
 *     "missing data" rather than "nothing interesting here."
 *
 * Engine reason vocabulary (engine_service.py):
 *   group_code               — group_code cluster placed whole
 *   group_code_split         — group_code cluster split across units
 *   mark_together            — mark cluster (keep_together) placed whole
 *   mark_together_split      — mark cluster split across units
 *   mark_split               — PASS 2 spread (mark behaviour: split)
 *   gender_drain             — PASS 4a fill of a gender-restricted unit
 *   fill                     — PASS 4b round-robin fill
 *   equalise                 — v1.0.0e PASS 4c sweep moved a cluster
 *                              to even out unit sizes. Always carries
 *                              `previous`, the placement reason that
 *                              originally put the participant in
 *                              their first unit.
 *
 * Meta shape:
 *   For committed allocation events (history): `meta.placement.reason`
 *   For in-flight proposals (review):          `meta.reason` (direct)
 *
 * Both helpers accept either shape via `unwrap`.
 *
 * v1.0.0e multi-line return: when an `equalise` placement is rendered,
 * the helper returns BOTH the original-cluster line and the equalise
 * line, joined with '\n'. Render sites use `whitespace-pre-line` to
 * preserve the break. This keeps the audit trail showing why the
 * participant was clustered AND why they were then moved.
 */

function unwrap(meta) {
  if (!meta) return null;
  // History rows wrap the reason under `.placement`; proposal rows
  // have it at the top level.
  return meta.placement || meta;
}

/**
 * Render a single placement reason payload to a one-liner. Returns
 * null when the payload doesn't merit a sub-line (e.g. `fill` in
 * history mode — too noisy to show on every row).
 *
 * `mode` is 'history' or 'extended':
 *   - history: fill → null, unknown → null
 *   - extended: fill → "Placed to fill remaining capacity"
 */
function singleLine(p, t, mode) {
  if (!p || !p.reason) return null;
  switch (p.reason) {
    case 'group_code':
      return t('history.reason.group_cluster', {
        code: p.cluster_id || p.group_code || '',
        n: p.cluster_placed_here ?? p.cluster_size ?? 0,
      });
    case 'group_code_split':
      return t('history.reason.group_cluster_split', {
        code: p.cluster_id || p.group_code || '',
        here: p.cluster_placed_here ?? 0,
        total: p.cluster_size ?? 0,
      });
    case 'mark_together':
      return t('history.reason.mark_cluster', {
        n: p.cluster_placed_here ?? p.cluster_size ?? 0,
      });
    case 'mark_together_split':
      return t('history.reason.mark_cluster_split', {
        here: p.cluster_placed_here ?? 0,
        total: p.cluster_size ?? 0,
      });
    case 'mark_split':
      // PASS 2 spread — the participant's mark has split behaviour, so
      // they were distributed away from same-mark peers on purpose.
      return mode === 'extended'
        ? t('engine.reason.mark_split')
        : t('history.reason.mark_split');
    case 'gender_drain':
      // PASS 4a — placed in a gender-restricted unit to fill it.
      // Renders unit name (snapshotted on the meta) + the gender
      // restriction in the destination. Falls back gracefully when
      // meta lacks either field (e.g. older proposals, or unit
      // references that survived deletion via SET NULL).
      return mode === 'extended'
        ? t('engine.reason.gender_drain', {
            unit: p.unit_name || '',
            gender: p.gender_restriction || '',
          })
        : t('history.reason.gender_drain', {
            unit: p.unit_name || '',
            gender: p.gender_restriction || '',
          });
    case 'equalise':
      return mode === 'extended'
        ? t('engine.reason.equalise')
        : t('history.reason.equalise');
    case 'fill':
      return mode === 'extended' ? t('engine.reason.fill') : null;
    default:
      return null;
  }
}

/**
 * History-mode: fill → null, unknown → null.
 *
 * For equalise placements, returns BOTH the original cluster line
 * and the equalise line, joined with '\n'. Caller renders with
 * `whitespace-pre-line`.
 */
export function reasoningLine(meta, t) {
  const p = unwrap(meta);
  if (!p) return null;
  const lines = [];
  if (p.reason === 'equalise' && p.previous) {
    const prior = singleLine(p.previous, t, 'history');
    if (prior) lines.push(prior);
  }
  const primary = singleLine(p, t, 'history');
  if (primary) lines.push(primary);
  return lines.length === 0 ? null : lines.join('\n');
}

/**
 * Review-mode: fill → "placed to fill", unknown → null. Unplaced is
 * handled separately by callers (see unplacedReasoningLine below).
 *
 * For equalise placements, same multi-line behaviour as history mode.
 */
export function reasoningLineExtended(meta, t) {
  const p = unwrap(meta);
  if (!p) return null;
  const lines = [];
  if (p.reason === 'equalise' && p.previous) {
    const prior = singleLine(p.previous, t, 'extended');
    if (prior) lines.push(prior);
  }
  const primary = singleLine(p, t, 'extended');
  if (primary) lines.push(primary);
  return lines.length === 0 ? null : lines.join('\n');
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
