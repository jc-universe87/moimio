import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { events as eventsApi, participants as participantsApi, notes as notesApi, email as emailApi, allocationCategories, allocations as allocationsApi, getToken } from '../services/api';
import { formatErrorMessage } from '../services/api';
import { useAuth, getPermsForEvent, getRoleForEvent } from '../hooks/useAuth';
import { useDateFormat } from '../hooks/useDateFormat';
import { useEventPhase, PHASE, SUB_STATE } from '../hooks/useEventPhase';
import OrganiseDashboard from '../components/OrganiseDashboard';
import PeopleTable from '../components/PeopleTable';
import CheckInPanel from '../components/CheckInPanel';
import FormConfigPanel from '../components/FormConfigPanel';
import SharePanel from '../components/SharePanel';
import PhaseStrip from '../components/PhaseStrip';
import RegistrationStateBanner from '../components/RegistrationStateBanner';
import UnassignedBanner from '../components/UnassignedBanner';
import SetupHub from './SetupHub';
import RegistrationPhasePage from './RegistrationPhasePage';
import NoPermissionPage from './NoPermissionPage';
import { getLandingForUser, canAccessSection } from '../services/landing';
import ReportsPage from './ReportsPage';
import { useI18n } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';
import StyleCustomiser from '../components/StyleCustomiser';
import NotesModal from '../components/NotesModal';
import { useConfirmOverlay } from '../components/ConfirmOverlay';
import MarksPanel from '../components/MarksPanel';
import EventAssignmentsPanel from '../components/EventAssignmentsPanel';
import PreferencesPanel from '../components/PreferencesPanel';
import RestoreModal from '../components/RestoreModal';
import StrongDeleteConfirm from '../components/StrongDeleteConfirm';
import ArchiveConfirm from '../components/ArchiveConfirm';
import { detailsFormToPatch } from '../components/DetailsEditor';

import TranslatedError from '../components/TranslatedError';
export default function EventDetailPage() {
  const { eventId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  // Section param. Default computed post-event-load based on phase:
  //   Event phase → 'board' (new)
  //   Registration/fallback → 'organise' (v45 behaviour)
  // 'organise' and 'board' both render OrganiseDashboard — 'organise' is
  // retained as a back-compat alias for bookmarked v45 URLs.
  const sectionParam = searchParams.get('section');

  const [event, setEvent] = useState(null);
  const [participantList, setParticipantList] = useState([]);
  const [noteCounts, setNoteCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // v0.70d-3c-11: when the participant list 403s with the
  // 'errors.participant.no_event_perms' key, override section to
  // 'no-access' so the user sees the friendly NoPermissionPage
  // (variant: 'unassigned') instead of the inline error banner at
  // the top of an otherwise-empty page. The same condition is what
  // getLandingForUser already routes 'no-access' for in normal
  // (URL-less) navigation; this flag covers the URL-jump case where
  // a staff opens ?section=people directly without being routed by
  // the helper. Cleared on the next loadData success.
  const [noEventPerms, setNoEventPerms] = useState(false);
  const [notesFor, setNotesFor] = useState(null);
  const [showStyler, setShowStyler] = useState(false);
  const { user, staffContext, logout, refreshStaffContext } = useAuth();
  const { t } = useI18n();
  // v0.70d-3c-12: surgical toast addition for mutation errors that
  // fire deep in the page (participant delete in PeopleTable; event-
  // details save when scrolled past the form). Banner-at-top stays
  // in place via the existing setError flow — toast is supplemental,
  // visible regardless of scroll position.
  //
  // v0.70d-3c-13: full TranslatedError consolidation across all 22
  // sites in the codebase. Inert classes stripped; `variant` prop
  // added for the two canonical shapes; sites matching the default
  // dropped className entirely. See TranslatedError.jsx for the
  // canonical-shape doc.
  const { showToast, ToastHost } = useToast();
  const { formatDate } = useDateFormat();
  const { phase, subState } = useEventPhase(event);
  // v0.50j: `isAdmin` here means "admin on THIS event". Super Admin
  // passes unconditionally; staff users must have an EventUserAssignment
  // with role='event_admin' on this event. The previous check against a
  // system-wide EVENT_ADMIN role was always loose — v0.50j removed that
  // role and tightened the gate.
  const isAdmin = user?.role === 'super_admin'
    || getRoleForEvent(staffContext, eventId) === 'event_admin';
  const userId = user?.id;
  const isStaff = user?.role === 'staff';
  // v0.50e-1c: look up staff permissions scoped to the event on screen.
  // Previously read from staffContext.permissions which implicitly assumed
  // one-event-per-staff; now works correctly for staff assigned to
  // multiple events.
  const staffPerms = isStaff ? getPermsForEvent(staffContext, eventId) : {};
  // For each view, staff have write access if their group grants it.
  // v0.50e-1a: for 'checkin', the permission is now a single value —
  // any truthy value ("write") means access. The === 'write' check
  // still works correctly because "write" is the only truthy value
  // after the fresh-start migration cleared old "read" entries.
  // v1.0-pre #10: canWrite handles the α-shape `checkin` object alongside
  // the legacy flat-string. For other views it's a straight 'write' string
  // comparison as before.
  const canWrite = (view) => {
    if (isAdmin) return true;
    if (!isStaff) return false;
    if (view === 'checkin') {
      const c = staffPerms.checkin;
      if (c && typeof c === 'object') return c.access === 'write';
      return c === 'write';
    }
    return staffPerms[view] === 'write';
  };
  // Helper: any check-in access at all (read or write — though current
  // model collapses both to "write"). Used for sidebar gating + view
  // visibility, distinct from canWrite which gates the tick action.
  const hasAnyCheckin = () => {
    if (isAdmin) return true;
    if (!isStaff) return false;
    const c = staffPerms.checkin;
    if (c && typeof c === 'object') return !!c.access;
    return !!c;
  };
  const { confirm, ConfirmOverlay } = useConfirmOverlay();

  // Effective section: if URL param is set, use it (with 'organise' aliasing
  // to 'board' during Event phase as a back-compat for the v45 sidebar item).
  // Otherwise the default depends on user + phase, computed centrally
  // by getLandingForUser (v0.50d-3).
  //
  // Note: the 'organise' alias only applies in EVENT phase. In other
  // phases 'organise' is the legacy section that renders the
  // OrganiseDashboard, so we leave it alone.
  let section;
  // v0.70d-3c-12: URL-jump validation — sectionParam comes from the
  // URL and may be a section the user doesn't have permission to see
  // (stale bookmark, shared link, perm changes after page open).
  // Compute whether the requested section is accessible; if not, fall
  // back to their default landing. The toast firing happens in a
  // useEffect below to avoid emitting on every render.
  const requestedSectionAccessible = sectionParam
    ? canAccessSection({ section: sectionParam, phase, staffPerms, isAdmin })
    : true;
  if (noEventPerms) {
    // v0.70d-3c-11: 403 fallback (G3). Backend told us the user is
    // assigned but has no perms; route to the friendly placeholder.
    section = 'no-access';
  } else if (sectionParam && requestedSectionAccessible) {
    // v0.50m: alias 'organise' → 'board' in BOTH Event AND Registration phase.
    // The sidebar's More menu item id is 'organise' (legacy) but the actual
    // renderer is under `section === 'board'` which mounts OrganiseDashboard.
    // Previously this alias only fired in Event phase, leaving a blank
    // page when an admin clicked Gruppentypen during Registration.
    section = (sectionParam === 'organise' && (phase === PHASE.EVENT || phase === PHASE.REGISTRATION))
      ? 'board'
      : sectionParam;
  } else {
    // Either no sectionParam, or sectionParam was inaccessible.
    // In the inaccessible case, the useEffect below shows a toast.
    section = getLandingForUser({ user, phase, staffPerms, isAdmin });
    // 'organise' returned by the helper for staff means "show them the
    // OrganiseDashboard"; admins land on 'board'. Both render via their
    // respective handlers further down. We do NOT alias 'organise' to
    // 'board' here — staff legitimately need OrganiseDashboard.
  }

  // v0.70d-3c-12: emit the URL-jump fallback toast once when an
  // inaccessible sectionParam is observed. Tracks the last "blocked"
  // sectionParam so we don't re-fire on every re-render. Cleared
  // whenever sectionParam returns to an accessible value.
  //
  // v1.0-pre #12 (v0.96): guard on `loading` so the toast doesn't fire
  // during bootstrap. While `event` is still loading, useEventPhase
  // falls back to PHASE.SETUP (see phase.js: `if (!event) return SETUP`),
  // and canAccessSection('checkin', SETUP, ...) returns false even for
  // staff with the correct pre_event flag. The early-return at line
  // ~501 hides the page itself during loading, but useEffect runs
  // regardless of that early return — so without this guard, the toast
  // fires once on every fresh mount of ?section=checkin (hard reload,
  // deep-link arrival from email, new tab). Once loading flips false,
  // the deps change and the effect runs again with the real phase.
  const lastBlockedSection = useRef(null);
  useEffect(() => {
    if (loading) return;
    if (sectionParam && !requestedSectionAccessible) {
      if (lastBlockedSection.current !== sectionParam) {
        lastBlockedSection.current = sectionParam;
        showToast(t('errors.section.no_access'), 'error', 5000);
      }
    } else {
      lastBlockedSection.current = null;
    }
  }, [sectionParam, requestedSectionAccessible, loading, showToast, t]);

  // Event details form
  const [detailForm, setDetailForm] = useState({ name: '', description: '', location: '', start_date: '', end_date: '' });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Email settings
  const [emailFrom, setEmailFrom] = useState('');
  const [emailReplyTo, setEmailReplyTo] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailSaved, setEmailSaved] = useState(false);
  const [emailError, setEmailError] = useState(null);

  // Allocation categories (used by the Export section for per-category PDFs)
  const [eventCategories, setEventCategories] = useState([]);
  // v0.50p: PdfExportModal component fully removed (file deleted).
  // Detailed PDF downloads happen directly from the AllocationBoard overflow
  // menu; compact/sign-in downloads are direct buttons on the Reports page.
  const [showRestore, setShowRestore] = useState(false);
  // v0.50g-2: delete-event state. `deleting` is the in-flight flag; the
  // error lands on `error` via setError the same way other admin mutations do.
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  // v0.50i: archive/unarchive state. Single confirm modal handles both
  // directions; copy and behaviour switches based on event.is_archived.
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false);
  const [archiving, setArchiving] = useState(false);

  const handleArchiveToggle = async () => {
    if (!event) return;
    setArchiving(true);
    try {
      const updated = event.is_archived
        ? await eventsApi.unarchive(eventId)
        : await eventsApi.archive(eventId);
      setEvent(updated);
      setShowArchiveConfirm(false);
    } catch (err) {
      setError(err);
    } finally {
      setArchiving(false);
    }
  };

  const handleDeleteEvent = async () => {
    if (!event) return;
    setDeleting(true);
    try {
      await eventsApi.delete(eventId);
      // Success — navigate back to the events list. Do this before the
      // setState calls below, which will never run because we're leaving.
      navigate('/admin/events');
    } catch (err) {
      setError(err);
      setShowDeleteConfirm(false);
      setDeleting(false);
    }
  };

  // v0.50g-2: trigger a per-event backup download from the confirmation
  // dialog so the Super Admin can snapshot before destroying. Same shape
  // as the dropped per-event backup button, resurrected here as a nudge.
  // v0.61c: getToken is now part of the static top-of-file import — the
  // earlier dynamic `await import('../services/api')` was producing a
  // Vite build warning (mixed static + dynamic imports of the same
  // module can't actually be code-split) and bought us nothing because
  // services/api was already in the main bundle.
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
      setError(err);
    }
  };

  // v0.50d-4: refresh staff permissions on event navigation. Ensures an
  // admin's recent permission changes are picked up when the staff user
  // enters an event (they might have been logged in throughout). No-op
  // for admins. Fire-and-forget — doesn't block loadData.
  useEffect(() => { loadData(); refreshStaffContext(); }, [eventId]);

  // v50c-3c-2a: soft auto-redirect for staff whose ONLY permission is
  // check-in. Multi-role staff (checkin + people, etc.) are NOT redirected —
  // they get the normal sidebar so they can navigate between their duties,
  // and can still click the Check-in nav item to reach it.
  // Ref-guarded so navigating back doesn't re-trigger.
  const didInitialCheckinRedirect = useRef(false);
  useEffect(() => {
    if (didInitialCheckinRedirect.current) return;
    if (!event) return;
    if (!isStaff || !staffPerms.checkin) return;
    if (phase !== PHASE.EVENT) return;
    // Check if checkin is the ONLY permission. Ignore 'none'/falsy entries.
    const permKeys = Object.keys(staffPerms).filter(
      k => staffPerms[k] && staffPerms[k] !== 'none'
    );
    const onlyCheckin = permKeys.length === 1 && permKeys[0] === 'checkin';
    if (onlyCheckin) {
      didInitialCheckinRedirect.current = true;
      navigate(`/admin/events/${eventId}/checkin`, { replace: true });
    }
  }, [event, isStaff, staffPerms, phase, eventId, navigate]);

  useEffect(() => {
    if (event) {
      setDetailForm({
        name: event.name || '', description: event.description || '',
        location: event.location || '', start_date: event.start_date || '', end_date: event.end_date || '',
        timezone: event.timezone || 'UTC',
      });
      setEmailFrom(event.settings?.email_from_name || '');
      setEmailReplyTo(event.settings?.email_reply_to || '');
    }
  }, [event]);

  const loadData = async () => {
    try {
      const [eventData, participantData] = await Promise.all([
        eventsApi.get(eventId),
        participantsApi.list(eventId),
      ]);
      setEvent(eventData);
      setParticipantList(participantData);
      setNoEventPerms(false);
      notesApi.counts(eventId).then(setNoteCounts).catch(() => {});
    } catch (err) {
      // v0.70d-3c-11: special-case the no-event-perms 403 — staff
      // user has an event assignment but no perm boxes ticked yet.
      // Re-route to the friendly NoPermissionPage instead of
      // surfacing the bare error banner. We still load the event
      // record (it's a separate request that DOESN'T 403 for
      // assignment-but-no-perms staff — they can see the event's
      // existence; they just can't see participants). If the event
      // request also failed, fall through to setError.
      const detailKey = err?.response?.data?.detail?.key
        ?? err?.detail?.key;
      if (detailKey === 'errors.participant.no_event_perms') {
        setNoEventPerms(true);
        // Try to grab the event record solo so the no-access page
        // can show the event name. If this also fails, eventName
        // will just be undefined (NoPermissionPage handles that).
        try {
          const eventData = await eventsApi.get(eventId);
          setEvent(eventData);
        } catch { /* swallow — already in fallback path */ }
      } else {
        setError(err);
      }
    }
    finally { setLoading(false); }
  };

  // Categories + (Event-phase only) allocations map for the unassigned banner.
  const [allocationsByCategory, setAllocationsByCategory] = useState({}); // {catId: {unitId: [{participant_id, ...}]}}

  // v0.70d-2c (R4-B): per-session dismissal of the "event has no
  // group types" banner. Seeded from sessionStorage so a refresh
  // respects the user's dismissal this session, but next session
  // starts fresh — giving the admin another chance to notice.
  const [r4bDismissed, setR4bDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(`r4b-dismissed-${eventId}`) === '1';
    } catch {
      return false;
    }
  });
  useEffect(() => {
    if (!event) return;
    allocationCategories.list(eventId).catch(() => []).then(cats => {
      setEventCategories(cats || []);
    });
    // Only fetch full allocations map when we're likely to render the
    // unassigned banner (Event phase, non-staff). Skip otherwise.
    if (event.status !== 'draft' && !isStaff) {
      allocationsApi.all(eventId).catch(() => ({})).then(map => {
        setAllocationsByCategory(map || {});
      });
    }
  }, [eventId, event, isStaff]);

  const handleSaveDetails = async (e) => {
    e.preventDefault(); setSaving(true); setSaved(false);
    try {
      // v0.50m: normalise the form payload — empty date inputs must be
      // serialised as null (Pydantic rejects "" for date fields with
      // "Input should be a valid date, input is too short"). The SetupHub
      // save path has done this since v50b via detailsFormToPatch; this
      // inline form on EventDetailPage was missed and crashed on save
      // whenever either date field was cleared.
      const patch = detailsFormToPatch(detailForm);
      const updated = await eventsApi.update(eventId, patch);
      setEvent(updated); setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      // v0.70d-3c-12: dual-fire (see handleDelete). Event-details
      // form is long enough that the save button is often scrolled
      // away from the top-of-page banner.
      setError(err);
      showToast(err, 'error');
    }
    finally { setSaving(false); }
  };

  const handleSaveEmail = async () => {
    setEmailSaving(true); setEmailSaved(false); setEmailError(null);
    try {
      const settings = { ...(event.settings || {}), email_from_name: emailFrom, email_reply_to: emailReplyTo };
      const updated = await eventsApi.update(eventId, { settings });
      setEvent(updated);
      setEmailSaved(true);
      setTimeout(() => setEmailSaved(false), 2000);
    } catch (err) { setEmailError(err); }
    finally { setEmailSaving(false); }
  };

  const toggleGroupPreferences = async () => {
    try {
      const settings = { ...(event.settings || {}), enable_group_preferences: !event.settings?.enable_group_preferences };
      const updated = await eventsApi.update(eventId, { settings });
      setEvent(updated);
    } catch {}
  };

  const toggleEmailConfirmation = async () => {
    try {
      const settings = { ...(event.settings || {}), require_email_confirmation: !event.settings?.require_email_confirmation };
      const updated = await eventsApi.update(eventId, { settings });
      setEvent(updated);
    } catch (err) { setError(err); }
  };

  const handleTestEmail = async () => {
    setTesting(true); setTestResult(null);
    try { await emailApi.test(eventId); setTestResult(t('event.email_test_sent')); }
    catch (err) { setTestResult(err.message); }
    finally { setTesting(false); }
  };

  const handleDelete = async (participantId, name) => {
    const ok = await confirm({
      title: `Remove ${name}?`,
      message: 'This participant will be removed from all active lists, allocations, and counts. Their data is preserved for record-keeping purposes but they will no longer be visible in the event. This action can be reversed by an administrator.',
      confirmLabel: 'Remove Participant',
      danger: true,
    });
    if (!ok) return;
    try { await participantsApi.delete(participantId); await loadData(); }
    catch (err) {
      // v0.70d-3c-12: dual-fire toast + banner. The setError still
      // updates the top-of-page banner (defence in depth — survives
      // page refresh / navigation), but the toast surfaces the error
      // immediately wherever the user is on the page. Critical here
      // because PeopleTable is long; user is often scrolled deep
      // when triggering the delete.
      setError(err);
      showToast(err, 'error');
    }
  };

  // v50c-2: close registration from the Event-phase banner. Uses the
  // dedicated /registration/close endpoint (the same path the Registration
  // phase banner will use in v50d). Broadcasts so AdminLayout refetches.
  const [closingReg, setClosingReg] = useState(false);
  const handleCloseRegistration = async () => {
    setClosingReg(true);
    try {
      const updated = await eventsApi.closeRegistration(eventId);
      setEvent(updated);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('moimio:event-changed'));
      }
    } catch (err) {
      setError(err);
    } finally {
      setClosingReg(false);
    }
  };

  // v50c-3c-1: re-open registration from the closed-state banner. Mirror of
  // close. Useful during Event phase when late signups may still arrive.
  const [reopeningReg, setReopeningReg] = useState(false);
  const handleReopenRegistration = async () => {
    setReopeningReg(true);
    try {
      const updated = await eventsApi.openRegistration(eventId);
      setEvent(updated);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('moimio:event-changed'));
      }
    } catch (err) {
      setError(err);
    } finally {
      setReopeningReg(false);
    }
  };

  // v1.0-pre #20: goToSection accepts an optional extras object so
  // callers (e.g. RegistrationPhasePage's Attention card) can deep-link
  // to a section with pre-filled query params (?status=pending etc.).
  const goToSection = (s, extras) => {
    const params = new URLSearchParams({ section: s });
    if (extras && typeof extras === 'object') {
      for (const [k, v] of Object.entries(extras)) {
        if (v !== undefined && v !== null && v !== '') params.set(k, String(v));
      }
    }
    navigate(`/admin/events/${eventId}?${params.toString()}`);
  };

  if (loading) return <p className="text-gray-400">{t('common.loading')}</p>;
  if (error && !event) return (
    <div className="max-w-lg mx-auto mt-8">
      <TranslatedError err={error} className="text-sm rounded-card p-4 mb-4" />
      <button onClick={loadData} className="text-sm text-steel-blue hover:text-mid-navy">{t('event.retry')}</button>
    </div>
  );
  if (!event) return <p className="text-red-500">{t('event.not_found')}</p>;

  // ─── v50b Setup hub routing ─────────────────────────────────────────
  // While the event is in Setup phase (draft status), the hub is the home.
  // Staff members (no setup access) bypass this — they see their own
  // assigned section via the v45 flow further below.
  //
  // onEventChange lets SetupHub tell us the event changed (e.g. opened
  // registration → status flips to 'open'). Updating our local `event`
  // re-runs useEventPhase, phase leaves SETUP, and this early-return
  // stops firing — falls through to the v45 UI below.
  // v0.50n: admins on this event see the Setup Hub in Setup phase,
  // regardless of their system-level role. Previously the gate was
  // `!isStaff` which stranded Staff users who created their own event
  // (they became per-event Event Admin, but still had system role
  // 'staff', so this branch didn't fire and they landed on the
  // allocation board with no way to configure the event).
  // `isAdmin` here means "Super Admin OR per-event admin" — see the
  // isAdmin calculation above.
  if (phase === PHASE.SETUP && isAdmin) {
    return <SetupHub onEventChange={setEvent} />;
  }
  // ────────────────────────────────────────────────────────────────────

  // v1.0-pre #4: header-block computation hoisted above the registration-
  // phase early-return so the same compact header (event name + status
  // badge + Registered/Checked-In/Pending pills) appears for both
  // RegistrationPhasePage and the v45 fall-through render.
  const activeParticipants = participantList.filter(p => p.registration_status !== 'cancelled');
  const registeredCount = activeParticipants.length;
  const checkedInCount = participantList.filter(p => p.checked_in).length;
  const pendingCount = participantList.filter(p => p.registration_status === 'pending').length;

  // v0.70d-2a (R8a/R8c): phase/status pill tones re-mapped to semantic
  // tokens. `open` (actively collecting registrations) reads as io-accent
  // — the current active state. `closed` (no longer collecting) is
  // neutral — it's not "pending action", just a quieter state. `archived`
  // stays burgundy (alert). Pending and checked-in counts move to
  // `--pending-color` and `--io-accent` respectively, so the colour
  // vocabulary is coherent: accent = active/positive, pending = awaiting
  // organiser action, alert = destructive/frozen, neutral = quiet.
  const STATUS_PILL = {
    draft:    { bg: 'var(--neutral-tint)', color: 'var(--text-muted)' },
    open:     { bg: 'var(--accent-tint)',  color: 'var(--io-accent)' },
    closed:   { bg: 'var(--neutral-tint)', color: 'var(--text-muted)' },
    archived: { bg: 'var(--alert-tint)',   color: 'var(--alert-burgundy)' },
  };
  const statusPill = STATUS_PILL[event.status] || STATUS_PILL.draft;
  const phaseLabel = (phase === PHASE.EVENT && subState)
    ? t('phase.' + subState)
    : (t('status.' + event.status) || event.status);

  // Compact header — name + phase badge + dates + Registered/Checked-In/
  // Pending stat pills. Used by both code paths below.
  const compactHeader = (
    <div
      className="card-surface-solid rounded-2xl px-4 py-3 mb-4"
      style={{ border: '1px solid var(--card-border)' }}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h1 className="font-heading text-lg font-bold truncate" style={{ color: 'var(--text-primary)' }}>
              {event.name}
            </h1>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0"
              style={{ background: statusPill.bg, color: statusPill.color }}>
              {phaseLabel}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
            {event.location && <span>{event.location}</span>}
            {event.start_date && <span>{formatDate(event.start_date)}{event.end_date ? ` – ${formatDate(event.end_date)}` : ''}</span>}
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div onClick={() => goToSection('people')} className="text-center cursor-pointer hover:opacity-80 transition-opacity">
            <div className="text-lg font-bold leading-none" style={{ color: 'var(--text-primary)' }}>{registeredCount}</div>
            <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>{t('event.registered_count')}</div>
          </div>
          <div onClick={() => goToSection('checkin')} className="text-center cursor-pointer hover:opacity-80 transition-opacity">
            <div className="text-lg font-bold leading-none" style={{ color: 'var(--io-accent)' }}>{checkedInCount}</div>
            <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>{t('event.checkedin_count')}</div>
          </div>
          <div onClick={() => goToSection('people', { status: 'pending' })} className="text-center cursor-pointer hover:opacity-80 transition-opacity">
            <div className="text-lg font-bold leading-none" style={{ color: 'var(--pending-color)' }}>{pendingCount}</div>
            <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>{t('event.pending_count')}</div>
          </div>
        </div>
      </div>
    </div>
  );

  // ─── v50d Registration phase landing ────────────────────────────────
  // Admin-only. Staff fall through to the v45 flow where their
  // permissions route them to the appropriate section (People /
  // Organise / Check-in etc.).
  //
  // Only overrides when there's no explicit section in the URL — so
  // navigating to ?section=people from within Registration still works
  // as expected. That's how "View all participants →" and the attention
  // queue's "Review" jump from the landing into the main app.
  if (phase === PHASE.REGISTRATION && isAdmin && !sectionParam) {
    return (
      <div>
        <ToastHost />
        <TranslatedError err={error} />
        {compactHeader}
        {/* v1.0-pre #21: PhaseStrip on the Registration overview page
            for visual consistency with the rest of the admin shell.
            Other pages render this strip below the compact header; the
            Registration overview was missing it. */}
        <div className="mb-4">
          <PhaseStrip currentPhase={phase} />
        </div>
        <RegistrationPhasePage
          event={event}
          participantList={participantList}
          isAdmin={isAdmin}
          isStaff={isStaff}
          staffPerms={staffPerms}
          onEventChange={setEvent}
          goToSection={goToSection}
        />
      </div>
    );
  }
  // ────────────────────────────────────────────────────────────────────

  const inputClass = "w-full rounded-card px-3 py-2 text-sm border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]";

  return (
    <div>
      <ToastHost />
      <TranslatedError err={error} />

      {/* Compact event header + stats — shared with the Registration phase
          early-return above (v1.0-pre #4). Defined as `compactHeader`
          earlier in this component to avoid duplication. */}
      {compactHeader}

      {/* v0.50i: Read-only banner shown when event is archived. v0.50i-1
          collapses the split Super/non-Super text into one message —
          archive is frozen for everyone, including Super Admins, so
          the same "unarchive to edit" instruction applies. Sits above
          PhaseStrip so it's the first thing the user notices. */}
      {event?.is_archived && (
        <div
          className="mb-4 rounded-card p-3 flex items-start gap-2 text-xs"
          style={{
            background: 'rgba(70,130,180,0.06)',
            border: '1px solid rgba(70,130,180,0.22)',
            color: 'var(--text-primary)',
          }}
        >
          <span aria-hidden="true" style={{ color: '#2B5A82' }}>📦</span>
          <div className="flex-1 min-w-0">
            <span className="font-semibold" style={{ color: '#2B5A82' }}>
              {t('event.archived_banner.label')}
            </span>
            <span style={{ color: 'var(--text-subtle)' }}>
              {' · '}
              {user?.role === 'super_admin'
                ? (t('event.archived_banner.super'))
                : (t('event.archived_banner.user'))}
            </span>
          </div>
        </div>
      )}

      {/* Phase strip (§7.2) — visible across all phases except Setup
          (Setup gets the hub layout which has its own PhaseStrip). */}
      {!isStaff && (
        <div className="mb-4">
          <PhaseStrip currentPhase={phase} />
        </div>
      )}

      {/* v0.70d-2c (R4-B): event-lifetime banner for admin events past
          Setup phase with zero group types configured. These events
          pre-date the Group-Types-required-on-new-events promotion;
          we don't block them (would break their flow), but warn
          clearly that allocation features will be limited and offer
          a one-click route back to the setup hub. Dismissable per
          session via sessionStorage so an admin who acknowledges
          the warning isn't nagged again this session. */}
      {isAdmin
        && phase !== PHASE.SETUP
        && eventCategories.length === 0
        && !r4bDismissed && (
        <div
          className="mb-4 rounded-card border p-3 flex items-start gap-3"
          style={{
            background: 'var(--pending-tint)',
            borderColor: 'var(--pending-border)',
          }}
          role="status"
        >
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-pending">
              {t('setup.group_types.missing_banner_title')}
            </p>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
              {t('setup.group_types.missing_banner_body')}
            </p>
            <button
              type="button"
              onClick={() => goToSection('setup')}
              className="text-[11px] font-semibold text-accent hover:opacity-80 mt-1"
            >
              {t('setup.group_types.missing_banner_cta')}
            </button>
          </div>
          <button
            type="button"
            onClick={() => {
              try { sessionStorage.setItem(`r4b-dismissed-${eventId}`, '1'); } catch { /* storage disabled; silent noop */ }
              setR4bDismissed(true);
            }}
            aria-label={t('common.dismiss')}
            className="shrink-0 text-lg leading-none"
            style={{ color: 'var(--text-subtle)' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* v1.0-pre #12: pre-event Check-in setup banner for staff. Renders
          when a staff member with checkin.pre_event has landed on People
          during Registration phase (their default landing per landing.js).
          The Registration overview page hosts the same link for admins;
          staff don't reach that page, so we surface it here instead. */}
      {phase === PHASE.REGISTRATION && isStaff && (() => {
        const c = staffPerms?.checkin;
        return c && typeof c === 'object' && c.access && c.pre_event;
      })() && section === 'people' && (
        <div
          className="card-surface-solid rounded-2xl px-4 py-3 mb-4 flex items-center justify-between gap-3"
          style={{ border: '1px solid var(--card-border)', background: 'var(--accent-tint)' }}
        >
          <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
            {t('reg_phase.checkin_pre_event_banner.body')}
          </div>
          <button
            type="button"
            onClick={() => goToSection('checkin')}
            className="shrink-0 text-sm font-semibold hover:underline"
            style={{ color: 'var(--io-accent)' }}
          >
            → {t('reg_phase.checkin_pre_event_link')}
          </button>
        </div>
      )}

      {/* ─── PEOPLE ─── */}
      {section === 'people' && (
        <PeopleTable
          eventId={eventId}
          userId={userId}
          participantList={participantList}
          noteCounts={noteCounts}
          isAdmin={canWrite('people')}
          canDelete={isAdmin}
          marksPerm={isAdmin ? 'write' : (staffPerms.marks || '')}
          /* v1.0-pre #20: deep-link the status pill via ?status=...
             so the Attention card on RegistrationPhasePage can jump
             admins straight into the Pending view. Recognised values
             match the pill ids: pending / confirmed / cancelled. */
          initialStatusFilter={searchParams.get('status') || ''}
          onDataChange={loadData}
          onOpenNotes={(p) => setNotesFor({ type: 'participant', id: p.id, name: `${p.first_name} ${p.last_name}` })}
          onDelete={handleDelete}
        />
      )}

      {/* ─── BOARD (Event phase default, also Registration fallback) ─── */}
      {section === 'board' && phase === PHASE.EVENT && (() => {
        /* v50c-3c-1: Event-phase board header cluster.
           - Registration state banner (open vs closed toggle)
           - Unassigned late-signup banner (when applicable)
           - Quick link to public registration form
           Computation of the unassigned banner data happens here at render
           time — cheap enough for realistic event sizes (≤ a few hundred
           participants). */
        const activeParts = participantList.filter(p => p.registration_status !== 'cancelled');

        // For each category with allocated_count > 0, count registered
        // participants NOT placed in any unit of that category.
        let topCat = null;
        let topCount = 0;
        for (const cat of eventCategories) {
          if ((cat.allocated_count || 0) === 0) continue;
          const unitMap = allocationsByCategory[cat.id] || {};
          const placedIds = new Set();
          for (const members of Object.values(unitMap)) {
            for (const m of members) placedIds.add(m.participant_id);
          }
          const unassigned = activeParts.filter(p => !placedIds.has(p.id)).length;
          if (unassigned > 0) {
            // Pick the category with the FEWEST unassigned — closest to done,
            // quickest actionable win. (Ties broken by whichever came first.)
            if (topCat === null || unassigned < topCount) {
              topCat = cat;
              topCount = unassigned;
            }
          }
        }

        return (
          <>
            <RegistrationStateBanner
              event={event}
              isAdmin={isAdmin}
              onClose={handleCloseRegistration}
              onReopen={handleReopenRegistration}
              busy={closingReg || reopeningReg}
            />
            {topCat && (
              <UnassignedBanner
                categoryName={topCat.name}
                count={topCount}
                onPlaceThem={() => {
                  // Scroll to the specific category card. Each card in
                  // OrganiseDashboard has id={`cat-${id}`} (v50c-3c-1a).
                  const el = document.getElementById(`cat-${topCat.id}`);
                  if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Brief highlight via CSS animation hook — the card
                    // can optionally listen for a class toggle. For now
                    // the scroll itself is the visual anchor.
                  }
                }}
              />
            )}
            {/* Right-aligned action row:
                - Enter check-in mode → (admin only, visible in Preparing + Live,
                  hidden in Done; spec §4.3/§5). Filled Steel Blue / Gold so it
                  stands out as the primary action while the event runs.
                - View registration form ↗ (always available). */}
            <div className="mb-4 flex items-center justify-end gap-3 flex-wrap">
              {isAdmin && phase === PHASE.EVENT && subState !== SUB_STATE.DONE && (
                <button
                  type="button"
                  onClick={() => navigate(`/admin/events/${eventId}/checkin`)}
                  className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 whitespace-nowrap"
                >
                  {t('checkin.mode.enter')} →
                </button>
              )}
              <a
                href={`/register/${eventId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-steel-blue dark:text-gold hover:underline"
              >
                {t('board.view_form')} ↗
              </a>
            </div>
          </>
        );
      })()}
      {section === 'board' && event?.settings?.enable_group_preferences && (
        <div className="mb-4">
          <PreferencesPanel eventId={eventId} isAdmin={isAdmin} />
        </div>
      )}
      {section === 'board' && <div className="pb-32 md:pb-10"><OrganiseDashboard eventId={eventId} eventName={event?.name} participantList={participantList} noteCounts={noteCounts} isAdmin={isAdmin} staffPerms={staffPerms} onDataChange={loadData} /></div>}

      {/* ─── REPORTS (placeholder — v50c-1) ─── */}
      {section === 'reports' && <ReportsPage eventId={eventId} eventName={event?.name} phase={phase} />}

      {/* ─── CHECK-IN ─── */}
      {/* v1.0-pre #12 (v0.97): pick the right view based on phase +
          pre_event sub-flag. Staff with check-in permission but not
          yet able to do check-in work (Setup phase, or Registration
          without pre_event) see the calm "starts when event begins"
          placeholder. Admins always see the operational panel. The
          gate in canAccessSection has already filtered out staff
          with no check-in access at all, so the only paths into
          this branch are (a) admins, (b) staff with at least the
          access flag set. */}
      {section === 'checkin' && (() => {
        const c = staffPerms?.checkin;
        const hasPreEvent = !!(c && typeof c === 'object' && c.access && c.pre_event);
        const checkinReady = isAdmin
          || phase === PHASE.EVENT
          || (phase === PHASE.REGISTRATION && hasPreEvent);
        if (checkinReady) {
          return (
            <CheckInPanel
              eventId={eventId}
              participantList={participantList}
              isAdmin={canWrite('checkin')}
              canCreateColumns={isAdmin}
              canViewColumns={hasAnyCheckin()}
              marksPerm={isAdmin ? 'write' : (staffPerms.marks || '')}
              userId={userId}
              noteCounts={noteCounts}
              onOpenNotes={(p) => setNotesFor({ type: 'participant', id: p.id, name: `${p.first_name} ${p.last_name}` })}
            />
          );
        }
        return (
          <NoPermissionPage
            eventName={event?.name}
            variant="checkin_not_yet"
            onRefresh={async () => { await refreshStaffContext(); await loadData(); }}
            onSignOut={() => { logout(); navigate('/login'); }}
          />
        );
      })()}

      {/* ─── SETUP: EVENT DETAILS ─── */}
      {section === 'event-details' && (
        <div className="max-w-2xl space-y-6 overflow-x-auto">
          <div
            className="card-surface-solid rounded-2xl p-5"
            style={{ border: '1px solid var(--card-border)' }}
          >
            <h3 className="font-heading font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
              {t('nav.setup.event_details')}
            </h3>
            {isAdmin ? (
              <form onSubmit={handleSaveDetails} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('event.details.name')} *
                  </label>
                  <input type="text" value={detailForm.name} required
                    onChange={e => setDetailForm(p => ({ ...p, name: e.target.value }))}
                    className={inputClass} />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('event.details.description')}
                  </label>
                  <textarea value={detailForm.description} rows={3}
                    onChange={e => setDetailForm(p => ({ ...p, description: e.target.value }))}
                    className={`${inputClass} resize-none`} />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('event.details.location')}
                  </label>
                  <input type="text" value={detailForm.location}
                    onChange={e => setDetailForm(p => ({ ...p, location: e.target.value }))}
                    className={inputClass} />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                      style={{ color: 'var(--text-subtle)' }}>
                      {t('event.details.start')}
                    </label>
                    <input type="date" value={detailForm.start_date}
                      onChange={e => setDetailForm(p => ({ ...p, start_date: e.target.value }))}
                      className={inputClass} />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                      style={{ color: 'var(--text-subtle)' }}>
                      {t('event.details.end')}
                    </label>
                    <input type="date" value={detailForm.end_date}
                      onChange={e => setDetailForm(p => ({ ...p, end_date: e.target.value }))}
                      className={inputClass} />
                  </div>
                </div>
                <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                  {t('event.details.date_hint')}
                </p>
                <button type="submit" disabled={saving}
                  className="text-sm font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 transition-colors">
                  {saved ? `✓ ${t('event.details.saved')}` : saving ? t('event.details.saving') : t('event.details.save')}
                </button>
              </form>
            ) : (
              <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>
                {t('common.no_access')}
              </p>
            )}
          </div>

          {/* v0.50g-2: Danger zone — Super Admin only. Hard-delete cascades
              through every participant, allocation, mark, custom field and
              note attached to this event. Irreversible by design — backup
              nudge link sits inside the confirmation dialog.
              v0.83 #33: collapsed by default to stop competing with the
              "Save details" CTA above. Same pattern as SetupHub's
              danger zone. Native <details>/<summary> for accessibility. */}
          {user?.role === 'super_admin' && (
            <details
              className="group card-surface-solid rounded-2xl"
              style={{ border: '1px solid rgba(128,0,32,0.25)' }}
            >
              <summary className="cursor-pointer p-5 flex items-center justify-between gap-3 select-none">
                <div className="min-w-0">
                  <h3 className="font-heading font-bold inline" style={{ color: 'var(--alert-burgundy)' }}>
                    {t('event.danger_zone')}
                  </h3>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {t('event.danger_zone.hint')}
                  </p>
                </div>
                <span aria-hidden="true"
                  className="shrink-0 text-xs transition-transform duration-150 group-open:rotate-180"
                  style={{ color: 'var(--alert-burgundy)' }}>
                  ▾
                </span>
              </summary>
              <div className="px-5 pb-5 pt-0">
                {/* v0.50i: Archive card — reversible, so steel-blue tones not
                    burgundy. Listed before Delete because it's the gentler
                    option. Button label/state flips based on is_archived. */}
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
                    onClick={() => setShowArchiveConfirm(true)}
                    className="text-xs font-semibold px-4 py-2 rounded-card text-white shrink-0 bg-steel-blue hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors"
                  >
                    {event?.is_archived
                      ? (t('event.unarchive.button'))
                      : (t('event.archive.button'))}
                  </button>
                </div>
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
                    onClick={() => setShowDeleteConfirm(true)}
                    className="text-xs font-semibold px-4 py-2 rounded-card text-white shrink-0"
                    style={{ background: 'var(--alert-burgundy)' }}
                  >
                    {t('event.delete.button')}
                  </button>
                </div>
              </div>
            </details>
          )}
        </div>
      )}

      {/* ─── SETUP: REGISTRATION (form + preferences) ─── */}
      {section === 'registration' && (
        <div className="max-w-2xl space-y-6 overflow-x-auto">
          {/* v0.50d-4c: Registration lifecycle controls removed.
              Opening, closing, and re-opening registration are now
              handled by phase-aware UI:
                - Setup phase → Setup hub "Open registration" card
                - Registration phase → landing page "Close registration"
                - Event phase → banners (reopen during late signup)
              This section is now purely the form config surface. */}

          {/* Form config — panel manages its own surface (v0.50d-5d). */}
          <FormConfigPanel eventId={eventId} isAdmin={isAdmin} />

          {/* Group preferences toggle */}
          {isAdmin && (
            <div
              className="card-surface-solid rounded-2xl p-4"
              style={{ border: '1px solid var(--card-border)' }}
            >
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={event?.settings?.enable_group_preferences || false} onChange={toggleGroupPreferences}
                  className="h-4 w-4 rounded accent-steel-blue dark:accent-gold" />
                <div>
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {t('event.enable_preferences')}
                  </span>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {t('event.enable_preferences.hint')}
                  </p>
                </div>
              </label>
            </div>
          )}

          {/* Style customiser */}
          <div
            className="card-surface-solid rounded-2xl p-4"
            style={{ border: '1px solid var(--card-border)' }}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <h3 className="font-heading font-bold" style={{ color: 'var(--text-primary)' }}>
                  {t('event.customise_appearance')}
                </h3>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                  {t('event.customise_appearance.hint')}
                </p>
              </div>
              <button onClick={() => setShowStyler(true)}
                className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 shrink-0">
                {t('event.customise_open')}
              </button>
            </div>
          </div>

          {/* Email settings */}
          {isAdmin && (
            <div
              className="card-surface-solid rounded-2xl p-5"
              style={{ border: '1px solid var(--card-border)' }}
            >
              <h3 className="font-heading font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                {t('event.email_confirmation')}
              </h3>
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={event?.settings?.require_email_confirmation || false} onChange={toggleEmailConfirmation}
                    className="h-4 w-4 rounded accent-steel-blue dark:accent-gold" />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                    {t('event.email_require')}
                  </span>
                </label>
                <div>
                  <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('event.email_from')}
                  </label>
                  <input type="text" value={emailFrom} onChange={e => setEmailFrom(e.target.value)}
                    placeholder={t('event.email_from_placeholder')} className={inputClass} />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('event.email_reply_to')}
                  </label>
                  <input type="email" value={emailReplyTo} onChange={e => setEmailReplyTo(e.target.value)}
                    placeholder={t('event.email_reply_to_placeholder')} className={inputClass} />
                </div>
                <div className="flex gap-2 items-center flex-wrap">
                  <button onClick={handleSaveEmail} disabled={emailSaving}
                    className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 transition-colors">
                    {emailSaved ? `✓ ${t('event.email_saved')}` : emailSaving ? t('common.saving') : t('event.email_save')}
                  </button>
                  <button onClick={handleTestEmail} disabled={testing}
                    className="text-xs font-semibold px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
                    style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
                    {testing ? t('event.email_sending') : t('event.email_test')}
                  </button>
                </div>
                {emailError && (
                  <p className="text-xs" style={{ color: 'var(--alert-burgundy)' }}>{formatErrorMessage(emailError, t).primary}</p>
                )}
                {testResult && (
                  <p className="text-xs" style={{ color: 'var(--text-subtle)' }}>{testResult}</p>
                )}
                {/* SMTP notice — uses a gentle attention tone (Burgundy-tinted),
                    not Tailwind amber (which doesn't render properly in dark). */}
                <div
                  className="rounded-card p-3 mt-2"
                  style={{
                    background: 'rgba(128,0,32,0.06)',
                    border: '1px solid rgba(128,0,32,0.15)',
                  }}
                >
                  <p className="text-xs font-semibold" style={{ color: 'var(--alert-burgundy)' }}>
                    {t('event.smtp_notice')}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                    {t('event.smtp_notice.hint')}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Sharing — last in registration */}
          <div
            className="card-surface-solid rounded-2xl p-5"
            style={{ border: '1px solid var(--card-border)' }}
          >
            <h3 className="font-heading font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
              {t('event.share.title')}
            </h3>
            <SharePanel eventId={eventId} event={event} />
          </div>
        </div>
      )}

      {/* ─── SETUP: EXPORT ─── */}
      {/* ─── NO ACCESS — friendly placeholder for staff with no perms.
            Reachable via getLandingForUser → 'no-access' or via direct
            URL ?section=no-access. The Refresh button also re-fetches
            staff permissions (v0.50d-4) in case an admin just updated
            them while the user was on this page. */}
      {section === 'no-access' && (() => {
        // v0.70d-2a (R12): derive the copy variant — pick the right
        // story for the situation rather than one-copy-fits-all.
        // v0.70d-3c-11: added 'organise_not_yet' for organise-only
        // staff in SETUP phase ("the board opens once registration
        // starts"), and fixed G5 — the original hasOnlyCheckin check
        // omitted `marks` from the exclusion list, so a staff with
        // both checkin:write and marks:write would have classified as
        // checkin-only. Marks added below.
        const hasOnlyCheckin = isStaff
          && !!staffPerms.checkin
          && !staffPerms.people
          && !staffPerms.organise
          && !staffPerms.reports
          && !staffPerms.marks;
        const hasOnlyOrganise = isStaff
          && !!staffPerms.organise
          && !staffPerms.people
          && !staffPerms.checkin
          && !staffPerms.reports
          && !staffPerms.marks;
        const isPreEvent = phase === PHASE.SETUP || phase === PHASE.REGISTRATION;
        let variant;
        if (hasOnlyCheckin && isPreEvent) {
          variant = 'checkin_not_yet';
        } else if (hasOnlyOrganise && phase === PHASE.SETUP) {
          // Organise staff during REGISTRATION already lands on the
          // organise board (perms admit them); only SETUP routes them
          // to no-access, and the dedicated copy reads better than
          // the generic 'unassigned' message.
          variant = 'organise_not_yet';
        } else {
          variant = 'unassigned';
        }
        return (
          <NoPermissionPage
            eventName={event?.name}
            variant={variant}
            onRefresh={async () => { await refreshStaffContext(); await loadData(); }}
            onSignOut={() => { logout(); navigate('/login'); }}
          />
        );
      })()}

      {/* ─── SETUP: STAFF ─── */}
      {section === 'staff' && (
        <div className="max-w-2xl">
          <EventAssignmentsPanel eventId={eventId} isAdmin={isAdmin} />
        </div>
      )}

      {/* ─── MARKS ─── v0.50f: staff with marks permission can also access */}
      {section === 'marks' && (
        <div className="max-w-2xl">
          <MarksPanel
            eventId={eventId}
            isAdmin={isAdmin}
            currentUserId={userId}
            marksPerm={isAdmin ? 'write' : (staffPerms.marks || '')}
          />
        </div>
      )}

      {notesFor && <NotesModal entityType={notesFor.type} entityId={notesFor.id} entityName={notesFor.name} onClose={() => { setNotesFor(null); notesApi.counts(eventId).then(setNoteCounts).catch(() => {}); }} isAdmin={isAdmin} />}
      {showRestore && <RestoreModal onClose={() => setShowRestore(false)} onDone={() => { setShowRestore(false); navigate('/admin/events'); }} />}
      {showStyler && <StyleCustomiser eventId={eventId} event={event} onSave={async (styleData) => {
        try {
          const settings = { ...(event.settings || {}), style: styleData };
          const updated = await eventsApi.update(eventId, { settings });
          setEvent(updated);
        } catch (err) { setError(err); }
      }} onClose={() => setShowStyler(false)} />}
      {/* v0.50g-2: Event delete confirmation. Type-to-confirm + scope
          preview + optional backup-first nudge. Reuses StrongDeleteConfirm
          from the marks system; the warning area carries a backup link. */}
      {/* v0.50i: Archive/Unarchive plain confirm modal. Reversible action,
          so a simple two-button dialog suffices — no type-to-confirm. */}
      {showArchiveConfirm && event && (
        <ArchiveConfirm
          open={true}
          event={event}
          busy={archiving}
          onConfirm={handleArchiveToggle}
          onCancel={() => { if (!archiving) setShowArchiveConfirm(false); }}
        />
      )}
      {showDeleteConfirm && event && (
        <StrongDeleteConfirm
          open={true}
          title={t('event.delete.confirm_title')}
          itemLabel={t('event.delete.item_label')}
          itemName={event.name}
          assigneeCount={participantList?.length || 0}
          assigneeNames={(participantList || []).slice(0, 10).map(p => `${p.first_name || ''} ${p.last_name || ''}`.trim() || '—')}
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
          onCancel={() => { if (!deleting) setShowDeleteConfirm(false); }}
        />
      )}
      <ConfirmOverlay />
    </div>
  );
}
