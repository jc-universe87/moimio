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
