/**
 * RegistrationStateBanner — shown on the Event-phase board to summarise
 * registration status, with a quick action to toggle it.
 *
 * Two states (mutually exclusive — only one renders at a time):
 *
 *   OPEN   — "Registration is still open" + "Close registration" button.
 *            Gold left stripe (attention, informational).
 *            Shows when phase=Event AND event.status === 'open'.
 *
 *   CLOSED — "Registration is closed" + "Re-open registration" button.
 *            Muted grey left stripe (settled state, no urgency).
 *            Shows when phase=Event AND event.status === 'closed'.
 *
 * Admins see the action button. Staff just see informational text.
 *
 * Props:
 *   - event              — required; drives which variant renders
 *   - isAdmin            — whether to show the action button
 *   - onClose            — close-registration handler (for OPEN state)
 *   - onReopen           — re-open-registration handler (for CLOSED state)
 *   - busy               — disables the action button during in-flight PATCH
 */

import { useI18n } from '../hooks/useI18n';

export default function RegistrationStateBanner({
  event, isAdmin, onClose, onReopen, busy = false,
}) {
  const { t } = useI18n();

  if (!event) return null;

  const isOpen = event.status === 'open';
  const isClosed = event.status === 'closed';
  if (!isOpen && !isClosed) return null;

  const stripeColor = isOpen ? '#FFD700' : 'var(--card-border)';
  const title = isOpen ? t('banner.reg_still_open.title') : t('banner.reg_closed.title');
  const body  = isOpen ? t('banner.reg_still_open.body')  : t('banner.reg_closed.body');
  const actionLabel = isOpen
    ? t('banner.reg_still_open.action')
    : t('banner.reg_closed.action');
  const handler = isOpen ? onClose : onReopen;

  return (
    <div
      className="card-surface-solid p-4 mb-4 flex items-start gap-3"
      style={{ borderLeft: `4px solid ${stripeColor}` }}
      role="status"
    >
      <div className="flex-1 min-w-0">
        <p className="font-body font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
          {title}
        </p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
          {body}
        </p>
      </div>
      {isAdmin && handler && (
        <button
          type="button"
          onClick={handler}
          disabled={busy}
          className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50 whitespace-nowrap shrink-0"
          style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
