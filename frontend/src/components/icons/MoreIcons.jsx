/**
 * Tiny SVG icon set for the sidebar More menu.
 *
 * 14×14, stroke 1.6, currentColor — inherits text colour for theming.
 * Lucide-style minimalism — clear at small sizes, no fill noise.
 */

const baseProps = {
  width: 14,
  height: 14,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

// Event details — info circle
export const IconDetails = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="12" cy="12" r="9" />
    <line x1="12" y1="11" x2="12" y2="17" />
    <line x1="12" y1="7" x2="12" y2="8" />
  </svg>
);

// Registration form — clipboard with line
export const IconRegistrationForm = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="6" y="4" width="12" height="17" rx="2" />
    <path d="M9 4h6v2.5h-6z" />
    <line x1="9" y1="11" x2="15" y2="11" />
    <line x1="9" y1="14.5" x2="15" y2="14.5" />
    <line x1="9" y1="18" x2="13" y2="18" />
  </svg>
);

// Group types — overlapping squares
export const IconGroupTypes = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="3" y="3" width="11" height="11" rx="1.5" />
    <rect x="10" y="10" width="11" height="11" rx="1.5" />
  </svg>
);

// Marks — three dots in a triangle
export const IconMarks = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="12" cy="6" r="2" fill="currentColor" stroke="none" />
    <circle cx="6" cy="17" r="2" fill="currentColor" stroke="none" />
    <circle cx="18" cy="17" r="2" fill="currentColor" stroke="none" />
  </svg>
);

// Staff & permissions — two people
export const IconStaff = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="9" cy="8" r="3" />
    <circle cx="17" cy="9" r="2.4" />
    <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
    <path d="M15 20c0-2.5 2-4.5 4.5-4.5" />
  </svg>
);

// Export — down arrow into tray
export const IconExport = (props) => (
  <svg {...baseProps} {...props}>
    <path d="M12 4v11" />
    <path d="M8 11l4 4 4-4" />
    <path d="M5 19h14" />
  </svg>
);

// Events — calendar (v1.0.1: sidebar nav glyphs)
export const IconCalendar = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="4" y="5" width="16" height="16" rx="2" />
    <line x1="4" y1="9" x2="20" y2="9" />
    <line x1="8" y1="3" x2="8" y2="6" />
    <line x1="16" y1="3" x2="16" y2="6" />
  </svg>
);

// Backup — archive box (lid + body + handle slot)
export const IconBackup = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="3" y="4" width="18" height="4" rx="1" />
    <path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8" />
    <line x1="10" y1="12" x2="14" y2="12" />
  </svg>
);

// Webhooks — event dispatched outward (node + arrow)
export const IconWebhook = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="6" cy="12" r="3" />
    <line x1="9" y1="12" x2="18" y2="12" />
    <path d="M14 8l4 4-4 4" />
  </svg>
);

// Workspace — building with windows + door
export const IconWorkspace = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="6" y="3" width="12" height="18" rx="1.5" />
    <circle cx="9.5" cy="7" r="0.9" fill="currentColor" stroke="none" />
    <circle cx="14.5" cy="7" r="0.9" fill="currentColor" stroke="none" />
    <circle cx="9.5" cy="11" r="0.9" fill="currentColor" stroke="none" />
    <circle cx="14.5" cy="11" r="0.9" fill="currentColor" stroke="none" />
    <path d="M10 21v-3.5h4V21" />
  </svg>
);

// Manage account — credit card
export const IconAccount = (props) => (
  <svg {...baseProps} {...props}>
    <rect x="3" y="6" width="18" height="12" rx="2" />
    <line x1="3" y1="10" x2="21" y2="10" />
    <line x1="7" y1="14" x2="11" y2="14" />
  </svg>
);

// Welcome tour — compass
export const IconTour = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M15.5 8.5l-2.2 4.8-4.8 2.2 2.2-4.8z" fill="currentColor" stroke="none" />
  </svg>
);

// Preferences — sliders (two tracks + knobs). Deliberately not a gear:
// a spoked cog reads like a sun next to the adjacent theme toggle.
export const IconSettings = (props) => (
  <svg {...baseProps} {...props}>
    <line x1="4" y1="8" x2="20" y2="8" />
    <circle cx="15" cy="8" r="2.4" />
    <line x1="4" y1="16" x2="20" y2="16" />
    <circle cx="9" cy="16" r="2.4" />
  </svg>
);

// Sign out — exit arrow
export const IconSignOut = (props) => (
  <svg {...baseProps} {...props}>
    <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
    <line x1="9" y1="12" x2="20" y2="12" />
    <path d="M16 8l4 4-4 4" />
  </svg>
);
