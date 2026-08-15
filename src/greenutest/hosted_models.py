from __future__ import annotations

import time
from typing import Any

from .model_base import ModelBackend
from .schemas import CandidateTest, Task

class HostedAPIModel(ModelBackend):
    """Base class for hosted-provider models.

    Provider-side energy is intentionally *not* estimated. Implementations log observable
    usage/latency metadata, while uncertainty must come from signals the provider actually
    exposes (for example behavioral disagreement, execution, or independent-oracle checks).
    """

    provider: str = "unknown"

    def __init__(self, model_id: str, max_output_tokens: int = 4096):
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens

    @staticmethod
    def _prompt(task: Task) -> tuple[str, str]:
        system = (
            "You are a software-testing assistant. Generate concise executable tests. "
            "Do not assume hidden evaluator tests, repair patches, or reference outputs are available."
        )
        user = f"CODE:\n{task.code}\n\nTESTING TASK:\n{task.prompt}\n"
        return system, user

    @staticmethod
    def _usage_dict(obj: Any) -> dict[str, Any]:
        if obj is None:
            return {}
        if hasattr(obj, "model_dump"):
            try:
                return dict(obj.model_dump())
            except Exception:
                pass
        out = {}
        for name in (
            "input_tokens", "output_tokens", "total_tokens", "prompt_token_count",
            "candidates_token_count", "total_token_count", "cache_creation_input_tokens",
            "cache_read_input_tokens",
        ):
            value = getattr(obj, name, None)
            if value is not None:
                out[name] = value
        return out

    def _candidate(self, text: str, *, seed: int, latency_s: float, metadata: dict[str, Any]) -> CandidateTest:
        metadata = {
            "provider": self.provider,
            "deployment": "hosted_api",
            "seed_requested": seed,
            "provider_seed_controlled": False,
            "latency_s": latency_s,
            "direct_energy_observable": False,
            "provider_energy_joules": None,
            "confidence_definition": None,
            **metadata,
        }
        return CandidateTest(text, self.model_id, raw_confidence=None, token_nll=None, metadata=metadata)


class OpenAIResponsesModel(HostedAPIModel):
    provider = "openai"

    def __init__(self, model_id: str, max_output_tokens: int = 4096, reasoning_effort: str | None = None):
        super().__init__(model_id, max_output_tokens)
        self.reasoning_effort = reasoning_effort

    def generate(self, task: Task, *, seed: int) -> CandidateTest:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install GreenUTest with the remote-api extra") from exc
        system, user = self._prompt(task)
        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "input": f"SYSTEM:\n{system}\n\nUSER:\n{user}",
            "max_output_tokens": self.max_output_tokens,
        }
        if self.reasoning_effort:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        start = time.perf_counter()
        response = OpenAI().responses.create(**kwargs)
        latency = time.perf_counter() - start
        text = getattr(response, "output_text", "") or ""
        return self._candidate(
            text, seed=seed, latency_s=latency,
            metadata={
                "api_response_id": getattr(response, "id", None),
                "response_model": getattr(response, "model", None),
                "usage": self._usage_dict(getattr(response, "usage", None)),
                "reasoning_effort": self.reasoning_effort,
            },
        )


class AnthropicMessagesModel(HostedAPIModel):
    provider = "anthropic"

    def generate(self, task: Task, *, seed: int) -> CandidateTest:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install GreenUTest with the remote-api extra") from exc
        system, user = self._prompt(task)
        start = time.perf_counter()
        response = Anthropic().messages.create(
            model=self.model_id,
            max_tokens=self.max_output_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency = time.perf_counter() - start
        chunks = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        return self._candidate(
            "".join(chunks), seed=seed, latency_s=latency,
            metadata={
                "api_response_id": getattr(response, "id", None),
                "response_model": getattr(response, "model", None),
                "usage": self._usage_dict(getattr(response, "usage", None)),
                "sampling_parameters": "provider_defaults",
            },
        )


class GoogleGenAIModel(HostedAPIModel):
    provider = "google"

    def generate(self, task: Task, *, seed: int) -> CandidateTest:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install GreenUTest with the remote-api extra") from exc
        system, user = self._prompt(task)
        config = types.GenerateContentConfig(max_output_tokens=self.max_output_tokens)
        start = time.perf_counter()
        response = genai.Client().models.generate_content(
            model=self.model_id,
            contents=f"SYSTEM:\n{system}\n\nUSER:\n{user}",
            config=config,
        )
        latency = time.perf_counter() - start
        return self._candidate(
            getattr(response, "text", "") or "", seed=seed, latency_s=latency,
            metadata={
                "response_model": getattr(response, "model_version", None),
                "usage": self._usage_dict(getattr(response, "usage_metadata", None)),
                "sampling_parameters": "provider_defaults",
            },
        )


