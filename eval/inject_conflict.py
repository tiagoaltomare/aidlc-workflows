#!/usr/bin/env python3
"""Write divergent OpenSpec texts and a conflict marker the Stop hook can see.

The marker does not resolve the conflict. archive-check is what decides, and
a human has to approve before anyone removes aidlc-docs/openspec/.conflict.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

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

DELTA = """---
type: Spec
title: Delta for login
status: draft
---

# Delta for login

## MODIFIED Requirements

### Requirement: User can login

The system SHALL reject every password until a second factor arrives.

#### Scenario: Valid credentials

- **GIVEN** a known account
- **WHEN** the user submits the right password
- **THEN** the system asks for a second factor
"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True)


def inject(repo: Path, change_id: str = "add-login") -> Path:
    spec = repo / "aidlc-docs" / "openspec" / "specs" / "login" / "spec.md"
    delta = repo / "aidlc-docs" / "openspec" / "changes" / change_id / "specs" / "login" / "spec.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    delta.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(LIVING, encoding="utf-8")
    delta.write_text(DELTA, encoding="utf-8")
    marker = repo / "aidlc-docs" / "openspec" / ".conflict.json"
    marker.write_text(json.dumps({
        "change_id": change_id,
        "requirement": "User can login",
        "reason": "modified_body_differs",
    }, indent=2) + "\n", encoding="utf-8")
    identity: list[str] = []
    configured = git(repo, "config", "user.email")
    if configured.returncode != 0 or not configured.stdout.strip():
        identity = ["-c", "user.email=memory-test@example.com", "-c", "user.name=Memory Test"]
    inside = git(repo, "rev-parse", "--is-inside-work-tree")
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        git(repo, "add", "-A")
        git(repo, *identity, "commit", "-m", "test: inject divergent OpenSpec bodies")
    return marker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inject divergent OpenSpec bodies")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--change-id", default="add-login")
    args = parser.parse_args(argv)
    marker = inject(Path(args.repo).resolve(), args.change_id)
    print(marker.relative_to(Path(args.repo).resolve()).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
