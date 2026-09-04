/**
 * groupTypeLabel — v1.0.4c payload pins.
 *
 * The rename fix rests on one contract: the edit form sends `name` /
 * `item_label` only when the organiser changed the text. If this ever
 * regresses, a stale tab can again silently detach a built-in type from
 * its translation, and the backend has no way to tell.
 */
import { describe, it, expect } from 'vitest';
import { editStateFor, updatePayloadFor } from './groupTypeLabel';

const t = (k) => ({ 'organise.default_type.rooms': 'Zimmerbelegung', 'organise.default_type.room': 'Zimmer' }[k] ?? `[${k}]`);
const rooms = { id: 'c1', name: 'Room Allocation', item_label: 'Room', name_key: 'rooms', item_label_key: 'room', rule_type: 'exclusive', is_default: true };

describe('editStateFor', () => {
  it('shows the translated names and remembers them', () => {
    const s = editStateFor(rooms, t);
    expect(s.name).toBe('Zimmerbelegung');
    expect(s.item_label).toBe('Zimmer');
    expect(s._shownName).toBe('Zimmerbelegung');
    expect(s._shownItemLabel).toBe('Zimmer');
  });
});

describe('updatePayloadFor', () => {
  it('omits name and item_label when neither box was touched', () => {
    const payload = updatePayloadFor({ ...editStateFor(rooms, t), rule_type: 'nonexclusive' });
    expect(payload).not.toHaveProperty('name');
    expect(payload).not.toHaveProperty('item_label');
    expect(payload).not.toHaveProperty('_shownName');
    expect(payload).not.toHaveProperty('_shownItemLabel');
    expect(payload.rule_type).toBe('nonexclusive');
  });

  it('sends name only when the name box changed', () => {
    const payload = updatePayloadFor({ ...editStateFor(rooms, t), name: 'Zimmer' });
    expect(payload.name).toBe('Zimmer');
    expect(payload).not.toHaveProperty('item_label');
  });

  it('sends item_label only when the label box changed', () => {
    const payload = updatePayloadFor({ ...editStateFor(rooms, t), item_label: 'Chalet' });
    expect(payload.item_label).toBe('Chalet');
    expect(payload).not.toHaveProperty('name');
  });

  it('treats an empty label the same as no label', () => {
    const custom = { id: 'c2', name: 'Tables', item_label: null, rule_type: 'exclusive', is_default: false };
    const payload = updatePayloadFor(editStateFor(custom, t));
    expect(payload).not.toHaveProperty('item_label');
  });
});
