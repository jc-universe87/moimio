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
 * Usage:
 *
 *   const { toast, showToast, ToastHost } = useToast();
 *   // ... somewhere in the component JSX:
 *   <ToastHost />
 *   // ... somewhere else:
 *   showToast('Saved', 'success');
 *   showToast(err, 'error');
 *   showToast('Running engine…', 'info');
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

  const showToast = useCallback((input, type = 'info', durationMs = 3000) => {
    if (timerRef.current) clearTimeout(timerRef.current);
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
    timerRef.current = setTimeout(() => setToast(null), durationMs);
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
    return (
      <div
        className="fixed top-[calc(1rem+env(safe-area-inset-top))] right-[calc(1rem+env(safe-area-inset-right))] z-50 px-4 py-2.5 rounded-xl shadow-lg text-sm font-medium max-w-sm"
        role="status"
        aria-live="polite"
        style={{
          background: isSuccess
            ? 'var(--io-accent)'
            : isError
              ? 'var(--alert-burgundy)'
              : 'var(--card-bg-solid)',
          // Dark-mode gold accent needs dark foreground to stay legible.
          // Light-mode steel-blue is fine with white text. Using
          // the var-based approach so the same utility carries both.
          color: isSuccess
            ? 'var(--on-accent)'
            : isError
              ? '#fff'
              : 'var(--text-primary)',
          border: isSuccess || isError
            ? 'none'
            : '1px solid var(--card-border)',
        }}
      >
        {toast.msg}
      </div>
    );
  }, [toast]);

  return { toast, showToast, clearToast, ToastHost };
}
