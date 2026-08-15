from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .harness import (
    Action,
    DecisionState,
    GreenUTestPolicy,
    RandomRoutingPolicy,
    RawConfidencePolicy,
    SmallOnlyPolicy,
    StaticComplexityPolicy,
    StrongOnlyPolicy,
)


class RoutingPolicy(Protocol):
    def decide(self, state: DecisionState) -> Action: ...


@dataclass(frozen=True)
class MultiSamplePlan:
    """Fixed sample-count baseline; aggregation happens after all samples are acquired."""

    samples: int
    aggregation: str = "majority_behavior"

    def __post_init__(self) -> None:
        if self.samples < 2:
            raise ValueError("self-consistency requires at least two samples")


@dataclass(frozen=True)
class AgenticFeedbackPlan:
    """Fixed-depth execution/coverage feedback baseline."""

    rounds: int
    feedback: tuple[str, ...] = ("execution", "coverage")

    def __post_init__(self) -> None:
        if self.rounds < 1:
            raise ValueError("agentic feedback requires at least one round")


@dataclass(frozen=True)
class SpecificationFirstPlan:
    """Generate an oracle/specification view independently of candidate implementation output."""

    independent_oracle: bool = True
    allow_candidate_implementation_in_oracle_prompt: bool = False


@dataclass(frozen=True)
class TraditionalToolPlan:
    backend: str
    enabled: bool = False


@dataclass(frozen=True)
class TemporalRoutingPlan:
    """Clean-room temporal value-routing control.

    A cheap model is allowed a fixed number of exploratory steps before a second routing
    decision. This is intentionally a protocol object, not a claimed reproduction of SWE-Router.
    """
    exploration_steps: int = 2
    features: tuple[str, ...] = ("risk", "raw_confidence", "complexity", "execution_feedback")

    def __post_init__(self) -> None:
        if self.exploration_steps < 1:
            raise ValueError("temporal routing requires at least one exploratory step")


@dataclass(frozen=True)
class STARouterStylePolicy:
    """Clean-room state-feature routing control, not an upstream STARouter reproduction.

    The policy deliberately uses only fields already available to GreenUTest. Its purpose is
    to isolate the value of calibrated/VoI routing from a simpler state-feature escalation rule.
    Coefficients must be frozen on policy-tuning data before held-out execution.
    """

    intercept: float = -0.5
    risk_weight: float = 2.0
    confidence_weight: float = -1.0
    complexity_weight: float = 0.03
    threshold: float = 0.5

    def score(self, state: DecisionState) -> float:
        confidence = 0.5 if state.raw_confidence is None else state.raw_confidence
        complexity = 0.0 if state.complexity is None else state.complexity
        return (
            self.intercept
            + self.risk_weight * state.risk
            + self.confidence_weight * confidence
            + self.complexity_weight * complexity
        )

    def decide(self, state: DecisionState) -> Action:
        return Action.ESCALATE if self.score(state) >= self.threshold else Action.EXECUTE


Baseline = RoutingPolicy | MultiSamplePlan | AgenticFeedbackPlan | SpecificationFirstPlan | TraditionalToolPlan | TemporalRoutingPlan


def build_baseline(name: str, config: dict[str, Any]) -> Baseline:
    """Build a baseline from a frozen config entry.

    This function never downloads a model, benchmark, or third-party implementation. It only
    converts configuration into a deterministic experiment plan/policy.
    """

    kind = config.get("type")
    if kind == "small_model_only":
        return SmallOnlyPolicy()
    if kind == "strong_model_only":
        return StrongOnlyPolicy()
    if kind == "random_routing":
        return RandomRoutingPolicy(float(config["escalation_rate"]), int(config["seed"]))
    if kind == "raw_confidence_routing":
        return RawConfidencePolicy(float(config["escalate_if_confidence_below"]))
    if kind == "static_complexity_routing":
        return StaticComplexityPolicy(float(config["escalate_if_complexity_at_least"]))
    if kind == "greenutest":
        return GreenUTestPolicy(
            float(config["risk_accept"]),
            float(config["risk_verify"]),
            float(config["risk_escalate"]),
            float(config["abstain_above"]),
        )
    if kind == "fixed_self_consistency":
        return MultiSamplePlan(samples=int(config["samples"]))
    if kind == "fixed_agentic_feedback":
        return AgenticFeedbackPlan(rounds=int(config["rounds"]))
    if kind == "specification_first":
        return SpecificationFirstPlan(independent_oracle=bool(config.get("independent_oracle", True)))
    if kind == "traditional_non_llm":
        return TraditionalToolPlan(backend=str(config["backend"]), enabled=bool(config.get("enabled", False)))
    if kind == "temporal_value_routing":
        return TemporalRoutingPlan(
            exploration_steps=int(config.get("exploration_steps", 2)),
            features=tuple(config.get("features", ("risk", "raw_confidence", "complexity", "execution_feedback"))),
        )
    if kind == "starouter_style":
        return STARouterStylePolicy(
            intercept=float(config.get("intercept", -0.5)),
            risk_weight=float(config.get("risk_weight", 2.0)),
            confidence_weight=float(config.get("confidence_weight", -1.0)),
            complexity_weight=float(config.get("complexity_weight", 0.03)),
            threshold=float(config.get("threshold", 0.5)),
        )
    raise KeyError(f"Unknown baseline {name!r} with type {kind!r}")
