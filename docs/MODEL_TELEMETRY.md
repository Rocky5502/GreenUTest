# Model telemetry and provider contract

GreenUTest deliberately separates **self-hosted telemetry** from **hosted-provider telemetry** so uncertainty/resource claims are based only on observable evidence.

## Core tiers

- `qwen25coder15b`: cheap controlled tier.
- `qwen25coder7b`: stronger same-family controlled tier.
- `qwen3coder30ba3b`: strong open sparse/MoE tier.
- `qwen3codernext`: frontier open sparse/MoE tier.
- `gpt56sol`: OpenAI frontier hosted condition.
- `claudesonnet5`: Anthropic frontier hosted condition.
- `gemini36flash`: Google frontier hosted condition.

`mistral7b` is optional cross-family appendix robustness.

## Self-hosted candidate telemetry

Each local Hugging Face generation records where available:

- mean generated-token negative log-likelihood (`token_nll`);
- raw confidence = `exp(-mean_NLL)` (uncalibrated);
- prompt SHA-256;
- prompt token count;
- generated token count;
- seed and supported sampling settings;
- requested Hub revision;
- resolved model/tokenizer commit hashes;
- NVML power trace/energy when enabled.

`build_local_model_from_config(..., allow_unpinned=False)` rejects unresolved open-weight revisions. Quantization must also be explicitly implemented/validated before it can be frozen.

## Hosted API telemetry

Hosted backends are lazy and do not import provider SDKs until a generation is requested. They archive:

- canonical configured model ID;
- provider/response model metadata when exposed;
- provider response/request ID when exposed;
- input/output/total token usage when exposed;
- wall-clock latency;
- call count in downstream aggregation;
- prompt/task provenance through the common run record.

Hosted candidates intentionally set `token_nll=None` and `raw_confidence=None` unless a provider-specific logprob path is explicitly validated and frozen. This prevents silent substitution of incomparable confidence definitions.

Provider-side energy is **unknown** unless the provider supplies verifiable telemetry. GreenUTest records no fabricated Joule estimate.

## Sampling constraints

Do not force one sampling API across providers:

- self-hosted Qwen/Mistral conditions can freeze temperature/top-p and seeds;
- GPT-5.6 Sol uses its supported reasoning-effort configuration;
- Claude Sonnet 5 uses provider defaults for sampling parameters that the current API rejects when overridden;
- Gemini 3.6 Flash uses the current provider API defaults and does not receive deprecated temperature/top-p/top-k controls.

The exact configuration is archived before held-out execution.

## Inspection and smoke commands

No model loading:

```bash
python -m greenutest inspect-model-plan --config configs/experiment.json
```

Self-hosted exploratory smoke:

```bash
python -m greenutest model-smoke --model qwen25coder15b
```

Hosted exploratory smoke (requires `.[remote-api]` and provider credentials):

```bash
python -m greenutest api-smoke --model gpt56sol
python -m greenutest api-smoke --model claudesonnet5
python -m greenutest api-smoke --model gemini36flash
```
