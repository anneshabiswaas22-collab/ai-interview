# Integrity and Complete-File Inventory

This directory makes the preservation boundary independently auditable.

- `SOURCE_MANIFEST.json` records archive provenance, licenses, trust/runtime flags, counts, sizes, tree digests, path-traversal results, symlink results, and adoption gates.
- `ARCHIVES.sha256` verifies the four original ZIP files.
- `EXTRACTED.sha256` verifies every one of the 1,705 extracted source files.
- `TRACKED_FILES.tsv` classifies every tracked or pending repository file by function, role, status, purpose, size, and digest.

The catalogs are generated without importing or executing archived code:

```bash
python3 scripts/build_repository_inventory.py
```

From the repository root, integrity can be checked with standard SHA-256 tooling:

```bash
sha256sum -c AnalyseFuture/inventory/ARCHIVES.sha256
sha256sum -c AnalyseFuture/inventory/EXTRACTED.sha256
```

`TRACKED_FILES.tsv` marks its own digest as `generated-on-demand` to avoid a recursive self-hash. All other listed files have concrete SHA-256 values.
