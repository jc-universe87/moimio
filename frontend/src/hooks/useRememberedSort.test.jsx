/**
 * useRememberedSort — v1.0.4zc (SORT-1).
 *
 * Four pins, all of them things that fail quietly rather than loudly: that a
 * sort is restored at all; that one user does not inherit another's; that a
 * column which no longer exists falls back to the default instead of leaving
 * the table sorted by nothing; and that storage which throws — a private
 * window, storage disabled — does not take the table down with it.
 *
 * The rendering of the two tables is not tested here: they are large page
 * components needing the API client, the auth context and a router, and the
 * behaviour worth pinning is all in the hook.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useRememberedSort } from './useRememberedSort';

const COLUMNS = ['participant_number', 'name', 'email'];
const opts = (over = {}) => ({
  storageKey: 'people',
  userId: 'u1',
  columns: COLUMNS,
  defaultCol: 'participant_number',
  ...over,
});

beforeEach(() => {
  window.localStorage.clear();
});

describe('useRememberedSort', () => {
  it('starts on the default when nothing was ever stored', () => {
    const { result } = renderHook(() => useRememberedSort(opts()));
    expect(result.current.sortCol).toBe('participant_number');
    expect(result.current.sortDir).toBe('asc');
  });

  it('remembers a sort across a remount', () => {
    const first = renderHook(() => useRememberedSort(opts()));
    act(() => { first.result.current.toggleSort('name'); });
    expect(first.result.current.sortCol).toBe('name');
    first.unmount();

    // A fresh mount is what leaving the page and coming back looks like.
    const second = renderHook(() => useRememberedSort(opts()));
    expect(second.result.current.sortCol).toBe('name');
    expect(second.result.current.sortDir).toBe('asc');
  });

  it('remembers the direction too', () => {
    const first = renderHook(() => useRememberedSort(opts()));
    act(() => { first.result.current.toggleSort('email'); });  // asc
    act(() => { first.result.current.toggleSort('email'); });  // flips to desc
    expect(first.result.current.sortDir).toBe('desc');
    first.unmount();

    const second = renderHook(() => useRememberedSort(opts()));
    expect(second.result.current.sortCol).toBe('email');
    expect(second.result.current.sortDir).toBe('desc');
  });

  it('does not let one user inherit another user\'s sort', () => {
    const mine = renderHook(() => useRememberedSort(opts({ userId: 'u1' })));
    act(() => { mine.result.current.toggleSort('email'); });
    mine.unmount();

    const theirs = renderHook(() => useRememberedSort(opts({ userId: 'u2' })));
    expect(theirs.result.current.sortCol).toBe('participant_number');
  });

  it('falls back to the default when the stored column no longer exists', () => {
    // A column since removed, or a hand-edited value.
    window.localStorage.setItem(
      'moimio.sort.people.u1', JSON.stringify({ col: 'a_column_we_dropped', dir: 'desc' }),
    );
    const { result } = renderHook(() => useRememberedSort(opts()));
    expect(result.current.sortCol).toBe('participant_number');
    expect(result.current.sortDir).toBe('asc');
  });

  it('falls back when the stored value is not readable at all', () => {
    window.localStorage.setItem('moimio.sort.people.u1', 'not json');
    const { result } = renderHook(() => useRememberedSort(opts()));
    expect(result.current.sortCol).toBe('participant_number');
  });

  it('survives storage that throws, as in a private window', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage disabled');
    });
    const { result } = renderHook(() => useRememberedSort(opts()));
    expect(result.current.sortCol).toBe('participant_number');
    // And sorting still works for this visit.
    act(() => { result.current.toggleSort('name'); });
    expect(result.current.sortCol).toBe('name');
    spy.mockRestore();
  });

  it('keeps the two tables apart', () => {
    const people = renderHook(() => useRememberedSort(opts({ storageKey: 'people' })));
    act(() => { people.result.current.toggleSort('name'); });
    people.unmount();

    const checkin = renderHook(() => useRememberedSort(
      opts({ storageKey: 'checkin', columns: ['participant_number', 'name'] })));
    expect(checkin.result.current.sortCol).toBe('participant_number');
  });
});
