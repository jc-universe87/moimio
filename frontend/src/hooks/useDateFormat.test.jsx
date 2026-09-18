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

describe('zoneLabel', () => {
  it('names the event\'s zone so nobody has to guess', () => {
    expect(hook().current.zoneLabel('Europe/Berlin')).toBe('Europe/Berlin');
  });

  it('gives something usable when the zone is unknown', () => {
    // Either the browser's own zone or an empty string — never the
    // unrecognised value, which would be a label that means nothing.
    expect(hook().current.zoneLabel('Middle/Earth')).not.toBe('Middle/Earth');
  });
});
