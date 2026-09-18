import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';
// v1.0.4y: drawn icons, not characters. ↩ was arriving as a colour emoji.
import { IconInfo, IconUndo } from './icons/RowIcons';

// v1.0.4x: same test the board uses to gate its drag affordances (see
// AllocationBoard.jsx:31). Hover-revealed controls are unreachable without a
// hover, so where there is none both controls stay visible instead.
const HAS_FINE_POINTER = typeof window !== 'undefined'
  && typeof window.matchMedia === 'function'
  && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

/**
 * ExcludedBlock — the participants kept out of this group type.
 *
 * v1.0.4k. Sits directly beneath the unassigned pool on the
 * AllocationBoard, as a shrink-0 sibling AFTER the pool's scroll
 * container, so it stays pinned while the pool scrolls.
 *
 * Structure copied from CategoryHintsStrip (rotating ▶ marker,
 * aria-expanded, singular/plural header pair, renders nothing at
 * zero) — the same collapsible-band idiom already on this screen and
 * in AllocationHistory.
 *
 * Every chip carries its own undo control. An exclusion that cannot be
 * found cannot be reversed, and reversibility is the whole reason this
 * block exists rather than the excluded simply vanishing from the pool.
 *
 * v1.0.4y — both controls are drawn icons now, not characters. See
 * icons/RowIcons.jsx for why a character could not be trusted to stay one.
 *
 * v1.0.4x — one pass over the row (EXCL-2, EXCL-3). The undo control used
 * to be a WORD beside a truncating name, and in a 256px panel the longer
 * locales left the name barely readable. It is now a glyph, and the name
 * has the row to itself. A details control joins it, so an excluded
 * person's panel is reachable from here as it is from every other row on
 * the board. Both are revealed on hover and on keyboard focus, the idiom
 * the board names at AllocationBoard.jsx:2318-2321, and both stay visible
 * where there is no hover.
 *
 * No new string: the undo control already carried
 * `organise.exclude.undo_title` as its accessible name, so a screen reader
 * hears exactly what it heard before, and the details control reuses
 * `insight.open`. `organise.exclude.undo`, the old visible word, is now
 * rendered nowhere — it is deleted with the rest of release z's batch, not
 * here, because the six locale files are that release's.
 *
 * Drag OUT of the block was considered and dropped for good (EXCL-1): the
 * stopPropagation calls below are what stop a drop vanishing into the
 * panel behind, and letting a drag escape would mean unpicking them.
 *
 * DROP TARGET — and the trap it avoids. The left panel's root element
 * carries onDragOver / onDrop for "drop here to unassign", so anything
 * nested inside it inherits that gesture. Dropping onto THIS block must
 * exclude, not unassign. Every drag handler below therefore calls
 * e.stopPropagation(); without it the drop silently unassigns and looks
 * like it worked.
 *
 * Props:
 *   people          — Array of participant objects to list (already
 *                     filtered to the excluded ones by the board)
 *   canEdit         — boolean; false hides the undo controls and
 *                     disables the drop target (read-only surfaces)
 *   selectedIds     — Set of selected participant id strings, shared
 *                     with the pool, so several exclusions can be
 *                     lifted in one action from the floating bulk bar
 *   onToggleSelect  — (participantId) => void; same handler the pool
 *                     chips use
 *   onInclude       — (participantId) => void; lift one exclusion
 *   onOpenInsight   — (participant) => void; v1.0.4x. Opens the same
 *                     InsightPanel the pool chips open. Somebody excluded
 *                     from one group type is still a participant of the
 *                     event, and their details and history must not become
 *                     unreachable because of it.
 *   onDropExclude   — () => void; a participant was dropped on the block
 *   onDragEnterBlock— () => void; lets the board clear the pool's own
 *                     drop highlight, which may already be lit from the
 *                     pointer passing over the pool on its way here
 */
// Revealed on hover and on keyboard focus anywhere in the row; always
// visible where there is no hover to reveal them with.
const REVEAL = HAS_FINE_POINTER
  ? 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
  : 'opacity-100';

export default function ExcludedBlock({ people, canEdit, selectedIds, onToggleSelect, onInclude, onOpenInsight, onDropExclude, onDragEnterBlock }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const list = Array.isArray(people) ? people : [];

  // Visibility floor: nobody excluded → render nothing at all. The
  // board must not carry an empty box for a feature most group types
  // never use.
  if (list.length === 0) return null;

  const n = list.length;

  return (
    <div
      // v1.0.4y: the block is now a bounded flex column rather than a shrink-0
      // sibling with an unbounded body. `min-h-0` is the part that was missing:
      // without it a flex child refuses to shrink below its content, which is
      // exactly how twenty-six rows escaped the card and painted on the page.
      // The cap is on the block, not on its list, so the header counts towards
      // the budget and stays visible however little room is left.
      className="shrink min-h-0 max-h-[35vh] flex flex-col overflow-hidden rounded-card mx-1.5 mb-1.5 transition-colors"
      style={{
        background: dragOver ? 'rgba(128,0,32,0.10)' : 'rgba(128,128,128,0.06)',
        border: dragOver
          ? '1px solid var(--alert-burgundy)'
          : '1px solid var(--card-border)',
      }}
      onDragOver={canEdit ? (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (onDragEnterBlock) onDragEnterBlock();
        setDragOver(true);
      } : undefined}
      onDragLeave={canEdit ? (e) => { e.stopPropagation(); setDragOver(false); } : undefined}
      onDrop={canEdit ? (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
        if (onDropExclude) onDropExclude();
      } : undefined}>

      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="shrink-0 w-full flex items-center justify-between px-2 py-1.5 text-left"
        aria-expanded={open}>
        <span className="text-[11px] font-semibold flex items-center gap-1.5"
          style={{ color: 'var(--text-muted)' }}>
          <span style={{
            display: 'inline-block',
            transform: open ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.15s',
          }}>▶</span>
          {t(n === 1 ? 'organise.exclude.header_one' : 'organise.exclude.header', { n })}
        </span>
      </button>

      {/* Transient drag hint. The German string is long and wraps in a
          narrow panel; that is acceptable for a hint that exists only
          while a drag is in flight. */}
      {dragOver && (
        <p className="shrink-0 text-[10px] px-2 pb-1.5 m-0 leading-tight"
          style={{ color: 'var(--alert-burgundy)' }}>
          {t('organise.exclude.drop_hint')}
        </p>
      )}

      {open && (
        <div className="flex flex-col gap-0.5 px-1.5 pb-1.5 overflow-y-auto"
          style={{ flex: '1 1 auto', minHeight: 0, overscrollBehavior: 'contain' }}>
          {list.map(p => {
          const pid = String(p.id);
          const isSel = !!(selectedIds && selectedIds.has(pid));
          return (
            <div key={p.id}
              onClick={canEdit && onToggleSelect ? () => onToggleSelect(pid) : undefined}
              className={`group flex items-center justify-between gap-1 text-xs rounded-card px-2 py-1 ${canEdit && onToggleSelect ? 'cursor-pointer' : ''}`}
              style={isSel
                ? { background: 'rgba(70,130,180,0.12)', boxShadow: 'inset 0 0 0 1px var(--io-accent)', color: 'var(--text-primary)' }
                : { background: 'rgba(0,0,0,0.03)', color: 'var(--text-muted)' }}>
              <span className="truncate">{p.first_name} {p.last_name}</span>
              <span className="flex items-center shrink-0">
                {/* Details. Always offered, including on read-only
                    surfaces: reading somebody's panel is not a write. */}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); if (onOpenInsight) onOpenInsight(p); }}
                  aria-label={t('insight.open')}
                  title={t('insight.open')}
                  className={`shrink-0 leading-none px-1 transition-opacity focus:opacity-100 ${REVEAL}`}
                  style={{ color: 'var(--text-subtle)' }}>
                  <IconInfo />
                </button>
                {canEdit && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); if (onInclude) onInclude(pid); }}
                    aria-label={t('organise.exclude.undo_title')}
                    title={t('organise.exclude.undo_title')}
                    className={`shrink-0 leading-none px-1 transition-opacity focus:opacity-100 ${REVEAL}`}
                    style={{ color: 'var(--io-accent)' }}>
                    <IconUndo />
                  </button>
                )}
              </span>
            </div>
          );
          })}
        </div>
      )}
    </div>
  );
}
