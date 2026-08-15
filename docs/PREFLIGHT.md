# GreenUTest preflight ladder

The experiment should move through these gates in order. None of the first four steps is a paper result.

## 0. Zero-GPU repository check

```powershell
python -m greenutest doctor
python -m unittest discover -s tests -v
python -m greenutest dry-run --output artifacts/dry-run
python scripts/verify_runlog.py artifacts/dry-run/runlog.jsonl
```

## 1. Fetch and verify ULT

```powershell
python scripts/fetch_benchmarks.py --name ult --dest external
python scripts/verify_upstream_checkouts.py --external external --name ult
```

The verifier checks both the pinned Git commit and the selected ULT/ULT_Lite Git blob identities.

## 2. NVML telemetry check

```powershell
pip install -e ".[dev,energy]"
python -m greenutest doctor --require-nvml
python scripts/sample_nvml.py --seconds 5
```

## 3. Single-model smoke

```powershell
pip install -e ".[dev,energy,analysis,local-hf]"
python -m greenutest model-smoke --model qwen25coder15b
```

Record the resolved model/tokenizer revisions. This is excluded pilot activity.

## 4. ULT_Lite generation-only bridge

```powershell
python -m greenutest ult-generation-pilot `
  --dataset external/UnLeakedTestBench/datasets/ULT_Lite.jsonl `
  --model qwen25coder15b `
  --max-tasks 4 `
  --measure-energy
```

This validates real data + real model + generated-token NLL + task-time NVML energy. All effectiveness outcomes are intentionally null, and evaluator reference tests are never accessed.

## 5. Only then enable real evaluation

After these gates, integrate/validate executable test evaluation, mutation/fault scoring, calibration-fit and policy-tuning. Freeze model revisions, quantization, benchmark hashes, prompts, split IDs, endpoints, margins and energy budgets before held-out execution.
