import { useState, useRef } from 'react';
import { useI18n } from '../hooks/useI18n';
import { getToken } from '../services/api';
import TranslatedError from './TranslatedError';

/**
 * RestoreModal — upload a Moimio backup ZIP, preview contents, confirm restore.
 *
 * Props:
 *   onClose  — () => void
 *   onDone   — () => void  called after successful restore (navigate away)
 */
export default function RestoreModal({ onClose, onDone }) {
  const { t } = useI18n();
  const fileRef = useRef(null);

  // 'idle' | 'previewing' | 'preview_ready' | 'restoring' | 'done'
  const [stage, setStage] = useState('idle');
  const [fileName, setFileName] = useState('');
  const [fileData, setFileData] = useState(null);   // raw File object for re-upload
  const [preview, setPreview] = useState(null);     // summary from /restore/preview
  const [result, setResult] = useState(null);       // result from /restore/confirm
  const [error, setError] = useState(null);

  // ── Preview ────────────────────────────────────────────────────────────────
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setFileData(file);
    setError(null);
    setPreview(null);
    setStage('previewing');

    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/events/restore/preview', {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      // v0.70d-3c-8: handle non-JSON responses (e.g. server returned
      // "Internal Server Error" plain text) without leaking a JSON
      // parse exception into the UI.
      const json = await res.json().catch(() => null);
      if (!res.ok) {
        const httpErr = new Error(`HTTP ${res.status}`);
        httpErr.status = res.status;
        if (json?.detail && typeof json.detail === 'object' && typeof json.detail.key === 'string') {
          httpErr.i18nKey = json.detail.key;
          if (json.detail.params) httpErr.i18nParams = json.detail.params;
        }
        // friendlyKey fallback by status — mirrors services/api.js
        if (res.status === 401) httpErr.friendlyKey = 'errors.unauthorised';
        else if (res.status === 403) httpErr.friendlyKey = 'errors.forbidden';
        else if (res.status === 404) httpErr.friendlyKey = 'errors.not_found';
        else if (res.status === 422) httpErr.friendlyKey = 'errors.validation';
        else if (res.status >= 500) httpErr.friendlyKey = 'errors.server';
        throw httpErr;
      }
      setPreview(json);
      setStage('preview_ready');
    } catch (err) {
      setError(err);
      setStage('idle');
    }
  };

  // ── Confirm ────────────────────────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!fileData) return;
    setStage('restoring');
    setError(null);

    try {
      const form = new FormData();
      form.append('file', fileData);
      const res = await fetch('/api/events/restore/confirm', {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      const json = await res.json().catch(() => null);
      if (!res.ok) {
        const httpErr = new Error(`HTTP ${res.status}`);
        httpErr.status = res.status;
        if (json?.detail && typeof json.detail === 'object' && typeof json.detail.key === 'string') {
          httpErr.i18nKey = json.detail.key;
          if (json.detail.params) httpErr.i18nParams = json.detail.params;
        }
        if (res.status === 401) httpErr.friendlyKey = 'errors.unauthorised';
        else if (res.status === 403) httpErr.friendlyKey = 'errors.forbidden';
        else if (res.status === 404) httpErr.friendlyKey = 'errors.not_found';
        else if (res.status === 422) httpErr.friendlyKey = 'errors.validation';
        else if (res.status >= 500) httpErr.friendlyKey = 'errors.server';
        throw httpErr;
      }
      setResult(json);
      setStage('done');
    } catch (err) {
      setError(err);
      setStage('preview_ready');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      onClick={onClose}>
      <div className="bg-card-solid rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="px-5 py-4 border-b border-card flex items-start justify-between">
          <div>
            <h3 className="font-heading font-bold text-body text-base">{t('portability.restore')}</h3>
            {fileName && <p className="text-xs text-subtle mt-0.5">{fileName}</p>}
          </div>
          <button onClick={onClose} className="text-subtle hover:text-muted text-lg leading-none ml-2">✕</button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">

          {/* Error */}
          <TranslatedError err={error} className="text-xs rounded-lg p-3" />

          {/* Done */}
          {stage === 'done' && result && (
            <div className="space-y-3">
              <div className="bg-accent-tint rounded-xl p-4 text-sm font-semibold text-accent">
                {t('portability.success')}
              </div>
              <div className="bg-neutral-tint rounded-xl p-4 space-y-1.5 text-xs text-muted">
                <p className="font-semibold text-body text-sm">{result.new_event_name}</p>
                <p>{t('portability.participants_found').replace('{n}', result.counts?.participants ?? 0)}</p>
                <p>{t('portability.allocations_found').replace('{n}', result.counts?.allocations ?? 0)}</p>
              </div>
            </div>
          )}

          {/* Upload */}
          {stage !== 'done' && (
            <>
              <button
                onClick={() => fileRef.current?.click()}
                disabled={stage === 'previewing' || stage === 'restoring'}
                className="w-full border-2 border-dashed border-card hover:border-steel-blue/40 rounded-xl py-5 text-sm text-muted hover:text-accent transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-center">
                {stage === 'previewing'
                  ? t('portability.previewing')
                  : t('portability.upload_hint')}
              </button>
              <input ref={fileRef} type="file" accept=".zip" className="hidden" onChange={handleFileChange} />

              {/* Preview summary */}
              {preview && (
                <div className="bg-neutral-tint rounded-xl p-4 space-y-2">
                  <p className="font-semibold text-body text-sm">{preview.event_name}</p>
                  <p className="text-xs text-subtle">{t('portability.exported_at')}: {preview.exported_at ? new Date(preview.exported_at).toLocaleString() : '—'}</p>
                  <div className="pt-1 grid grid-cols-2 gap-1.5 text-xs text-muted">
                    <span>👤 {t('portability.participants_found').replace('{n}', preview.counts?.participants ?? 0)}</span>
                    <span>📦 {t('portability.allocations_found').replace('{n}', preview.counts?.allocations ?? 0)}</span>
                  </div>
                  <p className="text-[10px] text-subtle pt-1 italic">{t('portability.restore_as_new_hint')}</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-card flex justify-end gap-2">
          {stage === 'done' ? (
            <button onClick={onDone}
              className="px-4 py-2 rounded-xl bg-deep-navy text-white text-xs font-semibold hover:bg-mid-navy transition-colors">
              {t('portability.go_to_events')}
            </button>
          ) : (
            <>
              <button onClick={onClose}
                className="px-4 py-2 rounded-xl border border-card text-muted text-xs hover:bg-neutral-tint transition-colors">
                {t('common.cancel')}
              </button>
              <button
                onClick={handleConfirm}
                disabled={stage !== 'preview_ready'}
                className="px-4 py-2 rounded-xl bg-deep-navy text-white text-xs font-semibold hover:bg-mid-navy transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                {stage === 'restoring'
                  ? t('portability.restoring')
                  : t('portability.confirm')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
