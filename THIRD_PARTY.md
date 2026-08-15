GreenUTest
Copyright 2026 GreenUTest contributors

This repository contains original experiment orchestration code. It does not redistribute third-party benchmark corpora, model weights, hidden tests, or baseline source code. Third-party resources fetched by helper scripts remain subject to their own licenses and terms.

# Third-party resources

| Resource | Upstream/provider | Intended use | Local policy |
|---|---|---|---|
| ULT / PLT / ULT_Lite | `huangd1999/UnLeakedTestBench` | primary uncertainty benchmark + contamination diagnostic | fetch pinned externally; evaluator references never enter prompts |
| TestGenEval / Lite | `facebookresearch/testgeneval`, HF datasets `kjain14/testgeneval*` | full RQ2 effectiveness + pilot | external only; upstream notes majority repo code CC-BY-NC and third-party files may differ |
| TestExplora | `microsoft/TestExplora` | proactive Fail-to-Pass real-bug validation | pinned harness; external benchmark JSON/testbeds; hash local data artifact |
| SWE-Mutation | `Sunny4Coding/SWE-Mutation` | realistic mutant discrimination / VRR / RDR | fetch pinned externally; repository MIT at audited revision; task repos retain their own terms |
| BugsInPy | `soarsmu/BugsInPy` | optional classical real-bug external validity | clone externally; do not vendor project checkouts |
| Qwen2.5-Coder / Qwen3-Coder weights | Qwen Hugging Face repositories | self-hosted model tiers | download to user cache; record exact Hub revision; never vendor weights |
| Mistral-7B-Instruct-v0.3 | Mistral Hugging Face repository | optional cross-family appendix | same as above |
| GPT-5.6 Sol | OpenAI API | frontier provider generalization | no credentials/logs committed; provider terms apply; no unverified energy estimate |
| Claude Sonnet 5 | Anthropic API | frontier provider generalization | same |
| Gemini 3.6 Flash | Google Gemini API | frontier provider generalization | same |
| Pynguin | upstream Python project/package | traditional non-LLM baseline | install separately; upstream license applies |

“STARouter-style”, “SWE-Router-style”, and fixed-agentic-feedback policies are clean-room experimental controls unless a separately pinned upstream implementation is explicitly integrated and license-reviewed.
