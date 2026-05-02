# `backend/app/fonts/` — self-hosted PDF fonts

Self-hosted from v0.70d-3c-10. Replaces the prior `fonts-dejavu-core`
apt dependency for PDF generation. Brand-aligned with the frontend's
`/public/fonts/` (which uses Nunito woff2 for web rendering).

## Files

| File                      | Purpose                                  | Licence            |
|---------------------------|------------------------------------------|--------------------|
| `Nunito-Regular.ttf`      | Body text — fpdf2 style key `""`         | SIL OFL 1.1 — see `OFL.txt` |
| `Nunito-Bold.ttf`         | Headers, emphasis — fpdf2 style key `"B"` | SIL OFL 1.1 — see `OFL.txt` |
| `Nunito-Italic.ttf`       | Empty-state placeholders — fpdf2 style key `"I"` | SIL OFL 1.1 — see `OFL.txt` |
| `Nunito-BoldItalic.ttf`   | Defensive — fpdf2 style key `"BI"`       | SIL OFL 1.1 — see `OFL.txt` |
| `OFL.txt`                 | SIL OFL 1.1 licence text                  | —                  |

## Why TTF and not woff2?

fpdf2 reads only TrueType (`.ttf`) and OpenType (`.otf`). The web
woff2 files at `frontend/public/fonts/` are subsetted variable
fonts intended for browser font-face — fpdf2 cannot consume them.
These TTFs are static instances at the specific weights the PDF
renderer asks for.

## Why not the apt package?

`fonts-dejavu-core` (Debian) was previously used — but it ships
only Sans regular + bold. `DejaVuSans-Oblique.ttf` lives in
`fonts-dejavu-extra`, which the Dockerfile didn't install. fpdf2
crashed with `FPDFException: Undefined font: dejavuI` whenever
the renderer hit a `set_font(family, "I", ...)` call. Self-hosting
the brand font with all four weights pinned in-repo eliminates
both the missing-weight bug and a dependency on what apt
happens to package today.

CJK rendering (Korean / Chinese / Japanese names) still falls
back to `fonts-noto-cjk`, installed via apt in the Dockerfile.
That package is ~92 MB and not part of brand identity, so it
stays apt-sourced.

## Licence compliance

All four TTFs are under the SIL Open Font License 1.1. The OFL
permits redistribution, modification, and use in commercial
products on the condition that the licence text travels with
the font files. `OFL.txt` in this directory satisfies that.

## Source

Official upstream: <https://github.com/googlefonts/nunito>
Pinned to the static-instance release shipped with the brand kit
(weights 400 / 700, regular and italic, four files total).
