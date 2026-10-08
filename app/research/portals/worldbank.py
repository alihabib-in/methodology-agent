"""World Bank Data API connector (https://api.worldbank.org/v2/).

Keyless JSON API. ``search`` filters the World Development Indicators catalogue
by keyword (cached in-memory); ``fetch`` returns the latest values for a given
country (ISO3, default ARE = United Arab Emirates).
"""

from __future__ import annotations

import re

import httpx

INDICATORS_URL = "https://api.worldbank.org/v2/indicator"
DATA_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{code}"

_catalogue_cache: list[dict] | None = None

_STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "or", "in", "on", "at", "to", "from",
    "with", "by", "rate", "index", "total", "per", "all", "data", "using",
    "use", "used", "number", "numbers", "people", "population", "country",
}


def _score(name: str, query: str) -> int:
    terms = [
        t for t in re.findall(r"[a-z0-9]+", query.lower())
        if len(t) >= 3 and t not in _STOPWORDS
    ]
    if not terms:
        return 0
    lowered = name.lower()
    return sum(1 for t in terms if re.search(rf"\b{re.escape(t)}\b", lowered))


class WorldBankClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def _catalogue(self) -> list[dict]:
        global _catalogue_cache
        if _catalogue_cache is None:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(
                    INDICATORS_URL,
                    params={"format": "json", "source": 2, "per_page": 2000},
                )
                resp.raise_for_status()
                data = resp.json()
            _catalogue_cache = data[1] if isinstance(data, list) and len(data) > 1 else []
        return _catalogue_cache

    def search(self, query: str, limit: int = 5) -> list[dict]:
        scored: list[tuple[int, dict]] = []
        for ind in self._catalogue():
            score = _score(ind.get("name") or "", query)
            if score > 0:
                scored.append((score, ind))
        scored.sort(key=lambda pair: -pair[0])
        matches = []
        for _score_val, ind in scored[:limit]:
            matches.append(
                {
                    "portal": "worldbank",
                    "dataset_id": ind.get("id"),
                    "title": ind.get("name"),
                    "source_note": (ind.get("sourceNote") or "")[:200],
                }
            )
        return matches

    def fetch(self, dataset_id: str, country: str = "ARE", limit: int = 5) -> dict:
        url = DATA_URL.format(country=country, code=dataset_id)
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.get(url, params={"format": "json", "per_page": limit})
            resp.raise_for_status()
            data = resp.json()

        rows = data[1] if isinstance(data, list) and len(data) > 1 else []
        title = dataset_id
        latest: list[dict] = []
        for row in rows:
            if row.get("value") is None:
                continue
            title = row.get("indicator", {}).get("value", title)
            latest.append(
                {
                    "country": row.get("country", {}).get("value", country),
                    "year": row.get("date"),
                    "value": row.get("value"),
                }
            )

        return {
            "portal": "worldbank",
            "dataset_id": dataset_id,
            "title": title,
            "latest": latest[:limit],
            "url": url,
        }
