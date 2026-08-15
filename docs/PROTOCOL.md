# GreenUTest confirmatory protocol

## 1. Design principle

GreenUTest is a **resource-allocation decision system**, not merely an LLM test generator. Evidence is acquired cheap-first; raw signals are calibrated into reliability risk; extra generation/verification is purchased only when its expected value-of-information exceeds the declared resource penalty.

## 2. Research questions and primary benchmark roles

### RQ1 — uncertainty reliability
Primary: ULT. Diagnostic: paired PLT.

Question: how well do lexical (when observable), behavioral, execution, oracle and software-risk signals predict invalid, incorrect or low-value generated tests?

Primary analyses include discrimination (AUROC/AUPRC), calibration (ECE/Brier), selective risk/coverage, and relationships with coverage/mutation/fault outcomes.

### RQ2 — sustainable adaptive testing
Primary: ULT + **full TestGenEval**.

Question: can calibrated uncertainty-guided routing reduce directly measured local energy/latency or hosted-call resources while preserving test quality?

Confirmatory structure: quality non-inferiority at reduced local energy plus quality comparison at matched resource budgets. TestGenEvalLite is pilot-only.

### RQ3 — fault-oriented reliability
Primary: TestExplora + SWE-Mutation.

TestExplora measures proactive Fail-to-Pass real-bug discovery and false validation. SWE-Mutation measures realistic mutant discrimination using benchmark-native Pass@1, VRR and RDR. BugsInPy is optional classical external validation.

## 3. Model strata

### Study A — controlled same-family routing
Qwen2.5-Coder-1.5B → Qwen2.5-Coder-7B.

This is the cleanest causal model-allocation experiment because family/training style is partially controlled.

### Study B — open-model scaling
Add Qwen3-Coder-30B-A3B-Instruct and Qwen3-Coder-Next. This tests whether the routing advantage persists as escalation reaches modern sparse/MoE code models.

### Study C — frontier provider generalization
GPT-5.6 Sol, Claude Sonnet 5 and Gemini 3.6 Flash. These conditions test provider/family generalization; they are not used to make unsupported provider-energy claims.

### Optional appendix
Mistral-7B-Instruct-v0.3 for cross-family robustness.

The machine-readable design is `configs/study_matrix.json`.

## 4. Dataset integrity

### ULT / PLT

- exact upstream Git revision is pinned;
- blob identities for ULT, ULT_Lite and PLT are recorded;
- array-vs-JSONL encoding is auto-detected;
- `test_list`, `tests`, `reference_tests`, `gold_tests` and equivalent evaluator fields never enter generator-visible task metadata/prompts/routing features;
- the same firewall applies to PLT so the diagnostic measures ecosystem contamination, not deliberate prompt leakage.

### TestGenEval

- use TestGenEvalLite to validate Docker/images/scoring;
- full confirmatory RQ2 uses `kjain14/testgeneval` with the pinned harness;
- hash/record the exact HF dataset snapshot or fingerprint before freeze.

### TestExplora

- main condition is non-hinted proactive discovery;
- fix patches/hints are evaluator-side unless a separately named hinted ablation is predeclared;
- distinguish environment/setup failure from model/test failure.

### SWE-Mutation

- preserve benchmark-native semantics and released curated mutation set;
- report Pass@1, VRR/RDR as defined by the benchmark;
- do not silently label realistic agent-crafted mutants as conventional first-order mutation.

## 5. Split policy

Every applicable dataset is divided into pilot, calibration-fit, policy-tuning and held-out-final partitions. Group by repository/project/PR family where metadata permit. Hash the held-out IDs before unblinding. Never use held-out outcomes to select models, thresholds, datasets, prompts, margins or budgets.

## 6. Uncertainty evidence

Cheap-first evidence may include:

- self-hosted generated-token NLL / entropy-derived lexical signal;
- static complexity/change risk;
- first execution status.

Conditional evidence may include:

- multi-sample behavioral disagreement;
- execution disagreement;
- independent-oracle/specification disagreement;
- stronger-model verification;
- fault/mutant-facing verification where methodologically permitted.

Hosted providers are not assigned synthetic NLL/logprob values. Cross-provider analyses use signals actually observable across providers.

## 7. Calibration and risk

Fit calibration/fusion on `calibration_fit` only (candidate methods may include Platt/logistic, isotonic, or other predeclared calibrators). Evaluate ECE, Brier, AUROC/AUPRC and selective risk. Freeze the selected calibration procedure before held-out execution.

## 8. VoI and routing

Before buying an expensive signal/action, compare expected downstream utility improvement with its resource penalty. The policy may accept/execute, verify, repair, regenerate, escalate or abstain. All thresholds and VoI coefficients are tuned only on `policy_tuning` then frozen.

## 9. Baselines

Required controls: small-only, strong-only, fixed self-consistency, matched random routing, raw-confidence routing where comparable, static-complexity routing, STARouter-style clean-room state routing, SWE-Router-style clean-room temporal routing, fixed agentic feedback, specification-first independent oracle, traditional Pynguin-style testing where compatible, and GreenUTest ablations.

Unsupported combinations are `N/A`. Every call/tool/action is charged to the requesting policy.

## 10. Resource accounting

### Self-hosted/local

Sample NVIDIA board power through NVML with monotonic timestamps and integrate:

`E_joules = Σ 0.5 * (P_i + P_{i+1}) * (t_{i+1} - t_i)`

Primary: raw directly measured Joules/Wh. Sensitivity: idle-adjusted GPU energy when stable. Optional: wall-meter cross-check.

Phase tags: model load/warmup, prefill, decoding, uncertainty acquisition, execution, verification, repair/regeneration, mutation/coverage evaluation.

### Hosted APIs

Archive provider usage tokens, latency and call count. Provider-side energy is unknown unless verifiable telemetry becomes available. Do not convert token counts or API price into Joules.

Therefore direct energy-efficiency claims are made within observable self-hosted conditions; hosted conditions primarily test quality/generalization and call/token allocation.

## 11. Model telemetry

Self-hosted generations archive NLL/raw confidence, prompt hash/token counts, generated tokens, seed/sampling configuration, requested and resolved model/tokenizer revisions.

Hosted generations archive provider/model IDs, response identifiers/versions where exposed, token usage and latency. Current provider sampling constraints are respected rather than forcing unsupported temperature/top-p controls.

## 12. Statistics

Use paired/task-aligned analyses where possible, 95% confidence intervals, effect sizes, and predeclared multiplicity correction. For RQ2 report non-inferiority and matched-resource comparisons. For mutation/fault endpoints use benchmark-appropriate paired/bootstrap analyses. Preserve confirmatory vs exploratory labeling.

## 13. Reproducibility contract

A publication-facing run must recover:

- GreenUTest commit SHA and frozen analysis-plan hash;
- benchmark revisions and external dataset hashes/fingerprints;
- model IDs/revisions/tokenizer revisions/quantization or canonical provider IDs;
- prompts and split hashes;
- seeds/sampling/provider configuration;
- machine/OS/Python/CUDA/driver/framework versions for self-hosted runs;
- direct energy sampling configuration or hosted usage metadata;
- action traces, generated tests, outcomes and infrastructure failures;
- evaluation tool/container versions.

No paper-facing number is typed manually; tables/figures must be generated from archived run logs by versioned analysis code.

## 14. Results policy

Pilot data may guide predeclared design freezing but never enter confirmatory tables. After held-out unblinding, do not change the frozen analysis. Report N/A combinations, failures, confidence intervals and effect sizes transparently.

## 15. Security

Generated tests and benchmark repositories are untrusted code. Use isolated containers/environments with network restrictions where feasible, resource/time limits and explicit workspaces. Credentials must never be passed into generated-test sandboxes or committed to logs.
