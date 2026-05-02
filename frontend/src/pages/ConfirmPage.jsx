import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { I18nProvider, useI18n } from '../hooks/useI18n';
import Wordmark from '../components/Wordmark';
import ThemeToggle from '../components/ThemeToggle';

/**
 * ConfirmPage — public email-confirmation landing.
 *
 * v0.70d-2b-1 (R7): three-state rewrite. Previous version silently
 * treated expired/stale tokens as "success", which was dishonest
 * UX — users who clicked an already-used link got a confirmation
 * message regardless of whether they'd actually just confirmed.
 *
 * State machine (backend drives it via `{state: 'fresh'|'already'}`
 * on 2xx or `{detail: {state: 'invalid'}}` on 404):
 *
 *   'loading' — network in flight
 *   'fresh'   — backend just flipped status PENDING → CONFIRMED;
 *               receipt email was sent. Celebratory tick + subtitle.
 *   'already' — token matched a CONFIRMED participant; idempotent
 *               re-visit (old bookmark, duplicate click, multi-device).
 *               Calm "already confirmed" message, no alarm.
 *   'invalid' — token doesn't match, was replaced by a newer one, or
 *               the participant is cancelled. Honest "this link is no
 *               longer valid" + next-steps hint.
 *   'network' — fetch failed (server down, client offline). Shows the
 *               network error message with a retry hint.
 *
 * StrictMode double-mount is defused by the `calledRef` guard, same
 * pattern as v0.57a used. Matters here because 'fresh' is the first
 * request that flips status, and we don't want a double-fire to send
 * the receipt email twice (though the backend's second call would now
 * return 'already' so the email is NOT re-sent — defence in depth).
 */
function ConfirmContent() {
  const { token } = useParams();
  const [state, setState] = useState('loading');
  const calledRef = useRef(false);
  const { t } = useI18n();

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;
    confirmRegistration();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const confirmRegistration = async () => {
    try {
      const res = await fetch(`/api/participants/confirm/${token}`);
      const data = await res.json().catch(() => null);
      if (res.ok) {
        // 2xx — backend returned {state: 'fresh'|'already', status: 'confirmed'}
        setState(data?.state === 'already' ? 'already' : 'fresh');
      } else {
        // Backend returns 404 with {detail: {state: 'invalid'}} for bad tokens.
        // Fall back to 'invalid' for any non-2xx response we can't parse —
        // safer to show a neutral "link's no good" than to mis-declare success.
        setState('invalid');
      }
    } catch {
      setState('network');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
         style={{ backgroundColor: 'var(--app-bg)' }}>
      <div className="fixed top-[calc(0.75rem+env(safe-area-inset-top))] right-[calc(0.75rem+env(safe-area-inset-right))]">
        <ThemeToggle tone="inline" />
      </div>

      <div className="w-full max-w-md text-center">
        <div className="mb-6 flex justify-center">
          {/* Wordmark enforces §9.5 io colour rule: Steel Blue on light,
              Gold on dark. */}
          <Wordmark size="xl" />
        </div>
        <div className="card-surface-solid p-8">
          {state === 'loading' && (
            <p style={{ color: 'var(--text-subtle)' }}>{t('confirm.loading')}</p>
          )}

          {state === 'fresh' && (
            <>
              <div className="text-5xl mb-4" style={{ color: 'var(--io-accent)' }}>✓</div>
              <h2 className="font-heading text-2xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}>
                {t('confirm.fresh.title')}
              </h2>
              <p className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>
                {t('confirm.fresh.subtitle')}
              </p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {t('confirm.fresh.body')}
              </p>
            </>
          )}

          {state === 'already' && (
            <>
              {/* Same tick as 'fresh' — this IS a confirmed state, just
                  not a freshly-made one. Keeping the visual consistent
                  avoids alarming users who click their link twice. */}
              <div className="text-5xl mb-4" style={{ color: 'var(--io-accent)' }}>✓</div>
              <h2 className="font-heading text-2xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}>
                {t('confirm.already.title')}
              </h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {t('confirm.already.body')}
              </p>
            </>
          )}

          {state === 'invalid' && (
            <>
              <div className="text-5xl mb-4" style={{ color: 'var(--alert-burgundy)' }}>✕</div>
              <h2 className="font-heading text-2xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}>
                {t('confirm.invalid.title')}
              </h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {t('confirm.invalid.body')}
              </p>
              <p className="text-xs mt-3" style={{ color: 'var(--text-subtle)' }}>
                {t('confirm.invalid.contact_hint')}
              </p>
            </>
          )}

          {state === 'network' && (
            <>
              <div className="text-5xl mb-4" style={{ color: 'var(--alert-burgundy)' }}>✕</div>
              <h2 className="font-heading text-2xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}>
                {t('confirm.invalid.title')}
              </h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {t('confirm.error.network')}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ConfirmPage() {
  return <I18nProvider><ConfirmContent /></I18nProvider>;
}
