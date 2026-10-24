import { describe, it, expect } from 'vitest';
import {
  ageOn, answersToSend, conditionMet, fitsFormat, isColumnField, visibleFieldIds,
} from './fieldConditions';

const C = (source, op, value) => (value === undefined ? { source, op } : { source, op, value });
const R = (conditions, match = 'all') => ({ match, conditions });

const teamer = { id: 'a', field_type: 'boolean', show_if: null };
const team = { id: 'b', field_type: 'text', show_if: R([C('a', 'one_of', ['true'])]) };
const note = { id: 'c', field_type: 'info', show_if: R([C('date_of_birth', 'age_under', 18)]) };
const welcome = { id: 'd', field_type: 'info', show_if: null };
const role = { id: 'e', field_type: 'select', options: { choices: ['Cook', 'Driver'] }, show_if: null };
const shift = { id: 'f', field_type: 'text', show_if: R([C('e', 'one_of', ['Cook'])]) };
const fields = [teamer, team, note, welcome, role, shift];
const START = '2026-06-01';
const shown = (fs, values = {}, person = {}) => visibleFieldIds(fs, values, person, START);

describe('ageOn', () => {
  it('counts a birthday on the day itself', () => {
    expect(ageOn('2008-06-01', START)).toBe(18);
    expect(ageOn('2008-06-02', START)).toBe(17);
  });
  it('is null without a date', () => {
    expect(ageOn('', START)).toBeNull();
  });
});

describe('visibleFieldIds', () => {
  it('shows the team field only once Teamer is Yes', () => {
    expect(shown(fields).has('b')).toBe(false);
    expect(shown(fields, { a: 'false' }).has('b')).toBe(false);
    expect(shown(fields, { a: 'true' }).has('b')).toBe(true);
  });
  it('under, at least and exactly an age, on the start date', () => {
    const ages = ['age_under', 'age_at_least', 'age_exactly'].map(op => (
      { id: op, field_type: 'info', show_if: R([C('date_of_birth', op, 18)]) }));
    expect([...shown(ages, {}, { date_of_birth: '2008-06-02' })]).toEqual(['age_under']);
    expect([...shown(ages, {}, { date_of_birth: '2008-06-01' })]).toEqual(['age_at_least', 'age_exactly']);
    expect([...shown(ages, {}, { date_of_birth: '' })]).toEqual([]);
  });
  it('always shows a field or note without a rule', () => {
    const s = shown(fields);
    expect(s.has('a') && s.has('d') && s.has('e')).toBe(true);
  });
  it('matches a dropdown answer, and "is not one of" waits for an answer', () => {
    expect(shown(fields, { e: 'Cook' }).has('f')).toBe(true);
    expect(shown(fields, { e: 'Driver' }).has('f')).toBe(false);
    const notCook = { id: 'g', field_type: 'text', show_if: R([C('e', 'not_one_of', ['Cook'])]) };
    expect(shown([role, notCook], { e: 'Driver' }).has('g')).toBe(true);
    expect(shown([role, notCook], {}).has('g')).toBe(false);
  });
  it('hides a field whose source is itself hidden', () => {
    const chain = [teamer, team, { id: 'g', field_type: 'text', show_if: R([C('b', 'contains', 'x')]) }];
    expect(shown(chain, { a: 'false', b: 'x' }).has('g')).toBe(false);
    expect(shown(chain, { a: 'true', b: 'x' }).has('g')).toBe(true);
  });
  it('reads built-in fields: text ignoring capitals, empty, gender', () => {
    const f = [
      { id: 'de', field_type: 'info', show_if: R([C('country', 'equals', 'Deutschland')]) },
      { id: 'nophone', field_type: 'text', show_if: R([C('phone', 'is_empty')]) },
      { id: 'women', field_type: 'info', show_if: R([C('gender', 'one_of', ['female'])]) },
    ];
    expect([...shown(f, {}, { country: ' deutschland ', phone: '', gender: 'female' })])
      .toEqual(['de', 'nophone', 'women']);
    expect([...shown(f, {}, { country: 'Österreich', phone: '0171 234567', gender: 'male' })]).toEqual([]);
  });
  it('combines conditions with all or any', () => {
    const conds = [C('a', 'one_of', ['true']), C('date_of_birth', 'age_under', 18)];
    const f = [teamer, { id: 'all', field_type: 'info', show_if: R(conds) },
      { id: 'any', field_type: 'info', show_if: R(conds, 'any') }];
    expect(shown(f, { a: 'true' }, { date_of_birth: '1990-01-01' }).has('all')).toBe(false);
    expect(shown(f, { a: 'true' }, { date_of_birth: '1990-01-01' }).has('any')).toBe(true);
    expect(shown(f, { a: 'true' }, { date_of_birth: '2010-01-01' }).has('all')).toBe(true);
  });
});

describe('answersToSend', () => {
  it('drops answers to hidden fields and never sends an info text', () => {
    const values = { a: 'false', b: 'Kitchen', c: 'x', d: 'y' };
    const s = visibleFieldIds(fields, values, { date_of_birth: '2008-06-02' }, START);
    expect(answersToSend(fields, values, s)).toEqual({ a: 'false' });
  });
});

describe('conditionMet', () => {
  const ctx = (answers, fieldsById) => ({ answers, fieldsById, person: {}, refDate: START });
  it('reads a Yes/No answer however it was spelled', () => {
    const byId = { a: teamer };
    expect(conditionMet(C('a', 'one_of', ['true']), ctx({ a: 'yes' }, byId))).toBe(true);
    expect(conditionMet(C('a', 'one_of', ['true']), ctx({ a: '0' }, byId))).toBe(false);
  });
  it('compares numbers and dates as numbers and dates', () => {
    const byId = { n: { field_type: 'number' }, d: { field_type: 'date' } };
    expect(conditionMet(C('n', 'gt', '9'), ctx({ n: '10' }, byId))).toBe(true);
    expect(conditionMet(C('n', 'lt', '2,5'), ctx({ n: '2' }, byId))).toBe(true);
    expect(conditionMet(C('d', 'before', '2026-06-01'), ctx({ d: '2026-05-31' }, byId))).toBe(true);
    expect(conditionMet(C('d', 'on', '2026-06-01'), ctx({ d: '2026-06-01' }, byId))).toBe(true);
  });
});

describe('fitsFormat', () => {
  it('is loose about phone numbers but not blind', () => {
    expect(fitsFormat('phone', '+49 (0)171 / 234-567')).toBe(true);
    expect(fitsFormat('phone', 'call me')).toBe(false);
    expect(fitsFormat('phone', '12345')).toBe(false);
  });
  it('checks email and digits, and leaves empty answers to "required"', () => {
    expect(fitsFormat('email', 'a@b.de')).toBe(true);
    expect(fitsFormat('email', 'a@b')).toBe(false);
    expect(fitsFormat('digits', '00123')).toBe(true);
    expect(fitsFormat('digits', '12a')).toBe(false);
    expect(fitsFormat('phone', '')).toBe(true);
  });
});

describe('isColumnField', () => {
  it('gives a column to answers and to info texts with a rule only', () => {
    expect(fields.filter(isColumnField).map(f => f.id)).toEqual(['a', 'b', 'c', 'e', 'f']);
  });
});
