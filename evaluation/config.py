"""Configuration for the evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalConfig:
    mode: str = "mock"  # "production" | "local" | "mock"
    llm_base_url: str = "http://localhost:8080/v1"
    llm_model: str = "qwen3-4b-instruct-2507"
    llm_timeout: float = 120.0
    llm_temperature: float = 0.1
    batch_size: int = 5  # transcript segments processed per incremental batch
    use_rag: bool = False
    output_dir: str = "evaluation/output"
    input: str | None = None
    run: str | None = None  # path to a prior run for `review`

    def output_for(self, meeting_id: str) -> str:
        return f"{self.output_dir}/{meeting_id}"
