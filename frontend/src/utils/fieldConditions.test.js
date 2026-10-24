import { describe, it, expect } from 'vitest';
import { ageOn, answersToSend, conditionMet, isColumnField, visibleFieldIds } from './fieldConditions';

const teamer = { id: 'a', field_type: 'boolean', show_if: null };
const team = { id: 'b', field_type: 'text', show_if: { source: 'a', any_of: ['true'] } };
const note = { id: 'c', field_type: 'info', show_if: { source: 'date_of_birth', age_under: 18 } };
const welcome = { id: 'd', field_type: 'info', show_if: null };
const role = { id: 'e', field_type: 'select', options: { choices: ['Cook', 'Driver'] }, show_if: null };
const shift = { id: 'f', field_type: 'text', show_if: { source: 'e', any_of: ['Cook'] } };
const fields = [teamer, team, note, welcome, role, shift];
const START = '2026-06-01';

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
    expect(visibleFieldIds(fields, {}, '', START).has('b')).toBe(false);
    expect(visibleFieldIds(fields, { a: 'false' }, '', START).has('b')).toBe(false);
    expect(visibleFieldIds(fields, { a: 'true' }, '', START).has('b')).toBe(true);
  });
  it('shows the consent note to under-18s on the start date only', () => {
    expect(visibleFieldIds(fields, {}, '2008-06-02', START).has('c')).toBe(true);
    expect(visibleFieldIds(fields, {}, '2008-06-01', START).has('c')).toBe(false);
    expect(visibleFieldIds(fields, {}, '', START).has('c')).toBe(false);
  });
  it('always shows a field or note without a rule', () => {
    const shown = visibleFieldIds(fields, {}, '', START);
    expect(shown.has('a') && shown.has('d') && shown.has('e')).toBe(true);
  });
  it('matches a dropdown answer against the ticked options', () => {
    expect(visibleFieldIds(fields, { e: 'Cook' }, '', START).has('f')).toBe(true);
    expect(visibleFieldIds(fields, { e: 'Driver' }, '', START).has('f')).toBe(false);
  });
  it('hides a field whose source is itself hidden', () => {
    const chain = [teamer, team, { id: 'g', field_type: 'text', show_if: { source: 'b', any_of: ['x'] } }];
    // b is not a valid source type, so g never shows; and b's stale answer
    // never counts while a is No.
    expect(visibleFieldIds(chain, { a: 'false', b: 'x' }, '', START).has('g')).toBe(false);
  });
});

describe('answersToSend', () => {
  it('drops answers to hidden fields and never sends an info text', () => {
    const values = { a: 'false', b: 'Kitchen', c: 'x', d: 'y' };
    const shown = visibleFieldIds(fields, values, '2008-06-02', START);
    expect(answersToSend(fields, values, shown)).toEqual({ a: 'false' });
  });
});

describe('conditionMet', () => {
  it('reads a Yes/No answer however it was spelled', () => {
    const ctx = (v) => ({ answers: { a: v }, sourceTypes: { a: 'boolean' }, dob: '', refDate: START });
    expect(conditionMet(team.show_if, ctx('yes'))).toBe(true);
    expect(conditionMet(team.show_if, ctx('0'))).toBe(false);
  });
});

describe('isColumnField', () => {
  it('gives a column to answers and to info texts with a rule only', () => {
    expect(fields.filter(isColumnField).map(f => f.id)).toEqual(['a', 'b', 'c', 'e', 'f']);
  });
});
