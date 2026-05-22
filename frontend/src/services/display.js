/**
 * Shared display utilities.
 */

// v1.0.0o: STATUS_LABELS export removed — was hardcoded English.
// All consumers now use t(STATUS_LABELS_KEYS[s]) for proper i18n.
// Keys live in PeopleTable.jsx as STATUS_LABELS_KEYS; resolve via
// status.pending / status.confirmed / status.cancelled in locale files.

// v0.70b: brand-aligned 2-color status system. Drops the traffic-light
// (gray/green/amber/red) for the Moimio palette: io-accent for the active
// state, alert burgundy for archived (deletable/historical), neutral for
// the resting states (draft, closed). See tailwind.config.js plugin.
export const EVENT_STATUS_COLORS = {
  draft:    'bg-neutral-tint text-muted',
  open:     'bg-accent-tint text-accent',
  closed:   'bg-neutral-tint text-muted',
  archived: 'bg-alert-tint text-alert',
};
