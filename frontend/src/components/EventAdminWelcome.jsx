import { useState, useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';

/**
 * EventAdminWelcome — one-time reassurance strip on the Setup Hub.
 *
 * Shown to a Staff user (not Super Admin) when they're viewing an event
 * they created. v0.50j gave Staff users with can_create_events the
 * ability to create events; the create_event service auto-grants them
 * a per-event admin EventUserAssignment so they don't get locked out.
 * That's invisible to the user though — they may land on the Setup
 * Hub after creation wondering "am I allowed to be here?"
 *
 * This strip answers the question: "Yes, you're the Event Admin for
 * this event, because you created it. Here's what that means."
 *
 * Dismissal is persisted per-event in localStorage so the strip
 * doesn't nag on every visit. Super Admins never see it.
 *
 * Props:
 *   eventId   — used as the dismissal-key suffix in localStorage
 *   eventName — displayed in the copy
 *   onClose   — optional callback when user dismisses
 */
export default function EventAdminWelcome({ eventId, eventName, onClose }) {
  const { t } = useI18n();
  const storageKey = `moimio.event_admin_welcome_dismissed:${eventId}`;
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(storageKey) === '1';
    } catch {
      return false;
    }
  });

  // If the eventId changes, re-check storage.
  useEffect(() => {
    try {
      setDismissed(localStorage.getItem(storageKey) === '1');
    } catch {
      setDismissed(false);
    }
  }, [storageKey]);

  if (dismissed) return null;

  const handleDismiss = () => {
    try {
      localStorage.setItem(storageKey, '1');
    } catch {
      /* ignore — sessionStorage/localStorage may be blocked */
    }
    setDismissed(true);
    if (onClose) onClose();
  };

  return (
    <div
      className="rounded-2xl px-4 py-3 mb-4 flex items-start gap-3"
      style={{
        background: 'rgba(70, 130, 180, 0.08)',
        border: '1px solid rgba(70, 130, 180, 0.25)',
      }}
    >
      {/* Shield icon — signals "your access is protected" */}
      <svg
        width="18" height="18" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round"
        style={{ color: 'var(--io-accent)', flexShrink: 0, marginTop: 1 }}
        aria-hidden="true"
      >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold mb-0.5" style={{ color: 'var(--text-primary)' }}>
          {t('event.admin_welcome.title')}
        </p>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          {t('event.admin_welcome.body', { name: eventName })}
        </p>
      </div>

      <button
        type="button"
        onClick={handleDismiss}
        className="shrink-0 text-xs font-medium px-2 py-1 rounded hover:bg-black/5 dark:hover:bg-white/10"
        style={{ color: 'var(--text-subtle)' }}
        aria-label={t('common.dismiss')}
      >
        {t('common.got_it')}
      </button>
    </div>
  );
}
