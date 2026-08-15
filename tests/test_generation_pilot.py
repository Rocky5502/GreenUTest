import json
import tempfile
import unittest
from pathlib import Path

from greenutest.harness import FakeModel, ULTAdapter
from greenutest.runner import run_generation_pilot


class GenerationPilotTests(unittest.TestCase):
    def test_generation_pilot_is_explicitly_non_scientific_and_no_reference_leak(self):
        sentinel = "DO_NOT_LEAK_REFERENCE_TEST"
        rows = [{
            "task_id": "u1",
            "code": "def f(x): return x + 1",
            "prompt": "test f",
            "test_list": [sentinel],
        }]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dataset = td / "ULT_Lite.jsonl"
            dataset.write_text(json.dumps(rows), encoding="utf-8")
            adapter = ULTAdapter(dataset)
            runlog = run_generation_pilot(adapter.tasks(), FakeModel("fake", 0.6), td / "out", max_tasks=1)
            text = runlog.read_text(encoding="utf-8")
            self.assertNotIn(sentinel, text)
            record = json.loads(text)
            self.assertFalse(record["metadata"]["scientific_result"])
            self.assertTrue(record["metadata"]["excluded_pilot"])
            self.assertFalse(record["metadata"]["evaluator_reference_tests_accessed"])
            self.assertIsNone(record["outcomes"]["mutation_score"])
            self.assertEqual(record["actions"], ["GENERATE_ONLY"])

    def test_ult_wrapper_rejects_nvml_for_hosted_api_before_call(self):
        from greenutest.runner import run_ult_generation_pilot
        hosted = {"id": "gpt-5.6-sol", "backend": "openai_responses", "deployment": "hosted_api"}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dataset = td / "PLT.jsonl"
            dataset.write_text(json.dumps([{"task_id": "p1", "code": "def f(x): return x", "prompt": "test f"}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "measure-energy"):
                run_ult_generation_pilot(dataset, hosted, td / "out", benchmark_name="plt", measure_energy=True)

    def test_generation_pilot_rejects_zero_tasks(self):
        with self.assertRaises(ValueError):
            run_generation_pilot([], FakeModel("fake", 0.5), ".", max_tasks=0)


if __name__ == "__main__":
    unittest.main()
