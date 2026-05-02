/**
 * MarkDots — small coloured dots shown next to a participant's name.
 *
 * v0.50f-3: assigned dots are now clickable and open the same modal as
 * the + button. Previously they were tooltip-only, which was asymmetric
 * (the + opened a modal but existing marks did not). If onManage is
 * provided, the whole cluster is interactive — dots and + button both
 * open the modal. If onManage is not provided (caller hasn't given us
 * a handler, e.g. before v0.50f-1's "read is implicit" rule), dots
 * render as static with just a tooltip.
 *
 * Props:
 *   marksForParticipant — array of mark definition objects (already
 *                          filtered by view)
 *   onManage            — optional callback. If provided, both dots and
 *                          + button open the modal for this participant.
 *   compact             — smaller sizing for dense layouts.
 */
export default function MarkDots({ marksForParticipant = [], onManage, compact = false }) {
  if (marksForParticipant.length === 0 && !onManage) return null;

  const dotSize = compact ? 6 : 8;
  const btnSize = compact ? 10 : 14;

  const handleOpen = (e) => {
    e.stopPropagation();
    onManage();
  };

  return (
    <span className="inline-flex items-center gap-0.5 ml-1">
      {marksForParticipant.map(m => (
        onManage ? (
          // Clickable: styled as a plain span with button semantics via
          // role + keyboard handler. A <button> would inherit block-ish
          // baseline styling that fights the inline flow; this keeps the
          // dot visually identical to the static version.
          <span
            key={m.id}
            title={m.name}
            role="button"
            tabIndex={0}
            onClick={handleOpen}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOpen(e); }}
            className="inline-block rounded-full shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
            style={{ backgroundColor: m.colour, width: `${dotSize}px`, height: `${dotSize}px` }}
          />
        ) : (
          <span
            key={m.id}
            title={m.name}
            className="inline-block rounded-full shrink-0"
            style={{ backgroundColor: m.colour, width: `${dotSize}px`, height: `${dotSize}px` }}
          />
        )
      ))}
      {onManage && (
        <button
          onClick={handleOpen}
          title="Manage marks"
          className="inline-flex items-center justify-center rounded-full transition-colors shrink-0 hover:bg-black/10 dark:hover:bg-white/20"
          style={{
            width: `${btnSize}px`,
            height: `${btnSize}px`,
            fontSize: compact ? '7px' : '9px',
            // v0.70d-2d-2 (P8): ring-only when no marks are assigned —
            // makes the empty state subtler than a solid grey block,
            // and reads as an "add" affordance rather than orphaned
            // grey debris next to the participant's name. When marks
            // ARE present, the button stays solid grey so it doesn't
            // compete visually with the coloured mark dots.
            background: marksForParticipant.length === 0
              ? 'transparent'
              : 'rgba(128,128,128,0.15)',
            border: marksForParticipant.length === 0
              ? '1px solid rgba(128,128,128,0.4)'
              : 'none',
            color: 'var(--text-subtle)',
          }}
        >
          ●
        </button>
      )}
    </span>
  );
}
