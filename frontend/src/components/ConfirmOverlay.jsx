import { useState, useCallback } from 'react';
import { useI18n } from '../hooks/useI18n';

export function useConfirmOverlay() {
  const [state, setState] = useState(null);

  const confirm = useCallback(({ title, message, confirmLabel, danger = false }) => {
    return new Promise((resolve) => {
      setState({ title, message, confirmLabel, danger, resolve });
    });
  }, []);

  const handleConfirm = () => { state?.resolve(true); setState(null); };
  const handleCancel = () => { state?.resolve(false); setState(null); };

  const ConfirmOverlay = () => {
    const { t } = useI18n();
    if (!state) return null;
    return (
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-24" onClick={handleCancel}>
        <div className="fixed inset-0 bg-black/20" />
        <div className="relative bg-card-solid rounded-xl shadow-2xl border border-card p-6 max-w-md w-full mx-4"
          onClick={e => e.stopPropagation()}>
          {state.title && <h3 className="font-heading font-bold text-body mb-2">{state.title}</h3>}
          {state.message && <p className="text-sm text-muted mb-4 leading-relaxed">{state.message}</p>}
          <div className="flex justify-end gap-2">
            <button onClick={handleCancel}
              className="text-sm px-4 py-2 rounded-lg border border-card text-muted hover:bg-neutral-tint transition-colors">
              {t('common.cancel')}
            </button>
            <button onClick={handleConfirm}
              className={`text-sm font-semibold px-4 py-2 rounded-lg transition-colors text-white ${
                state.danger ? 'bg-burgundy hover:bg-burgundy-700' : 'bg-steel-blue hover:bg-mid-navy'
              }`}>
              {state.confirmLabel || t('common.save')}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return { confirm, ConfirmOverlay };
}
