#!/usr/bin/env python3
"""Plan and record Grok Build trials for the memory extension.

The headless JSON schema and ~/.grok/sessions layout are not confirmed.
This script builds the command and writes trials.jsonl. It does not invent
token counts. When the grok CLI is missing it records grok_cli_absent and
exits 0 unless --require-grok is set. Running the battery is F5, not this phase.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OTEL_ENV = {
    "GROK_EXTERNAL_OTEL": "1",
    "OTEL_LOGS_EXPORTER": "console",
    "OTEL_LOG_TOOL_DETAILS": "1",
}


def alternation(repetitions: int) -> list[tuple[str, str]]:
    rows = []
    for index in range(repetitions):
        if index % 2 == 0:
            rows.append(("upstream", "extension"))
        else:
            rows.append(("extension", "upstream"))
    return rows


def plan_trials(repetitions: int, cycles: list[int]) -> list[dict]:
    planned = []
    for index, pair in enumerate(alternation(repetitions)):
        for arm in pair:
            for cycle in cycles:
                planned.append({"repetition": index, "arm": arm, "cycle": cycle})
    return planned


def cycle_prompt(arm: str, cycle: int) -> str:
    if arm == "extension":
        memory = (
            "The memory extension is enabled. Read only the latest handoff and "
            "knowledge index, then run aidlc_memory.py check. A human approves "
            "skip, delta, or full before reverse engineering."
        )
    else:
        memory = (
            "The memory extension is disabled. Do not create aidlc-docs/knowledge "
            "or aidlc-docs/openspec."
        )
    return (
        f"Run AI-DLC cycle {cycle} in this clean clone. {memory} "
        "Record every reverse-engineering decision in aidlc-docs/audit.md."
    )


def grok_argv(prompt: str, model: str, cwd: str) -> list[str]:
    return [
        "grok",
        "--no-auto-update",
        "-m",
        model,
        "-p",
        prompt,
        "--always-approve",
        "--output-format",
        "streaming-json",
        "--cwd",
        cwd,
    ]


def grok_available() -> bool:
    return shutil.which("grok") is not None


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_planned(planned: list[dict], model: str, repo: str, execute: bool) -> list[dict]:
    rows = []
    available = grok_available()
    for item in planned:
        prompt = cycle_prompt(item["arm"], item["cycle"])
        argv = grok_argv(prompt, model, repo)
        row = {
            **item,
            "model": model,
            "argv": argv,
            "env": dict(OTEL_ENV),
            "status": "not_run",
            "tokens_in": None,
            "duration_ms": None,
            "passed": None,
        }
        if execute and available:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, **OTEL_ENV},
            )
            row["status"] = "ran" if completed.returncode == 0 else "error"
            row["returncode"] = completed.returncode
        elif execute and not available:
            row["status"] = "not_run"
            row["reason"] = "grok_cli_absent"
        else:
            row["reason"] = "dry_run"
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record memory-extension trials")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--cycles", default="1,2,3")
    parser.add_argument("--model", default="unspecified")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", default="trials.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-grok", action="store_true")
    args = parser.parse_args(argv)
    cycles = [int(part) for part in args.cycles.split(",") if part]
    planned = plan_trials(args.repetitions, cycles)
    execute = not args.dry_run
    if execute and args.require_grok and not grok_available():
        print("grok CLI is not on PATH", file=sys.stderr)
        return 2
    rows = run_planned(planned, args.model, str(Path(args.repo).resolve()), execute)
    write_jsonl(Path(args.out), rows)
    if any(row.get("reason") == "grok_cli_absent" for row in rows):
        print("grok CLI is not on PATH; wrote placeholder trials", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
