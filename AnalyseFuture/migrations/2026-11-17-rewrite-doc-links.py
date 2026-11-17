#!/usr/bin/env python3
"""One-time, auditable link migration for the 2026-11-17 docs taxonomy move."""

from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]

MOVES = {
    "docs/VISION.md": "docs/product/VISION.md",
    "docs/PRODUCT_REQUIREMENTS.md": "docs/product/PRODUCT_REQUIREMENTS.md",
    "docs/FEATURE_MATRIX.md": "docs/product/FEATURE_MATRIX.md",
    "docs/COMPETITOR_BENCHMARKS.md": "docs/product/COMPETITOR_BENCHMARKS.md",
    "docs/ARCHITECTURE.md": "docs/architecture/ARCHITECTURE.md",
    "docs/API_CONTRACTS.md": "docs/architecture/API_CONTRACTS.md",
    "docs/DATA_MODEL.md": "docs/architecture/DATA_MODEL.md",
    "docs/INTERVIEW_ENGINE.md": "docs/architecture/INTERVIEW_ENGINE.md",
    "docs/VOICE_CODING_WHITEBOARD.md": "docs/architecture/VOICE_CODING_WHITEBOARD.md",
    "docs/DEVELOPER_SETUP.md": "docs/engineering/DEVELOPER_SETUP.md",
    "docs/TEXT_PRACTICE_DEVELOPMENT.md": "docs/engineering/TEXT_PRACTICE_DEVELOPMENT.md",
    "docs/QUALITY_AND_TESTING.md": "docs/engineering/QUALITY_AND_TESTING.md",
    "docs/MODEL_AND_FINETUNING.md": "docs/engineering/MODEL_AND_FINETUNING.md",
    "docs/OPERATIONS_DEPLOYMENT.md": "docs/operations/OPERATIONS_DEPLOYMENT.md",
    "docs/SECURITY_AND_PRIVACY.md": "docs/governance/SECURITY_AND_PRIVACY.md",
    "docs/LICENSE_AUDIT.md": "docs/governance/LICENSE_AUDIT.md",
    "docs/REUSE_VS_BUILD.md": "docs/governance/REUSE_VS_BUILD.md",
    "docs/UPSTREAM_SOURCES.md": "docs/governance/UPSTREAM_SOURCES.md",
    "docs/CREDIT_OPTIMIZATION.md": "docs/governance/CREDIT_OPTIMIZATION.md",
    "docs/ROADMAP.md": "docs/delivery/ROADMAP.md",
    "docs/IMPLEMENTATION_CHECKLIST.md": "docs/delivery/IMPLEMENTATION_CHECKLIST.md",
    "docs/IMPLEMENTATION_STATUS.md": "docs/delivery/IMPLEMENTATION_STATUS.md",
    "docs/CODEX_BLOCKERS.md": "docs/delivery/CODEX_BLOCKERS.md",
    "docs/CODEX_KICKOFF.md": "docs/delivery/CODEX_KICKOFF.md",
    "docs/PROJECT_CONTEXT.md": "docs/delivery/PROJECT_CONTEXT.md",
}
PREFIX_MOVES = {
    "docs/decisions": "docs/architecture/decisions",
    "docs/audits": "docs/research/audits",
}
INVERSE = {new: old for old, new in MOVES.items()}
LINK = re.compile(r"(!?\[[^\]]*\]\()(<[^>]+>|[^) ]+)([^)]*\))")


def map_path(path: str) -> str:
    if path in MOVES:
        return MOVES[path]
    for old, new in PREFIX_MOVES.items():
        if path == old or path.startswith(old + "/"):
            return new + path[len(old) :]
    return path


def old_source(current: str) -> str:
    if current in INVERSE:
        return INVERSE[current]
    for old, new in PREFIX_MOVES.items():
        if current == new or current.startswith(new + "/"):
            return old + current[len(new) :]
    return current


def rewrite_target(target: str, before: str, after: str) -> str:
    angled = target.startswith("<") and target.endswith(">")
    raw = target[1:-1] if angled else target
    parts = urlsplit(raw)
    if parts.scheme or parts.netloc or not parts.path or raw.startswith("#"):
        return target
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(before), parts.path))
    if resolved.startswith("../"):
        return target
    destination = map_path(resolved)
    relative = posixpath.relpath(destination, posixpath.dirname(after) or ".")
    rewritten = urlunsplit(("", "", relative, parts.query, parts.fragment))
    return f"<{rewritten}>" if angled else rewritten


for file in ROOT.rglob("*.md"):
    current = file.relative_to(ROOT).as_posix()
    if current.startswith("AnalyseFuture/sources/"):
        continue
    before = old_source(current)
    text = file.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        return match.group(1) + rewrite_target(match.group(2), before, current) + match.group(3)

    updated = LINK.sub(replace, text)
    if updated != text:
        file.write_text(updated, encoding="utf-8")

# Rewrite explicit repository-relative path mentions not expressed as Markdown links.
for file in ROOT.rglob("*"):
    if not file.is_file() or file.suffix.lower() not in {".md", ".txt", ".yml", ".yaml", ".json"}:
        continue
    current = file.relative_to(ROOT).as_posix()
    if current.startswith(("AnalyseFuture/sources/", ".git/")):
        continue
    try:
        text = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    updated = text
    for old, new in MOVES.items():
        updated = updated.replace(old, new)
    for old, new in PREFIX_MOVES.items():
        updated = updated.replace(old + "/", new + "/")
    if updated != text:
        file.write_text(updated, encoding="utf-8")
