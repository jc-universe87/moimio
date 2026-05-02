/**
 * InstallPrompt — v0.59b.
 *
 * Polite, dismissible banner at the bottom of admin pages. Two paths:
 *
 * 1. Chromium-based browsers (Chrome, Edge, Android Chrome, Brave):
 *    the `beforeinstallprompt` event fires when the site meets the
 *    browser's installability heuristics (valid manifest + engagement).
 *    We preventDefault() to suppress the browser's own banner, stash
 *    the event, and fire it later via `event.prompt()` when the user
 *    taps our "Install" button.
 *
 * 2. iOS Safari: `beforeinstallprompt` never fires — iOS only supports
 *    manual install via the Share menu. We detect iOS and show a
 *    text-only hint ("tap Share, then Add to Home Screen"). No
 *    automation is possible on iOS before Safari 17.4 and probably
 *    never for the full web-install flow.
 *
 * Gating rules (any of these hides the banner):
 *   - App is already in standalone mode (`display-mode: standalone`,
 *     or iOS's `window.navigator.standalone`).
 *   - User dismissed within the last 7 days (localStorage TTL).
 *   - `appinstalled` event already fired this session.
 *
 * Mounted once in AdminLayout so it only appears post-login, never on
 * public /register or /login pages — event participants who register
 * once should not be prompted to install an admin tool.
 *
 * Note on Chromium installability: as of 2024, Chromium requires a
 * service worker (with a `fetch` handler) before `beforeinstallprompt`
 * will fire. That ships in v0.59c. Until then, this banner is active
 * on iOS only; desktop/Android users can still install manually via
 * the browser's address-bar install icon. v0.59c completes the story.
 */

import { useState, useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';

const DISMISS_KEY = 'moimio.install.dismissed_at';
const DISMISS_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function isStandalone() {
  try {
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) return true;
    // iOS Safari exposes standalone on navigator, not via media query
    if (window.navigator.standalone === true) return true;
  } catch { /* ignore */ }
  return false;
}

function isIOS() {
  try {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  } catch { return false; }
}

function isDismissed() {
  try {
    const raw = localStorage.getItem(DISMISS_KEY);
    if (!raw) return false;
    const ts = parseInt(raw, 10);
    if (!Number.isFinite(ts)) return false;
    return (Date.now() - ts) < DISMISS_TTL_MS;
  } catch { return false; }
}

function markDismissed() {
  try { localStorage.setItem(DISMISS_KEY, String(Date.now())); } catch { /* ignore */ }
}

export default function InstallPrompt() {
  const { t } = useI18n();
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [mode, setMode] = useState(null); // 'native' | 'ios' | null

  useEffect(() => {
    if (isStandalone()) return;
    if (isDismissed()) return;

    const onBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setMode('native');
    };

    const onAppInstalled = () => {
      setDeferredPrompt(null);
      setMode(null);
      // appinstalled is also a signal to stop prompting — set TTL as
      // belt-and-braces even though standalone detection handles it next boot.
      markDismissed();
    };

    window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt);
    window.addEventListener('appinstalled', onAppInstalled);

    // iOS path — no event to wait for; set mode once if we detect iOS
    // Safari running outside standalone (which is already checked above).
    if (isIOS()) {
      setMode('ios');
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt);
      window.removeEventListener('appinstalled', onAppInstalled);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    try {
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice && choice.outcome === 'dismissed') {
        markDismissed();
      }
    } catch { /* user cancelled or unsupported — treat as dismiss */ }
    setDeferredPrompt(null);
    setMode(null);
  };

  const handleDismiss = () => {
    markDismissed();
    setMode(null);
  };

  if (mode === null) return null;

  return (
    <div
      className="fixed left-0 right-0 bottom-0 z-30 px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]"
      style={{
        background: 'var(--card-bg-solid)',
        borderTop: '1px solid var(--card-border)',
        boxShadow: '0 -4px 16px rgba(0,0,0,0.08)',
      }}
      role="dialog"
      aria-label={t('install.title')}>
      <div className="max-w-2xl mx-auto flex items-start gap-3">
        <img
          src="/icon-192.png"
          alt=""
          className="w-10 h-10 rounded-lg shrink-0"
          style={{ border: '1px solid var(--card-border)' }}
        />
        <div className="flex-1 min-w-0">
          <p className="font-heading font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
            {t('install.title')}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            {mode === 'ios' ? t('install.ios_hint') : t('install.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 pt-0.5">
          {mode === 'native' && (
            <button
              type="button"
              onClick={handleInstall}
              className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors">
              {t('install.button')}
            </button>
          )}
          <button
            type="button"
            onClick={handleDismiss}
            aria-label={t('install.dismiss')}
            title={t('install.dismiss')}
            className="text-xs px-2 py-1.5 rounded-card hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-subtle)' }}>
            {mode === 'ios' ? t('install.dismiss') : '✕'}
          </button>
        </div>
      </div>
    </div>
  );
}
