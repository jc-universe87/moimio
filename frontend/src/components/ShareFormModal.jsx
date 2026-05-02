/**
 * ShareFormModal — share a registration form URL.
 *
 * Contents:
 *   - QR code (generated client-side via the qrcode package)
 *   - The URL in a read-only input with a "Copy" button
 *   - A "Share…" button that invokes navigator.share() where available,
 *     falling back to clipboard copy on desktop browsers.
 *
 * Note on non-HTTPS contexts:
 *   The modern clipboard API (navigator.clipboard.writeText) and
 *   navigator.share() both require a "secure context" — which means
 *   HTTPS, localhost, or 127.0.0.1. On a plain-HTTP LAN address like
 *   192.168.x.x they silently fail.
 *
 *   We therefore try the modern API first and fall back to the legacy
 *   `document.execCommand('copy')` path on a selected <textarea>, which
 *   works without HTTPS. For share, we also pre-check availability before
 *   wiring up the button.
 *
 * Props:
 *   - url        the full registration URL to share
 *   - eventName  used in the native share text
 *   - onClose    modal close handler
 */

import { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { useI18n } from '../hooks/useI18n';
import { useTheme } from '../hooks/useTheme';

// Legacy clipboard fallback — selects a textarea and runs execCommand('copy').
// Works on basically every browser from the last 15 years, no HTTPS needed.
function legacyCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.top = '0';
  ta.style.left = '0';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  ta.setSelectionRange(0, text.length);
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}

// Best-effort copy: modern API first, legacy fallback on failure. Returns
// true on success, false if both paths fail (user will need to copy
// manually from the selected input).
async function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fall through
    }
  }
  return legacyCopy(text);
}

export default function ShareFormModal({ url, eventName, onClose }) {
  const { t } = useI18n();
  const { effective } = useTheme();
  const isDark = effective === 'dark';
  const [qrDataUrl, setQrDataUrl] = useState('');
  // 'idle' | 'copied' | 'failed'
  const [copyState, setCopyState] = useState('idle');
  // Whether the browser exposes navigator.share at all. Spec says it
  // requires a secure context, but Chrome Mobile (and some others)
  // actually allow it over plain HTTP — so we just probe for the API
  // and let the call itself decide. The catch clause below distinguishes
  // user-cancellation from genuine failures.
  const [canNativeShare] = useState(
    () => typeof navigator !== 'undefined' &&
          typeof navigator.share === 'function'
  );

  // Render the QR to a data URL once we have the URL. Re-render when
  // theme changes so colours stay legible against the backdrop.
  useEffect(() => {
    if (!url) return;
    QRCode.toDataURL(url, {
      errorCorrectionLevel: 'M',
      margin: 1,
      width: 256,
      color: {
        dark:  isDark ? '#F7F5F2' : '#0F1E2E',
        light: '#00000000', // transparent background
      },
    }).then(setQrDataUrl).catch(() => setQrDataUrl(''));
  }, [url, isDark]);

  const handleCopy = async () => {
    const ok = await copyToClipboard(url);
    setCopyState(ok ? 'copied' : 'failed');
    // Also select the input visually so the user can copy manually if
    // the automatic copy failed.
    const input = document.getElementById('share-url-input');
    if (input) input.select();
    setTimeout(() => setCopyState('idle'), 2000);
  };

  const handleNativeShare = async () => {
    const shareText = t('reg_phase.share.native_text', { event: eventName || '' });
    if (canNativeShare) {
      try {
        await navigator.share({ title: shareText, text: shareText, url });
      } catch (err) {
        // AbortError = user dismissed the share sheet. Anything else is
        // a real failure (NotAllowedError, browser refused, etc.) — fall
        // back to copy so the user still gets something useful.
        if (err && err.name !== 'AbortError') {
          handleCopy();
        }
      }
    } else {
      // No share API at all — treat the button as Copy.
      handleCopy();
    }
  };

  const copyLabel = copyState === 'copied'
    ? t('reg_phase.share.copied')
    : copyState === 'failed'
    ? t('reg_phase.share.copy_failed')
    : t('reg_phase.share.copy');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.45)' }}
      onClick={onClose}
    >
      <div
        className="card-surface-solid rounded-2xl p-6 w-full max-w-sm"
        style={{ border: '1px solid var(--card-border)' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="share-modal-title"
      >
        <div className="flex items-start justify-between gap-3 mb-4">
          <h2
            id="share-modal-title"
            className="font-heading font-bold text-lg"
            style={{ color: 'var(--text-primary)' }}
          >
            {t('reg_phase.share.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            className="text-lg leading-none px-1 hover:opacity-70"
            style={{ color: 'var(--text-subtle)' }}
          >
            ×
          </button>
        </div>

        {/* QR */}
        {qrDataUrl && (
          <div className="flex flex-col items-center mb-4">
            <div
              className="rounded-xl p-3"
              style={{
                background: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)',
                border: '1px solid var(--card-border)',
              }}
            >
              <img
                src={qrDataUrl}
                alt={t('reg_phase.share.qr_label')}
                width={192}
                height={192}
                style={{ display: 'block' }}
              />
            </div>
            <p className="text-[10px] uppercase tracking-caps mt-2" style={{ color: 'var(--text-subtle)' }}>
              {t('reg_phase.share.qr_label')}
            </p>
          </div>
        )}

        {/* Link */}
        <div className="mb-3">
          <label
            className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
            style={{ color: 'var(--text-subtle)' }}
          >
            {t('reg_phase.share.link_label')}
          </label>
          <div className="flex items-stretch gap-2">
            <input
              id="share-url-input"
              type="text"
              value={url}
              readOnly
              onFocus={(e) => e.target.select()}
              className="flex-1 min-w-0 rounded-card border px-2 py-1.5 text-xs font-mono"
              style={{
                background: 'var(--app-bg)',
                borderColor: 'var(--card-border)',
                color: 'var(--text-primary)',
              }}
            />
            <button
              type="button"
              onClick={handleCopy}
              className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap shrink-0"
              style={{
                borderColor: copyState === 'failed' ? 'var(--alert-burgundy)' : 'var(--card-border)',
                color: copyState === 'failed' ? 'var(--alert-burgundy)' : 'var(--text-muted)',
              }}
            >
              {copyLabel}
            </button>
            {/* v0.83 #18: direct Open ↗ link to the registration page —
                opens in a new tab so admins can preview without
                affecting their session. */}
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap shrink-0 flex items-center"
              style={{
                borderColor: 'var(--card-border)',
                color: 'var(--text-muted)',
              }}
            >
              {t('event.share.open_link')} ↗
            </a>
          </div>
          {copyState === 'failed' && (
            <p className="text-[10px] mt-1" style={{ color: 'var(--alert-burgundy)' }}>
              {t('reg_phase.share.copy_manual_hint')}
            </p>
          )}
        </div>

        {/* Native share (mobile) — only if the browser supports it */}
        {canNativeShare && (
          <button
            type="button"
            onClick={handleNativeShare}
            className="w-full text-xs font-semibold px-3 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80"
          >
            {t('reg_phase.share.native')}
          </button>
        )}
      </div>
    </div>
  );
}
