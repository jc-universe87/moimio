/**
 * forceReload — UPDATE-1.
 *
 * The one fault this pins: a service-worker `update()` that never settles
 * must not stop the reload. Also: caches are cleared, and the reload comes
 * even when the service worker API is absent or throws.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { forceReload } from './forceReload';

let reload;
let deleted;

beforeEach(() => {
  vi.useFakeTimers();
  reload = vi.fn();
  // window.location is not writable in jsdom; replace the object.
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { reload },
  });
  deleted = [];
  globalThis.caches = {
    keys: vi.fn(async () => ['workbox-precache-v2', 'moimio-fonts']),
    delete: vi.fn(async (k) => { deleted.push(k); return true; }),
  };
});

afterEach(() => {
  vi.useRealTimers();
  delete globalThis.caches;
  delete navigator.serviceWorker;
});

function setServiceWorker(update) {
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: { getRegistration: vi.fn(async () => ({ update })) },
  });
}

describe('forceReload', () => {
  it('still reloads when registration.update() never settles', async () => {
    setServiceWorker(() => new Promise(() => {}));   // hangs forever
    const p = forceReload({ nudgeMs: 1000 });
    await vi.advanceTimersByTimeAsync(999);
    expect(reload).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    await p;
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('clears every cache before reloading', async () => {
    setServiceWorker(async () => {});
    await forceReload({ nudgeMs: 1000 });
    expect(deleted.sort()).toEqual(['moimio-fonts', 'workbox-precache-v2']);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('reloads when update() rejects', async () => {
    setServiceWorker(async () => { throw new Error('nope'); });
    await forceReload({ nudgeMs: 1000 });
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('reloads when there is no service worker API at all', async () => {
    delete navigator.serviceWorker;
    await forceReload({ nudgeMs: 1000 });
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('does not wait out the timeout when update() settles quickly', async () => {
    setServiceWorker(async () => {});
    const p = forceReload({ nudgeMs: 60_000 });
    await vi.advanceTimersByTimeAsync(0);
    await p;
    expect(reload).toHaveBeenCalledTimes(1);
  });
});
