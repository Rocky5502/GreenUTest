# Baseline and fairness matrix

GreenUTest compares **compute-allocation strategies**, not merely model names. Baseline configurations live in `configs/experiment.json`; the machine-readable model/dataset study design is `configs/study_matrix.json`.

| Baseline | What it controls for | Fairness rule |
|---|---|---|
| `small_only` | cheapest model everywhere | same task/prompt and model tier |
| `strong_only` | quality-first upper-compute reference | same task/prompt |
| `fixed_self_consistency` | fixed extra sampling | charge every sample/call |
| `random_routing` | escalation without information | matched escalation rate and/or resource budget |
| `raw_confidence` | uncalibrated confidence routing | only where a genuine comparable confidence signal exists |
| `static_complexity` | software-engineering heuristic routing | same escalation model/budget; no uncertainty |
| `starouter_style` | state-feature model routing | clean-room control; never claim source reproduction |
| `swe_router_style` | temporal/exploration routing | fixed exploration depth; charge all exploratory calls |
| `fixed_agentic_feedback` | TestForge-like execution/coverage refinement | fixed rounds; charge all feedback iterations |
| `spec_first` | independent oracle/specification signal | candidate implementation excluded from oracle prompt |
| `traditional` | non-LLM search-based testing | matched wall-clock budget where semantics permit; unsupported = N/A |
| `greenutest` | calibrated risk + VoI + resource-aware actions | tune only on policy-tuning data |

## Model-comparison strata

1. **Controlled same-family:** Qwen2.5-Coder-1.5B → Qwen2.5-Coder-7B.
2. **Open scaling:** add Qwen3-Coder-30B-A3B and Qwen3-Coder-Next.
3. **Frontier generalization:** GPT-5.6 Sol, Claude Sonnet 5, Gemini 3.6 Flash.

Do not mix these strata into one causal claim. The same-family pair tests the routing mechanism most cleanly; open/frontier studies test robustness and generalization.

## Non-negotiable accounting

1. Every generation, verification, execution, regeneration, self-consistency sample, and exploratory routing step is charged to the policy that requested it.
2. Unsupported benchmark/baseline combinations are `N/A`, never zero.
3. Hyperparameters, model IDs/revisions, prompts, split hashes, and budgets are frozen before held-out execution.
4. Clean-room “style” controls are named as such in tables and prose.
5. Report actual routing/escalation rates beside quality and resource use; include matched-energy or matched-escalation analyses where relevant.
6. **Local/self-hosted models:** direct GPU Joules/Wh are observable with NVML and can support energy-efficiency claims.
7. **Hosted API models:** record provider-reported tokens, latency and call count. Do not fabricate provider-side Joules or compare unknown provider energy directly against measured local GPU energy.
8. A raw-confidence baseline must be omitted or redefined when a provider does not expose a scientifically comparable confidence/logprob signal; do not substitute self-reported verbal confidence silently.
