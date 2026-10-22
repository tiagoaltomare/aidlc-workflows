#!/bin/sh
# Fail when merging a ref produces a conflict outside the hook allowlist.
# Usage: merge_check.sh <repo> <allowlist> <ref> [ref...]
set -eu

if [ "$#" -lt 3 ]; then
  echo "usage: merge_check.sh <repo> <allowlist> <ref>..." >&2
  exit 2
fi

repo=$(CDPATH= cd "$1" && pwd)
allowlist=$2
shift 2

if [ ! -f "$allowlist" ]; then
  echo "allowlist not found: $allowlist" >&2
  exit 2
fi

tmp=$(mktemp -d)
cleanup() {
  git -C "$repo" worktree remove --force "$tmp" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT

git -C "$repo" worktree add --detach "$tmp" HEAD >/dev/null

for ref in "$@"; do
  git -C "$tmp" merge --no-commit --no-ff "$ref" >/dev/null 2>"$tmp/merge.err" || true
  git -C "$tmp" diff --name-only --diff-filter=U > "$tmp/conflicts" || true
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    if ! grep -Fxq "$path" "$allowlist"; then
      echo "conflict outside allowlist: $path (ref $ref)" >&2
      echo "$path" >> "$tmp/bad"
    fi
  done < "$tmp/conflicts"
  git -C "$tmp" merge --abort >/dev/null 2>&1 || git -C "$tmp" reset --hard HEAD >/dev/null
done

if [ -f "$tmp/bad" ]; then
  exit 1
fi
exit 0
