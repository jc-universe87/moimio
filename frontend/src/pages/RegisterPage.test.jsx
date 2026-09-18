/**
 * RegisterPage — the field marking. v1.0.4zf (2.7).
 *
 * v1.0.4ze recorded the server's per-field errors in state and rendered
 * none of them, so the banner said "check the fields marked below" and
 * nothing was marked. Worse than the raw error it replaced: that at least
 * named the field. Two of Johannes's twelve browser checks failed on it.
 *
 * Two causes, both pinned here:
 *   - the patch that read `err.fieldErrors` landed on the page-LOAD catch,
 *     not the submit catch, so the state was never populated at all;
 *   - nothing rendered the state even when it was set.
 *
 * The form is rendered for real. It needs a router (useParams), the i18n
 * provider it wraps itself in, and `fetch` for the event it loads on mount;
 * the submit goes through the real api client, which is mocked at the
 * network boundary so the server's actual 422 shape is what is exercised.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import en from '../i18n/locales/en.json';
import RegisterPage from './RegisterPage';

const EVENT_ID = '11111111-1111-1111-1111-111111111111';

// What the server really answers for `rest@gmail.com3242`, copied from a
// live call against the running stack.
const VALIDATION_422 = {
  detail: {
    key: 'errors.validation.summary',
    params: {},
    fields: { email: 'errors.field.email' },
  },
};

function mockFetch({ rejectSubmit = true } = {}) {
  return vi.fn(async (url, opts = {}) => {
    const u = String(url);
    if (opts.method === 'POST' && u.includes('/register')) {
      if (!rejectSubmit) {
        return { ok: true, status: 201, json: async () => ({ id: 'p1' }) };
      }
      return { ok: false, status: 422, json: async () => VALIDATION_422 };
    }
    if (u.includes('/custom-fields')) return { ok: true, json: async () => [] };
    if (u.includes('/allocation-categories')) return { ok: true, json: async () => [] };
    if (u.includes('/fields')) return { ok: true, json: async () => [] };
    // the event itself
    return {
      ok: true, status: 200,
      json: async () => ({
        id: EVENT_ID, name: 'Spring Retreat', status: 'open',
        start_date: '2026-06-01', end_date: '2026-06-03', settings: {},
      }),
    };
  });
}

async function renderForm(opts) {
  global.fetch = mockFetch(opts);
  render(
    <MemoryRouter initialEntries={[`/register/${EVENT_ID}`]}>
      <Routes>
        <Route path="/register/:eventId" element={<RegisterPage />} />
      </Routes>
    </MemoryRouter>,
  );
  // The form appears once the event has loaded. Its labels carry no
  // `htmlFor` and the inputs are their siblings, not their children, so
  // findByLabelText cannot reach them; the name attribute can.
  let emailInput = null;
  await waitFor(() => {
    emailInput = document.querySelector('input[name="email"]');
    expect(emailInput).not.toBeNull();
  }, { timeout: 3000 });
  return emailInput;
}

async function submitWith(email) {
  const emailInput = await renderForm();
  fireEvent.change(emailInput, { target: { name: 'email', value: email } });
  for (const [name, value] of [['first_name', 'Test'], ['last_name', 'Rest']]) {
    const el = document.querySelector(`input[name="${name}"]`);
    if (el) fireEvent.change(el, { target: { name, value } });
  }
  const consent = document.querySelector('input[type="checkbox"]');
  if (consent && !consent.checked) fireEvent.click(consent);
  fireEvent.submit(document.querySelector('form'));
  return emailInput;
}

beforeEach(() => {
  vi.restoreAllMocks();
  window.sessionStorage.clear();
  window.localStorage.clear();
});

describe('the rejected field is marked', () => {
  it('shows the field\'s own message, not only the summary', async () => {
    await submitWith('rest@gmail.com3242');
    // The specific message, beside the box — this is what was missing.
    await waitFor(() => {
      expect(screen.getByText(en['errors.field.email'])).toBeInTheDocument();
    });
  });

  it('marks the input itself', async () => {
    const emailInput = await submitWith('rest@gmail.com3242');
    await waitFor(() => {
      expect(emailInput).toHaveAttribute('aria-invalid', 'true');
    });
    // The house pattern, the same one the extra-person cards use.
    expect(emailInput.className).toContain('border-burgundy');
    expect(emailInput.className).not.toContain('border-gray-200');
  });

  it('shows the summary banner as well', async () => {
    await submitWith('rest@gmail.com3242');
    await waitFor(() => {
      expect(screen.getByText(en['errors.validation.summary'])).toBeInTheDocument();
    });
  });

  it('clears the mark, the message and the banner as it is corrected', async () => {
    const emailInput = await submitWith('rest@gmail.com3242');
    await waitFor(() => {
      expect(screen.getByText(en['errors.field.email'])).toBeInTheDocument();
    });

    fireEvent.change(emailInput, {
      target: { name: 'email', value: 'rest@gmail.com' },
    });

    await waitFor(() => {
      expect(screen.queryByText(en['errors.field.email'])).toBeNull();
    });
    expect(emailInput).toHaveAttribute('aria-invalid', 'false');
    // The last field error going takes the banner with it (2.7.3).
    expect(screen.queryByText(en['errors.validation.summary'])).toBeNull();
  });
});

describe('nothing is marked when nothing is wrong', () => {
  it('leaves every field unmarked before a submit', async () => {
    const emailInput = await renderForm();
    expect(emailInput).toHaveAttribute('aria-invalid', 'false');
    expect(emailInput.className).toContain('border-gray-200');
    expect(screen.queryByText(en['errors.field.email'])).toBeNull();
  });
});
