# GreenUTest framework design

## Design principle

The diagram is intentionally a **decision system**, not a conventional left-to-right “LLM generates tests” pipeline. The visual distinction should make three scientific ideas obvious:

1. evidence is acquired **cheap-first**;
2. uncertainty is **calibrated into reliability risk**, not reported as raw confidence;
3. the policy can decline to purchase more evidence when the expected value-of-information is lower than its energy cost.

## Logical layers

### Layer A — task and generation
A benchmark adapter normalizes a software-testing task and feeds the cheapest eligible model tier.

### Layer B — evidence acquisition
Cheap signals are acquired first: static code risk, lexical uncertainty when available, and first execution status. Conditional signals include behavioral disagreement, independent-oracle checks, or stronger/multi-sample evidence.

### Layer C — risk and VoI
A calibration/fusion model estimates a task/test reliability risk. Before an expensive signal is acquired, the VoI gate estimates whether the expected improvement in downstream action utility exceeds its energy penalty.

### Layer D — action routing
The policy chooses a supported action: accept/execute, verify, repair, regenerate, escalate, or abstain.

### Layer E — evaluation and telemetry
Testing effectiveness and direct energy are measured jointly. Raw task-level records preserve uncertainty evidence, action trace, test outcomes, and phase-attributed energy.

## Figure source

`assets/greenutest_framework.svg` is a standalone vector figure designed for README/docs use and later export. Its visual hierarchy deliberately uses restrained academic colors, grouped modules, and explicit feedback arrows.


---

# Dataset and benchmark protocol

## No benchmark mirroring

The repository stores only adapters and source manifests. Raw benchmark content is fetched into the Git-ignored `external/` directory.

## ULT / UnLeakedTestBench

Role: primary function-level generation and calibration benchmark.

Adapter expectations:

- retain upstream task IDs;
- capture repository/source metadata where available;
- never infer oracle correctness from “generated test passes” alone;
- preserve the upstream benchmark's contamination controls;
- run `ULT_Lite` first during integration before the full benchmark.

## BugsInPy

Role: real-fault detection and false-validation analysis.

For each bug we need a reproducible buggy/fixed pair. Environment/setup failure is a separate status from model/test failure.

A candidate test can support fault detection when it distinguishes the buggy version from the fixed/reference version under the benchmark contract.

## SWE-Mutation

Role: stress test of discriminative test-suite power using challenging mutants.

Do not silently treat its mutation concept as interchangeable with conventional first-order mutation. Preserve benchmark-specific labels and metrics in the raw records.

## TestGenEvalLite

Role: optional repository/file-level robustness extension.

It is deliberately optional because its Docker/image and upstream licensing requirements are heavier. Integrate only after the core function-level and real-fault experiments reproduce reliably.

## Split policy

The same stable task IDs must be used across model/policy comparisons. Split into:

- pilot;
- calibration-fit;
- policy-tuning;
- held-out final.

Group by repository/project where metadata permit. The held-out task list is hashed before unblinding.


---

# Baseline matrix

GreenUTest should be compared against **compute allocation strategies**, not merely different model names.

| Baseline | Purpose | What must be matched/controlled |
|---|---|---|
| small model only | efficiency floor | task/prompt/seed |
| strong model only | quality-first upper compute reference | task/prompt/seed |
| fixed self-consistency | fixed expensive uncertainty/computation | sample count |
| random routing | tests whether learned/risk routing beats arbitrary escalation | match escalation rate |
| raw-confidence routing | tests calibration contribution | same generator/action set |
| static complexity routing | SE heuristic control | same escalation budget |
| STARouter-style | internal/state-feature model routing concept | clearly label clean-room implementation |
| fixed agentic feedback | fixed rounds of execution/coverage feedback | same max rounds/tool access |
| specification-first | independent oracle before implementation-coupled validation | same oracle source availability |
| traditional non-LLM | classical test generation control | benchmark compatibility/time budget |
| GreenUTest | calibrated risk + VoI + energy-aware action routing | full method |

## GreenUTest ablations

At minimum:

- no calibration;
- no VoI gate;
- no oracle uncertainty;
- no behavioral uncertainty;
- no independent-oracle check;
- no abstention;
- no energy penalty.

## Fairness rules

1. Baselines must receive the same task context unless the original method requires a clearly documented difference.
2. Match seeds/task ordering when stochastic execution permits.
3. Random-routing comparisons must match GreenUTest's observed escalation rate or matched energy budget, not an arbitrary rate chosen after results are seen.
4. API models are excluded from direct provider-side energy comparisons unless verifiable provider telemetry is available.
5. Report unsupported baseline/benchmark combinations as **N/A**, not zero.


---

# Direct energy measurement protocol

## Primary measurement

For local NVIDIA GPU inference, sample instantaneous board power through NVML with monotonic timestamps and numerically integrate energy with the trapezoidal rule:

`E_joules = Σ 0.5 * (P_i + P_{i+1}) * (t_{i+1} - t_i)`

`Wh = J / 3600`

## Pilot requirements

- validate a stable sampling interval; target 100 ms or faster only when measurement overhead remains negligible;
- confirm timestamps are monotonic;
- confirm run-level integrated energy approximately equals the sum of phase-level energy;
- record idle power before/after blocks;
- repeat identical tasks to estimate measurement variation;
- interleave/randomize policy order within compatible blocks;
- separate model-load/warm-up from task-time inference.

## Phase tags

- `model_load_warmup`
- `prefill`
- `decoding`
- `uncertainty_acquisition`
- `test_execution`
- `verification`
- `repair_regeneration`
- `mutation_coverage_evaluation`

## Reporting

Primary: raw directly measured GPU Wh/J.

Sensitivity: idle-adjusted GPU energy when the idle estimate is stable enough to justify subtraction.

Optional: physical wall-meter cross-check for whole-system energy.

Do not invent API-provider energy estimates.


---

# Reproducibility contract

A full run is not publication-ready unless the following can be recovered:

- repository commit SHA;
- analysis-plan hash;
- partition/task-list hash;
- benchmark URL + pinned revision + selected file checksum;
- model ID + revision + tokenizer revision + quantization;
- prompt/template revision;
- random seed;
- operating system and Python version;
- GPU/driver/CUDA/PyTorch/Transformers versions;
- dedicated VRAM reported by the runtime;
- energy sampling backend and interval;
- policy config hash;
- raw task-level runlog;
- generated test content hash (and archived content when license permits);
- evaluation tool versions;
- explicit environment/setup failures.

## Data-to-paper rule

No scientific number should be manually typed into a paper table. Paper-facing tables/plots must be generated from archived task-level records by versioned code.


---

# Windows local setup

Recommended path: native Python + PowerShell for local-model inference; WSL2/Docker may be preferable for Linux-native benchmark environments such as BugsInPy/TestGenEval.

## Phase 0 — no GPU use

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m greenutest doctor
python -m greenutest dry-run --output artifacts/dry-run
python -m unittest discover -s tests -v
```

## Phase 1 — telemetry only

```powershell
pip install -e ".[dev,energy]"
python -m greenutest doctor --require-nvml
python scripts/sample_nvml.py --seconds 5
```

Do this before installing/downloading models. Confirm the GPU name and dedicated VRAM from `nvidia-smi`/NVML.

## Phase 2 — local model stack

```powershell
pip install -e ".[dev,energy,analysis,local-hf]"
python -m greenutest doctor --require-nvml
```

Freeze exact Torch/CUDA compatibility only after checking the installed NVIDIA driver. Do not blindly copy a CUDA wheel command from another machine.

## Phase 3 — benchmark environments

Use benchmark-provided Docker/Conda environments where practical. Keep benchmark checkouts under `external/`, never in the package source tree.


---

# Experiment protocol

## Stage A — harness verification

Pass all unit tests and the toy dry-run. No model downloads.

## Stage B — energy instrumentation pilot

Validate NVML sampling, phase attribution, idle baseline, and repeated-run variance using a tiny deterministic workload.

## Stage C — benchmark-adapter pilot

Integrate `ULT_Lite`, then a very small reproducible BugsInPy subset. Audit TestExplora as a secondary proactive Fail-to-Pass benchmark before enabling it. Verify task identity, environment status, generated-test archive, coverage/mutation reconciliation, and false-validation labeling logic.

## Stage D — model pilot

Run a small excluded pilot across the candidate local model tiers. Freeze:

- model revisions/quantization;
- prompt version;
- calibration candidates;
- uncertainty acquisition costs;
- candidate non-inferiority margin;
- matched energy budgets;
- VoI energy coefficient/threshold.

## Stage E — freeze

Create `configs/frozen/confirmatory.lock.json`, hash it, freeze held-out task IDs, and record the code commit.

## Stage F — held-out run

No threshold changes. Failures caused by infrastructure are reported separately and handled according to the predeclared missingness/retry policy.


---

# Results policy

Before held-out unblinding:

- plots/tables may use toy data only and must be labeled toy/synthetic;
- pilot data may guide instrumentation and frozen design choices but must never enter confirmatory tables;
- no cherry-picking model tiers, thresholds, datasets, or budgets based on final outcomes.

After held-out unblinding:

- preserve the frozen analysis plan;
- generate result tables from task-level logs;
- keep confirmatory and exploratory results separate;
- report failures and N/A combinations transparently;
- report effect sizes and confidence intervals beside significance tests.

---

## Pre-scale pilot gate

The full GPU matrix must not begin until the following are true: environment/GPU identity is archived; NVML power integration passes sanity checks; benchmark revisions and split hashes are frozen; model/tokenizer revisions and prompt hash are recorded; labels separate execution validity, oracle validity, false validation and fault detection; partitions are group-disjoint where possible; retry behavior never silently erases model failures; and confirmatory endpoints/budgets are frozen before held-out execution.

Stop scaling on unexplained power-meter discontinuity, partition leakage, revision mismatch, hidden retry behavior, or any task result that cannot be reconstructed from archived metadata.

## Baseline provenance rule

GreenUTest distinguishes direct controls, clean-room *style* baselines, and optional upstream reproductions. `STARouter-style` is a clean-room state-routing control, not a source-code reproduction claim. `fixed-agentic-feedback` is a fixed-depth execution/coverage-feedback control, not copied TestForge source. Any upstream implementation must be separately pinned and license-reviewed. Traditional non-LLM generation is exposed as an adapter and should use a pinned compatible tool such as Pynguin only where benchmark semantics permit.


## Dataset integrity and leakage firewall

- ULT reference/evaluator tests must never enter generation prompts, retrieval corpora, task metadata passed to model backends, or routing features.
- TestExplora defect-fix patches/hints are evaluator-side unless a specifically named hinted condition is being studied; the main GreenUTest condition uses the benchmark's non-leaking setup.
- Any dataset artifact not fully determined by a Git commit (for example an externally downloaded JSON/Hugging Face snapshot) must be hashed and recorded in the frozen run manifest.
- Benchmark repositories are checked out at the commits in `data/upstreams.json` by default. Floating HEAD is forbidden for confirmatory execution.

## Model-pair design

The principal local routing pair should, if the excluded hardware pilot confirms feasibility, use Qwen2.5-Coder-1.5B-Instruct as the cheap tier and Qwen2.5-Coder-7B-Instruct as the stronger tier. This same-family comparison reduces architecture/training-family confounding while creating a meaningful compute gap. Mistral-7B-Instruct-v0.3 is retained as a cross-family robustness condition rather than the default cheap tier. Exact revisions and quantization are frozen after the pilot.

## Routing controls

In addition to STARouter-style state routing, include a clean-room temporal routing control that buys a fixed amount of cheap exploration before deciding whether to escalate. This is inspired by recent trajectory/value-routing work but is not presented as an upstream reproduction. All exploratory turns are charged to its energy/time budget.

## Lexical uncertainty acquisition contract

For local Hugging Face models, GreenUTest records mean generated-token negative log-likelihood directly from generation logits. The raw confidence control is the geometric mean generated-token probability, `exp(-mean_NLL)`, and is explicitly treated as uncalibrated. Prompt SHA-256, prompt/generated token counts, requested model revision, and resolved model/tokenizer Hub commit hashes are recorded with each candidate. The excluded pilot may resolve a floating model snapshot; confirmatory execution refuses unresolved model revisions.

Sampling parameters are part of the frozen configuration. Multi-sample/semantic uncertainty must use distinct predeclared seeds and charge every generation to the corresponding policy.
