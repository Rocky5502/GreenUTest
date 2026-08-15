# Local model telemetry contract

GreenUTest's local Hugging Face backend is designed to make uncertainty and compute accounting auditable before any confirmatory result is produced.

## Model tiers

The pre-pilot candidate plan is:

- `qwen25coder15b`: cheap tier (`Qwen/Qwen2.5-Coder-1.5B-Instruct`)
- `qwen25coder7b`: stronger same-family tier (`Qwen/Qwen2.5-Coder-7B-Instruct`)
- `mistral7b`: cross-family robustness tier (`mistralai/Mistral-7B-Instruct-v0.3`)

These IDs are not frozen scientific commitments until the excluded hardware/model pilot finishes and exact model/tokenizer revisions plus quantization are written into the frozen configuration.

## Candidate-level telemetry

Each local generation records:

- mean generated-token negative log-likelihood (`token_nll`);
- raw confidence = `exp(-mean_NLL)` (uncalibrated geometric-mean generated-token probability);
- prompt SHA-256;
- prompt token count;
- generated token count;
- seed and sampling settings;
- requested model revision;
- resolved model Hub commit hash when exposed by Transformers;
- resolved tokenizer Hub commit hash when exposed by Transformers.

Raw confidence is a baseline signal only. It must not be described as calibrated probability before calibration-fit evaluation.

## No-GPU inspection

```bash
python -m greenutest inspect-model-plan --config configs/experiment.json
```

This command does not import model weights.

## First model smoke test

Only after the environment and NVML telemetry checks pass:

```bash
python -m greenutest model-smoke \
  --config configs/experiment.json \
  --model qwen25coder15b \
  --seed 20260815
```

This command may download/load weights and use the GPU. It is **exploratory pilot activity**. Copy the resolved model/tokenizer revisions into the configuration before confirmatory execution.

## Confirmatory guard

`build_local_model_from_config(..., allow_unpinned=False)` rejects unresolved revisions. Quantized loading is also rejected unless that loading path has been explicitly implemented and validated; GreenUTest must never silently ignore a frozen quantization setting.
