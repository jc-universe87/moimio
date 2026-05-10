import { useEffect, useState } from 'react';
import {
  notes as notesApi,
  preferenceRequests as prefApi,
  customFields as cfApi,
  allocations as allocApi,
  allocationCategories as catApi,
  getToken,
} from '../services/api';
import { useI18n } from '../hooks/useI18n';
import { useDateFormat } from '../hooks/useDateFormat';
import { useToast } from '../hooks/useToast';
import { downloadParticipantDataExport } from '../utils/downloadParticipantDataExport';
import MarkDots from './MarkDots';
import AllocationHistory from './AllocationHistory';
import GroupCodeTooltip from './GroupCodeTooltip';

/**
 * InsightPanel — slide-out (desktop) / bottom sheet (mobile) showing a
 * participant's full profile from the allocation board.
 *
 * v0.58e: closes §6.2.2 of the design overhaul. The organiser taps an info
 * icon on a participant card anywhere on the board (pool or group column)
 * and the panel slides in.
 *
 * Self-contained: fetches its own supplementary data (notes, preferences,
 * custom field defs, all allocations across categories) when opened.
 * Parent only needs to hand it the participant + eventId + marks.
 *
 * Layout:
 *   Desktop (>= md): fixed right edge, 400px wide.
 *   Mobile: bottom sheet, 90vh max.
 *
 * Props:
 *   participant      — participant object (from participantList), or null to hide
 *   eventId          — required when participant is present
 *   marksForPerson   — array of mark defs assigned to this participant (from useMarks)
 *   isAdmin          — v0.60b: gates the allocation history section
 *   participants     — v1.0.0e: full event participant list (used by
 *                      GroupCodeTooltip to compute clustermates).
 *                      Optional; the tooltip silently degrades to a
 *                      no-op when missing (e.g. legacy callers).
 *   onClose          — () => void
 */
export default function InsightPanel({ participant, eventId, marksForPerson = [], isAdmin = false, participants = null, onClose }) {
  const { t, lang } = useI18n();
  const { formatDate } = useDateFormat();
  const { showToast, ToastHost } = useToast();
  const [notes, setNotes] = useState([]);
  const [prefRequests, setPrefRequests] = useState([]);
  const [customFieldDefs, setCustomFieldDefs] = useState([]);
  const [allAllocations, setAllAllocations] = useState({}); // { catId: { unitId: [{participant_id, ...}] } }
  const [unitsById, setUnitsById] = useState({}); // { unitId: { id, name, category_id, ... } }
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  // v0.73: per-click busy flag for the data-export button. Disables
  // re-clicks while the fetch is in flight; resets on completion or
  // error. Reset when the panel closes (participant prop change).
  const [exporting, setExporting] = useState(false);
  const [isMobileView, setIsMobileView] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < 768
  );

  useEffect(() => { setExporting(false); }, [participant?.id]);

  // v0.73: data export trigger. Admin-only path; the button is also
  // gated by isAdmin so this handler should never fire as a non-admin.
  // Defence in depth — the backend rejects non-admins via
  // ensure_event_admin regardless.
  const handleExport = async () => {
    if (!participant || !eventId || exporting) return;
    setExporting(true);
    try {
      await downloadParticipantDataExport({
        eventId,
        participantId: participant.id,
        token: getToken(),
      });
      showToast(
        t('people.export.success', { name: `${participant.first_name} ${participant.last_name}` }),
        'success'
      );
    } catch (err) {
      // The helper sets friendlyKey + i18nKey on its thrown errors
      // so showToast/formatErrorMessage can render a localised line.
      // Fallback to the static error key if neither is available.
      const fallbackErr = err?.i18nKey || err?.friendlyKey ? err : new Error(t('people.export.error'));
      showToast(fallbackErr, 'error');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    const onResize = () => setIsMobileView(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Fetch supplementary data when panel opens
  useEffect(() => {
    if (!participant || !eventId) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      notesApi.list('participant', participant.id).catch(() => []),
      prefApi.list(eventId).catch(() => []),
      cfApi.list(eventId).catch(() => []),
      allocApi.all(eventId).catch(() => ({})),
      catApi.list(eventId).catch(() => []),
    ]).then(async ([pNotes, allPrefReqs, cfDefs, allAllocs, cats]) => {
      if (cancelled) return;
      setNotes(pNotes || []);
      const myPrefReqs = (allPrefReqs || []).filter(pr =>
        String(pr.participant_id) === String(participant.id) ||
        String(pr.preferred_participant_id || '') === String(participant.id)
      );
      setPrefRequests(myPrefReqs);
      setCustomFieldDefs(cfDefs || []);
      setAllAllocations(allAllocs || {});
      setCategories(cats || []);
      // v0.58e-1: Fetch units for every category in parallel so the
      // allocations section can show human-readable unit names instead
      // of UUIDs. The allocations/all endpoint returns
      // {category_id: {unit_id: [members]}} with no unit names inline,
      // so we need a separate lookup.
      try {
        const unitLists = await Promise.all(
          (cats || []).map(c =>
            fetch(`/api/events/${eventId}/allocation-categories/${c.id}/units/`, {
              headers: { Authorization: `Bearer ${getToken() || ''}` },
            })
              .then(r => r.ok ? r.json() : [])
              .catch(() => [])
          )
        );
        if (cancelled) return;
        const map = {};
        unitLists.flat().forEach(u => {
          if (u && u.id) map[String(u.id)] = u;
        });
        setUnitsById(map);
      } catch { /* ignore, fall back to showing UUIDs */ }
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [participant, eventId]);

  // Close on Escape
  useEffect(() => {
    if (!participant) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [participant, onClose]);

  if (!participant) return null;

  // v0.58e-1: Derive this participant's allocations from correctly-shaped
  // self-fetched data. Shape: { catId: { unitId: [{participant_id, ...}] } }
  const myAllocations = [];
  for (const [catId, unitsMap] of Object.entries(allAllocations || {})) {
    if (!unitsMap || typeof unitsMap !== 'object') continue;
    for (const [unitId, members] of Object.entries(unitsMap)) {
      if (!Array.isArray(members)) continue;
      const hit = members.some(m => {
        const pid = typeof m === 'object' ? m.participant_id : m;
        return String(pid) === String(participant.id);
      });
      if (!hit) continue;
      const unit = unitsById[String(unitId)];
      const cat = categories.find(c => String(c.id) === String(catId));
      myAllocations.push({
        unitName: (unit && unit.name) || unitId,
        categoryName: (cat && cat.name) || '—',
      });
    }
  }

  // Panel + backdrop styles
  const panelStyle = isMobileView
    ? {
        position: 'fixed',
        left: 0,
        right: 0,
        bottom: 0,
        maxHeight: '90vh',
        background: 'var(--card-bg-solid)',
        borderTopLeftRadius: '20px',
        borderTopRightRadius: '20px',
        boxShadow: '0 -8px 28px rgba(0,0,0,0.18)',
        zIndex: 60,
        display: 'flex',
        flexDirection: 'column',
      }
    : {
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '400px',
        background: 'var(--card-bg-solid)',
        boxShadow: '-8px 0 28px rgba(0,0,0,0.12)',
        zIndex: 60,
        display: 'flex',
        flexDirection: 'column',
      };

  const Row = ({ label, children }) => (
    <div className="flex gap-3 text-xs py-1">
      <span className="w-24 shrink-0" style={{ color: 'var(--text-subtle)' }}>{label}</span>
      <span className="flex-1 break-words" style={{ color: 'var(--text-primary)' }}>{children}</span>
    </div>
  );

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30"
        style={{ zIndex: 59 }}
        onClick={onClose}
      />

      <aside style={panelStyle} role="dialog" aria-modal="true" aria-label={t('insight.title')}>
        {/* Drag handle on mobile */}
        {isMobileView && (
          <div className="flex justify-center pt-2 pb-1">
            <div className="w-10 h-1 rounded-full" style={{ background: 'var(--card-border)' }} />
          </div>
        )}

        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-3 shrink-0"
          style={{ borderBottom: '1px solid var(--card-border)' }}>
          <div className="min-w-0 flex items-center gap-2">
            <h2 className="font-heading font-bold text-base truncate" style={{ color: 'var(--text-primary)' }}>
              {participant.first_name} {participant.last_name}
            </h2>
            {marksForPerson.length > 0 && (
              <MarkDots marksForParticipant={marksForPerson} />
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-2">
            {isAdmin && (
              <button
                onClick={handleExport}
                disabled={exporting}
                title={t('people.export.cta.hint')}
                aria-label={t('people.export.cta')}
                className="text-xs font-semibold px-2.5 py-1 rounded-md border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
                style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
                {exporting ? <span className="animate-spin inline-block">⟳</span> : '↓'} {t('people.export.cta')}
              </button>
            )}
            <button
              onClick={onClose}
              aria-label={t('common.close')}
              className="text-xl hover:opacity-70"
              style={{ color: 'var(--text-subtle)' }}>
              ✕
            </button>
          </div>
        </div>

        <ToastHost />

        {/* Scrollable body — v0.59a: bottom padding respects iOS
            safe-area-inset so the last item clears the home bar on
            mobile (panel reaches viewport bottom). Inset is 0 on
            desktop/non-notched devices, so unconditional is fine. */}
        <div className="overflow-y-auto flex-1 px-5 pt-4 pb-[calc(1rem+env(safe-area-inset-bottom))] space-y-4">
          {/* Contact */}
          <section>
            <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('insight.contact')}
            </h3>
            <Row label={t('register.email')}>{participant.email}</Row>
            {participant.phone && <Row label={t('people.col.phone')}>{participant.phone}</Row>}
            {participant.country && <Row label={t('people.col.country')}>{participant.country}</Row>}
            {participant.church_organisation && (
              <Row label={t('people.col.church')}>{participant.church_organisation}</Row>
            )}
          </section>

          {/* Registration meta */}
          <section>
            <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('insight.registration')}
            </h3>
            {participant.participant_number != null && (
              <Row label={t('people.col.participant_number')}>
                #{String(participant.participant_number).padStart(3, '0')}
              </Row>
            )}
            {participant.group_code && (
              <Row label={t('people.col.group_code')}>
                <GroupCodeTooltip
                  code={participant.group_code}
                  participants={participants}
                  selfId={participant.id}
                  t={t}
                  lang={lang}
                >
                  <span className="font-mono text-xs cursor-help">{participant.group_code}</span>
                </GroupCodeTooltip>
              </Row>
            )}
            {participant.gender && (
              <Row label={t('people.col.gender')}>
                {participant.gender === 'male' ? t('people.gender.male') : t('people.gender.female')}
              </Row>
            )}
            {participant.date_of_birth && (
              <Row label={t('people.col.dob')}>
                {formatDate(participant.date_of_birth)}
              </Row>
            )}
            {participant.created_at && (
              <Row label={t('people.col.registered_at')}>
                {formatDate(participant.created_at)}
              </Row>
            )}
            {participant.registration_status && participant.registration_status !== 'confirmed' && (
              <Row label={t('insight.status')}>
                <span style={{ color: 'var(--text-muted)' }}>{participant.registration_status}</span>
              </Row>
            )}
          </section>

          {/* Current allocations */}
          <section>
            <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('insight.allocations')}
            </h3>
            {myAllocations.length > 0 ? (
              <ul className="space-y-1">
                {myAllocations.map((a, i) => (
                  <li key={i} className="flex gap-3 text-xs">
                    <span className="w-24 shrink-0" style={{ color: 'var(--text-subtle)' }}>{a.categoryName}</span>
                    <span style={{ color: 'var(--text-primary)' }}>{a.unitName}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs italic" style={{ color: 'var(--text-subtle)' }}>
                {t('insight.no_allocations')}
              </p>
            )}
          </section>

          {/* Preference requests */}
          {prefRequests.length > 0 && (
            <section>
              <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
                style={{ color: 'var(--text-subtle)' }}>
                {t('insight.preferences')}
              </h3>
              <ul className="space-y-2">
                {prefRequests.map((pr, i) => (
                  <li key={pr.id || i} className="text-xs" style={{ color: 'var(--text-primary)' }}>
                    <p style={{ color: 'var(--text-subtle)' }}>
                      {t('prefs.wants_to_be_with')}
                    </p>
                    <div className="mt-1 rounded-card p-2 space-y-0.5"
                      style={{ background: 'var(--app-bg)' }}>
                      {pr.preferred_participant_number != null && (
                        <p className="font-mono font-bold text-[11px]"
                          style={{ color: 'var(--io-accent)' }}>
                          #{String(pr.preferred_participant_number).padStart(3, '0')}
                        </p>
                      )}
                      {pr.preferred_name && (
                        <p className="font-semibold">{pr.preferred_name}</p>
                      )}
                      {pr.preferred_details && (
                        <p className="italic" style={{ color: 'var(--text-muted)' }}>
                          {pr.preferred_details}
                        </p>
                      )}
                      {pr.resolved && (
                        <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
                          ✓ {t('prefs.resolved')}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Custom fields */}
          {customFieldDefs.length > 0 && participant.custom_fields && Object.keys(participant.custom_fields).length > 0 && (
            <section>
              <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
                style={{ color: 'var(--text-subtle)' }}>
                {t('insight.custom_fields')}
              </h3>
              {customFieldDefs.map(def => {
                const val = participant.custom_fields?.[def.id];
                if (val === undefined || val === null || val === '') return null;
                return <Row key={def.id} label={def.label}>{String(val)}</Row>;
              })}
            </section>
          )}

          {/* Message */}
          {participant.message && (
            <section>
              <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
                style={{ color: 'var(--text-subtle)' }}>
                {t('people.col.message')}
              </h3>
              <p className="text-xs whitespace-pre-wrap" style={{ color: 'var(--text-primary)' }}>
                {participant.message}
              </p>
            </section>
          )}

          {/* Notes */}
          <section>
            <h3 className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('insight.notes')} {notes.length > 0 && <span className="font-normal normal-case" style={{ color: 'var(--text-subtle)' }}>({notes.length})</span>}
            </h3>
            {loading ? (
              <p className="text-xs italic" style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>
            ) : notes.length > 0 ? (
              <ul className="space-y-2">
                {notes.map(n => (
                  <li key={n.id} className="text-xs" style={{ color: 'var(--text-primary)' }}>
                    <span className="whitespace-pre-wrap">{n.body}</span>
                    {n.created_at && (
                      <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                        {formatDate(n.created_at)}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs italic" style={{ color: 'var(--text-subtle)' }}>
                {t('insight.no_notes')}
              </p>
            )}
          </section>

          {/* v0.60b: allocation history — admin only, silently hidden
              when the participant has no history so the panel doesn't
              clutter for fresh registrations. */}
          {participant && (
            <AllocationHistory
              eventId={eventId}
              participantId={participant.id}
              isAdmin={isAdmin}
            />
          )}
        </div>
      </aside>
    </>
  );
}
