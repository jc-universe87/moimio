#!/usr/bin/env python3
"""
split-translations.py — convert a unified translations.json into the
per-locale file structure used since v0.70.

Usage:
    python3 scripts/split-translations.py PATH_TO_UNIFIED.json

Input format (the operator's translation pipeline output):
    {
      "en":    { "key.one": "...", "key.two": "...", ... },
      "de":    { "key.one": "...", "key.two": "...", ... },
      "ko":    { ... },
      "es":    { ... },
      "pt-BR": { ... },
      "fr":    { ... }
    }

Output:
    src/i18n/locales/en.json
    src/i18n/locales/de.json
    src/i18n/locales/ko.json
    src/i18n/locales/es.json
    src/i18n/locales/pt-BR.json
    src/i18n/locales/fr.json

Each output file contains ONLY that language's flat key→string map,
with keys alphabetically sorted (matches the project i18n discipline).

Safety checks (any failure aborts before any file is written):
  - Input must contain all 6 SUPPORTED_LANGS as top-level keys.
  - Each language block must have the same key set as English (parity).
  - If existing locale files have keys missing from the input, abort —
    likely a stale or partial drop. Override with --force.
"""

import argparse
import json
import sys
from pathlib import Path

SUPPORTED_LANGS = ["en", "de", "ko", "es", "pt-BR", "fr"]
LOCALES_DIR = Path(__file__).resolve().parent.parent / "src" / "i18n" / "locales"


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="Unified translations.json from the pipeline")
    parser.add_argument("--force", action="store_true",
                        help="Skip the 'input is missing existing keys' safety check")
    args = parser.parse_args()

    if not args.input.is_file():
        fail(f"input file not found: {args.input}")

    try:
        with args.input.open(encoding="utf-8") as f:
            unified = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"input is not valid JSON: {e}")

    # Top-level structure check
    if not isinstance(unified, dict):
        fail("input must be a JSON object with one block per language")
    missing_langs = [lang for lang in SUPPORTED_LANGS if lang not in unified]
    if missing_langs:
        fail(f"input is missing top-level language blocks: {', '.join(missing_langs)}")
    extra_langs = [lang for lang in unified if lang not in SUPPORTED_LANGS]
    if extra_langs:
        fail(f"input has unexpected top-level language blocks: {', '.join(extra_langs)}")

    # Parity check: every language must have the same key set as EN
    en_keys = set(unified["en"].keys())
    parity_problems = []
    for lang in SUPPORTED_LANGS:
        keys = set(unified[lang].keys())
        missing = en_keys - keys
        extra = keys - en_keys
        if missing or extra:
            parity_problems.append((lang, missing, extra))
    if parity_problems:
        for lang, missing, extra in parity_problems:
            print(f"  {lang}: missing={sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}, "
                  f"extra={sorted(extra)[:5]}{'...' if len(extra) > 5 else ''}", file=sys.stderr)
        fail("input has parity gaps between language blocks; refusing to write")

    # Existing-keys safety check (skipped with --force)
    if not args.force and LOCALES_DIR.is_dir():
        for lang in SUPPORTED_LANGS:
            existing_path = LOCALES_DIR / f"{lang}.json"
            if not existing_path.is_file():
                continue
            try:
                with existing_path.open(encoding="utf-8") as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                continue
            existing_keys = set(existing.keys())
            input_keys = set(unified[lang].keys())
            dropped = existing_keys - input_keys
            if dropped:
                print(f"  {lang}: input is missing {len(dropped)} keys present in current "
                      f"{existing_path.name}: {sorted(dropped)[:5]}"
                      f"{'...' if len(dropped) > 5 else ''}", file=sys.stderr)
                fail("input would drop existing keys; use --force to confirm intentional removal")

    # All checks passed — write the per-locale files
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)
    for lang in SUPPORTED_LANGS:
        out = LOCALES_DIR / f"{lang}.json"
        sorted_block = dict(sorted(unified[lang].items()))
        with out.open("w", encoding="utf-8") as f:
            json.dump(sorted_block, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  wrote {out} ({len(sorted_block)} keys, {out.stat().st_size:,} bytes)")

    print(f"\n{len(SUPPORTED_LANGS)} locale files written to {LOCALES_DIR}/")


if __name__ == "__main__":
    main()
