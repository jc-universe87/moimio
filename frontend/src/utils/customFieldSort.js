// v1.0.1e-1 — ONE typed sort-value function for custom-field columns,
// shared by PeopleTable and CheckInPanel so the two views can never
// drift again (CheckInPanel previously had no custom-field sorting at
// all, silently falling back to participant number).
//
// Returns a comparable value; unset values sort first ascending.
export function cfSortValue(cfDef, raw) {
  const unset = raw === undefined || raw === null || raw === '';
  const type = cfDef?.field_type;
  if (type === 'select' && cfDef.options?.choices) {
    if (unset) return -1;
    const i = cfDef.options.choices.indexOf(raw);
    return i === -1 ? -1 : i;
  }
  if (type === 'number') {
    if (unset) return -Infinity;
    const n = parseFloat(raw);
    return Number.isNaN(n) ? -Infinity : n;
  }
  if (type === 'boolean') {
    if (unset) return -1;                      // unset < false < true
    return /^(true|1|yes|ja)$/i.test(String(raw)) ? 1 : 0;
  }
  if (type === 'date') {
    if (unset) return -Infinity;
    const t = Date.parse(raw);
    return Number.isNaN(t) ? -Infinity : t;   // real chronology, not text
  }
  return String(raw ?? '').toLowerCase();
}
