#!/usr/bin/env python3
"""Cross-check Memory RE Decision blocks in audit.md with re_decision events."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BLOCK = re.compile(
    r"## Memory RE Decision\s+"
    r"\*\*Timestamp\*\*:.*?\s+"
    r"\*\*RE Decision\*\*: (skip|delta|full)\s+"
    r"\*\*Reasons\*\*:.*?\s+"
    r"\*\*User Input\*\*:.*?\s+"
    r"\*\*Approved\*\*: (yes|no)",
    re.DOTALL,
)


def parse_decisions(text: str) -> list[dict]:
    found = []
    for match in BLOCK.finditer(text):
        found.append({"mode": match.group(1), "approved": match.group(2)})
    return found


def parse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("event") == "re_decision":
            events.append(item)
    return events


def cross_check(audit_text: str, events_text: str) -> dict:
    decisions = parse_decisions(audit_text)
    events = parse_events(events_text)
    mismatches = []
    if len(decisions) != len(events):
        mismatches.append({
            "reason": "count",
            "decisions": len(decisions),
            "events": len(events),
        })
    for index, (decision, event) in enumerate(zip(decisions, events)):
        if decision["mode"] != event.get("mode"):
            mismatches.append({"reason": "mode", "index": index, "audit": decision["mode"], "event": event.get("mode")})
        if decision["approved"] != "yes":
            mismatches.append({"reason": "not_approved", "index": index})
    return {
        "decisions": len(decisions),
        "events": len(events),
        "mismatches": mismatches,
        "ok": not mismatches and len(decisions) == len(events),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-check audit decisions and memory events")
    parser.add_argument("--audit", required=True)
    parser.add_argument("--events", required=True)
    args = parser.parse_args(argv)
    result = cross_check(
        Path(args.audit).read_text(encoding="utf-8"),
        Path(args.events).read_text(encoding="utf-8"),
    )
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
