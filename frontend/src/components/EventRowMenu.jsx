import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useI18n } from '../hooks/useI18n';

/**
 * EventRowMenu — per-event ⋯ action menu on the events list. v0.51.1.
 *
 * Items:
 *   - Pin/Unpin   — visible when canPin (admin) && !event.is_archived.
 *                   Pinned events float to top of the active list (v0.70d-3c-9).
 *   - Duplicate   — visible when canDuplicate (i.e. user can create events)
 *   - Archive     — visible when canArchive && !event.is_archived
 *   - Unarchive   — visible when canArchive &&  event.is_archived
 *   - Delete      — visible when canDelete
 *
 * When NO items apply the button is hidden entirely.
 *
 * v0.51.1 fix — rendering the popover via a React portal into document.body
 * with position:fixed, measuring the button's viewport coordinates on open.
 * This escapes all ancestor stacking contexts (the v0.51 build used
 * position:absolute inside the card, and a later sibling card painted on top
 * of the middle items — classic CSS stacking issue where a sibling positioned
 * element beats an earlier sibling's absolutely-positioned child).
 *
 * Props:
 *   event          — { id, name, is_archived }
 *   canDuplicate   — bool
 *   canArchive     — bool (today: super_admin only)
 *   canDelete      — bool (today: super_admin only)
 *   onDuplicate    — () => void
 *   onArchive      — () => void  (used for both archive and unarchive)
 *   onDelete       — () => void
 *   canPin         — bool (admin can pin/unpin)
 *   onPin          — () => void  (used for both pin and unpin)
 */
export default function EventRowMenu({
  event,
  canDuplicate,
  canArchive,
  canDelete,
  canPin,
  onDuplicate,
  onArchive,
  onDelete,
  onPin,
}) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  // Viewport coordinates for the popover. Null until measured on open.
  const [pos, setPos] = useState(null);
  const btnRef = useRef(null);
  const menuRef = useRef(null);

  const hasAny = canDuplicate || canArchive || canDelete || canPin;

  // Measure the button and compute popover coordinates. Called on open and
  // on scroll/resize while open so the menu tracks the button.
  const measure = useCallback(() => {
    if (!btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const flipUp = spaceBelow < 180;
    // Align the popover's right edge with the button's right edge.
    const right = Math.max(8, window.innerWidth - rect.right);
    setPos({
      top: flipUp ? null : rect.bottom + 4,
      bottom: flipUp ? window.innerHeight - rect.top + 4 : null,
      right,
    });
  }, []);

  // Close on outside click or Escape. Reposition on scroll/resize.
  useEffect(() => {
    if (!open) return;
    const onDocDown = (e) => {
      if (menuRef.current?.contains(e.target)) return;
      if (btnRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    const onScrollOrResize = () => measure();
    document.addEventListener('mousedown', onDocDown);
    document.addEventListener('keydown', onKey);
    window.addEventListener('scroll', onScrollOrResize, true);
    window.addEventListener('resize', onScrollOrResize);
    return () => {
      document.removeEventListener('mousedown', onDocDown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('scroll', onScrollOrResize, true);
      window.removeEventListener('resize', onScrollOrResize);
    };
  }, [open, measure]);

  if (!hasAny) return null;

  const handleToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (open) {
      setOpen(false);
      return;
    }
    measure();
    setOpen(true);
  };

  const stop = (fn) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    setOpen(false);
    fn?.();
  };

  const menu = open && pos ? (
    <div
      ref={menuRef}
      // position: fixed via portal to document.body — escapes every ancestor
      // stacking context (card's position:relative, transforms, opacity, etc.)
      className="fixed z-[1000] rounded-xl shadow-lg overflow-hidden"
      style={{
        background: 'var(--card-bg-solid)',
        border: '1px solid var(--card-border)',
        minWidth: 160,
        top: pos.top !== null ? `${pos.top}px` : 'auto',
        bottom: pos.bottom !== null ? `${pos.bottom}px` : 'auto',
        right: `${pos.right}px`,
      }}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
    >
      {canPin && !event.is_archived && (
        <MenuItem onClick={stop(onPin)}>
          {event.settings?.pinned ? t('events.menu.unpin') : t('events.menu.pin')}
        </MenuItem>
      )}
      {canDuplicate && (
        <MenuItem onClick={stop(onDuplicate)}>
          {t('events.menu.duplicate')}
        </MenuItem>
      )}
      {canArchive && !event.is_archived && (
        <MenuItem onClick={stop(onArchive)}>
          {t('event.archive.button')}
        </MenuItem>
      )}
      {canArchive && event.is_archived && (
        <MenuItem onClick={stop(onArchive)}>
          {t('event.unarchive.button')}
        </MenuItem>
      )}
      {canDelete && (
        <MenuItem onClick={stop(onDelete)} danger>
          {t('event.delete.button')}
        </MenuItem>
      )}
    </div>
  ) : null;

  return (
    <div className="shrink-0">
      <button
        ref={btnRef}
        type="button"
        aria-label={t('events.menu.open_label')}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={handleToggle}
        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        style={{ color: 'var(--text-muted)' }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <circle cx="5"  cy="12" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="19" cy="12" r="2" />
        </svg>
      </button>
      {menu && createPortal(menu, document.body)}
    </div>
  );
}

function MenuItem({ children, onClick, danger }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left px-4 py-2 text-sm transition-colors hover:bg-black/[0.04] dark:hover:bg-white/[0.06]"
      style={{ color: danger ? 'var(--alert-burgundy)' : 'var(--text-primary)' }}
    >
      {children}
    </button>
  );
}
