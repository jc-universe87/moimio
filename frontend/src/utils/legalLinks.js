/**
 * legalLinks — where the hosted edition's legal pages live (LEGAL-2).
 *
 * The site publishes its legal pages in three languages; the app speaks
 * six. A URL built from the app's locale would 404 for the other three, so
 * the mapping is explicit here and everything the site does not publish
 * falls back to English. Add a language to SITE_LANGS only when the site
 * actually has the pages.
 *
 * Only the hosted edition ever links here. The Terms say in their own §2,
 * §3 and §15 that they do not cover Community Edition, so a CE install must
 * never be shown these addresses; that decision is made by the caller
 * (LegalNotice), not by this module.
 */

export const LEGAL_SITE_BASE = 'https://moimio.app';

/** App locales for which the site has legal pages. */
export const SITE_LANGS = ['en', 'de', 'ko'];

export const LEGAL_PAGES = ['terms', 'privacy', 'dpa'];

/** The site language to use for an app locale: itself if published, else English. */
export function legalSiteLang(appLang) {
  return SITE_LANGS.includes(appLang) ? appLang : 'en';
}

/** `https://moimio.app/{lang}/legal/{page}/` for one page. */
export function legalPageUrl(page, appLang) {
  if (!LEGAL_PAGES.includes(page)) {
    throw new Error(`legalPageUrl: unknown page "${page}"`);
  }
  return `${LEGAL_SITE_BASE}/${legalSiteLang(appLang)}/legal/${page}/`;
}

/** All three, keyed by page, for one app locale. */
export function legalPageUrls(appLang) {
  return Object.fromEntries(LEGAL_PAGES.map(p => [p, legalPageUrl(p, appLang)]));
}
