/**
 * NoPermissionPage — friendly landing for users with no actionable
 * permissions on the current event (or whose actionable work has
 * not yet started).
 *
 * v0.70d-2a (R12): split one-copy-fits-all into named variants so
 * the page tells the right story for the right situation:
 *   - 'unassigned'       — staff not yet assigned anything for this
 *                          event. Copy: "Nothing assigned yet."
 *   - 'checkin_not_yet'  — check-in staff during Setup/Registration.
 *                          They ARE assigned, their work just hasn't
 *                          started. Copy: "Your check-in starts when
 *                          the event begins."
 *
 * Mechanics in `services/landing.js` already return 'no-access' in
 * both situations; the call-site computes the right variant based
 * on phase + permissions and passes it in.
 *
 * Tone: calm, not error-y. They're not blocked because they did
 * something wrong.
 *
 * Props:
 *   - eventName  — used in the page heading ("for {eventName}")
 *   - variant    — 'unassigned' (default) | 'checkin_not_yet'
 *   - onRefresh  — optional callback; if absent, falls back to
 *                  window.location.reload()
 *   - onSignOut  — sign out + redirect to login (caller wires this)
 */

import { useI18n } from '../hooks/useI18n';

export default function NoPermissionPage({ eventName, variant = 'unassigned', onRefresh, onSignOut }) {
  const { t } = useI18n();

  const handleRefresh = () => {
    if (onRefresh) onRefresh();
    else window.location.reload();
  };

  return (
    <div
      className="min-h-[60vh] flex items-center justify-center p-6"
      style={{ color: 'var(--text-primary)' }}
    >
      <div
        className="card-surface-solid rounded-2xl p-8 max-w-md w-full text-center"
        style={{ border: '1px solid var(--card-border)' }}
      >
        {/* Soft icon — empty inbox / hourglass / waiting */}
        <div className="mx-auto mb-4 flex items-center justify-center" style={{ width: 64, height: 64 }}>
          <svg
            width="64"
            height="64"
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={{ color: 'var(--text-subtle)' }}
          >
            <rect x="14" y="22" width="36" height="28" rx="3" />
            <path d="M14 30h12l3 5h6l3-5h12" />
            <line x1="22" y1="14" x2="42" y2="14" opacity="0.5" />
            <line x1="26" y1="10" x2="38" y2="10" opacity="0.3" />
          </svg>
        </div>

        <h1 className="font-heading font-bold text-xl mb-2" style={{ color: 'var(--text-primary)' }}>
          {t(`no_perm.${variant}.title`)}
        </h1>
        {eventName && (
          <p className="text-sm mb-3" style={{ color: 'var(--text-subtle)' }}>
            {eventName}
          </p>
        )}
        <p className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
          {t(`no_perm.${variant}.body`)}
        </p>
        <p className="text-xs mb-6" style={{ color: 'var(--text-subtle)' }}>
          {t(`no_perm.${variant}.contact_hint`)}
        </p>

        <div className="flex gap-2 justify-center">
          <button
            type="button"
            onClick={handleRefresh}
            className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80"
          >
            ↻ {t('no_perm.refresh')}
          </button>
          {onSignOut && (
            <button
              type="button"
              onClick={onSignOut}
              className="text-xs font-medium px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
              style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
            >
              {t('no_perm.sign_out')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
