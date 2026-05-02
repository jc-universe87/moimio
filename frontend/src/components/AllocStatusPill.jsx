/**
 * AllocStatusPill — compact state indicator for an allocation category.
 *
 * Three states derived from category data:
 *   - Not allocated — allocated_count === 0
 *   - Confirmed    — cat.confirmed === true
 *   - In progress  — anything else (allocations exist but not yet confirmed)
 *
 * Styling:
 *   - Not allocated → muted + dashed border (suggests "nothing here yet")
 *   - In progress   → neutral grey pill
 *   - Confirmed     → Steel Blue / Gold pill with checkmark
 */

import { useI18n } from '../hooks/useI18n';
import { useTheme } from '../hooks/useTheme';

export const ALLOC_STATE = {
  NOT_ALLOCATED: 'not_allocated',
  IN_PROGRESS: 'in_progress',
  CONFIRMED: 'confirmed',
};

export function deriveAllocState(cat) {
  if (!cat) return ALLOC_STATE.NOT_ALLOCATED;
  if (cat.confirmed) return ALLOC_STATE.CONFIRMED;
  if ((cat.allocated_count || 0) === 0) return ALLOC_STATE.NOT_ALLOCATED;
  return ALLOC_STATE.IN_PROGRESS;
}

export default function AllocStatusPill({ state }) {
  const { t } = useI18n();
  const { effective } = useTheme();
  const isDark = effective === 'dark';

  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    fontSize: 10,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    padding: '3px 8px',
    borderRadius: 6,
    whiteSpace: 'nowrap',
  };

  if (state === ALLOC_STATE.CONFIRMED) {
    return (
      <span
        style={{
          ...baseStyle,
          color: isDark ? '#FFD700' : '#0C447C',
          backgroundColor: isDark ? 'rgba(255, 215, 0, 0.12)' : 'rgba(70, 130, 180, 0.12)',
        }}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M2 5 L4 7 L8 3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {t('alloc.status.confirmed')}
      </span>
    );
  }

  if (state === ALLOC_STATE.IN_PROGRESS) {
    return (
      <span
        style={{
          ...baseStyle,
          color: 'var(--text-muted)',
          backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
        }}
      >
        {t('alloc.status.in_progress')}
      </span>
    );
  }

  // NOT_ALLOCATED — dashed outline, muted
  return (
    <span
      style={{
        ...baseStyle,
        color: 'var(--text-subtle)',
        border: '1px dashed var(--card-border)',
        padding: '2px 7px',
      }}
    >
      {t('alloc.status.not_allocated')}
    </span>
  );
}
