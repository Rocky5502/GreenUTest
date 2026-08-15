# Dataset plan and provenance

This directory stores **metadata, schemas, pins, and split manifests**, not third-party benchmark corpora. GreenUTest deliberately avoids mirroring large or leakage-sensitive datasets. Exact upstream revisions are frozen in `upstreams.json`; `scripts/fetch_benchmarks.py` checks out those commits by default.

## Confirmatory hierarchy

| Priority | Benchmark | Scientific role | Planned endpoint | Public-repo policy |
|---|---|---|---|---|
| P0 | ULT / UnLeakedTestBench | Primary contamination-conscious function-level test generation | validity, branch/statement coverage, mutation score, calibration, energy | Fetch pinned upstream; reference tests evaluator-only |
| P1 | BugsInPy | Real buggy/fixed validation and false-validation analysis | real fault detection / distinguishing behavior | Clone pinned framework; never vendor project checkouts |
| P1 | TestExplora | Proactive repository-level bug discovery stress test | Fail-to-Pass / fault discovery under documentation-derived intent | External benchmark JSON + pinned harness; hash local dataset artifact |
| P2 | SWE-Mutation | Discriminative test-suite stress test | mutant discrimination / suite quality | Fetch pinned upstream |
| P2 | TestGenEvalLite | Repository/file-level robustness and agentic-baseline comparability | pass, coverage, mutation | Optional; external only because upstream licensing is mixed/CC-BY-NC |
| CI | Toy benchmark | Zero-GPU orchestration sanity only | schema/control-flow checks | Included |

## ULT integrity rule

ULT is the primary benchmark. The released files may carry a `.jsonl` suffix while using a JSON-array encoding. The adapter auto-detects both encodings. Fields such as `test_list`, `gold_tests`, or equivalent evaluator references are **never copied into `Task.metadata` or model prompts**. They are accessible only through evaluator-side APIs.

## Reproducible fetch

```bash
python scripts/fetch_benchmarks.py --list
python scripts/fetch_benchmarks.py --name ult --dest external
python scripts/fetch_benchmarks.py --name bugsinpy --dest external
python scripts/fetch_benchmarks.py --name testexplora --dest external
```

The default is pinned. `--floating` is exploratory only and must never be used for a held-out confirmatory run.
