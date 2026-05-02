import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../hooks/useI18n';
import { getToken } from '../services/api';
import RestoreModal from '../components/RestoreModal';
import EmptyState from '../components/EmptyState';
import TranslatedError from '../components/TranslatedError';

export default function BackupPage() {
  const { t } = useI18n();
  const navigate = useNavigate();

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(new Set()); // event ids checked for backup
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState([]); // log lines
  const [showRestore, setShowRestore] = useState(false);
  const [error, setError] = useState(null);
  // v0.70d-2b (R11): backup mode toggle. "full" = everything including
  // participants/allocations/responses (true backup/restore). "structure"
  // = event shape only (categories, units, form fields, marks,
  // settings), GDPR-safe template for sharing between organisations.
  // Ported from the deleted AdminLayout modal, which previously owned
  // this state.
  const [mode, setMode] = useState('full');

  useEffect(() => {
    fetch('/api/events/', { headers: { Authorization: `Bearer ${getToken()}` } })
      .then(r => r.json())
      .then(data => { setEvents(Array.isArray(data) ? data : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const toggleAll = () => {
    if (selected.size === events.length) setSelected(new Set());
    else setSelected(new Set(events.map(e => e.id)));
  };

  const toggleEvent = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleDownloadSelected = async () => {
    if (selected.size === 0) return;
    setDownloading(true);
    setDownloadProgress([]);
    setError(null);

    const toDownload = events.filter(e => selected.has(e.id));

    for (const ev of toDownload) {
      setDownloadProgress(p => [...p, t('backup.downloading_event').replace('{name}', ev.name) + '…']);
      try {
        // v0.70d-2b (R11): append ?mode=structure when structure mode
        // is selected. Server-side the filename suffix differentiates
        // the ZIP name too (moimio-backup-<id>-structure.zip).
        const qs = mode === 'structure' ? '?mode=structure' : '';
        const res = await fetch(`/api/events/${ev.id}/export/backup.zip${qs}`, {
          headers: { Authorization: `Bearer ${getToken()}` },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const cd = res.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : `moimio-backup-${ev.id}.zip`;
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
        setDownloadProgress(p => [...p.slice(0, -1), `✓ ${ev.name}`]);
      } catch (err) {
        setDownloadProgress(p => [...p.slice(0, -1), `✗ ${ev.name}: ${err.message}`]);
      }
      // Small delay between downloads so browser doesn't block
      await new Promise(r => setTimeout(r, 400));
    }
    setDownloading(false);
  };


  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-2xl font-bold text-body">{t('nav.setup.export')}</h1>
      </div>

      <TranslatedError err={error} className="text-sm rounded-lg p-3 mb-4" />

      {/* Restore from backup — always visible */}
      <div className="bg-card-solid rounded-xl shadow-sm border border-card p-5 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-heading font-bold text-body text-sm">{t('portability.restore')}</h2>
            <p className="text-xs text-subtle mt-0.5">{t('portability.restore_hint')}</p>
          </div>
          <button onClick={() => setShowRestore(true)}
            className="border border-card text-muted text-xs font-semibold px-4 py-2 rounded-lg hover:border-steel-blue hover:text-accent whitespace-nowrap transition-colors">
            ↑ {t('portability.restore')}
          </button>
        </div>
      </div>

      {/* Multi-event backup */}
      <div className="bg-card-solid rounded-xl shadow-sm border border-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-heading font-bold text-body text-sm">{t('backup.download_events')}</h2>
            <p className="text-xs text-subtle mt-0.5">{t('backup.download_events.hint')}</p>
          </div>
          {events.length > 0 && (
            <button onClick={toggleAll}
              className="text-xs text-accent hover:opacity-80 font-medium">
              {selected.size === events.length ? t('backup.deselect_all') : t('backup.select_all')}
            </button>
          )}
        </div>

        {loading ? (
          <p className="text-sm text-subtle">{t('common.loading')}</p>
        ) : events.length === 0 ? (
          <EmptyState
            compact
            title={t('backup.no_events.title')}
            hint={t('backup.no_events.hint')}
          />
        ) : (
          <div className="space-y-1.5 mb-4">
            {events.map(ev => (
              <label key={ev.id} className="flex items-center gap-3 p-3 rounded-lg border border-card hover:bg-neutral-tint cursor-pointer transition-colors">
                <input type="checkbox" checked={selected.has(ev.id)} onChange={() => toggleEvent(ev.id)}
                  className="h-4 w-4 rounded text-accent" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-body truncate">{ev.name}</p>
                  <p className="text-[10px] text-subtle">{ev.status} · {ev.start_date || t('backup.no_date')}</p>
                </div>
              </label>
            ))}
          </div>
        )}

        {/* Download progress log */}
        {downloadProgress.length > 0 && (
          <div className="bg-neutral-tint rounded-lg p-3 mb-3 space-y-0.5">
            {downloadProgress.map((line, i) => (
              <p key={i} className={`text-xs font-mono ${line.startsWith('✓') ? 'text-accent' : line.startsWith('✗') ? 'text-alert' : 'text-muted'}`}>{line}</p>
            ))}
          </div>
        )}

        {/* v0.70d-2b (R11): backup mode selector, ported from the
            deleted AdminLayout modal. "Full" is the historical behaviour
            — every participant and allocation, for true backup/restore.
            "Structure" is GDPR-safe — event shape only, no PII. Share a
            structure backup with another organisation as a template
            without leaking personal data. */}
        {events.length > 0 && (
          <div className="bg-neutral-tint rounded-lg p-3 mb-3">
            <p className="text-[11px] font-semibold text-body mb-2">
              {t('backup.mode.label')}
            </p>
            <div className="space-y-1.5">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="backup-mode"
                  value="full"
                  checked={mode === 'full'}
                  onChange={() => setMode('full')}
                  className="mt-0.5 h-3.5 w-3.5 text-accent"
                />
                <div className="flex-1">
                  <p className="text-xs font-medium text-body">
                    {t('backup.mode.full')}
                  </p>
                  <p className="text-[10px] text-subtle">
                    {t('backup.mode.full.hint')}
                  </p>
                </div>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="backup-mode"
                  value="structure"
                  checked={mode === 'structure'}
                  onChange={() => setMode('structure')}
                  className="mt-0.5 h-3.5 w-3.5 text-accent"
                />
                <div className="flex-1">
                  <p className="text-xs font-medium text-body">
                    {t('backup.mode.structure')}
                  </p>
                  <p className="text-[10px] text-subtle">
                    {t('backup.mode.structure.hint')}
                  </p>
                </div>
              </label>
            </div>
          </div>
        )}

        <button
          onClick={handleDownloadSelected}
          disabled={selected.size === 0 || downloading}
          className="w-full py-2.5 rounded-xl bg-steel-blue text-white text-xs font-semibold hover:bg-mid-navy transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
          {downloading
            ? t('backup.downloading')
            : t('backup.download_selected').replace('{n}', selected.size)}
        </button>
      </div>

      {showRestore && (
        <RestoreModal
          onClose={() => setShowRestore(false)}
          onDone={() => { setShowRestore(false); navigate('/admin'); }}
        />
      )}
    </div>
  );
}
