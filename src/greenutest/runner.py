from __future__ import annotations
import json
import uuid
from pathlib import Path
from greenutest.harness import ToyAdapter, NullEnergyMeter, synthetic_evaluate, FakeModel, Action, DecisionState, GreenUTestPolicy, weighted_risk, lexical_uncertainty, static_risk
from greenutest.schemas import Evidence, RunRecord


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
