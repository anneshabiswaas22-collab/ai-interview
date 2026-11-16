#!/usr/bin/env python3
"""Validate the repository's Markdown: every relative link and image must exist, and every #anchor must match a heading.

Offline and deterministic (external URLs are not fetched; see docs/maintainers/releasing.md for the manual external-link check).
Usage: python scripts/check_docs.py            exit code 1 and a list of problems if anything is broken.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"node_modules", ".venv", "dist", "data", "logs", ".git", ".pytest_cache", ".ruff_cache"}
# Every inline link/image target, including the OUTER target of a nested badge link [![alt](img)](target):
#   ](<path with spaces>)  or  ](path "title")  ](path 'title')  ](path_(with)_parens)
INLINE = re.compile(r"\]\(\s*(?:<([^>\n]+)>|((?:[^()\s]|\([^()\s]*\))+))(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
REFDEF = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*<?([^\s>]+)>?", re.M)           # [label]: target
HTML_REF = re.compile(r"""<(?:img|a|source)\b[^>]*?\b(?:src|href|srcset)\s*=\s*["']([^"']+)["']""", re.I | re.S)
FENCE = re.compile(r"^ {0,3}(```|~~~)")


def markdown_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts))


def slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation except - and _, spaces to -."""
    text = re.sub(r"<[^>]+>", "", heading).strip().lower()
    text = re.sub(r"[`*_~]", lambda m: "_" if m.group(0) == "_" else "", text)
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def _blank_code(text: str) -> str:
    """Replace fenced code blocks and inline code with spaces (newlines kept), so offsets still map to line numbers."""
    out, in_code = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            in_code = not in_code
            out.append(" " * len(line))
        elif in_code:
            out.append(" " * len(line))
        else:
            out.append(re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


def anchors(path: Path) -> set[str]:
    out: dict[str, int] = {}
    found: set[str] = set()
    lines = _blank_code(path.read_text(encoding="utf-8")).split("\n")

    def add(heading: str) -> None:
        base = slug(heading)
        n = out.get(base, 0)
        found.add(base if n == 0 else f"{base}-{n}")
        out[base] = n + 1

    for i, line in enumerate(lines):
        m = re.match(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            add(m.group(1))
        elif i + 1 < len(lines) and line.strip() and re.match(r"^ {0,3}(=+|-+)\s*$", lines[i + 1]) and not re.match(r"^ {0,3}[-*>|]", line):
            add(line.strip())                                   # setext heading (underlined with === or ---)
        for a in re.findall(r"<a\s+(?:name|id)=[\"']([^\"']+)[\"']", line):
            found.add(a)
    return found


def links(path: Path) -> list[tuple[int, str]]:
    text = _blank_code(path.read_text(encoding="utf-8"))
    hits: list[tuple[int, str]] = []
    for rx in (INLINE, REFDEF, HTML_REF):
        for m in rx.finditer(text):
            target = next(g for g in m.groups() if g)
            hits.append((text.count("\n", 0, m.start()) + 1, target.strip()))
    return sorted(hits)


def exists_exact_case(path: Path) -> bool:
    """Path.exists() is case-insensitive on macOS and Windows; GitHub and Linux are not. Check every component's exact name."""
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return path.exists()
    cur = ROOT
    for part in rel.parts:
        if part in ("..", "."):
            cur = cur / part
            continue
        if not cur.is_dir() or part not in {p.name for p in cur.iterdir()}:
            return False
        cur = cur / part
    return True


def check() -> list[str]:
    problems: list[str] = []
    cache: dict[Path, set[str]] = {}
    for md in markdown_files():
        for n, target in links(md):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("//"):
                continue                               # external URL, mailto: ... (not fetched)
            ref, _, frag = target.partition("#")
            # normpath collapses ".." WITHOUT touching letter case (resolve() rewrites case to the on-disk name on Windows)
            dest = md if not ref else Path(os.path.normpath(md.parent / unquote(ref)))
            where = f"{md.relative_to(ROOT)}:{n}"
            if ref and not dest.exists():
                problems.append(f"{where}: missing file {ref}")
                continue
            if ref and not exists_exact_case(dest):
                problems.append(f"{where}: wrong letter case in {ref} (works on macOS/Windows, breaks on GitHub and Linux)")
                continue
            if frag and dest.suffix == ".md":
                if dest not in cache:
                    cache[dest] = anchors(dest)
                if frag.lower() not in cache[dest]:
                    problems.append(f"{where}: no heading for #{frag} in {dest.relative_to(ROOT)}")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print(p)
    print(f"{len(markdown_files())} Markdown files checked: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
