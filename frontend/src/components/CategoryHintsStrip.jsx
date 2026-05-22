import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';

/**
 * CategoryHintsStrip — informational signals for an unconfirmed
 * category on the AllocationBoard. v0.72; collapsible (Tier 2) in
 * v1.0.0q.
 *
 * Surfaces two computed quality signals to the organiser:
 *
 *   1. Mark cluster splits — one line per mark whose placed
 *      participants are spread across ≥2 distinct units. Pre-computed
 *      by `computeMarkSplits` (see frontend/src/utils/computeCategoryHints.js).
 *
 *   2. Unallocated count — a single trailing line surfacing how many
 *      active participants remain unplaced in this category. Already
 *      computed in AllocationBoard scope as `unassigned.length` and
 *      passed through.
 *
 * v1.0.0q (Tier 2): the strip is now a collapsible band with a
 * header showing "N items to review". Default open when count ≥ 3,
 * closed otherwise — keeps the board visually quiet when nothing
 * needs attention, while still surfacing the count so the
 * organiser knows there's something to expand into.
 *
 * Visibility rules:
 *   - Returns null when both signals are zero (no splits AND zero
 *     unallocated). Band never renders an empty box.
 *   - Caller is responsible for category.confirmed gating — when a
 *     category is confirmed, the strip is unmounted entirely by the
 *     parent (decision: hints disappear on confirm).
 *
 * Props:
 *   markSplits        — Array<{markId, markName, distribution: [{unitId, unitName, count}]}>
 *                       from computeMarkSplits. Distribution is pre-sorted
 *                       (largest cluster first).
 *   unallocatedCount  — number, count of active participants not yet
 *                       placed in any unit of this category.
 */
export default function CategoryHintsStrip({ markSplits, unallocatedCount }) {
  const { t } = useI18n();

  const splits = Array.isArray(markSplits) ? markSplits : [];
  const unalloc = Number.isFinite(unallocatedCount) ? unallocatedCount : 0;

  // v1.0.0q: collapsed by default unless count is meaningful (≥3).
  // The visible-header-with-count is the always-on signal; the body
  // is the on-demand detail.
  const totalCount = splits.length + (unalloc > 0 ? 1 : 0);
  const [open, setOpen] = useState(totalCount >= 3);

  // Visibility floor: no splits AND no unallocated → render nothing.
  if (totalCount === 0) return null;

  const sep = t('organise.hints.distribution_sep');

  return (
    <div
      role="status"
      aria-label={t('organise.hints.aria_label')}
      className="rounded-card mb-3"
      style={{
        background: 'rgba(70,130,180,0.06)',
        border: '1px solid rgba(70,130,180,0.22)',
      }}
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-left"
        aria-expanded={open}>
        <span className="text-[11px] font-semibold flex items-center gap-1.5"
          style={{ color: 'var(--text-primary)' }}>
          <span style={{
            display: 'inline-block',
            transform: open ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.15s',
          }}>▶</span>
          {t('organise.review.header', { n: totalCount })}
        </span>
      </button>
      {open && (
        <div className="flex flex-col gap-1 px-3 pb-2 pt-0">
          {splits.map(split => {
            const distribution = split.distribution
              .map(d => t('organise.hints.distribution_item', { count: d.count, unit: d.unitName }))
              .join(sep);
            return (
              <p
                key={split.markId}
                className="text-[11px] m-0"
                style={{ color: 'var(--text-primary)' }}
              >
                {t('organise.hints.mark_split', { mark: split.markName, distribution })}
              </p>
            );
          })}
          {unalloc > 0 && (
            <p
              className="text-[11px] m-0"
              style={{ color: 'var(--text-primary)' }}
            >
              {t('organise.hints.unallocated', { n: unalloc })}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
