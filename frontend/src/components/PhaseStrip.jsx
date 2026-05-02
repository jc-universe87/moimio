/**
 * PhaseStrip — event lifecycle indicator (spec §7.2).
 *
 * Shows three segments: Setup · Registration · Event.
 *   - Past phase     → checkmark + name
 *   - Current phase  → filled dot + bolded name (Steel Blue in light, Gold in dark)
 *   - Future phase   → hollow dot + dimmed name
 *
 * Not tappable (status indicator only — navigation is via sidebar).
 * Mobile viewport gets a compact 3-dot version with shorter labels.
 *
 * Future iteration per §7.2: past phases may become tappable for navigation.
 * For v50b we ship read-only.
 */

import { useI18n } from '../hooks/useI18n';
import { PHASE } from '../hooks/useEventPhase';

const ORDER = [PHASE.SETUP, PHASE.REGISTRATION, PHASE.EVENT];

function statusOf(segment, current) {
  const curIdx = ORDER.indexOf(current);
  const segIdx = ORDER.indexOf(segment);
  if (segIdx < curIdx) return 'past';
  if (segIdx === curIdx) return 'current';
  return 'future';
}

export default function PhaseStrip({ currentPhase, className = '' }) {
  const { t } = useI18n();

  const labels = {
    [PHASE.SETUP]: t('phase.setup'),
    [PHASE.REGISTRATION]: t('phase.registration'),
    [PHASE.EVENT]: t('phase.event'),
  };
  const shortLabels = {
    [PHASE.SETUP]: t('phase.setup'),
    [PHASE.REGISTRATION]: t('phase.registration_short'),
    [PHASE.EVENT]: t('phase.event'),
  };

  return (
    <nav
      aria-label={t('phase.strip_label')}
      className={`w-full ${className}`}
    >
      {/* Desktop / tablet — inline labels */}
      <ol className="hidden sm:flex items-center gap-2 list-none p-0 m-0">
        {ORDER.map((seg, i) => {
          const s = statusOf(seg, currentPhase);
          const isCurrent = s === 'current';
          const isPast = s === 'past';
          return (
            <li key={seg} className="flex items-center gap-2">
              <PhaseDot status={s} />
              <span
                aria-current={isCurrent ? 'step' : undefined}
                className={`font-body text-xs uppercase tracking-caps ${
                  isCurrent
                    ? 'font-bold text-steel-blue dark:text-gold'
                    : isPast
                    ? 'font-semibold'
                    : 'font-semibold'
                }`}
                style={{
                  color: isCurrent
                    ? undefined /* handled by utility class above */
                    : isPast
                    ? 'var(--text-muted)'
                    : 'var(--text-subtle)',
                }}
              >
                {labels[seg]}
              </span>
              {/* Visually hidden status suffix for screen readers */}
              <span className="sr-only">
                {' — '}
                {t(s === 'past' ? 'phase.completed' : s === 'current' ? 'phase.current' : 'phase.upcoming')}
              </span>
              {i < ORDER.length - 1 && (
                <span
                  aria-hidden="true"
                  className="h-px w-8 mx-1"
                  style={{ backgroundColor: 'var(--card-border)' }}
                />
              )}
            </li>
          );
        })}
      </ol>

      {/* Mobile — compact three-dot variant */}
      <ol className="flex sm:hidden items-center justify-between list-none p-0 m-0 gap-1">
        {ORDER.map((seg, i) => {
          const s = statusOf(seg, currentPhase);
          const isCurrent = s === 'current';
          return (
            <li key={seg} className="flex items-center gap-1.5 flex-1 min-w-0">
              <PhaseDot status={s} small />
              <span
                aria-current={isCurrent ? 'step' : undefined}
                className={`font-body text-[10px] uppercase tracking-caps truncate ${
                  isCurrent
                    ? 'font-bold text-steel-blue dark:text-gold'
                    : 'font-semibold'
                }`}
                style={{
                  color: isCurrent
                    ? undefined
                    : s === 'past'
                    ? 'var(--text-muted)'
                    : 'var(--text-subtle)',
                }}
              >
                {shortLabels[seg]}
              </span>
              {i < ORDER.length - 1 && (
                <span
                  aria-hidden="true"
                  className="h-px flex-1 mx-1"
                  style={{ backgroundColor: 'var(--card-border)' }}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/**
 * Small status dot. Inline SVG so we can use currentColor and have
 * it work in both light/dark without theming juggling.
 */
function PhaseDot({ status, small = false }) {
  const size = small ? 8 : 10;
  // Current: filled circle in accent.
  // Past:    outlined circle with a checkmark (subtle).
  // Future:  hollow circle with muted stroke.
  if (status === 'current') {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 10 10"
        aria-hidden="true"
        className="shrink-0 text-steel-blue dark:text-gold"
      >
        <circle cx="5" cy="5" r="4" fill="currentColor" />
      </svg>
    );
  }
  if (status === 'past') {
    return (
      <svg
        width={size + 2}
        height={size + 2}
        viewBox="0 0 12 12"
        aria-hidden="true"
        className="shrink-0"
        style={{ color: 'var(--tick-color)' }}
      >
        <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <path
          d="M3.5 6.2 L5.2 7.8 L8.5 4.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }
  // future
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 10 10"
      aria-hidden="true"
      className="shrink-0"
      style={{ color: 'var(--text-subtle)' }}
    >
      <circle cx="5" cy="5" r="4" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}
