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
 *
 * v1.0.4zg (FORM-2) adds the second half. The form carries `noValidate`,
 * because Chrome's own bubbles are written in Chrome's language — a German
 * registrant was told "Please fill out this field." in English, and no page
 * can translate or suppress that text. Turning the browser's check off is one
 * attribute; the work is that Moimio must now check everything it was
 * checking. These tests are what says it does: nothing leaves the page while
 * a check fails, and a complete form still goes.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import en from '../i18n/locales/en.json';
import RegisterPage from './RegisterPage';

const EVENT_ID = '11111111-1111-1111-1111-111111111111';

// What the server really answers for `rest@example.com3242`, copied from a
// live call against the running stack.
const VALIDATION_422 = {
  detail: {
    key: 'errors.validation.summary',
    params: {},
    fields: { email: 'errors.field.email' },
  },
};

function mockFetch({ rejectSubmit = true, privacyNoticeUrl = null, workspaceFails = false } = {}) {
  return vi.fn(async (url, opts = {}) => {
    const u = String(url);
    // LEGAL-1: the workspace's privacy notice URL, or null, or a broken read.
    if (u.includes('/workspace/public')) {
      if (workspaceFails) return { ok: false, status: 500, json: async () => ({}) };
      return { ok: true, status: 200, json: async () => ({ privacy_notice_url: privacyNoticeUrl }) };
    }
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

const registerPosts = () =>
  (global.fetch.mock?.calls || []).filter(
    ([url, opts]) => opts?.method === 'POST' && String(url).includes('/register'));

const set = (name, value) => {
  const el = document.querySelector(`[name="${name}"]`);
  expect(el, `no control named ${name}`).not.toBeNull();
  fireEvent.change(el, { target: { name, value } });
  return el;
};

const tickConsent = () => {
  const consent = document.querySelector('input[name="gdpr_consent"]');
  if (consent && !consent.checked) fireEvent.click(consent);
};

/** Everything the server needs, correctly filled. */
function fillValid(email = 'rest@example.com') {
  set('first_name', 'Test');
  set('last_name', 'Rest');
  set('email', email);
  tickConsent();
}

const submitForm = () => fireEvent.submit(document.querySelector('#register-form'));

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
    await submitWith('rest@example.com3242');
    // The specific message, beside the box — this is what was missing.
    await waitFor(() => {
      expect(screen.getByText(en['errors.field.email'])).toBeInTheDocument();
    });
  });

  it('marks the input itself', async () => {
    const emailInput = await submitWith('rest@example.com3242');
    await waitFor(() => {
      expect(emailInput).toHaveAttribute('aria-invalid', 'true');
    });
    // The house pattern, the same one the extra-person cards use.
    expect(emailInput.className).toContain('border-burgundy');
    expect(emailInput.className).not.toContain('border-gray-200');
  });

  it('shows the summary banner as well', async () => {
    await submitWith('rest@example.com3242');
    await waitFor(() => {
      expect(screen.getByText(en['errors.validation.summary'])).toBeInTheDocument();
    });
  });

  it('clears the mark, the message and the banner as it is corrected', async () => {
    const emailInput = await submitWith('rest@example.com3242');
    await waitFor(() => {
      expect(screen.getByText(en['errors.field.email'])).toBeInTheDocument();
    });

    fireEvent.change(emailInput, {
      target: { name: 'email', value: 'rest@example.com' },
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

// ─── v1.0.4zg (FORM-2): the browser stops being asked ────────────────────

describe('the form does its own checking', () => {
  it('does not ask the browser to validate', async () => {
    await renderForm();
    const form = document.querySelector('#register-form');
    expect(form).not.toBeNull();
    // The attribute IS the fix for the English bubbles; if it comes off,
    // Chrome speaks over Moimio again, in its own language.
    expect(form.noValidate).toBe(true);
  });

  it('keeps `required` on the inputs — it is what a screen reader announces', async () => {
    await renderForm();
    for (const name of ['first_name', 'last_name', 'email', 'gdpr_consent']) {
      expect(document.querySelector(`[name="${name}"]`).required).toBe(true);
    }
  });

  it('catches an empty required field itself, and sends nothing', async () => {
    await renderForm();
    submitForm();

    await waitFor(() => {
      expect(screen.getAllByText(en['errors.field.required']).length).toBeGreaterThan(0);
    });
    const email = document.querySelector('input[name="email"]');
    expect(email).toHaveAttribute('aria-invalid', 'true');
    expect(email.className).toContain('border-burgundy');
    expect(screen.getByText(en['errors.validation.summary'])).toBeInTheDocument();
    // The one that matters: it never left the page.
    expect(registerPosts()).toHaveLength(0);
  });

  it('asks for consent in Moimio\'s words, not the browser\'s', async () => {
    await renderForm();
    set('first_name', 'Test');
    set('last_name', 'Rest');
    set('email', 'rest@example.com');
    submitForm();

    await waitFor(() => {
      expect(screen.getByText(en['errors.participant.gdpr_required'])).toBeInTheDocument();
    });
    expect(document.querySelector('input[name="gdpr_consent"]'))
      .toHaveAttribute('aria-invalid', 'true');
    expect(registerPosts()).toHaveLength(0);
  });

  it('catches a malformed address without asking the server', async () => {
    await renderForm();
    fillValid('nope@nope');
    submitForm();

    await waitFor(() => {
      expect(screen.getByText(en['errors.field.email'])).toBeInTheDocument();
    });
    expect(registerPosts()).toHaveLength(0);
  });

  it('clears each mark as it is corrected', async () => {
    await renderForm();
    submitForm();
    await waitFor(() => {
      expect(screen.getAllByText(en['errors.field.required']).length).toBeGreaterThan(0);
    });

    fillValid();

    await waitFor(() => {
      expect(screen.queryByText(en['errors.field.required'])).toBeNull();
    });
    expect(screen.queryByText(en['errors.validation.summary'])).toBeNull();
    expect(document.querySelector('input[name="email"]'))
      .toHaveAttribute('aria-invalid', 'false');
  });

  it('still submits a form with nothing wrong with it', async () => {
    await renderForm({ rejectSubmit: false });
    fillValid();
    submitForm();

    await waitFor(() => expect(registerPosts()).toHaveLength(1));
  });

  it('checks an extra person\'s card in the same pass', async () => {
    await renderForm();
    fillValid();
    fireEvent.click(screen.getByText(new RegExp(en['register.add_person'])));

    // The card carries the primary's email but no name and no consent.
    const card = document.getElementById('extra-person-0');
    expect(card, 'the card the scroll aims at').not.toBeNull();
    submitForm();

    await waitFor(() => {
      expect(card.querySelectorAll('[aria-invalid="true"]').length).toBeGreaterThan(0);
    });
    expect(screen.getByText(
      en['errors.register.extra_people_incomplete'].replace('{count}', '1'),
    )).toBeInTheDocument();
    expect(registerPosts()).toHaveLength(0);
  });
});

describe('the privacy notice link (LEGAL-1)', () => {
  const consentLabel = () =>
    document.querySelector('input[name="gdpr_consent"]').closest('div').querySelector('label');

  it('renders nothing extra when the workspace has not set a URL', async () => {
    await renderForm({ privacyNoticeUrl: null });
    expect(screen.queryByTestId('privacy-notice-link')).toBeNull();
    // The consent sentence is exactly what it was.
    expect(consentLabel().textContent).toBe(`${en['register.gdpr']} *`);
  });

  it('renders a link right after the consent sentence when one is set', async () => {
    await renderForm({ privacyNoticeUrl: 'https://example.org/privacy' });
    const link = await screen.findByTestId('privacy-notice-link');
    expect(link.getAttribute('href')).toBe('https://example.org/privacy');
    expect(link.textContent).toBe(en['register.privacy_notice']);
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
    // Sentence, link, required marker, in that order.
    expect(consentLabel().textContent).toBe(`${en['register.gdpr']} ${en['register.privacy_notice']} *`);
  });

  it('shows the same link on an extra person\'s card', async () => {
    await renderForm({ privacyNoticeUrl: 'https://example.org/privacy' });
    await screen.findByTestId('privacy-notice-link');
    fireEvent.click(screen.getByText(new RegExp(en['register.add_person'])));
    const card = document.getElementById('extra-person-0');
    expect(card.querySelector('[data-testid="privacy-notice-link"]')).not.toBeNull();
  });

  it('does not block registration when the URL is unset', async () => {
    await renderForm({ rejectSubmit: false, privacyNoticeUrl: null });
    fillValid();
    submitForm();
    await waitFor(() => expect(registerPosts()).toHaveLength(1));
  });

  it('leaves the form intact when the workspace read fails', async () => {
    await renderForm({ workspaceFails: true });
    expect(document.querySelector('#register-form')).not.toBeNull();
    expect(screen.queryByTestId('privacy-notice-link')).toBeNull();
  });
});
