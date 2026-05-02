/**
 * TranslatedError — Pattern B error banner.
 *
 * v0.70d-3c-6: centralises the Pattern B render block from
 * v0.70d-3b's OrganiseDashboard demonstration. Wraps `ErrorBanner`
 * with a `formatErrorMessage(err, t)` call so callers don't have to
 * inline the {primary, detail} destructure at every site.
 *
 * v0.70d-3c-13 (consolidation): named `variant` shapes replace the
 * 13-site className drift audited at the end of 3c-12. Two canonical
 * shapes cover the page-level + tight-space cases:
 *
 *   variant="card"     'text-sm rounded-card p-3 mb-4'   (default)
 *   variant="compact"  'text-xs rounded-card p-2'
 *
 * Sites that match a variant should omit `className` entirely.
 * Sites with legitimate context-specific layout (no bottom margin,
 * `max-w-md`, modal positioning, `rounded-lg` for modal radius
 * convention, or `p-4` emphasis) override `className` directly —
 * `className` always wins over `variant` when both are passed.
 *
 * IMPORTANT: ErrorBanner sets `background`, `color`, and `border`
 * via inline `style={}` — those properties cannot be overridden by
 * Tailwind utility classes (inline style takes precedence). Do NOT
 * pass `bg-alert-tint`, `text-alert`, or `border border-alert` in
 * className — they are inert noise. The 3c-13 audit stripped these
 * at 7 sites where they had silently accumulated.
 *
 * Accepts:
 *   err       — error object (with i18nKey / friendlyKey / message)
 *               OR a translated string OR null/undefined.
 *   variant   — 'card' (default) or 'compact'.
 *   className — when provided, fully replaces the variant default.
 *               Pass an empty string to clear all utility classes.
 *
 * If `err` is null / undefined / empty string, returns null — so
 * call sites can do `<TranslatedError err={error} />` without
 * `{error && ...}` wrapping. Mirrors the OrganiseDashboard pattern
 * shipped in v0.70d-3b.
 */

import { formatErrorMessage } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import ErrorBanner from './ErrorBanner';

const VARIANT_CLASSES = {
  card: 'text-sm rounded-card p-3 mb-4',
  compact: 'text-xs rounded-card p-2',
};

export default function TranslatedError({
  err,
  variant = 'card',
  className,
}) {
  const { t } = useI18n();
  if (!err) return null;
  const { primary, detail } = formatErrorMessage(err, t);
  const resolved =
    className !== undefined ? className : VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.card;
  return (
    <ErrorBanner className={resolved}>
      <p className="font-semibold">{primary}</p>
      {detail && <p className="text-xs opacity-70 mt-1">{detail}</p>}
    </ErrorBanner>
  );
}
