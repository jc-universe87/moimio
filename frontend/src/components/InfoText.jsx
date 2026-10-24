// v1.0.7 — an organiser's info text on the registration form.
//
// Plain text, with two kinds of link and nothing else:
//   • a pasted web address:          https://example.org/consent.pdf
//   • a link with its own wording:   [Consent form](https://example.org/consent.pdf)
// Only http and https. Line breaks are kept. No HTML is ever interpreted:
// everything is rendered as React text, so an organiser's text cannot put
// markup or script on a public page.

const LINK = /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>()]+)/g;
// A sentence ending right after an address keeps its full stop.
const TRAILING = /[.,;:!?'"]+$/;

export function parseInfoText(text) {
  const out = [];
  let last = 0;
  for (const m of String(text ?? '').matchAll(LINK)) {
    let href = m[2] || m[3];
    let label = m[1] || href;
    let end = m.index + m[0].length;
    if (m[3]) {
      const tail = (href.match(TRAILING) || [''])[0];
      if (tail) {
        href = href.slice(0, -tail.length);
        label = href;
        end -= tail.length;
      }
    }
    if (m.index > last) out.push({ text: text.slice(last, m.index) });
    out.push({ text: label, href });
    last = end;
  }
  if (last < String(text ?? '').length) out.push({ text: text.slice(last) });
  return out;
}

export default function InfoText({ title, text, linkColor }) {
  return (
    <div className="rounded-lg border border-steel-blue/20 bg-steel-blue/5 px-3 py-2.5">
      {title && <p className="text-sm font-semibold text-gray-700 mb-0.5">{title}</p>}
      <p className="text-sm text-gray-600 whitespace-pre-wrap break-words">
        {parseInfoText(text).map((part, i) => (part.href ? (
          <a key={i} href={part.href} target="_blank" rel="noopener noreferrer"
            className="underline underline-offset-2"
            style={{ color: linkColor || 'var(--io-accent, #4682B4)' }}>
            {part.text}
          </a>
        ) : <span key={i}>{part.text}</span>))}
      </p>
    </div>
  );
}
