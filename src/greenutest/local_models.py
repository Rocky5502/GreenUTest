from __future__ import annotations

import hashlib
import math

from .model_base import ModelBackend
from .schemas import CandidateTest, Task

class TransformersLocalModel(ModelBackend):
    """Local Hugging Face backend with generated-token uncertainty telemetry.

    Heavy dependencies are imported lazily in ``load`` so configuration/preflight checks remain
    CPU-only. ``raw_confidence`` is the geometric mean probability of generated tokens and is
    intentionally treated as an *uncalibrated* signal. ``token_nll`` is the mean negative
    log-likelihood over generated tokens.
    """

    def __init__(
        self,
        model_id: str,
        revision: str | None = None,
        max_new_tokens: int = 1024,
        temperature: float = 0.2,
        top_p: float = 0.95,
        do_sample: bool = True,
        trust_remote_code: bool = False,
    ):
        self.model_id = model_id
        self.revision = revision
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        self.trust_remote_code = trust_remote_code
        self.model = None
        self.tok = None
        self.resolved_model_revision = None
        self.resolved_tokenizer_revision = None

    def load(self):
        if self.model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Install GreenUTest with the local-hf extra") from exc
        self.tok = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            trust_remote_code=self.trust_remote_code,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            revision=self.revision,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=self.trust_remote_code,
        )
        self.resolved_model_revision = getattr(self.model.config, "_commit_hash", None)
        self.resolved_tokenizer_revision = getattr(self.tok, "init_kwargs", {}).get("_commit_hash")

    def _prompt(self, task: Task) -> str:
        system = (
            "You are a software-testing assistant. Generate concise executable Python tests. "
            "Do not assume hidden evaluator tests or reference outputs are available."
        )
        user = f"CODE:\n{task.code}\n\nTESTING TASK:\n{task.prompt}\n"
        if self.tok is not None and getattr(self.tok, "chat_template", None):
            return self.tok.apply_chat_template(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                tokenize=False,
                add_generation_prompt=True,
            )
        return f"SYSTEM:\n{system}\n\nUSER:\n{user}\n\nASSISTANT:\n"

    def generate(self, task: Task, *, seed: int) -> CandidateTest:
        self.load()
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        prompt = self._prompt(task)
        encoded = self.tok(prompt, return_tensors="pt")
        encoded = {k: v.to(self.model.device) for k, v in encoded.items()}
        input_len = encoded["input_ids"].shape[1]
        gen_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.do_sample,
            "return_dict_in_generate": True,
            "output_scores": True,
            "pad_token_id": self.tok.eos_token_id,
        }
        if self.do_sample:
            gen_kwargs.update({"temperature": self.temperature, "top_p": self.top_p})
        with torch.inference_mode():
            out = self.model.generate(**encoded, **gen_kwargs)
        generated = out.sequences[0, input_len:]
        text = self.tok.decode(generated, skip_special_tokens=True)

        token_logps: list[float] = []
        for step_scores, token_id in zip(out.scores, generated):
            logp = torch.log_softmax(step_scores[0].float(), dim=-1)[int(token_id.item())]
            token_logps.append(float(logp.item()))
        token_nll = -sum(token_logps) / len(token_logps) if token_logps else None
        raw_confidence = math.exp(-token_nll) if token_nll is not None else None

        return CandidateTest(
            text,
            self.model_id,
            raw_confidence=raw_confidence,
            token_nll=token_nll,
            metadata={
                "seed": seed,
                "requested_revision": self.revision,
                "resolved_model_revision": self.resolved_model_revision,
                "resolved_tokenizer_revision": self.resolved_tokenizer_revision,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_tokens": int(input_len),
                "generated_tokens": int(generated.numel()),
                "do_sample": self.do_sample,
                "temperature": self.temperature if self.do_sample else None,
                "top_p": self.top_p if self.do_sample else None,
                "confidence_definition": "geometric_mean_generated_token_probability",
            },
        )


def build_local_model_from_config(config: dict, *, allow_unpinned: bool = False) -> TransformersLocalModel:
    """Construct a local HF backend from a frozen model configuration.

    Confirmatory callers should keep ``allow_unpinned=False``. The excluded hardware pilot may
    set it to True; the resolved Hub commit hashes emitted in CandidateTest metadata must then be
    copied into the frozen configuration before held-out execution.
    """

    if config.get("backend") != "transformers":
        raise ValueError(f"Unsupported local backend: {config.get('backend')!r}")
    revision = config.get("revision")
    unresolved = revision is None or str(revision).startswith("TBD")
    if unresolved and not allow_unpinned:
        raise ValueError("Model revision is unresolved; pin it before confirmatory execution")
    if unresolved:
        revision = None
    quantization = config.get("quantization")
    if quantization and not str(quantization).startswith("TBD") and str(quantization).lower() not in {"none", "false"}:
        raise NotImplementedError(
            "Quantized loading must be explicitly implemented and validated before freezing; "
            f"got {quantization!r}"
        )
    return TransformersLocalModel(
        str(config["id"]),
        revision=revision,
        max_new_tokens=int(config.get("max_new_tokens", 1024)),
        temperature=float(config.get("temperature", 0.2)),
        top_p=float(config.get("top_p", 0.95)),
        do_sample=bool(config.get("do_sample", True)),
        trust_remote_code=bool(config.get("trust_remote_code", False)),
    )



