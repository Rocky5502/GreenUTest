GreenUTest
Copyright 2026 GreenUTest contributors

This repository contains original experiment orchestration code. It does not
redistribute third-party benchmark corpora, model weights, hidden tests, or
baseline source code. Third-party resources fetched by helper scripts remain
subject to their own licenses and terms. See THIRD_PARTY.md.

# Third-party resources

GreenUTest does not vendor benchmark datasets, model weights, or external baseline implementations.

The following upstream resources are referenced by adapters/setup scripts. **Always re-check the upstream license and terms at the pinned revision before a public release or redistribution.**

| Resource | Upstream | Intended use | Local policy |
|---|---|---|---|
| ULT / UnLeakedTestBench | `huangd1999/UnLeakedTestBench` | Primary function-level benchmark | Fetch externally; preserve benchmark integrity; do not mirror hidden tests |
| BugsInPy | `soarsmu/BugsInPy` | Real buggy/fixed pairs | Clone externally; do not vendor project checkouts |
| SWE-Mutation | `Sunny4Coding/SWE-Mutation` | Discriminative-suite stress test | Clone externally; pin revision |
| TestGenEval | `facebookresearch/testgeneval` | Repository/file-level robustness | Optional external dependency; note upstream non-commercial terms where applicable |
| Hugging Face models | model-specific repositories | LLM backends | Download to user cache; model license applies |
| Pynguin | upstream Python package/repository | Traditional non-LLM baseline | Install separately; upstream license applies |

“STARouter-style” and “fixed agentic feedback” policies in this repository are clean-room experimental interfaces that reproduce **comparison concepts**, not copied source code.

- **TestExplora** — Microsoft research benchmark harness, pinned via `data/upstreams.json`; repository license MIT at the audited revision. Benchmark JSON/repository testbeds remain external and retain their own provenance.
- **Qwen2.5-Coder-1.5B-Instruct / 7B-Instruct** — model weights remain external under the upstream model-card license; GreenUTest records model snapshot revisions rather than redistributing weights.
