/**
 * Moimio i18n — per-language dynamic loading.
 *
 * v0.70: previously a single `translations.json` bundling all 6 language
 * blocks (~300 KB) was statically imported into the main chunk. Now
 * English is bundled (the `t()` fallback dict, ~46 KB), and the other
 * 5 languages live in `i18n/locales/*.json` and are dynamically imported
 * on first use of that language. Vite produces one chunk per language
 * file; each is downloaded only when the user actually needs it.
 *
 * Trade-offs:
 *   - EN users pay zero extra network requests (their dict is in main).
 *   - Non-EN users download 1 lang chunk (~50 KB raw / ~10 KB gz) the
 *     first time their language is selected. Subsequent renders use the
 *     in-memory copy.
 *   - During the load window for a non-EN language, `t()` falls back to
 *     EN (same behaviour as a missing-key fallback). On fast connections
 *     this flash is imperceptible; on slow ones it's a brief EN flash
 *     before the localised text appears. Acceptable trade — see v0.70
 *     route-splitting decision discussion.
 *   - The silent EN fallback (when a key is missing in the active lang)
 *     remains intact because EN is always loaded. Bracketed `[key]`
 *     output still indicates a key missing in EN itself — the developer
 *     signal for an unregistered key.
 *
 * Language persistence (unchanged from pre-v0.70):
 *   - Admin language: localStorage('moimio_lang')
 *   - Registration page: sessionStorage('moimio_lang_override')
 *
 * Usage (unchanged):
 *   const { t, lang, setLang } = useI18n();
 *   t('login.title')         → "Sign in" (or translation)
 */

import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import enTranslations from '../i18n/locales/en.json';

export const SUPPORTED_LANGS = [
  { code: 'en',    label: 'English' },
  { code: 'de',    label: 'Deutsch' },
  { code: 'ko',    label: '한국어' },
  { code: 'es',    label: 'Español' },
  { code: 'pt-BR', label: 'Português (BR)' },
  { code: 'fr',    label: 'Français' },
];

const VALID_CODES = new Set(SUPPORTED_LANGS.map(l => l.code));

// Vite analyses these dynamic imports at build time and emits one chunk
// per language file. The map indirection keeps the call-site clean and
// gives us a single place to add a new language. Keep paths string-
// literal — Vite cannot statically analyse computed paths.
const LANG_LOADERS = {
  de:      () => import('../i18n/locales/de.json'),
  ko:      () => import('../i18n/locales/ko.json'),
  es:      () => import('../i18n/locales/es.json'),
  'pt-BR': () => import('../i18n/locales/pt-BR.json'),
  fr:      () => import('../i18n/locales/fr.json'),
};

const I18nContext = createContext(null);

export function I18nProvider({ children, forRegistration = false }) {
  const [lang, setLangState] = useState(() => {
    if (forRegistration) {
      // Registration page: sessionStorage override first, then localStorage, then 'en'
      return sessionStorage.getItem('moimio_lang_override')
        || localStorage.getItem('moimio_lang')
        || 'en';
    }
    // Admin: localStorage, fallback to 'en'
    return localStorage.getItem('moimio_lang') || 'en';
  });

  // Dictionaries available right now. EN is always present.
  const [dicts, setDicts] = useState({ en: enTranslations });

  // Tracks which langs we've already kicked off a fetch for, so we don't
  // double-fetch on lang round-trips (en → de → en → de). Ref because
  // we only need it for control flow, not for re-render.
  const requestedLangsRef = useRef(new Set(['en']));

  // Race guard — if the user switches lang multiple times before the
  // first fetch resolves, only the latest selection wins.
  const latestLangRef = useRef(lang);

  useEffect(() => {
    latestLangRef.current = lang;
    if (requestedLangsRef.current.has(lang)) return;
    const loader = LANG_LOADERS[lang];
    if (!loader) return;  // unknown lang — t() will fall back to EN
    requestedLangsRef.current.add(lang);
    loader()
      .then(mod => {
        if (latestLangRef.current !== lang) return;
        setDicts(prev => ({ ...prev, [lang]: mod.default }));
      })
      .catch(err => {
        // Non-fatal — t() will keep using the EN fallback. Remove from
        // requested set so a retry (e.g. user re-selects this lang) can
        // attempt the fetch again.
        requestedLangsRef.current.delete(lang);
        console.error(`[i18n] failed to load ${lang}:`, err);
      });
  }, [lang]);

  // Admin language change — persists to localStorage
  const setLang = useCallback((code) => {
    if (!VALID_CODES.has(code)) return;
    localStorage.setItem('moimio_lang', code);
    setLangState(code);
  }, []);

  // Registration-only override — sessionStorage so admin's pref is preserved
  const setLangOverride = useCallback((code) => {
    if (!VALID_CODES.has(code)) return;
    sessionStorage.setItem('moimio_lang_override', code);
    setLangState(code);
  }, []);

  const clearLangOverride = useCallback(() => {
    sessionStorage.removeItem('moimio_lang_override');
  }, []);

  const t = useCallback((key, vars = {}) => {
    const dict = dicts[lang] || enTranslations;
    let val = dict[key];
    if (val === undefined) {
      // Silent EN fallback (parity safety net) — same behaviour as before.
      val = enTranslations[key];
      if (val === undefined) return `[${key}]`;
    }
    return val.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`);
  }, [lang, dicts]);

  return (
    <I18nContext.Provider value={{ t, lang, setLang, setLangOverride, clearLangOverride }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Fallback for components rendered outside an I18nProvider (rare —
    // top-level error states, the setup-status loader). Only English is
    // available here because the dynamic loaders need a Provider's
    // useEffect to fire.
    return {
      t: (key, vars = {}) => {
        const val = enTranslations[key];
        if (!val) return `[${key}]`;
        return val.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`);
      },
      lang: 'en',
      setLang: () => {},
      setLangOverride: () => {},
      clearLangOverride: () => {},
    };
  }
  return ctx;
}
