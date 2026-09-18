import { describe, it, expect } from 'vitest';
import { collapseMoves } from './AllocationHistory';

/**
 * v1.0.4k: settle the "can an exclusion invent a phantom move?"
 * question by running it, not by reasoning about it.
 *
 * `collapseMoves` walks the newest-first audit feed and turns a
 * consecutive {assign, unassign} pair into one "Moved from X to Y"
 * line. Exclusions write an `exclude` row plus one `unassign` per unit
 * vacated, all in one transaction, and `occurred_at` uses
 * clock_timestamp() so those rows are guaranteed to have DISTINCT,
 * correctly ordered timestamps.
 *
 * Write order inside add_exclusion (allocation_service.py): the
 * exclude row first, then the unassigns. Newest-first, therefore, a
 * burst reads [unassign…, exclude] — there is no assign in it at all.
 *
 * Rows below are in the order the API returns them: newest first.
 */

const row = (o) => ({
  id: o.id,
  event_type: o.type,
  source: o.source || 'manual',
  unit_name: o.unit ?? '',
  category_name: o.category ?? 'Rooms',
  // v1.0.4zb (HIST-1): the feed spans every group type, so a pair must
  // share one before it can be read as a move. Left undefined unless a
  // case says otherwise, which is how the rows above still pair.
  category_id: o.categoryId,
  actor_display_name: 'Org',
  occurred_at: o.at || '2026-09-16T10:00:00Z',
  meta: null,
});

describe('collapseMoves — exclusion sequences', () => {
  it('leaves a single-unit exclusion burst uncollapsed', () => {
    // Time order: exclude, then unassign Room A. Newest-first below.
    const items = collapseMoves([
      row({ id: '2', type: 'unassign', unit: 'Room A', source: 'participant_excluded' }),
      row({ id: '1', type: 'exclude', unit: '' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['unassign', 'exclude']);
  });

  it('leaves a multi-unit exclusion burst uncollapsed', () => {
    const items = collapseMoves([
      row({ id: '4', type: 'unassign', unit: 'Team C', source: 'participant_excluded' }),
      row({ id: '3', type: 'unassign', unit: 'Team B', source: 'participant_excluded' }),
      row({ id: '2', type: 'unassign', unit: 'Team A', source: 'participant_excluded' }),
      row({ id: '1', type: 'exclude', unit: '' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['unassign', 'unassign', 'unassign', 'exclude']);
    expect(items.some(i => i.kind === 'move')).toBe(false);
  });

  it('does not invent a move when the person is later placed in the SAME group type', () => {
    // assign_participant writes the include row immediately before the
    // assign row, so the include sits between the two and breaks the
    // pair on its own — the source guard is not what saves this one.
    const items = collapseMoves([
      row({ id: '4', type: 'assign', unit: 'Room B' }),
      row({ id: '3', type: 'include', unit: '' }),
      row({ id: '2', type: 'unassign', unit: 'Room A', source: 'participant_excluded' }),
      row({ id: '1', type: 'exclude', unit: '' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['assign', 'include', 'unassign', 'exclude']);
  });

  it('does not invent a move when the person is later placed in a DIFFERENT group type', () => {
    // This is the reachable one. No include row is written (there is no
    // exclusion in the other group type to lift), so the assign and the
    // exclusion-driven unassign sit adjacent with nothing between them.
    // Without the source guard this collapsed into
    // "Moved from Room A to Team 1".
    const items = collapseMoves([
      row({ id: '3', type: 'assign', unit: 'Team 1', category: 'Teams' }),
      row({ id: '2', type: 'unassign', unit: 'Room A', source: 'participant_excluded' }),
      row({ id: '1', type: 'exclude', unit: '' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['assign', 'unassign', 'exclude']);
  });

  it('still collapses an ordinary manual move', () => {
    const items = collapseMoves([
      row({ id: '2', type: 'assign', unit: 'Room B' }),
      row({ id: '1', type: 'unassign', unit: 'Room A', source: 'manual_cascade' }),
    ]);
    expect(items).toHaveLength(1);
    expect(items[0].kind).toBe('move');
    expect(items[0].from_unit).toBe('Room A');
    expect(items[0].to_unit).toBe('Room B');
  });

  it('still refuses to collapse a same-unit pair', () => {
    const items = collapseMoves([
      row({ id: '2', type: 'assign', unit: 'Room A' }),
      row({ id: '1', type: 'unassign', unit: 'Room A' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['assign', 'unassign']);
  });
});

describe('collapseMoves — group types (v1.0.4zb, HIST-1)', () => {
  it('does not invent a move across two different group types', () => {
    // The feed is scoped to one participant but spans every group type, and
    // the pairing test compares unit names. Removing somebody from Room A
    // and later placing them in Team 1 — two unrelated actions, two
    // different group types — used to render as "Moved from Room A to
    // Team 1". Neither row carries the exclusion source, so v1.0.4k's guard
    // never saw this one.
    const items = collapseMoves([
      row({ id: '2', type: 'assign', unit: 'Team 1', category: 'Small Groups', categoryId: 'c2' }),
      row({ id: '1', type: 'unassign', unit: 'Room A', category: 'Rooms', categoryId: 'c1' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['assign', 'unassign']);
    expect(items.some(i => i.kind === 'move')).toBe(false);
  });

  it('still collapses a genuine move within one group type', () => {
    // The thing the fix must not break.
    const items = collapseMoves([
      row({ id: '2', type: 'assign', unit: 'Room B', category: 'Rooms', categoryId: 'c1' }),
      row({ id: '1', type: 'unassign', unit: 'Room A', category: 'Rooms', categoryId: 'c1' }),
    ]);
    expect(items.map(i => i.kind)).toEqual(['move']);
    expect(items[0].from_unit).toBe('Room A');
    expect(items[0].to_unit).toBe('Room B');
  });
});
