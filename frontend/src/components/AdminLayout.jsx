import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth, getPermsForEvent, getRoleForEvent } from '../hooks/useAuth';
import { useCapabilities } from '../hooks/useCapabilities';
import UserPreferencesPanel from './UserPreferencesPanel';
import WelcomePanel from './WelcomePanel';
import ThemeToggle from './ThemeToggle';
import InstallPrompt from './InstallPrompt';
import UpdatePrompt from './UpdatePrompt';
import { useI18n } from '../hooks/useI18n';
import { useEventPhase, PHASE } from '../hooks/useEventPhase';
import { events as eventsApi } from '../services/api';
import {
  IconDetails, IconRegistrationForm,
  IconMarks, IconStaff,
} from './icons/MoreIcons';

// v0.58i: auto-populated at build time from frontend/package.json
// `moimioVersion` field via vite.config.js define. Fallback "dev" keeps
// the UI functional when the constant isn't defined (e.g. test runs).
const MOIMIO_VERSION = typeof __MOIMIO_VERSION__ !== 'undefined' ? __MOIMIO_VERSION__ : 'dev';

export default function AdminLayout() {
  const { user, staffContext, logout } = useAuth();
  const { capabilities } = useCapabilities();
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPrefs, setShowPrefs] = useState(false);
  const [showLegal, setShowLegal] = useState(false);
  // v0.99f: manual "check for new version" affordance in the legal modal.
  // Pre-fix, the only user-facing update path was the auto-detected
  // UpdatePrompt toast — when that didn't fire (browser-specific SW
  // quirks, HTTP-cached SW script, mobile lifecycle weirdness), users
  // had no way to force-pull a new build. The button below clears all
  // service-worker caches and triggers a hard reload, so the next page
  // load is guaranteed to refetch every asset from the origin. Brief
  // checking-state spinner so a click feels acknowledged before reload.
  const [isCheckingForUpdate, setIsCheckingForUpdate] = useState(false);
  const handleCheckForUpdates = async () => {
    if (isCheckingForUpdate) return;
    setIsCheckingForUpdate(true);
    try {
      // Best-effort: nudge the SW to check for updates first. If a new
      // build is on the server, this triggers the install of a waiting
      // SW. The hard reload that follows then activates it.
      if ('serviceWorker' in navigator) {
        try {
          const reg = await navigator.serviceWorker.getRegistration();
          if (reg) await reg.update();
        } catch { /* ignore */ }
      }
      // Wipe every cache the browser holds for this origin (Workbox
      // precache, runtime caches, anything else). Without this, the
      // reload could be served from cache and miss the new shell.
      if (typeof caches !== 'undefined') {
        try {
          const keys = await caches.keys();
          await Promise.all(keys.map(k => caches.delete(k)));
        } catch { /* ignore */ }
      }
    } finally {
      // Reload regardless of whether the cache cleanup partially
      // failed — a fresh page request is still the right next step,
      // and any partial cache state will be replaced on the next load.
      window.location.reload();
    }
  };
  // v0.70d-2c (R3-C-hybrid): the "View welcome tour" menu item opens
  // WelcomePanel in a fixed overlay. State here rather than inside the
  // sidebar DOM subtree because we want the modal to escape the sidebar's
  // transform + overflow context and cover the whole viewport.
  const [showWelcome, setShowWelcome] = useState(false);

  // v0.70d-2b (R11): backup state + fetch + download handler lived
  // here for the sidebar modal. Modal gone, state gone. The Backup
  // button in the user menu now navigates to /admin/backup (the
  // BackupPage, which owns its own state). One source of truth for
  // backup UI; no more divergent sibling surfaces to keep in sync.

  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 768);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);
  // v50d-2: More menu collapsed by default; persists per-session.
  const [moreOpen, setMoreOpen] = useState(false);

  const isStaff = user?.role === 'staff';
  const isSuperAdmin = user?.role === 'super_admin';
  // v0.50j: EVENT_ADMIN no longer exists as a system role. User-management
  // rights flow from the `can_manage_users` flag, which Super Admin has
  // implicitly. (The previous `isAdmin` variable declared here was unused.)
  const canManageUsers = isSuperAdmin || !!user?.can_manage_users;

  // v0.50d-2a: previously, staff were auto-redirected from /admin to
  // their (singular) assigned event on mount. That worked for single-
  // event staff but trapped multi-event staff — the events list was
  // unreachable because mounting /admin would bounce them straight
  // back. Now staff land on the events list (which is server-scoped to
  // their assigned events as of v0.50c-3c-2c) and pick. Single-event
  // staff see a one-entry list — one extra click, worth it for correctness.
  // The proper multi-event auth context refactor is deferred to v0.50e.

  useEffect(() => {
    const check = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
    };
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  const handleLogout = () => { logout(); navigate('/login'); };
  const closeSidebar = () => { if (isMobile) setSidebarOpen(false); };

  const searchParams = new URLSearchParams(location.search);
  // activeSection — for sidebar highlight. URL param wins; 'organise' is
  // aliased to 'board' for back-compat with v45 URLs. Default when inside
  // an event but no section param: 'board' if Event phase, 'organise'
  // otherwise (which also maps to 'board' but the variable name is clearer).
  const rawSectionParam = searchParams.get('section');
  const normalisedSection = rawSectionParam === 'organise' ? 'board' : rawSectionParam;
  // activeSection is finalised below, after currentPhase is known so we
  // can pick the right default for the current phase's landing.

  const eventMatch = location.pathname.match(/\/admin\/events\/([^/]+)/);
  const insideEvent = !!eventMatch;
  const eventId = eventMatch ? eventMatch[1] : null;

  // Fetch the current event to derive its phase, which drives the
  // phase-conditional sidebar nav (§7.3 "Section nav items (phase-dependent)").
  // Re-fetches when:
  //   - eventId changes (navigation to different event)
  //   - pathname or search change (normal navigation inside event)
  //   - 'moimio:event-changed' window event fires (EventDetailPage / SetupHub
  //     broadcasts this when they locally update event state, e.g. after
  //     opening registration — we'd otherwise show stale sidebar nav).
  const [currentEvent, setCurrentEvent] = useState(null);
  const [refetchNonce, setRefetchNonce] = useState(0);
  useEffect(() => {
    const handler = () => setRefetchNonce(n => n + 1);
    window.addEventListener('moimio:event-changed', handler);
    return () => window.removeEventListener('moimio:event-changed', handler);
  }, []);
  useEffect(() => {
    if (!eventId) { setCurrentEvent(null); return; }
    let cancelled = false;
    eventsApi.get(eventId)
      .then(ev => { if (!cancelled) setCurrentEvent(ev); })
      .catch(() => { if (!cancelled) setCurrentEvent(null); });
    return () => { cancelled = true; };
  }, [eventId, location.pathname, location.search, refetchNonce]);
  const { phase: currentPhase } = useEventPhase(currentEvent);

  const navigateSection = (section) => {
    // v0.50d-4: special '_home' id navigates without a section param so
    // the phase-based landing page fires (Registration landing, board, etc.).
    if (section === '_home') {
      navigate(`/admin/events/${eventId}`);
    } else {
      navigate(`/admin/events/${eventId}?section=${section}`);
    }
    closeSidebar();
  };

  // For staff: only show views they have permission to access.
  // v0.50e-1c: perms are scoped to the event currently shown in the URL.
  // Outside of an event, perms is {} — sidebar shows the events list only.
  const perms = isStaff ? getPermsForEvent(staffContext, eventId) : {};
  // v0.50e-1d: per-category overrides removed. Single organise permission.
  const hasOrganiseAccess = !!perms.organise;
  // v1.0-pre #10: checkin perm is now an object {access, pre_event}.
  // For sidebar gating (item visible when staff has any check-in access)
  // we read access. The pre_event flag matters only for the link on the
  // Registration overview page — sidebar Check-in is unchanged.
  const hasAnyCheckin = (() => {
    const c = perms.checkin;
    if (c && typeof c === 'object') return !!c.access;
    return !!c;
  })();

  // v0.50n: "admin on this event" — Super Admin globally, OR per-event
  // admin via EventUserAssignment. Used for the phase flags below so
  // Staff users who are per-event admins get the same Setup Hub /
  // More menu / primary nav treatment as Super Admins on that event.
  // Previously phase flags gated on `!isStaff` which stranded Staff
  // event-admins with no Setup access to events they created.
  const isEventAdmin = isSuperAdmin
    || (eventId && getRoleForEvent(staffContext, eventId) === 'event_admin');

  const inSetupPhase = insideEvent && currentPhase === PHASE.SETUP && isEventAdmin;
  const inEventPhase = insideEvent && currentPhase === PHASE.EVENT && isEventAdmin;
  // v0.50d-4: declared here (earlier than v0.50d-2's placement) so the
  // primary nav + setupItems logic below can reference it.
  const inRegistrationPhase = insideEvent && currentPhase === PHASE.REGISTRATION && isEventAdmin;

  // Default active section when none is explicit in the URL — depends on
  // phase so the right primary nav item stays highlighted on the phase
  // landing. Registration landing → '_home'; Event landing → 'board'.
  const defaultActive = currentPhase === PHASE.REGISTRATION ? '_home' : 'board';
  const activeSection = normalisedSection
    || (location.pathname.includes('/events/') ? defaultActive : null);

  // Primary nav in Event phase (§4.3): Board / People / Reports. No Check-in
  // for admins — they toggle check-in mode ON the board (v50c-3 work).
  // v0.50d-4: Registration phase now has its own primary nav — the
  // Registration landing is home, People is reachable directly. Check-in
  // is omitted (nothing to check in to yet).
  // v0.50n: `isStaff && !isEventAdmin` — Staff who are NOT per-event
  // admins use permission-based nav; Staff who ARE event admins fall
  // through to the admin branches below and see the full nav for
  // their phase.
  const primaryItems = (isStaff && !isEventAdmin)
    ? [
        perms.people && { id: 'people', label: t('nav.people'), icon: '👥' },
        hasOrganiseAccess && { id: 'organise', label: t('nav.organise'), icon: '📋' },
        hasAnyCheckin && { id: 'checkin', label: t('nav.checkin'), icon: '✓' },
        perms.reports && { id: 'reports', label: t('nav.reports'), icon: '📊' },
        // v0.50f-1: Marks sidebar entry only for staff with write access.
        // Read is implicit (anyone can click a mark dot to see what it means),
        // but there's no value in a dedicated sidebar section without write.
        perms.marks === 'write' && { id: 'marks', label: t('nav.marks'), icon: '⚑' },
      ].filter(Boolean)
    : inEventPhase
    ? [
        // v0.50o: renamed "Board" → "Organise" for phase-consistent naming
        // with Registration (both phases use the OrganiseDashboard as the
        // primary work surface). "Organise" matches Moimio's brand verb
        // (Gather · Organise) and removes the Board/Organise ambiguity
        // where the More menu used to duplicate this entry.
        { id: 'board',   label: t('nav.organise'),   icon: '📋' },
        { id: 'people',  label: t('nav.people'),  icon: '👥' },
        { id: 'reports', label: t('nav.reports'), icon: '📊' },
      ]
    : inRegistrationPhase
    ? [
        { id: '_home',   label: t('nav.registration_home'), icon: '✎' },
        // v0.50o: Organise promoted from More → primary nav during
        // Registration. Organisers routinely start allocating while
        // registration is still open; having one click to get there
        // matters. The alias `organise → board` (v0.50m) routes this
        // id to the OrganiseDashboard component.
        { id: 'organise', label: t('nav.organise'), icon: '📋' },
        { id: 'people',  label: t('nav.people'),  icon: '👥' },
        // v0.50g-2: Reports visible in Registration too. Organisers care
        // most about registration counts DURING registration, so the
        // report surface matters here at least as much as in Event phase.
        { id: 'reports', label: t('nav.reports'), icon: '📊' },
      ]
    : [
        { id: 'people', label: t('nav.people'), icon: '👥' },
        { id: 'organise', label: t('nav.organise'), icon: '📋' },
        { id: 'checkin', label: t('nav.checkin'), icon: '✓' },
      ];

  // Phase-conditional setup nav (§7.3):
  // - Setup phase → ONE "Setup" link that lands on the hub.
  // - Registration phase → hidden; served by More menu (v0.50d-4).
  // - Event phase → hidden; served by More menu (v50d-2).
  // - Other phases → legacy v45 items remain.
  // v0.50n: Staff who are NOT per-event admins keep the empty setupItems
  // (they don't see setup nav). Staff who ARE event admins fall through
  // to the admin phase branches.
  const setupItems = (isStaff && !isEventAdmin)
    ? []
    : inSetupPhase
    ? [] // Hub replaces the list; a single "Setup" link is shown separately below
    : inRegistrationPhase
    ? [] // Served by More menu — avoid duplication (v0.50d-4)
    : inEventPhase
    ? [] // Hidden in Event phase; surfaced via the More menu (v50d-2)
    : [
        ...(canManageUsers ? [{ id: 'staff', label: t('nav.setup.staff') }] : []),
        { id: 'registration', label: t('nav.setup.registration') },
        { id: 'event-details', label: t('nav.setup.event_details') },
        { id: 'marks', label: t('nav.setup.marks') },
      ];

  // v50d-2: "More" menu — surfaces Setup-style items during Registration
  // and Event phases, when the Setup hub is no longer the home. Kept
  // collapsed by default to keep the sidebar focused on primary nav.
  // v0.50n: show to Staff event-admins too, not just Super/System admins.
  // v0.50o: Organise removed from More — promoted to primary nav for both
  // Registration and Event phases. No more duplication (Board in primary
  // + Organise in More pointing to the same component).
  const moreItems = (isEventAdmin && (inRegistrationPhase || inEventPhase))
    ? [
        { id: 'event-details', label: t('nav.more.event_details'), Icon: IconDetails },
        { id: 'registration', label: t('nav.more.registration_setup'), Icon: IconRegistrationForm },
        { id: 'marks', label: t('nav.more.marks'), Icon: IconMarks },
        ...(canManageUsers ? [{ id: 'staff', label: t('nav.more.staff'), Icon: IconStaff }] : []),
      ]
    : [];

  // v50d-2: auto-open More when the active section is one of its children,
  // so the user always sees their current location highlighted in context.
  useEffect(() => {
    if (moreItems.some(it => it.id === activeSection)) {
      setMoreOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSection, moreItems.length]);

  // v0.70d-2c (R3-C-hybrid): welcome-tour modal — ESC dismiss + body
  // scroll lock while open. The Legal modal gets away without these
  // because it's short; welcome tour is scroll-heavy, so a locked
  // body prevents background scroll-bleed on iOS. No-op when
  // !showWelcome, so the hook is always safe to run.
  useEffect(() => {
    if (!showWelcome) return;
    const onKey = (e) => {
      if (e.key === 'Escape') setShowWelcome(false);
    };
    window.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [showWelcome]);

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--app-bg)' }}>
      {isMobile && sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 z-30" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={
        isMobile
          ? `bg-deep-navy dark:bg-sidebar-dark text-white fixed inset-y-0 left-0 z-40 w-56 transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`
          : `bg-deep-navy dark:bg-sidebar-dark text-white shrink-0 transition-all duration-200 ${sidebarOpen ? 'w-56' : 'w-0 overflow-hidden'}`
      }
        aria-hidden={isMobile && !sidebarOpen}
        style={isMobile ? { height: '100vh' } : sidebarOpen ? { position: 'sticky', top: 0, height: '100vh' } : {}}>
        {(sidebarOpen || isMobile) && (
          <div className="flex flex-col min-h-full overflow-y-auto">
            {/* Logo — top padding respects iOS safe-area so the MOIMio
                wordmark clears the notch when app is installed / the
                browser is in viewport-fit=cover mode (v0.59a). */}
            <div className="px-3 pt-[calc(0.625rem+env(safe-area-inset-top))] pb-2.5 border-b border-white/10 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2 min-w-0">
                <img src="/logogram.svg" alt="" className="w-9 h-9 shrink-0" />
                <div className="border-l border-white/12 pl-2 min-w-0">
                  {/* §9.3 Wordmark: MOIM + io (Gold on this dark sidebar). */}
                  <h1 className="font-heading leading-none" style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '0.068em' }}>
                    <span className="text-white">MOIM</span>
                    <span className="text-gold" style={{ fontSize: '12.7px', fontWeight: 700, letterSpacing: '0.045em', position: 'relative', top: '-0.05em' }}>io</span>
                  </h1>
                  <p className="whitespace-nowrap mt-0.5" style={{ fontFamily: "'Nunito Sans', sans-serif", fontSize: '6.5px', letterSpacing: '0.04em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)', fontWeight: 600 }}>Gather · Organise</p>
                </div>
              </div>
              <button onClick={() => setSidebarOpen(false)}
                className="text-white/25 hover:text-white text-sm transition-colors ml-1 shrink-0"
                title="Collapse sidebar">
                {isMobile ? '✕' : '◀'}
              </button>
            </div>

            {/* Primary nav */}
            <div className="px-3 pt-2.5 pb-1.5 shrink-0">
              {insideEvent ? (
                <>
                  {/* Back-to-events link. Visible for both admins (full
                      events list) and staff (their assigned events,
                      scoped server-side as of v0.50c-3c-2c). Staff who
                      serve multiple events need this to switch between
                      them; single-event staff just see one entry. */}
                  <button onClick={() => { navigate('/admin'); closeSidebar(); }}
                    className="block w-full text-left px-2 py-1 rounded-lg text-xs text-white/55 hover:text-white hover:bg-white/5 transition-colors mb-1.5">
                    {t('nav.all_events')}
                  </button>
                  {inSetupPhase ? (
                    /* Setup phase: one link to the hub (§7.3). People/Organise/
                       Check-in don't apply pre-registration, so they're hidden. */
                    <button
                      onClick={() => { navigate(`/admin/events/${eventId}`); closeSidebar(); }}
                      className="block w-full text-left px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors bg-steel-blue text-white">
                      {t('nav.setup_hub')}
                    </button>
                  ) : (
                    <div className="space-y-0.5">
                      {primaryItems.map(item => (
                        <button key={item.id} onClick={() => navigateSection(item.id)}
                          className={`block w-full text-left px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
                            activeSection === item.id
                              ? 'bg-steel-blue text-white'
                              : 'text-white/70 hover:text-white hover:bg-white/5'
                          }`}>
                          {item.label}
                        </button>
                      ))}
                      {/* v50d-2: More menu — collapsible group of phase-
                          deferred Setup items (Details, Registration form,
                          Group types, Marks, Staff, Export). Only shown
                          during Registration / Event phases for admins. */}
                      {moreItems.length > 0 && (
                        <div className="pt-1.5 mt-1.5 border-t border-white/10">
                          <button
                            type="button"
                            onClick={() => setMoreOpen(o => !o)}
                            aria-expanded={moreOpen}
                            className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-semibold text-white/55 hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <span>{t('nav.more')}</span>
                            <span
                              aria-hidden="true"
                              className="text-[10px] transition-transform"
                              style={{ transform: moreOpen ? 'rotate(90deg)' : 'none' }}
                            >
                              ▶
                            </span>
                          </button>
                          {moreOpen && (
                            <div className="mt-0.5 space-y-0.5">
                              {moreItems.map(item => (
                                <button
                                  key={item.id}
                                  onClick={() => navigateSection(item.id)}
                                  className={`flex items-center gap-2 w-full text-left pl-5 pr-3 py-1.5 rounded-lg text-xs transition-colors ${
                                    activeSection === item.id
                                      ? 'bg-white/10 text-white'
                                      : 'text-white/45 hover:text-white/85 hover:bg-white/5'
                                  }`}
                                >
                                  <item.Icon className="shrink-0 opacity-80" />
                                  <span>{item.label}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                /* v1.0-pre: Events link visible for all roles, including
                   staff. Pairs with the existing back-to-events link
                   inside an event (line ~320, comment "Visible for both
                   admins and staff"). The previous `!isStaff` gate hid
                   the only sidebar link from staff who'd navigated to
                   /admin (the events list) or /admin/users etc., trapping
                   them on whatever page they'd reached. */
                <NavLink to="/admin" end onClick={closeSidebar}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive ? 'bg-steel-blue text-white' : 'text-white/60 hover:text-white hover:bg-white/5'
                    }`}>
                  {t('nav.events')}
                </NavLink>
              )}
            </div>

            {/* Setup nav — admins only */}
            {insideEvent && setupItems.length > 0 && (
              <div className="px-3 py-1">
                <div className="border-t border-white/10 pt-2 space-y-0.5">
                  <p className="px-2 py-0.5 text-[8px] uppercase tracking-wider text-white/20 font-semibold">{t('nav.setup')}</p>
                  {setupItems.map(item => (
                    <button key={item.id} onClick={() => navigateSection(item.id)}
                      className={`block w-full text-left px-3 py-1.5 rounded-lg text-xs transition-colors ${
                        activeSection === item.id
                          ? 'bg-white/10 text-white'
                          : 'text-white/50 hover:text-white/80 hover:bg-white/5'
                      }`}>
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {/* Backup — always visible for admins.
                v0.70d-2b (R11): routes to the BackupPage at /admin/backup
                instead of opening a sidebar modal that duplicated the
                page. The modal is gone. */}
            {!isStaff && (
              <div className="px-3 pb-1">
                <div className="border-t border-white/10 pt-2">
                  <button onClick={() => { navigate('/admin/backup'); closeSidebar(); }}
                    className="block w-full text-left px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/80 hover:bg-white/5 transition-colors">
                    {t('nav.backup')}
                  </button>
                  {/* v1.0.0g: Webhooks. Super-admin only AND the outbound
                      webhook capability has to be on. Hidden for staff
                      and event-admins; hidden when FEATURE_OUTBOUND_WEBHOOKS
                      is off (in which case the backend router isn't
                      registered either, so clicking would 404). */}
                  {user?.role === 'super_admin' && capabilities.outbound_webhooks && (
                    <button onClick={() => { navigate('/admin/webhooks'); closeSidebar(); }}
                      className="block w-full text-left px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/80 hover:bg-white/5 transition-colors">
                      {t('nav.webhooks')}
                    </button>
                  )}
                  {/* v1.0.0v: Workspace settings — currently houses only the
                      Danger Zone (customer-triggered workspace deletion).
                      Super-admin-only; no capability flag — basic admin
                      feature, the endpoint just queues a webhook event
                      that's a no-op for self-hosters with no SaaS endpoint. */}
                  {user?.role === 'super_admin' && (
                    <button onClick={() => { navigate('/admin/workspace'); closeSidebar(); }}
                      className="block w-full text-left px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/80 hover:bg-white/5 transition-colors">
                      {t('nav.workspace')}
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Spacer — pushes footer to bottom */}
            <div className="flex-1" />

            {/* Footer — bottom padding respects iOS safe-area so the
                theme toggle + version row clear the home indicator
                (v0.59a). */}
            <div className="border-t border-white/10 shrink-0 px-3 pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))]">
              <div className="mb-1">
                <div className="text-[11px] text-white/65 truncate">{user?.full_name}</div>
                <div className="text-[9px] text-white/40 truncate">{user?.role ? t('role.' + user.role) : ''}</div>
              </div>
              {/* User management link — admins with permission. When
                  clicked from inside an event, passes ?from={eventId} so
                  UserManagementPage can render a "Back to event" breadcrumb
                  (v0.50d-4b). Single-click return to the event context. */}
              {canManageUsers && (
                <button onClick={() => {
                    const target = insideEvent
                      ? `/admin/users?from=${eventId}`
                      : '/admin/users';
                    navigate(target);
                    closeSidebar();
                  }}
                  className={`block w-full text-left px-2 py-1 rounded-lg text-[10px] transition-colors mb-0.5 ${
                    location.pathname === '/admin/users'
                      ? 'text-white bg-white/10'
                      : 'text-white/55 hover:text-white hover:bg-white/5'
                  }`}>
                  {t('nav.users')}
                </button>
              )}
              {/* v0.70d-2c (R3-C-hybrid): re-open the welcome overlay
                  any time. Sits above Preferences so it reads as a
                  "review" action rather than a settings toggle. */}
              <button onClick={() => { setShowWelcome(true); closeSidebar(); }}
                className="block w-full text-left px-2 py-1 rounded-lg text-[10px] text-white/55 hover:text-white hover:bg-white/5 transition-colors">
                {t('nav.welcome_tour')}
              </button>
              <button onClick={() => setShowPrefs(!showPrefs)}
                className="block w-full text-left px-2 py-1 rounded-lg text-[10px] text-white/55 hover:text-white hover:bg-white/5 transition-colors">
                {showPrefs ? t('common.close_prefs') : t('prefs.title')}
              </button>
              {showPrefs && <UserPreferencesPanel onClose={() => setShowPrefs(false)} />}
              <button onClick={handleLogout}
                className="block w-full text-left px-2 py-1 rounded-lg text-[10px] text-white/55 hover:text-white hover:bg-white/5 transition-colors">
                {t('nav.sign_out')}
              </button>
              {/* Version + legal + theme toggle (§9.8) */}
              <div className="flex items-center justify-between mt-1 gap-1">
                <button onClick={() => setShowLegal(true)}
                  className="flex-1 text-left px-2 py-1 rounded-lg text-[9px] text-white/40 hover:text-white/70 transition-colors">
                  {MOIMIO_VERSION} · © Pistio
                </button>
                <ThemeToggle tone="sidebar" />
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Legal notice modal */}
      {showLegal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setShowLegal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-sm"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="font-heading font-bold text-base text-deep-navy">{t('legal.title')}</h2>
                <p className="text-[10px] text-gray-400 mt-0.5">Moimio {MOIMIO_VERSION}</p>
              </div>
              <button onClick={() => setShowLegal(false)}
                className="text-gray-300 hover:text-gray-500 text-xl leading-none ml-4">×</button>
            </div>
            <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
              <p>
                <span className="font-semibold text-gray-800">{t('legal.software_by')}</span><br />
                Pistio<br />
                {t('legal.trading_name')}<br />
                Johannes Kim<br />
                {t('legal.sole_trader')}
              </p>
              <p className="text-gray-400 text-[10px]">
                {t('legal.no_warranty')}
              </p>
            </div>
            {/* v0.99f: manual update check. Clears caches and hard-reloads —
                fresh asset request guaranteed. The button is in the legal
                modal rather than the main UI because (a) it's a corner-
                case escape hatch most users never need, and (b) when the
                auto-detected UpdatePrompt isn't firing, this gives users
                an obvious way to force a refresh. */}
            <button
              type="button"
              onClick={handleCheckForUpdates}
              disabled={isCheckingForUpdate}
              className="mt-4 w-full py-2 rounded-xl text-xs font-semibold border border-steel-blue text-steel-blue hover:bg-steel-blue hover:text-white transition-colors disabled:opacity-60 disabled:cursor-wait inline-flex items-center justify-center gap-1.5">
              {isCheckingForUpdate && (
                <span className="inline-block animate-spin" aria-hidden="true">⟳</span>
              )}
              {isCheckingForUpdate
                ? t('legal.checking_for_updates')
                : t('legal.check_for_updates')}
            </button>
            <button onClick={() => setShowLegal(false)}
              className="mt-2 w-full py-2 rounded-xl bg-deep-navy text-white text-xs font-semibold hover:bg-mid-navy transition-colors">
              {t('common.close')}
            </button>
          </div>
        </div>
      )}

      {/* v0.70d-2c (R3-C-hybrid): welcome-tour overlay. Rendered
          outside the sidebar subtree so it escapes transforms +
          overflow contexts and truly covers the viewport. The modal
          shell provides backdrop dismiss; WelcomePanel itself
          renders the close button via `onClose`. ESC key + body
          scroll-lock handled by the useEffect below the render. */}
      {showWelcome && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-y-auto py-6 px-3"
          onClick={() => setShowWelcome(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="welcome-title"
        >
          <div
            className="max-w-lg w-full my-auto"
            onClick={e => e.stopPropagation()}
          >
            <WelcomePanel
              isAdmin={!isStaff}
              onClose={() => setShowWelcome(false)}
              onCta={() => setShowWelcome(false)}
            />
          </div>
        </div>
      )}


      <main className={`flex-1 px-4 ${isMobile ? 'pt-16' : 'pt-4'} pb-16 md:p-6 md:pb-10 overflow-auto min-w-0`}>
        {!sidebarOpen && (
          <button onClick={() => setSidebarOpen(true)}
            className="fixed top-[calc(0.75rem+env(safe-area-inset-top))] left-[calc(0.75rem+env(safe-area-inset-left))] z-20 bg-deep-navy text-white w-10 h-10 rounded-xl flex items-center justify-center text-lg shadow-md hover:bg-mid-navy transition-colors">
            ≡
          </button>
        )}
        <Outlet />
      </main>

      {/* v0.59b: install-to-home-screen prompt. Self-gates (standalone,
          dismissed, iOS vs native). Only mounted inside AdminLayout so
          public /register and /login visitors are never prompted. */}
      <InstallPrompt />

      {/* v0.59d: new-version-available toast + offline-ready confirmation.
          Also registers the service worker on mount (single call site —
          vite-plugin-pwa's injectRegister is null). Self-renders null
          when no notification is active, so no conditional wrapping. */}
      <UpdatePrompt />
    </div>
  );
}
