/**
 * forceReload — clear every cache this origin holds, then hard-reload (UPDATE-1).
 *
 * The escape hatch behind the Legal Notice modal's button, for a browser
 * that is holding a stale shell. It does exactly two things that matter:
 * empties `caches` (the Workbox precache and everything else) and calls
 * `window.location.reload()`, so the next load fetches every asset from the
 * origin.
 *
 * Before those it nudges the service worker with `registration.update()`.
 * That nudge is best effort and is not allowed to decide anything: the
 * previous version awaited it with no timeout, and an `update()` that never
 * settled meant the `finally` never ran, the reload never happened, and the
 * button spun until the modal was closed. Here it is raced against a short
 * timeout, so a quick install still gets a head start and a hang costs at
 * most UPDATE_NUDGE_MS.
 *
 * Nothing here checks a version, and the label on the button no longer
 * says it does.
 */

export const UPDATE_NUDGE_MS = 1500;

function withTimeout(promise, ms) {
  return new Promise((resolve) => {
    const id = setTimeout(resolve, ms);
    Promise.resolve(promise).then(
      () => { clearTimeout(id); resolve(); },
      () => { clearTimeout(id); resolve(); },
    );
  });
}

export async function forceReload({ nudgeMs = UPDATE_NUDGE_MS } = {}) {
  try {
    if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
      await withTimeout((async () => {
        const reg = await navigator.serviceWorker.getRegistration();
        if (reg) await reg.update();
      })(), nudgeMs);
    }
  } catch { /* the reload below is the answer either way */ }

  try {
    if (typeof caches !== 'undefined') {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    }
  } catch { /* partial cache state is replaced on the next load */ }

  window.location.reload();
}
