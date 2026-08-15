from __future__ import annotations

from .hosted_models import AnthropicMessagesModel, GoogleGenAIModel, OpenAIResponsesModel
from .local_models import TransformersLocalModel, build_local_model_from_config
from .model_base import FakeModel, ModelBackend

def build_model_backend_from_config(config: dict, *, allow_unpinned: bool = False) -> ModelBackend:
    """Construct a lazy backend for either self-hosted or hosted models."""
    backend = config.get("backend")
    if backend == "transformers":
        return build_local_model_from_config(config, allow_unpinned=allow_unpinned)
    if backend == "openai_responses":
        return OpenAIResponsesModel(
            str(config["id"]),
            max_output_tokens=int(config.get("max_output_tokens", 4096)),
            reasoning_effort=config.get("reasoning_effort"),
        )
    if backend == "anthropic_messages":
        return AnthropicMessagesModel(str(config["id"]), int(config.get("max_output_tokens", 4096)))
    if backend == "google_genai":
        return GoogleGenAIModel(str(config["id"]), int(config.get("max_output_tokens", 4096)))
    raise ValueError(f"Unsupported model backend: {backend!r}")

