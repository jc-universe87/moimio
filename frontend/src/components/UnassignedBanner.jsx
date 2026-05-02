/**
 * UnassignedBanner — shows on the Event-phase board when participants
 * haven't been placed into an allocation category that has already
 * started being allocated (i.e. late signups).
 *
 * Detection rule (set by parent):
 *   - only counts a category that has allocated_count > 0
 *   - highest-count category wins (we show one banner, pointing to one)
 *   - count = participants registered and not placed in that category
 *
 * Props:
 *   - categoryName  — name of the category the banner points to
 *   - count         — number of unassigned participants in that category
 *   - onPlaceThem   — callback that opens that category on the board
 */

import { useI18n } from '../hooks/useI18n';

export default function UnassignedBanner({ categoryName, count, onPlaceThem }) {
  const { t } = useI18n();

  if (!count || !categoryName) return null;

  return (
    <div
      className="card-surface-solid p-4 mb-4 flex items-start gap-3"
      style={{ borderLeft: '4px solid var(--alert-burgundy)' }}
      role="status"
    >
      <div className="flex-1 min-w-0">
        <p className="font-body font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
          {t('banner.unassigned.title', { n: count, cat: categoryName })}
        </p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
          {t('banner.unassigned.body')}
        </p>
      </div>
      {onPlaceThem && (
        <button
          type="button"
          onClick={onPlaceThem}
          className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap shrink-0"
          style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
        >
          {t('banner.unassigned.action')} ↓
        </button>
      )}
    </div>
  );
}
