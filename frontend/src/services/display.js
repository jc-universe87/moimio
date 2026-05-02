/**
 * Shared display utilities.
 */

export const STATUS_LABELS = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
};

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
