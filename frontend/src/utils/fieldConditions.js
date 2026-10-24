// v1.0.7 — conditional registration fields, info texts and text formats.
//
// The browser half of backend/app/services/field_conditions.py: the same
// rules, evaluated the same way, so the form hides exactly the fields the
// server will refuse to store. Keep the two in step.
//
// A rule: { match: 'all' | 'any', conditions: [{ source, op, value }] }.
// `source` is a built-in field name (BUILTIN_KINDS) or the id of a custom
// field above. Every condition except `is_empty` needs an answer.

export const INFO = 'info';

export const BUILTIN_KINDS = {
  date_of_birth: 'age',
  gender: 'gender',
  email: 'text',
  phone: 'text',
  address: 'text',
  country: 'text',
  church_organisation: 'text',
};
export const CUSTOM_KINDS = { boolean: 'boolean', select: 'select', text: 'text', number: 'number', date: 'date' };
export const OPS = {
  boolean: ['one_of'],
  select: ['one_of', 'not_one_of'],
  gender: ['one_of'],
  text: ['equals', 'contains', 'not_contains'],
  number: ['equals', 'gt', 'lt'],
  date: ['before', 'after', 'on'],
  age: ['age_under', 'age_at_least', 'age_exactly'],
};
export const ANY_KIND_OPS = ['is_empty', 'is_filled'];
export const FORMATS = ['phone', 'email', 'digits'];

const TRUE = new Set(['true', '1', 'yes']);
const FALSE = new Set(['false', '0', 'no']);

const normBool = (v) => {
  const s = String(v ?? '').trim().toLowerCase();
  if (TRUE.has(s)) return 'true';
  if (FALSE.has(s)) return 'false';
  return null;
};
const normText = (v) => String(v ?? '').trim().split(/\s+/).join(' ').toLowerCase();
const blank = (v) => v === undefined || v === null || String(v).trim() === '';
const num = (v) => {
  if (typeof v === 'number') return v;
  const n = Number(String(v ?? '').trim().replace(',', '.'));
  return String(v ?? '').trim() === '' || Number.isNaN(n) ? null : n;
};

// 'YYYY-MM-DD' → [y, m, d], or null. Never through Date, so no time zone
// can move a birthday by a day.
const parts = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ''));
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
};
const isoOf = (iso) => (parts(iso) ? String(iso).slice(0, 10) : null);

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

export const sourceKind = (source, fieldsById) => (
  BUILTIN_KINDS[source] || CUSTOM_KINDS[fieldsById[source]?.field_type] || null
);

export function conditionMet(cond, { answers, fieldsById, person, refDate }) {
  const { source, op, value } = cond;
  const raw = source in BUILTIN_KINDS ? person?.[source] : answers[source];
  if (op === 'is_empty') return blank(raw);
  if (op === 'is_filled') return !blank(raw);
  if (blank(raw)) return false;
  const kind = sourceKind(source, fieldsById);
  if (kind === 'boolean') return (value || []).map(normBool).includes(normBool(raw));
  if (kind === 'select' || kind === 'gender') {
    const hit = (value || []).includes(String(raw));
    return op === 'one_of' ? hit : op === 'not_one_of' && !hit;
  }
  if (kind === 'text') {
    const have = normText(raw);
    const want = normText(value);
    if (op === 'equals') return have === want;
    if (op === 'contains') return have.includes(want);
    if (op === 'not_contains') return !have.includes(want);
    return false;
  }
  if (kind === 'number') {
    const a = num(raw);
    const b = num(value);
    if (a === null || b === null) return false;
    return op === 'equals' ? a === b : op === 'gt' ? a > b : op === 'lt' ? a < b : false;
  }
  if (kind === 'date') {
    const a = isoOf(raw);
    const b = isoOf(value);
    if (!a || !b) return false;
    return op === 'before' ? a < b : op === 'after' ? a > b : op === 'on' ? a === b : false;
  }
  if (kind === 'age') {
    const age = ageOn(raw, refDate);
    if (age === null || !Number.isInteger(value)) return false;
    return op === 'age_under' ? age < value : op === 'age_at_least' ? age >= value
      : op === 'age_exactly' ? age === value : false;
  }
  return false;
}

export function ruleMet(rule, ctx) {
  if (!rule) return true;
  const results = (rule.conditions || []).map(c => conditionMet(c, ctx));
  return rule.match === 'any' ? results.some(Boolean) : results.every(Boolean);
}

// Fields come from the API already in form order. `person` holds the
// built-in answers (only those of fields on the form). Returns the ids of
// the custom fields shown for this person, info texts included. An answer
// counts towards a later rule only if its own field is shown.
export function visibleFieldIds(fields, values, person, refDate) {
  const fieldsById = Object.fromEntries(fields.map(f => [f.id, f]));
  const answers = {};
  const shown = new Set();
  for (const f of fields) {
    if (!ruleMet(f.show_if, { answers, fieldsById, person, refDate })) continue;
    shown.add(f.id);
    const v = values?.[f.id];
    if (f.field_type !== INFO && !blank(v)) answers[f.id] = v;
  }
  return shown;
}

// The answers worth sending: shown, non-empty, never an info text.
export function answersToSend(fields, values, shown) {
  const out = {};
  for (const f of fields) {
    if (f.field_type === INFO || !shown.has(f.id)) continue;
    const v = values?.[f.id];
    if (!blank(v)) out[f.id] = v;
  }
  return out;
}

// Only an info text with a rule says something about a person, so only
// that kind gets a column in People and at check-in.
export const isColumnField = (f) => f.field_type !== INFO || !!f.show_if;

// ─── Formats ────────────────────────────────────────────────────────────
// Deliberately loose: a phone number is 6 to 15 digits with the usual
// separators, which catches typos but cannot prove a number exists.
const PHONE_CHARS = /^\+?[\d\s\-()/.]+$/;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const DIGITS = /^\d+$/;

export function fitsFormat(fmt, value) {
  if (!fmt || blank(value)) return true;
  const s = String(value).trim();
  if (fmt === 'phone') return PHONE_CHARS.test(s) && (s.match(/\d/g) || []).length >= 6 && (s.match(/\d/g) || []).length <= 15;
  if (fmt === 'email') return EMAIL.test(s);
  if (fmt === 'digits') return DIGITS.test(s);
  return true;
}

export const fieldFormat = (f) => (f.field_type === 'text' && FORMATS.includes(f.options?.format) ? f.options.format : null);
