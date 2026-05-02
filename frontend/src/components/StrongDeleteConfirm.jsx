import { useState, useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';

import ErrorBanner from './ErrorBanner';
/**
 * StrongDeleteConfirm — modal that requires typing the item's name to
 * confirm deletion. Shows assignee count and up to 10 recently affected
 * participants to make the destructive scope visible.
 *
 * Used for marks deletion in v0.50f. Generic enough to reuse for other
 * destructive actions where "are you sure?" isn't strong enough.
 *
 * Props:
 *   open          — boolean, whether to show
 *   title         — dialog title
 *   itemLabel     — what kind of thing is being deleted (e.g. "mark")
 *   itemName      — the specific name (required typed confirmation)
 *   itemColour    — optional hex colour for a visual dot preview
 *   assigneeCount — total number of affected items
 *   assigneeNames — array of names (shown as pills; max 10 rendered)
 *   warning       — optional additional warning line
 *   onConfirm     — called when user clicks Delete with matching name
 *   onCancel      — called when user dismisses
 */
export default function StrongDeleteConfirm({
  open,
  title,
  itemLabel,
  itemName,
  itemColour,
  assigneeCount = 0,
  assigneeNames = [],
  warning,
  onConfirm,
  onCancel,
  loading = false,
}) {
  const [typed, setTyped] = useState('');
  const { t } = useI18n();

  useEffect(() => {
    if (!open) setTyped('');
  }, [open]);

  if (!open) return null;

  // v0.50j-4: case-insensitive match. The label that shows the phrase
  // to type is rendered uppercase for visual weight (tracking-caps styling),
  // which misleads users into thinking case matters. It doesn't.
  const matches =
    typed.trim().toLocaleLowerCase() === (itemName || '').toLocaleLowerCase();
  const displayedNames = assigneeNames.slice(0, 10);
  const hiddenCount = Math.max(0, assigneeCount - displayedNames.length);

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: 'rgba(0,0,0,0.5)' }}
      onClick={onCancel}
    >
      <div
        className="card-surface-solid rounded-2xl w-full max-w-md flex flex-col"
        style={{ border: '1px solid var(--card-border)', boxShadow: '0 24px 64px rgba(0,0,0,0.4)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="p-5" style={{ borderBottom: '1px solid var(--card-border)' }}>
          <h2 className="font-heading font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
            {title}
          </h2>
        </div>

        <div className="p-5 space-y-4">
          {/* Item preview */}
          <div className="flex items-center gap-2">
            {itemColour && (
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ background: itemColour }}
              />
            )}
            <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
              {itemName}
            </span>
            {itemLabel && (
              <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>
                ({itemLabel})
              </span>
            )}
          </div>

          {/* Assignee count */}
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {assigneeCount === 0
              ? t('strong_delete.no_assignees')
              : t('strong_delete.assignee_count', { n: assigneeCount })}
          </p>

          {/* Recent assignees pills */}
          {displayedNames.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {displayedNames.map((n, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(128,128,128,0.12)', color: 'var(--text-muted)' }}
                >
                  {n}
                </span>
              ))}
              {hiddenCount > 0 && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{ color: 'var(--text-subtle)' }}
                >
                  {t('strong_delete.and_n_more', { n: hiddenCount })}
                </span>
              )}
            </div>
          )}

          {warning && (
            <ErrorBanner className="text-xs rounded-card p-2">
              {warning}
            </ErrorBanner>
          )}

          {/* Type-to-confirm */}
          <div>
            <label
              className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
              style={{ color: 'var(--text-subtle)' }}
            >
              {t('strong_delete.type_to_confirm_label', { name: itemName })}
            </label>
            <input
              type="text"
              value={typed}
              onChange={e => setTyped(e.target.value)}
              autoFocus
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
            disabled={!matches || loading}
            className="flex-1 text-sm font-semibold px-4 py-2 rounded-card transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: matches ? 'var(--alert-burgundy)' : 'var(--alert-burgundy)', color: '#fff' }}
          >
            {loading ? (t('common.deleting')) : t('common.delete')}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="text-sm font-medium px-4 py-2 rounded-card hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ color: 'var(--text-muted)' }}
          >
            {t('common.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
}
