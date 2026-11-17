#!/usr/bin/env python3
"""Build reproducible repository and preserved-source inventories.

This script reads files as data. It never imports or executes preserved source code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FUTURE = ROOT / "AnalyseFuture"
INVENTORY = FUTURE / "inventory"
TRACKED_INVENTORY = INVENTORY / "TRACKED_FILES.tsv"

SOURCES = [
    {
        "id": "deepinterview",
        "name": "DeepInterview",
        "archive": "DeepInterview-main.zip",
        "source": "DeepInterview-main",
        "upstream": "ngoanpv/DeepInterview",
        "ref": "unknown from ZIP; verify before adoption",
        "license": "Apache-2.0",
        "license_paths": ["LICENSE", "NOTICE"],
    },
    {
        "id": "euron-upstream",
        "name": "Euron Open Conversation upstream snapshot",
        "archive": "euron-open-real-time-ai-conversation-system-main.zip",
        "source": "euron-open-real-time-ai-conversation-system-main",
        "upstream": "euron-sde-team/euron-open-real-time-ai-conversation-system",
        "ref": "216a8fc52a055587f436f2446f1a80b6868bd14a",
        "license": "MIT",
        "license_paths": ["LICENSE"],
    },
    {
        "id": "grillkit",
        "name": "GrillKit",
        "archive": "grillkit-main.zip",
        "source": "grillkit-main",
        "upstream": "unknown from ZIP; verify before adoption",
        "ref": "unknown from ZIP; verify before adoption",
        "license": "Apache-2.0",
        "license_paths": ["LICENSE", "NOTICE"],
    },
    {
        "id": "local-ai-interviewer",
        "name": "Local AI Interviewer",
        "archive": "local-ai-interviewer-main.zip",
        "source": "local-ai-interviewer-main",
        "upstream": "unknown from ZIP; verify before adoption",
        "ref": "unknown from ZIP; verify before adoption",
        "license": "MIT",
        "license_paths": ["LICENSE"],
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(files: list[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(base).as_posix()):
        relative = path.relative_to(base).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def detail_for_research(parts: tuple[str, ...], name: str) -> tuple[str, str]:
    lowered = {part.lower() for part in parts}
    if name.lower() in {"license", "notice", "copying"}:
        return "third-party-license", "Preserved upstream license or attribution evidence"
    if "test" in lowered or "tests" in lowered or ".test." in name or ".spec." in name:
        return "preserved-test", "Untrusted upstream test evidence; excluded from active test discovery"
    if "docs" in lowered or name.lower().startswith("readme"):
        return "preserved-documentation", "Untrusted upstream documentation retained for research"
    if "src" in lowered or "app" in lowered or "apps" in lowered:
        return "preserved-source", "Untrusted upstream implementation retained for selective analysis"
    if name.endswith(("lock", "lock.yaml", "lock.json")) or "lock" in name.lower():
        return "preserved-lockfile", "Upstream dependency-resolution evidence; not an active workspace lock"
    return "preserved-artifact", "Untrusted upstream artifact retained byte-for-byte from the archive"


def classify(path_text: str) -> tuple[str, str, str, str]:
    path = PurePosixPath(path_text)
    parts = path.parts
    name = path.name

    if path_text.startswith("AnalyseFuture/sources/"):
        kind, purpose = detail_for_research(parts, name)
        return "research/preserved-source", kind, "preserved-non-runtime", purpose
    if path_text.startswith("AnalyseFuture/archives/"):
        return "research/archive", "source-archive", "preserved-non-runtime", "Original immutable input archive corresponding to one extracted research tree"
    if path_text.startswith("AnalyseFuture/inventory/"):
        return "research/inventory", "generated-integrity-metadata", "governance", "Machine-readable integrity, provenance, and complete file-catalog evidence"
    if path_text.startswith("AnalyseFuture/migrations/"):
        return "research/migration-record", "migration-tool", "historical-tooling", "Auditable one-time repository reorganization helper"
    if path_text.startswith("AnalyseFuture/"):
        return "research/governance", "research-documentation", "governance", "Defines research boundaries, source findings, or long-horizon product ideas"

    if path_text.startswith("apps/interview-platform/apps/web/test/"):
        return "application/web", "web-unit-test", "test-only", "Verifies candidate/admin web behavior and shared UI integration"
    if path_text.startswith("apps/interview-platform/apps/web/src/app/"):
        return "application/web", "web-route", "active-runtime", "Next.js route, layout, page, or request boundary for the candidate/admin experience"
    if path_text.startswith("apps/interview-platform/apps/web/src/components/"):
        return "application/web", "web-component", "active-runtime", "Candidate/admin presentation component consuming web libraries and shared UI/contracts"
    if path_text.startswith("apps/interview-platform/apps/web/src/lib/"):
        return "application/web", "web-library", "active-runtime", "Browser/server web helper connecting routes and components to API, session, or realtime contracts"
    if path_text.startswith("apps/interview-platform/apps/web/"):
        return "application/web", "web-config-or-asset", "active-support", "Web application configuration, asset, design note, or build helper"

    if path_text.startswith("apps/interview-platform/apps/api/test/integration/"):
        return "application/api", "api-integration-test", "test-only", "Exercises authenticated API behavior with isolated PostgreSQL and Redis"
    if path_text.startswith("apps/interview-platform/apps/api/test/"):
        return "application/api", "api-unit-test", "test-only", "Verifies API domain, security, adapter, and service behavior"
    api_roles = {
        "controllers": ("api-controller", "Translates authenticated HTTP requests into service operations"),
        "routes": ("api-route", "Declares API endpoints, middleware, and controller wiring"),
        "services": ("api-service", "Owns application use cases and authoritative business behavior"),
        "repositories": ("api-repository", "Owns persistent data access and transaction boundaries"),
        "integrations": ("api-integration", "Adapts external model, mail, realtime, Redis, or document services"),
        "jobs": ("api-background-job", "Declares durable queue work, retries, maintenance, or dispatch recovery"),
        "middleware": ("api-middleware", "Enforces authentication, validation, limits, and HTTP policy"),
        "security": ("api-security", "Implements password, session-token, TOTP, or cryptographic controls"),
        "presenters": ("api-presenter", "Maps internal data to public response contracts"),
        "core": ("api-core", "Provides configuration, context, logging, validation, identifiers, and effects"),
        "db": ("api-database-binding", "Binds generated database types and connection configuration"),
        "domain": ("api-domain-rule", "Defines dependency-light domain validation and value rules"),
        "demo": ("api-demo-data", "Creates explicitly simulated local development data"),
    }
    if path_text.startswith("apps/interview-platform/apps/api/src/"):
        section = parts[5] if len(parts) > 5 else "entrypoint"
        kind, purpose = api_roles.get(section, ("api-entrypoint", "Starts or coordinates the API, worker, or CLI process"))
        return "application/api", kind, "active-runtime", purpose
    if path_text.startswith("apps/interview-platform/apps/api/"):
        return "application/api", "api-config", "active-support", "API package manifest, compiler configuration, or code-generation helper"

    if path_text.startswith("apps/interview-platform/apps/stubs/"):
        status = "test-only" if "/test/" in path_text else "development-runtime"
        return "application/provider-stubs", "provider-stub", status, "Deterministic simulated provider used for offline development and verification"
    if path_text.startswith("apps/interview-platform/packages/"):
        package = parts[3] if len(parts) > 3 else "shared"
        return f"application/shared-package/{package}", "shared-library", "active-runtime", "Versioned in-workspace contract, API client, or UI primitive consumed by platform applications"
    if path_text.startswith("apps/interview-platform/db/migrations/"):
        return "application/database", "database-migration", "active-runtime", "Ordered PostgreSQL schema evolution consumed by migration and API processes"
    if path_text == "apps/interview-platform/db/migrate.ts":
        return "application/database", "migration-runner", "active-runtime", "Applies ordered PostgreSQL migrations"
    if path_text.startswith("apps/interview-platform/e2e/"):
        return "application/end-to-end", "browser-test-or-fixture", "test-only", "Exercises complete offline candidate and administration flows"
    if path_text.startswith("apps/interview-platform/deploy/"):
        return "application/deployment", "compose-config", "active-operations", "Defines local or AWS-connected service composition and safe example variables"
    if path_text.startswith("apps/interview-platform/infra/docker/"):
        return "application/infrastructure", "container-build", "active-operations", "Builds deployable platform images from the application workspace"
    if path_text.startswith("apps/interview-platform/infra/terraform/"):
        return "application/infrastructure", "terraform", "active-operations", "Defines reusable cloud modules and environment composition"
    if path_text.startswith("apps/interview-platform/scripts/"):
        return "application/tooling", "application-script", "active-tooling", "Supports local setup, sanitization, AWS deployment, or one-off operational tasks"
    if path_text.startswith("apps/interview-platform/docs/"):
        return "application/reference", "generated-api-reference", "active-documentation", "Application-owned generated API contract"
    if path_text.startswith("apps/interview-platform/third-party/") or name in {"LICENSE", "SECURITY.md"} and path_text.startswith("apps/interview-platform/"):
        return "application/legal", "license-or-security", "governance", "Application license, third-party attribution, model evidence, or security policy"
    if path_text.startswith("apps/interview-platform/"):
        kind = "workspace-lockfile" if "lock" in name else "workspace-config"
        return "application/workspace", kind, "active-support", "Self-contained pnpm/Turbo application workspace configuration or developer entrypoint"

    if path_text.startswith("packages/interview-core/test/"):
        return "experiment/interview-core", "experimental-unit-test", "test-only", "Verifies the standalone server-owned policy and evidence-validation experiment"
    if path_text.startswith("packages/interview-core/src/"):
        return "experiment/interview-core", "experimental-library", "experimental", "Dependency-free interview policy or evidence-validation implementation"
    if path_text.startswith("packages/interview-core/"):
        return "experiment/interview-core", "experimental-package-metadata", "experimental", "Declares and documents the standalone interview-core experiment"

    if path_text.startswith("docs/"):
        area = parts[1] if len(parts) > 1 else "index"
        kind = "architecture-decision" if "decisions" in parts else "audit" if "audits" in parts else f"{area}-documentation"
        return f"documentation/{area}", kind, "source-of-truth", f"Maintained {area} knowledge linked through docs/README.md"
    if path_text.startswith("scripts/"):
        return "repository/tooling", "repository-script", "active-tooling", "Repository-wide validation, inventory, or maintenance automation"
    if path_text.startswith(".github/workflows/"):
        return "repository/automation", "ci-workflow", "active-automation", "Runs path-scoped repository validation in GitHub Actions"
    if path_text.startswith(".github/ISSUE_TEMPLATE/"):
        return "repository/collaboration", "issue-template", "governance", "Structures audit or feature requests"
    if path_text.startswith(".github/"):
        return "repository/collaboration", "collaboration-template", "governance", "Defines contribution or pull-request expectations"

    root_roles = {
        "README.md": ("project-entrypoint", "Public project status, navigation, and truthful capability summary"),
        "AGENTS.md": ("agent-policy", "Mandatory operating and safety policy for coding agents"),
        "CONTRIBUTING.md": ("contributor-policy", "Contribution, review, security disclosure, and quality workflow"),
        "THIRD_PARTY_NOTICES.md": ("legal-notices", "Release-critical third-party attribution and redistribution evidence"),
        "REFERENCE_REPOSITORIES.txt": ("research-index", "Dated external repository, model, license, and benchmark inventory"),
        "PROJECT_STRUCTURE.md": ("structure-contract", "Canonical repository layout, ownership, and file-placement policy"),
        ".gitignore": ("ignore-policy", "Prevents secrets, candidate data, dependencies, and generated output from entering Git"),
        ".gitattributes": ("repository-attributes", "Marks preserved sources and archives for correct Git/GitHub handling"),
    }
    if path_text in root_roles:
        kind, purpose = root_roles[path_text]
        return "repository/root", kind, "governance", purpose
    return "repository/uncategorized", "review-required", "unknown", "File requires explicit ownership review"


def tracked_and_pending_files() -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    )
    return sorted({line for line in output.splitlines() if line and (ROOT / line).is_file()})


def build_source_integrity() -> None:
    INVENTORY.mkdir(parents=True, exist_ok=True)
    archive_lines: list[str] = []
    extracted_lines: list[str] = []
    manifests: list[dict[str, object]] = []

    all_extracted = sorted(path for path in (FUTURE / "sources").rglob("*") if path.is_file())
    for file in all_extracted:
        extracted_lines.append(f"{sha256(file)}  {file.relative_to(ROOT).as_posix()}")

    for source in SOURCES:
        archive = FUTURE / "archives" / source["archive"]
        extraction = FUTURE / "sources" / source["source"]
        files = sorted(path for path in extraction.rglob("*") if path.is_file())
        archive_hash = sha256(archive)
        archive_lines.append(f"{archive_hash}  {archive.relative_to(ROOT).as_posix()}")
        unsafe: list[str] = []
        symlinks: list[str] = []
        with zipfile.ZipFile(archive) as bundle:
            entries = [entry for entry in bundle.infolist() if not entry.is_dir()]
            for entry in entries:
                path = PurePosixPath(entry.filename)
                if path.is_absolute() or ".." in path.parts:
                    unsafe.append(entry.filename)
                mode = (entry.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    symlinks.append(entry.filename)
        manifests.append(
            {
                "id": source["id"],
                "name": source["name"],
                "status": "preserved-research-only",
                "trust": "untrusted",
                "executable": False,
                "runtime_dependency": False,
                "workspace_member": False,
                "ci_build": False,
                "archive_path": archive.relative_to(ROOT).as_posix(),
                "archive_sha256": archive_hash,
                "archive_bytes": archive.stat().st_size,
                "zip_file_entries": len(entries),
                "extraction_path": extraction.relative_to(ROOT).as_posix(),
                "extracted_files": len(files),
                "extracted_bytes": sum(file.stat().st_size for file in files),
                "extracted_tree_sha256": tree_digest(files, extraction),
                "path_traversal_entries": unsafe,
                "symlink_entries": symlinks,
                "upstream": source["upstream"],
                "ref": source["ref"],
                "license": source["license"],
                "license_paths": [f"{extraction.relative_to(ROOT).as_posix()}/{item}" for item in source["license_paths"]],
                "review_method": "static archive and source inspection; code not executed",
                "reviewed_on": "2026-11-17",
                "adoption_gate": "ADR, exact provenance, license/security/privacy review, scoped integration tests, rollback, and maintenance owner",
            }
        )

    (INVENTORY / "ARCHIVES.sha256").write_text("\n".join(archive_lines) + "\n", encoding="utf-8")
    (INVENTORY / "EXTRACTED.sha256").write_text("\n".join(extracted_lines) + "\n", encoding="utf-8")
    (INVENTORY / "SOURCE_MANIFEST.json").write_text(
        json.dumps({"schema_version": 1, "generated_on": "2026-11-17", "sources": manifests}, indent=2) + "\n",
        encoding="utf-8",
    )


def build_tracked_inventory() -> None:
    INVENTORY.mkdir(parents=True, exist_ok=True)
    rows: list[list[object]] = []
    for path_text in tracked_and_pending_files():
        path = ROOT / path_text
        category, kind, status, purpose = classify(path_text)
        digest = "generated-on-demand" if path == TRACKED_INVENTORY else sha256(path)
        rows.append([path_text, path.stat().st_size, digest, category, kind, status, purpose])
    with TRACKED_INVENTORY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256", "functional_category", "content_role", "runtime_status", "purpose_and_relationship"])
        writer.writerows(rows)


if __name__ == "__main__":
    build_source_integrity()
    # Run twice so the generated files themselves appear in the complete catalog.
    build_tracked_inventory()
    build_tracked_inventory()
