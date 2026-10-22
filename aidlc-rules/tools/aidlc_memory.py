#!/usr/bin/env python3
"""Deterministic memory checks for the AI-DLC memory extension.

Python 3 standard library only. The model must not calculate hashes; this
script does. See aws-aidlc-rule-details/extensions/memory/memory-spec.md.

When Python or this file is missing, run ``aidlc_memory.py manual`` from a
machine that has it, or follow the Manual fallback section of that spec:
git diff --name-only --no-renames, then SHA-256 after ``tr -d '\\r'``.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL_VERSION = "1"
DEFAULT_STALE_RATIO = 0.30
DEFAULT_AGGREGATE_RATIO = 0.30
DEFAULT_DELTA_STREAK = 3
DEFAULT_BUDGET_TOKENS = 2000

CODE_EXTENSIONS = {
    ".java", ".py", ".js", ".ts", ".jsx", ".tsx", ".kt", ".kts", ".scala",
    ".groovy", ".go", ".rs", ".rb", ".php", ".c", ".h", ".cpp", ".hpp",
    ".cc", ".cs", ".fs", ".swift", ".vue", ".svelte", ".sql", ".sh",
}
EXCLUDE_DIRS = {
    "aidlc-docs", ".git", "node_modules", "vendor", "dist", "build",
    "target", "__pycache__", ".venv", "venv", ".tox",
}
MANIFEST_NAMES = {
    "pom.xml", "package.json", "package-lock.json", "build.gradle",
    "build.gradle.kts", "settings.gradle", "go.mod", "go.sum", "Cargo.toml",
    "Cargo.lock", "requirements.txt", "pyproject.toml", "Pipfile", "Gemfile",
    "composer.json", "Makefile", "Dockerfile", "docker-compose.yml",
    "compose.yaml", "Package.swift", "mix.exs", "pubspec.yaml", "build.sbt",
}
MANIFEST_SUFFIXES = {".csproj"}

FORCE_FULL = {
    "source_commit_absent_or_unreachable",
    "divergence_over_threshold",
    "manifest_or_toplevel",
    "delta_streak",
    "unaudited_commits",
    "handoff_missing_or_unapproved",
    "user_requested",
    "no_codekb",
}
RESUME_SUPPRESSED = {"handoff_missing_or_unapproved", "delta_streak"}

KEY_ORDER = [
    "type", "title", "description", "status", "source_commit", "aggregate",
    "re_mode", "covers", "derived_from", "generated", "verified", "sources",
]


def knowledge_dir(workspace: Path) -> Path:
    return workspace / "aidlc-docs" / "knowledge"


def openspec_dir(workspace: Path) -> Path:
    return workspace / "aidlc-docs" / "openspec"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_git(workspace: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=workspace,
        check=False,
        capture_output=True,
    )


def git_ok(workspace: Path) -> bool:
    proc = run_git(workspace, ["rev-parse", "--is-inside-work-tree"])
    return proc.returncode == 0 and proc.stdout.strip() == b"true"


def git_head(workspace: Path) -> str | None:
    proc = run_git(workspace, ["rev-parse", "HEAD"])
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip() or None


def commit_reachable(workspace: Path, commit: str | None) -> bool:
    if not commit or commit == "unversioned":
        return False
    exists = run_git(workspace, ["cat-file", "-e", f"{commit}^{{commit}}"])
    if exists.returncode != 0:
        return False
    ancestor = run_git(workspace, ["merge-base", "--is-ancestor", commit, "HEAD"])
    return ancestor.returncode == 0


def split_z(blob: bytes) -> list[str]:
    parts = blob.split(b"\0")
    return [part.decode("utf-8", "replace") for part in parts if part]


def changed_paths(workspace: Path, commit: str) -> set[str]:
    """Paths that differ between commit and the working tree, renames split."""
    proc = run_git(
        workspace,
        ["diff", "--name-only", "-z", "--no-renames", commit],
    )
    names = set(split_z(proc.stdout))
    status = run_git(workspace, ["status", "--porcelain=v1", "-z"])
    raw = status.stdout.split(b"\0")
    index = 0
    while index < len(raw):
        rec = raw[index]
        if not rec:
            index += 1
            continue
        if len(rec) < 4:
            index += 1
            continue
        xy = rec[:2].decode("utf-8", "replace")
        path = rec[3:].decode("utf-8", "replace")
        names.add(path.replace("\\", "/"))
        if "R" in xy or "C" in xy:
            index += 1
            if index < len(raw) and raw[index]:
                names.add(raw[index].decode("utf-8", "replace").replace("\\", "/"))
        index += 1
    return {name.replace("\\", "/") for name in names}


def commits_since(workspace: Path, commit: str) -> list[str]:
    proc = run_git(workspace, ["log", "--format=%H", f"{commit}..HEAD"])
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.decode("utf-8", "replace").splitlines() if line]


def toplevel_dirs(workspace: Path, rev: str) -> set[str]:
    proc = run_git(workspace, ["ls-tree", "-d", "--name-only", rev])
    if proc.returncode != 0:
        return set()
    return {line.strip() for line in proc.stdout.decode("utf-8", "replace").splitlines() if line.strip()}


def file_sha256(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        payload = data
    else:
        payload = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def parse_scalar(raw: str):
    text = raw.strip()
    if " #" in text and not (text.startswith('"') or text.startswith("'")):
        text = text.split(" #", 1)[0].rstrip()
    if text in ("", "~", "null", "Null", "NULL"):
        return None
    if text in ("true", "True", "TRUE"):
        return True
    if text in ("false", "False", "FALSE"):
        return False
    if text.startswith("{") and text.endswith("}"):
        return parse_flow_map(text)
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in split_commas(inner)]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def split_commas(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    quote = ""
    for char in text:
        if quote:
            buf.append(char)
            if char == quote:
                quote = ""
            continue
        if char in ("'", '"'):
            quote = char
            buf.append(char)
            continue
        if char == ",":
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(char)
    if buf:
        parts.append("".join(buf))
    return parts


def parse_flow_map(text: str) -> dict:
    inner = text.strip()[1:-1].strip()
    result: dict = {}
    if not inner:
        return result
    for part in split_commas(inner):
        key, sep, value = part.partition(":")
        if not sep:
            continue
        result[key.strip().strip("\"'")] = parse_scalar(value.strip())
    return result


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml_subset(frontmatter: str) -> dict:
    lines = frontmatter.splitlines()

    def parse_block(start: int, indent: int) -> tuple[dict, int]:
        mapping: dict = {}
        index = start
        while index < len(lines):
            raw = lines[index]
            if not raw.strip() or raw.strip().startswith("#"):
                index += 1
                continue
            current = indent_of(raw)
            if current < indent:
                break
            if current > indent:
                break
            stripped = raw.strip()
            if stripped.startswith("- "):
                break
            key, sep, rest = stripped.partition(":")
            if not sep:
                break
            key = key.strip()
            rest = rest.strip()
            if rest == "" or rest in ("|", ">"):
                if index + 1 < len(lines) and lines[index + 1].strip():
                    next_indent = indent_of(lines[index + 1])
                    next_stripped = lines[index + 1].strip()
                    if next_indent > current and next_stripped.startswith("- "):
                        child, index = parse_list(index + 1, next_indent)
                        mapping[key] = child
                        continue
                    if next_indent > current:
                        child_map, index = parse_block(index + 1, next_indent)
                        mapping[key] = child_map
                        continue
                mapping[key] = None
                index += 1
                continue
            mapping[key] = parse_scalar(rest)
            index += 1
        return mapping, index

    def parse_list(start: int, indent: int) -> tuple[list, int]:
        items: list = []
        index = start
        while index < len(lines):
            raw = lines[index]
            if not raw.strip() or raw.strip().startswith("#"):
                index += 1
                continue
            current = indent_of(raw)
            if current < indent:
                break
            stripped = raw.strip()
            if not stripped.startswith("- "):
                break
            content = stripped[2:].strip()
            if content == "":
                if index + 1 < len(lines) and indent_of(lines[index + 1]) > current:
                    child, index = parse_block(index + 1, indent_of(lines[index + 1]))
                    items.append(child)
                    continue
                items.append(None)
                index += 1
                continue
            key, sep, rest = content.partition(":")
            looks_like_key = sep and key.strip() and " " not in key.strip()
            if looks_like_key:
                item: dict = {}
                if rest.strip():
                    item[key.strip()] = parse_scalar(rest.strip())
                else:
                    item[key.strip()] = None
                index += 1
                while index < len(lines):
                    raw_next = lines[index]
                    if not raw_next.strip() or raw_next.strip().startswith("#"):
                        index += 1
                        continue
                    next_indent = indent_of(raw_next)
                    if next_indent <= current:
                        break
                    nxt = raw_next.strip()
                    if nxt.startswith("- "):
                        break
                    child_key, child_sep, child_rest = nxt.partition(":")
                    if not child_sep:
                        break
                    if child_rest.strip() == "" and index + 1 < len(lines):
                        deeper = indent_of(lines[index + 1])
                        if deeper > next_indent and lines[index + 1].strip().startswith("- "):
                            nested, index = parse_list(index + 1, deeper)
                            item[child_key.strip()] = nested
                            continue
                        if deeper > next_indent:
                            nested_map, index = parse_block(index + 1, deeper)
                            item[child_key.strip()] = nested_map
                            continue
                    item[child_key.strip()] = parse_scalar(child_rest.strip()) if child_rest.strip() else None
                    index += 1
                items.append(item)
                continue
            items.append(parse_scalar(content))
            index += 1
        return items, index

    parsed, _ = parse_block(0, 0)
    return parsed


def split_frontmatter(text: str) -> tuple[str | None, str]:
    normalized = text.lstrip("\ufeff")
    lines = normalized.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            return frontmatter, body
    return None, text


def quote_scalar(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    text = str(value)
    if (
        text == ""
        or text.strip() != text
        or text.lower() in {"true", "false", "null"}
        or any(char in text for char in ":#{}[]&*!|>%@`,'\"")
    ):
        return json.dumps(text, ensure_ascii=False)
    return text


def dump_value_lines(key: str, value, indent: int) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines = [f"{pad}{key}:"]
        for child_key, child_value in value.items():
            lines.extend(dump_value_lines(str(child_key), child_value, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}{key}: []"]
        lines = [f"{pad}{key}:"]
        for item in value:
            if isinstance(item, dict):
                first = True
                for child_key, child_value in item.items():
                    if first:
                        if isinstance(child_value, (dict, list)):
                            lines.append(f"{pad}  - {child_key}:")
                            if isinstance(child_value, dict):
                                for grand_key, grand_value in child_value.items():
                                    lines.extend(dump_value_lines(str(grand_key), grand_value, indent + 6))
                            else:
                                for grand in child_value:
                                    lines.append(f"{pad}      - {quote_scalar(grand)}")
                        else:
                            lines.append(f"{pad}  - {child_key}: {quote_scalar(child_value)}")
                        first = False
                    else:
                        lines.extend(dump_value_lines(str(child_key), child_value, indent + 4))
                if first:
                    lines.append(f"{pad}  - {{}}")
            else:
                lines.append(f"{pad}  - {quote_scalar(item)}")
        return lines
    return [f"{pad}{key}: {quote_scalar(value)}"]


def dump_frontmatter(data: dict) -> str:
    keys = [key for key in KEY_ORDER if key in data]
    keys.extend(key for key in data if key not in keys)
    lines = ["---"]
    for key in keys:
        lines.extend(dump_value_lines(str(key), data[key], 0))
    lines.append("---")
    return "\n".join(lines) + "\n"


def load_marker(path: Path) -> tuple[bool, dict]:
    if not path.is_file():
        return False, {}
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return True, {}
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return True, {}
        if isinstance(data, dict) and data.get("enabled") is False:
            return False, data
        return True, data if isinstance(data, dict) else {}
    return True, {}


def safe_path(workspace: Path, relative: str) -> Path | None:
    rel = relative.replace("\\", "/").strip()
    if not rel or rel.startswith("/") or rel.startswith("../") or "/../" in f"/{rel}/":
        return None
    candidate = (workspace / rel).resolve()
    try:
        candidate.relative_to(workspace.resolve())
    except ValueError:
        return None
    return candidate


def covers_path(pattern: str, relative: str) -> bool:
    pattern = pattern.replace("\\", "/").lstrip("./")
    relative = relative.replace("\\", "/")
    if pattern.endswith("/"):
        return relative.startswith(pattern)
    if "*" in pattern or "?" in pattern:
        return fnmatch.fnmatch(relative, pattern)
    return relative == pattern


def is_manifest(path: str) -> bool:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    return name in MANIFEST_NAMES or Path(name).suffix.lower() in MANIFEST_SUFFIXES


def iter_code_files(workspace: Path, extensions: set[str]) -> list[str]:
    found: list[str] = []
    for dirpath, dirnames, filenames in os_walk(workspace):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDE_DIRS]
        for filename in filenames:
            if Path(filename).suffix.lower() in extensions:
                full = Path(dirpath) / filename
                rel = full.relative_to(workspace).as_posix()
                found.append(rel)
    found.sort()
    return found


def os_walk(root: Path):
    return os.walk(root)


def source_identity(source: dict) -> str | None:
    path = source.get("path") or source.get("resource")
    if not isinstance(path, str):
        return None
    path = path.replace("\\", "/").lstrip("./")
    if path.startswith("http://") or path.startswith("https://"):
        return None
    return path


def load_entries(workspace: Path) -> tuple[list[dict], list[str]]:
    code_dir = knowledge_dir(workspace) / "code"
    entries: list[dict] = []
    warnings: list[str] = []
    if not code_dir.is_dir():
        return entries, warnings
    for path in sorted(code_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, _body = split_frontmatter(text)
        if frontmatter is None:
            warnings.append(f"unreadable:{path.name}")
            continue
        meta = parse_yaml_subset(frontmatter)
        sources = meta.get("sources") if isinstance(meta.get("sources"), list) else []
        covers = meta.get("covers") if isinstance(meta.get("covers"), list) else []
        cleaned_sources = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            identity = source_identity(source)
            if not identity:
                continue
            sha = source.get("sha256")
            cleaned_sources.append({
                "path": identity,
                "sha256": sha.lower() if isinstance(sha, str) else None,
            })
        commit = meta.get("source_commit")
        entries.append({
            "path": path.relative_to(workspace).as_posix(),
            "abs": path,
            "source_commit": commit if isinstance(commit, str) and commit else None,
            "aggregate": bool(meta.get("aggregate") is True),
            "covers": [item.replace("\\", "/") for item in covers if isinstance(item, str)],
            "sources": cleaned_sources,
            "re_mode": meta.get("re_mode") if isinstance(meta.get("re_mode"), str) else None,
        })
    return entries, warnings


def entry_claims(entry: dict, relative: str) -> bool:
    for source in entry["sources"]:
        if source["path"] == relative:
            return True
    for pattern in entry["covers"]:
        if covers_path(pattern, relative):
            return True
    return False


def human_verified(meta: dict) -> bool:
    verified = meta.get("verified")
    events: list = []
    if isinstance(verified, dict):
        events = [verified]
    elif isinstance(verified, list):
        events = [item for item in verified if isinstance(item, dict)]
    return any(str(item.get("by") or "").startswith("human:") for item in events)


def load_handoffs(workspace: Path) -> list[tuple[int, Path, dict]]:
    directory = knowledge_dir(workspace) / "handoff"
    found: list[tuple[int, Path, dict]] = []
    if not directory.is_dir():
        return found
    for path in directory.glob("cycle-*.md"):
        match = re.search(r"cycle-(\d+)", path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, _body = split_frontmatter(text)
        meta = parse_yaml_subset(frontmatter) if frontmatter is not None else {}
        found.append((int(match.group(1)), path, meta))
    found.sort(key=lambda item: item[0])
    return found


def delta_streak(handoffs: list[tuple[int, Path, dict]]) -> int:
    sequence = list(reversed(handoffs))
    index = 0
    while index < len(sequence) and not human_verified(sequence[index][2]):
        index += 1
    streak = 0
    while index < len(sequence):
        meta = sequence[index][2]
        if not human_verified(meta) or meta.get("re_mode") != "delta":
            break
        streak += 1
        index += 1
    return streak


def latest_handoff_approved(handoffs: list[tuple[int, Path, dict]]) -> bool:
    if not handoffs:
        return False
    return human_verified(handoffs[-1][2])


def load_estimate(workspace: Path, budget: int) -> dict:
    handoffs = load_handoffs(workspace)
    handoff_text = ""
    if handoffs:
        handoff_text = handoffs[-1][1].read_text(encoding="utf-8", errors="replace")
    index_path = knowledge_dir(workspace) / "index.md"
    index_text = index_path.read_text(encoding="utf-8", errors="replace") if index_path.is_file() else ""
    estimated = (len(handoff_text) + len(index_text)) // 4
    return {
        "handoff_chars": len(handoff_text),
        "index_chars": len(index_text),
        "estimated_tokens": estimated,
        "budget_tokens": budget,
        "within_budget": estimated <= budget,
    }


def append_event(workspace: Path, event: dict) -> None:
    directory = knowledge_dir(workspace)
    directory.mkdir(parents=True, exist_ok=True)
    event = {"ts": now_iso(), **event}
    path = directory / ".events.jsonl"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def unaudited_commits(workspace: Path, shas: list[str]) -> list[str]:
    audit_path = workspace / "aidlc-docs" / "audit.md"
    text = audit_path.read_text(encoding="utf-8", errors="replace") if audit_path.is_file() else ""
    missing = []
    for sha in shas:
        if sha in text or sha[:12] in text or sha[:7] in text:
            continue
        missing.append(sha)
    return missing


def assess_entries(
    workspace: Path,
    entries: list[dict],
    use_git: bool,
    head: str | None,
    aggregate_ratio: float,
) -> None:
    reachable_cache: dict[str, bool] = {}
    candidate_cache: dict[str, set[str] | None] = {}
    for entry in entries:
        commit = entry["source_commit"]
        reachable = False
        if use_git and head and commit:
            if commit not in reachable_cache:
                reachable_cache[commit] = commit_reachable(workspace, commit)
            reachable = reachable_cache[commit]
        entry["source_commit_reachable"] = reachable
        if use_git and head and reachable:
            if commit not in candidate_cache:
                candidate_cache[commit] = changed_paths(workspace, commit)
            candidates = candidate_cache[commit]
        else:
            candidates = None
        stale_sources = []
        noted_sources = []
        divergent = []
        for source in entry["sources"]:
            relative = source["path"]
            target = safe_path(workspace, relative)
            reason = None
            if target is None or not target.is_file():
                reason = "missing"
            elif not source["sha256"]:
                reason = "hash_missing"
            elif candidates is not None and relative not in candidates:
                reason = None
            else:
                digest = file_sha256(target)
                source["actual"] = digest
                if digest != source["sha256"]:
                    reason = "hash_mismatch"
            if reason:
                divergent.append({"path": relative, "reason": reason})
        missing = [item for item in divergent if item["reason"] == "missing"]
        mismatched = [item for item in divergent if item["reason"] != "missing"]
        if not entry["aggregate"]:
            stale_sources = divergent
        else:
            total = len(entry["sources"])
            ratio = (len(mismatched) / total) if total else 0.0
            if missing or ratio > aggregate_ratio:
                stale_sources = divergent
            else:
                noted_sources = mismatched
                stale_sources = missing
        entry["status"] = "stale" if stale_sources else "current"
        entry["stale_sources"] = stale_sources
        entry["noted_sources"] = noted_sources
        entry["divergent"] = divergent


def manifest_or_toplevel(workspace: Path, entries: list[dict], head: str | None) -> bool:
    if not head:
        return False
    commits = {entry["source_commit"] for entry in entries if entry.get("source_commit_reachable")}
    for commit in commits:
        names = changed_paths(workspace, commit)
        if any(is_manifest(name) for name in names):
            return True
        before = toplevel_dirs(workspace, commit)
        after = toplevel_dirs(workspace, "HEAD")
        if before != after:
            return True
        names = changed_paths(workspace, commit)
        head_dirs = toplevel_dirs(workspace, "HEAD")
        for name in names:
            if "/" not in name:
                continue
            first = name.split("/", 1)[0]
            if first not in head_dirs and first not in before:
                return True
    return False


def collect_unaudited(workspace: Path, entries: list[dict], head: str | None) -> list[str]:
    if not head:
        return []
    shas: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        commit = entry["source_commit"]
        if not entry.get("source_commit_reachable") or not commit:
            continue
        for sha in commits_since(workspace, commit):
            if sha not in seen:
                seen.add(sha)
                shas.append(sha)
    return unaudited_commits(workspace, shas)


def build_check(workspace: Path, resume: bool, user_requested_full: bool) -> dict:
    marker = knowledge_dir(workspace) / ".aidlc-memory"
    enabled, config = load_marker(marker)
    if not enabled:
        reason = "marker_disabled" if marker.is_file() else "marker_absent"
        return {
            "protocol_version": PROTOCOL_VERSION,
            "enabled": False,
            "mode": "disabled",
            "reasons": [reason],
        }
    stale_ratio = float(config.get("stale_ratio", DEFAULT_STALE_RATIO))
    aggregate_ratio = float(config.get("aggregate_ratio", DEFAULT_AGGREGATE_RATIO))
    max_streak = int(config.get("max_delta_streak", DEFAULT_DELTA_STREAK))
    budget = int(config.get("budget_tokens", DEFAULT_BUDGET_TOKENS))
    extensions = CODE_EXTENSIONS
    if isinstance(config.get("code_extensions"), list):
        extensions = {str(item).lower() if str(item).startswith(".") else f".{item}" for item in config["code_extensions"]}

    # aggregate ratio can be overridden per marker; apply before assess by temporarily
    # stashing it on the function via a local rewrite below.
    global_ratio = aggregate_ratio

    use_git = git_ok(workspace)
    head = git_head(workspace) if use_git else None
    entries, warnings = load_entries(workspace)
    assess_entries(workspace, entries, use_git, head, global_ratio)

    code_files = iter_code_files(workspace, extensions)
    uncovered = [path for path in code_files if not any(entry_claims(entry, path) for entry in entries)]
    known: set[str] = set()
    divergent_paths: set[str] = set()
    for entry in entries:
        for source in entry["sources"]:
            known.add(source["path"])
        for item in entry["divergent"]:
            divergent_paths.add(item["path"])
    uncovered_set = set(uncovered)
    denominator = len(known | uncovered_set)
    numerator = len(divergent_paths | uncovered_set)
    divergence_ratio = (numerator / denominator) if denominator else 0.0

    handoffs = load_handoffs(workspace)
    streak = delta_streak(handoffs)
    handoff_ok = latest_handoff_approved(handoffs) if entries else False
    structural = manifest_or_toplevel(workspace, entries, head) if entries else False
    missing_audits = collect_unaudited(workspace, entries, head) if entries else []
    estimate = load_estimate(workspace, budget)

    reasons: list[str] = []
    if user_requested_full:
        reasons.append("user_requested")
    if not entries and not code_files:
        if "user_requested" not in reasons:
            reasons.append("greenfield")
            mode = "skip"
        else:
            mode = "full"
    elif not entries:
        reasons.append("no_codekb")
        if uncovered:
            reasons.append("uncovered_files")
        mode = "full"
    else:
        unreachable = any(
            (not entry["source_commit"] or entry["source_commit"] == "unversioned" or not entry["source_commit_reachable"])
            for entry in entries
        )
        if use_git and head and unreachable:
            reasons.append("source_commit_absent_or_unreachable")
        if divergence_ratio > stale_ratio:
            reasons.append("divergence_over_threshold")
        if structural:
            reasons.append("manifest_or_toplevel")
        if not resume and streak >= max_streak:
            reasons.append("delta_streak")
        if missing_audits:
            reasons.append("unaudited_commits")
        if not resume and not handoff_ok:
            reasons.append("handoff_missing_or_unapproved")
        stale_entry = any(entry["status"] == "stale" for entry in entries)
        noted = any(entry["noted_sources"] for entry in entries)
        if stale_entry:
            reasons.append("stale_entries")
        if uncovered:
            reasons.append("uncovered_files")
        if divergent_paths and (noted or not stale_entry):
            reasons.append("divergent_sources")
        if any(reason in FORCE_FULL for reason in reasons):
            mode = "full"
        elif stale_entry or uncovered or divergent_paths:
            mode = "delta"
        else:
            reasons.append("clean")
            mode = "skip"

    if resume:
        reasons = [reason for reason in reasons if reason not in RESUME_SUPPRESSED]
        if mode == "full" and not any(reason in FORCE_FULL for reason in reasons):
            if any(reason in {"stale_entries", "uncovered_files", "divergent_sources"} for reason in reasons):
                mode = "delta"
            else:
                mode = "skip"
                if "clean" not in reasons:
                    reasons.append("clean")

    if estimate["within_budget"] is False:
        warnings.append("over_budget")
    if any(entry["noted_sources"] for entry in entries):
        warnings.append("aggregate_below_threshold")

    public_entries = []
    for entry in entries:
        public_entries.append({
            "path": entry["path"],
            "status": entry["status"],
            "aggregate": entry["aggregate"],
            "source_commit": entry["source_commit"],
            "source_commit_reachable": entry["source_commit_reachable"],
            "stale_sources": entry["stale_sources"],
            "noted_sources": entry["noted_sources"],
        })
    stale_sources = sorted(divergent_paths)
    report = {
        "protocol_version": PROTOCOL_VERSION,
        "enabled": True,
        "generated_at": now_iso(),
        "head": head,
        "git": bool(use_git and head),
        "mode": mode,
        "reasons": reasons,
        "warnings": warnings,
        "stale_ratio": stale_ratio,
        "divergence_ratio": round(divergence_ratio, 6),
        "entries": public_entries,
        "uncovered": uncovered,
        "stale_sources": stale_sources,
        "unaudited_commits": missing_audits,
        "delta_streak": streak,
        "load_estimate": estimate,
    }
    return report


def write_check_artifacts(workspace: Path, report: dict) -> None:
    if not report.get("enabled"):
        return
    code_dir = knowledge_dir(workspace) / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    target = code_dir / ".stale.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    append_event(workspace, {
        "event": "re_decision",
        "mode": report["mode"],
        "reasons": report["reasons"],
        "head": report.get("head"),
    })
    for path in report.get("stale_sources") or []:
        append_event(workspace, {"event": "stale_detected", "path": path, "reason": "stale"})
    for path in report.get("uncovered") or []:
        append_event(workspace, {"event": "stale_detected", "path": path, "reason": "uncovered"})


def format_summary(report: dict) -> str:
    if not report.get("enabled"):
        return (
            "# Memory check\n\n"
            "- **Enabled**: no\n"
            f"- **Mode**: {report['mode']}\n"
            f"- **Reasons**: {', '.join(report['reasons'])}\n\n"
            "Memory is off. Follow the workflow with no knowledge bundle and no OpenSpec tree.\n"
        )
    stale = ", ".join(report["stale_sources"]) or "(none)"
    uncovered = ", ".join(report["uncovered"]) or "(none)"
    reasons = ", ".join(report["reasons"]) or "(none)"
    tokens = report["load_estimate"]["estimated_tokens"]
    budget = report["load_estimate"]["budget_tokens"]
    return (
        "# Memory check\n\n"
        "- **Enabled**: yes\n"
        f"- **Mode**: {report['mode']}\n"
        f"- **HEAD**: {report.get('head') or '(none)'}\n"
        f"- **Reasons**: {reasons}\n"
        f"- **Stale sources**: {stale}\n"
        f"- **Uncovered**: {uncovered}\n"
        f"- **Divergence ratio**: {report['divergence_ratio']}\n"
        f"- **Load estimate**: {tokens} tokens (budget {budget})\n\n"
        "Do not compute hashes. Use this result. A human approves skip, delta, or full "
        "before Reverse Engineering.\n"
    )


def check_exit(report: dict) -> int:
    if report["mode"] in ("delta", "full"):
        return 1
    return 0


def resolve_entry(workspace: Path, entry_arg: str) -> Path:
    raw = Path(entry_arg)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(workspace / raw)
        candidates.append(knowledge_dir(workspace) / "code" / raw)
    root = workspace.resolve()
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(entry_arg)


def stamp_entry(workspace: Path, entry_arg: str) -> int:
    marker = knowledge_dir(workspace) / ".aidlc-memory"
    enabled, _config = load_marker(marker)
    if not enabled:
        print("memory extension is off", file=sys.stderr)
        return 2
    try:
        path = resolve_entry(workspace, entry_arg)
    except FileNotFoundError:
        print(f"entry not found: {entry_arg}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        print("entry has no frontmatter", file=sys.stderr)
        return 2
    meta = parse_yaml_subset(frontmatter)
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        print("entry has no sources", file=sys.stderr)
        return 1
    hashes: dict[str, str] = {}
    for source in sources:
        if not isinstance(source, dict):
            print("source entry is not a mapping", file=sys.stderr)
            return 1
        identity = source_identity(source)
        if not identity:
            print("source has no path", file=sys.stderr)
            return 1
        target = safe_path(workspace, identity)
        if target is None or not target.is_file():
            print(f"missing source: {identity}", file=sys.stderr)
            return 1
        hashes[identity] = file_sha256(target)
    use_git = git_ok(workspace)
    head = git_head(workspace) if use_git else None
    meta["source_commit"] = head if head else "unversioned"
    for source in sources:
        if not isinstance(source, dict):
            continue
        identity = source_identity(source)
        if identity in hashes:
            source["path"] = identity
            if not source.get("resource"):
                source["resource"] = identity
            source["sha256"] = hashes[identity]
    rendered = dump_frontmatter(meta) + body
    path.write_text(rendered.replace("\r\n", "\n"), encoding="utf-8")
    return 0


def emit(workspace: Path, event: str, fields: dict) -> int:
    marker = knowledge_dir(workspace) / ".aidlc-memory"
    enabled, _config = load_marker(marker)
    if not enabled:
        print("memory extension is off", file=sys.stderr)
        return 2
    append_event(workspace, {"event": event, **fields})
    return 0


MANUAL = """# Manual memory check

Use this when Python 3 or aidlc_memory.py is not available. Do not invent a hash.

1. If aidlc-docs/knowledge/.aidlc-memory does not exist, stop. Memory is off.
2. Read each aidlc-docs/knowledge/code/*.md frontmatter for source_commit, aggregate, and each source path (or resource) and sha256.
3. git rev-parse HEAD. For each distinct source_commit run git cat-file -e <commit>^{commit} and git merge-base --is-ancestor <commit> HEAD. If that fails, hash every source and treat the mode as full.
4. When the commit is an ancestor, list candidates with git diff --name-only --no-renames <commit> and git status --porcelain.
5. Hash a text file after deleting CR bytes: tr -d '\\r' < file | sha256sum. A mismatch or a missing file is stale. A new code file that no path and no covers entry claims is uncovered.
6. Apply the mode table in extensions/memory/memory-spec.md. Write aidlc-docs/knowledge/code/.stale.json.
7. Do not skip reverse engineering when the mode is delta or full. Ask the human, then record the Memory RE Decision audit block.

stamp by hand: recompute each source hash, write the hex into sha256, and set source_commit to git rev-parse HEAD only after every source file was present.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aidlc_memory.py", description="AI-DLC memory check and stamp")
    parser.add_argument("--workspace", default=".", help="Project root that contains aidlc-docs/")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Write .stale.json and choose skip, delta, or full")
    check.add_argument("--resume", action="store_true", help="In-progress cycle; do not force full for a missing handoff")
    check.add_argument("--user-requested-full", action="store_true")
    check.add_argument("--json", action="store_true", help="Print the result JSON on stdout")

    stamp = sub.add_parser("stamp", help="Rewrite source_commit and sha256 for one codekb entry")
    stamp.add_argument("entry", help="Path to the codekb markdown entry")

    emit_parser = sub.add_parser("emit", help="Append an archive or handoff event")
    emit_sub = emit_parser.add_subparsers(dest="emit_command", required=True)
    archive = emit_sub.add_parser("archive")
    archive.add_argument("--change-id", required=True)
    archive.add_argument("--result", required=True, choices=["applied", "blocked"])
    handoff = emit_sub.add_parser("handoff")
    handoff.add_argument("--cycle", required=True, type=int)
    handoff.add_argument("--approved", required=True, choices=["true", "false"])

    sub.add_parser("manual", help="Print the no-Python procedure")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace = Path(args.workspace).resolve()
    if args.command == "manual":
        print(MANUAL)
        return 0
    if args.command == "check":
        report = build_check(workspace, resume=args.resume, user_requested_full=args.user_requested_full)
        write_check_artifacts(workspace, report)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_summary(report))
        return check_exit(report)
    if args.command == "stamp":
        return stamp_entry(workspace, args.entry)
    if args.command == "emit":
        if args.emit_command == "archive":
            return emit(workspace, "archive", {"change_id": args.change_id, "result": args.result})
        approved = args.approved == "true"
        return emit(workspace, "handoff", {"cycle": args.cycle, "approved": approved})
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
