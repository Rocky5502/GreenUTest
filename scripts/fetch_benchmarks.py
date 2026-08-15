#!/usr/bin/env python3
"""Fetch benchmark source repositories without mirroring them into GreenUTest."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "upstreams.json"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--name", choices=["ult", "bugsinpy", "swe_mutation", "testgeneval", "testexplora"])
    p.add_argument("--dest", default="external")
    p.add_argument("--list", action="store_true")
    p.add_argument("--revision", help="Explicit commit/tag override. By default the manifest pinned_commit is used.")
    p.add_argument("--floating", action="store_true", help="Use upstream default branch HEAD (exploratory only; never confirmatory).")
    args = p.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    if args.list:
        for name, spec in manifest.items():
            print(f"{name:14} {spec['repo']}")
        return 0
    if not args.name:
        p.error("--name is required unless --list is used")

    spec = manifest[args.name]
    dest_root = Path(args.dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    target = dest_root / Path(spec["repo"]).stem.replace(".git", "")
    if target.exists():
        print(f"Already exists: {target}. Refusing to modify an existing checkout.")
        return 2

    run(["git", "clone", "--filter=blob:none", spec["repo"], str(target)])
    revision = args.revision or (None if args.floating else spec.get("pinned_commit"))
    if revision:
        run(["git", "checkout", "--detach", revision], cwd=target)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=target, text=True).strip()
    expected = None if args.floating else spec.get("pinned_commit")
    if expected and sha != expected:
        raise RuntimeError(f"Checkout mismatch for {args.name}: expected {expected}, got {sha}")
    label = "Floating checkout" if args.floating else "Pinned checkout"
    print(f"{label}: {target} @ {sha}")
    print("Review the upstream license and README before executing or redistributing any asset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
