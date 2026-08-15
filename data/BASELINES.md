# Baseline matrix

GreenUTest compares against controls that isolate **model strength, sampling budget, routing signal, agentic feedback, oracle independence, and traditional testing**. Baseline configurations live in `configs/experiment.json`.

| Baseline | What it controls for | Fairness rule |
|---|---|---|
| `small_only` | cheapest model everywhere | same prompt/task/seed policy |
| `strong_only` | quality-first model everywhere | same prompt/task/seed policy |
| `fixed_self_consistency` | fixed extra sampling | charge all sample energy/time |
| `random_routing` | routing rate without information | match escalation rate where reported |
| `raw_confidence` | uncalibrated confidence routing | same model pair and action space |
| `static_complexity` | SE heuristic routing | same model pair; no uncertainty |
| `starouter_style` | state-feature model routing | clean-room control; do not claim upstream reproduction |
| `swe_router_style` | temporal/exploration routing | fixed exploration depth; charge exploration energy |
| `fixed_agentic_feedback` | TestForge-like execution/coverage refinement | fixed rounds; charge all feedback iterations |
| `spec_first` | independent oracle/specification signal | candidate implementation excluded from oracle prompt |
| `traditional` | non-LLM search-based testing | report unsupported tasks separately, never as zero |
| `greenutest` | calibrated risk + VoI + energy-aware actions | tuned only on policy-tuning partition |

## Non-negotiable accounting

1. Every model call, verification call, execution, regeneration, and exploratory routing step is charged to the policy that requested it.
2. Unsupported benchmark/baseline combinations are `N/A`, never score zero.
3. Hyperparameters are frozen before held-out execution.
4. Clean-room “style” controls are named as such in tables and prose.
5. For routing comparisons, report both outcome quality and actual routing/escalation rate; when useful, add matched-energy and matched-escalation analyses.
