#!/usr/bin/env python3
"""Inventory repository data without importing/executing application or archive code.

No network, archive extraction, dependency installation, deletion, or Git mutation.
Use --check to compare the checked-in evidence with a fresh deterministic scan.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (
    "docs/recovery/FILE_DISPOSITION.tsv",
    "docs/recovery/DEPENDENCY_GRAPH.tsv",
    "docs/recovery/INVENTORY_SUMMARY.json",
)
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}
JS_IMPORT = re.compile(
    r"\b(?:import|export)\s+(?:[^;\n]*?\s+from\s*)?[\"']([^\"']+)[\"']"
    r"|\b(?:import|require)\s*\(\s*[\"']([^\"']+)[\"']\s*\)"
)


def git_paths(*args: str, root: Path = ROOT) -> list[str]:
    """NUL boundaries preserve spaces/newlines in filenames; failures fail the scan."""
    result = subprocess.check_output(["git", "ls-files", "-z", *args], cwd=root)
    return sorted(set(os.fsdecode(part) for part in result.split(b"\0") if part))


def owner(path: str) -> str:
    parts = PurePosixPath(path).parts
    if path.startswith("AnalyseFuture/sources/"):
        return "preserved/" + parts[2]
    if path.startswith("apps/interview-platform/"):
        if len(parts) > 3 and parts[2] in {"apps", "packages"}:
            return "/".join(parts[2:4])
        return "platform/" + (parts[2] if len(parts) > 3 else "workspace")
    if path.startswith("packages/interview-core/"):
        return "experimental/interview-core"
    return parts[0] if len(parts) > 1 else "repository"


def classify(path: str) -> tuple[str, str, str]:
    """Conservative initial disposition, not a security or usefulness verdict."""
    p = PurePosixPath(path)
    parts, name = p.parts, p.name.lower()
    legal = name in {"license", "license.md", "license.txt", "notice", "notice.md", "copying"}
    if legal or name == "third_party_notices.md" or "/third-party/" in path:
        return "LICENSE/PROVENANCE", "license, attribution or upstream asset provenance", "retain; legal obligations require review before reuse"
    if path in OUTPUTS:
        return "GENERATED", "reproducible recovery inventory evidence", "retain; regenerate with scripts/recovery_inventory.py; self hash/size excluded"
    if path.startswith("AnalyseFuture/archives/"):
        return "LICENSE/PROVENANCE", "original recovery source archive", "retain byte-for-byte; never treat archive presence as working functionality"
    if path.startswith("AnalyseFuture/inventory/"):
        return "LICENSE/PROVENANCE", "existing archive integrity and provenance evidence", "retain baseline evidence; this scan does not rewrite it"
    is_test = any(part.lower() in {"test", "tests", "e2e", "__tests__"} for part in parts)
    is_test = is_test or bool(re.search(r"(?:\.test\.|\.spec\.|^test_|_test\.)", name))
    if is_test:
        return "TEST", "test, fixture or test-runner support", "retain; preserved-source tests are not implied to have run"
    if name.endswith((".md", ".txt", ".rst")) or "docs" in parts:
        return "DOCUMENTATION", "requirements, architecture, operation or source documentation", "retain; unique content and claims need human review before consolidation"
    config = (
        name.startswith((".env", ".git", ".docker", ".editor", ".prettier", ".nvm"))
        or "lock" in name or "config" in name or name in {"package.json", "pyproject.toml", "makefile", "dockerfile", "tsconfig.json"}
        or p.suffix in {".yaml", ".yml", ".toml", ".ini", ".tf"}
        or "requirements" in name or path.startswith(".github/")
    )
    if config:
        return "CONFIGURATION", "build, dependency, development, automation or infrastructure configuration", "retain; inspect scripts and dependency trust before execution"
    if path.startswith("AnalyseFuture/sources/"):
        return "RECOVERABLE", "preserved implementation or asset candidate for feature comparison", "retain; candidate only, integration/security/license fitness not yet established"
    if path.startswith("AnalyseFuture/"):
        return "FUTURE", "preserved recovery/research material and migration helper", "retain; no current-runtime dependency inferred"
    if path.startswith("packages/interview-core/"):
        return "RECOVERABLE", "standalone policy/evidence experiment", "retain; not wired into the application unless dependency graph proves otherwise"
    if path.startswith("scripts/"):
        return "CONFIGURATION", "repository validation or recovery tooling", "retain; explicit invocation needed; not product runtime"
    if path.startswith("apps/interview-platform/"):
        if "/src/" in path or "/db/" in path or "/apps/stubs/" in path:
            return "ACTIVE", "primary application source, schema, or offline provider", "retain; placement/import analysis is not proof of runtime reachability or tested behavior"
        return "CONFIGURATION", "primary application asset, operational helper or workspace support", "retain; verify direct callers before relocating"
    return "SUSPICIOUS", "unassigned repository artifact requiring review", "retain and investigate; unassigned does not establish maliciousness"


def safe_file(path: Path, root: Path) -> bytes:
    """Never follow repository symlinks into credentials or outside the checkout."""
    if path.is_symlink():
        return os.fsencode(os.readlink(path))
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {path.relative_to(root)}")
    return path.read_bytes()


def tsv(headers: list[str], rows: list[dict[str, object]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=headers, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def package_exports(paths: list[str], root: Path) -> dict[str, str]:
    exports = {}
    for path in paths:
        if PurePosixPath(path).name != "package.json" or (root / path).is_symlink():
            continue
        try:
            data = json.loads(safe_file(root / path, root))
        except (ValueError, UnicodeDecodeError):
            continue
        name = data.get("name")
        if isinstance(name, str):
            # Scope by workspace to avoid connecting preserved copies to active code.
            scope = path.split("/sources/")[1].split("/")[0] if "/sources/" in path else "active"
            exports[f"{scope}:{name}"] = str(PurePosixPath(path).parent)
    return exports


def normalize(base: PurePosixPath, specifier: str) -> str:
    parts: list[str] = []
    for part in (base / specifier).parts:
        if part == "..":
            if not parts:
                return ""
            parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def resolve_import(source: str, spec: str, files: set[str], packages: dict[str, str]) -> tuple[str, str]:
    if spec.startswith("."):
        base = normalize(PurePosixPath(source).parent, spec)
    elif spec.startswith("@/") and "/src/" in source:
        base = source.split("/src/")[0] + "/src/" + spec[2:]
    else:
        scope = source.split("/sources/")[1].split("/")[0] if "/sources/" in source else "active"
        matched = next((name for name in sorted(packages, key=len, reverse=True)
                        if name.startswith(scope + ":") and (spec == name.split(":", 1)[1]
                        or spec.startswith(name.split(":", 1)[1] + "/"))), None)
        if matched:
            return packages[matched] + "/package.json", "workspace-package"
        return "", "external-or-alias"
    candidates = [base, *(base + ext for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json")),
                  *(base + "/index" + ext for ext in (".ts", ".tsx", ".js", ".mjs"))]
    # TS sources often use .js specifiers for the emitted ESM path.
    if base.endswith(".js"):
        candidates.extend([base[:-3] + ".ts", base[:-3] + ".tsx"])
    target = next((candidate for candidate in candidates if candidate in files), "")
    return target, "local" if target else "unresolved-local"


def import_edges(paths: list[str], root: Path) -> list[dict[str, str]]:
    files, packages = set(paths), package_exports(paths, root)
    edges = []
    for path in paths:
        p = root / path
        if p.suffix not in CODE_SUFFIXES or p.is_symlink():
            continue
        try:
            content = safe_file(p, root).decode("utf-8")
        except UnicodeDecodeError:
            continue
        specs: set[str] = set()
        if p.suffix == ".py":
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    specs.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    specs.add("." * node.level + (node.module or ""))
        else:
            specs.update(a or b for a, b in JS_IMPORT.findall(content))
        for spec in sorted(specs):
            if p.suffix == ".py":
                # Resolve by candidate path; no importlib/module execution.
                if spec.startswith("."):
                    levels = len(spec) - len(spec.lstrip("."))
                    base = PurePosixPath(path).parent
                    for _ in range(levels - 1):
                        base = base.parent
                    module = (base / spec.lstrip(".").replace(".", "/")).as_posix()
                    options = [module + ".py", module + "/__init__.py"]
                else:
                    options = []
                    for parent in PurePosixPath(path).parents:
                        module = (parent / spec.replace(".", "/")).as_posix()
                        options.extend([module + ".py", module + "/__init__.py"])
                target = next((option for option in options if option in files), "")
                resolution = "local" if target else "external-or-unresolved-python"
            else:
                target, resolution = resolve_import(path, spec, files, packages)
            edges.append({"source": path, "specifier": spec, "target": target,
                          "resolution": resolution, "owner": owner(path)})
    return edges


def ignored_summary(paths: list[str]) -> dict[str, object]:
    areas: Counter[str] = Counter()
    for path in paths:
        parts = PurePosixPath(path).parts
        marker = next((part for part in parts if part in {
            "node_modules", ".next", ".turbo", "dist", "coverage", ".terraform", ".results", ".report"
        }), None)
        if marker:
            areas[marker] += 1
        elif PurePosixPath(path).name.startswith(".env"):
            areas["local environment configuration (contents not read)"] += 1
        else:
            areas["other ignored runtime/build/tool artifacts (contents not read)"] += 1
    return {"total_files": len(paths), "files_by_area": dict(sorted(areas.items())),
            "scope": "Git-ignored untracked paths counted by name only; no contents or secret values read"}


def build(root: Path = ROOT) -> dict[str, str]:
    paths = sorted(set(git_paths("--cached", "--others", "--exclude-standard", root=root)) | set(OUTPUTS))
    ignored = git_paths("--others", "--ignored", "--exclude-standard", root=root)
    hashes: dict[str, str] = {}
    contents: dict[str, bytes] = {}
    for path in paths:
        if path in OUTPUTS:
            continue
        data = safe_file(root / path, root)
        contents[path] = data
        hashes[path] = hashlib.sha256(data).hexdigest()
    groups: dict[str, list[str]] = defaultdict(list)
    for path, digest in hashes.items():
        groups[digest].append(path)
    rows = []
    for path in paths:
        status, responsibility, reason = classify(path)
        if (root / path).is_symlink():
            status, responsibility, reason = "SUSPICIOUS", "repository symbolic link", "retain; link target bytes hashed without following link; manual target review required"
        duplicate_of = ""
        if path in hashes and len(groups[hashes[path]]) > 1:
            duplicate_of = next(other for other in groups[hashes[path]] if other != path)
            reason += "; exact-byte match only, no retirement justified"
        rows.append({"path": path, "status": status, "owner": owner(path),
                     "responsibility": responsibility, "sha256": hashes.get(path, "self-generated:excluded"),
                     "bytes": len(contents[path]) if path in contents else "self-generated:excluded",
                     "exact_byte_match": duplicate_of, "evidence_and_disposition": reason,
                     "review_method": "automated path/content metadata; not individual manual review"})
    edges = import_edges([p for p in paths if p not in OUTPUTS], root)
    summary = {
        "schema_version": 1,
        "scope": "All git tracked plus nonignored untracked files, including hidden paths and recovery outputs",
        "total_accounted_files": len(rows),
        "directories_with_accounted_files": len({parent.as_posix() for path in paths
                                                   for parent in PurePosixPath(path).parents
                                                   if parent.as_posix() != "."}),
        "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "owner_counts": dict(sorted(Counter(row["owner"] for row in rows).items())),
        "exact_byte_duplicate_groups": sum(len(group) > 1 for group in groups.values()),
        "files_with_an_exact_byte_match": sum(len(group) for group in groups.values() if len(group) > 1),
        "dependency_edges": len(edges),
        "dependency_resolution_counts": dict(sorted(Counter(edge["resolution"] for edge in edges).items())),
        "ignored": ignored_summary(ignored),
        "self_reference_exclusions": list(OUTPUTS),
        "limitations": [
            "Automated classification is provisional, not a manual file-by-file review, reachability proof or security clearance.",
            "RECOVERABLE means candidate preserved material, not recovered working behavior. No files are classified UNNECESSARY solely by extension or age.",
            "Exact-byte matches do not establish functional redundancy, trust or permission to remove a copy.",
            "Static JS/TS import regex can include comments and miss computed imports; Python AST does not resolve runtime sys.path or plugin discovery.",
            "Generated evidence outputs are accounted but omit self-referential content hash and size. All other inventory files are hashed as bytes.",
            "Ignored dependency/build/runtime files are counted without reading contents; Git object database and external Docker volumes are outside source inventory scope.",
        ],
    }
    return {
        OUTPUTS[0]: tsv(list(rows[0]), rows),
        OUTPUTS[1]: tsv(["source", "specifier", "target", "resolution", "owner"], edges),
        OUTPUTS[2]: json.dumps(summary, indent=2, sort_keys=True) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = build()
    stale = []
    for path, content in generated.items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_text() != content:
                stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    if stale:
        print("Recovery inventory needs regeneration:", ", ".join(stale))
        return 1
    print("Recovery inventory", "current" if args.check else "generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
