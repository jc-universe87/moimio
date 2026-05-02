import { useI18n } from '../hooks/useI18n';

/**
 * ArchiveConfirm — shared modal for Archive/Unarchive confirmations.
 *
 * v0.51: lifted out of EventDetailPage so both EventsPage (row menu)
 * and EventDetailPage (Danger zone button) can use it. Copy and button
 * label flip based on `event.is_archived`; the caller supplies the
 * handler and the loading flag.
 *
 * Props:
 *   open       — boolean
 *   event      — the event object (needs .is_archived; optional .name)
 *   busy       — archive in flight (disables buttons)
 *   onConfirm  — () => void, triggers the archive/unarchive call
 *   onCancel   — () => void, closes the modal
 */
export default function ArchiveConfirm({ open, event, busy, onConfirm, onCancel }) {
  const { t } = useI18n();
  if (!open || !event) return null;

  const isArchived = !!event.is_archived;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={() => { if (!busy) onCancel?.(); }}
    >
      <div
        className="card-surface-solid rounded-2xl shadow-2xl max-w-md w-full p-6"
        style={{ border: '1px solid var(--card-border)' }}
        onClick={e => e.stopPropagation()}
      >
        <h3 className="font-heading font-bold text-lg mb-2" style={{ color: 'var(--text-primary)' }}>
          {isArchived
            ? (t('event.unarchive.confirm_title'))
            : (t('event.archive.confirm_title'))}
        </h3>
        {event.name && (
          <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
            {event.name}
          </p>
        )}
        <p className="text-sm mb-5" style={{ color: 'var(--text-subtle)' }}>
          {isArchived
            ? (t('event.unarchive.confirm_body'))
            : (t('event.archive.confirm_body'))}
        </p>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="text-xs font-semibold px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className="text-xs font-semibold px-4 py-2 rounded-card text-white bg-steel-blue hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50"
          >
            {busy
              ? (t('common.loading'))
              : (isArchived
                  ? (t('event.unarchive.button'))
                  : (t('event.archive.button')))}
          </button>
        </div>
      </div>
    </div>
  );
}
