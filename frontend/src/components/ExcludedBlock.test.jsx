/**
 * ExcludedBlock — v1.0.4k.
 *
 * Four pins, all of them things that fail silently rather than loudly:
 * the block must not render an empty box; the header must use the real
 * singular/plural key pair; every chip must carry a reachable undo
 * control (an exclusion nobody can find is an exclusion nobody can
 * reverse); and a drop on the block must stop propagating, or it
 * reaches the panel's own "drop here to unassign" handler and silently
 * unassigns instead of excluding.
 *
 * Interpolation uses the real English strings, so a locale edit that
 * drops {n} is caught here.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import en from '../i18n/locales/en.json';

vi.mock('../hooks/useI18n', () => ({
  useI18n: () => ({
    t: (k, params) => {
      const raw = en[k];
      if (raw === undefined) return `[${k}]`;
      if (!params) return raw;
      return Object.entries(params).reduce(
        (s, [key, val]) => s.replace(new RegExp(`\\{${key}\\}`, 'g'), String(val)),
        raw,
      );
    },
  }),
}));

import ExcludedBlock from './ExcludedBlock';

const people = [
  { id: 'p1', first_name: 'Ann', last_name: 'Smith' },
  { id: 'p2', first_name: 'Ben', last_name: 'Jones' },
];

describe('ExcludedBlock', () => {
  it('renders nothing when nobody is excluded', () => {
    const { container } = render(<ExcludedBlock people={[]} canEdit />);
    expect(container.firstChild).toBeNull();
  });

  it('uses the singular header for one person and the plural for more', () => {
    const { unmount } = render(<ExcludedBlock people={people.slice(0, 1)} canEdit />);
    expect(screen.getByRole('button', { expanded: false })).toHaveTextContent(
      en['organise.exclude.header_one'],
    );
    unmount();

    render(<ExcludedBlock people={people} canEdit />);
    expect(screen.getByRole('button', { expanded: false })).toHaveTextContent('Excluded (2)');
  });

  it('gives every chip an undo control that reports the right id', () => {
    const onInclude = vi.fn();
    render(<ExcludedBlock people={people} canEdit onInclude={onInclude} />);
    fireEvent.click(screen.getByRole('button', { expanded: false }));

    const undos = screen.getAllByTitle(en['organise.exclude.undo_title']);
    expect(undos).toHaveLength(2);
    fireEvent.click(undos[1]);
    expect(onInclude).toHaveBeenCalledWith('p2');
  });

  it('hides the undo control when the viewer cannot edit', () => {
    render(<ExcludedBlock people={people} canEdit={false} />);
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    expect(screen.queryByTitle(en['organise.exclude.undo_title'])).toBeNull();
  });

  it('excludes on drop and stops the event reaching the panel below', () => {
    // The panel root carries "drop here to unassign". Without
    // stopPropagation on the block, a drop here silently unassigns and
    // looks like it worked.
    const onDropExclude = vi.fn();
    const panelDrop = vi.fn();
    render(
      <div onDragOver={(e) => e.preventDefault()} onDrop={panelDrop}>
        <ExcludedBlock people={people} canEdit onDropExclude={onDropExclude} />
      </div>,
    );

    const header = screen.getByRole('button', { expanded: false });
    const block = header.parentElement;
    fireEvent.dragOver(block);
    expect(screen.getByText(en['organise.exclude.drop_hint'])).toBeTruthy();

    fireEvent.drop(block);
    expect(onDropExclude).toHaveBeenCalledTimes(1);
    expect(panelDrop).not.toHaveBeenCalled();
  });
});
