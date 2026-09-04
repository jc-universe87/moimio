#!/usr/bin/env python3
"""Add one or more UI strings to all six locale files, keeping them
sorted and byte-stable.

Usage:
    python3 frontend/scripts/add-i18n-key.py additions.json

`additions.json` maps key -> {locale: string} and must cover every
locale in LOCALES. Existing keys are only overwritten with --force.
Files are written with the exact format the repository uses (2-space
indent, UTF-8, sorted keys, trailing newline), so the diff is the added
lines and nothing else. Run frontend/scripts/validate-i18n-keys.py
afterwards.
"""
import json
import sys
from pathlib import Path

LOCALES = ["en", "de", "ko", "es", "fr", "pt-BR"]
HERE = Path(__file__).resolve().parent
LOCALE_DIR = HERE.parent / "src" / "i18n" / "locales"


def main(argv: list[str]) -> int:
    force = "--force" in argv
    args = [a for a in argv if a != "--force"]
    if len(args) != 1:
        print(__doc__)
        return 2
    additions = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    for key, per_locale in additions.items():
        missing = [l for l in LOCALES if l not in per_locale]
        if missing:
            print(f"{key}: missing locales {missing}")
            return 1
    for loc in LOCALES:
        path = LOCALE_DIR / f"{loc}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, per_locale in additions.items():
            if key in data and not force:
                print(f"{loc}: {key} already present, skipping (use --force to overwrite)")
                continue
            data[key] = per_locale[loc]
        out = json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n"
        path.write_text(out, encoding="utf-8")
        print(f"{loc}: {len(data)} keys")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
