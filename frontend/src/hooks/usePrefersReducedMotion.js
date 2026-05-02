/**
 * usePrefersReducedMotion — v0.70d-2c (R3-C-hybrid)
 *
 * Returns true if the user has requested reduced motion at the OS /
 * browser level (`@media (prefers-reduced-motion: reduce)`). Moimio's
 * welcome-panel motion components check this to decide whether to
 * animate or snap to the final state.
 *
 * Reacts live if the user toggles the OS setting mid-session (rare but
 * correct) — the MediaQueryList change listener keeps the state
 * current.
 *
 * SSR-safe: defaults to `false` (motion allowed) when `window` is
 * undefined, matching the default UX. The first client render picks
 * up the real value.
 */

import { useState, useEffect } from 'react';

const QUERY = '(prefers-reduced-motion: reduce)';

export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false;
    return window.matchMedia(QUERY).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mql = window.matchMedia(QUERY);
    const handler = (e) => setReduced(e.matches);
    // Safari < 14 still only supports the legacy addListener/removeListener
    // API. Use whichever is present — modern Chrome/Firefox/Edge/Safari
    // all expose addEventListener('change', ...).
    if (mql.addEventListener) {
      mql.addEventListener('change', handler);
      return () => mql.removeEventListener('change', handler);
    } else if (mql.addListener) {
      mql.addListener(handler);
      return () => mql.removeListener(handler);
    }
  }, []);

  return reduced;
}
