from __future__ import annotations
import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path
from . import __version__
from .runner import run_toy, run_ult_generation_pilot
from .harness import ToyAdapter, build_local_model_from_config


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
    p_models = sub.add_parser("inspect-model-plan", help="Print configured local model tiers without loading weights")
    p_models.add_argument("--config", default="configs/experiment.json")
    p_smoke = sub.add_parser("model-smoke", help="Load one configured local model and generate one toy test; this may use GPU")
    p_smoke.add_argument("--config", default="configs/experiment.json")
    p_smoke.add_argument("--model", default="qwen25coder15b")
    p_smoke.add_argument("--seed", type=int, default=20260815)
    p_ult = sub.add_parser("ult-generation-pilot", help="Run excluded ULT generation-only preflight; loads a real model and may use GPU")
    p_ult.add_argument("--config", default="configs/experiment.json")
    p_ult.add_argument("--dataset", required=True, help="Path to pinned ULT/ULT_Lite file")
    p_ult.add_argument("--model", default="qwen25coder15b")
    p_ult.add_argument("--output", default="artifacts/ult-generation-pilot")
    p_ult.add_argument("--max-tasks", type=int, default=4)
    p_ult.add_argument("--seed", type=int, default=20260815)
    p_ult.add_argument("--measure-energy", action="store_true")
    p_ult.add_argument("--device-index", type=int, default=0)
    p_ult.add_argument("--sampling-interval-ms", type=int, default=100)

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
    if args.command == "inspect-model-plan":
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        rows = {}
        for key, model in cfg["models"].items():
            rows[key] = {"id": model["id"], "role": model.get("role"), "revision": model.get("revision"), "quantization": model.get("quantization"), "do_sample": model.get("do_sample"), "temperature": model.get("temperature"), "top_p": model.get("top_p")}
        print(json.dumps(rows, indent=2))
        return 0
    if args.command == "model-smoke":
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if args.model not in cfg["models"]:
            print(f"Unknown model key: {args.model}", file=sys.stderr)
            return 2
        backend = build_local_model_from_config(cfg["models"][args.model], allow_unpinned=True)
        task = next(iter(ToyAdapter().tasks()))
        candidate = backend.generate(task, seed=args.seed)
        print(json.dumps({"model_key": args.model, "model_id": candidate.model_id, "task_id": task.task_id, "raw_confidence": candidate.raw_confidence, "token_nll": candidate.token_nll, "metadata": candidate.metadata, "preview": candidate.text[:500], "warning": "Exploratory smoke only. Pin resolved model/tokenizer revisions before confirmatory execution."}, indent=2))
        return 0
    if args.command == "ult-generation-pilot":
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if args.model not in cfg["models"]:
            print(f"Unknown model key: {args.model}", file=sys.stderr)
            return 2
        path = run_ult_generation_pilot(
            args.dataset, cfg["models"][args.model], args.output,
            max_tasks=args.max_tasks, seed=args.seed, measure_energy=args.measure_energy,
            device_index=args.device_index, sampling_interval_ms=args.sampling_interval_ms,
        )
        print(path)
        return 0
    return 1
