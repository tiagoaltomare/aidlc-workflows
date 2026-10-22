#!/usr/bin/env python3
"""Summarize trials.jsonl: median, paired 95% interval, pass^k, and 3/n.

Failures are listed on their own so a person can read them. The interval is a
percentile bootstrap of the paired median (baseline minus extension). A
positive median means the extension used less of that metric.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("median of an empty sample")
    ordered = sorted(values)
    count = len(ordered)
    mid = count // 2
    if count % 2:
        return float(ordered[mid])
    return float(ordered[mid - 1] + ordered[mid]) / 2.0


def pass_at_k(successes: int, total: int, k: int) -> float:
    if k <= 0 or total <= 0 or k > total or successes < k:
        return 0.0
    return math.comb(successes, k) / math.comb(total, k)


def rule_of_three(failures: int, total: int) -> float | None:
    """Upper failure rate at about 95% confidence when no failures were seen."""
    if total <= 0:
        raise ValueError("rule of three needs a positive sample")
    if failures != 0:
        return None
    return 3.0 / total


def paired_median_ci(
    baseline: list[float],
    extension: list[float],
    n_boot: int = 2000,
    seed: int = 0,
) -> dict:
    if len(baseline) != len(extension) or not baseline:
        raise ValueError("paired samples must be non-empty and the same length")
    deltas = [base - other for base, other in zip(baseline, extension)]
    rng = random.Random(seed)
    count = len(deltas)
    samples = []
    for _ in range(n_boot):
        draw = [deltas[rng.randrange(count)] for _ in range(count)]
        samples.append(median(draw))
    samples.sort()
    low_index = int(0.025 * n_boot)
    high_index = min(n_boot - 1, int(0.975 * n_boot))
    return {
        "median_delta": median(deltas),
        "low": samples[low_index],
        "high": samples[high_index],
        "pairs": count,
    }


def median_reduction(baseline: list[float], extension: list[float]) -> float:
    percents = [(base - other) / base for base, other in zip(baseline, extension) if base > 0]
    if not percents:
        return 0.0
    return median(percents)


def load_trials(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def pair_metric(rows: list[dict], metric: str, cycles: set[int]) -> tuple[list[float], list[float]]:
    grouped: dict[tuple[int, int], dict[str, float]] = {}
    for row in rows:
        if row.get("cycle") not in cycles:
            continue
        value = row.get(metric)
        if not isinstance(value, (int, float)):
            continue
        key = (int(row["repetition"]), int(row["cycle"]))
        grouped.setdefault(key, {})[row["arm"]] = float(value)
    baseline = []
    extension = []
    for key in sorted(grouped):
        arms = grouped[key]
        if "upstream" in arms and "extension" in arms:
            baseline.append(arms["upstream"])
            extension.append(arms["extension"])
    return baseline, extension


def failures_of(rows: list[dict]) -> list[dict]:
    found = []
    for row in rows:
        failed = row.get("passed") is False or row.get("status") in {"fail", "error"}
        if failed:
            found.append({
                "repetition": row.get("repetition"),
                "arm": row.get("arm"),
                "cycle": row.get("cycle"),
                "status": row.get("status"),
                "reason": row.get("reason"),
            })
    return found


def summarize(rows: list[dict], metric: str = "tokens_in", cycles: tuple[int, ...] = (2, 3)) -> dict:
    baseline, extension = pair_metric(rows, metric, set(cycles))
    summary = {
        "metric": metric,
        "cycles": list(cycles),
        "failures": failures_of(rows),
    }
    if baseline:
        interval = paired_median_ci(baseline, extension)
        summary["paired"] = interval
        summary["median_reduction"] = median_reduction(baseline, extension)
        summary["reduction_ci_above_zero"] = interval["low"] > 0
    else:
        summary["paired"] = None
        summary["median_reduction"] = None
        summary["reduction_ci_above_zero"] = None
    decided = [row for row in rows if row.get("passed") is not None]
    successes = sum(1 for row in decided if row.get("passed") is True)
    summary["pass_at_1"] = pass_at_k(successes, len(decided), 1) if decided else None
    summary["pass_at_3"] = pass_at_k(successes, len(decided), 3) if decided else None
    failure_count = sum(1 for row in decided if row.get("passed") is not True)
    summary["rule_of_three"] = rule_of_three(failure_count, len(decided)) if decided else None
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize trials.jsonl")
    parser.add_argument("--trials", required=True)
    parser.add_argument("--metric", default="tokens_in")
    args = parser.parse_args(argv)
    summary = summarize(load_trials(Path(args.trials)), args.metric)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
