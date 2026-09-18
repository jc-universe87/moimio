/**
 * I18nProvider — the document says which language it is in. v1.0.4zg (2.3).
 *
 * `index.html` ships `lang="en"`, so until now a German page claimed to be
 * English. That is what a screen reader reads the page in, and what a browser
 * uses to decide whether to offer a translation.
 *
 * It is NOT what fixes the browser's own validation bubbles — Chrome writes
 * those in its own UI language whatever the document says, which is why the
 * registration form turns them off instead (see RegisterPage.test.jsx).
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

import { I18nProvider, useI18n } from './useI18n';

function LangSwitch() {
  const { lang, setLang } = useI18n();
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <button onClick={() => setLang('de')}>de</button>
      <button onClick={() => setLang('ko')}>ko</button>
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  document.documentElement.lang = 'en';
});

describe('the document language', () => {
  it('is set from the interface language on mount', async () => {
    localStorage.setItem('moimio_lang', 'de');
    render(<I18nProvider><LangSwitch /></I18nProvider>);

    await waitFor(() => expect(document.documentElement.lang).toBe('de'));
  });

  it('follows the language when it changes', async () => {
    render(<I18nProvider><LangSwitch /></I18nProvider>);
    await waitFor(() => expect(document.documentElement.lang).toBe('en'));

    fireEvent.click(screen.getByText('ko'));

    await waitFor(() => expect(document.documentElement.lang).toBe('ko'));
    expect(screen.getByTestId('lang')).toHaveTextContent('ko');
  });
});
