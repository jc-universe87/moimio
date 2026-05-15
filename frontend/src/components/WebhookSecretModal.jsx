import { useState, useRef, useEffect } from 'react';
import { useI18n } from '../hooks/useI18n';

/**
 * WebhookSecretModal — v1.0.0g.
 *
 * Sticky "show once" pattern for displaying a newly generated webhook
 * signing secret. The secret is never recoverable through the UI after
 * this modal closes; the admin must copy it now or rotate to get a new
 * one.
 *
 * Sticky: the modal refuses to close on click-outside or Escape. The
 * user must check the "I have saved this" box and click Done.
 *
 * Clipboard fallback (v1.0.0g): the Clipboard API requires a secure
 * context (HTTPS or localhost). Self-hosters often access the admin UI
 * over plain HTTP on a LAN IP (e.g. 192.168.x.x), where navigator
 * .clipboard.writeText silently fails. We fall back to the legacy
 * document.execCommand('copy') flow which works on any origin.
 *
 * State reset (v1.0.0g-2): returning null from a component's render
 * does NOT unmount it — useState values persist across open/close
 * cycles. We explicitly reset `acknowledged` and `copied` whenever the
 * modal opens with a (possibly new) endpoint, so the admin must
 * actively re-confirm every time. This is the safeguard rationale —
 * the checkbox is meant to be friction, not a sticky preference.
 *
 * Props:
 *   open       — boolean
 *   endpoint   — { name, url, secret }
 *   onAck      — called when user clicks "I have saved this"
 */
export default function WebhookSecretModal({ open, endpoint, onAck }) {
  const { t } = useI18n();
  const [acknowledged, setAcknowledged] = useState(false);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef(null);

  // Reset on every open / endpoint change. v1.0.0g-2 fix for sticky
  // checkbox: previously the acknowledge tick survived across opens
  // because returning null doesn't unmount the component.
  useEffect(() => {
    if (open) {
      setAcknowledged(false);
      setCopied(false);
    }
  }, [open, endpoint?.secret]);

  if (!open || !endpoint) return null;

  const handleCopy = async () => {
    let succeeded = false;

    // Modern path — works on HTTPS / localhost.
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(endpoint.secret);
        succeeded = true;
      } catch {
        // Fall through to legacy path
      }
    }

    // Legacy path — works over HTTP on LAN IPs, where most self-hosters
    // will access the admin UI. Requires a real DOM selection.
    if (!succeeded && inputRef.current) {
      try {
        inputRef.current.focus();
        inputRef.current.select();
        inputRef.current.setSelectionRange(0, endpoint.secret.length);
        succeeded = document.execCommand('copy');
      } catch {
        succeeded = false;
      }
    }

    if (succeeded) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } else if (inputRef.current) {
      // Final fallback: at least select the text so the user can copy
      // manually with Ctrl+C / long-press.
      inputRef.current.focus();
      inputRef.current.select();
    }
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: 'rgba(0,0,0,0.65)' }}
      onClick={(e) => e.stopPropagation()}
    >
      <div
        className="w-full max-w-lg rounded-lg shadow-xl p-6"
        style={{
          background: 'var(--card-bg-solid)',
          color: 'var(--text-primary)',
          border: '1px solid var(--card-border)',
        }}
      >
        <h2
          className="text-lg font-semibold mb-2"
          style={{ color: 'var(--text-primary)' }}
        >
          {t('webhooks.secret_modal.title')}
        </h2>
        <p
          className="text-sm mb-4"
          style={{ color: 'var(--text-muted)' }}
        >
          {t('webhooks.secret_modal.description')}
        </p>

        <div className="mb-4">
          <label
            className="block text-xs font-medium mb-1"
            style={{ color: 'var(--text-muted)' }}
          >
            {t('webhooks.secret_modal.endpoint_label')}
          </label>
          <div
            className="text-sm"
            style={{ color: 'var(--text-primary)' }}
          >
            {endpoint.name}
          </div>
          <div
            className="text-xs break-all"
            style={{ color: 'var(--text-subtle)' }}
          >
            {endpoint.url}
          </div>
        </div>

        <div className="mb-4">
          <label
            className="block text-xs font-medium mb-1"
            style={{ color: 'var(--text-muted)' }}
          >
            {t('webhooks.secret_modal.secret_label')}
          </label>
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              readOnly
              value={endpoint.secret}
              className="flex-1 px-3 py-2 rounded font-mono text-xs"
              style={{
                background: 'var(--neutral-tint)',
                color: 'var(--text-primary)',
                border: '1px solid var(--card-border)',
              }}
              onFocus={(e) => e.target.select()}
            />
            <button
              type="button"
              onClick={handleCopy}
              className="px-3 py-2 rounded text-xs font-medium whitespace-nowrap"
              style={{
                background: copied
                  ? 'var(--accent-tint)'
                  : 'var(--io-accent)',
                color: copied
                  ? 'var(--io-accent)'
                  : 'var(--on-accent)',
                border: copied
                  ? '1px solid var(--accent-border)'
                  : 'none',
              }}
            >
              {copied
                ? t('webhooks.secret_modal.copied')
                : t('webhooks.secret_modal.copy')}
            </button>
          </div>
        </div>

        <div
          className="mb-4 p-3 rounded text-xs"
          style={{
            background: 'var(--accent-tint)',
            color: 'var(--text-primary)',
            border: '1px solid var(--accent-border)',
          }}
        >
          {t('webhooks.secret_modal.warning')}
        </div>

        <label className="flex items-start gap-2 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
            className="mt-0.5"
            style={{ accentColor: 'var(--io-accent)' }}
          />
          <span
            className="text-sm"
            style={{ color: 'var(--text-primary)' }}
          >
            {t('webhooks.secret_modal.acknowledge')}
          </span>
        </label>

        <div className="flex justify-end">
          <button
            type="button"
            disabled={!acknowledged}
            onClick={onAck}
            className="px-4 py-2 rounded font-medium text-sm"
            style={{
              background: acknowledged
                ? 'var(--io-accent)'
                : 'var(--neutral-tint)',
              color: acknowledged
                ? 'var(--on-accent)'
                : 'var(--text-subtle)',
              cursor: acknowledged ? 'pointer' : 'not-allowed',
            }}
          >
            {t('webhooks.secret_modal.done')}
          </button>
        </div>
      </div>
    </div>
  );
}
