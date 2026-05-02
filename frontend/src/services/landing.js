/**
 * getLandingForUser — given a user, an event, and the current phase,
 * return the section the user should land on by default.
 *
 * This is the single source of truth for "where does this user land
 * when they enter an event without an explicit ?section= URL param."
 *
 * Returns one of the section IDs the EventDetailPage already knows
 * how to render: 'board', 'people', 'organise', 'checkin', 'reports',
 * 'marks', 'no-access'.
 *
 * v0.70d-3c-11 priority overhaul
 * ──────────────────────────────
 * The previous implementation considered only people/organise/checkin
 * as landing destinations. Marks-only and reports-only staff routed
 * to 'no-access' even though the sidebar correctly offered them a
 * direct entry to click. That UX gap closes here: marks and reports
 * are now first-class landings.
 *
 * Resolution priority follows sidebar order (people, organise,
 * checkin, reports, marks) with one phase-specific override: in
 * EVENT phase, organise wins over people because the allocation
 * board is the operational surface during the event itself. Outside
 * EVENT phase, sidebar order is strict.
 *
 * Per phase, only certain destinations make sense:
 *
 *   SETUP — registrations haven't started yet. Anything that needs
 *           registration data (organise, checkin) routes to a
 *           "not yet" placeholder. Reports renders an empty page,
 *           which is acceptable. Marks works fully (defs are managed
 *           in setup).
 *           Allowed: people, reports, marks.
 *           Priority: people → reports → marks.
 *
 *   REGISTRATION — registrations are coming in; allocation can
 *           start; check-in setup (pre-event) is allowed for staff
 *           who have the pre_event sub-flag set.
 *           Allowed: people, organise, reports, marks, checkin (pre_event).
 *           Priority: people → organise → reports → marks → checkin.
 *
 *   EVENT — everything is live.
 *           Allowed: organise, people, checkin, reports, marks.
 *           Priority: organise → people → checkin → reports → marks
 *                     (organise overrides people here — phase exception).
 *
 * Admins (Super Admin or per-event admin) short-circuit to phase
 * defaults — Setup phase is handled upstream by the SetupHub
 * early-return; Registration phase by RegistrationPhasePage; Event
 * phase lands on board.
 */

import { PHASE } from '../hooks/useEventPhase';

// v1.0-pre #10/#12: checkin permission is now an object
// {access: 'write' | '', pre_event: bool}. These helpers read both
// the new α-shape and the legacy flat-string shape so callers don't
// need to repeat the dual-shape handling.
function _checkinAccess(perms) {
  const c = perms?.checkin;
  if (c && typeof c === 'object') return !!c.access;
  return !!c;
}

function _checkinPreEvent(perms) {
  const c = perms?.checkin;
  if (c && typeof c === 'object') return !!c.access && !!c.pre_event;
  return false;
}

/**
 * canAccessSection — given a section ID and the user's context,
 * return whether they should be allowed to render that section.
 *
 * v0.70d-3c-12: introduced for URL-jump validation. When a user
 * navigates to `?section=X` for a section they don't have access
 * to, EventDetailPage falls back to their default landing and
 * shows a toast — but the fallback only fires when
 * canAccessSection returns false.
 *
 * v1.0-pre #12: checkin gating is now a single "do you have any
 * check-in access at all" check. The phase + pre_event sub-flag
 * decision moved into the section renderer in EventDetailPage,
 * which picks between the operational CheckInPanel and the
 * "Your check-in starts when the event begins" placeholder
 * (NoPermissionPage variant=checkin_not_yet). This means staff
 * who click Check-in but lack the pre_event flag in Registration
 * phase land on the calm informational page instead of being
 * silently redirected to their default landing with a confusing
 * toast — the click expressed an intent, so the response should
 * be about Check-in, not about whatever section they happened to
 * have access to.
 *
 * Admin sections (event-details, staff, registration) require
 * isAdmin (super-admin or per-event admin). Staff-perm-gated
 * sections require the matching perm view. The 'no-access' and
 * pseudo-sections always pass — they're either pure UI states or
 * safe destinations.
 */
export function canAccessSection({ section, phase, staffPerms, isAdmin }) {
  if (!section) return true;
  if (isAdmin) return true;
  const perms = staffPerms || {};

  // Admin-only sections — staff never reach these
  if (section === 'event-details' || section === 'staff' || section === 'registration') {
    return false;
  }

  // Staff-perm-gated sections
  if (section === 'people') return !!perms.people;
  if (section === 'board' || section === 'organise') return !!perms.organise;
  if (section === 'checkin') {
    // v1.0-pre #12 (v0.97): any staff with check-in access can navigate
    // here regardless of phase or pre_event sub-flag. The renderer in
    // EventDetailPage decides which view to show. Staff with no check-in
    // access at all still get redirected with a toast — they arrived by
    // mistake (stale bookmark, mis-shared URL).
    return _checkinAccess(perms);
  }
  if (section === 'reports') return !!perms.reports;
  if (section === 'marks') return !!perms.marks;

  // 'no-access' is the friendly placeholder, anyone can land there.
  // Unknown section IDs fall through as accessible — let the
  // EventDetailPage section switch handle them (it'll show nothing
  // for unrecognised values, which is fine).
  return true;
}

export function getLandingForUser({ user, phase, staffPerms, isAdmin }) {
  const role = user?.role;

  // Admins: callers should already have routed Setup/Registration to
  // their dedicated landings. This function returns the *default
  // section* for when no early-return handles them — the Event-phase
  // board.
  if (isAdmin || role === 'super_admin') {
    return 'board';
  }

  if (role === 'staff') {
    const perms = staffPerms || {};
    const hasPeople   = !!perms.people;
    const hasOrganise = !!perms.organise;
    const hasCheckin  = _checkinAccess(perms);  // α-shape aware
    const hasCheckinPreEvent = _checkinPreEvent(perms);  // v1.0-pre #12
    const hasReports  = !!perms.reports;
    const hasMarks    = !!perms.marks;
    const hasAny = hasPeople || hasOrganise || hasCheckin || hasReports || hasMarks;

    if (!hasAny) return 'no-access';

    if (phase === PHASE.SETUP) {
      // SETUP priority: people → reports → marks. Organise/checkin
      // route to no-access with phase-specific variants (the
      // EventDetailPage classifier picks 'organise_not_yet' or
      // 'checkin_not_yet' as appropriate).
      if (hasPeople) return 'people';
      if (hasReports) return 'reports';
      if (hasMarks) return 'marks';
      return 'no-access';
    }

    if (phase === PHASE.REGISTRATION) {
      // REGISTRATION priority: people → organise → reports → marks → checkin.
      // v1.0-pre #12 (v0.96): checkin lands here only when the staff
      // member has the pre_event sub-flag set — those staff get the
      // operational CheckInPanel during Registration. Without pre_event,
      // checkin staff fall through to no-access where the variant
      // classifier picks the 'checkin_not_yet' copy. v0.97 also lets
      // them click Check-in directly and arrive at the same copy via
      // the section renderer (canAccessSection no longer gates on
      // pre_event — see above).
      if (hasPeople) return 'people';
      if (hasOrganise) return 'organise';
      if (hasReports) return 'reports';
      if (hasMarks) return 'marks';
      if (hasCheckinPreEvent) return 'checkin';
      return 'no-access';
    }

    if (phase === PHASE.EVENT) {
      // EVENT priority: organise → people → checkin → reports → marks.
      // Organise wins over people in this phase (board is the
      // operational surface during the event itself).
      // v0.50e-1e: 'board' (not 'organise') is the renderer key for
      // the allocation board in EventDetailPage.
      if (hasOrganise) return 'board';
      if (hasPeople) return 'people';
      if (hasCheckin) return 'checkin';
      if (hasReports) return 'reports';
      if (hasMarks) return 'marks';
      return 'no-access';
    }

    return 'no-access';
  }

  return 'board';
}
