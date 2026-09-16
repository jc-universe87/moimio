import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';

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
 *   onDropExclude   — () => void; a participant was dropped on the block
 *   onDragEnterBlock— () => void; lets the board clear the pool's own
 *                     drop highlight, which may already be lit from the
 *                     pointer passing over the pool on its way here
 */
export default function ExcludedBlock({ people, canEdit, selectedIds, onToggleSelect, onInclude, onDropExclude, onDragEnterBlock }) {
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
      className="shrink-0 rounded-card mx-1.5 mb-1.5 transition-colors"
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
        className="w-full flex items-center justify-between px-2 py-1.5 text-left"
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
        <p className="text-[10px] px-2 pb-1.5 m-0 leading-tight"
          style={{ color: 'var(--alert-burgundy)' }}>
          {t('organise.exclude.drop_hint')}
        </p>
      )}

      {open && (
        <div className="flex flex-col gap-0.5 px-1.5 pb-1.5">
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
              {canEdit && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); if (onInclude) onInclude(pid); }}
                  aria-label={t('organise.exclude.undo_title')}
                  title={t('organise.exclude.undo_title')}
                  className="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded-card hover:bg-black/5 dark:hover:bg-white/10"
                  style={{ color: 'var(--io-accent)' }}>
                  {t('organise.exclude.undo')}
                </button>
              )}
            </div>
          );
          })}
        </div>
      )}
    </div>
  );
}
