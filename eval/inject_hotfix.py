#!/usr/bin/env python3
"""Inject a commit made outside AI-DLC: content edit, rename, or CRLF rewrite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

MESSAGE = "hotfix: injected outside AI-DLC"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def commit(repo: Path, message: str) -> str:
    identity: list[str] = []
    configured = git(repo, "config", "user.email")
    if configured.returncode != 0 or not configured.stdout.strip():
        identity = ["-c", "user.email=memory-test@example.com", "-c", "user.name=Memory Test"]
    added = git(repo, "add", "-A")
    if added.returncode != 0:
        raise RuntimeError(added.stderr.strip())
    result = git(repo, *identity, "commit", "-m", message)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    head = git(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        raise RuntimeError(head.stderr.strip())
    return head.stdout.strip()


def inject(repo: Path, kind: str, path: str) -> str:
    target = repo / path
    if kind == "content":
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = target.read_text(encoding="utf-8") if target.is_file() else ""
        target.write_text(previous + "\n# hotfix outside AI-DLC\n", encoding="utf-8")
    elif kind == "rename":
        if not target.is_file():
            raise FileNotFoundError(path)
        destination = target.with_name(target.stem + "-renamed" + target.suffix)
        moved = git(repo, "mv", path, destination.relative_to(repo).as_posix())
        if moved.returncode != 0:
            raise RuntimeError(moved.stderr.strip())
    elif kind == "crlf":
        if not target.is_file():
            raise FileNotFoundError(path)
        text = target.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        target.write_bytes(text.replace(b"\n", b"\r\n"))
    else:
        raise ValueError(f"unknown kind {kind}")
    return commit(repo, MESSAGE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inject an out-of-workflow hotfix commit")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--kind", required=True, choices=["content", "rename", "crlf"])
    parser.add_argument("--path", default="src/app.py")
    args = parser.parse_args(argv)
    sha = inject(Path(args.repo).resolve(), args.kind, args.path)
    print(sha)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
