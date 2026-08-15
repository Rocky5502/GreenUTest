from __future__ import annotations
import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path
from . import __version__
from .runner import run_toy


def doctor(require_nvml: bool = False) -> int:
    rows = {
        "greenutest": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "nvidia_smi": shutil.which("nvidia-smi") is not None,
        "pynvml": importlib.util.find_spec("pynvml") is not None,
        "torch": importlib.util.find_spec("torch") is not None,
        "transformers": importlib.util.find_spec("transformers") is not None,
    }
    print(json.dumps(rows, indent=2))
    if require_nvml and not rows["pynvml"]:
        print("NVML Python bindings missing. Install with: pip install -e '.[energy]'", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="greenutest")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_doc = sub.add_parser("doctor", help="Inspect local prerequisites without downloading anything")
    p_doc.add_argument("--require-nvml", action="store_true")

    p_dry = sub.add_parser("dry-run", help="Run deterministic toy orchestration; no external code/GPU")
    p_dry.add_argument("--output", default="artifacts/dry-run")
    p_dry.add_argument("--seed", type=int, default=20260815)

    sub.add_parser("inspect-manifest", help="Print benchmark upstream manifest")

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor(args.require_nvml)
    if args.command == "dry-run":
        path = run_toy(args.output, seed=args.seed)
        print(path)
        return 0
    if args.command == "inspect-manifest":
        root = Path(__file__).resolve().parents[2]
        print((root / "data" / "upstreams.json").read_text(encoding="utf-8"))
        return 0
    return 1
