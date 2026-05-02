/**
 * SetupHub — landing page for an event in Setup phase (§4.1).
 *
 * v50b-3 redesign: one action per card.
 *   - Details card: "Save & confirm" saves event fields AND flips confirmed.
 *     Empty dates are normalised to null server-side (was: bug sent "" → 400).
 *   - Registration card: "Save & confirm" confirms the card. The inner
 *     FormConfigPanel handles its own field saves (different action, kept).
 *   - Group types / Marks / Staff: no confirm button (not gates).
 *
 * v0.70d-2a (R5): Registration card previously used "Mark as configured"
 * here — two different verbs for the same gesture. Both cards now use
 * the default "Save & confirm" label from SetupCard for consistency.
 */

import { useEffect, useRef, useState } from 'react';
import { formatErrorMessage } from '../services/api';
import { useParams, useNavigate } from 'react-router-dom';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';
import {
  events as eventsApi,
  allocationCategories,
  marks as marksApi,
  eventAssignments as assignmentsApi,
  getToken,
} from '../services/api';
import { useAuth, getRoleForEvent } from '../hooks/useAuth';
import { useI18n } from '../hooks/useI18n';
import { useEventPhase } from '../hooks/useEventPhase';
import { useDateFormat } from '../hooks/useDateFormat';
import { EVENT_STATUS_COLORS } from '../services/display';

import PhaseStrip from '../components/PhaseStrip';
import SetupCard from '../components/SetupCard';
import DetailsEditor, { detailsFormToPatch } from '../components/DetailsEditor';
import FormConfigPanel from '../components/FormConfigPanel';
import SharePanel from '../components/SharePanel';
import MarksPanel from '../components/MarksPanel';
import GroupTypesEditor from '../components/GroupTypesEditor';
import EventAssignmentsPanel from '../components/EventAssignmentsPanel';
import EventAdminWelcome from '../components/EventAdminWelcome';
import StrongDeleteConfirm from '../components/StrongDeleteConfirm';

export default function SetupHub({ onEventChange }) {
  const { eventId } = useParams();
  const { user, staffContext } = useAuth();
  const { t } = useI18n();
  const { formatDate } = useDateFormat();
  // v0.50j: per-event admin check. Super Admin or per-event assignment
  // role=event_admin. Setup hub is the admin-facing config page for an
  // event, so per-event gating is correct here.
  const isAdmin = user?.role === 'super_admin'
    || getRoleForEvent(staffContext, eventId) === 'event_admin';

  const [event, setEventState] = useState(null);

  // Wrap setEvent so updates propagate to the parent EventDetailPage.
  // That's what triggers phase-based re-routing once we open registration.
  // Also broadcasts a window event so AdminLayout refetches its own copy
  // of the event (for phase-conditional sidebar nav).
  const setEvent = (next) => {
    setEventState(next);
    if (onEventChange) onEventChange(next);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('moimio:event-changed'));
    }
  };

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Details form — draft state, controlled from here so the card's footer
  // button can read it and save.
  const [detailsForm, setDetailsForm] = useState({
    name: '', description: '', location: '',
    timezone: 'UTC', start_date: '', end_date: '',
  });
  const [detailsSaving, setDetailsSaving] = useState(false);
  const [detailsError, setDetailsError] = useState(null);

  // Registration confirm state (field saves happen inside FormConfigPanel).
  const [regSaving, setRegSaving] = useState(false);
  const [regError, setRegError] = useState(null);

  // Summary data for card one-liners
  const [categories, setCategories] = useState([]);
  const [marksDefs, setMarksDefs] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [enabledFieldCount, setEnabledFieldCount] = useState(0);

  const [openCard, setOpenCard] = useState(null);

  // v0.70d-2e-1 (S5): when a brand-new event arrives via the
  // EventsPage name-only create flow, the Details card carries
  // empty description / location / dates and is unconfirmed —
  // open it automatically so the organiser fills it once.
  // useRef gate ensures we only auto-open once per mount: if the
  // user manually closes the Details card we don't reopen it on
  // the next event reload (which fires after every confirm /
  // unconfirm / open-registration). This will be generalised in
  // 2e-2 (S6) to "first unconfirmed required card on load" — for
  // now scoped narrowly to the S5 new-event fingerprint.
  const autoOpenedRef = useRef(false);

  const [opening, setOpening] = useState(false);
  const [openError, setOpenError] = useState(null);

  // v0.50m: danger zone lives on the Setup Hub now too, so Super Admins can
  // undo an accidentally-created event without having to wait until the
  // Registration/Event phase exposes the More menu.
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [archiveError, setArchiveError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  // v0.70d-2d-2 (S4): Danger Zone collapsed by default. The audit
  // observed it competing with — and in dark mode louder than — the
  // primary "Open registration" CTA. Danger Zone is rare-use recovery,
  // not the page's primary affordance, so it now lives behind a
  // summary row that expands on click. Content stays available; visual
  // hierarchy corrects itself.
  const [showDanger, setShowDanger] = useState(false);
  const navigate = useNavigate();

  const { phase, canOpenReg } = useEventPhase(event);
  const prefersReducedMotion = usePrefersReducedMotion();

  // v0.70d-2e-2 (S3 Q2 composed transition): when the gate card
  // transitions from "not ready" to "ready", briefly flash it
  // (fade-in + scale 1.0 → 1.02 → 1.0 over 400ms ease-out-quint).
  // Settles to static after the one transition.
  //
  // We track the previous canOpenReg value via useRef so we fire
  // ONLY on positive transitions (false → true). Negative
  // transitions (super-admin un-confirms a card → canOpenReg
  // becomes false again) must NOT flash — that would celebrate
  // a regression. Initial mount also doesn't flash (the prev
  // ref is set to whatever canOpenReg started at on mount, so
  // there's no false→true jump on the first effect run).
  //
  // prefersReducedMotion skips the flash entirely — the user's
  // OS-level preference wins. The brighter tint and copy
  // punch-up still apply (those aren't motion).
  const prevCanOpenRef = useRef(canOpenReg);
  const [gateFlashing, setGateFlashing] = useState(false);
  useEffect(() => {
    const prev = prevCanOpenRef.current;
    prevCanOpenRef.current = canOpenReg;
    if (prev === false && canOpenReg === true && !prefersReducedMotion) {
      setGateFlashing(true);
      const timer = setTimeout(() => setGateFlashing(false), 400);
      return () => clearTimeout(timer);
    }
  }, [canOpenReg, prefersReducedMotion]);

  // Whenever the event loads/reloads, hydrate the details draft form.
  useEffect(() => {
    if (!event) return;
    setDetailsForm({
      name: event.name || '',
      description: event.description || '',
      location: event.location || '',
      timezone: event.timezone || 'UTC',
      start_date: event.start_date || '',
      end_date: event.end_date || '',
    });
  }, [event]);

  // v0.70d-2e-2 (S6 c): auto-expand the first unconfirmed required
  // card on first load. Walks the required trio in order:
  //   1. Details (if !details_confirmed → open it)
  //   2. Registration (if !registration_confirmed → open it)
  //   3. Group Types (if categories.length === 0 → open it)
  //   4. Otherwise → leave all closed
  // Generalises 2e-1's narrow new-event fingerprint, which only
  // covered case 1. The `autoOpenedRef` gate is unchanged from 2e-1
  // — fires ONCE per mount. If the user closes the auto-opened card
  // manually before another event reload, we don't reopen.
  // Re-mount (navigate away + back) resets the ref. The "next thing
  // to do" auto-expands again, which is what an organiser coming
  // back the next day expects: they land on what's still open.
  // We require BOTH `event` AND `categories` to be loaded before
  // making the decision — otherwise on a fast first-paint we'd see
  // event populated but categories still [] and incorrectly open
  // Group Types when in fact it has data. Tracked via the
  // `loading` flag from loadData() — once that flips false, all
  // four data sources have settled.
  useEffect(() => {
    if (loading || !event || autoOpenedRef.current) return;
    if (!event.details_confirmed) {
      setOpenCard('details');
    } else if (!event.registration_confirmed) {
      setOpenCard('registration');
    } else if (categories.length === 0) {
      setOpenCard('group_types');
    }
    // else: all required cards are confirmed/populated → leave closed.
    autoOpenedRef.current = true;
  }, [loading, event, categories]);

  const loadData = async () => {
    try {
      const [eventData, cats, marksD, asgs, fields] = await Promise.all([
        eventsApi.get(eventId),
        allocationCategories.list(eventId).catch(() => []),
        marksApi.listDefs(eventId).catch(() => []),
        assignmentsApi.list(eventId).catch(() => []),
        eventsApi.getFields(eventId).catch(() => []),
      ]);
      setEvent(eventData);
      setCategories(cats || []);
      setMarksDefs(marksD || []);
      setAssignments(asgs || []);
      setEnabledFieldCount((fields || []).filter(f => f.is_enabled).length);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [eventId]);

  // ─── Save + confirm combined flow (Details) ───
  const handleDetailsSaveAndConfirm = async () => {
    setDetailsSaving(true); setDetailsError(null);
    try {
      // 1. PATCH event with normalised payload (empty dates → null).
      //    Note: the server will silently un-confirm details_confirmed on
      //    this patch because DETAILS_FIELDS touched. We then explicitly
      //    re-confirm in step 2.
      const patch = detailsFormToPatch(detailsForm);
      await eventsApi.update(eventId, patch);
      // 2. Confirm the card.
      const confirmed = await eventsApi.confirmCard(eventId, 'details');
      setEvent(confirmed);
      setOpenCard(null); // collapse after success
      await loadData();
    } catch (err) {
      setDetailsError(err);
    } finally {
      setDetailsSaving(false);
    }
  };

  const handleDetailsUnconfirm = async () => {
    try {
      const updated = await eventsApi.unconfirmCard(eventId, 'details');
      setEvent(updated);
    } catch (err) {
      setDetailsError(err);
    }
  };

  // ─── Confirm-only flow (Registration) ───
  // Field toggles save via FormConfigPanel's internal "Save" — kept because
  // that's a different action (field-level toggles). This button just
  // confirms the card.
  const handleRegConfirm = async () => {
    setRegSaving(true); setRegError(null);
    try {
      const updated = await eventsApi.confirmCard(eventId, 'registration');
      setEvent(updated);
      setOpenCard(null);
      await loadData();
    } catch (err) {
      setRegError(err);
    } finally {
      setRegSaving(false);
    }
  };

  const handleRegUnconfirm = async () => {
    try {
      const updated = await eventsApi.unconfirmCard(eventId, 'registration');
      setEvent(updated);
    } catch (err) {
      setRegError(err);
    }
  };

  const handleOpenRegistration = async () => {
    setOpening(true); setOpenError(null);
    try {
      const updated = await eventsApi.openRegistration(eventId);
      setEvent(updated);
    } catch (err) {
      setOpenError(err);
    } finally {
      setOpening(false);
    }
  };

  // v0.50m: archive/unarchive from the Setup Hub danger zone. Mirrors the
  // logic that lives on EventDetailPage's danger zone — reversible op, so
  // a plain two-button dialog suffices (no type-to-confirm).
  const handleArchiveToggle = async () => {
    if (!event) return;
    setArchiving(true); setArchiveError(null);
    try {
      const updated = event.is_archived
        ? await eventsApi.unarchive(eventId)
        : await eventsApi.archive(eventId);
      setEvent(updated);
      setShowArchiveConfirm(false);
    } catch (err) {
      setArchiveError(err);
    } finally {
      setArchiving(false);
    }
  };

  // v0.50m: hard-delete from the Setup Hub danger zone. On success we
  // navigate back to the events list because this page no longer has
  // an event to display. Guarded by StrongDeleteConfirm (type-to-confirm).
  const handleDeleteEvent = async () => {
    if (!event) return;
    setDeleting(true); setDeleteError(null);
    try {
      await eventsApi.delete(eventId);
      navigate('/admin/events');
    } catch (err) {
      setDeleteError(err);
      setShowDeleteConfirm(false);
      setDeleting(false);
    }
  };

  // v0.61c-1: backup-before-delete from the Setup-phase danger zone.
  // Same shape as EventDetailPage's handler — surfaced inside the
  // delete-confirm warning so an organiser experimenting in Setup can
  // snapshot before destroying. Setup is arguably the more dangerous
  // delete path because there are no participants yet to give the
  // organiser pause; without this affordance a stub event with
  // already-uploaded marks/group-types could be lost on a careless click.
  const handleBackupBeforeDelete = async () => {
    try {
      const url = `/api/events/${eventId}/export/backup.zip`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
      if (!res.ok) throw new Error('Backup failed');
      const cd = res.headers.get('Content-Disposition') || '';
      const match = cd.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : `moimio-backup-${eventId}.zip`;
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setDeleteError(err);
    }
  };

  if (loading) {
    return <p style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>;
  }
  if (error && !event) {
    const { primary, detail } = formatErrorMessage(error, t);
    return (
      <div className="bg-alert-tint text-alert text-sm rounded-card p-3">
        <p className="font-semibold">{primary}</p>
        {detail && <p className="text-xs opacity-70 mt-1">{detail}</p>}
      </div>
    );
  }
  if (!event) return null;

  // Build summaries
  const detailsSummary = buildDetailsSummary(event, formatDate);
  const registrationSummary = enabledFieldCount > 0
    ? t('setup.registration.summary', { n: enabledFieldCount + 3 })
    : null;
  const groupTypesSummary = categories.length > 0
    ? t('setup.group_types.summary', { n: categories.length })
    : null;
  const marksSummary = marksDefs.length > 0
    ? t('setup.marks.summary', { n: marksDefs.length })
    : null;
  const staffSummary = assignments.length > 0
    ? t('setup.staff.summary', { n: assignments.length })
    : null;

  const toggle = (key) => setOpenCard(prev => (prev === key ? null : key));

  return (
    <div className="max-w-2xl mx-auto">
      {/* v0.50l: reassure a Staff user that they have Event Admin rights on
          an event they created. Shown once per event per browser (dismissal
          stored in localStorage). Super Admins and users viewing events
          they didn't create don't see it. */}
      {user?.role === 'staff'
        && event?.created_by
        && user?.id
        && event.created_by === user.id
        && isAdmin && (
          <EventAdminWelcome eventId={eventId} eventName={event.name} />
        )}

      {/* Event header + phase pill */}
      <header className="mb-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="font-heading font-extrabold text-xl" style={{ color: 'var(--text-primary)' }}>
            {event.name}
          </h1>
          <span className={`pill-status ${EVENT_STATUS_COLORS[event.status] || ''}`}>
            {t('status.' + event.status) || event.status}
          </span>
        </div>
        <h2 className="font-heading font-bold text-lg mt-2" style={{ color: 'var(--text-primary)' }}>
          {t('setup.hub.title')}
        </h2>
        <p className="text-xs mt-1" style={{ color: 'var(--text-subtle)' }}>
          {t('setup.hub.subtitle')}
        </p>
      </header>

      <div className="mb-5">
        <PhaseStrip currentPhase={phase} />
      </div>

      {/* v0.70d-2e-2 (S6 b): three spacing groups in the SetupHub
          card stack:
            1. Required trio (Details, Registration, Group Types) —
               tight space-y-2.5 within the group; this is the
               organiser's primary path
            2. Optional pair (Marks, Staff) — same space-y-2.5
               within, separated from the required trio by pt-5
               break to signal "different category"
            3. Gate card already has its own mt-5 (further down)
          The breaks aren't decorative — they signal the structure
          of the page so the eye lands on the required trio first
          and parses Marks/Staff as supplementary. */}
      <div>
        {/* Required trio */}
        <div className="space-y-2.5">
          <SetupCard
            name={t('setup.details.name')}
            priority="required"
            summary={detailsSummary}
            emptyCopy={t('setup.details.empty')}
            confirmed={event.details_confirmed}
            isOpen={openCard === 'details'}
            onToggleOpen={() => toggle('details')}
            canConfirm
            onSaveAndConfirm={handleDetailsSaveAndConfirm}
            onUnconfirm={handleDetailsUnconfirm}
            saving={detailsSaving}
            saveError={detailsError}
          >
            <DetailsEditor
              form={detailsForm}
              onChange={setDetailsForm}
              isAdmin={isAdmin}
              error={null}
            />
          </SetupCard>

          <SetupCard
            name={t('setup.registration.name')}
            priority="required"
            summary={registrationSummary}
            emptyCopy={t('setup.registration.empty')}
            confirmed={event.registration_confirmed}
            isOpen={openCard === 'registration'}
            onToggleOpen={() => toggle('registration')}
            canConfirm
            onSaveAndConfirm={handleRegConfirm}
            onUnconfirm={handleRegUnconfirm}
            saving={regSaving}
            saveError={regError}
            confirmDisabledReason={categories.length === 0 ? t('setup.group_types.required_gate') : null}
          >
            <div className="space-y-6">
              <FormConfigPanel eventId={eventId} isAdmin={isAdmin} />
              {/* v0.70d-2d-2 (S10): wrap only when SharePanel will actually
                  render content (registration is open). Otherwise we'd
                  show an empty bordered container. */}
              {event?.status === 'open' && (
                <div className="pt-4 border-t" style={{ borderColor: 'var(--card-border)' }}>
                  <SharePanel eventId={eventId} event={event} />
                </div>
              )}
            </div>
          </SetupCard>

          <SetupCard
            name={t('setup.group_types.name')}
            priority="required"
            summary={groupTypesSummary}
            emptyCopy={t('setup.group_types.empty')}
            confirmed={categories.length > 0}
            isOpen={openCard === 'group_types'}
            onToggleOpen={() => toggle('group_types')}
          >
            {/* v0.70d-2b-1 → v0.70d-2c (R4-B): promoted to required. The
                audit's finding was that registration-open events with 0
                group types degrade the allocation engine to a placeholder.
                The "Open registration" button in the Registration card is
                now gated on groupTypesCount > 0 (see below). */}
            <GroupTypesEditor
              eventId={eventId}
              isAdmin={isAdmin}
              onChange={loadData}
            />
          </SetupCard>
        </div>

        {/* Optional pair — separated from required trio */}
        <div className="space-y-2.5 pt-5">
          <SetupCard
            name={t('setup.marks.name')}
            priority="optional"
            summary={marksSummary}
            emptyCopy={t('setup.marks.empty')}
            confirmed={marksDefs.length > 0}
            isOpen={openCard === 'marks'}
            onToggleOpen={() => toggle('marks')}
          >
            <MarksPanel eventId={eventId} isAdmin={isAdmin} embedded onChange={loadData} />
          </SetupCard>

          <SetupCard
            name={t('setup.staff.name')}
            priority="optional"
            summary={staffSummary}
            emptyCopy={t('setup.staff.empty')}
            confirmed={assignments.length > 0}
            isOpen={openCard === 'staff'}
            onToggleOpen={() => toggle('staff')}
          >
            <EventAssignmentsPanel eventId={eventId} isAdmin={isAdmin} onChange={loadData} />
          </SetupCard>
        </div>
      </div>

      {/* Gate card
          v0.70d-2e-2 (S3 Q2): brighter tint when ready (/15 light,
          /30 dark — was /10 and /20). The ready state is louder so
          the eye lands here once it's actionable. Brief flash
          (.gate-flash class) on the false→true transition. Button
          copy upgrades from "Open registration →" to "Ready to open
          registration →" when ready, signalling readiness directly
          rather than displaying a quiet uniform CTA. */}
      <section
        className={`mt-5 rounded-card p-4 flex items-center justify-between gap-4 ${
          canOpenReg ? 'bg-steel-blue/15 dark:bg-steel-blue/30' : ''
        } ${gateFlashing ? 'gate-flash' : ''}`}
        style={!canOpenReg ? { backgroundColor: 'var(--card-bg)' } : {}}
      >
        <div>
          <p className="font-body font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
            {t('setup.gate.title')}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
            {canOpenReg ? t('setup.gate.ready_hint') : t('setup.gate.locked_hint')}
          </p>
          {openError && <p className="text-xs mt-2 text-burgundy">{formatErrorMessage(openError, t).primary}</p>}
        </div>
        <button
          type="button"
          onClick={handleOpenRegistration}
          disabled={!canOpenReg || opening}
          className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {opening
            ? t('setup.gate.opening')
            : canOpenReg
              ? t('setup.gate.ready_button')
              : t('setup.gate.title') + ' →'}
        </button>
      </section>

      {/* v0.50m → v0.70d-2d-2: Danger zone on the Setup Hub. Super
          Admin only — matches the backend guards on
          archive/unarchive/delete (require_role SUPER_ADMIN). Lets a
          Super Admin clean up an accidentally-created event without
          having to flow through to Registration phase first. Archive
          is reversible (steel-blue), Delete is not (burgundy) and
          uses type-to-confirm for strong intent.
          v0.70d-2d-2 (S4): collapsed by default. The audit observed
          the previous always-expanded section competing with — and in
          dark mode actively louder than — the primary "Open
          registration" CTA above. Danger Zone is rare-use recovery,
          not the page's primary affordance, so it now lives behind a
          quiet summary row. Click the row to expand. The destructive
          intent still reads at a glance via the burgundy-tinted
          border on the inner Delete box. */}
      {user?.role === 'super_admin' && (
        <div
          className="card-surface-solid rounded-2xl mt-5 overflow-hidden"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <button
            type="button"
            onClick={() => setShowDanger(s => !s)}
            aria-expanded={showDanger}
            className="w-full px-5 py-3 flex items-center justify-between gap-3 text-left hover:bg-black/[0.02] dark:hover:bg-white/[0.03] transition-colors"
          >
            <div className="min-w-0">
              <div className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
                {t('event.danger_zone')}
              </div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                {t('event.danger_zone.hint')}
              </div>
            </div>
            <span className="text-xs shrink-0" style={{ color: 'var(--text-subtle)' }} aria-hidden="true">
              {showDanger ? '▾' : '▸'}
            </span>
          </button>

          {showDanger && (
            <div className="px-5 pb-5">
              {archiveError && (
                <p className="text-xs mb-3" style={{ color: 'var(--alert-burgundy)' }}>{formatErrorMessage(archiveError, t).primary}</p>
              )}
              {deleteError && (
                <p className="text-xs mb-3" style={{ color: 'var(--alert-burgundy)' }}>{formatErrorMessage(deleteError, t).primary}</p>
              )}

              {/* Archive — reversible, steel-blue */}
              <div
                className="rounded-card p-4 flex items-center justify-between gap-3 mb-3"
                style={{
                  background: 'rgba(70,130,180,0.04)',
                  border: '1px solid rgba(70,130,180,0.22)',
                }}
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {event?.is_archived
                      ? (t('event.unarchive.title'))
                      : (t('event.archive.title'))}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {event?.is_archived
                      ? (t('event.unarchive.hint'))
                      : (t('event.archive.hint'))}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowArchiveConfirm(true)}
                  className="text-xs font-semibold px-4 py-2 rounded-card text-white shrink-0 bg-steel-blue hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors"
                >
                  {event?.is_archived
                    ? (t('event.unarchive.button'))
                    : (t('event.archive.button'))}
                </button>
              </div>

              {/* Delete — irreversible, burgundy */}
              <div
                className="rounded-card p-4 flex items-center justify-between gap-3"
                style={{
                  background: 'rgba(128,0,32,0.04)',
                  border: '1px solid rgba(128,0,32,0.15)',
                }}
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {t('event.delete.title')}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {t('event.delete.hint')}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(true)}
                  className="text-xs font-semibold px-4 py-2 rounded-card text-white shrink-0"
                  style={{ background: 'var(--alert-burgundy)' }}
                >
                  {t('event.delete.button')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Archive/Unarchive plain confirm modal — reversible action, no
          type-to-confirm needed. */}
      {showArchiveConfirm && event && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => { if (!archiving) setShowArchiveConfirm(false); }}
        >
          <div
            className="card-surface-solid rounded-2xl shadow-2xl max-w-md w-full p-6"
            style={{ border: '1px solid var(--card-border)' }}
            onClick={e => e.stopPropagation()}
          >
            <h3 className="font-heading font-bold text-lg mb-2" style={{ color: 'var(--text-primary)' }}>
              {event.is_archived
                ? (t('event.unarchive.confirm_title'))
                : (t('event.archive.confirm_title'))}
            </h3>
            <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>
              {event.is_archived
                ? (t('event.unarchive.confirm_body'))
                : (t('event.archive.confirm_body'))}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowArchiveConfirm(false)}
                disabled={archiving}
                className="text-xs font-medium px-4 py-2 rounded-card border disabled:opacity-50"
                style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleArchiveToggle}
                disabled={archiving}
                className="text-xs font-semibold px-4 py-2 rounded-card text-white bg-steel-blue hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50"
              >
                {archiving
                  ? (t('common.loading'))
                  : event.is_archived
                    ? (t('event.unarchive.button'))
                    : (t('event.archive.button'))}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete type-to-confirm modal — shared component used across the
          app for high-risk destructive actions.
          v0.61c-1: i18n keys corrected (event.delete.confirm.title/warning
          were typos for confirm_title/warning — the dot-form keys never
          existed in the i18n dictionary so the modal was rendering raw
          [event.delete.confirm.title] strings). Also brought into parity
          with EventDetailPage's delete flow by offering the
          "Download backup first?" link inside the warning. */}
      {showDeleteConfirm && event && (
        <StrongDeleteConfirm
          open={showDeleteConfirm}
          title={t('event.delete.confirm_title')}
          itemLabel={t('event.delete.item_label')}
          itemName={event.name}
          warning={(
            <span>
              {t('event.delete.warning')}
              {' '}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); handleBackupBeforeDelete(); }}
                className="underline font-semibold hover:opacity-80"
                style={{ color: 'var(--alert-burgundy)' }}
              >
                {t('event.delete.backup_first')}
              </button>
            </span>
          )}
          onConfirm={handleDeleteEvent}
          onCancel={() => setShowDeleteConfirm(false)}
          loading={deleting}
        />
      )}
    </div>
  );
}

function buildDetailsSummary(event, formatDate) {
  if (!event.start_date && !event.location) return null;
  const parts = [event.name];
  if (event.start_date) {
    const dates = event.end_date && event.end_date !== event.start_date
      ? `${formatDate(event.start_date)}–${formatDate(event.end_date)}`
      : formatDate(event.start_date);
    parts.push(dates);
  }
  if (event.location) parts.push(event.location);
  return parts.join(' · ');
}
