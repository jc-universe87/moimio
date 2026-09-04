#!/usr/bin/env python3
"""Fail if Moimio CE's version markers disagree (v1.0.4c).

Markers:
  backend/app/version.py      __version__ = "1.0.4c"
  frontend/package.json       "moimioVersion": "v1.0.4c"

Always: the two must name the same version (the frontend carries a
leading "v", the backend does not).

On a tag push (GITHUB_REF_NAME starts with "v", or --tag given): the tag
must equal the frontend marker, and CHANGELOG.md must have a
"## [<version>]" heading for it.

Runs in the CI `checks` job before any image is built, so a ship with a
stale marker fails at the push, not in the sidebar three days later.
Usage: python3 scripts/check-version-markers.py [--tag vX.Y.Z]
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def backend_version() -> str:
    text = (ROOT / "backend/app/version.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        sys.exit("backend/app/version.py: no __version__ found")
    return m.group(1)


def frontend_version() -> str:
    pkg = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    v = pkg.get("moimioVersion", "")
    if not v.startswith("v"):
        sys.exit(f'frontend/package.json: moimioVersion {v!r} must start with "v"')
    return v


def main(argv: list[str]) -> int:
    tag = None
    if "--tag" in argv:
        tag = argv[argv.index("--tag") + 1]
    elif os.environ.get("GITHUB_REF_TYPE") == "tag":
        tag = os.environ.get("GITHUB_REF_NAME")

    be = backend_version()
    fe = frontend_version()
    problems = []
    if f"v{be}" != fe:
        problems.append(f"backend {be!r} vs frontend {fe!r}")

    if tag and tag.startswith("v"):
        if tag != fe:
            problems.append(f"tag {tag!r} vs frontend marker {fe!r}")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        if not re.search(rf"^## \[{re.escape(tag[1:])}\]", changelog, re.M):
            problems.append(f"CHANGELOG.md has no '## [{tag[1:]}]' heading")

    if problems:
        print("check-version-markers: MISMATCH")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"check-version-markers: OK, {fe}" + (f" (tag {tag})" if tag else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
