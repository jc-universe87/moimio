/**
 * normalizeSearch — fold a name or query to a form that ignores the
 * cosmetic differences people type inconsistently, so a participant
 * search never fails on punctuation or accents alone.
 *
 * Handled:
 *   - hyphens and dashes:        eun-hye = eunhye = eun hye
 *   - apostrophes (every kind):  O'Brien = O’Brien = OBrien  (straight,
 *                                curly ’ ‘, modifier ʼ, ʻokina, backtick)
 *   - spaces / periods / middots
 *   - accents (French/Spanish/Nordic/Baltic/Czech/Romanian/Vietnamese/etc.):
 *                                François = francois, Núñez = nunez,
 *                                Åström = astroem, Nguyễn = nguyen
 *   - German umlauts and ß:      Müller = Mueller = müller
 *                                (ä→ae, ö→oe, ü→ue, ß→ss, matching the
 *                                official DIN transliteration)
 *   - special Latin letters that don't decompose: Turkish ı→i, Polish ł→l,
 *                                Croatian/Vietnamese đ→d, Icelandic þ→th ð→d,
 *                                French œ→oe, Maltese ħ→h
 *
 * Every Latin-script name folds to plain a–z. NOT handled (deliberately):
 *   - non-Latin scripts (Cyrillic, Greek, Arabic, Hangul, CJK): searching in
 *     one script won't find another — cross-script transliteration is a
 *     separate, much larger (and lossy) feature
 *   - fuzzy / typo tolerance (edit distance) — a dropped umlaut written bare
 *     ("muller") is a misspelling, not a spacing/accent variant
 */
export function normalizeSearch(s) {
  return (s || '')
    .toLowerCase()
    // German expansions first — must run before NFD would fold ü→u
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/æ/g, 'ae')
    .replace(/ø/g, 'o')
    // special Latin letters that do NOT decompose under NFD (they are their
    // own code points, not base+accent), so they must be mapped by hand:
    .replace(/ı/g, 'i')                 // Turkish dotless i
    .replace(/ł/g, 'l')                 // Polish l-stroke
    .replace(/đ/g, 'd').replace(/ð/g, 'd') // Croatian/Vietnamese d-stroke, Icelandic eth
    .replace(/þ/g, 'th')                // Icelandic thorn
    .replace(/œ/g, 'oe')                // French/OE ligature
    .replace(/ħ/g, 'h').replace(/ŧ/g, 't').replace(/ŋ/g, 'n') // Maltese h-bar, t-bar, eng
    // strip remaining combining accents: é→e, ñ→n, å→a, ç→c, ï→i, ...
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    // drop separators typed inconsistently: apostrophes (straight/curly/
    // modifier/okina/backtick), hyphens & dashes, whitespace, periods, middot
    .replace(/['\u2018\u2019\u02bb\u02bc`.\u00b7\u2010\u2011\u2013\u2014\u2212\s-]+/g, '');
}
