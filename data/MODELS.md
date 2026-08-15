# Model matrix and provenance

GreenUTest uses **seven core models** arranged into controlled scaling, open-model scaling, and frontier-provider generalization studies. Model IDs below are configuration defaults; open-weight Hub revisions/quantization are frozen after the excluded hardware pilot, while hosted API conditions use canonical provider model IDs and archive provider response metadata.

## Core models

| Key | Model | Role | Deployment | Direct energy? |
|---|---|---|---|---|
| `qwen25coder15b` | Qwen2.5-Coder-1.5B-Instruct | cheap open starting tier | local/self-hosted | yes, NVML |
| `qwen25coder7b` | Qwen2.5-Coder-7B-Instruct | stronger same-family tier | local/self-hosted | yes, NVML |
| `qwen3coder30ba3b` | Qwen3-Coder-30B-A3B-Instruct | strong sparse/open tier | local/self-hosted | yes, NVML |
| `qwen3codernext` | Qwen3-Coder-Next | frontier open sparse tier | local/self-hosted | yes, NVML |
| `gpt56sol` | GPT-5.6 Sol (`gpt-5.6-sol`) | OpenAI frontier generalization | hosted API | no provider energy estimate |
| `claudesonnet5` | Claude Sonnet 5 (`claude-sonnet-5`) | Anthropic frontier generalization | hosted API | no provider energy estimate |
| `gemini36flash` | Gemini 3.6 Flash (`gemini-3.6-flash`) | Google frontier generalization | hosted API | no provider energy estimate |

Optional appendix robustness: `mistral7b` / Mistral-7B-Instruct-v0.3.

## Why these tiers

1. **Controlled causal pair:** Qwen2.5-Coder 1.5B → 7B keeps the model family fixed while creating a meaningful capability/compute gap.
2. **Open scaling:** Qwen3-Coder-30B-A3B and Qwen3-Coder-Next test whether GreenUTest still helps when escalation reaches modern sparse/MoE code models.
3. **Frontier generalization:** GPT-5.6 Sol, Claude Sonnet 5 and Gemini 3.6 Flash test provider/model-family generalization rather than declaring a single vendor “best.”

## Uncertainty comparability

Generated-token mean NLL is measured directly only when the self-hosted backend exposes logits. GreenUTest **does not invent token-NLL values for hosted APIs**. Frontier API conditions rely on cross-provider signals that are actually observable: behavioral disagreement, execution outcomes, independent-oracle disagreement, static software risk, and repeated-sample consistency. Provider-reported input/output tokens and latency are logged as resource proxies, not converted into fabricated Joules.

## Sampling policy

Sampling behavior is model-specific and frozen before held-out runs. Do not force a shared `temperature/top_p` interface onto models whose current APIs reject or ignore those parameters. The hosted-provider adapters intentionally preserve provider defaults unless the frozen protocol documents a supported control.

## Verification sources (audited 2026-08-15)

- OpenAI model docs: `https://developers.openai.com/api/docs/models/gpt-5.6-sol`
- Anthropic Sonnet 5 docs: `https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5`
- Google latest Gemini models: `https://ai.google.dev/gemini-api/docs/latest-model`
- Qwen3-Coder-30B-A3B-Instruct: `https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct`
- Qwen3-Coder-Next: `https://huggingface.co/Qwen/Qwen3-Coder-Next`
