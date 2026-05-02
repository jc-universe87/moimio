/**
 * SetupCard — inline-expanding card used on the Setup hub (§4.1).
 *
 * v50b-6: status shown BOTH as a label ("Required" / "Suggested") AND as
 * a coloured left stripe. Belt-and-braces, per §4.1 "left border accent
 * OR small Required label" — both is clearer than either alone.
 *
 *   Required + not confirmed  → stripe: Burgundy,     label: "Required" in Burgundy
 *   Required + confirmed      → stripe: Steel/Gold,   label: "Required" muted
 *   Suggested + confirmed     → stripe: Steel/Gold,   label: "Suggested" muted
 *   Suggested + not confirmed → no stripe,            label: "Suggested" muted
 *   Optional  + anything      → stripe only if confirmed, no label
 *
 * Stripe is applied via inline style to beat the `card-surface-solid`
 * shorthand border (`border: 0.5px solid var(--card-border)`) which was
 * overriding Tailwind's `border-l-*` utilities in v50b-5. Inline wins.
 */

import { useI18n } from '../hooks/useI18n';
import { useTheme } from '../hooks/useTheme';
import { formatErrorMessage } from '../services/api';

// Inline colour values so the stripe always wins against the card's
// shorthand `border: 0.5px solid ...`. No Tailwind utility class can
// reliably override a shorthand declared in the same specificity class.
const COLOURS = {
  burgundy:  'var(--alert-burgundy)',   // §9.1 required-not-yet (attention)
  steelBlue: '#4682B4',   // §9.1 confirmed, light mode
  gold:      '#FFD700',   // §9.1 confirmed, dark mode
};

export default function SetupCard({
  name,
  priority = 'optional',
  summary,
  emptyCopy,
  confirmed = false,
  isOpen = false,
  onToggleOpen,
  canConfirm = false,
  onSaveAndConfirm,
  onUnconfirm,
  confirmLabel = null,
  // v0.70d-2c (R4-B): when set, disables the confirm button and
  // renders the reason as a muted hint next to it. Used by SetupHub's
  // Registration card to gate "Open registration" on group-types
  // existence; generic enough that future gates can reuse it.
  confirmDisabledReason = null,
  saveError = null,
  saving = false,
  children,
}) {
  const { t } = useI18n();
  const { effective } = useTheme();
  const isDark = effective === 'dark';

  const isConfigured = !!summary;

  // Stripe colour: Burgundy for required-not-yet, Steel Blue/Gold when
  // confirmed. null = no stripe (card's default 0.5px grey shows through).
  let stripeColor = null;
  if (priority === 'required' && !confirmed) stripeColor = COLOURS.burgundy;
  else if (confirmed) stripeColor = isDark ? COLOURS.gold : COLOURS.steelBlue;

  const cardStyle = stripeColor
    ? { borderLeft: `4px solid ${stripeColor}` }
    : {};

  // Label style: Burgundy while attention-needed, muted grey otherwise
  const requiredLabelStyle = (priority === 'required' && !confirmed)
    ? { color: COLOURS.burgundy }
    : { color: 'var(--text-subtle)' };

  return (
    <article className={`card-surface-solid transition-shadow ${isOpen ? 'shadow-sm' : ''}`}
             style={cardStyle}>
      {/* Header row — clickable to toggle */}
      <button
        type="button"
        onClick={onToggleOpen}
        aria-expanded={isOpen}
        className="w-full text-left px-4 py-3 flex items-center gap-3"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-body font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
              {name}
            </span>

            {priority === 'required' && (
              <span className="text-[10px] uppercase tracking-caps font-bold"
                    style={requiredLabelStyle}>
                {t('setup.required')}
              </span>
            )}
            {priority === 'suggested' && (
              <span className="text-[10px] uppercase tracking-caps font-semibold"
                    style={{ color: 'var(--text-subtle)' }}>
                {t('setup.suggested')}
              </span>
            )}

            {confirmed && (
              <span className="inline-flex items-center"
                    style={{ color: 'var(--tick-color)' }}
                    aria-label={t('setup.configured')}
                    title={t('setup.configured')}>
                <CheckIcon />
              </span>
            )}
          </div>
          {/* v0.58e-3: always show the italic description for visual
              consistency across all cards. When configured, show the
              count/status summary ABOVE the description so users get
              both "what's in it" and "what this card is for." */}
          {isConfigured && summary && (
            <p className="text-xs mt-0.5"
               style={{
                 color: 'var(--text-muted)',
                 fontStyle: 'normal',
                 display: '-webkit-box',
                 WebkitLineClamp: 2,
                 WebkitBoxOrient: 'vertical',
                 overflow: 'hidden',
               }}>
              {summary}
            </p>
          )}
          {emptyCopy && (
            <p className="text-xs mt-0.5"
               style={{
                 color: 'var(--text-subtle)',
                 fontStyle: 'italic',
                 display: '-webkit-box',
                 WebkitLineClamp: 2,
                 WebkitBoxOrient: 'vertical',
                 overflow: 'hidden',
               }}>
              {emptyCopy}
            </p>
          )}
        </div>
        <Chevron open={isOpen} />
      </button>

      {/* Expanded body */}
      {isOpen && (
        <div className="border-t px-4 py-4 space-y-4"
             style={{ borderColor: 'var(--card-border)' }}>
          {children}

          {canConfirm && (
            <div className="flex items-center gap-2 pt-3 border-t flex-wrap"
                 style={{ borderColor: 'var(--card-border)' }}>
              {saveError && (
                <p className="text-xs text-burgundy w-full">{formatErrorMessage(saveError, t).primary}</p>
              )}
              {confirmed ? (
                <button
                  type="button"
                  onClick={onUnconfirm}
                  className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
                  style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
                >
                  {t('setup.unconfirm')}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={onSaveAndConfirm}
                    disabled={saving || !!confirmDisabledReason}
                    title={confirmDisabledReason || undefined}
                    className="text-xs font-semibold px-4 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? t('common.saving') : (confirmLabel || t('setup.confirm'))}
                  </button>
                  {confirmDisabledReason && (
                    <span className="text-[11px] text-pending ml-1">
                      {confirmDisabledReason}
                    </span>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

// ─── icons ───

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 10 10" aria-hidden="true">
      <path d="M2 5 L4 7 L8 3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Chevron({ open }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"
         className="shrink-0 transition-transform"
         style={{
           color: 'var(--text-subtle)',
           transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
         }}>
      <path d="M3 4.5 L6 8 L9 4.5" fill="none" stroke="currentColor"
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
