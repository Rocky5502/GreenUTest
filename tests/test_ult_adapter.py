import json
import tempfile
import unittest
from pathlib import Path

from greenutest.harness import ULTAdapter


class ULTAdapterTests(unittest.TestCase):
    def _check(self, payload: str):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"ULT_Lite.jsonl"
            path.write_text(payload,encoding="utf-8")
            adapter=ULTAdapter(path, benchmark_name="plt")
            tasks=list(adapter.tasks())
            self.assertEqual(len(tasks),1)
            self.assertEqual(tasks[0].task_id,"10")
            self.assertEqual(tasks[0].benchmark,"plt")
            upstream=tasks[0].metadata["upstream"]
            self.assertNotIn("test_list",upstream)
            self.assertNotIn("tests",upstream)
            self.assertTrue(upstream["reference_tests_present"])
            self.assertEqual(adapter.reference_tests("10"),("assert f(1)==1",))
    def test_json_array_release_shape(self):
        self._check(json.dumps([{"task_id":"10","code":"def f(x): return x","prompt":"test f","test_list":["assert f(1)==1"]}]))
    def test_jsonl_shape(self):
        self._check(json.dumps({"task_id":"10","code":"def f(x): return x","prompt":"test f","test_list":["assert f(1)==1"]})+"\n")

if __name__ == "__main__":
    unittest.main()
