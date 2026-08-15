import json
import unittest
from pathlib import Path

class ResearchMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.exp = json.loads((root / "configs" / "experiment.json").read_text())
        cls.matrix = json.loads((root / "configs" / "study_matrix.json").read_text())

    def test_core_benchmark_set(self):
        self.assertEqual(set(self.matrix["core_benchmarks"]), {"ult","testgeneval","testexplora","swe_mutation"})

    def test_every_study_reference_resolves(self):
        models=set(self.exp["models"]); benchmarks=set(self.exp["benchmarks"])
        for name, study in self.matrix["studies"].items():
            with self.subTest(study=name):
                for key in ("models","reference_models"):
                    self.assertTrue(set(study.get(key,[])) <= models)
                self.assertTrue(set(study.get("benchmarks",[])) <= benchmarks)
                self.assertTrue(set(study.get("benchmark_pair",[])) <= benchmarks)

    def test_api_energy_guardrail(self):
        for key in ("gpt56sol","claudesonnet5","gemini36flash"):
            self.assertEqual(self.exp["models"][key]["deployment"], "hosted_api")
            self.assertFalse(self.exp["models"][key]["direct_energy_observable"])
        self.assertFalse(self.matrix["guardrails"]["api_provider_energy_estimation"])

    def test_plt_is_diagnostic_not_core(self):
        self.assertNotIn("plt", self.matrix["core_benchmarks"])
        self.assertIn("plt", self.matrix["diagnostic_or_optional_benchmarks"])

if __name__ == "__main__":
    unittest.main()
