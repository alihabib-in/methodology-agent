"""Minimal web client for research verification (Phase E).

Fetches a URL and extracts readable text, gated by the credibility policy. Only
credible sources are fetched; user-generated content is never retrieved.
"""

from __future__ import annotations

import re

import httpx

from app.research.sources import is_credible

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)


def extract_text(html: str) -> str:
    html = _SCRIPT_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class WebClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch(self, url: str) -> dict:
        if not is_credible(url):
            return {"url": url, "allowed": False, "reason": "not a credible source"}

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPError as exc:
            return {"url": url, "allowed": True, "error": str(exc)}

        return {"url": url, "allowed": True, "text": extract_text(html)[:4000]}
