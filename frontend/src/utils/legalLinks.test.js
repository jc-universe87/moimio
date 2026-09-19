/**
 * legalLinks — LEGAL-2.
 *
 * The site publishes legal pages in three languages, the app speaks six.
 * These pin the mapping: a published language is used as itself, every
 * other one falls back to English, and no URL is ever built for a language
 * the site does not have (it would 404).
 */
import { describe, it, expect } from 'vitest';
import { legalSiteLang, legalPageUrl, legalPageUrls, SITE_LANGS } from './legalLinks';

const APP_LANGS = ['en', 'de', 'ko', 'es', 'fr', 'pt-BR'];

describe('legalSiteLang', () => {
  it.each(['en', 'de', 'ko'])('keeps %s, which the site publishes', (lang) => {
    expect(legalSiteLang(lang)).toBe(lang);
  });

  it.each(['es', 'fr', 'pt-BR'])('falls back to en for %s, which the site does not publish', (lang) => {
    expect(legalSiteLang(lang)).toBe('en');
  });

  it('falls back to en for anything unexpected', () => {
    expect(legalSiteLang(undefined)).toBe('en');
    expect(legalSiteLang('xx')).toBe('en');
  });
});

describe('legalPageUrl', () => {
  it('builds https://moimio.app/{lang}/legal/{page}/ for a published language', () => {
    expect(legalPageUrl('terms', 'de')).toBe('https://moimio.app/de/legal/terms/');
    expect(legalPageUrl('privacy', 'ko')).toBe('https://moimio.app/ko/legal/privacy/');
    expect(legalPageUrl('dpa', 'en')).toBe('https://moimio.app/en/legal/dpa/');
  });

  it('never emits a URL in an unpublished language', () => {
    for (const lang of APP_LANGS) {
      for (const page of ['terms', 'privacy', 'dpa']) {
        const url = legalPageUrl(page, lang);
        const siteLang = url.split('/')[3];
        expect(SITE_LANGS).toContain(siteLang);
      }
    }
    expect(legalPageUrl('terms', 'fr')).toBe('https://moimio.app/en/legal/terms/');
    expect(legalPageUrl('terms', 'pt-BR')).toBe('https://moimio.app/en/legal/terms/');
  });

  it('refuses a page that is not one of the three', () => {
    expect(() => legalPageUrl('imprint', 'en')).toThrow();
  });
});

describe('legalPageUrls', () => {
  it('returns all three, keyed by page', () => {
    expect(legalPageUrls('es')).toEqual({
      terms: 'https://moimio.app/en/legal/terms/',
      privacy: 'https://moimio.app/en/legal/privacy/',
      dpa: 'https://moimio.app/en/legal/dpa/',
    });
  });
});
