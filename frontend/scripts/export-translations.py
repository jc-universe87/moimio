#!/usr/bin/env python3
"""
export-translations.py — assemble per-locale files into a unified
translations.json suitable for sending to a translation service.

Usage:
    python3 scripts/export-translations.py [-o OUTPUT_PATH]

Defaults:
    Output written to ../translations-export-{timestamp}.json (one
    directory above frontend/, since frontend/ should stay out of
    git for export artefacts).

Output format (matches the input format of split-translations.py
for a clean round-trip):
    {
      "en":    { "key.one": "...", "key.two": "...", ... },
      "de":    { ... },
      "ko":    { ... },
      "es":    { ... },
      "pt-BR": { ... },
      "fr":    { ... }
    }

Each language block is sorted alphabetically by key (matches the
project i18n discipline).

Safety checks (any failure aborts before writing output):
  - All 6 expected locale files must exist.
  - Each locale must have the same key set as English (parity check;
    same rule the validator enforces at build time).
  - Output path must not already exist (or --force to overwrite).
"""

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

SUPPORTED_LANGS = ["en", "de", "ko", "es", "pt-BR", "fr"]
LOCALES_DIR = Path(__file__).resolve().parent.parent / "src" / "i18n" / "locales"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent.parent  # one above frontend/


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output path (default: ../translations-export-{timestamp}.json)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing output file",
    )
    args = parser.parse_args()

    if not LOCALES_DIR.is_dir():
        fail(f"locales directory not found: {LOCALES_DIR}")

    # Read all 6 locale files (or fail loudly)
    blocks = {}
    for lang in SUPPORTED_LANGS:
        path = LOCALES_DIR / f"{lang}.json"
        if not path.is_file():
            fail(f"missing locale file: {path}")
        try:
            with path.open(encoding="utf-8") as f:
                blocks[lang] = json.load(f)
        except json.JSONDecodeError as e:
            fail(f"{path.name}: not valid JSON: {e}")
        if not isinstance(blocks[lang], dict):
            fail(f"{path.name}: must be a flat key→string object")

    # Parity check — every locale must have EN's key set
    en_keys = set(blocks["en"].keys())
    parity_problems = []
    for lang in SUPPORTED_LANGS:
        keys = set(blocks[lang].keys())
        missing = en_keys - keys
        extra = keys - en_keys
        if missing or extra:
            parity_problems.append((lang, missing, extra))
    if parity_problems:
        for lang, missing, extra in parity_problems:
            print(f"  {lang}: missing={sorted(missing)[:5]}"
                  f"{'...' if len(missing) > 5 else ''}, "
                  f"extra={sorted(extra)[:5]}"
                  f"{'...' if len(extra) > 5 else ''}", file=sys.stderr)
        fail("locale files have parity gaps; refusing to export")

    # Default output path: timestamped, sibling of frontend/
    if args.output is None:
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        args.output = DEFAULT_OUT_DIR / f"translations-export-{ts}.json"

    if args.output.exists() and not args.force:
        fail(f"output already exists: {args.output} (use --force to overwrite)")

    # Build unified output, alpha-sorted per locale (round-trip safe)
    unified = {}
    for lang in SUPPORTED_LANGS:
        unified[lang] = dict(sorted(blocks[lang].items()))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total_keys = len(en_keys)
    print(f"  wrote {args.output} ({total_keys} keys × {len(SUPPORTED_LANGS)} "
          f"locales, {args.output.stat().st_size:,} bytes)")
    print(f"\nReady to send. Round-trip via split-translations.py when "
          f"the translated file is back.")


if __name__ == "__main__":
    main()
