import { useState, useRef, useEffect, useCallback, useId, cloneElement, isValidElement } from 'react';
import { formatNamesList } from '../utils/formatNamesList';

/**
 * GroupCodeTooltip — hover/long-press popover that lists the OTHER
 * participants sharing this group code in the current event.
 *
 * v1.0.0e: introduced for the People board, Check-in board, and the
 * Insight panel's registration section.
 *
 * v1.0.0e: refined interaction model, applied uniformly across every
 * surface that wraps a group-code badge:
 *
 *   - Desktop: hover opens the popover, mouseleave closes. Click is
 *     reserved for the badge's own action (e.g. inline edit on
 *     PeopleTable) — clicking also closes any open hover popover, so
 *     edit and tooltip don't fight for the same z-space.
 *   - Touch: short tap delegates to the badge's onClick (edit, etc.);
 *     long-press (~500 ms) opens the bottom-sheet popover. Subsequent
 *     scrim/X tap dismisses the sheet without triggering edit.
 *
 * The pre-v1.0.0e `noClick` prop is gone — click never toggles the
 * popover; it always delegates to the child. The interaction is the
 * same on every surface, regardless of whether the badge has a click
 * handler attached.
 *
 * The list of names is empty when no one else shares this code in
 * this event. v1.0.0e switches the empty case from "suppress
 * everything" to "render a quiet 'no other person with this group
 * code' message" — the organiser hovering on a code wants to know
 * whether the cluster is one or many, and silence answered that
 * question ambiguously.
 *
 * Two sources of cluster members:
 *
 *   - DYNAMIC (live surfaces): `participants` is the full event
 *     participant list. The component filters for matching group_code,
 *     excludes `selfId`, and recomputes on every render — picks up
 *     adds and deletes immediately.
 *
 *   - STATIC (history audit trail): `staticMembers` is the imprinted
 *     [{id, name}] snapshot from the engine commit's meta payload.
 *     When provided, dynamic lookup is skipped — the popover shows
 *     who was in the cluster AT THAT TIME, even if the participant
 *     list has changed since.
 *
 * Props:
 *   children        (required) — the visible token, typically a span
 *                                with the group-code text. Cloned
 *                                with hover, touch, and click handlers.
 *   code            (required) — group code string, used for filtering
 *                                in dynamic mode and as the bottom-
 *                                sheet header.
 *   participants                — array of full participant records.
 *                                Required for dynamic mode.
 *   selfId                      — pid of the participant whose row
 *                                this badge sits on. Excluded from
 *                                the rendered list.
 *   staticMembers               — optional [{id?, name}] for static
 *                                mode. When set, `participants` is
 *                                ignored.
 *   t / lang        (required) — i18n function and locale code.
 */

// 500 ms matches platform conventions for long-press (Android, iOS).
// Long enough that a dragging thumb won't trigger it accidentally;
// short enough that a deliberate hold feels responsive.
const LONG_PRESS_MS = 500;

export default function GroupCodeTooltip({
  children,
  code,
  participants,
  selfId = null,
  staticMembers = null,
  t,
  lang = 'en',
}) {
  const [open, setOpen] = useState(false);
  const [isTouch, setIsTouch] = useState(() =>
    typeof window !== 'undefined'
      ? !window.matchMedia('(hover: hover) and (pointer: fine)').matches
      : false
  );
  const triggerRef = useRef(null);
  const popoverRef = useRef(null);
  const titleId = useId();

  // Long-press state. `longPressTimer` holds the pending setTimeout so
  // we can cancel on touchend / touchmove / unmount; `longPressFired`
  // tracks whether the timer fired BEFORE touchend (i.e. it really
  // was a long-press, not a tap). The synthetic click that browsers
  // emit after touchend is suppressed when longPressFired is true,
  // so a long-press that opened the tooltip never also triggers the
  // child's click handler (e.g. inline edit in PeopleTable).
  const longPressTimer = useRef(null);
  const longPressFired = useRef(false);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined;
    const mq = window.matchMedia('(hover: hover) and (pointer: fine)');
    const update = () => setIsTouch(!mq.matches);
    if (mq.addEventListener) {
      mq.addEventListener('change', update);
      return () => mq.removeEventListener('change', update);
    } else if (mq.addListener) {
      mq.addListener(update);
      return () => mq.removeListener(update);
    }
    return undefined;
  }, []);

  // Cleanup the long-press timer on unmount so a pending fire can't
  // setState into an unmounted component.
  useEffect(() => () => {
    if (longPressTimer.current) clearTimeout(longPressTimer.current);
  }, []);

  // Escape closes and returns focus to the trigger.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        if (triggerRef.current && typeof triggerRef.current.focus === 'function') {
          triggerRef.current.focus();
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  // Outside-click closes the desktop popover. The mobile bottom-sheet
  // has its own scrim handler.
  useEffect(() => {
    if (!open || isTouch) return undefined;
    const onClick = (e) => {
      if (triggerRef.current && triggerRef.current.contains(e.target)) return;
      if (popoverRef.current && popoverRef.current.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open, isTouch]);

  // ─── Compute the names list ───
  const names = (() => {
    if (staticMembers && Array.isArray(staticMembers)) {
      return staticMembers
        .filter(m => !selfId || (m && m.id && String(m.id) !== String(selfId)))
        .map(m => (m && m.name) || '')
        .filter(Boolean);
    }
    if (!Array.isArray(participants)) return [];
    const wanted = (code || '').trim();
    if (!wanted) return [];
    return participants
      .filter(p => p && (p.group_code || '').trim() === wanted)
      .filter(p => !selfId || String(p.id) !== String(selfId))
      .map(p => `${p.first_name || ''} ${p.last_name || ''}`.trim())
      .filter(Boolean);
  })();

  // v1.0.0e: empty list now renders an "alone" message rather than
  // suppressing the tooltip outright. The organiser asked: hovering
  // a code that turns out to be a singleton should explicitly say so,
  // not stay silent (silence reads as "loading" or "broken").
  const tooltipText = names.length > 0
    ? t('group_code.tooltip.with', { names: formatNamesList(names, lang) })
    : t('group_code.tooltip.alone');

  // ─── Handlers ───

  const handleHoverOpen = useCallback(() => {
    if (!isTouch) setOpen(true);
  }, [isTouch]);

  const handleHoverClose = useCallback(() => {
    if (isTouch) return;
    // Tiny delay lets focus moves into the popover settle first.
    setTimeout(() => {
      if (popoverRef.current && document.activeElement
          && popoverRef.current.contains(document.activeElement)) return;
      setOpen(false);
    }, 80);
  }, [isTouch]);

  const handleTouchStart = useCallback(() => {
    longPressFired.current = false;
    if (longPressTimer.current) clearTimeout(longPressTimer.current);
    longPressTimer.current = setTimeout(() => {
      longPressFired.current = true;
      setOpen(true);
      // Light haptic feedback on supported devices — confirms the
      // gesture without being intrusive. No-op on iOS Safari (which
      // doesn't expose vibrate) and on desktop browsers.
      if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
        try { navigator.vibrate(10); } catch { /* ignore */ }
      }
    }, LONG_PRESS_MS);
  }, []);

  const cancelLongPress = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  // ─── Compose handlers onto the child ───

  if (!isValidElement(children)) {
    return children;
  }

  const childOnClick = children.props.onClick;
  const childOnMouseEnter = children.props.onMouseEnter;
  const childOnMouseLeave = children.props.onMouseLeave;
  const childOnTouchStart = children.props.onTouchStart;
  const childOnTouchEnd = children.props.onTouchEnd;
  const childOnTouchMove = children.props.onTouchMove;
  const childOnTouchCancel = children.props.onTouchCancel;

  const wrappedChild = cloneElement(children, {
    ref: (node) => {
      triggerRef.current = node;
      const childRef = children.ref;
      if (typeof childRef === 'function') childRef(node);
      else if (childRef && typeof childRef === 'object') childRef.current = node;
    },
    // v1.0.0e: suppress the browser's native long-press behaviour so
    // our 500 ms timer can fire cleanly. Without these, Android Chrome
    // and iOS Safari race us with their own long-press: text selection
    // (Android), text-selection callout (iOS). Both can fire
    // `touchcancel` before our timer completes, which our cancel
    // handler then catches — and the tooltip never opens.
    //   user-select: none      — no text selection on long-press
    //   -webkit-touch-callout: none — no iOS callout menu
    //   touch-action: manipulation  — short-circuit the gesture stack
    //                                 so the browser doesn't wait
    //                                 for double-tap zoom either
    style: {
      ...children.props.style,
      userSelect: 'none',
      WebkitUserSelect: 'none',
      WebkitTouchCallout: 'none',
      touchAction: 'manipulation',
    },
    onMouseEnter: (e) => {
      handleHoverOpen();
      if (childOnMouseEnter) childOnMouseEnter(e);
    },
    onMouseLeave: (e) => {
      handleHoverClose();
      if (childOnMouseLeave) childOnMouseLeave(e);
    },
    onTouchStart: (e) => {
      handleTouchStart();
      if (childOnTouchStart) childOnTouchStart(e);
    },
    onTouchEnd: (e) => {
      cancelLongPress();
      if (childOnTouchEnd) childOnTouchEnd(e);
    },
    onTouchMove: (e) => {
      cancelLongPress();
      if (childOnTouchMove) childOnTouchMove(e);
    },
    onTouchCancel: (e) => {
      cancelLongPress();
      if (childOnTouchCancel) childOnTouchCancel(e);
    },
    onClick: (e) => {
      // Synthetic click after a long-press touchend — suppress so the
      // child's onClick (e.g. enter inline edit mode) doesn't fire on
      // top of the just-opened tooltip. Reset the flag so subsequent
      // genuine clicks work normally.
      if (longPressFired.current) {
        longPressFired.current = false;
        e.preventDefault();
        e.stopPropagation();
        return;
      }
      // Close any open popover when the user clicks the badge — both
      // desktop hover state and any accidental touch state. Then
      // delegate to the child's own onClick (edit mode, etc.).
      if (open) setOpen(false);
      if (childOnClick) childOnClick(e);
    },
    'aria-describedby': open ? titleId : undefined,
    tabIndex: children.props.tabIndex ?? 0,
  });

  return (
    <span className="relative inline-block">
      {wrappedChild}

      {/* Desktop popover */}
      {open && !isTouch && (
        <div
          ref={popoverRef}
          id={titleId}
          role="tooltip"
          className="absolute left-0 top-full mt-1 z-30 rounded-card shadow-lg p-2.5 max-w-xs"
          style={{
            background: 'var(--card-bg-solid)',
            border: '1px solid var(--card-border)',
            color: 'var(--text-primary)',
            whiteSpace: 'normal',
          }}
        >
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {tooltipText}
          </p>
        </div>
      )}

      {/* Mobile bottom sheet */}
      {open && isTouch && (
        <div
          className="fixed inset-0 z-50 flex items-end"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-labelledby={titleId}
            className="w-full rounded-t-2xl p-5 pb-[calc(1.25rem+env(safe-area-inset-bottom))]"
            style={{
              background: 'var(--card-bg-solid)',
              borderTop: '1px solid var(--card-border)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <p
                id={titleId}
                className="font-mono text-sm font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {code}
              </p>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label={t('common.close')}
                className="text-lg leading-none shrink-0"
                style={{ color: 'var(--text-subtle)' }}
              >
                ✕
              </button>
            </div>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {tooltipText}
            </p>
          </div>
        </div>
      )}
    </span>
  );
}
