"""Regression tests for evidence safety and coverage, using synthetic repositories."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest

import recovery_inventory as inventory


class RecoveryInventoryTests(unittest.TestCase):
    def test_preserved_code_is_only_a_recovery_candidate(self):
        status, _, reason = inventory.classify("AnalyseFuture/sources/example/app/score.py")
        self.assertEqual(status, "RECOVERABLE")
        self.assertIn("not yet established", reason)
        self.assertEqual(inventory.classify("AnalyseFuture/sources/example/tests/test_score.py")[0], "TEST")
        self.assertEqual(inventory.classify("AnalyseFuture/sources/example/LICENSE")[0], "LICENSE/PROVENANCE")

    def test_unassigned_data_is_retained_for_investigation(self):
        status, _, reason = inventory.classify("unknown-binary.exe")
        self.assertEqual(status, "SUSPICIOUS")
        self.assertIn("retain", reason)

    def test_normalize_prevents_import_escape(self):
        self.assertEqual(inventory.normalize(pathlib.PurePosixPath("apps/api"), "../types"), "apps/types")
        self.assertEqual(inventory.normalize(pathlib.PurePosixPath("."), "../../outside"), "")

    def test_relative_and_alias_imports_resolve_without_execution(self):
        files = {"app/src/shared.ts", "app/src/feature.tsx"}
        for spec in ("./shared", "./shared.js", "@/shared"):
            self.assertEqual(inventory.resolve_import("app/src/feature.tsx", spec, files, {}),
                             ("app/src/shared.ts", "local"))
        self.assertEqual(inventory.resolve_import("app/src/feature.tsx", "./missing", files, {})[1], "unresolved-local")

    def test_workspace_names_do_not_connect_archives_to_product(self):
        packages = {"active:@demo/types": "apps/packages/types", "archive:@demo/types": "AnalyseFuture/sources/archive/types"}
        result = inventory.resolve_import("AnalyseFuture/sources/archive/app/index.ts", "@demo/types", set(), packages)
        self.assertEqual(result[0], "AnalyseFuture/sources/archive/types/package.json")

    def test_full_scan_accounts_hidden_duplicates_and_ignored_without_running_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            (root / ".gitignore").write_text(".env\nnode_modules/\n")
            (root / ".hidden").write_bytes(b"shared data")
            (root / "copy").write_bytes(b"shared data")
            (root / ".env").write_text("DO_NOT_READ=private\n")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "untrusted.js").write_text("throw new Error('never execute');")
            (root / "malicious.py").write_text("raise RuntimeError('never execute')\nimport external_dependency\n")
            first = inventory.build(root)
            second = inventory.build(root)
            self.assertEqual(first, second)
            rows = {row["path"]: row for row in csv.DictReader(io.StringIO(first[inventory.OUTPUTS[0]]), delimiter="\t")}
            self.assertIn(".hidden", rows)
            self.assertNotIn(".env", rows)
            self.assertNotIn("node_modules/untrusted.js", rows)
            self.assertEqual(rows[".hidden"]["sha256"], hashlib.sha256(b"shared data").hexdigest())
            self.assertEqual(rows[".hidden"]["exact_byte_match"], "copy")
            self.assertIn("no retirement justified", rows["copy"]["evidence_and_disposition"])
            summary = json.loads(first[inventory.OUTPUTS[2]])
            self.assertEqual(summary["ignored"]["total_files"], 2)
            self.assertEqual(summary["total_accounted_files"], 7)
            self.assertIn("external_dependency", first[inventory.OUTPUTS[1]])
            for generated in inventory.OUTPUTS:
                self.assertEqual(rows[generated]["sha256"], "self-generated:excluded")

    def test_symlink_is_hashed_as_link_without_reading_external_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            link = root / "external"
            link.symlink_to("/definitely/not/readable/credential")
            self.assertEqual(inventory.safe_file(link, root), b"/definitely/not/readable/credential")

    def test_missing_tracked_file_fails_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            file = root / "lost.txt"
            file.write_text("must remain accounted")
            subprocess.run(["git", "add", "lost.txt"], cwd=root, check=True)
            file.unlink()
            with self.assertRaises(FileNotFoundError):
                inventory.build(root)

    def test_tsv_preserves_unusual_paths(self):
        path = "folder/newline\nfile\twith-tabs.ts"
        output = inventory.tsv(["path"], [{"path": path}])
        self.assertEqual(list(csv.DictReader(io.StringIO(output), delimiter="\t")), [{"path": path}])


if __name__ == "__main__":
    unittest.main()
