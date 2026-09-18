#!/usr/bin/env python3
"""Set Moimio CE's version in every file marker at once (v1.0.4c).

Usage: python3 scripts/bump-version.py v1.0.4d

Writes backend/app/version.py — both `__version__` and its own line-1
docstring — and frontend/package.json, then runs
check-version-markers.py. Does not touch CHANGELOG.md or git.

v1.0.4w (VERSION-1): the docstring used to be left for a human to edit,
and it drifted — at v1.0.4l it still read "(v1.0.4k)". It is set here and
checked by check-version-markers.py, so it cannot drift again.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not re.fullmatch(r"v\d+\.\d+\.\d+[a-z]*", argv[0]):
        print(__doc__)
        return 2
    tag = argv[0]
    bare = tag[1:]

    p = ROOT / "backend/app/version.py"
    s = p.read_text(encoding="utf-8")
    s, n = re.subn(r'^__version__\s*=\s*"[^"]+"', f'__version__ = "{bare}"', s, flags=re.M)
    if n != 1:
        sys.exit("backend/app/version.py: expected exactly one __version__ line")

    s, n = re.subn(r"\(v[0-9][^)]*\)", f"({tag})", s, count=1)
    if n != 1:
        sys.exit("backend/app/version.py: line-1 docstring names no (vX.Y.Z)")
    p.write_text(s, encoding="utf-8")

    p = ROOT / "frontend/package.json"
    s = p.read_text(encoding="utf-8")
    s, n = re.subn(r'"moimioVersion":\s*"[^"]+"', f'"moimioVersion": "{tag}"', s)
    if n != 1:
        sys.exit("frontend/package.json: expected exactly one moimioVersion")
    p.write_text(s, encoding="utf-8")
    print(f"bump-version: all file markers now {tag}")
    return subprocess.call([sys.executable, str(ROOT / "scripts/check-version-markers.py")])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
