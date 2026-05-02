/**
 * CheckinOverlayPage — fullscreen check-in mode for an event (§5).
 *
 * Routed at /admin/events/:eventId/checkin — a SIBLING of the main admin
 * layout, not a nested child. That means no sidebar, no event header chrome;
 * just a minimal top bar (event name + exit) and the full check-in surface.
 *
 * Admin users arrive here by clicking "Enter check-in mode →" from the
 * Event-phase board. They see a "Back to board" exit button (top-left).
 *
 * Staff users with checkin permission are auto-redirected here on load
 * (by EventDetailPage) and have no exit button — this IS their permitted view.
 *
 * Content: reuses the existing CheckInPanel component (the same surface
 * previously at ?section=checkin). Wrapping it in fullscreen chrome keeps
 * feature parity with v45 and lets us evolve the UI separately later.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, Navigate } from 'react-router-dom';
import { events as eventsApi, participants as participantsApi, notes as notesApi } from '../services/api';
import { useAuth, getPermsForEvent, getRoleForEvent } from '../hooks/useAuth';
import { useI18n } from '../hooks/useI18n';
import CheckInPanel from '../components/CheckInPanel';
import NotesModal from '../components/NotesModal';
import ThemeToggle from '../components/ThemeToggle';
import TranslatedError from '../components/TranslatedError';

export default function CheckinOverlayPage() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const { user, staffContext, logout } = useAuth();
  const { t } = useI18n();

  // v0.50j: per-event admin check (Super Admin or per-event assignment).
  const isAdmin = user?.role === 'super_admin'
    || getRoleForEvent(staffContext, eventId) === 'event_admin';
  const isStaff = user?.role === 'staff';
  // v0.50e-1c: scope staff permissions to the event on screen, so staff
  // assigned to multiple events see the right permissions for each.
  const staffPerms = isStaff ? getPermsForEvent(staffContext, eventId) : {};
  const userId = user?.id;
  // v0.83 #12: checkin perm is now an object {access, pre_event}.
  // Read .access for both shapes; truthy for legacy "write" too.
  const _checkinPerm = staffPerms.checkin;
  const _hasCheckinAccess = (_checkinPerm && typeof _checkinPerm === 'object')
    ? !!_checkinPerm.access
    : !!_checkinPerm;
  const canViewColumns = isAdmin || (isStaff && _hasCheckinAccess);
  const canWriteCheckin = isAdmin || (isStaff && _hasCheckinAccess);

  const [event, setEvent] = useState(null);
  const [participantList, setParticipantList] = useState([]);
  const [noteCounts, setNoteCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notesFor, setNotesFor] = useState(null);

  const loadData = async () => {
    try {
      const [eventData, participantData] = await Promise.all([
        eventsApi.get(eventId),
        participantsApi.list(eventId),
      ]);
      setEvent(eventData);
      setParticipantList(participantData);
      notesApi.counts(eventId).then(setNoteCounts).catch(() => {});
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [eventId]);

  // Staff without checkin permission shouldn't be here. Kick them back
  // to the main event page and let the normal admin flow route them.
  if (isStaff && !_hasCheckinAccess) {
    return <Navigate to={`/admin/events/${eventId}`} replace />;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--app-bg)' }}>
        <p style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>
      </div>
    );
  }
  if (error && !event) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: 'var(--app-bg)' }}>
        <TranslatedError err={error} className="text-sm rounded-card p-3 max-w-md" />
      </div>
    );
  }
  if (!event) return null;

  // Admins see the "Back to board" exit. Staff see no exit (this is
  // their landing; they stay here for the duration of their shift).
  const showExit = isAdmin;

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--app-bg)' }}>
      {/* Minimal top bar — event name + exit (admin) / theme toggle.
          v0.59a: header top padding includes safe-area-inset-top so the
          bar clears the iOS notch when the app is installed. Bottom
          padding and border stay at their original values. */}
      <header
        className="border-b px-4 pt-[calc(0.625rem+env(safe-area-inset-top))] pb-2.5 flex items-center gap-3"
        style={{ borderColor: 'var(--card-border)', backgroundColor: 'var(--card-bg-solid)' }}
      >
        {showExit && (
          <button
            type="button"
            onClick={() => navigate(`/admin/events/${eventId}`)}
            className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            ← {t('checkin.mode.back')}
          </button>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
            {t('checkin.mode.title')}
          </p>
          <h1 className="font-heading font-bold text-sm truncate" style={{ color: 'var(--text-primary)' }}>
            {event.name}
          </h1>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => { logout(); navigate('/login'); }}
            className="text-xs font-medium px-2 py-1 rounded-card hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap"
            style={{ color: 'var(--text-subtle)' }}
          >
            {t('nav.sign_out')}
          </button>
        </div>
      </header>

      {/* Check-in surface
          v0.70d-2d-1 (C4): bottom padding includes safe-area-inset-bottom
          so the last visible card isn't clipped behind iOS Safari's
          toolbar. Mirrors the header's safe-area-inset-top pattern. */}
      <main className="px-3 md:px-5 pt-3 md:pt-5 pb-[calc(0.75rem+env(safe-area-inset-bottom))] md:pb-[calc(1.25rem+env(safe-area-inset-bottom))]">
        <div className="bg-white dark:bg-white/5 rounded-xl shadow-sm border border-gray-100 dark:border-white/10 overflow-hidden">
          <CheckInPanel
            eventId={eventId}
            participantList={participantList}
            isAdmin={canWriteCheckin}
            canCreateColumns={isAdmin}
            canViewColumns={canViewColumns}
            marksPerm={isAdmin ? 'write' : (staffPerms.marks || '')}
            userId={userId}
            noteCounts={noteCounts}
            onOpenNotes={(p) => setNotesFor({ type: 'participant', id: p.id, name: `${p.first_name} ${p.last_name}` })}
          />
        </div>
      </main>

      {notesFor && (
        <NotesModal
          entityType={notesFor.type}
          entityId={notesFor.id}
          entityName={notesFor.name}
          onClose={() => {
            setNotesFor(null);
            notesApi.counts(eventId).then(setNoteCounts).catch(() => {});
          }}
          isAdmin={isAdmin}
        />
      )}
    </div>
  );
}
