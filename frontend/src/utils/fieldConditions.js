// v1.0.7 — conditional registration fields and info texts.
//
// The browser half of backend/app/services/field_conditions.py: the same
// rules, evaluated the same way, so the form hides exactly the fields the
// server will refuse to store. Keep the two in step.
//
// A rule is one of:
//   { source: '<custom field id>', any_of: ['true'] }   yes/no or select answer
//   { source: 'date_of_birth', age_under: 18 }          age on the event's start
//
// An `info` field is the organiser's text; nobody fills it in.

export const INFO = 'info';
export const DOB_SOURCE = 'date_of_birth';
export const SOURCE_TYPES = ['boolean', 'select'];

const TRUE = new Set(['true', '1', 'yes']);
const FALSE = new Set(['false', '0', 'no']);

const normBool = (v) => {
  const s = String(v ?? '').trim().toLowerCase();
  if (TRUE.has(s)) return 'true';
  if (FALSE.has(s)) return 'false';
  return null;
};

// 'YYYY-MM-DD' → [y, m, d], or null. Never through Date, so no time zone
// can move a birthday by a day.
const parts = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ''));
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
};

export function ageOn(dobIso, onIso) {
  const b = parts(dobIso);
  const o = parts(onIso);
  if (!b || !o) return null;
  const beforeBirthday = o[1] < b[1] || (o[1] === b[1] && o[2] < b[2]);
  return o[0] - b[0] - (beforeBirthday ? 1 : 0);
}

const pad = (n) => String(n).padStart(2, '0');
export const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

// The day ages are counted on: the event's start, or today without one.
export const referenceDate = (eventStartDate) => eventStartDate || todayIso();

export function conditionMet(rule, { answers, sourceTypes, dob, refDate }) {
  if (!rule) return true;
  if (rule.source === DOB_SOURCE) {
    const age = ageOn(dob, refDate);
    return age !== null && Number.isInteger(rule.age_under) && age < rule.age_under;
  }
  const raw = answers[rule.source];
  if (raw === undefined || raw === null || raw === '') return false;
  const wanted = rule.any_of || [];
  if (sourceTypes[rule.source] === 'boolean') {
    return wanted.map(normBool).includes(normBool(raw));
  }
  return wanted.includes(raw);
}

// Fields come from the API already in form order. Returns the set of field
// ids that are shown for this person, info texts included. An answer counts
// towards a later rule only if its own field is shown.
export function visibleFieldIds(fields, values, dob, refDate) {
  const sourceTypes = Object.fromEntries(fields.map(f => [f.id, f.field_type]));
  const answers = {};
  const shown = new Set();
  for (const f of fields) {
    if (!conditionMet(f.show_if, { answers, sourceTypes, dob, refDate })) continue;
    shown.add(f.id);
    const v = values?.[f.id];
    if (f.field_type !== INFO && v !== undefined && v !== null && v !== '') answers[f.id] = v;
  }
  return shown;
}

// The answers worth sending: shown, non-empty, never an info text.
export function answersToSend(fields, values, shown) {
  const out = {};
  for (const f of fields) {
    if (f.field_type === INFO || !shown.has(f.id)) continue;
    const v = values?.[f.id];
    if (v !== undefined && v !== null && v !== '') out[f.id] = v;
  }
  return out;
}

// Only an info text with a rule says something about a person, so only
// that kind gets a column in People and at check-in.
export const isColumnField = (f) => f.field_type !== INFO || !!f.show_if;
