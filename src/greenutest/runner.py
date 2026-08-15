from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Callable

from greenutest.harness import (
    Action,
    DecisionState,
    FakeModel,
    GreenUTestPolicy,
    ModelBackend,
    NVMLPowerSampler,
    NullEnergyMeter,
    ToyAdapter,
    ULTAdapter,
    build_local_model_from_config,
    lexical_uncertainty,
    static_risk,
    summarize_power,
    synthetic_evaluate,
    weighted_risk,
)
from greenutest.schemas import Evidence, RunRecord, Task


def run_toy(output: str | Path, seed: int = 20260815) -> Path:
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    runlog = out / "runlog.jsonl"
    cheap = FakeModel("fake-cheap", quality=0.55)
    strong = FakeModel("fake-strong", quality=0.82)
    policy = GreenUTestPolicy()
    meter = NullEnergyMeter()
    rows = []
    for idx, task in enumerate(ToyAdapter().tasks()):
        task_seed = seed + idx
        candidate = cheap.generate(task, seed=task_seed)
        evidence: list[Evidence] = [static_risk(task), lexical_uncertainty(candidate)]
        risk = weighted_risk(evidence, {"lexical_uncertainty": 2.0, "static_software_risk": 1.0})
        state = DecisionState(risk=risk, complexity=task.complexity, raw_confidence=candidate.raw_confidence)
        action = policy.decide(state)
        actions = [action.value]
        if action == Action.ESCALATE:
            candidate = strong.generate(task, seed=task_seed)
            actions.append(Action.EXECUTE.value)
        outcome = synthetic_evaluate(task, candidate)
        record = RunRecord(
            run_id=str(uuid.uuid4()), task_id=task.task_id, benchmark=task.benchmark,
            partition="pilot", policy="greenutest", seed=task_seed,
            candidate={"model_id": candidate.model_id, "text": candidate.text,
                       "raw_confidence": candidate.raw_confidence, "token_nll": candidate.token_nll,
                       "synthetic": True},
            evidence=[{"name": e.name, "value": e.value, "cost_joules": e.cost_joules, "metadata": e.metadata}
                      for e in evidence],
            actions=actions, outcomes=outcome.__dict__, energy=meter.summary(), status="ok",
            metadata={"synthetic": True, "scientific_result": False, "risk": risk},
        )
        rows.append(record.to_dict())
    runlog.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    summary = {"synthetic": True, "scientific_result": False, "records": len(rows), "runlog": str(runlog), "note": "Dry-run validates orchestration only; no benchmark/model/GPU result is produced."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return runlog


def _task_fingerprint(task: Task) -> dict[str, str | float | None]:
    return {
        "repository": task.repository,
        "complexity": task.complexity,
        "code_sha256": hashlib.sha256(task.code.encode("utf-8")).hexdigest(),
        "task_prompt_sha256": hashlib.sha256(task.prompt.encode("utf-8")).hexdigest(),
    }


def run_generation_pilot(
    tasks,
    model: ModelBackend,
    output: str | Path,
    *,
    max_tasks: int = 4,
    seed: int = 20260815,
    energy_sampler_factory: Callable[[], NVMLPowerSampler] | None = None,
) -> Path:
    """Run an excluded generation-only pilot over normalized tasks.

    This is a preflight bridge, not a scientific evaluation. It never requests evaluator-side
    reference tests and leaves all testing-effectiveness outcomes as null. Its purpose is to
    validate real model generation, lexical uncertainty telemetry, provenance, and optional
    task-time GPU energy before the execution/mutation pipeline is enabled.
    """
    if max_tasks < 1:
        raise ValueError("max_tasks must be positive")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    power_dir = out / "power"
    if energy_sampler_factory is not None:
        power_dir.mkdir(exist_ok=True)
    runlog = out / "runlog.jsonl"

    load = getattr(model, "load", None)
    if callable(load):
        load()

    rows = []
    for idx, task in enumerate(tasks):
        if idx >= max_tasks:
            break
        task_seed = seed + idx
        samples = []
        sampler = energy_sampler_factory() if energy_sampler_factory is not None else None
        if sampler is not None:
            sampler.set_phase("decoding")
            sampler.start()
        try:
            candidate = model.generate(task, seed=task_seed)
            status = "ok"
            error = None
        except Exception as exc:
            candidate = None
            status = "model_error"
            error = {"type": type(exc).__name__, "message": str(exc)}
        finally:
            if sampler is not None:
                samples = sampler.stop()

        if samples:
            energy = summarize_power(samples)
            energy.update({"backend": "nvml", "measured": True, "sampling": "task_time_only"})
            safe_id = hashlib.sha256(task.task_id.encode("utf-8")).hexdigest()[:16]
            (power_dir / f"{safe_id}.jsonl").write_text(
                "".join(json.dumps({"t": s.t, "watts": s.watts, "phase": s.phase}) + "\n" for s in samples),
                encoding="utf-8",
            )
        else:
            energy = NullEnergyMeter().summary()

        if candidate is not None:
            ev = lexical_uncertainty(candidate)
            evidence = [{"name": ev.name, "value": ev.value, "cost_joules": ev.cost_joules, "metadata": ev.metadata}]
            candidate_dict = {
                "model_id": candidate.model_id,
                "text": candidate.text,
                "raw_confidence": candidate.raw_confidence,
                "token_nll": candidate.token_nll,
                "metadata": candidate.metadata,
            }
        else:
            evidence = []
            candidate_dict = {"model_id": getattr(model, "model_id", "unknown"), "error": error}

        record = RunRecord(
            run_id=str(uuid.uuid4()),
            task_id=task.task_id,
            benchmark=task.benchmark,
            partition="pilot",
            policy="generation_only_preflight",
            seed=task_seed,
            candidate=candidate_dict,
            evidence=evidence,
            actions=["GENERATE_ONLY"],
            outcomes={
                "syntax_valid": None,
                "execution_valid": None,
                "oracle_valid": None,
                "fault_triggered": None,
                "fault_detected": None,
                "false_validation": None,
                "branch_coverage": None,
                "line_coverage": None,
                "mutation_score": None,
                "incremental_value": None,
                "details": {"not_evaluated": True},
            },
            energy=energy,
            status=status,
            metadata={
                "scientific_result": False,
                "excluded_pilot": True,
                "generation_only": True,
                "evaluator_reference_tests_accessed": False,
                "task": _task_fingerprint(task),
                "error": error,
            },
        )
        rows.append(record.to_dict())

    runlog.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    summary = {
        "scientific_result": False,
        "excluded_pilot": True,
        "generation_only": True,
        "records": len(rows),
        "ok": sum(r["status"] == "ok" for r in rows),
        "errors": sum(r["status"] != "ok" for r in rows),
        "runlog": str(runlog),
        "note": "Preflight only: no syntax/execution/oracle/coverage/mutation/fault metric is inferred here.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return runlog


def run_ult_generation_pilot(
    dataset: str | Path,
    model_config: dict,
    output: str | Path,
    *,
    max_tasks: int = 4,
    seed: int = 20260815,
    measure_energy: bool = False,
    device_index: int = 0,
    sampling_interval_ms: int = 100,
) -> Path:
    """Convenience wrapper for the first real ULT + local-model pilot."""
    adapter = ULTAdapter(dataset)
    model = build_local_model_from_config(model_config, allow_unpinned=True)
    factory = None
    if measure_energy:
        factory = lambda: NVMLPowerSampler(device_index=device_index, interval_s=sampling_interval_ms / 1000.0)
    return run_generation_pilot(
        adapter.tasks(), model, output, max_tasks=max_tasks, seed=seed, energy_sampler_factory=factory
    )
