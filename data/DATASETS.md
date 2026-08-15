# Dataset plan and provenance

GreenUTest uses **four core benchmarks** plus contamination/pilot/external-validity diagnostics. This directory stores metadata, schemas, pins, and split manifests—not mirrored third-party corpora. Exact Git revisions are frozen in `upstreams.json`; external dataset snapshots that are not fully determined by Git must be hashed before the confirmatory freeze.

## Final hierarchy

| Priority | Benchmark | Scientific role | Primary endpoints | Public-repo policy |
|---|---|---|---|---|
| **P0** | **ULT / UnLeakedTestBench** | RQ1 uncertainty/calibration + function-level RQ2 efficiency | AUROC/AUPRC, ECE/Brier, validity, coverage, mutation, energy | pinned upstream; reference tests evaluator-only |
| **P0** | **TestGenEval (full)** | RQ2 realistic test effectiveness | pass, coverage, mutation, quality-at-budget/non-inferiority | pinned harness; full HF dataset external + hashed |
| **P0** | **TestExplora** | RQ3 proactive real-bug discovery | Fail-to-Pass, false validation, fault discovery | pinned harness; benchmark JSON/testbeds external + hashed |
| **P0** | **SWE-Mutation** | RQ3 discriminative reliability | Pass@1, VRR, RDR / realistic mutant detection | pinned upstream; curated mutation data external checkout |
| Diagnostic | **PLT / PreLeakedTestbench** | contamination/memorization-vs-reasoning analysis paired with ULT | calibration/confidence/performance inflation | same pinned ULT repo; evaluator references never enter generation context |
| Pilot | **TestGenEvalLite** | fast Docker/integration debugging before full TestGenEval | smoke/pipeline reconciliation only | never substitute for full confirmatory TestGenEval |
| Optional | **BugsInPy** | classical real-bug external validity | buggy/fixed distinguishing behavior | pinned framework; no vendored project checkouts |
| CI | Toy | zero-GPU orchestration sanity | schema/control-flow only | included |

## RQ mapping

- **RQ1 — uncertainty reliability:** ULT is primary; PLT is the paired contamination diagnostic.
- **RQ2 — sustainable adaptive testing:** ULT + full TestGenEval are primary.
- **RQ3 — fault discovery and discriminative reliability:** TestExplora + SWE-Mutation are primary.
- BugsInPy is an external-validity extension, not required to carry the main claims.

## ULT / PLT integrity firewall

The released ULT-family files may use a `.jsonl` suffix while containing a JSON array; the adapter auto-detects both array and line-delimited encodings. Any field that can act as evaluator truth (`test_list`, `tests`, `reference_tests`, `gold_tests`) is stripped from generator-visible metadata and retained only in an evaluator-side store. This rule also applies to PLT even though it is intentionally leaked: the experiment studies contamination effects in the model/training ecosystem, not deliberate prompt leakage by GreenUTest.

Pinned files at the audited upstream revision include `ULT.jsonl`, `ULT_Lite.jsonl`, and `PLT.jsonl`; their Git blob identities are recorded in `upstreams.json`.

## TestGenEval protocol

Use `kjain14/testgenevallite` only while validating Docker/images, prompts, scoring, and log reconciliation. Final RQ2 evaluation uses **`kjain14/testgeneval`** and the pinned `facebookresearch/testgeneval` harness. Record the exact Hugging Face dataset snapshot/fingerprint locally before freeze.

## TestExplora protocol

The main condition is non-hinted proactive discovery: fix patches/hints are evaluator-side. A valid discovery should reflect Fail-to-Pass behavior between buggy and repaired states, not simply a generated test that agrees with the current implementation.

## SWE-Mutation protocol

Use the released curated mutation data (`data/curated_mutations.jsonl`) and preserve benchmark-native metrics such as VRR and RDR. Do not silently equate its realistic agent-crafted mutants with conventional first-order mutation operators.

## Reproducible fetch

```bash
python scripts/fetch_benchmarks.py --list
python scripts/fetch_benchmarks.py --name ult --dest external
python scripts/fetch_benchmarks.py --name testgeneval --dest external
python scripts/fetch_benchmarks.py --name testexplora --dest external
python scripts/fetch_benchmarks.py --name swe_mutation --dest external
python scripts/verify_upstream_checkouts.py --external external
```

The default is pinned. `--floating` is exploratory only and forbidden for held-out confirmatory execution.
