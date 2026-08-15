# Contributing

GreenUTest is a research artifact. Contributions should preserve scientific traceability.

## Principles

1. Do not add manuscript source or unpublished paper results.
2. Do not vendor third-party benchmark corpora or model weights.
3. Every new metric must state its unit, denominator, and failure handling.
4. Every new policy must have a deterministic dry-run test.
5. Do not change confirmatory defaults after held-out unblinding without creating a new analysis version.
6. External baselines must be pinned and license-reviewed before integration.

## Local checks

```bash
python -m compileall -q src tests scripts
python -m unittest discover -s tests -v
```
