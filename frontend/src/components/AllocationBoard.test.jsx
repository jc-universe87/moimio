/**
 * AllocationBoard — the stranded place, per path. v1.0.4zf (2.8).
 *
 * Excluding somebody takes them out of every unit they hold in this
 * group type, a locked one included, and the lock stays on: the place
 * stays empty across engine runs with nothing on screen connecting the
 * two. v1.0.4ze added the offer that says so, from `handleExclude`.
 *
 * Johannes could not confirm it in the browser. The reason is here: the
 * bulk selection bar does not go through `handleExclude` at all. It
 * called the endpoint and threw the answer away, so excluding four
 * people at once said nothing about any place it stranded.
 *
 * One test per path that can strand a place. The board is rendered for
 * real; only its edges are mocked — the api, the toast host, the confirm
 * overlay, the event stream and the marks store.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import en from '../i18n/locales/en.json';

const api = {
  units: { list: vi.fn(), update: vi.fn(), create: vi.fn(), delete: vi.fn() },
  alloc: { byCategory: vi.fn(), assign: vi.fn(), unassign: vi.fn(), move: vi.fn() },
  cat: { listExclusions: vi.fn(), addExclusion: vi.fn(), removeExclusion: vi.fn() },
};
const confirmMock = vi.fn();

vi.mock('../services/api', () => ({
  allocationUnits: { get list() { return api.units.list; }, get update() { return api.units.update; },
    get create() { return api.units.create; }, get delete() { return api.units.delete; } },
  allocations: { get byCategory() { return api.alloc.byCategory; }, get assign() { return api.alloc.assign; },
    get unassign() { return api.alloc.unassign; }, get move() { return api.alloc.move; } },
  allocationCategories: { get listExclusions() { return api.cat.listExclusions; },
    get addExclusion() { return api.cat.addExclusion; }, get removeExclusion() { return api.cat.removeExclusion; } },
  notes: { list: async () => [] },
  preferenceRequests: { list: async () => [] },
  getToken: () => 't',
  formatErrorMessage: (e) => String(e?.message || e),
}));

const t = (k, params) => {
  const raw = en[k];
  if (raw === undefined) return `[${k}]`;
  if (!params) return raw;
  return Object.entries(params).reduce(
    (s, [key, val]) => s.replace(new RegExp(`\\{${key}\\}`, 'g'), String(val)), raw);
};
vi.mock('../hooks/useI18n', () => ({ useI18n: () => ({ t, lang: 'en' }) }));
vi.mock('../hooks/useToast', () => ({ useToast: () => ({ showToast: () => {}, ToastHost: () => null }) }));
vi.mock('./ConfirmOverlay', () => ({
  useConfirmOverlay: () => ({ confirm: (...a) => confirmMock(...a), ConfirmOverlay: () => null }),
}));
vi.mock('../hooks/useEventStream', () => ({ useEventStream: () => {} }));
vi.mock('../hooks/useMarks', () => ({
  useMarks: () => ({ defs: [], assignments: [], getParticipantMarks: () => [], assign: () => {}, unassign: () => {} }),
}));

import AllocationBoard from './AllocationBoard';

const CATEGORY = { id: 'c1', name: 'Rooms', unit_type: 'room', is_confirmed: false, settings: {} };
const ANN = { id: 'p1', first_name: 'Ann', last_name: 'Smith' };
const BEN = { id: 'p2', first_name: 'Ben', last_name: 'Jones' };
const CAI = { id: 'p3', first_name: 'Cai', last_name: 'Lee' };
// What the endpoint answers when the exclusion emptied a place in a
// unit the organiser had locked.
const STRANDED = { vacated_kept_units: [{ id: 'u1', name: 'Room 1' }] };

function board(props = {}) {
  return render(
    <MemoryRouter><AllocationBoard
      eventId="e1" eventName="Retreat" category={CATEGORY} allCategories={[CATEGORY]}
      participantList={[ANN, BEN, CAI]} noteCounts={{}} isAdmin
      onSelectCategory={() => {}} onDataChange={() => {}} {...props} /></MemoryRouter>,
  );
}

const excludeControls = () => screen.getAllByLabelText(en['organise.exclude.action_title']);

beforeEach(() => {
  vi.clearAllMocks();
  api.units.list.mockResolvedValue([{ id: 'u1', name: 'Room 1', capacity: 4, is_kept: true }]);
  api.alloc.byCategory.mockResolvedValue({ u1: [{ participant_id: 'p3', participant_name: 'Cai Lee' }] });
  api.cat.listExclusions.mockResolvedValue({ excluded_ids: [] });
  api.cat.addExclusion.mockResolvedValue(STRANDED);
  api.units.update.mockResolvedValue({});
  confirmMock.mockResolvedValue(true);
});

async function ready() {
  await waitFor(() => expect(screen.getByText('Ann Smith')).toBeInTheDocument());
}

describe('every path that strands a place says so', () => {
  it('says it from a pool chip', async () => {
    board();
    await ready();
    // The pool chips come first in the tree; Ann is the first of them.
    fireEvent.click(excludeControls()[0]);

    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1));
    expect(confirmMock.mock.calls[0][0].message).toBe(
      t('organise.exclude.left_locked_place', { name: 'Ann Smith', unit: 'Room 1' }));
    await waitFor(() => expect(api.units.update).toHaveBeenCalledWith(
      'e1', 'c1', 'u1', { is_kept: false }));
  });

  it('says it from a unit member', async () => {
    board();
    await ready();
    await waitFor(() => expect(screen.getByText('Cai Lee')).toBeInTheDocument());
    // The member row's control is the last of them: the pool holds Ann
    // and Ben, the unit holds Cai.
    const controls = excludeControls();
    fireEvent.click(controls[controls.length - 1]);

    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1));
    expect(confirmMock.mock.calls[0][0].message).toContain('Room 1');
    await waitFor(() => expect(api.units.update).toHaveBeenCalledWith(
      'e1', 'c1', 'u1', { is_kept: false }));
  });

  it('says it from the bulk selection bar — the path that said nothing', async () => {
    board();
    await ready();
    fireEvent.click(screen.getByText('Ann Smith'));
    fireEvent.click(screen.getByText('Ben Jones'));

    const bar = await screen.findByText(en['organise.exclude.action']);
    fireEvent.click(bar);

    await waitFor(() => expect(api.cat.addExclusion).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(confirmMock).toHaveBeenCalled());
    expect(confirmMock.mock.calls[0][0].message).toContain('Room 1');
    await waitFor(() => expect(api.units.update).toHaveBeenCalledWith(
      'e1', 'c1', 'u1', { is_kept: false }));
  });

  it('offers one place once, however many people vacated it', async () => {
    board();
    await ready();
    fireEvent.click(screen.getByText('Ann Smith'));
    fireEvent.click(screen.getByText('Ben Jones'));
    fireEvent.click(await screen.findByText(en['organise.exclude.action']));

    await waitFor(() => expect(api.cat.addExclusion).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(api.units.update).toHaveBeenCalled());
    expect(confirmMock).toHaveBeenCalledTimes(1);
  });

  it('says nothing when no place was stranded', async () => {
    api.cat.addExclusion.mockResolvedValue({ vacated_kept_units: [] });
    board();
    await ready();
    fireEvent.click(excludeControls()[0]);

    await waitFor(() => expect(api.cat.addExclusion).toHaveBeenCalled());
    expect(confirmMock).not.toHaveBeenCalled();
    expect(api.units.update).not.toHaveBeenCalled();
  });
});
