"""Archive and lint tests for the OpenSpec subset in aidlc_memory.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aidlc_memory as mem  # noqa: E402


def enable(repo: Path) -> None:
    marker = repo / "aidlc-docs" / "knowledge" / ".aidlc-memory"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}\n", encoding="utf-8")


def write(repo: Path, relative: str, text: str) -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


LIVING = """---
type: Spec
title: login
status: stable
---

# login specification

## Requirements

### Requirement: User can login

The system SHALL accept a known email and password.

#### Scenario: Valid credentials

- **GIVEN** a known account
- **WHEN** the user submits the right password
- **THEN** the system opens a session
"""

ADDED = """---
type: Spec
title: Delta for login
status: draft
---

# Delta for login

## ADDED Requirements

### Requirement: User can logout

The system SHALL end the session on request.

#### Scenario: Logout

- **GIVEN** an open session
- **WHEN** the user logs out
- **THEN** the session is gone
"""


def test_archive_apply_requires_approval_and_blocks_conflict(tmp_path: Path):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    delta = ADDED.replace(
        "### Requirement: User can logout\n\nThe system SHALL end the session on request.",
        "### Requirement: User can login\n\nThe system SHALL reject every password.",
    )
    write(tmp_path, "aidlc-docs/openspec/changes/add-login/specs/login/spec.md", delta)
    before = (tmp_path / "aidlc-docs/openspec/specs/login/spec.md").read_text(encoding="utf-8")
    code = mem.main(["--workspace", str(tmp_path), "archive-apply", "--change", "add-login", "--approved"])
    assert code == 1
    assert (tmp_path / "aidlc-docs/openspec/specs/login/spec.md").read_text(encoding="utf-8") == before
    assert (tmp_path / "aidlc-docs/openspec/changes/add-login").is_dir()
    refused = mem.main(["--workspace", str(tmp_path), "archive-apply", "--change", "add-login"])
    assert refused == 2
    assert (tmp_path / "aidlc-docs/openspec/changes/add-login").is_dir()


def test_archive_apply_merges_and_moves(tmp_path: Path):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    write(tmp_path, "aidlc-docs/openspec/changes/add-login/specs/login/spec.md", ADDED)
    code = mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "add-login"])
    assert code == 0
    code = mem.main(["--workspace", str(tmp_path), "archive-apply", "--change", "add-login", "--approved"])
    assert code == 0
    merged = (tmp_path / "aidlc-docs/openspec/specs/login/spec.md").read_text(encoding="utf-8")
    assert "User can login" in merged
    assert "User can logout" in merged
    assert not (tmp_path / "aidlc-docs/openspec/changes/add-login").exists()
    archived = list((tmp_path / "aidlc-docs/openspec/changes/archive").glob("*-add-login"))
    assert len(archived) == 1
    events = (tmp_path / "aidlc-docs/knowledge/.events.jsonl").read_text(encoding="utf-8")
    assert '"event": "archive"' in events
    assert '"result": "applied"' in events


def test_identical_add_is_not_a_conflict(tmp_path: Path):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    delta = """---
type: Spec
title: Delta
---

# Delta

## ADDED Requirements

### Requirement: User can login

The system SHALL accept a known email and password.

#### Scenario: Valid credentials

- **GIVEN** a known account
- **WHEN** the user submits the right password
- **THEN** the system opens a session
"""
    write(tmp_path, "aidlc-docs/openspec/changes/add-login/specs/login/spec.md", delta)
    code = mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "add-login"])
    assert code == 0


def test_removed_missing_and_rename_block(tmp_path: Path):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    removed = """# Delta

## REMOVED Requirements

### Requirement: Missing one
"""
    write(tmp_path, "aidlc-docs/openspec/changes/drop-login/specs/login/spec.md", removed)
    assert mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "drop-login"]) == 1
    renamed = """# Delta

## RENAMED Requirements

### Requirement: User can login
"""
    write(tmp_path, "aidlc-docs/openspec/changes/rename-login/specs/login/spec.md", renamed)
    assert mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "rename-login"]) == 1
    assert (tmp_path / "aidlc-docs/openspec/specs/login/spec.md").read_text(encoding="utf-8") == LIVING


def test_conflict_markers_and_lint(tmp_path: Path):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING + "\n<<<<<<< HEAD\n")
    write(tmp_path, "aidlc-docs/openspec/changes/add-login/specs/login/spec.md", ADDED)
    assert mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "add-login"]) == 1
    code = mem.main(["--workspace", str(tmp_path), "lint"])
    assert code == 1
    clean = tmp_path / "clean"
    enable(clean)
    write(clean, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    assert mem.main(["--workspace", str(clean), "lint"]) == 0


def test_memory_off_refuses_archive(tmp_path: Path):
    assert mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "add-login"]) == 2


def test_archive_check_json_names_the_conflict(tmp_path: Path, capsys):
    enable(tmp_path)
    write(tmp_path, "aidlc-docs/openspec/specs/login/spec.md", LIVING)
    delta = """# Delta

## MODIFIED Requirements

### Requirement: Does not exist

The system SHALL do something else entirely here.
"""
    write(tmp_path, "aidlc-docs/openspec/changes/add-login/specs/login/spec.md", delta)
    code = mem.main(["--workspace", str(tmp_path), "archive-check", "--change", "add-login"])
    assert code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["conflicts"][0]["code"] == "modified_missing"
