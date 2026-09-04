/**
 * DemoNotice — v1.0.4c.
 *
 * Three pins: renders nothing unless the capability is on; when on and
 * an inbox URL is given, "/mail/" is a link to it; when on without a
 * URL, "/mail/" stays plain text. Uses the real English wording so a
 * change to the locale string that drops the "/mail/" token is caught.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import en from '../i18n/locales/en.json';

let caps = {};
vi.mock('../hooks/useCapabilities', () => ({
  useCapabilities: () => ({ capabilities: caps, loading: false }),
}));
vi.mock('../hooks/useI18n', () => ({
  useI18n: () => ({ t: (k) => en[k] ?? `[${k}]` }),
}));

import DemoNotice from './DemoNotice';

describe('DemoNotice', () => {
  it('renders nothing when demo_notice is off', () => {
    caps = { demo_notice: false, demo_mail_url: '' };
    render(<DemoNotice />);
    expect(screen.queryByTestId('demo-notice')).toBeNull();
  });

  it('links /mail/ to the inbox URL when one is configured', () => {
    caps = { demo_notice: true, demo_mail_url: 'https://demo.moimio.app/mail/' };
    render(<DemoNotice />);
    const notice = screen.getByTestId('demo-notice');
    expect(notice.textContent).toBe(en['demo.notice']);
    const link = screen.getByRole('link', { name: '/mail/' });
    expect(link.getAttribute('href')).toBe('https://demo.moimio.app/mail/');
  });

  it('keeps /mail/ as plain text when no inbox URL is configured', () => {
    caps = { demo_notice: true, demo_mail_url: '' };
    render(<DemoNotice />);
    expect(screen.getByTestId('demo-notice').textContent).toBe(en['demo.notice']);
    expect(screen.queryByRole('link')).toBeNull();
  });
});
