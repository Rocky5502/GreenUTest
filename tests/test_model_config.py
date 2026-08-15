import json
import unittest
from pathlib import Path

from greenutest.harness import TransformersLocalModel, build_local_model_from_config


class ModelConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.models = json.loads((root / "configs" / "experiment.json").read_text())["models"]

    def test_confirmatory_factory_rejects_unpinned_models(self):
        with self.assertRaises(ValueError):
            build_local_model_from_config(self.models["qwen25coder15b"])

    def test_pilot_factory_is_lazy_and_keeps_generation_settings(self):
        model = build_local_model_from_config(self.models["qwen25coder15b"], allow_unpinned=True)
        self.assertIsInstance(model, TransformersLocalModel)
        self.assertIsNone(model.model)
        self.assertIsNone(model.tok)
        self.assertTrue(model.do_sample)
        self.assertAlmostEqual(model.temperature, 0.2)
        self.assertAlmostEqual(model.top_p, 0.95)

    def test_all_primary_models_are_local_transformers(self):
        for cfg in self.models.values():
            self.assertEqual(cfg["backend"], "transformers")
            self.assertFalse(cfg["trust_remote_code"])


if __name__ == "__main__":
    unittest.main()
