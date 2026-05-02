import { useI18n } from '../hooks/useI18n';

/**
 * CategoryHintsStrip — informational signals for an unconfirmed
 * category on the AllocationBoard. v0.72.
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
 * Visibility rules:
 *   - Returns null when both signals are zero (no splits AND zero
 *     unallocated). Strip never renders an empty box.
 *   - Caller is responsible for category.confirmed gating — when a
 *     category is confirmed, the strip is unmounted entirely by the
 *     parent (decision: hints disappear on confirm).
 *
 * Visual treatment:
 *   - Steel-blue informational tint, mirroring the confirmed banner's
 *     visual language. These are status signals to inform the
 *     organiser's next action, not warnings — burgundy would be
 *     misleadingly alarmist for routine fragmentation feedback.
 *   - Vertical stack of lines, one signal per row. No leading icon —
 *     the tinted box and the quoted mark names communicate "hint"
 *     without iconographic clutter at multi-line scale.
 *
 * Renders identically on desktop and mobile; lines wrap naturally as
 * the viewport narrows. No mobile-specific markup needed.
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

  // Visibility floor: no splits AND no unallocated → render nothing.
  if (splits.length === 0 && unalloc === 0) return null;

  const sep = t('organise.hints.distribution_sep');

  return (
    <div
      role="status"
      aria-label={t('organise.hints.aria_label')}
      className="rounded-card px-3 py-2 mb-3 flex flex-col gap-1"
      style={{
        background: 'rgba(70,130,180,0.06)',
        border: '1px solid rgba(70,130,180,0.22)',
      }}
    >
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
  );
}
