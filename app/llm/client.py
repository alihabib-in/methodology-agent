from typing import Any

import httpx

from app.core.config import settings


class LLMError(RuntimeError):
    """Raised when the underlying LLM server cannot be reached or responds badly."""


class LLMClient:
    """Runtime-agnostic client for any OpenAI-compatible LLM server.

    The rest of the application only depends on this interface (``chat``),
    never on llama.cpp, vLLM, CPU or GPU specifics.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        temperature: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = timeout or settings.llm_timeout_seconds
        self.temperature = temperature or settings.llm_temperature

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Unexpected LLM response shape") from exc

    def health(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/models")
                response.raise_for_status()
        except httpx.HTTPError:
            return {"available": False, "model": self.model}
        return {"available": True, "model": self.model}
