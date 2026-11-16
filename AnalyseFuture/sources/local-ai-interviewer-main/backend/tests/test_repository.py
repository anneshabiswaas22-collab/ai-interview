"""Repository consistency: docs links, configuration documentation, versions and CI hygiene. Fast, offline, deterministic."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_check_docs():
    spec = importlib.util.spec_from_file_location("check_docs", ROOT / "scripts" / "check_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_markdown_links_images_and_anchors_are_valid():
    problems = _load_check_docs().check()
    assert problems == [], "\n".join(problems)


def test_the_docs_checker_catches_broken_links_and_anchors(tmp_path, monkeypatch):
    cd = _load_check_docs()
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("# Title\n\n## Getting started\n\n[ok](docs/a.md) [bad](docs/missing.md) [anchor](#getting-started) "
                                        "[badanchor](#nope) ![img](docs/x.png) `[not a link](nowhere.md)`\n", encoding="utf-8")
    (tmp_path / "docs" / "a.md").write_text("# A\n```\n[in code](nowhere.md)\n```\n[back](../README.md#getting-started)\n", encoding="utf-8")
    monkeypatch.setattr(cd, "ROOT", tmp_path)
    problems = cd.check()
    assert len(problems) == 3, problems
    assert any("missing.md" in p for p in problems) and any("#nope" in p for p in problems) and any("x.png" in p for p in problems)


def test_the_docs_checker_has_no_blind_spots(tmp_path, monkeypatch):
    """Cases an earlier, line-based version missed (found by the independent audit). Each `bad*` target must be reported once."""
    cd = _load_check_docs()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.png").write_bytes(b"")
    (tmp_path / "docs" / "a (1).md").write_text("Title\n=====\n\nSub\n---\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "[![badge](docs/ok.png)](bad1.md)\n"                    # outer target of a nested badge link
        "[ref link][r] and [r2]\n\n[r]: bad2.md\n[r2]: <docs/ok.png>\n"   # reference-style definitions
        "<img\n  alt=\"x\"\n  src=\"bad3.png\">\n"              # multi-line HTML
        "[t](bad4.md 'single-quoted title') [t](<docs/a (1).md#title>) [t](docs/a%20(1).md#sub)\n"
        "![case](DOCS/ok.png)\n"                                 # wrong letter case
        "[setext](docs/a%20(1).md#nope)\n",                      # anchors of setext headings exist; this one does not
        encoding="utf-8")
    monkeypatch.setattr(cd, "ROOT", tmp_path)
    problems = cd.check()
    for needle in ("bad1.md", "bad2.md", "bad3.png", "bad4.md", "DOCS/ok.png", "#nope"):
        assert sum(needle in p for p in problems) == 1, (needle, problems)
    assert len(problems) == 6, problems


def test_github_heading_slugs():
    cd = _load_check_docs()
    assert cd.slug("5a. Resumes — interview questions about your own experience") == "5a-resumes--interview-questions-about-your-own-experience"
    assert cd.slug("`code` and *emphasis*") == "code-and-emphasis"


# Environment variables the code reads that are NOT user settings: set by the app itself, OS/tool conventions, or test-only switches.
NOT_SETTINGS = {"HF_HUB_OFFLINE", "LAI_NO_BROWSER", "LOCALAPPDATA", "NO_COLOR", "OLLAMA_MODELS"}
ENV_READ = re.compile(r"""(?:environ\.get\(|environ\[|_env\w*\(|getenv\(|env_value\()\s*["']([A-Z][A-Z0-9_]+)["']""")


def test_every_setting_is_documented_and_every_documented_setting_is_used():
    """Both directions, by actual reads in code (a mention in a comment does not count)."""
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    documented = set(re.findall(r"^#?\s?([A-Z][A-Z0-9_]+)=", example, re.M))
    sources = [*(ROOT / "backend" / "app").rglob("*.py"), ROOT / "scripts" / "manage.py"]
    read = set().union(*(ENV_READ.findall(p.read_text(encoding="utf-8")) for p in sources))
    assert read - NOT_SETTINGS - documented == set(), f"settings missing from .env.example: {sorted(read - NOT_SETTINGS - documented)}"
    assert documented - read == set(), f".env.example documents settings no code reads: {sorted(documented - read)}"


def test_backend_and_frontend_versions_match():
    from app import __version__
    pkg = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == __version__
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-.](?:dev|rc|a|b)\.?\d+)?", __version__)


def test_workflow_actions_are_pinned_to_commit_shas_and_permissions_are_explicit():
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows
    for wf in workflows:
        text = wf.read_text(encoding="utf-8")
        for ref in re.findall(r"uses:\s*([^\s#]+)", text):
            if ref.startswith("./"):
                continue
            assert re.search(r"@[0-9a-f]{40}$", ref), f"{wf.name}: {ref} is not pinned to a full commit SHA"
        assert re.search(r"^permissions:", text, re.M), f"{wf.name}: no top-level permissions block (least privilege)"


def test_no_secrets_or_personal_data_files_are_committed():
    import subprocess
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    if not files:          # not a git checkout (e.g. a source archive): nothing to check
        return
    bad = [f for f in files if re.search(r"(^|/)\.env$|\.sqlite3?$|\.pem$|\.key$|(^|/)data/|(^|/)logs/|id_rsa|(^|/)\.coverage|(^|/)htmlcov/|\.db$", f)]
    assert bad == []
    secret = re.compile(r"(sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
    for f in files:
        p = ROOT / f
        if p.suffix in {".png", ".jpg", ".ico", ".woff2", ".pdf"} or not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        assert not secret.search(p.read_text(encoding="utf-8", errors="ignore")), f"possible secret in {f}"


def test_tool_versions_are_pinned_once_and_agree():
    """ruff is pinned in requirements-dev.txt (CI installs from it) and must match the pre-commit hook revision."""
    dev = (ROOT / "backend" / "requirements-dev.txt").read_text(encoding="utf-8")
    ruff = re.search(r"^ruff==([\d.]+)", dev, re.M).group(1)
    hook = re.search(r"ruff-pre-commit\s+rev:\s*v([\d.]+)", (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    assert hook and hook.group(1) == ruff
    workflows = "".join(p.read_text(encoding="utf-8") for p in (ROOT / ".github" / "workflows").glob("*.yml"))
    assert not re.search(r"(ruff|pip-audit)==\d", workflows), "pin tool versions in requirements-dev.txt, not in workflows"
