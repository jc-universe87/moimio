import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { preferences as prefsApi, getToken } from '../services/api';
import { useI18n } from './useI18n';

const DateFormatContext = createContext(null);

export function DateFormatProvider({ children }) {
  // v1.0.4zf (2.6): the short zone name is language-dependent, so this hook
  // needs to know which language is being read. I18nProvider wraps this one
  // in App.jsx, and useI18n degrades to English without a provider, so this
  // is safe in a bare render too.
  const { lang } = useI18n();
  const [dateFormat, setDateFormat] = useState('DD/MM/YYYY');
  // v1.0.4ze (DATE-1): the user's zone, as the fallback when an event has
  // none. Stored since v1.0.0k and, until this release, read by nothing.
  const [timezone, setTimezone] = useState(null);

  const loadPrefs = useCallback(async () => {
    // Only try if we have a token
    if (!getToken()) return;
    try {
      const data = await prefsApi.get();
      if (data?.date_format) setDateFormat(data.date_format);
      if (data?.timezone) setTimezone(data.timezone);
    } catch {
      // Not logged in or prefs not available
    }
  }, []);

  // Try loading on mount (token may already be set from sessionStorage)
  useEffect(() => {
    // Small delay to let AuthProvider set the token first
    const timer = setTimeout(loadPrefs, 100);
    return () => clearTimeout(timer);
  }, [loadPrefs]);

  const formatDate = useCallback((dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr + (dateStr.includes('T') ? '' : 'T00:00:00'));
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    switch (dateFormat) {
      case 'MM/DD/YYYY': return `${month}/${day}/${year}`;
      case 'YYYY-MM-DD': return `${year}-${month}-${day}`;
      // v1.0.0k: locale-specific numeric presets. Long-form (with month
      // name) is intentionally not handled here — it requires
      // Intl.DateTimeFormat integration and is deferred.
      case 'DD.MM.YYYY': return `${day}.${month}.${year}`;
      case 'YYYY.MM.DD': return `${year}.${month}.${day}`;
      case 'YYYY년 MM월 DD일': return `${year}년 ${month}월 ${day}일`;
      default: return `${day}/${month}/${year}`;
    }
  }, [dateFormat]);

  // v1.0.4ze (DATE-1). `formatDate` takes a date and returns a date; the
  // columns that needed a TIME called the browser's own formatter with
  // `undefined` as the locale, which means "whatever this browser thinks" —
  // which is how a German organiser with ISO selected saw `7/10/26, 2:09 PM`.
  //
  // Decisions this implements, settled in session 86:
  //   D8  times show in the EVENT's zone, named on screen, with the user's
  //       as the fallback. Almost every time this product shows is a fact
  //       about an event, and an unlabelled hour's difference on a check-in
  //       time is worse than a labelled one.
  //   D9  24-hour everywhere. Right for five of the six locales, defensible
  //       for the sixth, and it avoids a preference that would need a
  //       migration.
  //
  // A zone that is empty or that this browser does not recognise falls back
  // silently — to the user's, then to the browser's. Never an error, never a
  // blocked save, and no zone picker: that is after v1.0.5 if it is wanted.
  const resolveZone = useCallback((eventZone) => {
    for (const z of [eventZone, timezone]) {
      if (!z) continue;
      try {
        new Intl.DateTimeFormat('en', { timeZone: z }).format(new Date());
        return z;
      } catch {
        // Not a zone this browser knows. Try the next one.
      }
    }
    return undefined;  // the browser's own
  }, [timezone]);

  const formatTime = useCallback((value, eventZone) => {
    if (!value) return '';
    const d = new Date(value);
    if (isNaN(d.getTime())) return String(value);
    const zone = resolveZone(eventZone);
    try {
      return new Intl.DateTimeFormat('en-GB', {
        hour: '2-digit', minute: '2-digit', hour12: false,
        ...(zone ? { timeZone: zone } : {}),
      }).format(d);
    } catch {
      return new Intl.DateTimeFormat('en-GB', {
        hour: '2-digit', minute: '2-digit', hour12: false,
      }).format(d);
    }
  }, [resolveZone]);

  // The date half has to be read in the same zone, or a time near midnight
  // lands on the wrong day.
  const formatDateTime = useCallback((value, eventZone) => {
    if (!value) return '';
    const d = new Date(value);
    if (isNaN(d.getTime())) return String(value);
    const zone = resolveZone(eventZone);
    let y, m, day;
    try {
      const parts = new Intl.DateTimeFormat('en-CA', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        ...(zone ? { timeZone: zone } : {}),
      }).formatToParts(d);
      const get = (t) => parts.find(p => p.type === t)?.value || '';
      y = get('year'); m = get('month'); day = get('day');
    } catch {
      y = String(d.getFullYear());
      m = String(d.getMonth() + 1).padStart(2, '0');
      day = String(d.getDate()).padStart(2, '0');
    }
    return `${formatDate(`${y}-${m}-${day}`)} ${formatTime(value, eventZone)}`;
  }, [formatDate, formatTime, resolveZone]);

  // The zone as it should be NAMED beside a time (D8).
  //
  // v1.0.4zf (2.6): the SHORT name, in the language being read — "MESZ" for
  // a German reader, "CEST" for an English one — not the IANA identifier.
  // `Europe/Berlin` beside a time told an organiser nothing they wanted and
  // read like a filename.
  //
  // The browser supplies it: `timeZoneName: 'short'` on the app's current
  // locale. No table of abbreviations is built here — there are hundreds,
  // they differ by language, and they change. Where a locale has no short
  // form the browser gives an offset such as "GMT+9", which is a true and
  // useful answer and ships as it is.
  //
  // The identifier must never reach the screen again, so the fallback when
  // everything else fails is '' rather than the zone id.
  const zoneLabel = useCallback((eventZone) => {
    const zone = resolveZone(eventZone);
    const sample = new Date();
    try {
      const parts = new Intl.DateTimeFormat(lang || 'en', {
        timeZoneName: 'short',
        ...(zone ? { timeZone: zone } : {}),
      }).formatToParts(sample);
      const named = parts.find(p => p.type === 'timeZoneName')?.value;
      if (named) return named;
    } catch {
      // An unknown zone, or a locale this browser has no data for.
    }
    return '';
  }, [resolveZone, lang]);

  const updateFormat = (newFormat) => {
    setDateFormat(newFormat);
  };

  return (
    <DateFormatContext.Provider value={{
      dateFormat, formatDate, formatTime, formatDateTime, zoneLabel,
      updateFormat, reloadPrefs: loadPrefs,
    }}>
      {children}
    </DateFormatContext.Provider>
  );
}

export function useDateFormat() {
  const ctx = useContext(DateFormatContext);
  if (!ctx) return {
    dateFormat: 'DD/MM/YYYY',
    formatDate: (d) => d,
    formatTime: (d) => (d ? String(d) : ''),
    formatDateTime: (d) => (d ? String(d) : ''),
    zoneLabel: () => '',
    updateFormat: () => {}, reloadPrefs: () => {},
  };
  return ctx;
}
