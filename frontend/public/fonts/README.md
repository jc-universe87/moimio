# /public/fonts — self-hosted fonts

Self-hosted from v0.70d-3c (R14 brand kit integration). Replaces
the prior fonts.bunny.net CDN dependency.

## Files

| File                            | Purpose                          | Licence            |
|---------------------------------|----------------------------------|--------------------|
| `nunito-latin.woff2`            | Nunito (variable, weights 400–800), Latin subset. Headings, wordmark.   | SIL OFL 1.1 — see `Nunito-OFL.txt` |
| `nunito-sans-latin.woff2`       | Nunito Sans (variable, weights 400–800), Latin subset. Body, labels.    | SIL OFL 1.1 — see `NunitoSans-OFL.txt` |
| `pretendard-medium.subset.woff2`| Pretendard Medium (500), Hangul subset. Loaded only when Korean text renders, via `unicode-range` in `index.css`. | SIL OFL 1.1 — see `Pretendard-LICENSE.txt` |

## Why subset?

Latin subsets are sized for Moimio's six locales' Latin coverage:
basic Latin, extended Latin, Latin Ext A/B, common punctuation,
arrows (→), and geometric shapes (·). Generated via `pyftsubset`
from the brand pack v1.2 source TTFs. Combined: 186 KB.

Pretendard is loaded conditionally: the `@font-face` rule in
`index.css` declares `unicode-range` covering Hangul + Hangul
Compat Jamo + Hangul Syllables + Halfwidth Hangul. Browsers
only fetch the file when rendering glyphs in that range.
Non-KR sessions never download the 268 KB.

## Licence compliance

All three font families are SIL Open Font License 1.1. The OFL
permits redistribution, modification, and use in commercial
products on the condition that the licence text travels with
the font files. The three `*-OFL.txt` and `*-LICENSE.txt` files
in this directory satisfy that requirement.

## Regenerating the subsets

If you need to extend the character coverage (e.g. Cyrillic,
Greek, more CJK), re-run `pyftsubset` from the brand pack
v1.2 source TTFs:

```bash
pyftsubset \
  /path/to/Nunito-VariableFont_wght.ttf \
  --output-file=nunito-latin.woff2 \
  --flavor=woff2 \
  --unicodes="U+0000-024F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2100-214F,U+2190-21FF,U+25A0-25FF,U+2E00-2E7F" \
  --layout-features='*' \
  --no-hinting
```

The brand kit's `moimio-brand-font/` directory contains the
original TTFs. Update the `--unicodes` range to include
additional ranges as needed.
