import json
import re
import unittest
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")

class ManifestPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.manifest = json.loads((root / "data" / "upstreams.json").read_text())

    def test_every_benchmark_source_has_immutable_commit(self):
        for name, spec in self.manifest["sources"].items():
            with self.subTest(source=name):
                self.assertRegex(spec["pinned_commit"], HEX40)

    def test_pinned_code_baseline_sources_are_immutable(self):
        for name in ("starouter", "pynguin"):
            self.assertRegex(self.manifest["baseline_sources"][name]["pinned_commit"], HEX40)

    def test_ult_family_selected_files_have_blob_identity(self):
        ult = self.manifest["sources"]["ult"]
        for key in ("git_blob_sha", "lite_git_blob_sha", "plt_git_blob_sha"):
            self.assertRegex(ult[key], HEX40)
        self.assertGreater(ult["plt_size_bytes"], ult["size_bytes"])
        self.assertGreater(ult["size_bytes"], ult["lite_size_bytes"])

    def test_testgeneval_full_is_canonical_confirmatory_dataset(self):
        tge = self.manifest["sources"]["testgeneval"]
        self.assertEqual(tge["dataset_full"], "kjain14/testgeneval")
        self.assertEqual(tge["dataset_lite"], "kjain14/testgenevallite")

if __name__ == "__main__":
    unittest.main()
