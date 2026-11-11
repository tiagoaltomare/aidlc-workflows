"""CLI: python3 -m aidlc_validate CHECK --root PRODUCT_REPO"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from aidlc_validate import checks

CheckFn = Callable[[Path], list[str]]

CHECK_FNS: dict[str, CheckFn] = {
    "config": checks.check_config,
    "units-dag": checks.check_units_dag,
    "traceability": checks.check_traceability,
    "scope-in-vision": checks.check_scope_in_vision,
    "export": checks.check_export,
    "stories": checks.check_stories,
    "assumptions": checks.check_assumptions,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aidlc_validate",
        description="Run one deterministic AI-DLC artifact check.",
    )
    parser.add_argument("check", choices=sorted(CHECK_FNS))
    parser.add_argument(
        "--root",
        required=True,
        help="Product repository root (directory that contains aidlc.config.yaml)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: product root does not exist: {root}", file=sys.stderr)
        return 2
    errors = CHECK_FNS[args.check](root)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"{args.check}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
