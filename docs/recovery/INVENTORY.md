# Recovery inventory and dependency evidence

This is an automated initial disposition, not a claim that every file has been
manually reviewed or that every preserved feature works. Nothing was removed or
relocated to produce this inventory. Existing `AnalyseFuture/inventory/` evidence
and all original archives and extracted sources remain untouched.

From the repository root:

```sh
python3 scripts/test_recovery_inventory.py
python3 scripts/recovery_inventory.py
python3 scripts/recovery_inventory.py --check
```

The generator is Python standard library only. It reads source as data; it never
imports preserved application modules, executes package scripts, extracts ZIPs,
downloads dependencies or modifies Git. Source additions/changes require a fresh
scan. `--check` exits nonzero when evidence is stale. Run it after tests/builds
finish because the ignored-artifact counts can change while those run.

- [FILE_DISPOSITION.tsv](FILE_DISPOSITION.tsv): every tracked and nonignored
  untracked file (including hidden files), its SHA-256, size, owner, initial
  status, responsibility and retention rationale. Exact-byte matches are
  recorded separately from status: identical bytes alone do not establish
  functional redundancy or justify retirement.
- [DEPENDENCY_GRAPH.tsv](DEPENDENCY_GRAPH.tsv): static JS/TS literal imports and
  Python AST import declarations, with local resolution when possible. Workspace
  package references resolve within their own source tree; archived copies are
  not linked to the active app merely because package names match. `owner` groups
  edges by application/package or preserved source for ownership review.
- [INVENTORY_SUMMARY.json](INVENTORY_SUMMARY.json): file/status/owner totals,
  duplicate counts, dependency resolution counts and ignored-artifact counts.

`ACTIVE` indicates application placement and possible static use, not proof that
a route is reachable. `RECOVERABLE` indicates a preserved implementation candidate
to compare, not recovered working behavior. `SUSPICIOUS` means unassigned or a
symbolic link needing review; it is not an accusation of maliciousness. No file
is labelled `UNNECESSARY` or assigned a deletion decision by this scanner.
`TEST`, `CONFIGURATION`, `DOCUMENTATION` and `LICENSE/PROVENANCE` retain their
respective responsibilities even when identical copies exist. Archived tests
being catalogued does not mean their dependencies were trusted or tests executed.

Only the three generated evidence outputs omit their own SHA-256/size: embedding
their final hashes in themselves has no stable solution. Every other listed file
is hashed as bytes. Symbolic links are hashed as link text without following the
target, and require review. Missing tracked files or inaccessible file reads fail
the scan rather than silently dropping evidence. Generated output is deterministic
for the same source and ignored-path set; it contains no clock-dependent values.

Ignored dependency/build/runtime files are counted by pathname only. Their content
is not reviewed or hashed, and local environment-file contents are not read. Git
object storage, Docker image layers/volumes and paths outside this checkout are not
application source inventory. The baseline Git bundle and working-tree backup
are recorded separately in the recovery report.

The import graph is a navigation aid: regex matching can include commented JS/TS
imports, while computed imports, framework routing, runtime plugins, SQL joins,
Terraform references and network calls need targeted review. Python AST resolution
does not model runtime `sys.path`. Unresolved or external edges remain visible;
absence of an edge does not prove that a file is unused. Source-code execution
tests and manual feature/source audits supply the behavioral evidence separately.
