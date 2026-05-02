#!/usr/bin/env python3
"""
validate-i18n-keys.py — verify every static t('key') callsite in
frontend/src has a matching key in i18n/locales/en.json.

Catches the dot-vs-underscore class of bug that hit twice in
production (v0.61c-1 delete.confirm, v0.70b-1 archive.confirm), where
a developer wrote `t('foo.bar.baz')` but the actual key was stored as
`foo.bar_baz` (or vice versa) — silently rendering a bracketed raw
key like [foo.bar.baz] in the UI until a real-use screenshot caught
it.

This validator runs at build time (wired into `npm run build` via
package.json), failing the Docker image build before deploy if any
static callsite references a key not present in en.json.

Usage:
    python3 scripts/validate-i18n-keys.py [--quiet] [--json]

Exit codes:
    0 — every static callsite resolves cleanly; build can proceed
    1 — at least one static callsite references a missing key
    2 — internal error (en.json malformed, src/ missing, etc.)

Static callsite forms recognised:
    t('foo.bar.baz')
    t("foo.bar.baz")
    t('foo.bar.baz', { var: x })
    t("foo.bar.baz", { var: x })

Skipped (reported as informational unless --quiet):
    t(`foo.bar.${x}`)        — dynamic template literal
    t(`literal-no-interp`)   — plain template literal (none in use today)
    t(varName)               — variable key (e.g. t(labelKey))

Scope: every .js/.jsx (and .ts/.tsx for future-proofing) file under
frontend/src/. Comments are not stripped before scanning — a t()
callsite mentioned in a comment will be checked. This is intentional:
keep the validator simple and the codebase free of stale references
even in comments.

Parity between en.json and the other 5 locale files is NOT checked
here — that's the splitter's responsibility (split-translations.py),
and during v0.70 the non-EN locales are deliberately stale pending
the operator's translation-overhaul ship.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Repo layout: frontend/scripts/ -> ../src/i18n/locales/en.json
SCRIPT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = SCRIPT_DIR.parent
SRC_DIR = FRONTEND_DIR / "src"
EN_JSON = SRC_DIR / "i18n" / "locales" / "en.json"

# File extensions to scan
SCAN_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}

# Match t('...') or t("...") — STATIC string literal only.
# Captures the key. Allows optional whitespace inside the parens and
# allows a trailing `,` (for the {vars} second arg) or `)`.
#
# Pattern: \bt\(\s*(['"])([^'"]+)\1\s*[,)]
#   \b           word boundary so we don't match `set(...)`, `get(...)`, etc.
#   t\(          literal `t(`
#   \s*          optional whitespace
#   (['"])       opening quote (group 1)
#   ([^'"]+)     the key — anything that isn't a quote (group 2)
#   \1           matching closing quote
#   \s*          optional whitespace
#   [,)]         either a comma (vars follow) or close paren
STATIC_T_RE = re.compile(r"\bt\(\s*(['\"])([^'\"]+)\1\s*[,)]")

# Match t(`...`) — TEMPLATE LITERAL form. Includes both interpolated
# (`foo.${x}`) and plain (`foo`) variants. Reported as skipped.
TEMPLATE_T_RE = re.compile(r"\bt\(\s*`([^`]*)`")

# Match t(identifier) where identifier is a bare variable name —
# t(labelKey), t(label), etc. NOT a function call (no opening paren
# after the identifier). Reported as skipped.
VAR_T_RE = re.compile(r"\bt\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)")


def fail(msg: str, code: int = 2) -> None:
    print(f"validate-i18n-keys: error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_en_keys() -> set:
    if not EN_JSON.is_file():
        fail(f"en.json not found at {EN_JSON}")
    try:
        with EN_JSON.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"en.json is not valid JSON: {e}")
    if not isinstance(data, dict):
        fail("en.json must be a flat object (key → string)")
    return set(data.keys())


def iter_source_files():
    if not SRC_DIR.is_dir():
        fail(f"src dir not found at {SRC_DIR}")
    for path in sorted(SRC_DIR.rglob("*")):
        if path.is_file() and path.suffix in SCAN_EXTENSIONS:
            yield path


def scan_file(path: Path):
    """
    Return (static_hits, template_hits, var_hits) for one file.

    Each hit is a dict: {"file": <relpath>, "line": <int>, "key": <str>}.
    For template/var hits, "key" is the raw match content (template
    body or variable name) so the operator can locate it.
    """
    static, template, var = [], [], []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return static, template, var
    rel = str(path.relative_to(FRONTEND_DIR))
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in STATIC_T_RE.finditer(line):
            static.append({"file": rel, "line": lineno, "key": m.group(2)})
        for m in TEMPLATE_T_RE.finditer(line):
            template.append({"file": rel, "line": lineno, "key": m.group(1)})
        # var matches must NOT also match the static or template form
        # — and STATIC_T_RE already consumed any t('foo') on this line.
        # Re-scan the line and exclude positions already covered by
        # static/template matches.
        covered = set()
        for m in STATIC_T_RE.finditer(line):
            covered.update(range(m.start(), m.end()))
        for m in TEMPLATE_T_RE.finditer(line):
            covered.update(range(m.start(), m.end()))
        for m in VAR_T_RE.finditer(line):
            if m.start() in covered:
                continue
            var.append({"file": rel, "line": lineno, "key": m.group(1)})
    return static, template, var


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress informational output (skipped callsites, summary). "
             "Errors still print. Use in CI when you want minimal noise.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit a single JSON document to stdout instead of human output. "
             "Sets --quiet implicitly.",
    )
    args = parser.parse_args()
    if args.json:
        args.quiet = True

    en_keys = load_en_keys()

    all_static, all_template, all_var = [], [], []
    for path in iter_source_files():
        s, t, v = scan_file(path)
        all_static.extend(s)
        all_template.extend(t)
        all_var.extend(v)

    misses = [hit for hit in all_static if hit["key"] not in en_keys]

    if args.json:
        print(json.dumps({
            "en_keys_count": len(en_keys),
            "static_callsites": len(all_static),
            "unique_static_keys": len({h["key"] for h in all_static}),
            "template_callsites": all_template,
            "var_callsites": all_var,
            "misses": misses,
        }, indent=2))
        sys.exit(1 if misses else 0)

    # Human-readable mode
    if not args.quiet:
        print(f"validate-i18n-keys: scanning {SRC_DIR}")
        print(f"  en.json: {len(en_keys)} keys at {EN_JSON.relative_to(FRONTEND_DIR)}")
        print(f"  static callsites: {len(all_static)} "
              f"({len({h['key'] for h in all_static})} unique keys)")
        if all_template:
            print(f"  template-literal callsites (skipped): {len(all_template)}")
            for hit in all_template:
                print(f"    {hit['file']}:{hit['line']}  t(`{hit['key']}`)")
        if all_var:
            print(f"  variable-key callsites (skipped): {len(all_var)}")
            for hit in all_var:
                print(f"    {hit['file']}:{hit['line']}  t({hit['key']})")
        print()

    if misses:
        print(f"validate-i18n-keys: FAIL — {len(misses)} static callsite(s) "
              f"reference key(s) not in en.json:", file=sys.stderr)
        for hit in misses:
            print(f"  {hit['file']}:{hit['line']}  t('{hit['key']}')",
                  file=sys.stderr)
        print(file=sys.stderr)
        print("Each line above is a key the developer wrote but does not "
              "exist in en.json.", file=sys.stderr)
        print("Likely cause: dot-vs-underscore typo, or a key that was "
              "renamed/removed without updating callers.", file=sys.stderr)
        print("Fix by either correcting the callsite or adding the key to "
              "all 6 locale files (per TRANSLATION_RULE.md).", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print("validate-i18n-keys: OK — every static callsite resolves.")
    sys.exit(0)


if __name__ == "__main__":
    main()
