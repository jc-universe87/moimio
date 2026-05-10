import { useState, useRef, useEffect, useCallback } from 'react';
import { useI18n } from './useI18n';
import { formatErrorMessage } from '../services/api';

/**
 * useToast — ephemeral feedback notifications.
 *
 * v0.70d-1: promoted from the inline pattern in AllocationBoard /
 * EventsPage / others into a shared hook so every surface that needs
 * a transient "Saved" / "Something failed" message uses the same
 * code path and visual language.
 *
 * R2: replaces the six native `alert()` calls in AllocationBoard +
 * OrganiseDashboard. Those alerts were jarring, uncomposable, and
 * off-brand; a toast in the same spot the success pattern already
 * used is a direct improvement without new component surface area.
 *
 * R8a: the rendered toast uses semantic tokens. Success = io-accent
 * (steel-blue / gold); error = alert-burgundy; info = card surface
 * with card border. No raw green hex (#1E7A34) — the v0.70c sweep
 * missed this because it was in inline-style hex literals, not
 * Tailwind classes.
 *
 * v1.0.0e: 'warning' variant added — brand Gold (#FFD700) with deep-
 * navy text. Used for soft, take-note messages that don't carry the
 * severity of an error: e.g. a manual move that breaks a constraint
 * the engine had honoured. The variant intentionally sits between
 * success (positive) and error (blocking); the user does not need to
 * acknowledge it, but it should catch the eye.
 *
 * Usage:
 *
 *   const { toast, showToast, ToastHost } = useToast();
 *   // ... somewhere in the component JSX:
 *   <ToastHost />
 *   // ... somewhere else:
 *   showToast('Saved', 'success');
 *   showToast(err, 'error');
 *   showToast('Running engine…', 'info');
 *   showToast('Moved away from cluster', 'warning');
 *
 * The ToastHost is a ready-rendered element; drop it once per hook
 * call inside your component's JSX tree. It self-positions via
 * `position: fixed`, so it can live anywhere in the render.
 *
 * Notes:
 *   - The default duration is 3 s. Override per-call via the third
 *     argument if needed (e.g. 5 s for long error messages).
 *   - Only one toast visible at a time. A new showToast replaces
 *     the current one. Rapid-fire toasts (e.g. save → success →
 *     another save → success) collapse to the latest, which is
 *     correct UX.
 *   - Timer is cleared on unmount — no setState-after-unmount warnings.
 */
export function useToast() {
  const { t } = useI18n();
  const [toast, setToast] = useState(null); // { msg, type }
  const timerRef = useRef(null);

  const showToast = useCallback((input, type = 'info', durationMs = null) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    // v1.0.0e: warnings carry information the organiser needs to read
    // (e.g. "moved away from group SMITH-742"). 3 seconds is too fast
    // to register a name + a constraint context, so warnings get a
    // longer default (10 s) and the rendered toast adds a manual
    // close button. Other variants keep the prior 3 s default and
    // still auto-dismiss without ceremony. Explicit `durationMs`
    // overrides everything.
    const effectiveDuration = durationMs ?? (type === 'warning' ? 10000 : 3000);
    // v0.70d-3c-8: accept either a translated string OR an Error
    // object (with i18nKey / friendlyKey / message). When an Error is
    // passed, resolve to the translated primary line via
    // formatErrorMessage so toasts no longer leak bracketed keys.
    let msg;
    if (input && typeof input === 'object' && (input.i18nKey || input.friendlyKey || input.message)) {
      const { primary } = formatErrorMessage(input, t);
      msg = primary;
    } else {
      msg = input;
    }
    setToast({ msg, type });
    timerRef.current = setTimeout(() => setToast(null), effectiveDuration);
  }, [t]);

  const clearToast = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setToast(null);
  }, []);

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  const ToastHost = useCallback(() => {
    if (!toast) return null;
    // v0.70d-1: semantic tokens per R8a. Success = io-accent (adapts
    // light/dark via CSS var), error = burgundy, info = card surface.
    // `--io-accent` renders steel-blue in light mode, gold in dark.
    // Gold-on-white text needs deep-navy foreground, so we switch
    // the text colour too. Everywhere else white-on-saturated is fine.
    const isSuccess = toast.type === 'success';
    const isError = toast.type === 'error';
    const isWarning = toast.type === 'warning';
    // v1.0.0e warning: brand Gold (#FFD700) with deep-navy text.
    // Hardcoded hex matches the canonical alert pair from the brand
    // tokens (Gold + Deep Navy). The toast renders with the optional
    // exclamation prefix to read as "take note" rather than blocking.
    return (
      <div
        className="fixed top-[calc(1rem+env(safe-area-inset-top))] right-[calc(1rem+env(safe-area-inset-right))] z-50 px-4 py-2.5 rounded-xl shadow-lg text-sm font-medium max-w-sm flex items-start gap-3"
        role="status"
        aria-live="polite"
        style={{
          background: isSuccess
            ? 'var(--io-accent)'
            : isError
              ? 'var(--alert-burgundy)'
              : isWarning
                ? '#FFD700'
                : 'var(--card-bg-solid)',
          // Dark-mode gold accent needs dark foreground to stay legible.
          // Light-mode steel-blue is fine with white text. Using
          // the var-based approach so the same utility carries both.
          // Warning is gold-on-navy regardless of theme.
          color: isSuccess
            ? 'var(--on-accent)'
            : isError
              ? '#fff'
              : isWarning
                ? '#0F1E2E'
                : 'var(--text-primary)',
          border: isSuccess || isError || isWarning
            ? 'none'
            : '1px solid var(--card-border)',
        }}
      >
        <span className="flex-1 min-w-0">
          {isWarning && (
            <span aria-hidden="true" style={{ marginRight: '0.5em', fontWeight: 700 }}>!</span>
          )}
          {toast.msg}
        </span>
        {/* v1.0.0e: warnings get a manual close button so the organiser
            can dismiss them as soon as they've read the message. The 10s
            auto-dismiss still applies as a backstop. Other variants
            don't render a close button — their 3s window is short
            enough that an X would be noise. */}
        {isWarning && (
          <button
            type="button"
            onClick={clearToast}
            aria-label="Close"
            className="shrink-0 leading-none text-base font-bold opacity-70 hover:opacity-100 transition-opacity"
            style={{ color: '#0F1E2E' }}
          >
            ✕
          </button>
        )}
      </div>
    );
  }, [toast, clearToast]);

  return { toast, showToast, clearToast, ToastHost };
}
