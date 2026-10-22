"""Tests for aidlc_memory.py. Git edge cases stay inside temporary repositories."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aidlc_memory as mem  # noqa: E402

RULES = Path(__file__).resolve().parents[2]
TEMPLATE = RULES / "aws-aidlc-rule-details" / "templates" / "codekb-entry.md"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} failed: {proc.stderr}")
    return proc


def init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init")
    git(repo, "config", "user.email", "memory-test@example.com")
    git(repo, "config", "user.name", "Memory Test")


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def write_sources(repo: Path, names: list[str], text: str | None = None) -> None:
    for name in names:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((text if text is not None else f"content {name}\n").encode("utf-8"))


def enable(repo: Path) -> None:
    marker = repo / "aidlc-docs" / "knowledge" / ".aidlc-memory"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"enabled": true, "protocol_version": "1"}\n', encoding="utf-8")


def write_entry(repo: Path, sources: list[str], aggregate: bool = False, name: str = "sample.md") -> Path:
    lines = [
        "---",
        "type: CodeKB Entry",
        "title: Sample",
        f"aggregate: {'true' if aggregate else 'false'}",
        "covers: []",
        "sources:",
    ]
    for src in sources:
        stem = Path(src).stem
        lines.extend([
            f"  - id: {stem}",
            f"    resource: {src}",
            f"    path: {src}",
            f"    sha256: {'0' * 64}",
        ])
    lines.extend(["---", "", "# Sample", "", "Body stays.", ""])
    dest = repo / "aidlc-docs" / "knowledge" / "code" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def write_handoff(repo: Path, number: int, mode: str, human: bool = True) -> None:
    actor = "human:tester" if human else "agent:aidlc-memory"
    text = (
        "---\n"
        "type: Handoff\n"
        f"title: Cycle {number:02d}\n"
        f"re_mode: {mode}\n"
        "verified:\n"
        f"  - by: \"{actor}\"\n"
        "    at: \"2026-10-22T00:00:00Z\"\n"
        "---\n\n"
        f"# Cycle {number:02d} Handoff\n\n"
        "## Escopo\n\ndone\n\n## Changes\n\nnone\n\n## Stale\n\nnone\n\n"
        "## Dívidas\n\nnone\n\n## Pendências\n\nnone\n\n## Commit\n\npending\n"
    )
    path = repo / "aidlc-docs" / "knowledge" / "handoff" / f"cycle-{number:02d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seal_audit(repo: Path) -> None:
    log = git(repo, "log", "--format=%H")
    audit = repo / "aidlc-docs" / "audit.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(log.stdout, encoding="utf-8")


def setup_stamped(repo: Path, files: list[str], aggregate: bool = False, handoffs: int = 1, mode: str = "full") -> Path:
    init_repo(repo)
    enable(repo)
    write_sources(repo, files)
    commit_all(repo, "sources")
    entry = write_entry(repo, files, aggregate=aggregate)
    assert mem.main(["--workspace", str(repo), "stamp", str(entry)]) == 0
    for number in range(1, handoffs + 1):
        write_handoff(repo, number, mode)
    commit_all(repo, "memory")
    seal_audit(repo)
    return entry


def run_check(repo: Path, *extra: str) -> tuple[int, dict]:
    code = mem.main(["--workspace", str(repo), "check", "--json", *extra])
    report = json.loads((repo / "aidlc-docs" / "knowledge" / "code" / ".stale.json").read_text(encoding="utf-8"))
    return code, report


def test_template_frontmatter_parses():
    text = TEMPLATE.read_text(encoding="utf-8")
    frontmatter, body = mem.split_frontmatter(text)
    assert frontmatter is not None
    meta = mem.parse_yaml_subset(frontmatter)
    assert meta["type"] == "CodeKB Entry"
    assert meta["sources"][0]["path"]
    assert "## Summary" in body


def test_frontmatter_roundtrip_quotes_actors():
    meta = {
        "type": "Handoff",
        "re_mode": "delta",
        "verified": [{"by": "human:tester", "at": "2026-10-22T00:00:00Z"}],
        "sources": [{"id": "a", "resource": "src/a.py", "path": "src/a.py", "sha256": "ab" * 32}],
    }
    parsed = mem.parse_yaml_subset(mem.dump_frontmatter(meta).split("---", 2)[1])
    assert parsed["verified"][0]["by"] == "human:tester"
    assert parsed["sources"][0]["sha256"] == "ab" * 32
    assert parsed["re_mode"] == "delta"


def test_disabled_without_marker(tmp_path: Path):
    code = mem.main(["--workspace", str(tmp_path), "check", "--json"])
    assert code == 0
    assert not (tmp_path / "aidlc-docs" / "knowledge" / "code" / ".stale.json").exists()


def test_marker_enabled_false(tmp_path: Path):
    marker = tmp_path / "aidlc-docs" / "knowledge" / ".aidlc-memory"
    marker.parent.mkdir(parents=True)
    marker.write_text('{"enabled": false}\n', encoding="utf-8")
    code = mem.main(["--workspace", str(tmp_path), "check", "--json"])
    assert code == 0
    assert not (tmp_path / "aidlc-docs" / "knowledge" / "code" / ".stale.json").exists()


def test_greenfield_skip(tmp_path: Path):
    enable(tmp_path)
    code, report = run_check(tmp_path)
    assert code == 0
    assert report["mode"] == "skip"
    assert "greenfield" in report["reasons"]


def test_clean_skip_and_events(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    setup_stamped(repo, files)
    code, report = run_check(repo)
    assert code == 0
    assert report["mode"] == "skip"
    assert report["reasons"] == ["clean"]
    assert report["stale_sources"] == []
    events = (repo / "aidlc-docs" / "knowledge" / ".events.jsonl").read_text(encoding="utf-8")
    assert '"event": "re_decision"' in events
    assert '"mode": "skip"' in events


def test_hash_mismatch_is_delta_under_threshold(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    setup_stamped(repo, files)
    (repo / "src" / "f0.py").write_text("changed\n", encoding="utf-8")
    code, report = run_check(repo)
    assert code == 1
    assert report["mode"] == "delta"
    assert "src/f0.py" in report["stale_sources"]
    assert report["entries"][0]["status"] == "stale"
    assert any(item["reason"] == "hash_mismatch" for item in report["entries"][0]["stale_sources"])


def test_crlf_same_text_is_not_stale(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    setup_stamped(repo, files)
    (repo / "src" / "f0.py").write_bytes(b"content src/f0.py\r\n")
    code, report = run_check(repo)
    assert code == 0
    assert report["mode"] == "skip"
    assert report["stale_sources"] == []


def test_uncovered_file(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    setup_stamped(repo, files)
    (repo / "src" / "new.py").write_text("new\n", encoding="utf-8")
    code, report = run_check(repo)
    assert code == 1
    assert "src/new.py" in report["uncovered"]
    assert report["mode"] == "delta"


def test_ratio_boundary_and_full(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(10)]
    setup_stamped(repo, files)
    for index in range(3):
        (repo / "src" / f"f{index}.py").write_text("changed\n", encoding="utf-8")
    _code, report = run_check(repo)
    assert report["divergence_ratio"] == pytest.approx(0.3)
    assert report["mode"] == "delta"
    for index in range(3, 4):
        (repo / "src" / f"f{index}.py").write_text("changed\n", encoding="utf-8")
    _code, report = run_check(repo)
    assert report["divergence_ratio"] == pytest.approx(0.4)
    assert report["mode"] == "full"
    assert "divergence_over_threshold" in report["reasons"]


def test_rename_without_rename_detection(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(10)]
    setup_stamped(repo, files)
    git(repo, "mv", "src/f0.py", "src/renamed.py")
    commit_all(repo, "rename")
    seal_audit(repo)
    code, report = run_check(repo)
    assert code == 1
    assert "src/f0.py" in report["stale_sources"]
    assert "src/renamed.py" in report["uncovered"]
    assert report["mode"] == "delta"


def test_missing_commit_falls_back_to_hash_and_forces_full(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    entry = setup_stamped(repo, files)
    bogus = "deadbeef" * 5
    front, body = mem.split_frontmatter(entry.read_text(encoding="utf-8"))
    meta = mem.parse_yaml_subset(front)
    meta["source_commit"] = bogus
    entry.write_text(mem.dump_frontmatter(meta) + body, encoding="utf-8")
    commit_all(repo, "lose commit")
    seal_audit(repo)
    _code, report = run_check(repo)
    assert report["mode"] == "full"
    assert "source_commit_absent_or_unreachable" in report["reasons"]
    assert report["entries"][0]["status"] == "current"
    assert report["stale_sources"] == []


def test_shallow_clone_commit_not_in_history(tmp_path: Path):
    origin = tmp_path / "origin"
    files = [f"src/f{i}.py" for i in range(4)]
    setup_stamped(origin, files)
    clone = tmp_path / "clone"
    proc = subprocess.run(
        ["git", "-c", "protocol.file.allow=always", "clone", "--depth", "1", origin.as_uri(), str(clone)],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.fail(proc.stderr)
    git(clone, "config", "user.email", "memory-test@example.com")
    git(clone, "config", "user.name", "Memory Test")
    _code, report = run_check(clone)
    assert report["git"] is True
    assert report["entries"][0]["source_commit_reachable"] is False
    assert "source_commit_absent_or_unreachable" in report["reasons"]
    assert report["mode"] == "full"
    assert report["entries"][0]["status"] == "current"


def test_no_git_uses_hash_only(tmp_path: Path):
    enable(tmp_path)
    files = ["src/a.py", "src/b.py", "src/c.py", "src/d.py"]
    write_sources(tmp_path, files)
    entry = write_entry(tmp_path, files)
    assert mem.main(["--workspace", str(tmp_path), "stamp", "sample.md"]) == 0
    write_handoff(tmp_path, 1, "full")
    code, report = run_check(tmp_path)
    assert code == 0
    assert report["git"] is False
    assert report["mode"] == "skip"
    parsed = mem.parse_yaml_subset(mem.split_frontmatter(entry.read_text(encoding="utf-8"))[0])
    assert parsed["source_commit"] == "unversioned"
    (tmp_path / "src" / "a.py").write_text("edited\n", encoding="utf-8")
    code, report = run_check(tmp_path)
    assert code == 1
    assert report["mode"] == "delta"
    assert "src/a.py" in report["stale_sources"]


def test_user_requested_full(tmp_path: Path):
    repo = tmp_path / "repo"
    setup_stamped(repo, [f"src/f{i}.py" for i in range(4)])
    code, report = run_check(repo, "--user-requested-full")
    assert code == 1
    assert report["mode"] == "full"
    assert "user_requested" in report["reasons"]


def test_handoff_missing_and_resume(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    enable(repo)
    files = [f"src/f{i}.py" for i in range(4)]
    write_sources(repo, files)
    commit_all(repo, "sources")
    entry = write_entry(repo, files)
    assert mem.main(["--workspace", str(repo), "stamp", str(entry)]) == 0
    commit_all(repo, "memory")
    seal_audit(repo)
    code, report = run_check(repo)
    assert code == 1
    assert report["mode"] == "full"
    assert "handoff_missing_or_unapproved" in report["reasons"]
    code, report = run_check(repo, "--resume")
    assert code == 0
    assert report["mode"] == "skip"
    assert "handoff_missing_or_unapproved" not in report["reasons"]


def test_unapproved_handoff_forces_full(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(4)]
    init_repo(repo)
    enable(repo)
    write_sources(repo, files)
    commit_all(repo, "sources")
    entry = write_entry(repo, files)
    mem.main(["--workspace", str(repo), "stamp", str(entry)])
    write_handoff(repo, 1, "full", human=False)
    commit_all(repo, "memory")
    seal_audit(repo)
    _code, report = run_check(repo)
    assert report["mode"] == "full"
    assert "handoff_missing_or_unapproved" in report["reasons"]


def test_three_delta_cycles_force_full(tmp_path: Path):
    repo = tmp_path / "repo"
    setup_stamped(repo, [f"src/f{i}.py" for i in range(4)], handoffs=3, mode="delta")
    code, report = run_check(repo)
    assert code == 1
    assert report["mode"] == "full"
    assert "delta_streak" in report["reasons"]
    code, report = run_check(repo, "--resume")
    assert code == 0
    assert report["mode"] == "skip"


def test_unaudited_commit(tmp_path: Path):
    repo = tmp_path / "repo"
    setup_stamped(repo, [f"src/f{i}.py" for i in range(4)])
    (repo / "notes.txt").write_text("hotfix outside the workflow\n", encoding="utf-8")
    commit_all(repo, "hotfix outside")
    _code, report = run_check(repo)
    assert report["mode"] == "full"
    assert "unaudited_commits" in report["reasons"]
    seal_audit(repo)
    _code, report = run_check(repo)
    assert "unaudited_commits" not in report["reasons"]
    assert report["mode"] == "skip"


def test_manifest_change_forces_full(tmp_path: Path):
    repo = tmp_path / "repo"
    setup_stamped(repo, [f"src/f{i}.py" for i in range(4)])
    (repo / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    commit_all(repo, "deps")
    seal_audit(repo)
    _code, report = run_check(repo)
    assert report["mode"] == "full"
    assert "manifest_or_toplevel" in report["reasons"]


def test_toplevel_directory_forces_full(tmp_path: Path):
    repo = tmp_path / "repo"
    setup_stamped(repo, [f"src/f{i}.py" for i in range(4)])
    extra = repo / "extra" / "keep.txt"
    extra.parent.mkdir()
    extra.write_text("dir\n", encoding="utf-8")
    commit_all(repo, "add extra")
    seal_audit(repo)
    _code, report = run_check(repo)
    assert "manifest_or_toplevel" in report["reasons"]
    assert report["mode"] == "full"


def test_aggregate_hotfix_is_listed_and_entry_stays_current(tmp_path: Path):
    repo = tmp_path / "repo"
    files = [f"src/f{i}.py" for i in range(5)]
    setup_stamped(repo, files, aggregate=True)
    (repo / "src" / "f0.py").write_text("hotfix\n", encoding="utf-8")
    code, report = run_check(repo)
    assert code == 1
    assert report["mode"] == "delta"
    assert report["entries"][0]["status"] == "current"
    assert report["entries"][0]["noted_sources"][0]["path"] == "src/f0.py"
    assert "src/f0.py" in report["stale_sources"]
    assert "aggregate_below_threshold" in report["warnings"]


def test_stamp_refuses_missing_source_without_writing(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    enable(repo)
    entry = write_entry(repo, ["src/missing.py"])
    before = entry.read_text(encoding="utf-8")
    code = mem.main(["--workspace", str(repo), "stamp", "sample.md"])
    assert code == 1
    assert entry.read_text(encoding="utf-8") == before


def test_stamp_updates_hash_and_commit(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    enable(repo)
    write_sources(repo, ["src/a.py"])
    commit_all(repo, "sources")
    entry = write_entry(repo, ["src/a.py"])
    assert mem.main(["--workspace", str(repo), "stamp", "sample.md"]) == 0
    meta = mem.parse_yaml_subset(mem.split_frontmatter(entry.read_text(encoding="utf-8"))[0])
    assert meta["source_commit"] == git(repo, "rev-parse", "HEAD").stdout.strip()
    assert meta["sources"][0]["sha256"] == mem.file_sha256(repo / "src" / "a.py")
    assert "Body stays." in entry.read_text(encoding="utf-8")


def test_path_escape_is_missing(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    enable(repo)
    outside = tmp_path / "secret.py"
    outside.write_text("secret\n", encoding="utf-8")
    write_sources(repo, [f"src/f{i}.py" for i in range(4)])
    commit_all(repo, "sources")
    entry = write_entry(repo, ["../secret.py", "src/f0.py", "src/f1.py", "src/f2.py"])
    mem.main(["--workspace", str(repo), "stamp", str(entry)])
    # stamp refuses because ../secret.py is not a safe workspace path
    assert "sha256: " + ("0" * 64) in entry.read_text(encoding="utf-8")


def test_manual_prints_fallback():
    code = mem.main(["manual"])
    assert code == 0


def test_manual_text_has_git_and_hash_steps(capsys: pytest.CaptureFixture[str]):
    mem.main(["manual"])
    out = capsys.readouterr().out
    assert "git diff --name-only --no-renames" in out
    assert "sha256sum" in out
    assert "tr -d" in out


def test_emit_handoff_and_archive(tmp_path: Path):
    enable(tmp_path)
    assert mem.main(["--workspace", str(tmp_path), "emit", "handoff", "--cycle", "2", "--approved", "true"]) == 0
    assert mem.main(["--workspace", str(tmp_path), "emit", "archive", "--change-id", "add-login", "--result", "blocked"]) == 0
    lines = (tmp_path / "aidlc-docs" / "knowledge" / ".events.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines]
    assert events[0]["event"] == "handoff" and events[0]["approved"] is True
    assert events[1]["event"] == "archive" and events[1]["result"] == "blocked"


def test_lf_normalization_matches_manual_recipe(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"alpha\r\nbeta\rgamma\n")
    digest = mem.file_sha256(path)
    import hashlib
    manual = hashlib.sha256(b"alpha\nbeta\ngamma\n").hexdigest()
    assert digest == manual
