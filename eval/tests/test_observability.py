"""Tests for the memory observability harness. They do not call grok."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval"))

import dup_check  # noqa: E402
import inject_conflict  # noqa: E402
import inject_hotfix  # noqa: E402
import parse_audit  # noqa: E402
import report  # noqa: E402
import run_trials  # noqa: E402


def git(repo: Path, *args: str) -> None:
    proc = subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)


def init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init")
    git(repo, "config", "user.email", "memory-test@example.com")
    git(repo, "config", "user.name", "Memory Test")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")


def test_trial_plan_alternates_arms_and_builds_grok_command():
    planned = run_trials.plan_trials(2, [1, 2, 3])
    first = [row["arm"] for row in planned if row["repetition"] == 0]
    second = [row["arm"] for row in planned if row["repetition"] == 1]
    assert first[:3] == ["upstream", "upstream", "upstream"]
    assert first[3:] == ["extension", "extension", "extension"]
    assert second[0] == "extension"
    assert second[3] == "upstream"
    argv = run_trials.grok_argv("hello", "grok-test", "/tmp/repo")
    assert argv[:4] == ["grok", "--no-auto-update", "-m", "grok-test"]
    assert "--always-approve" in argv
    assert "streaming-json" in argv
    assert run_trials.OTEL_ENV["GROK_EXTERNAL_OTEL"] == "1"
    assert run_trials.OTEL_ENV["OTEL_LOG_TOOL_DETAILS"] == "1"


def test_dry_run_writes_placeholders(tmp_path: Path):
    out = tmp_path / "trials.jsonl"
    code = run_trials.main([
        "--repetitions", "1",
        "--cycles", "1",
        "--model", "grok-test",
        "--repo", str(tmp_path),
        "--out", str(out),
        "--dry-run",
    ])
    assert code == 0
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert {row["arm"] for row in rows} == {"upstream", "extension"}
    assert all(row["status"] == "not_run" and row["reason"] == "dry_run" for row in rows)
    assert all(row["tokens_in"] is None for row in rows)


def test_inject_hotfix_kinds(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    content = inject_hotfix.inject(repo, "content", "src/app.py")
    assert content
    assert "hotfix outside AI-DLC" in (repo / "src" / "app.py").read_text(encoding="utf-8")
    renamed = inject_hotfix.inject(repo, "rename", "src/app.py")
    assert renamed != content
    assert (repo / "src" / "app-renamed.py").is_file()
    crlf = inject_hotfix.inject(repo, "crlf", "src/app-renamed.py")
    assert b"\r\n" in (repo / "src" / "app-renamed.py").read_bytes()
    assert crlf != renamed


def test_inject_conflict_writes_marker(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    marker = inject_conflict.inject(repo)
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["requirement"] == "User can login"
    living = (repo / "aidlc-docs/openspec/specs/login/spec.md").read_text(encoding="utf-8")
    delta = (repo / "aidlc-docs/openspec/changes/add-login/specs/login/spec.md").read_text(encoding="utf-8")
    assert "accept a known email" in living
    assert "second factor" in delta


def test_parse_audit_cross_check(tmp_path: Path):
    audit = tmp_path / "audit.md"
    events = tmp_path / "events.jsonl"
    audit.write_text(
        "## Memory RE Decision\n"
        "**Timestamp**: 2026-10-22T00:00:00Z\n"
        "**RE Decision**: delta\n"
        "**Reasons**: stale_entries\n"
        '**User Input**: "delta"\n'
        "**Approved**: yes\n",
        encoding="utf-8",
    )
    events.write_text(json.dumps({"event": "re_decision", "mode": "delta"}) + "\n", encoding="utf-8")
    result = parse_audit.cross_check(audit.read_text(encoding="utf-8"), events.read_text(encoding="utf-8"))
    assert result["ok"] is True
    events.write_text(json.dumps({"event": "re_decision", "mode": "full"}) + "\n", encoding="utf-8")
    result = parse_audit.cross_check(audit.read_text(encoding="utf-8"), events.read_text(encoding="utf-8"))
    assert result["ok"] is False


def test_dup_check_flags_copied_paragraph_only():
    spec = (
        "The system shall accept a known email and password and open a session "
        "for that account without asking again during the same visit today.\n"
    )
    copied = spec
    reference = "See change add-login, requirement User can login.\n"
    assert dup_check.compare_texts(copied, spec)
    assert dup_check.compare_texts(reference, spec) == []


def test_report_median_interval_passk_and_rule_of_three():
    assert report.median([1, 3, 2]) == 2
    assert report.pass_at_k(9, 10, 2) == pytest.approx(36 / 45)
    assert report.rule_of_three(0, 30) == pytest.approx(0.1)
    assert report.rule_of_three(1, 30) is None
    baseline = [100, 120, 80, 110, 90, 130, 100, 140]
    extension = [50, 60, 40, 55, 45, 65, 50, 70]
    interval = report.paired_median_ci(baseline, extension, n_boot=500, seed=1)
    assert interval["median_delta"] > 0
    assert interval["low"] > 0
    same = report.paired_median_ci([10, 10, 10, 10], [10, 10, 10, 10], n_boot=200, seed=1)
    assert same["low"] == 0
    rows = []
    for index, (base, other) in enumerate(zip(baseline, extension)):
        rows.append({"repetition": index, "arm": "upstream", "cycle": 2, "tokens_in": base, "passed": True, "status": "ran"})
        rows.append({"repetition": index, "arm": "extension", "cycle": 2, "tokens_in": other, "passed": True, "status": "ran"})
    rows.append({"repetition": 0, "arm": "extension", "cycle": 1, "passed": False, "status": "fail", "reason": "missed audit"})
    summary = report.summarize(rows)
    assert summary["reduction_ci_above_zero"] is True
    assert summary["median_reduction"] >= 0.3
    assert len(summary["failures"]) == 1
    assert summary["failures"][0]["reason"] == "missed audit"


def test_merge_check_allowlist(tmp_path: Path):
    repo = tmp_path / "repo"
    init_repo(repo)
    allow = tmp_path / "allow.txt"
    allow.write_text("ok.md\n")
    (repo / "ok.md").write_text("base\n", encoding="utf-8")
    (repo / "nope.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "base files")
    git(repo, "checkout", "-b", "other")
    (repo / "ok.md").write_text("other\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "other ok")
    git(repo, "checkout", "-")
    (repo / "ok.md").write_text("main\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "main ok")
    script = ROOT / "eval" / "merge_check.sh"
    allowed = subprocess.run(["sh", str(script), str(repo), str(allow), "other"], check=False, capture_output=True, text=True)
    assert allowed.returncode == 0, allowed.stderr
    git(repo, "checkout", "-b", "bad")
    (repo / "nope.md").write_text("bad branch\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "bad")
    git(repo, "checkout", "-")
    (repo / "nope.md").write_text("main nope\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "main nope")
    blocked = subprocess.run(["sh", str(script), str(repo), str(allow), "bad"], check=False, capture_output=True, text=True)
    assert blocked.returncode == 1
    assert "nope.md" in blocked.stderr


def test_hooks_log_and_block(tmp_path: Path):
    log = tmp_path / "tool.jsonl"
    env = {
        **dict(**{key: value for key, value in __import__("os").environ.items()}),
        "EVAL_HOOK_LOG": str(log),
        "EVAL_RUN_ID": "run-1",
        "EVAL_CYCLE": "2",
        "EVAL_STAGE": "inception",
    }
    event = {
        "hookEventName": "PostToolUse",
        "toolName": "Read",
        "toolInput": {"path": "src/app.py"},
        "sessionId": "sess",
    }
    proc = subprocess.run(
        [sys.executable, str(ROOT / "eval" / "hooks" / "post_tool_use.py")],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    recorded = json.loads(log.read_text(encoding="utf-8"))
    assert recorded["run_id"] == "run-1"
    assert recorded["ciclo"] == "2"
    assert recorded["etapa"] == "inception"
    assert recorded["tool"] == "Read"
    assert recorded["arquivo"] == "src/app.py"

    blocker = str(ROOT / "eval" / "hooks" / "block_auto_conflict.py")
    denied = subprocess.run(
        [sys.executable, blocker],
        input=json.dumps({"hookEventName": "PreToolUse", "toolInput": {"command": "git checkout --ours spec.md"}}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert denied.returncode == 2
    assert json.loads(denied.stdout)["decision"] == "deny"
    allowed = subprocess.run(
        [sys.executable, blocker],
        input=json.dumps({"hookEventName": "PreToolUse", "toolInput": {"command": "git status"}}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert allowed.returncode == 0
    conflict = tmp_path / "aidlc-docs" / "openspec"
    conflict.mkdir(parents=True)
    (conflict / ".conflict.json").write_text("{}\n", encoding="utf-8")
    stopped = subprocess.run(
        [sys.executable, blocker],
        input=json.dumps({"hookEventName": "Stop", "cwd": str(tmp_path)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert stopped.returncode == 2
    (conflict / ".conflict-approved").write_text("human\n", encoding="utf-8")
    released = subprocess.run(
        [sys.executable, blocker],
        input=json.dumps({"hookEventName": "Stop", "cwd": str(tmp_path)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert released.returncode == 0
