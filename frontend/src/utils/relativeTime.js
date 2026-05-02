/**
 * formatRelativeTime — localised relative time formatter.
 *
 * Usage:
 *   formatRelativeTime(new Date('2026-04-15'), 'en')     → "3 days ago"
 *   formatRelativeTime(new Date('2026-04-15'), 'de')     → "vor 3 Tagen"
 *   formatRelativeTime(new Date(Date.now() - 60_000), 'en') → "1 minute ago"
 *   formatRelativeTime(null, 'en')                        → null
 *
 * Uses Intl.RelativeTimeFormat (supported in all modern browsers). Picks
 * the largest unit that fits (minutes → hours → days → weeks → months → years).
 *
 * For < 60 seconds we return "just now" (via a caller-provided translation
 * since Intl doesn't have a clean "just now" unit). The caller passes in
 * a `justNowLabel` string for the current language.
 */

const THRESHOLDS = [
  { unit: 'year',   seconds: 365 * 24 * 60 * 60 },
  { unit: 'month',  seconds: 30 * 24 * 60 * 60 },
  { unit: 'week',   seconds: 7 * 24 * 60 * 60 },
  { unit: 'day',    seconds: 24 * 60 * 60 },
  { unit: 'hour',   seconds: 60 * 60 },
  { unit: 'minute', seconds: 60 },
];

// Map our app's BCP-47-ish codes to what Intl expects. Most pass
// through; 'pt-BR' is already a valid Intl locale tag.
const INTL_LOCALE = {
  'en': 'en',
  'de': 'de',
  'ko': 'ko',
  'es': 'es',
  'pt-BR': 'pt-BR',
  'fr': 'fr',
};

export function formatRelativeTime(date, lang = 'en', justNowLabel = 'just now') {
  if (!date) return null;
  const d = date instanceof Date ? date : new Date(date);
  if (isNaN(d.getTime())) return null;

  const diffSeconds = Math.round((d.getTime() - Date.now()) / 1000);
  const abs = Math.abs(diffSeconds);

  // "just now" for under a minute (in either direction)
  if (abs < 60) return justNowLabel;

  const locale = INTL_LOCALE[lang] || 'en';
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  for (const { unit, seconds } of THRESHOLDS) {
    if (abs >= seconds) {
      const value = Math.round(diffSeconds / seconds);
      return rtf.format(value, unit);
    }
  }
  // Fallback — shouldn't hit this because < 60s is caught above
  return justNowLabel;
}
