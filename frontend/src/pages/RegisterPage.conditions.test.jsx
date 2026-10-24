/**
 * RegisterPage — conditional fields and info texts (v1.0.7).
 *
 * "Teamer" Yes/No opens "Which team" (required); a parental-consent note
 * shows to anyone under 18 on the event's start date. Same rendering and
 * network mocking as RegisterPage.test.jsx.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import RegisterPage from './RegisterPage';

const EVENT_ID = '22222222-2222-2222-2222-222222222222';
const TEAMER = 'f-teamer';
const TEAM = 'f-team';
const NOTE = 'f-note';

const CUSTOM_FIELDS = [
  { id: TEAMER, label: 'Teamer', field_type: 'boolean', is_required: false, show_if: null },
  { id: TEAM, label: 'Which team', field_type: 'text', is_required: true,
    show_if: { source: TEAMER, any_of: ['true'] } },
  { id: NOTE, label: 'Parental consent', field_type: 'info', is_required: false,
    options: { text: 'Bring the [signed form](https://example.org/consent.pdf).' },
    show_if: { source: 'date_of_birth', age_under: 18 } },
];

function mockFetch() {
  return vi.fn(async (url, opts = {}) => {
    const u = String(url);
    if (u.includes('/workspace/public')) return { ok: true, json: async () => ({ privacy_notice_url: null }) };
    if (opts.method === 'POST' && u.includes('/register')) {
      return { ok: true, status: 201, json: async () => ({ id: 'p1' }) };
    }
    if (u.includes('/custom-fields')) return { ok: true, json: async () => CUSTOM_FIELDS };
    if (u.includes('/fields')) {
      return { ok: true, json: async () => [{ field_name: 'date_of_birth', is_enabled: true, is_required: false }] };
    }
    return {
      ok: true, status: 200,
      json: async () => ({ id: EVENT_ID, name: 'Camp', status: 'open', start_date: '2026-06-01', settings: {} }),
    };
  });
}

async function renderForm() {
  global.fetch = mockFetch();
  render(
    <MemoryRouter initialEntries={[`/register/${EVENT_ID}`]}>
      <Routes><Route path="/register/:eventId" element={<RegisterPage />} /></Routes>
    </MemoryRouter>,
  );
  await waitFor(() => expect(document.querySelector('input[name="email"]')).not.toBeNull(), { timeout: 3000 });
}

const set = (name, value) => fireEvent.change(document.querySelector(`[name="${name}"]`), { target: { name, value } });
const teamerRadio = (yes) => document.querySelectorAll(`input[name="cf_${TEAMER}"]`)[yes ? 0 : 1];
const teamInput = () => document.querySelector(`input[name="cf_${TEAM}"]`);
const fillValid = () => {
  set('first_name', 'Ana'); set('last_name', 'Lee'); set('email', 'ana@example.com');
  fireEvent.click(document.querySelector('input[name="gdpr_consent"]'));
};
const lastPostBody = () => {
  const posts = global.fetch.mock.calls.filter(([u, o]) => o?.method === 'POST' && String(u).includes('/register'));
  return posts.length ? JSON.parse(posts[posts.length - 1][1].body) : null;
};

describe('RegisterPage conditional fields', () => {
  it('shows "Which team" only once Teamer is Yes', async () => {
    await renderForm();
    expect(teamInput()).toBeNull();
    fireEvent.click(teamerRadio(true));
    expect(teamInput()).not.toBeNull();
    fireEvent.click(teamerRadio(false));
    expect(teamInput()).toBeNull();
  });

  it('does not ask for a required field that is hidden, and does not send its old answer', async () => {
    await renderForm();
    fillValid();
    fireEvent.click(teamerRadio(true));
    fireEvent.change(teamInput(), { target: { value: 'Kitchen' } });
    fireEvent.click(teamerRadio(false));
    fireEvent.submit(document.querySelector('#register-form'));
    await waitFor(() => expect(lastPostBody()).not.toBeNull());
    expect(lastPostBody().custom_fields).toEqual({ [TEAMER]: 'false' });
  });

  it('asks for the team when Teamer is Yes', async () => {
    await renderForm();
    fillValid();
    fireEvent.click(teamerRadio(true));
    fireEvent.submit(document.querySelector('#register-form'));
    await waitFor(() => expect(teamInput().getAttribute('aria-invalid')).toBe('true'));
    expect(lastPostBody()).toBeNull();
  });

  it('shows the consent note, with its link, to someone under 18 on the start date', async () => {
    await renderForm();
    expect(document.body.textContent).not.toContain('Parental consent');
    set('date_of_birth', '2008-06-02');
    expect(document.body.textContent).toContain('Parental consent');
    const link = [...document.querySelectorAll('a')].find(a => a.textContent === 'signed form');
    expect(link.getAttribute('href')).toBe('https://example.org/consent.pdf');
    set('date_of_birth', '2008-06-01');
    expect(document.body.textContent).not.toContain('Parental consent');
  });
});
