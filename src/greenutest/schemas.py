from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class Task:
    task_id: str
    benchmark: str
    prompt: str
    code: str = ""
    repository: str | None = None
    complexity: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CandidateTest:
    text: str
    model_id: str
    raw_confidence: float | None = None
    token_nll: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Evidence:
    name: str
    value: float | bool | str | None
    cost_joules: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Outcome:
    syntax_valid: bool | None = None
    execution_valid: bool | None = None
    oracle_valid: bool | None = None
    fault_triggered: bool | None = None
    fault_detected: bool | None = None
    false_validation: bool | None = None
    branch_coverage: float | None = None
    line_coverage: float | None = None
    mutation_score: float | None = None
    incremental_value: float | None = None
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class RunRecord:
    run_id: str
    task_id: str
    benchmark: str
    partition: str
    policy: str
    seed: int
    candidate: dict[str, Any]
    evidence: list[dict[str, Any]]
    actions: list[str]
    outcomes: dict[str, Any]
    energy: dict[str, Any]
    status: str
    analysis_plan_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
