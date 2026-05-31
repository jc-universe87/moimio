import { useState, useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';
import TranslatedError from './TranslatedError';

/**
 * DangerZoneDeletionModal — workspace-level "delete this workspace" modal.
 *
 * Three visual states, one component:
 *   1. confirm   — explainer + typed-confirmation field + Delete/Cancel
 *   2. submitting — spinner state on the Delete button
 *   3. success   — what-happens-next view with a single Close action
 *
 * Why not StrongDeleteConfirm? That component is built around typing the
 * specific item's NAME (e.g. an event name) and shows an assignee count
 * that defaults to "No items affected" when zero — misleading copy in
 * the workspace-deletion context where everything is affected. This
 * modal is purpose-built for fixed-token confirmation ("type DELETE").
 *
 * The wire contract uses the canonical English token "DELETE" in every
 * locale. The UI shows the token in-locale (warmer-but-firm framing per
 * the customer-facing copy decision); the submit normalises case so
 * users typing "delete" or "Delete" still pass.
 *
 * Props:
 *   open        — boolean; if false, returns null
 *   onSubmit    — async () => Promise<{event_id: string}>; called when
 *                  user types DELETE and clicks Confirm. Returns the
 *                  request-deletion API response on success, or throws.
 *   onClose     — called for Cancel or Close (both confirm and success
 *                  states). Caller is responsible for setting open=false.
 *   userEmail   — the super-admin's email; shown in the success state
 *                  as where the export-link email will be sent.
 */
export default function DangerZoneDeletionModal({ open, onSubmit, onClose, userEmail }) {
  const { t } = useI18n();
  const [typed, setTyped] = useState('');
  const [phase, setPhase] = useState('confirm');  // 'confirm' | 'submitting' | 'success'
  const [error, setError] = useState(null);

  // Reset internal state whenever the modal re-opens. We don't reset on
  // close so the success-state copy stays visible during the close
  // transition (no caller manages that, but the principle is sound).
  useEffect(() => {
    if (open) {
      setTyped('');
      setPhase('confirm');
      setError(null);
    }
  }, [open]);

  if (!open) return null;

  // Match case-insensitively for UX (typing "delete" should also work);
  // the submit normalises to the canonical uppercase "DELETE".
  const matches = typed.trim().toLocaleUpperCase() === 'DELETE';

  const handleConfirm = async () => {
    if (!matches || phase === 'submitting') return;
    setPhase('submitting');
    setError(null);
    try {
      await onSubmit('DELETE');
      setPhase('success');
    } catch (err) {
      setError(err);
      setPhase('confirm');
    }
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: 'rgba(0,0,0,0.5)' }}
      onClick={phase === 'submitting' ? undefined : onClose}
    >
      <div
        className="card-surface-solid rounded-2xl w-full max-w-lg flex flex-col"
        style={{ border: '1px solid var(--card-border)', boxShadow: '0 24px 64px rgba(0,0,0,0.4)' }}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {phase === 'success' ? (
          <SuccessView t={t} userEmail={userEmail} onClose={onClose} />
        ) : (
          <ConfirmView
            t={t}
            typed={typed}
            setTyped={setTyped}
            matches={matches}
            error={error}
            submitting={phase === 'submitting'}
            onConfirm={handleConfirm}
            onCancel={onClose}
          />
        )}
      </div>
    </div>
  );
}

// ─── Confirm view ─────────────────────────────────────────────────────

function ConfirmView({ t, typed, setTyped, matches, error, submitting, onConfirm, onCancel }) {
  return (
    <>
      <div className="p-5" style={{ borderBottom: '1px solid var(--card-border)' }}>
        <h2 className="font-heading font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
          {t('danger_zone.modal.title')}
        </h2>
      </div>

      <div className="p-5 space-y-4">
        <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
          {t('danger_zone.modal.body')}
        </p>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {t('danger_zone.modal.timeline')}
        </p>

        {error && (
          <TranslatedError err={error} variant="compact" />
        )}

        <div>
          <label
            htmlFor="danger-zone-confirm"
            className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
            style={{ color: 'var(--text-subtle)' }}
          >
            {t('danger_zone.modal.confirm_label')}
          </label>
          <input
            id="danger-zone-confirm"
            type="text"
            value={typed}
            onChange={e => setTyped(e.target.value)}
            disabled={submitting}
            autoFocus
            autoComplete="off"
            spellCheck={false}
            className="w-full rounded-card border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
            style={{
              background: 'var(--app-bg)',
              borderColor: 'var(--card-border)',
              color: 'var(--text-primary)',
            }}
          />
        </div>
      </div>

      <div className="flex gap-2 p-5" style={{ borderTop: '1px solid var(--card-border)' }}>
        <button
          type="button"
          onClick={onConfirm}
          disabled={!matches || submitting}
          className="flex-1 text-sm font-semibold px-4 py-2 rounded-card transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ background: 'var(--alert-burgundy)', color: '#fff' }}
        >
          {submitting
            ? t('danger_zone.modal.submitting')
            : t('danger_zone.modal.confirm_button')}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="text-sm font-medium px-4 py-2 rounded-card hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ color: 'var(--text-muted)' }}
        >
          {t('common.cancel')}
        </button>
      </div>
    </>
  );
}

// ─── Success view ─────────────────────────────────────────────────────

function SuccessView({ t, userEmail, onClose }) {
  return (
    <>
      <div className="p-5" style={{ borderBottom: '1px solid var(--card-border)' }}>
        <h2 className="font-heading font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
          {t('danger_zone.success.title')}
        </h2>
      </div>

      <div className="p-5 space-y-3">
        <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
          {t('danger_zone.success.body', { email: userEmail || '' })}
        </p>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {t('danger_zone.success.timeline')}
        </p>
      </div>

      <div className="flex justify-end p-5" style={{ borderTop: '1px solid var(--card-border)' }}>
        <button
          type="button"
          onClick={onClose}
          className="text-sm font-semibold px-4 py-2 rounded-card transition-colors"
          style={{ background: 'var(--io-accent)', color: '#fff' }}
        >
          {t('common.close')}
        </button>
      </div>
    </>
  );
}
