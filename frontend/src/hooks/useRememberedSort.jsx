/**
 * useRememberedSort — a table's sort column and direction, remembered. v1.0.4zc.
 *
 * Sorting the People list by name lasted until the page was left; coming back
 * put it on participant number again, so somebody who works by name re-sorted
 * on every visit (SORT-1).
 *
 * WHERE IT IS KEPT, AND WHAT THAT COSTS. Browser storage, keyed by the user's
 * id. `UserPreferences` carries three typed columns — language, date_format,
 * timezone — and no JSON column, so a per-user sort would need a new column,
 * which is a migration, and v1.0.4zb's was the only one this series gets.
 *
 * So this is PER BROWSER, not per account: the sort follows the user on the
 * computer where they set it and does not travel with them to another. Keying
 * on the user's id is what stops two people sharing a computer inheriting each
 * other's sort, which is the part that would actually confuse somebody. Making
 * it follow the account wants a JSON preferences column, after v1.0.5.
 *
 * A STALE VALUE FALLS BACK SILENTLY. The stored column is checked against the
 * columns the table actually sorts by, and the direction against 'asc'/'desc'.
 * Anything else — a column since removed, a hand-edited value, storage that
 * throws in a private window — is ignored and the default applies. Never an
 * error, never an empty table.
 *
 * Usage:
 *   const { sortCol, sortDir, toggleSort } = useRememberedSort({
 *     storageKey: 'people', userId: user?.id,
 *     columns: SORTABLE, defaultCol: 'participant_number',
 *   });
 */

import { useCallback, useEffect, useState } from 'react';

const PREFIX = 'moimio.sort';

function keyFor(storageKey, userId) {
  // No user yet (the auth context loads a tick later) → no key, so nothing is
  // read or written until we know whose sort it is.
  return userId ? `${PREFIX}.${storageKey}.${userId}` : null;
}

export function useRememberedSort({ storageKey, userId, columns, defaultCol, defaultDir = 'asc' }) {
  const [sortCol, setSortCol] = useState(defaultCol);
  const [sortDir, setSortDir] = useState(defaultDir);
  // Until the stored value has been read, nothing is written — or the default
  // would overwrite what we are about to restore.
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    const k = keyFor(storageKey, userId);
    if (!k) return;
    try {
      const raw = window.localStorage.getItem(k);
      if (raw) {
        const saved = JSON.parse(raw);
        // Validate both halves before trusting either.
        if (saved && columns.includes(saved.col)) {
          setSortCol(saved.col);
          setSortDir(saved.dir === 'desc' ? 'desc' : 'asc');
        }
      }
    } catch {
      // Unreadable, unparseable, or storage disabled. The default stands.
    }
    setRestored(true);
  }, [storageKey, userId]);

  useEffect(() => {
    const k = keyFor(storageKey, userId);
    if (!k || !restored) return;
    try {
      window.localStorage.setItem(k, JSON.stringify({ col: sortCol, dir: sortDir }));
    } catch {
      // Private window, or storage full. Sorting still works for this visit.
    }
  }, [storageKey, userId, restored, sortCol, sortDir]);

  // Same behaviour the two tables had inline: clicking the sorted column
  // flips direction, clicking another moves to it ascending.
  const toggleSort = useCallback((col) => {
    setSortCol(prev => {
      if (prev === col) {
        setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
        return prev;
      }
      setSortDir('asc');
      return col;
    });
  }, []);

  return { sortCol, sortDir, toggleSort };
}
