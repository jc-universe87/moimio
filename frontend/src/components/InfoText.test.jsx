import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import InfoText, { parseInfoText } from './InfoText';

describe('parseInfoText', () => {
  it('turns a pasted address into a link and keeps the full stop', () => {
    expect(parseInfoText('See https://example.org/a.pdf.')).toEqual([
      { text: 'See ' },
      { text: 'https://example.org/a.pdf', href: 'https://example.org/a.pdf' },
      { text: '.' },
    ]);
  });
  it('turns [wording](address) into a link with that wording', () => {
    expect(parseInfoText('[Consent form](https://example.org/c.pdf) please')).toEqual([
      { text: 'Consent form', href: 'https://example.org/c.pdf' },
      { text: ' please' },
    ]);
  });
  it('leaves anything that is not http or https as plain text', () => {
    expect(parseInfoText('[x](javascript:alert(1)) ftp://a.b')).toEqual([
      { text: '[x](javascript:alert(1)) ftp://a.b' },
    ]);
  });
});

describe('InfoText', () => {
  it('never interprets HTML', () => {
    const { container } = render(<InfoText title="T" text={'<b>bold</b><script>x()</script>'} />);
    expect(container.querySelector('b')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(container.textContent).toContain('<b>bold</b>');
  });
  it('opens links in a new tab without handing the page over', () => {
    const { container } = render(<InfoText text="https://example.org" />);
    const a = container.querySelector('a');
    expect(a.getAttribute('target')).toBe('_blank');
    expect(a.getAttribute('rel')).toBe('noopener noreferrer');
  });
  it('keeps the line breaks the organiser typed', () => {
    const { container } = render(<InfoText text={'one\ntwo'} />);
    expect(container.querySelector('p.whitespace-pre-wrap').textContent).toBe('one\ntwo');
  });
});
