#!/usr/bin/env python3
"""Language bar and link check for the translated docs.

The README, the user manual and the installation guides exist in six
languages, side by side: `03-people.md` (English) and `03-people.de.md`,
`03-people.ko.md`, ... Every one of them starts with a language bar
linking its siblings.

    python3 scripts/docs-i18n.py bar     # add or refresh the language bars
    python3 scripts/docs-i18n.py check   # verify links and #anchors

`check` exits non-zero on a missing sibling, a broken relative link or an
anchor that matches no heading in its target.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (suffix, name shown in the bar). English has no suffix.
LANGS = [
    ("", "English"),
    ("de", "Deutsch"),
    ("ko", "한국어"),
    ("es", "Español"),
    ("pt-BR", "Português (Brasil)"),
    ("fr", "Français"),
]

SOURCES = (
    [Path("README.md")]
    + sorted(Path("docs/manual").glob("[0-9][0-9]-*.md"))
    + [Path("docs/manual/README.md"), Path("docs/manual/quick-guide.md")]
    + [Path("docs/installation/README.md"), Path("docs/installation/beginner.md"),
       Path("docs/installation/quick-guide.md")]
)
# Only English sources: drop anything that already carries a language suffix.
_SUFFIXES = tuple(f".{s}.md" for s, _ in LANGS if s)
SOURCES = [p for p in SOURCES if not p.name.endswith(_SUFFIXES)]


def variant(src: Path, suffix: str) -> Path:
    return src if not suffix else src.with_name(f"{src.stem}.{suffix}.md")


def bar(src: Path, current: str) -> str:
    centred = src == Path("README.md")
    parts = []
    for suffix, name in LANGS:
        target = variant(src, suffix).name
        if suffix == current:
            parts.append(f"<b>{name}</b>" if centred else f"**{name}**")
        else:
            parts.append(f'<a href="{target}">{name}</a>' if centred else f"[{name}]({target})")
    line = "🌐 " + " · ".join(parts)
    return f'<p align="center">{line}</p>' if centred else line


def _is_bar(line: str) -> bool:
    return line.startswith("🌐 ") or line.startswith('<p align="center">🌐 ')


def cmd_bar() -> int:
    for src in SOURCES:
        for suffix, _ in LANGS:
            path = ROOT / variant(src, suffix)
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").split("\n")
            if lines and _is_bar(lines[0]):
                lines = lines[1:]
                while lines and not lines[0].strip():
                    lines = lines[1:]
            path.write_text(bar(src, suffix) + "\n\n" + "\n".join(lines), encoding="utf-8")
    return 0


# ─── check ────────────────────────────────────────────────────────────

_LINK_RE = re.compile(r'\]\(([^)\s]+)\)|href="([^"]+)"|src="([^"]+)"|srcset="([^"]+)"')
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _strip_inline(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("`", "").replace("*", "")


def slugs(path: Path) -> set[str]:
    """GitHub's heading anchors for a Markdown file."""
    seen: dict[str, int] = {}
    out: set[str] = set()
    in_fence = False
    for line in path.read_text(encoding="utf-8").split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if not m:
            continue
        slug = re.sub(r"[^\w\- ]", "", _strip_inline(m.group(2)).strip().lower()).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        out.add(slug if n == 0 else f"{slug}-{n}")
    return out


def _links(path: Path):
    in_fence = False
    for no, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", "", line)
        for m in _LINK_RE.finditer(line):
            yield no, next(g for g in m.groups() if g)


def cmd_check() -> int:
    problems = []
    files = []
    for src in SOURCES:
        for suffix, _ in LANGS:
            path = ROOT / variant(src, suffix)
            if path.exists():
                files.append(path)
            else:
                problems.append(f"missing: {variant(src, suffix)}")
    for path in files:
        rel = path.relative_to(ROOT)
        for no, link in _links(path):
            if re.match(r"^[a-z]+:", link) or link.startswith("//"):
                continue
            target, _, anchor = link.partition("#")
            dest = path if not target else (path.parent / target).resolve()
            if not dest.exists():
                problems.append(f"{rel}:{no}: broken link {link}")
                continue
            if anchor and dest.suffix == ".md" and anchor not in slugs(dest):
                problems.append(f"{rel}:{no}: no heading for #{anchor} in {dest.relative_to(ROOT)}")
    for p in problems:
        print(p)
    print(f"docs-i18n: checked {len(files)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit({"bar": cmd_bar, "check": cmd_check}[cmd]())
