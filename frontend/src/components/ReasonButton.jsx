import { useState, useRef, useEffect, useCallback, useId } from 'react';

/**
 * ReasonButton — a name on the allocation review surface that reveals
 * its placement reason on hover (desktop) or tap (mobile).
 *
 * v0.70d-1: introduced as part of R1. Every chip on the review
 * surface — in "Will be," in "Unplaced," in "Gender unknown" — is
 * wrapped in this component so the reasoning is discoverable without
 * visual clutter on first glance.
 *
 * Interaction (single component, dual behaviour):
 *
 *   ≥768 px (pointer-fine device): hover opens a popover below the
 *   name. Mouse leave closes. Click ALSO opens and pins; click
 *   elsewhere closes. Handles the mixed-input edge case (users
 *   who alternate mouse + keyboard).
 *
 *   <768 px (touch device): tap opens a half-screen bottom sheet.
 *   Tap scrim or close button dismisses. Keyboard-friendly by
 *   having a real `<button>` and `role="dialog"` on the sheet.
 *
 * The 768 px breakpoint is the same as the existing isMobileView
 * state in AllocationBoard — intentional consistency.
 *
 * Props:
 *   name            (required) — display string for the chip
 *   participantNumber           — optional # prefix (e.g. "#017")
 *   reasoning       (required) — plain-string body of the popover.
 *                                null suppresses the popover entirely
 *                                (for sites where reasoning is N/A).
 *   variant                     — 'placed' (default) | 'unplaced' |
 *                                'gender-unknown'
 *                                Changes chip visual only (background
 *                                tint, text colour). All three use
 *                                semantic tokens per R8.
 *   popoverTitleKey             — optional i18n key for the popover
 *                                title. Defaults to participant's name.
 *   t                           — i18n function from useI18n()
 *
 * Accessibility:
 *   - Uses <button>, not a div.
 *   - Popover has role="tooltip" on desktop; bottom sheet has
 *     role="dialog" + aria-labelledby.
 *   - Escape key dismisses both variants.
 *   - Focus returns to the originating button on dismiss.
 */
export default function ReasonButton({
  name,
  participantNumber,
  reasoning,
  variant = 'placed',
  pending = false,
  t,
}) {
  const [open, setOpen] = useState(false);
  const [isTouch, setIsTouch] = useState(() =>
    typeof window !== 'undefined'
      ? !window.matchMedia('(hover: hover) and (pointer: fine)').matches
      : false
  );
  const buttonRef = useRef(null);
  const popoverRef = useRef(null);
  // v0.70d-1-1: stable unique id for aria-labelledby. Previously built
  // from `name`, which collided on duplicate names and produced invalid
  // HTML for non-ASCII characters. useId is the React 19 idiom.
  const titleId = useId();

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined;
    const mq = window.matchMedia('(hover: hover) and (pointer: fine)');
    const update = () => setIsTouch(!mq.matches);
    // Modern browsers use `change` event; older Safari used addListener
    if (mq.addEventListener) {
      mq.addEventListener('change', update);
      return () => mq.removeEventListener('change', update);
    } else if (mq.addListener) {
      mq.addListener(update);
      return () => mq.removeListener(update);
    }
    return undefined;
  }, []);

  // Close on Escape
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  // Close desktop popover on outside click
  useEffect(() => {
    if (!open || isTouch) return undefined;
    const onClick = (e) => {
      if (buttonRef.current?.contains(e.target)) return;
      if (popoverRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open, isTouch]);

  const handleToggle = useCallback(() => {
    setOpen(o => !o);
  }, []);

  const handleHoverOpen = useCallback(() => {
    if (!isTouch) setOpen(true);
  }, [isTouch]);

  const handleHoverClose = useCallback(() => {
    // Desktop only, and only if the reason popover isn't focused.
    // We use a tiny setTimeout to allow focus moves into the popover.
    if (isTouch) return;
    setTimeout(() => {
      if (popoverRef.current && document.activeElement
          && popoverRef.current.contains(document.activeElement)) return;
      setOpen(false);
    }, 80);
  }, [isTouch]);

  // Style — R8-compliant. Three variants, all use semantic tokens.
  const chipStyle =
    variant === 'unplaced'
      ? { background: 'var(--alert-tint)', color: 'var(--alert-burgundy)' }
    : variant === 'gender-unknown'
      ? { background: 'var(--alert-tint)', color: 'var(--alert-burgundy)' }
      : { background: 'var(--accent-tint)', color: 'var(--io-accent)' };

  const label = participantNumber
    ? `${name} #${String(participantNumber).padStart(3, '0')}`
    : name;

  const hasReasoning = !!reasoning;

  // v0.73c: pending participants render in italic + slightly muted.
  // Layered on top of the variant chipStyle (which sets background and
  // base colour) so the pending signal is visible regardless of variant
  // (placed, unplaced, gender-unknown). Distinct from mark dots — those
  // are filled coloured circles inside the chip area; this is text styling.
  const pendingStyle = pending
    ? { fontStyle: 'italic', opacity: 0.7 }
    : null;

  return (
    <span className="relative inline-block">
      <button
        ref={buttonRef}
        type="button"
        onClick={hasReasoning ? handleToggle : undefined}
        onMouseEnter={hasReasoning ? handleHoverOpen : undefined}
        onMouseLeave={hasReasoning ? handleHoverClose : undefined}
        disabled={!hasReasoning}
        aria-haspopup={hasReasoning ? 'dialog' : undefined}
        aria-expanded={hasReasoning ? open : undefined}
        className={`text-xs px-2 py-0.5 rounded-full transition-opacity ${
          hasReasoning ? 'cursor-help hover:opacity-80' : 'cursor-default'
        }`}
        style={{ ...chipStyle, ...pendingStyle }}
        title={pending && t ? t('organise.pending_pill.tooltip') : undefined}
      >
        {label}
      </button>

      {/* Desktop popover */}
      {open && !isTouch && hasReasoning && (
        <div
          ref={popoverRef}
          role="tooltip"
          className="absolute left-0 top-full mt-1 z-30 rounded-card shadow-lg p-3 w-64"
          style={{
            background: 'var(--card-bg-solid)',
            border: '1px solid var(--card-border)',
            color: 'var(--text-primary)',
          }}
        >
          <p className="font-semibold text-sm mb-1"
             style={{ color: 'var(--text-primary)' }}>
            {label}
          </p>
          <p className="text-xs whitespace-pre-line" style={{ color: 'var(--text-muted)' }}>
            {reasoning}
          </p>
        </div>
      )}

      {/* Mobile bottom sheet */}
      {open && isTouch && hasReasoning && (
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
                className="font-semibold text-base"
                style={{ color: 'var(--text-primary)' }}
              >
                {label}
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
            <p className="text-sm whitespace-pre-line" style={{ color: 'var(--text-muted)' }}>
              {reasoning}
            </p>
          </div>
        </div>
      )}
    </span>
  );
}
