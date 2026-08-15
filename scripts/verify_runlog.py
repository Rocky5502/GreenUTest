#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = {
    "run_id", "task_id", "benchmark", "partition", "policy", "seed",
    "candidate", "evidence", "actions", "outcomes", "energy", "status"
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("runlog")
    args = p.parse_args()
    path = Path(args.runlog)
    count = 0
    errors: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        count += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {i}: invalid JSON: {exc}")
            continue
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"line {i}: missing {missing}")
        if row.get("partition") == "heldout_final" and row.get("analysis_plan_hash") in (None, "", "TBD"):
            errors.append(f"line {i}: held-out row lacks frozen analysis_plan_hash")
    if errors:
        print("\n".join(errors))
        return 2
    print(f"OK: {count} runlog records validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
