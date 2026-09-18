/**
 * Tiny SVG icons for the controls that sit on a row — a pool chip, a unit
 * member, an excluded person. v1.0.4y.
 *
 * WHY THESE EXIST. These controls used to be bare characters: ⓘ, ⊘, ✕ and,
 * from v1.0.4x, ↩ for "put this person back". Most of those have text
 * presentation and drew as flat grey glyphs. U+21A9 does not: it is in the
 * emoji set, and on a system with a colour emoji font it renders as a white
 * arrow on a filled blue rounded square. So one control on the excluded row
 * arrived as an emoji beside a flat grey neighbour, which is what Johannes
 * reported on v1.0.4x. A character cannot be relied on to stay a character.
 *
 * THE CONVENTION is `icons/MoreIcons.jsx`'s, at row scale: a 24-unit viewBox,
 * no fill, `currentColor` so each caller's own colour still applies, round
 * caps and joins, Lucide-style minimalism. Only the drawn size differs — 13px
 * to sit on a 12px line of text rather than the sidebar's 14.
 *
 * `aria-hidden` is deliberate on every one of them. Each already sits inside a
 * button carrying its own `aria-label`, so the icon must stay silent or a
 * screen reader announces the control twice.
 */

const baseProps = {
  width: 13,
  height: 13,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

// Details — info circle. Same shape as MoreIcons' IconDetails, so the two
// sets read as one vocabulary.
export const IconInfo = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="12" cy="12" r="9" />
    <line x1="12" y1="11" x2="12" y2="17" />
    <line x1="12" y1="7" x2="12" y2="8" />
  </svg>
);

// Put back — the undo arrow. Replaces ↩, the one glyph that was arriving as
// an emoji.
export const IconUndo = (props) => (
  <svg {...baseProps} {...props}>
    <path d="M9 14 4 9l5-5" />
    <path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11" />
  </svg>
);

// Exclude — a barred circle. Replaces ⊘, and stays visibly different from
// the plain ✕ beside it, which is what the v1.0.4k comment asked for when it
// chose two different characters.
export const IconExclude = (props) => (
  <svg {...baseProps} {...props}>
    <circle cx="12" cy="12" r="9" />
    <line x1="5.6" y1="5.6" x2="18.4" y2="18.4" />
  </svg>
);

// Remove from this unit — a plain cross. Replaces ✕.
export const IconRemove = (props) => (
  <svg {...baseProps} {...props}>
    <line x1="6" y1="6" x2="18" y2="18" />
    <line x1="18" y1="6" x2="6" y2="18" />
  </svg>
);
