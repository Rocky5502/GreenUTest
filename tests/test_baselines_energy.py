import json
import unittest
from pathlib import Path

from greenutest.baselines import (
    AgenticFeedbackPlan,
    MultiSamplePlan,
    STARouterStylePolicy,
    SpecificationFirstPlan,
    TraditionalToolPlan,
    build_baseline,
)
from greenutest.harness import Action, DecisionState, PowerSample, summarize_power


class BaselineAndEnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.policies = json.loads((root / "configs" / "experiment.json").read_text())["policies"]

    def test_every_configured_baseline_builds(self):
        built = {name: build_baseline(name, cfg) for name, cfg in self.policies.items()}
        self.assertEqual(set(built), set(self.policies))
        self.assertIsInstance(built["fixed_self_consistency"], MultiSamplePlan)
        self.assertIsInstance(built["fixed_agentic_feedback"], AgenticFeedbackPlan)
        self.assertIsInstance(built["spec_first"], SpecificationFirstPlan)
        self.assertIsInstance(built["traditional"], TraditionalToolPlan)

    def test_starouter_style_is_deterministic(self):
        p = STARouterStylePolicy()
        low = DecisionState(risk=0.1, complexity=3, raw_confidence=0.9)
        high = DecisionState(risk=0.9, complexity=20, raw_confidence=0.2)
        self.assertEqual(p.decide(low), Action.EXECUTE)
        self.assertEqual(p.decide(high), Action.ESCALATE)

    def test_phase_energy_summary(self):
        samples = [
            PowerSample(0, 100, "prefill"),
            PowerSample(1, 100, "prefill"),
            PowerSample(2, 200, "decode"),
            PowerSample(3, 200, "decode"),
        ]
        summary = summarize_power(samples, idle_watts=50)
        self.assertAlmostEqual(summary["joules"], 450.0)
        self.assertAlmostEqual(summary["by_phase_joules"]["prefill"], 100.0)
        self.assertAlmostEqual(summary["by_phase_joules"]["decode"], 200.0)
        self.assertAlmostEqual(summary["idle_adjusted_joules"], 300.0)


if __name__ == "__main__":
    unittest.main()
