/**
 * Event phase + sub-state detection (spec §3).
 *
 * Outer phases: Setup / Registration / Event
 * Sub-states (only defined when phase === 'event'):
 *   Preparing — registration closed or start_date arrived, event not yet over
 *   Live      — start_date <= today <= end_date
 *   Done      — today > end_date
 *
 * Outer-phase rules (unchanged from v50b):
 *   Setup        — event.status === 'draft'
 *   Registration — event.status === 'open' AND today < start_date
 *   Event        — all other configured states (closed / archived / open-but-started)
 *
 * Sub-state rules (§3.104):
 *   Preparing — default Event sub-state. Registration is closed, or start_date
 *               arrived with registration still open (door-reg case). No end_date
 *               crossed yet.
 *   Live      — today is between start_date and end_date (inclusive both ends).
 *   Done      — today > end_date.
 *
 * Edge cases decided for v50c-1:
 *   - end_date null → never becomes Done from date alone. If start_date is
 *     also null, stays Preparing forever until organiser sets dates or closes.
 *   - today === start_date → Live (you're on the day).
 *   - today === end_date → Live (the event hasn't ended yet).
 *   - start_date null, end_date somehow set → treat as Preparing until end_date
 *     passes (unusual config; organiser hasn't finalised).
 *
 * Timezone: compared at day granularity using browser-local date. Imperfect
 * for international organisers; proper timezone-aware logic is future work.
 */

export const PHASE = {
  SETUP: 'setup',
  REGISTRATION: 'registration',
  EVENT: 'event',
};

export const SUB_STATE = {
  PREPARING: 'preparing',
  LIVE: 'live',
  DONE: 'done',
};

function compareDates(a, b) {
  const da = a instanceof Date ? a : new Date(a + 'T00:00:00');
  const db = b instanceof Date ? b : new Date(b + 'T00:00:00');
  const ymdA = da.getFullYear() * 10000 + (da.getMonth() + 1) * 100 + da.getDate();
  const ymdB = db.getFullYear() * 10000 + (db.getMonth() + 1) * 100 + db.getDate();
  if (ymdA < ymdB) return -1;
  if (ymdA > ymdB) return 1;
  return 0;
}

export function getEventPhase(event, now = new Date()) {
  if (!event) return PHASE.SETUP;
  const status = event.status;

  if (status === 'draft') return PHASE.SETUP;
  if (status === 'archived') return PHASE.EVENT;
  if (status === 'closed') return PHASE.EVENT;

  if (status === 'open') {
    if (!event.start_date) return PHASE.REGISTRATION;
    if (compareDates(now, event.start_date) >= 0) return PHASE.EVENT;
    return PHASE.REGISTRATION;
  }

  return PHASE.SETUP;
}

/**
 * Derive the Event-phase sub-state. Returns null when the event isn't in
 * Event phase (caller should check).
 */
export function getEventSubState(event, now = new Date()) {
  if (!event) return null;
  const phase = getEventPhase(event, now);
  if (phase !== PHASE.EVENT) return null;

  // Archived events are treated as Done — they're past events in the archive.
  if (event.status === 'archived') return SUB_STATE.DONE;

  const hasStart = !!event.start_date;
  const hasEnd = !!event.end_date;

  // today > end_date → Done
  if (hasEnd && compareDates(now, event.end_date) > 0) return SUB_STATE.DONE;

  // Live: start_date <= today <= end_date
  if (hasStart && compareDates(now, event.start_date) >= 0
      && (!hasEnd || compareDates(now, event.end_date) <= 0)) {
    return SUB_STATE.LIVE;
  }

  // Default: Preparing (registration closed pre-event, or no dates yet)
  return SUB_STATE.PREPARING;
}

export function canOpenRegistration(event) {
  return !!(event && event.details_confirmed && event.registration_confirmed);
}
