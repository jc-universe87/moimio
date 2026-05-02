import { useState, useEffect, useRef, useMemo } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { events as eventsApi, marks as marksApi } from '../services/api';
import { useAuth, getRoleForEvent } from '../hooks/useAuth';
import { useDateFormat } from '../hooks/useDateFormat';
import { useI18n } from '../hooks/useI18n';
import { getEventPhase, PHASE } from '../services/phase';
import EventRowMenu from '../components/EventRowMenu';
import ArchiveConfirm from '../components/ArchiveConfirm';
import StrongDeleteConfirm from '../components/StrongDeleteConfirm';
import EmptyState from '../components/EmptyState';
import WelcomePanel from '../components/WelcomePanel';

import TranslatedError from '../components/TranslatedError';
/**
 * EventsPage — admin/staff landing page. v0.51 structure.
 *
 * Changes from v0.50t:
 *   - Paired header button: [+ New event | ↑ From backup]. Restore links
 *     to /admin/backup (existing flow).
 *   - Segmented filter: [Active] [Past] [Archived]. Active is the default.
 *     Only one tab's cards render at a time. Tab persists in URL
 *     (?tab=active|past|archived) so post-archive navigation lands right.
 *   - Per-row ⋯ menu with Duplicate / Archive (or Unarchive) / Delete.
 *     Archive/Delete lift the existing confirm modals (ArchiveConfirm
 *     component is new, StrongDeleteConfirm already reusable).
 *   - Archived tab is Super-Admin only and hidden when count = 0 for
 *     non-super-admin users.
 *   - Footer hint about archive/delete living on Details page removed —
 *     no longer true.
 *
 * Archive grouping logic unchanged: is_archived rows go to Archived
 * regardless of date; otherwise, end_date < today → Past, else Active.
 */
export default function EventsPage() {
  const [eventList, setEventList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  // v0.70d-2e-1 (S5): create form is name-only — duplicates of the
  // Details card (description, location, start_date, end_date) are
  // dropped here and asked once on the SetupHub Details card. Mark
  // import stays — it's adjacent to event-setup and has no other
  // entry point before SetupHub loads. New events land in SetupHub
  // with Details auto-opened.
  const [form, setForm] = useState({ name: '' });
  const [copyMarks, setCopyMarks] = useState(false);
  const [copyMarksSourceId, setCopyMarksSourceId] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState(null);

  // v0.51: row-menu confirm state.
  const [archiveTarget, setArchiveTarget] = useState(null); // event | null
  const [archiving, setArchiving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);   // event | null
  const [deleting, setDeleting] = useState(false);

  // v0.51: ephemeral banner (no global toast system in the codebase;
  // same inline pattern AllocationBoard uses).
  const [toast, setToast] = useState(null);
  const toastTimer = useRef(null);
  const showToast = (msg, type = 'info') => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast({ msg, type });
    toastTimer.current = setTimeout(() => setToast(null), 3000);
  };
  useEffect(() => () => { if (toastTimer.current) clearTimeout(toastTimer.current); }, []);

  const createFormRef = useRef(null);
  const { user, staffContext, logout } = useAuth();
  const { formatDate } = useDateFormat();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const isAdmin = user?.role === 'super_admin' || !!user?.can_create_events;
  const isStaff = user?.role === 'staff';
  const isSuperAdmin = user?.role === 'super_admin';

  // v0.51: tab state in URL (?tab=active|past|archived). Default 'active'.
  const urlTab = searchParams.get('tab');
  const tab = (urlTab === 'past' || urlTab === 'archived') ? urlTab : 'active';
  const setTab = (next) => {
    setSearchParams(prev => {
      const np = new URLSearchParams(prev);
      if (next === 'active') np.delete('tab'); else np.set('tab', next);
      return np;
    }, { replace: true });
  };

  useEffect(() => { loadEvents(); }, []);
  useEffect(() => {
    if (showCreate && createFormRef.current) {
      createFormRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [showCreate]);

  const loadEvents = async () => {
    try {
      const data = await eventsApi.list();
      setEventList(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      // v0.70d-2e-1 (S5): payload is name-only. Backend defaults
      // remaining fields to null/empty; SetupHub Details card asks
      // for them once.
      const payload = { name: form.name };
      const newEvent = await eventsApi.create(payload);
      if (copyMarks && copyMarksSourceId) {
        try {
          await marksApi.importFrom(newEvent.id, copyMarksSourceId);
        } catch (err) {
          console.warn('Mark import on create failed:', err);
        }
      }
      setShowCreate(false);
      setForm({ name: '' });
      setCopyMarks(false);
      setCopyMarksSourceId('');
      // v0.70d-2e-1 (E3): if the user created the event from the
      // Past or Archived tab, return them to Active before navigating
      // — when they come back to EventsPage later (via sidebar nav),
      // they should land on Active where the new event lives, not
      // the tab they happened to be on at create time.
      if (tab !== 'active') {
        setTab('active');
      }
      navigate(`/admin/events/${newEvent.id}`);
    } catch (err) {
      setError(err);
    } finally {
      setCreating(false);
    }
  };

  // ─── Row menu action handlers ───
  const handleRowPin = async (event) => {
    // v0.70d-3c-9: toggle event.settings.pinned via the events PATCH
    // endpoint. settings JSONB merges client-side: copy current
    // settings, flip pinned, send the merged object. Re-loads the
    // events list to get the updated sort order.
    try {
      const newSettings = { ...(event.settings || {}), pinned: !event.settings?.pinned };
      await eventsApi.update(event.id, { settings: newSettings });
      await loadEvents();
    } catch (err) {
      setError(err);
    }
  };

  const handleRowDuplicate = (event) => {
    navigate(`/admin/events/duplicate/${event.id}`);
  };

  const handleRowArchiveConfirm = async () => {
    if (!archiveTarget) return;
    setArchiving(true);
    const wasArchived = !!archiveTarget.is_archived;
    try {
      if (wasArchived) {
        await eventsApi.unarchive(archiveTarget.id);
      } else {
        await eventsApi.archive(archiveTarget.id);
      }
      setArchiveTarget(null);
      await loadEvents();
      showToast(
        wasArchived
          ? (t('events.unarchived.toast'))
          : (t('events.archived.toast')),
        'success',
      );
    } catch (err) {
      setError(err);
    } finally {
      setArchiving(false);
    }
  };

  const handleRowDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await eventsApi.delete(deleteTarget.id);
      setDeleteTarget(null);
      await loadEvents();
    } catch (err) {
      setError(err);
    } finally {
      setDeleting(false);
    }
  };

  // ─── Grouping + filtering ───
  const todayYmd = useMemo(() => {
    const d = new Date();
    return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
  }, []);

  const isPast = (event) => {
    if (!event.end_date) return false;
    const [y, m, d] = event.end_date.split('-').map(Number);
    const endYmd = y * 10000 + m * 100 + d;
    return endYmd < todayYmd;
  };

  const needle = search.trim().toLowerCase();
  const matchesSearch = (event) => !needle || (event.name || '').toLowerCase().includes(needle);

  const { activeEvents, pastEvents, archivedEvents } = useMemo(() => {
    const active = [];
    const past = [];
    const archived = [];
    for (const e of eventList) {
      if (!matchesSearch(e)) continue;
      if (e.is_archived) { archived.push(e); continue; }
      (isPast(e) ? past : active).push(e);
    }
    active.sort((a, b) => {
      // v0.70d-3c-9: pinned events float to top of active list. Pin
      // is a per-event flag in settings.pinned. Below the pinned ones,
      // the standard date-descending sort still applies.
      const aPinned = !!a.settings?.pinned;
      const bPinned = !!b.settings?.pinned;
      if (aPinned !== bPinned) return aPinned ? -1 : 1;
      if (a.start_date && b.start_date) return a.start_date < b.start_date ? 1 : -1;
      if (a.start_date) return -1;
      if (b.start_date) return 1;
      return (b.created_at || '').localeCompare(a.created_at || '');
    });
    past.sort((a, b) => (b.end_date || '').localeCompare(a.end_date || ''));
    archived.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
    return { activeEvents: active, pastEvents: past, archivedEvents: archived };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventList, needle, todayYmd]);

  const visibleEvents =
    tab === 'archived' ? archivedEvents :
    tab === 'past'     ? pastEvents :
                         activeEvents;

  const showArchivedTab = isSuperAdmin || archivedEvents.length > 0;

  const phaseStyle = (event) => {
    if (event.is_archived) {
      return { bg: 'rgba(128,0,32,0.10)', color: 'var(--alert-burgundy)', label: t('events.group.archived') };
    }
    if (isPast(event)) {
      return { bg: 'var(--neutral-tint)', color: 'var(--text-subtle)', label: t('phase.past') };
    }
    const phase = getEventPhase(event);
    if (phase === PHASE.EVENT) {
      return { bg: 'var(--accent-tint)', color: 'var(--io-accent)', label: t('phase.event') };
    }
    if (phase === PHASE.REGISTRATION) {
      return { bg: 'var(--pending-tint)', color: 'var(--pending-color)', label: t('phase.registration') };
    }
    return { bg: 'var(--neutral-tint)', color: 'var(--text-muted)', label: t('phase.setup') };
  };

  const metricFor = (event) => {
    const participantCount = event.participant_count ?? 0;
    const checkedIn = event.checked_in_count ?? 0;

    if (isPast(event) || event.is_archived) {
      // v0.70d-2d-2 (E11): if check-in was actually used (any
      // participant was checked in), show "who came" — that's the
      // semantically correct measure for a past event. If no
      // check-ins ever happened (events that pre-date check-in
      // tracking, or organisers who didn't use it), fall back to
      // total registrations with a label that softens to "Angemeldet"
      // so the number's meaning is always explicit. Heuristic:
      // checkedIn > 0 ⇒ check-in was used. checkedIn === 0 with
      // participants registered ⇒ no check-in tracking.
      if (checkedIn > 0) {
        return {
          value: String(checkedIn),
          label: t('events.metric.attendees'),
        };
      }
      return {
        value: participantCount > 0 ? String(participantCount) : '—',
        label: t('events.metric.registered_past'),
      };
    }

    const phase = getEventPhase(event);
    if (phase === PHASE.EVENT) {
      return {
        value: participantCount > 0 ? `${checkedIn} / ${participantCount}` : '—',
        label: t('events.metric.checked_in'),
      };
    }
    if (phase === PHASE.REGISTRATION) {
      return {
        value: String(participantCount),
        label: t('events.metric.registered'),
      };
    }
    const confirmed = (event.details_confirmed ? 1 : 0) + (event.registration_confirmed ? 1 : 0);
    return {
      value: `${confirmed} / 2`,
      label: t('events.metric.cards_confirmed'),
    };
  };

  const renderCard = (event) => {
    const style = phaseStyle(event);
    const metric = metricFor(event);
    const dim = isPast(event) || event.is_archived;

    const canDuplicate = isAdmin;
    const canArchive = isSuperAdmin;
    const canDelete = isSuperAdmin;

    return (
      <div
        key={event.id}
        className="card-surface-solid relative block rounded-2xl px-4 py-3 transition-colors hover:bg-black/[0.02] dark:hover:bg-white/[0.04]"
        style={{ border: '1px solid var(--card-border)' }}
      >
        {event.settings?.pinned && !event.is_archived && (
          <div className="flex items-center gap-1 mb-1.5 text-xs font-semibold" style={{ color: 'var(--io-accent)' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2L9 7l-7 1 5 5-1 7 6-3 6 3-1-7 5-5-7-1z" />
            </svg>
            <span>{t('events.pinned.label')}</span>
          </div>
        )}
        <Link to={`/admin/events/${event.id}`} className="block">
          <div className="flex items-center justify-between gap-3 pr-10">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-heading font-bold truncate" style={{ color: dim ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                  {event.name}
                </h3>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 uppercase tracking-caps"
                  style={{ background: style.bg, color: style.color }}>
                  {style.label}
                </span>
                {user?.role === 'staff'
                  && getRoleForEvent(staffContext, event.id) === 'event_admin' && (
                  <span
                    className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 uppercase tracking-caps"
                    style={{
                      background: 'rgba(70, 130, 180, 0.12)',
                      color: 'var(--io-accent)',
                      border: '1px solid rgba(70, 130, 180, 0.25)',
                    }}
                    title={t('event.admin_pill.title')}
                  >
                    {t('event.admin_pill.label')}
                  </span>
                )}
              </div>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                {/* v0.70d-2d-2 (E9): no fallback when dates aren't set —
                    empty is quieter than filler. The location, when set,
                    becomes the leading element instead of a subordinate
                    suffix. */}
                {event.start_date
                  ? `${formatDate(event.start_date)}${event.end_date ? ` – ${formatDate(event.end_date)}` : ''}${event.location ? ` · ${event.location}` : ''}`
                  : (event.location || '')}
              </p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm font-semibold" style={{ color: dim ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                {metric.value}
              </p>
              <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                {metric.label}
              </p>
            </div>
          </div>
        </Link>

        {/* ⋯ menu — absolutely positioned outside the <Link>. */}
        <div className="absolute top-1/2 -translate-y-1/2 right-2">
          <EventRowMenu
            canPin={isSuperAdmin}
            onPin={() => handleRowPin(event)}
            event={event}
            canDuplicate={canDuplicate}
            canArchive={canArchive}
            canDelete={canDelete}
            onDuplicate={() => handleRowDuplicate(event)}
            onArchive={() => setArchiveTarget(event)}
            onDelete={() => setDeleteTarget(event)}
          />
        </div>
      </div>
    );
  };

  const existingEvents = eventList;

  const tabs = [
    { key: 'active', label: t('events.tab.active'), count: activeEvents.length },
    { key: 'past',   label: t('events.tab.past'),   count: pastEvents.length   },
  ];
  if (showArchivedTab) {
    tabs.push({ key: 'archived', label: t('events.tab.archived'), count: archivedEvents.length });
  }

  return (
    <div>
      {toast && (
        <div className="fixed top-[calc(1rem+env(safe-area-inset-top))] right-[calc(1rem+env(safe-area-inset-right))] z-50 px-4 py-2.5 rounded-xl shadow-lg text-sm font-medium"
          style={{
            background:
              toast.type === 'success' ? 'var(--io-accent)' :
              toast.type === 'error'   ? 'var(--alert-burgundy)' :
              'var(--card-bg-solid)',
            color:
              toast.type === 'success' ? 'var(--on-accent)' :
              toast.type === 'error'   ? '#fff' :
              'var(--text-primary)',
            border: toast.type === 'success' || toast.type === 'error' ? 'none' : '1px solid var(--card-border)',
          }}>
          {toast.msg}
        </div>
      )}

      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="font-heading text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {t('events.title')}
        </h1>
        {isAdmin && (
          <div className="inline-flex rounded-card overflow-hidden" style={{ border: '1px solid var(--card-border)' }}>
            <button
              type="button"
              onClick={() => {
                setShowCreate(!showCreate);
                if (!showCreate) {
                  setTimeout(() => createFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
                }
              }}
              title={t('events.header.new_tooltip')}
              className="text-sm font-semibold px-4 py-2 bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors"
            >
              {showCreate ? t('common.cancel') : t('events.new')}
            </button>
            <Link
              to="/admin/backup"
              title={t('events.header.backup_tooltip')}
              className="text-sm font-medium px-4 py-2 hover:bg-black/5 dark:hover:bg-white/10 transition-colors flex items-center"
              style={{ color: 'var(--text-muted)', borderLeft: '1px solid var(--card-border)' }}
            >
              ↑ {t('events.header.from_backup')}
            </Link>
          </div>
        )}
      </div>

      <TranslatedError err={error} />

      {showCreate && (
        <div ref={createFormRef}
          className="card-surface-solid rounded-2xl p-5 mb-6"
          style={{ border: '1px solid var(--card-border)' }}>
          <h2 className="font-heading font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
            {t('events.create.title')}
          </h2>
          {/* v0.70d-2e-1 (S5): name-only form. Description, location,
              and dates moved to the SetupHub Details card (where they
              already lived as duplicates) — the organiser fills them
              once. Mark import stays here because it's adjacent to
              event-setup and has no entry point before SetupHub
              loads. */}
          <p className="text-xs mb-3" style={{ color: 'var(--text-subtle)' }}>
            {t('events.create.name_only_hint')}
          </p>
          <form onSubmit={handleCreate} className="space-y-3">
            <input type="text" placeholder={t('events.name') + ' *'} value={form.name}
              onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
              required
              autoFocus
              className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />

            {existingEvents.length > 0 && (
              <div className="space-y-2 pt-1">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input type="checkbox" checked={copyMarks}
                    onChange={e => setCopyMarks(e.target.checked)}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold mt-0.5" />
                  <div className="min-w-0">
                    <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                      {t('events.create.copy_marks')}
                    </span>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                      {t('events.create.copy_marks.hint')}
                    </p>
                  </div>
                </label>
                {copyMarks && (
                  <select
                    value={copyMarksSourceId}
                    onChange={e => setCopyMarksSourceId(e.target.value)}
                    className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
                  >
                    <option value="">{t('events.create.copy_marks.select')}</option>
                    {existingEvents.map(e => (
                      <option key={e.id} value={e.id}>{e.name}</option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <button type="submit" disabled={creating || (copyMarks && !copyMarksSourceId)}
              className="text-sm font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 transition-colors">
              {creating ? t('events.creating') : t('events.create.title')}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <p className="text-gray-400 text-sm">{t('common.loading')}</p>
      ) : eventList.length === 0 && isStaff ? (
        <div
          className="card-surface-solid rounded-2xl p-8 max-w-md mx-auto text-center"
          style={{ border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}
        >
          <div className="mx-auto mb-4 flex items-center justify-center" style={{ width: 64, height: 64 }}>
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.6"
              strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ color: 'var(--text-subtle)' }}>
              <rect x="14" y="22" width="36" height="28" rx="3" />
              <path d="M14 30h12l3 5h6l3-5h12" />
              <line x1="22" y1="14" x2="42" y2="14" opacity="0.5" />
              <line x1="26" y1="10" x2="38" y2="10" opacity="0.3" />
            </svg>
          </div>
          <h1 className="font-heading font-bold text-xl mb-2" style={{ color: 'var(--text-primary)' }}>
            {t('staff_waiting.title')}
          </h1>
          <p className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>{t('staff_waiting.body')}</p>
          <p className="text-xs mb-6" style={{ color: 'var(--text-subtle)' }}>{t('no_perm.unassigned.contact_hint')}</p>
          <div className="flex gap-2 justify-center">
            <button type="button" onClick={loadEvents}
              className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
              ↻ {t('no_perm.refresh')}
            </button>
            <button type="button" onClick={() => { logout(); navigate('/login'); }}
              className="text-xs font-medium px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
              style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
              {t('no_perm.sign_out')}
            </button>
          </div>
        </div>
      ) : eventList.length === 0 ? (
        <WelcomePanel
          isAdmin={isAdmin}
          onCta={() => {
            setShowCreate(true);
            setTimeout(() => createFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
          }}
        />
      ) : (
        <>
          {/* v0.70d-2e-1 (E4): collapse search bar + tab bar while
              create-form is expanded. They aren't useful while the
              user's task is "type the name and submit", and on mobile
              their stacked height pushed the event list entirely off-
              screen. Reverses on Cancel or successful create. */}
          {!showCreate && (
            <>
              <div className="mb-4">
                <input
                  type="text"
                  placeholder={t('events.search_placeholder')}
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
                />
              </div>

              {/* Segmented tab bar — v0.51. */}
              <div className="mb-4 inline-flex rounded-card overflow-hidden" style={{ border: '1px solid var(--card-border)' }}>
                {tabs.map((tt, i) => {
                  const selected = tab === tt.key;
                  return (
                    <button
                      key={tt.key}
                      type="button"
                      onClick={() => setTab(tt.key)}
                      className="text-xs font-semibold px-3 py-1.5 transition-colors"
                      style={{
                        background: selected ? 'var(--io-accent)' : 'transparent',
                        // v0.53.1: use `--card-bg-solid` not hardcoded '#fff'. Matches
                        // the pattern in PeopleTable / AllocationBoard for text on the
                        // accent colour. Ensures readable contrast in BOTH modes:
                        // light → white text on Steel Blue; dark → dark card bg on Gold.
                        // Previously '#fff' on dark mode Gold was effectively illegible.
                        color: selected ? 'var(--card-bg-solid)' : 'var(--text-muted)',
                        borderLeft: i === 0 ? 'none' : '1px solid var(--card-border)',
                      }}
                    >
                      {tt.label} · {tt.count}
                    </button>
                  );
                })}
              </div>
            </>
          )}

          <div>
            {visibleEvents.length === 0 ? (
              <EmptyState
                compact
                title={needle
                  ? (t('events.tab.empty_search.title'))
                  : (t('events.tab.empty.title'))}
                hint={needle
                  ? (t('events.tab.empty_search.hint'))
                  : (t('events.tab.empty.hint'))}
              />
            ) : (
              <div className="space-y-2">
                {visibleEvents.map(renderCard)}
              </div>
            )}
          </div>
        </>
      )}

      <ArchiveConfirm
        open={!!archiveTarget}
        event={archiveTarget}
        busy={archiving}
        onConfirm={handleRowArchiveConfirm}
        onCancel={() => { if (!archiving) setArchiveTarget(null); }}
      />
      {deleteTarget && (
        <StrongDeleteConfirm
          open={true}
          title={t('event.delete.confirm_title')}
          itemLabel={t('event.delete.item_label')}
          itemName={deleteTarget.name}
          assigneeCount={deleteTarget.participant_count ?? 0}
          warning={t('event.delete.warning')}
          onConfirm={handleRowDeleteConfirm}
          onCancel={() => { if (!deleting) setDeleteTarget(null); }}
        />
      )}
    </div>
  );
}
