#!/usr/bin/env python3
"""Validate local Markdown links with only Python's standard library.

External URLs and same-page heading anchors are intentionally not checked.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "node_modules", ".venv", ".next"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in SKIP for part in path.relative_to(ROOT).parts)
    ]


def main() -> int:
    errors: list[str] = []
    count = 0
    for doc in markdown_files():
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            # Avoid most fenced / code example issues; local links in prose still work.
            if line.lstrip().startswith(("http://", "https://")):
                continue
            for match in LINK_RE.finditer(line):
                raw = match.group(1).strip().split(" ", 1)[0].strip("<>")
                if not raw or raw.startswith(("#", "mailto:", "tel:", "data:")):
                    continue
                u = urlsplit(raw)
                if u.scheme or u.netloc:
                    continue
                target = unquote(u.path)
                if not target:
                    continue
                # Absolute Markdown paths are repository-relative.
                resolved = (ROOT / target.lstrip("/")) if target.startswith("/") else (doc.parent / target)
                count += 1
                if not resolved.exists():
                    errors.append(f"{doc.relative_to(ROOT)}:{lineno}: broken local link: {raw}")
    if errors:
        print("\n".join(errors))
        print(f"FAILED: {len(errors)} broken links, {count} checked.")
        return 1
    print(f"OK: {count} local links across {len(markdown_files())} Markdown files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
