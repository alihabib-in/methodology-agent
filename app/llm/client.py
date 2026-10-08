from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings

_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 15.0


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

        last_error: Exception | None = None
        for attempt in range(_RETRIES):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.NetworkError, httpx.ProtocolError) as exc:
                # The local llama.cpp server can crash/restart under load.
                # These fail fast, so retry after giving it time to reload.
                last_error = exc
                time.sleep(_RETRY_BACKOFF_SECONDS)
            except (KeyError, IndexError, TypeError) as exc:
                # A transient/malformed body (e.g. mid-restart) — retry.
                last_error = exc
                time.sleep(_RETRY_BACKOFF_SECONDS)
            except httpx.TimeoutException as exc:
                # Genuinely slow; don't multiply the wait with retries.
                raise LLMError(f"LLM request timed out: {exc}") from exc
            except httpx.HTTPError as exc:
                raise LLMError(f"LLM request failed: {exc}") from exc

        raise LLMError(f"LLM request failed after {_RETRIES} attempts: {last_error}")

    def health(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/models")
                response.raise_for_status()
        except httpx.HTTPError:
            return {"available": False, "model": self.model}
        return {"available": True, "model": self.model}
