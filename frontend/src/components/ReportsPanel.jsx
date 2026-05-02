import { useState, useEffect } from 'react';
import { events as eventsApi, getToken } from '../services/api';
import { formatErrorMessage } from '../services/api';
import { useI18n } from '../hooks/useI18n';

import ErrorBanner from './ErrorBanner';
/**
 * ReportsPanel — aggregate reporting surface for an event (v0.50g).
 *
 * Three at-a-glance tiles (registration / allocation progress / check-in)
 * plus a per-category roster download list. Each category card exposes
 * one-click downloads for the "compact" and "sign-in" PDF formats. The
 * "detailed" format (PII) lives elsewhere — it's gated on people:read
 * and belongs to the allocation board, not here.
 *
 * Access:
 *   - Admin: full
 *   - Staff with reports:read: full (this page is the primary reason to
 *     grant that permission)
 *   - Others: caller (AdminLayout/EventDetailPage) should not route here
 *
 * Props:
 *   eventId   — UUID
 *   eventName — human name, used in downloaded PDF filenames
 *   phase     — current event phase ('setup' | 'registration' | 'event')
 *               Used to gate the check-in tile (only meaningful in event).
 */
export default function ReportsPanel({ eventId, eventName, phase }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  // v0.50g-1: two separate error states.
  //   statsError: fatal — /stats fetch failed, page can't render meaningfully
  //   downloadError: non-fatal — a PDF download failed (e.g. empty category);
  //                  shown as a dismissable banner above the roster list so
  //                  the user stays oriented and can try a different roster
  const [statsError, setStatsError] = useState(null);
  const [downloadError, setDownloadError] = useState(null);
  const [downloadingKey, setDownloadingKey] = useState(null); // "<catId>:<format>"
  // v0.50k: optional cover page toggle. Default OFF — most organisers
  // print many copies and the cover would waste paper. Turn on when
  // handing over to a sponsor, stakeholder, or for handover archives.
  const [includeCoverPage, setIncludeCoverPage] = useState(false);
  const { t, lang } = useI18n();
  // v0.50o: PDF output language, independent of UI language. Defaults
  // to the current UI lang so a German user's first-time download is
  // automatically in German. Override when exporting for staff who
  // speak a different language. Scope: session-level — the selector
  // resets on each page load rather than persisting, because most
  // organisers will export several PDFs in the same language in one
  // sitting and a sticky setting from yesterday is more confusing
  // than helpful.
  const [pdfLang, setPdfLang] = useState(lang);
  // If the user changes their UI language while on this page, track
  // that as the new PDF default (mirrors the "match UI language" rule).
  useEffect(() => { setPdfLang(lang); }, [lang]);

  const PDF_LANG_OPTIONS = [
    { code: 'en',    label: 'English' },
    { code: 'de',    label: 'Deutsch' },
    { code: 'ko',    label: '한국어' },
    { code: 'es',    label: 'Español' },
    { code: 'pt-BR', label: 'Português (BR)' },
    { code: 'fr',    label: 'Français' },
  ];

  useEffect(() => {
    let alive = true;
    setLoading(true);
    eventsApi.stats(eventId)
      .then(data => { if (alive) { setStats(data); setStatsError(null); } })
      .catch(err => { if (alive) setStatsError(err); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [eventId]);

  const showCheckin = phase === 'event';
  const empty = stats && stats.registration.total_active === 0 && stats.allocation.category_count === 0;

  // v0.50g-1: build a filename like `asdfadsf_small_groups_compact_2026-04-18_en.pdf`.
  // Slugs are lowercased with non-alphanumerics collapsed to underscores so
  // they're safe on all filesystems. Date is ISO (browser local) so files
  // sort chronologically in Downloads folders.
  // v0.50o: language code appended as the last element so the same roster
  // exported in multiple languages saves as distinct files side by side.
  const buildPdfFilename = (categoryName, format) => {
    const slug = (s) => (s || 'untitled')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    const today = new Date();
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    const parts = [slug(eventName), slug(categoryName), format, dateStr, slug(pdfLang)].filter(Boolean);
    return `${parts.join('_')}.pdf`;
  };

  const downloadPdf = async (categoryId, categoryName, format) => {
    const key = `${categoryId}:${format}`;
    setDownloadingKey(key);
    setDownloadError(null);
    try {
      const params = new URLSearchParams({ format });
      if (includeCoverPage) params.set('with_cover', 'true');
      // v0.50o: pass the chosen PDF language to the server so the
      // rendered strings (column headers, cover labels, "NEEDS
      // ALLOCATION" banner, footer page counter, etc.) come back in
      // the target language rather than English.
      params.set('lang', pdfLang);
      const url = `/api/events/${eventId}/export/category/${categoryId}/pdf?${params.toString()}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
      if (!res.ok) {
        // v0.70d-3c-8a: backend now returns dict-detail
        // {key, params} for translatable errors (M5 architecture).
        // Extract i18nKey/i18nParams so the catch handler's
        // formatErrorMessage call can render a translated message
        // instead of a stringified [object Object]. Fall back to
        // friendlyKey from status when no dict-detail available.
        const j = await res.json().catch(() => null);
        const httpErr = new Error(`HTTP ${res.status}`);
        httpErr.status = res.status;
        if (j?.detail && typeof j.detail === 'object' && typeof j.detail.key === 'string') {
          httpErr.i18nKey = j.detail.key;
          if (j.detail.params) httpErr.i18nParams = j.detail.params;
        } else if (typeof j?.detail === 'string') {
          httpErr.message = j.detail;
        }
        if (res.status === 401) httpErr.friendlyKey = 'errors.unauthorised';
        else if (res.status === 403) httpErr.friendlyKey = 'errors.forbidden';
        else if (res.status === 404) httpErr.friendlyKey = 'errors.not_found';
        else if (res.status === 422) httpErr.friendlyKey = 'errors.validation';
        else if (res.status >= 500) httpErr.friendlyKey = 'errors.server';
        throw httpErr;
      }
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = buildPdfFilename(categoryName, format);
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setDownloadError(err);
    } finally {
      setDownloadingKey(null);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-10 text-sm" style={{ color: 'var(--text-subtle)' }}>
        {t('common.loading')}
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="max-w-3xl">
        <ErrorBanner className="text-xs rounded-card p-3">
          {formatErrorMessage(statsError, t).primary}
        </ErrorBanner>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h3 className="font-heading font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
          {t('reports.title')}
        </h3>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
          {t('reports.subtitle')}
        </p>
      </div>

      {empty ? (
        <div
          className="card-surface-solid rounded-2xl p-8 text-center"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {t('reports.empty')}
          </p>
        </div>
      ) : (
        <>
          {/* ─── At-a-glance tiles ─── */}
          <div
            className="grid gap-3"
            style={{ gridTemplateColumns: showCheckin ? '1fr 1fr 1fr' : '1fr 1fr' }}
          >
            {/* Registration tile */}
            <div
              className="card-surface-solid rounded-2xl p-4"
              style={{ border: '1px solid var(--card-border)' }}
            >
              <p className="text-[10px] uppercase tracking-caps font-semibold mb-2" style={{ color: 'var(--text-subtle)' }}>
                {t('reports.tile.registration')}
              </p>
              <p className="text-2xl font-heading font-bold" style={{ color: 'var(--text-primary)' }}>
                {stats.registration.total_active}
              </p>
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
                {t('reports.tile.registration_detail', {
                  confirmed: stats.registration.confirmed,
                  pending: stats.registration.pending,
                  cancelled: stats.registration.cancelled,
                })}
              </p>
            </div>

            {/* Allocation tile */}
            <div
              className="card-surface-solid rounded-2xl p-4"
              style={{ border: '1px solid var(--card-border)' }}
            >
              <p className="text-[10px] uppercase tracking-caps font-semibold mb-2" style={{ color: 'var(--text-subtle)' }}>
                {t('reports.tile.allocation')}
              </p>
              {/* v0.89 #29: headline = % of registered participants
                  allocated in at least one group. The meaningful "are
                  we done with allocations?" question. Subtitle shows
                  the raw counts. */}
              <p className="text-2xl font-heading font-bold" style={{ color: 'var(--text-primary)' }}>
                {(stats.allocation.coverage_percent ?? 0)}%
              </p>
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
                {t('reports.tile.allocation_detail', {
                  placed: stats.allocation.participants_placed ?? 0,
                  total: stats.allocation.participants_total ?? 0,
                })}
              </p>
            </div>

            {/* Check-in tile — only in event/post_event phases */}
            {showCheckin && (
              <div
                className="card-surface-solid rounded-2xl p-4"
                style={{ border: '1px solid var(--card-border)' }}
              >
                <p className="text-[10px] uppercase tracking-caps font-semibold mb-2" style={{ color: 'var(--text-subtle)' }}>
                  {t('reports.tile.checkin')}
                </p>
                <p className="text-2xl font-heading font-bold" style={{ color: 'var(--text-primary)' }}>
                  {stats.checkin.percent}%
                </p>
                <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
                  {t('reports.tile.checkin_detail', {
                    checked_in: stats.checkin.checked_in,
                    total: stats.registration.total_active,
                  })}
                </p>
              </div>
            )}
          </div>

          {/* ─── Per-category roster downloads ─── */}
          <div>
            <h4 className="font-heading font-bold text-sm mb-2" style={{ color: 'var(--text-primary)' }}>
              {t('reports.rosters.title')}
            </h4>
            <p className="text-xs mb-3" style={{ color: 'var(--text-subtle)' }}>
              {t('reports.rosters.hint')}
            </p>

            {/* v0.50g-1: inline dismissable banner for download errors (e.g.
                trying to print a roster for a category with no allocations
                yet). Keeps the rest of the page intact — previously this
                took over the whole panel and stranded the user. */}
            {downloadError && (
              <ErrorBanner className="text-xs rounded-card p-3 mb-3 flex items-start gap-2">
                <div className="flex-1">{formatErrorMessage(downloadError, t).primary}</div>
                <button
                  onClick={() => setDownloadError(null)}
                  className="shrink-0 hover:opacity-70 font-bold"
                  aria-label={t('common.dismiss')}
                >
                  ✕
                </button>
              </ErrorBanner>
            )}

            {stats.allocation.per_category.length === 0 ? (
              <div
                className="card-surface-solid rounded-2xl p-4 text-center text-xs"
                style={{ border: '1px solid var(--card-border)', color: 'var(--text-subtle)' }}
              >
                {t('reports.rosters.none')}
              </div>
            ) : (
              <>
                {/* v0.50o: PDF language selector. Applies to all downloads
                    on this page for the duration of the session. Default
                    matches the current UI language, override when exporting
                    for staff who read a different language. */}
                <div
                  className="card-surface-solid rounded-2xl px-4 py-3 mb-3 flex items-center gap-3 flex-wrap"
                  style={{ border: '1px solid var(--card-border)' }}
                >
                  <label
                    className="text-xs font-semibold"
                    style={{ color: 'var(--text-primary)' }}
                    htmlFor="pdf-lang-select"
                  >
                    {t('reports.pdf_language')}
                  </label>
                  <select
                    id="pdf-lang-select"
                    value={pdfLang}
                    onChange={e => setPdfLang(e.target.value)}
                    className="text-xs rounded-card px-2 py-1 border bg-transparent"
                    style={{
                      borderColor: 'var(--card-border)',
                      color: 'var(--text-primary)',
                    }}
                  >
                    {PDF_LANG_OPTIONS.map(opt => (
                      <option key={opt.code} value={opt.code}>{opt.label}</option>
                    ))}
                  </select>
                  <span className="text-[11px] flex-1 min-w-0" style={{ color: 'var(--text-subtle)' }}>
                    {t('reports.pdf_language.hint')}
                  </span>
                </div>

                {/* v0.50k: cover-page toggle applied to all downloads in this list. */}
                <label
                  className="flex items-start gap-2 mb-2 text-xs cursor-pointer select-none"
                  style={{ color: 'var(--text-muted)' }}
                >
                  <input
                    type="checkbox"
                    checked={includeCoverPage}
                    onChange={e => setIncludeCoverPage(e.target.checked)}
                    className="mt-0.5 h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold"
                  />
                  <span>
                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {t('export.pdf.cover.label')}
                    </span>
                    {' — '}
                    {t('export.pdf.cover.hint_inline')}
                  </span>
                </label>
                <div className="space-y-2">
                  {stats.allocation.per_category.map(cat => {
                  const compactKey = `${cat.id}:compact`;
                  const signinKey = `${cat.id}:signin`;
                  return (
                    <div
                      key={cat.id}
                      className="card-surface-solid rounded-2xl px-4 py-3 flex items-center gap-3"
                      style={{ border: '1px solid var(--card-border)' }}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {cat.name}
                        </p>
                        <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                          {/* v0.89 #29: simpler per-category metric —
                              units + % of participants allocated in
                              this specific category. Reads consistently
                              with the headline tile above. */}
                          {t('reports.rosters.category_detail', {
                            units: cat.unit_count,
                            percent: cat.coverage_percent ?? 0,
                          })}
                        </p>
                      </div>
                      <button
                        onClick={() => downloadPdf(cat.id, cat.name, 'compact')}
                        disabled={downloadingKey === compactKey}
                        className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50 shrink-0"
                        style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
                      >
                        {downloadingKey === compactKey
                          ? (t('common.loading'))
                          : (t('reports.rosters.compact'))}
                      </button>
                      <button
                        onClick={() => downloadPdf(cat.id, cat.name, 'signin')}
                        disabled={downloadingKey === signinKey}
                        className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50 shrink-0"
                        style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
                      >
                        {downloadingKey === signinKey
                          ? (t('common.loading'))
                          : (t('reports.rosters.signin'))}
                      </button>
                    </div>
                  );
                })}
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
