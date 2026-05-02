/**
 * ConfirmEditModal — explicit confirmation step for participant field edits.
 *
 * v1.0-pre #2: per Johannes's instruction, every field edit on a participant
 * should require explicit confirmation rather than auto-saving on blur.
 * Shows the old value, the new value, and a primary "Confirm" button. The
 * user can also cancel.
 *
 * Renders nothing when `open` is false.
 *
 * Props:
 *   open       — boolean, render the modal when true
 *   fieldLabel — human-readable name of the field being changed (translated)
 *   oldValue   — current value (string, displayed as muted strikethrough-ish)
 *   newValue   — proposed value (string, displayed as the highlighted target)
 *   participantName — name of the affected participant (translated for context)
 *   onConfirm  — async handler called when user clicks Confirm. Modal closes
 *                automatically once the promise resolves.
 *   onCancel   — handler called on Cancel or Esc. Closes immediately.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

export default function ConfirmEditModal({
  open, fieldLabel, oldValue, newValue, participantName, onConfirm, onCancel,
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);

  // Esc to close (when not busy — don't let users escape mid-save).
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape' && !busy) onCancel();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, busy, onCancel]);

  if (!open) return null;

  const handleConfirm = async () => {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  };

  // Render an empty value as the placeholder em-dash for visual symmetry.
  const display = (v) => (v === '' || v === null || v === undefined) ? '—' : v;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0, 0, 0, 0.5)' }}
      onClick={busy ? undefined : onCancel}
    >
      <div
        className="card-surface-solid rounded-2xl shadow-xl max-w-md w-full p-5"
        style={{ border: '1px solid var(--card-border)' }}
        onClick={e => e.stopPropagation()}
      >
        <h2 className="font-heading text-base font-bold mb-1"
          style={{ color: 'var(--text-primary)' }}>
          {t('people.edit.confirm.title')}
        </h2>
        <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
          {t('people.edit.confirm.body', { name: participantName, field: fieldLabel })}
        </p>

        <div className="rounded-card p-3 mb-4 space-y-2"
          style={{ background: 'var(--app-bg)', border: '1px solid var(--card-border)' }}>
          <div>
            <div className="text-[10px] uppercase tracking-caps font-semibold mb-0.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('people.edit.confirm.from')}
            </div>
            <div className="text-sm break-words"
              style={{ color: 'var(--text-muted)', textDecoration: 'line-through', textDecorationColor: 'var(--text-subtle)' }}>
              {display(oldValue)}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-caps font-semibold mb-0.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('people.edit.confirm.to')}
            </div>
            <div className="text-sm font-semibold break-words"
              style={{ color: 'var(--text-primary)' }}>
              {display(newValue)}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="text-sm font-medium px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={busy}
            className="text-sm font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50"
          >
            {busy
              ? t('people.edit.confirm.saving')
              : t('people.edit.confirm.button')}
          </button>
        </div>
      </div>
    </div>
  );
}
