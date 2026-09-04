/**
 * DemoNotice — v1.0.4c.
 *
 * Non-dismissable notice shown on every admin page and above the public
 * registration form when the instance reports `demo_notice` in
 * /api/capabilities. Tells the visitor that this is a demonstration
 * workspace, that mail is captured on the server (readable at a public
 * inbox), and that no real personal data should be entered.
 *
 * The text is a single translated string. Every language version
 * contains the literal token "/mail/" exactly once; the component splits
 * on that token and, when `demo_mail_url` is non-empty, renders it as a
 * link. No HTML lives in the locale files, so the approved wording is
 * used verbatim.
 *
 * Renders nothing unless the capability is on. CE defaults it off, so a
 * self-hoster never sees this. Gold left stripe, matching the existing
 * "attention, informational" banner style.
 */

import { useCapabilities } from '../hooks/useCapabilities';
import { useI18n } from '../hooks/useI18n';

const MAIL_TOKEN = '/mail/';

export default function DemoNotice({ className = '' }) {
  const { capabilities } = useCapabilities();
  const { t } = useI18n();

  if (!capabilities.demo_notice) return null;

  const text = t('demo.notice');
  const [before, after] = text.split(MAIL_TOKEN);
  const hasToken = after !== undefined;
  const url = capabilities.demo_mail_url;

  return (
    <div
      className={`card-surface-solid p-4 mb-4 ${className}`}
      style={{ borderLeft: '4px solid #FFD700' }}
      role="status"
      data-testid="demo-notice"
    >
      <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
        {hasToken ? (
          <>
            {before}
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline font-bold"
              >
                {MAIL_TOKEN}
              </a>
            ) : (
              <span className="font-bold">{MAIL_TOKEN}</span>
            )}
            {after}
          </>
        ) : text}
      </p>
    </div>
  );
}
