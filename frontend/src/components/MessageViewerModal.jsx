import { useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';

/**
 * MessageViewerModal — read-only overlay showing a participant's full
 * registration message.
 *
 * Why this exists (v0.70d-3c-10): the People table's message column
 * previously relied on a `title` tooltip, which is hover-only and so
 * useless on touch devices. The desktop tooltip is preserved (showing
 * a 200-char preview), and clicking the cell now opens this modal
 * with the full message regardless of viewport.
 *
 * Pattern mirrors NotesModal (overlay + click-outside-to-close + X
 * close button + whitespace-pre-wrap content) but is much simpler:
 * no API, no state, no submit form. Pure display.
 */
export default function MessageViewerModal({ participantName, message, onClose }) {
  const { t } = useI18n();

  // Esc-to-close — small UX nicety that keyboard users expect from
  // modals. Bound on mount, cleaned up on unmount.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-card-solid rounded-xl shadow-lg w-full max-w-lg max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-5 py-3 border-b border-card flex items-center justify-between shrink-0">
          <div className="min-w-0">
            <h3 className="font-heading font-bold text-body">{t('people.col.message')}</h3>
            {participantName && <p className="text-xs text-subtle truncate">{participantName}</p>}
          </div>
          <button onClick={onClose}
            className="text-subtle hover:text-muted text-lg shrink-0 ml-2"
            aria-label={t('common.close')}>
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-3">
          <p className="text-sm text-body whitespace-pre-wrap break-words">
            {message}
          </p>
        </div>

        <div className="px-5 py-3 border-t border-card shrink-0 flex justify-end">
          <button onClick={onClose}
            className="bg-steel-blue text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-mid-navy transition-colors">
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
}
