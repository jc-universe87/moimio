/**
 * TimezonePicker — v0.70d-2b (R13)
 *
 * Shared picker for any IANA timezone. Replaces the hard-coded ~12
 * zone <select> that previously lived duplicated in DetailsEditor
 * and UserPreferencesPanel.
 *
 * Behaviour:
 *   - Uses `Intl.supportedValuesOf('timeZone')` where available
 *     (Node 20+, Chrome 99+, Safari 15.4+, Firefox 93+) to pull the
 *     full IANA zone list (~420 entries) from the browser's ICU data.
 *   - Falls back to a hand-curated shortlist for older browsers.
 *   - Rendered as a text input with a `<datalist>` attached —
 *     browser-native autocomplete, no JS library needed, works
 *     well with keyboard and screen readers, and `[color-scheme]`
 *     propagates correctly in dark mode.
 *
 * Props:
 *   value       — current zone string (e.g. 'Europe/London')
 *   onChange    — (newValue: string) => void
 *   className   — passed through to the <input>; consumers style
 *                 their own surface (light card vs always-dark
 *                 sidebar) by supplying their own class string.
 *   id          — optional; pairs with a parent <label htmlFor=>
 *   ariaLabel   — fallback accessible name when there's no visible
 *                 label sibling (rare)
 *
 * The input accepts free-text entry. The datalist is a suggestion
 * surface, not a constraint — users can type any IANA zone (e.g.
 * 'Pacific/Auckland') even if the current browser's `supportedValuesOf`
 * is missing it. Backend validation still enforces the canonical
 * set; this picker just makes the common cases fast.
 */

import { useMemo, useId } from 'react';

// Fallback for browsers without `Intl.supportedValuesOf('timeZone')`.
// Same list the two old consumers used; covers Moimio's core markets
// (EU + Korean-connected communities + a few Americas zones).
const FALLBACK_ZONES = [
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Europe/Madrid',
  'Europe/Rome',
  'Asia/Seoul',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'America/New_York',
  'America/Los_Angeles',
  'America/Sao_Paulo',
];

function getAllTimezones() {
  try {
    if (typeof Intl !== 'undefined' && typeof Intl.supportedValuesOf === 'function') {
      const all = Intl.supportedValuesOf('timeZone');
      if (Array.isArray(all) && all.length > 0) return all;
    }
  } catch {
    // Fall through to fallback.
  }
  return FALLBACK_ZONES;
}

export default function TimezonePicker({
  value = '',
  onChange,
  className = '',
  id,
  ariaLabel,
}) {
  // Reactive-identity-stable reactId; only used if consumer didn't
  // supply an id. Ensures the input <-> datalist link is unique even
  // if multiple TimezonePickers render on the same page.
  const autoId = useId();
  const listId = `${id || autoId}-list`;

  const zones = useMemo(() => getAllTimezones(), []);

  return (
    <>
      <input
        type="text"
        list={listId}
        id={id || autoId}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        className={className}
        aria-label={ariaLabel}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        autoComplete="off"
      />
      <datalist id={listId}>
        {zones.map((z) => (
          <option key={z} value={z} />
        ))}
      </datalist>
    </>
  );
}
