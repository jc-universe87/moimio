/**
 * UpdatePrompt — v0.59d, reliability hardened in v0.73d, further in v0.99c.
 *
 * Two roles:
 *
 * 1. Registers the service worker on mount (via `useRegisterSW` from
 *    vite-plugin-pwa's virtual module). This is the ONLY call site
 *    for SW registration — the plugin's `injectRegister` option is
 *    set to null in vite.config.js to avoid double-registration.
 *
 * 2. Surfaces two user-facing notifications:
 *    - "Update available" toast with a Refresh button, shown when a
 *      new SW has installed and is waiting. User clicks Refresh ->
 *      updateServiceWorker(true) posts SKIP_WAITING to the waiting
 *      SW and reloads the page with the new version active.
 *    - "Ready to use offline" toast, shown briefly (auto-dismisses
 *      after 4s) when the SW finishes its initial precache. This is
 *      a one-time notification per SW install — not repeated on
 *      every subsequent reload.
 *
 * v0.73d reliability fixes:
 *   Q1c — visibilitychange-driven update check.
 *   Q2c — state-aware refresh button with reload fallback.
 *   Q3d' — suppress stale needRefresh events.
 *
 * v0.99c reliability fixes (real-use feedback across browsers):
 *
 *   R1 — explicit update check on initial registration. Pre-fix, the
 *   only triggers were 60-min poll and visibilitychange. Visibility
 *   doesn't fire on initial page load, and the poll is too slow. On
 *   Chrome/DDG users opening a fresh tab after a deploy would not
 *   see the prompt until they switched tabs and back. The new flow
 *   calls registration.update() once immediately after registration,
 *   so the check happens within the first second of any page load.
 *
 *   R2 — poll interval reduced from 60min to 15min. The 60min was
 *   set when visibility-change was the primary trigger; with the
 *   initial-load check now in place, 15min is a tighter safety net
 *   without being a noticeable network burden (one HEAD-equivalent
 *   to /sw.js per quarter hour).
 *
 *   R3 — refresh-button watchdog. Pre-fix, step 1 (waiting SW
 *   present) called updateServiceWorker(true) and trusted the plugin
 *   to fire `controllerchange` and reload. On certain Chromium
 *   multi-tab scenarios `controllerchange` doesn't fire, leaving the
 *   button spinning forever. The new flow waits 5 seconds; if the
 *   page hasn't reloaded by then, falls through to the hard-reload
 *   fallback (clear precache + window.location.reload).
 *
 *   R4 — update-in-progress flag. After the user clicks Refresh, we
 *   set a sessionStorage marker with the timestamp. On next page
 *   load (which happens immediately after the refresh), if a fresh
 *   needRefresh fires within 30s of the marker, treat it as stale
 *   and suppress. This kills the Safari "prompt comes back even
 *   though we just updated" symptom — Safari's SW lifecycle
 *   sometimes generates spurious update events right after activation.
 *   The 30s window is generous enough to absorb load + lifecycle
 *   settling, short enough that a real update arriving 30s+ later
 *   still prompts normally.
 *
 * Mounted in AdminLayout alongside InstallPrompt.
 */

import { useEffect, useRef, useState } from 'react';
// `virtual:pwa-register/react` is a build-time virtual module injected
// by vite-plugin-pwa. No eslint disable comment needed — the project
// doesn't use eslint-plugin-import, and the plugin resolves this
// import correctly at build time.
import { useRegisterSW } from 'virtual:pwa-register/react';
import { useI18n } from '../hooks/useI18n';

const OFFLINE_TOAST_MS = 4000;
const POLL_INTERVAL_MS = 15 * 60 * 1000;       // R2: 15 min safety net
const STALE_RECHECK_MS = 500;                  // Q3d' delay
const FORCED_UPDATE_WAIT_MS = 1500;            // Q2c step-2 wait
const REFRESH_WATCHDOG_MS = 5000;              // R3: step-1 watchdog
const UPDATE_IN_PROGRESS_KEY = 'moimio_update_in_progress';
const UPDATE_GRACE_MS = 30 * 1000;             // R4: post-refresh grace

export default function UpdatePrompt() {
  const { t } = useI18n();
  const registrationRef = useRef(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    needRefresh: [needRefresh, setNeedRefresh],
    offlineReady: [offlineReady, setOfflineReady],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(swUrl, registration) {
      registrationRef.current = registration || null;
      if (registration) {
        // R1: explicit update check on initial registration. Catches
        // the "fresh tab opened after deploy" case where neither
        // visibilitychange nor the poll has fired yet. Idempotent and
        // cheap on the SW side; if there's no new build, nothing
        // happens.
        try { registration.update(); } catch { /* ignore */ }

        // R2: 15-min poll as safety net (was 60min in v0.73d).
        setInterval(() => {
          try { registration.update(); } catch { /* ignore */ }
        }, POLL_INTERVAL_MS);
      }
    },
    onRegisterError(err) {
      console.warn('[moimio] SW registration failed', err);
    },
  });

  // Q1c — visibilitychange-driven update check. When the tab becomes
  // visible, force registration.update() to detect new builds.
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== 'visible') return;
      const reg = registrationRef.current;
      if (reg) {
        try { reg.update(); } catch { /* ignore */ }
      }
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, []);

  // Q3d' + R4 — when needRefresh flips, decide whether it's a real
  // update or a stale / post-refresh event.
  useEffect(() => {
    if (!needRefresh) return undefined;

    // R4: if we just initiated a refresh in the last 30s, this
    // needRefresh event is the SW lifecycle catching up after
    // activation, not a fresh new update. Suppress.
    try {
      const updateAt = parseInt(sessionStorage.getItem(UPDATE_IN_PROGRESS_KEY) || '0', 10);
      if (updateAt && Date.now() - updateAt < UPDATE_GRACE_MS) {
        setNeedRefresh(false);
        return undefined;
      }
      // Marker is stale — clean it up so we don't accumulate state.
      if (updateAt) sessionStorage.removeItem(UPDATE_IN_PROGRESS_KEY);
    } catch { /* sessionStorage may be unavailable in private mode etc */ }

    // Q3d': verify there's actually a waiting worker after a 500ms
    // settling window. If not, the event was stale — suppress.
    const id = setTimeout(() => {
      const reg = registrationRef.current;
      if (!reg || !reg.waiting) {
        setNeedRefresh(false);
      }
    }, STALE_RECHECK_MS);
    return () => clearTimeout(id);
  }, [needRefresh, setNeedRefresh]);

  // Auto-dismiss the offline-ready toast after a few seconds.
  useEffect(() => {
    if (!offlineReady) return undefined;
    const id = setTimeout(() => setOfflineReady(false), OFFLINE_TOAST_MS);
    return () => clearTimeout(id);
  }, [offlineReady, setOfflineReady]);

  // Q2c + R3 — state-aware refresh with watchdog and reload fallback.
  //
  // Step 1: if a waiting SW is present, post SKIP_WAITING via the
  //   plugin and wait up to 5s for the page to reload. If it doesn't
  //   (controllerchange didn't fire — known Chromium multi-tab
  //   issue), fall through to the hard-reload path (R3).
  // Step 2: if no waiting SW, force registration.update() and wait
  //   1.5s for an install round-trip. Re-check waiting.
  // Step 3: nothing reached the plugin's normal path. Clear precache
  //   and hard reload.
  const handleRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);

    // R4: mark refresh start so a needRefresh that fires post-reload
    // is recognised as stale.
    try {
      sessionStorage.setItem(UPDATE_IN_PROGRESS_KEY, String(Date.now()));
    } catch { /* ignore */ }

    try {
      const reg = registrationRef.current;

      // Step 1.
      if (reg?.waiting) {
        updateServiceWorker(true);
        // R3 watchdog: if updateServiceWorker doesn't fire its own
        // reload within 5s, fall through to step 3.
        await new Promise(r => setTimeout(r, REFRESH_WATCHDOG_MS));
        // If we're still here, the plugin didn't reload us. Force it.
        await hardReload();
        return;
      }

      // Step 2: force a check.
      if (reg) {
        try { await reg.update(); } catch { /* ignore */ }
        await new Promise(r => setTimeout(r, FORCED_UPDATE_WAIT_MS));
      }

      // Re-check after the wait.
      if (reg?.waiting) {
        updateServiceWorker(true);
        await new Promise(r => setTimeout(r, REFRESH_WATCHDOG_MS));
        await hardReload();
        return;
      }

      // Step 3: nothing reachable through the plugin's normal path.
      await hardReload();
    } finally {
      setIsRefreshing(false);
    }
  };

  // Shared hard-reload helper used by R3 fallback and step 3. Clears
  // the precache so the next page load cannot be served stale shell,
  // then forces a hard navigation. caches.delete is best-effort.
  const hardReload = async () => {
    try {
      if (typeof caches !== 'undefined') {
        const keys = await caches.keys();
        await Promise.all(keys.map(k => caches.delete(k)));
      }
    } catch { /* ignore */ }
    window.location.reload();
  };

  const handleDismissUpdate = () => {
    setNeedRefresh(false);
  };

  // Render guard. Even if state hasn't propagated yet from the
  // setTimeout above, this is a belt-and-braces check at render time:
  // we only render the update toast when there's actually a waiting
  // worker.
  const reg = registrationRef.current;
  const showUpdate = needRefresh && reg && reg.waiting;

  if (!showUpdate && !offlineReady) return null;

  // Style matches InstallPrompt: bottom banner, card-surface-solid,
  // border-top, safe-area-inset-bottom (v0.59a convention).
  return (
    <div
      className="fixed left-0 right-0 bottom-0 z-30 px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]"
      style={{
        background: 'var(--card-bg-solid)',
        borderTop: '1px solid var(--card-border)',
        boxShadow: '0 -4px 16px rgba(0,0,0,0.08)',
      }}
      role="status"
      aria-live="polite"
      aria-label={showUpdate ? t('update.title') : t('update.offline_ready')}>
      <div className="max-w-2xl mx-auto flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {showUpdate ? (
            <>
              <p className="font-heading font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
                {t('update.title')}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                {t('update.subtitle')}
              </p>
            </>
          ) : (
            <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
              {t('update.offline_ready')}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0 pt-0.5">
          {showUpdate && (
            <>
              <button
                type="button"
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors disabled:opacity-70 disabled:cursor-wait inline-flex items-center gap-1.5">
                {isRefreshing && (
                  <span className="inline-block animate-spin" aria-hidden="true">⟳</span>
                )}
                {t('update.refresh')}
              </button>
              <button
                type="button"
                onClick={handleDismissUpdate}
                disabled={isRefreshing}
                aria-label={t('common.close')}
                className="text-xs px-2 py-1.5 rounded-card hover:bg-black/5 dark:hover:bg-white/10 transition-colors disabled:opacity-50"
                style={{ color: 'var(--text-subtle)' }}>
                ✕
              </button>
            </>
          )}
          {offlineReady && !showUpdate && (
            <button
              type="button"
              onClick={() => setOfflineReady(false)}
              aria-label={t('common.close')}
              className="text-xs px-2 py-1.5 rounded-card hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              style={{ color: 'var(--text-subtle)' }}>
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
