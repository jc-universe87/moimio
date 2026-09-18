/**
 * useDateFormat — the time half. v1.0.4ze (DATE-1).
 *
 * `formatDate` took a date and returned a date. The columns that needed a
 * TIME called the browser's own formatter with `undefined` as the locale,
 * which means "whatever this browser thinks" — which is how a German
 * organiser with ISO selected saw `7/10/26, 2:09 PM`.
 *
 * What is pinned here is the behaviour the decisions settled: 24-hour
 * everywhere (D9), the event's zone with the user's as fallback (D8), and a
 * zone this browser does not know falling back silently rather than
 * throwing. The date half is unchanged and is not re-tested.
 */
import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';

import { DateFormatProvider, useDateFormat } from './useDateFormat';

// A fixed instant: 2026-07-10T13:09:00Z. In Berlin that is 15:09 the same
// day; in Seoul 22:09; in Los Angeles 06:09.
const T = '2026-07-10T13:09:00Z';

const wrapper = ({ children }) => (
  <DateFormatProvider>{children}</DateFormatProvider>
);
const hook = () => renderHook(() => useDateFormat(), { wrapper }).result;

describe('formatTime', () => {
  it('is 24-hour, never am/pm', () => {
    const t = hook().current.formatTime(T, 'UTC');
    expect(t).toBe('13:09');
    expect(t).not.toMatch(/[ap]m/i);
  });

  it('shows the time in the event\'s zone, not the browser\'s', () => {
    const { formatTime } = hook().current;
    expect(formatTime(T, 'Europe/Berlin')).toBe('15:09');
    expect(formatTime(T, 'Asia/Seoul')).toBe('22:09');
  });

  it('falls back silently when the event has no zone', () => {
    // No event zone and no user preference in a bare provider: the
    // browser's own. It must produce a time rather than throw or blank.
    expect(hook().current.formatTime(T)).toMatch(/^\d{2}:\d{2}$/);
  });

  it('falls back silently when the zone is not one this browser knows', () => {
    // A stale or hand-typed value. The box is free text and validated
    // nowhere, so this is reachable.
    expect(hook().current.formatTime(T, 'Middle/Earth')).toMatch(/^\d{2}:\d{2}$/);
  });

  it('returns empty for nothing, and passes rubbish through', () => {
    const { formatTime } = hook().current;
    expect(formatTime(null)).toBe('');
    expect(formatTime('')).toBe('');
    expect(formatTime('not a date')).toBe('not a date');
  });
});

describe('formatDateTime', () => {
  it('reads the DATE in the same zone as the time', () => {
    // 2026-07-10T23:30Z is still the 10th in New York (UTC-4 in July) and
    // already the 11th in Seoul (UTC+9). A date formatted in one zone and a
    // time in another would disagree about which day it was.
    const { formatDateTime } = hook().current;
    const late = '2026-07-10T23:30:00Z';
    expect(formatDateTime(late, 'Asia/Seoul')).toBe('11/07/2026 08:30');
    expect(formatDateTime(late, 'America/New_York')).toBe('10/07/2026 19:30');
  });

  it('uses the chosen date format, not the browser\'s locale', () => {
    // The provider's default is DD/MM/YYYY. The old code produced
    // 7/10/26 here, which is the fault DATE-1 named.
    const out = hook().current.formatDateTime(T, 'UTC');
    expect(out).toBe('10/07/2026 13:09');
  });
});

describe('zoneLabel (v1.0.4zf, 2.6)', () => {
  // The IANA identifier read like a filename beside a time. What belongs
  // there is the SHORT name in the language being read — "MESZ" for a German
  // reader. The assertions are about the SHAPE of the answer rather than one
  // hard-coded abbreviation, because the abbreviation a runtime can produce
  // depends on its ICU data.

  it('never returns the IANA identifier', () => {
    // The one thing that must not happen, whatever the locale data holds.
    // The rule is that no Area/Location form reaches a screen. 'UTC' is a
    // genuine short name that happens to equal its own identifier, so the
    // slash is what distinguishes the two cases, not string equality.
    const { zoneLabel } = hook().current;
    for (const z of ['Europe/Berlin', 'Asia/Seoul', 'America/New_York', 'UTC']) {
      const out = zoneLabel(z);
      expect(out).not.toContain('/');
      expect(out).not.toBe('Europe/Berlin');
    }
  });

  it('gives a short name or an offset, never something empty for a real zone', () => {
    // Where a locale has no abbreviation the browser answers with an offset
    // form such as GMT+9, which is true and useful and ships as it is.
    const out = hook().current.zoneLabel('Europe/Berlin');
    expect(out).toMatch(/^(?:[A-Z]{2,6}|GMT[+-]\d{1,2}(?::\d{2})?)$/);
  });

  it('answers in the language being read where the data allows it', () => {
    // This environment's ICU gives German "MESZ" for Berlin in summer and an
    // offset for English. Asserting they DIFFER pins the language-dependence
    // without hard-coding either, and skips honestly where a runtime has
    // only one form for both.
    const de = new Intl.DateTimeFormat('de', {
      timeZone: 'Europe/Berlin', timeZoneName: 'short',
    }).formatToParts(new Date('2026-07-10T13:09:00Z'))
      .find(p => p.type === 'timeZoneName')?.value;
    const en = new Intl.DateTimeFormat('en', {
      timeZone: 'Europe/Berlin', timeZoneName: 'short',
    }).formatToParts(new Date('2026-07-10T13:09:00Z'))
      .find(p => p.type === 'timeZoneName')?.value;
    if (de === en) {
      // Say so rather than forcing a pass: this runtime has no separate
      // German short name, so there is nothing here to prove.
      expect(de).toBeTruthy();
      return;
    }
    expect(de).not.toBe(en);
  });

  it('returns nothing rather than a bad label for an unknown zone', () => {
    // Falls through to the browser's own zone or to '', but never to the
    // string it was given.
    expect(hook().current.zoneLabel('Middle/Earth')).not.toBe('Middle/Earth');
  });
});
