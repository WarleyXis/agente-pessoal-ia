from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class OllamaTiming:
    model: str | None = None
    load_ns: int = 0
    prompt_ns: int = 0
    generation_ns: int = 0
    calls: int = 0

    def record(self, payload: dict) -> None:
        fields = ("load_duration", "prompt_eval_duration", "eval_duration")
        values = [payload.get(key) for key in fields]
        if any(type(value) is int for value in values):
            load, prompt, generation = (
                max(value, 0) if type(value) is int else 0 for value in values
            )
            self.load_ns += load
            self.prompt_ns += prompt
            self.generation_ns += generation
            self.calls += 1

    def public_data(self) -> dict:
        return {
            "model": self.model,
            "load_ms": round(self.load_ns / 1_000_000),
            "prompt_ms": round(self.prompt_ns / 1_000_000),
            "generation_ms": round(self.generation_ns / 1_000_000),
            "calls": self.calls,
        }


current_timing: ContextVar[OllamaTiming | None] = ContextVar("ollama_timing", default=None)
