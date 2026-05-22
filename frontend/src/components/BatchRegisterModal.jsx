import { useState, useRef } from 'react';
import { useI18n } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';
import { getToken } from '../services/api';
import TranslatedError from './TranslatedError';

/**
 * BatchRegisterModal — bulk CSV import for a single event.
 *
 * Props:
 *   eventId  — UUID string
 *   onClose  — () => void
 *   onDone   — () => void  called after a successful commit so PeopleTable refreshes
 */
export default function BatchRegisterModal({ eventId, onClose, onDone }) {
  const { t, lang } = useI18n();
  const { showToast, ToastHost } = useToast();
  const fileRef = useRef(null);

  // 'idle' | 'previewing' | 'preview_ready' | 'committing' | 'done'
  const [stage, setStage] = useState('idle');
  const [previewData, setPreviewData] = useState(null);   // full response from /batch/preview
  const [result, setResult] = useState(null);             // response from /batch/commit
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
  // v1.0.0p: user-selected date format. 'eu' = DD.MM.YYYY (default
  // for everyone except KO UI); 'iso' = YYYY.MM.DD (also covers
  // Korean numeric convention — same shape). Sent as query param
  // to /batch/preview; the backend's _parse_dob_smart resolves any
  // genuinely-ambiguous numeric date per this hint.
  const [dobFormat, setDobFormat] = useState(lang === 'ko' ? 'iso' : 'eu');

  // ── Template download ──────────────────────────────────────────────────────
  const handleTemplateDownload = async () => {
    try {
      const res = await fetch(
        `/api/events/${eventId}/participants/batch/template.csv`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      const cd = res.headers.get('Content-Disposition') || '';
      const match = cd.match(/filename="?([^"]+)"?/);
      a.download = match ? match[1] : 'moimio_template.csv';
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setError(err);
    }
  };

  // ── CSV preview ────────────────────────────────────────────────────────────
  // v0.83 #34: extracted to a helper so both the file-input change handler
  // and the drag-and-drop handler below can share the same upload path.
  const processCsvFile = async (file) => {
    if (!file) return;
    // Light validation: extension or MIME hint that this is CSV. Accept
    // common Excel-saves variants too. Anything else is silently ignored
    // (the dropzone gives no error toast — the user just sees nothing
    // happen, which is the right pattern for accidental drags).
    const looksLikeCsv = file.name.toLowerCase().endsWith('.csv')
      || file.type === 'text/csv'
      || file.type === 'application/vnd.ms-excel';
    if (!looksLikeCsv) {
      setError(new Error(t('batch.err.not_csv') || 'Please drop a .csv file.'));
      return;
    }
    setFileName(file.name);
    setError(null);
    setPreviewData(null);
    setStage('previewing');

    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(
        `/api/events/${eventId}/participants/batch/preview?dob_format=${dobFormat}`,
        { method: 'POST', headers: { Authorization: `Bearer ${getToken()}` }, body: form }
      );
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
      setPreviewData(json);
      setStage('preview_ready');
    } catch (err) {
      setError(err);
      setStage('idle');
    }
  };

  const handleFileChange = (e) => processCsvFile(e.target.files?.[0]);

  // v0.83 #34: drag-and-drop. State lives on the dropzone button below;
  // these are the handlers it wires up. Always preventDefault on dragover
  // so the drop event fires (browser default is to navigate to the file).
  const [isDragOver, setIsDragOver] = useState(false);
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (stage === 'previewing' || stage === 'committing') return;
    setIsDragOver(true);
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (stage === 'previewing' || stage === 'committing') return;
    const file = e.dataTransfer?.files?.[0];
    processCsvFile(file);
  };

  // ── Commit ─────────────────────────────────────────────────────────────────
  const handleCommit = async () => {
    if (!previewData) return;
    setStage('committing');
    setError(null);
    try {
      const res = await fetch(
        `/api/events/${eventId}/participants/batch/commit`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            rows: previewData.rows,
            // v0.85 #16: round-trip the new-custom-field info from the
            // preview so the backend creates definitions and writes
            // values for any unknown CSV columns the admin chose to
            // accept (we surface them in a banner above; no opt-out yet
            // — accepting them is implicit by clicking Commit).
            new_custom_fields: previewData.new_custom_fields || [],
            unknown_values_by_row: previewData.unknown_values_by_row || [],
          }),
        }
      );
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
      // v0.70d-3a-4 (M1): success toast on import. The modal stays
      // open showing a full summary card with created/skipped/failed
      // counts — the toast is the at-the-moment feedback for the
      // commit action specifically. Uses json.created (the actually-
      // imported count) so the toast number matches what landed.
      if (json.created > 0) {
        showToast(t('batch.import_complete', { n: json.created }), 'success');
      }
      onDone();
    } catch (err) {
      setError(err);
      setStage('preview_ready');
    }
  };

  const validCount = previewData?.summary?.valid ?? 0;
  const canCommit = stage === 'preview_ready' && validCount > 0;

  // ── Row colour ─────────────────────────────────────────────────────────────
  const rowStyle = (row) => {
    if (!row.valid) return 'bg-alert-tint border-alert';
    if (row.warnings?.length) return 'bg-alert-tint border-alert';
    return 'bg-accent-tint border-accent';
  };

  const rowDot = (row) => {
    if (!row.valid) return '🔴';
    if (row.warnings?.length) return '🟡';
    return '🟢';
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      onClick={onClose}>
      <div className="bg-card-solid rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="px-5 py-4 border-b border-card flex items-start justify-between shrink-0">
          <div>
            <h3 className="font-heading font-bold text-body text-base">{t('batch.title')}</h3>
            {fileName && <p className="text-xs text-subtle mt-0.5">{fileName}</p>}
          </div>
          <button onClick={onClose} className="text-subtle hover:text-muted text-lg leading-none ml-2 shrink-0">✕</button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* Error banner */}
          <TranslatedError err={error} className="text-xs rounded-lg p-3" />

          {/* Done state */}
          {stage === 'done' && result && (
            <div className="space-y-3">
              <div className={`rounded-xl p-4 text-sm font-semibold ${result.failed === 0 ? 'bg-accent-tint text-accent' : 'bg-alert-tint text-alert'}`}>
                {result.failed === 0
                  ? t('batch.success')
                  : t('batch.partial_success')}
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-accent-tint rounded-xl p-3">
                  <div className="text-2xl font-bold text-accent">{result.created}</div>
                  <div className="text-xs text-accent mt-0.5">{t('batch.created')}</div>
                </div>
                <div className="bg-neutral-tint rounded-xl p-3">
                  <div className="text-2xl font-bold text-muted">{result.skipped}</div>
                  <div className="text-xs text-subtle mt-0.5">{t('batch.skipped')}</div>
                </div>
                <div className={`rounded-xl p-3 ${result.failed > 0 ? 'bg-alert-tint' : 'bg-neutral-tint'}`}>
                  <div className={`text-2xl font-bold ${result.failed > 0 ? 'text-alert' : 'text-subtle'}`}>{result.failed}</div>
                  <div className={`text-xs mt-0.5 ${result.failed > 0 ? 'text-alert' : 'text-subtle'}`}>{t('batch.failed')}</div>
                </div>
              </div>
              {result.errors?.length > 0 && (
                <div className="bg-alert-tint rounded-xl p-3 space-y-1">
                  {result.errors.map((e, i) => (
                    <p key={i} className="text-xs text-alert">
                      {t('batch.row_n').replace('{n}', e.row_num)}: {e.reason}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Upload + template — idle or preview_ready */}
          {stage !== 'done' && (
            <>
              <div className="flex items-center gap-3">
                {/* v0.83 #34: drag-and-drop. The same button doubles as a
                    drop target — drag a .csv from the file explorer and
                    release over this card. Click still works as before. */}
                <button
                  onClick={() => fileRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  disabled={stage === 'previewing' || stage === 'committing'}
                  className={`flex-1 border-2 border-dashed rounded-xl py-4 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-center ${
                    isDragOver
                      ? 'border-steel-blue bg-steel-blue/5 text-accent'
                      : 'border-card hover:border-steel-blue/40 text-muted hover:text-accent'
                  }`}>
                  {stage === 'previewing'
                    ? t('batch.previewing')
                    : (isDragOver
                        ? t('batch.drop_here')
                        : t('batch.upload_csv'))}
                </button>
                <button
                  onClick={handleTemplateDownload}
                  className="shrink-0 px-3 py-2 rounded-xl border border-card text-xs text-muted hover:text-accent hover:border-steel-blue/40 transition-colors">
                  ↓ {t('batch.template_download')}
                </button>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
              {/* v1.0.0p: prominent date-format selector. Was a 10px
                  grey footnote that disappeared once preview rendered;
                  now a proper band above the upload area, two clear
                  radios, default European (or ISO for KO UI). The
                  backend honours this hint to disambiguate genuinely-
                  ambiguous numeric dates (both first components ≤ 12,
                  e.g. 01.05.2000) — Excel-mangled round-trips no
                  longer reject ~40% of real DOBs. */}
              {stage !== 'previewing' && stage !== 'committing' && !previewData && (
                <div className="mt-3 rounded-xl border p-3"
                  style={{ borderColor: 'var(--card-border)', background: 'var(--app-bg)' }}>
                  <div className="text-[10px] uppercase tracking-caps font-semibold mb-2"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('batch.date_format.label')}
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <label className="flex-1 flex items-start gap-2 cursor-pointer rounded-lg px-3 py-2 transition-colors"
                      style={{
                        background: dobFormat === 'eu' ? 'var(--accent-tint)' : 'transparent',
                        border: '1px solid',
                        borderColor: dobFormat === 'eu' ? 'var(--io-accent)' : 'var(--card-border)',
                      }}>
                      <input type="radio" name="dob-format" value="eu"
                        checked={dobFormat === 'eu'}
                        onChange={() => setDobFormat('eu')}
                        className="mt-0.5" />
                      <div className="min-w-0">
                        <div className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {t('batch.date_format.eu')}
                        </div>
                        <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                          {t('batch.date_format.eu.example')}
                        </div>
                      </div>
                    </label>
                    <label className="flex-1 flex items-start gap-2 cursor-pointer rounded-lg px-3 py-2 transition-colors"
                      style={{
                        background: dobFormat === 'iso' ? 'var(--accent-tint)' : 'transparent',
                        border: '1px solid',
                        borderColor: dobFormat === 'iso' ? 'var(--io-accent)' : 'var(--card-border)',
                      }}>
                      <input type="radio" name="dob-format" value="iso"
                        checked={dobFormat === 'iso'}
                        onChange={() => setDobFormat('iso')}
                        className="mt-0.5" />
                      <div className="min-w-0">
                        <div className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {t('batch.date_format.iso')}
                        </div>
                        <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                          {t('batch.date_format.iso.example')}
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              )}

              {/* Summary bar */}
              {previewData && (
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="bg-neutral-tint text-muted rounded-lg px-2 py-1">
                    {t('batch.total_n').replace('{n}', previewData.summary.total)}
                  </span>
                  <span className="bg-accent-tint text-accent rounded-lg px-2 py-1">
                    🟢 {previewData.summary.valid}
                  </span>
                  {previewData.summary.invalid > 0 && (
                    <span className="bg-alert-tint text-alert rounded-lg px-2 py-1">
                      🔴 {previewData.summary.invalid}
                    </span>
                  )}
                  {previewData.summary.with_warnings > 0 && (
                    <span className="bg-alert-tint text-alert rounded-lg px-2 py-1">
                      🟡 {previewData.summary.with_warnings}
                    </span>
                  )}
                </div>
              )}

              {/* v0.85 #16: new-custom-fields banner. When the parser
                  finds unknown columns (not Moimio-export-only and not
                  matching existing custom fields), warn the admin that
                  they will be added as custom fields, hidden from the
                  public registration form by default. Implicit accept on
                  Commit; admin can rename headers in the source file
                  and re-upload to skip. */}
              {previewData && (previewData.new_custom_fields || []).length > 0 && (
                <div
                  className="rounded-card p-3 text-xs"
                  style={{
                    background: 'rgba(212,168,44,0.08)',
                    border: '1px solid rgba(212,168,44,0.30)',
                    color: 'var(--text-body)',
                  }}
                >
                  <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                    {t('batch.new_fields_title', { n: previewData.new_custom_fields.length })}
                  </div>
                  <div className="mb-1.5">
                    {t('batch.new_fields_body')}
                  </div>
                  <ul className="list-disc pl-5 space-y-0.5">
                    {previewData.new_custom_fields.map(label => (
                      <li key={label} className="font-mono">{label}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* v0.58h: Defensive same-gender warning.
                  If every valid row has the same gender AND the file has
                  more than 2 rows AND at least one row has a gender set,
                  warn the organiser that this might be CSV autofill from
                  Excel/Numbers. Doesn't block — single-gender events are
                  legitimate. */}
              {(() => {
                const validRows = (previewData?.rows || []).filter(r => r.valid);
                if (validRows.length < 3) return null;
                const genders = validRows
                  .map(r => r.data?.gender)
                  .filter(g => g);  // ignore blanks
                if (genders.length < 3) return null;
                const allSame = genders.every(g => g === genders[0]);
                if (!allSame) return null;
                return (
                  <div className="rounded-xl px-3 py-2 text-xs flex items-start gap-2"
                    style={{
                      background: 'rgba(234, 179, 8, 0.08)',
                      border: '1px solid rgba(234, 179, 8, 0.3)',
                      color: 'var(--text-muted)',
                    }}>
                    <span className="shrink-0">⚠️</span>
                    <span>
                      {t('batch.same_gender_warning', { gender: genders[0] })}
                    </span>
                  </div>
                );
              })()}

              {/* Preview table.
                  v0.61a: sticky <thead> so the column headers stay
                  visible when scrolling through a 50+ row CSV.
                  v0.61a: responsive column strategy — on < sm (mobile),
                  the "#" column is hidden and Email folds under Name in
                  a muted sub-line. On sm+ the original 4-column layout
                  returns. Dark-mode palette fix deferred to v0.70. */}
              {previewData?.rows?.length > 0 && (
                <div className="border border-card rounded-xl overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 z-10">
                      <tr className="bg-neutral-tint text-muted">
                        <th className="hidden sm:table-cell px-3 py-2 text-left font-semibold w-8">#</th>
                        <th className="px-3 py-2 text-left font-semibold">{t('batch.preview_name')}</th>
                        <th className="hidden sm:table-cell px-3 py-2 text-left font-semibold">{t('batch.preview_email')}</th>
                        <th className="px-3 py-2 text-left font-semibold">{t('batch.preview_status')}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {previewData.rows.map(row => (
                        <tr key={row.row_num} className={`border-l-2 ${rowStyle(row)}`}>
                          <td className="hidden sm:table-cell px-3 py-2 text-subtle">{row.row_num}</td>
                          <td className="px-3 py-2 font-medium text-body">
                            <span className="sm:hidden text-subtle mr-1">#{row.row_num}</span>
                            {row.data?.first_name || '—'} {row.data?.last_name || ''}
                            {row.data?.email && (
                              <span className="block sm:hidden text-subtle text-[10px] truncate">
                                {row.data.email}
                              </span>
                            )}
                          </td>
                          <td className="hidden sm:table-cell px-3 py-2 text-muted">{row.data?.email || '—'}</td>
                          <td className="px-3 py-2">
                            <span className="mr-1">{rowDot(row)}</span>
                            {row.errors?.length > 0 && (
                              <span className="text-alert">{row.errors.map(e => t(`batch.err.${e}`) || e).join(', ')}</span>
                            )}
                            {row.errors?.length === 0 && row.warnings?.length > 0 && (
                              <span className="text-alert">{row.warnings.map(w => t(`batch.warn.${w}`) || w).join(', ')}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-card flex justify-end gap-2 shrink-0">
          {stage === 'done' ? (
            <button onClick={onClose}
              className="px-4 py-2 rounded-xl bg-deep-navy text-white text-xs font-semibold hover:bg-mid-navy transition-colors">
              {t('common.close')}
            </button>
          ) : (
            <>
              <button onClick={onClose}
                className="px-4 py-2 rounded-xl border border-card text-muted text-xs hover:bg-neutral-tint transition-colors">
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCommit}
                disabled={!canCommit}
                className="px-4 py-2 rounded-xl bg-deep-navy text-white text-xs font-semibold hover:bg-mid-navy transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                {stage === 'committing'
                  ? t('batch.committing')
                  : t('batch.commit').replace('{n}', validCount)}
              </button>
            </>
          )}
        </div>
      </div>
      <ToastHost />
    </div>
  );
}
