/**
 * LegalNotice — LEGAL-2.
 *
 * Two editions, two bodies, and they must not leak into each other:
 *   hosted → three links to moimio.app in the site's language for the app's
 *            locale, no MIT text;
 *   CE     → the MIT disclaimer verbatim, and no link to moimio.app at all,
 *            because the Terms there do not cover Community Edition.
 * The old `legal.no_warranty` sentence must appear in neither.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import en from '../i18n/locales/en.json';

let lang = 'en';
vi.mock('../hooks/useI18n', () => ({
  useI18n: () => ({ t: (k) => en[k] ?? `[${k}]`, lang }),
}));

import LegalNotice, { MIT_WARRANTY_DISCLAIMER } from './LegalNotice';

const OLD_SENTENCE = 'This software is provided as-is.';

describe('LegalNotice, hosted', () => {
  it('shows the three links in the site language for a published locale', () => {
    lang = 'de';
    render(<LegalNotice hosted />);
    expect(screen.getByRole('link', { name: /Terms of Service/ }).getAttribute('href'))
      .toBe('https://moimio.app/de/legal/terms/');
    expect(screen.getByRole('link', { name: /Privacy Policy/ }).getAttribute('href'))
      .toBe('https://moimio.app/de/legal/privacy/');
    expect(screen.getByRole('link', { name: /Data Processing Agreement/ }).getAttribute('href'))
      .toBe('https://moimio.app/de/legal/dpa/');
    expect(screen.getAllByRole('link')).toHaveLength(3);
  });

  it('falls back to English pages for a locale the site does not publish', () => {
    lang = 'fr';
    render(<LegalNotice hosted />);
    for (const a of screen.getAllByRole('link')) {
      expect(a.getAttribute('href')).toMatch(/^https:\/\/moimio\.app\/en\/legal\/(terms|privacy|dpa)\/$/);
    }
  });

  it('opens in a new tab, opener-isolated', () => {
    lang = 'en';
    render(<LegalNotice hosted />);
    for (const a of screen.getAllByRole('link')) {
      expect(a.getAttribute('target')).toBe('_blank');
      expect(a.getAttribute('rel')).toBe('noopener noreferrer');
    }
  });

  it('carries neither the MIT text nor the old sentence', () => {
    lang = 'en';
    const { container } = render(<LegalNotice hosted />);
    expect(container.textContent).not.toContain('WITHOUT WARRANTY');
    expect(container.textContent).not.toContain(OLD_SENTENCE);
  });
});

describe('LegalNotice, Community Edition', () => {
  it('shows the MIT warranty disclaimer verbatim and nothing else', () => {
    lang = 'de';
    const { container } = render(<LegalNotice hosted={false} />);
    expect(screen.getByTestId('legal-mit-disclaimer').textContent).toBe(MIT_WARRANTY_DISCLAIMER);
    expect(container.textContent.trim()).toBe(MIT_WARRANTY_DISCLAIMER);
  });

  it('has no link to moimio.app', () => {
    lang = 'en';
    const { container } = render(<LegalNotice hosted={false} />);
    expect(screen.queryAllByRole('link')).toHaveLength(0);
    expect(container.innerHTML).not.toContain('moimio.app');
  });

  it('does not carry the old sentence', () => {
    const { container } = render(<LegalNotice hosted={false} />);
    expect(container.textContent).not.toContain(OLD_SENTENCE);
  });
});

describe('the old sentence is gone from every locale', () => {
  it('has no legal.no_warranty key in en', () => {
    expect(en['legal.no_warranty']).toBeUndefined();
  });
});
