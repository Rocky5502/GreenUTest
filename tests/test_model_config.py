import json
import unittest
from pathlib import Path

from greenutest.harness import (
    AnthropicMessagesModel,
    GoogleGenAIModel,
    OpenAIResponsesModel,
    TransformersLocalModel,
    build_local_model_from_config,
    build_model_backend_from_config,
)


class ModelConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.models = json.loads((root / "configs" / "experiment.json").read_text())["models"]

    def test_confirmatory_local_factory_rejects_unpinned_models(self):
        with self.assertRaises(ValueError):
            build_local_model_from_config(self.models["qwen25coder15b"])

    def test_pilot_local_factory_is_lazy(self):
        model = build_local_model_from_config(self.models["qwen25coder15b"], allow_unpinned=True)
        self.assertIsInstance(model, TransformersLocalModel)
        self.assertIsNone(model.model)
        self.assertIsNone(model.tok)

    def test_seven_core_models_are_present(self):
        core = {k for k,v in self.models.items() if str(v.get("study_tier","")).startswith("core_")}
        self.assertEqual(core, {"qwen25coder15b","qwen25coder7b","qwen3coder30ba3b","qwen3codernext","gpt56sol","claudesonnet5","gemini36flash"})

    def test_hosted_factories_are_lazy_and_provider_specific(self):
        cases = {
            "gpt56sol": OpenAIResponsesModel,
            "claudesonnet5": AnthropicMessagesModel,
            "gemini36flash": GoogleGenAIModel,
        }
        for key, cls in cases.items():
            with self.subTest(model=key):
                backend = build_model_backend_from_config(self.models[key], allow_unpinned=True)
                self.assertIsInstance(backend, cls)
                self.assertFalse(self.models[key]["direct_energy_observable"])

    def test_local_core_models_are_direct_energy_observable(self):
        for key in ("qwen25coder15b","qwen25coder7b","qwen3coder30ba3b","qwen3codernext"):
            self.assertEqual(self.models[key]["backend"], "transformers")
            self.assertTrue(self.models[key]["direct_energy_observable"])
            self.assertFalse(self.models[key]["trust_remote_code"])

    def test_provider_sampling_constraints_are_not_overridden(self):
        self.assertNotIn("temperature", self.models["claudesonnet5"])
        self.assertNotIn("top_p", self.models["claudesonnet5"])
        self.assertNotIn("temperature", self.models["gemini36flash"])
        self.assertNotIn("top_p", self.models["gemini36flash"])


if __name__ == "__main__":
    unittest.main()
