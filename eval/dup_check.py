#!/usr/bin/env python3
"""Flag requirement paragraphs that repeat a spec paragraph.

Comparison is 5-word shingles and Jaccard. A score above 0.5 is a duplicated
passage. Short references that share fewer than five words are ignored.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


def shingles(words: list[str], size: int = 5) -> set[tuple[str, ...]]:
    if len(words) < size:
        return set()
    return {tuple(words[index:index + size]) for index in range(len(words) - size + 1)}


def jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def paragraphs(text: str) -> list[str]:
    without_fences = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return [part.strip() for part in re.split(r"\n\s*\n", without_fences) if part.strip()]


def compare_texts(requirements: str, spec: str, threshold: float = 0.5) -> list[dict]:
    hits = []
    spec_parts = [(index, shingles(tokens(part))) for index, part in enumerate(paragraphs(spec))]
    for req_index, part in enumerate(paragraphs(requirements)):
        req_shingles = shingles(tokens(part))
        if not req_shingles:
            continue
        for spec_index, spec_shingles in spec_parts:
            if not spec_shingles:
                continue
            score = jaccard(req_shingles, spec_shingles)
            if score > threshold:
                hits.append({
                    "requirement_paragraph": req_index,
                    "spec_paragraph": spec_index,
                    "jaccard": round(score, 4),
                })
    return hits


def compare_files(requirement_paths: list[Path], spec_paths: list[Path], threshold: float) -> list[dict]:
    hits = []
    for requirement in requirement_paths:
        req_text = requirement.read_text(encoding="utf-8", errors="replace")
        for spec in spec_paths:
            for hit in compare_texts(req_text, spec.read_text(encoding="utf-8", errors="replace"), threshold):
                hits.append({"requirements": str(requirement), "spec": str(spec), **hit})
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect duplicated spec text inside requirements")
    parser.add_argument("--requirements", nargs="+", required=True)
    parser.add_argument("--specs", nargs="+", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args(argv)
    hits = compare_files(
        [Path(path) for path in args.requirements],
        [Path(path) for path in args.specs],
        args.threshold,
    )
    print(json.dumps({"hits": hits, "ok": not hits}, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
