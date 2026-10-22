#!/usr/bin/env python3
"""PostToolUse hook: append one NDJSON record per tool call.

Fields: run_id, ciclo, etapa, tool, arquivo, ts, event.
EVAL_HOOK_LOG overrides the output path. EVAL_RUN_ID, EVAL_CYCLE, and
EVAL_STAGE identify the trial. The hook never blocks the tool.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def file_from_input(tool_input: object) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for key in ("path", "file_path", "file", "target"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def record_from(event: dict) -> dict:
    tool_input = event.get("toolInput") or event.get("tool_input") or {}
    return {
        "run_id": os.environ.get("EVAL_RUN_ID") or event.get("sessionId") or "",
        "ciclo": os.environ.get("EVAL_CYCLE") or "",
        "etapa": os.environ.get("EVAL_STAGE") or "",
        "tool": event.get("toolName") or event.get("tool_name") or "",
        "arquivo": file_from_input(tool_input),
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event.get("hookEventName") or os.environ.get("GROK_HOOK_EVENT") or "PostToolUse",
    }


def destination(event: dict) -> Path:
    override = os.environ.get("EVAL_HOOK_LOG")
    if override:
        return Path(override)
    root = event.get("workspaceRoot") or event.get("cwd") or os.getcwd()
    return Path(root) / "aidlc-docs" / "knowledge" / ".tool-use.jsonl"


def main() -> int:
    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    if not isinstance(event, dict):
        event = {}
    path = destination(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record_from(event), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
