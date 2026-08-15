# GreenUTest preflight ladder

Move through these gates in order. Preflight/pilot outputs are not paper results.

## Gate 0 — zero-GPU repository integrity

```powershell
python -m greenutest doctor
python -m unittest discover -s tests -v
python -m greenutest dry-run --output artifacts/dry-run
python scripts/verify_runlog.py artifacts/dry-run/runlog.jsonl
python -m greenutest inspect-model-plan
```

## Gate 1 — core benchmark provenance

```powershell
python scripts/fetch_benchmarks.py --name ult --dest external
python scripts/fetch_benchmarks.py --name testgeneval --dest external
python scripts/fetch_benchmarks.py --name testexplora --dest external
python scripts/fetch_benchmarks.py --name swe_mutation --dest external
python scripts/verify_upstream_checkouts.py --external external
```

ULT verification covers `ULT.jsonl`, `ULT_Lite.jsonl`, and `PLT.jsonl`. Separately downloaded Hugging Face/TestExplora dataset artifacts must receive a content/snapshot hash before freeze.

## Gate 2 — NVML telemetry

```powershell
pip install -e ".[dev,energy]"
python -m greenutest doctor --require-nvml
python scripts/sample_nvml.py --seconds 5
```

Check stable timestamps/power readings and archive GPU identity.

## Gate 3 — cheap local model smoke

```powershell
pip install -e ".[dev,analysis,energy,local-hf]"
python -m greenutest model-smoke --model qwen25coder15b
```

Record the resolved model/tokenizer Hub commits. Repeat for `qwen25coder7b`, then only scale to Qwen3 tiers after the cheap/strong path is stable.

## Gate 4 — ULT_Lite generation-only bridge

```powershell
python -m greenutest ult-generation-pilot `
  --dataset external/UnLeakedTestBench/datasets/ULT_Lite.jsonl `
  --benchmark ult `
  --model qwen25coder15b `
  --max-tasks 4 `
  --measure-energy
```

All effectiveness outcomes remain null. This validates real data + real model + NLL telemetry + task-time local energy without using evaluator references.

## Gate 5 — PLT leakage diagnostic bridge

```powershell
python -m greenutest ult-generation-pilot `
  --dataset external/UnLeakedTestBench/datasets/PLT.jsonl `
  --benchmark plt `
  --model qwen25coder15b `
  --max-tasks 4 `
  --measure-energy
```

PLT's evaluator tests remain excluded from generator context even though PLT is intentionally contamination-prone.

## Gate 6 — hosted frontier smoke

```powershell
pip install -e ".[dev,remote-api]"
python -m greenutest api-smoke --model gpt56sol
python -m greenutest api-smoke --model claudesonnet5
python -m greenutest api-smoke --model gemini36flash
```

Confirm response text, canonical model metadata, token usage and latency logging. Do not estimate provider-side energy.

## Gate 7 — evaluation engines

Validate one tiny deterministic slice of each evaluation path before scaling:

1. ULT execution/coverage/mutation reconciliation;
2. TestGenEvalLite Docker pipeline, then full TestGenEval availability;
3. TestExplora buggy/fixed Fail-to-Pass evaluator with fix hints kept evaluator-side;
4. SWE-Mutation Pass@1/VRR/RDR scoring;
5. optional BugsInPy environment reproduction.

## Gate 8 — pilot model matrix

Run excluded pilot slices across:

- Qwen2.5-Coder 1.5B and 7B first;
- Qwen3-Coder-30B-A3B and Qwen3-Coder-Next next;
- GPT-5.6 Sol / Claude Sonnet 5 / Gemini 3.6 Flash after hosted telemetry is stable.

Use pilot data only to freeze feasible quantization, prompts, calibration model, uncertainty acquisition costs, VoI thresholds, margins and budgets.

## Gate 9 — freeze

Before held-out execution freeze/hash:

- code SHA;
- model IDs/revisions/quantization and provider IDs;
- benchmark revisions + external dataset snapshot hashes;
- group-disjoint task splits;
- prompt hashes;
- calibration/routing/VoI configuration;
- confirmatory endpoints and non-inferiority margin;
- local energy budgets and API resource reporting plan;
- retry/missingness rules.

## Gate 10 — held-out run

No tuning after unblinding. Stop on revision mismatch, data leakage, hidden retry behavior, unexplained energy-meter discontinuity, or any row that cannot be reconstructed from archived provenance.
