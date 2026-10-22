#!/usr/bin/env python3
"""PreToolUse and Stop hook: refuse automatic OpenSpec conflict resolution.

Exit 2 with a JSON deny decision blocks the tool or the end of the turn.
Anything else exits 0. A human clears the block by creating
aidlc-docs/openspec/.conflict-approved after reviewing the diff.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

AUTO_RESOLVE = re.compile(r"(--ours\b|--theirs\b|-X\s*ours\b|-X\s*theirs\b|-Xours\b|-Xtheirs\b)")
MARKER_REWRITE = re.compile(r"(sed|perl|python).{0,80}<<<<<<<|<<<<<<<.{0,80}(sed|perl)")


def command_of(event: dict) -> str:
    tool_input = event.get("toolInput") or event.get("tool_input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}))
    return 2


def workspace_of(event: dict) -> Path:
    root = event.get("workspaceRoot") or event.get("cwd") or os.getcwd()
    return Path(root)


def main() -> int:
    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    if not isinstance(event, dict):
        event = {}
    name = event.get("hookEventName") or os.environ.get("GROK_HOOK_EVENT") or ""
    if name in {"Stop", "StopFailure"}:
        root = workspace_of(event)
        conflict = root / "aidlc-docs" / "openspec" / ".conflict.json"
        approved = root / "aidlc-docs" / "openspec" / ".conflict-approved"
        if conflict.is_file() and not approved.is_file():
            return deny("OpenSpec conflict requires a human approval before the turn can end.")
        return 0
    command = command_of(event)
    if AUTO_RESOLVE.search(command) or MARKER_REWRITE.search(command):
        return deny("Automatic conflict resolution is blocked. A human must choose the OpenSpec result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
