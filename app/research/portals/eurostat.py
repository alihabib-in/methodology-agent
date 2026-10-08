"""Eurostat SDMX 2.1 connector (https://ec.europa.eu/eurostat/api/).

Keyless JSON API. ``fetch`` retrieves a dataset (returns its label, updated
timestamp and a sample of values). ``search`` filters a curated catalogue of
commonly requested datasets by keyword — Eurostat does not expose a simple
full-text search endpoint, so discovery falls back to this catalogue (extendable).
"""

from __future__ import annotations

import re

import httpx

DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

_STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "or", "in", "on", "at", "to", "from",
    "with", "by", "rate", "index", "total", "per", "all", "data", "using",
    "use", "used", "number", "numbers", "people", "population", "country",
}

# (dataset_code, human-readable title). Extend as needed.
CATALOG: list[tuple[str, str]] = [
    ("isoc_eb_ain2", "Artificial intelligence by NACE Rev. 2 activity"),
    ("isoc_eb_ai", "Enterprises using artificial intelligence"),
    ("isoc_ci_in_h", "Households - level of internet access"),
    ("isoc_ci_eu_en2", "Individuals - internet use"),
    ("isoc_ci_im_i", "Individuals - digital skills"),
    ("nama_10_gdp", "GDP and main components (national accounts)"),
    ("une_rt_m", "Unemployment by sex and age - monthly"),
    ("prc_hicp_manr", "HICP - inflation rate"),
    ("lfst_r_lfsd2pop", "Employment rate by sex, age and citizenship"),
    ("educ_uoe_enra", "Pupils and students enrolled in education"),
    ("env_air_emis", "Air emissions accounts"),
    ("t2020_10", "Share of renewable energy in gross final energy consumption"),
]


class EurostatClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[dict]:
        terms = [
            t for t in re.findall(r"[a-z0-9]+", query.lower())
            if len(t) >= 3 and t not in _STOPWORDS
        ]
        scored: list[tuple[int, tuple[str, str]]] = []
        for code, title in CATALOG:
            score = sum(1 for t in terms if re.search(rf"\b{re.escape(t)}\b", title.lower()))
            if score > 0:
                scored.append((score, (code, title)))
        scored.sort(key=lambda pair: -pair[0])
        matches = []
        for _score, (code, title) in scored[:limit]:
            matches.append(
                {"portal": "eurostat", "dataset_id": code, "title": title, "source_note": ""}
            )
        return matches

    def fetch(self, dataset_id: str, limit: int = 5) -> dict:
        url = f"{DATA_URL}/{dataset_id}"
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.get(url, params={"format": "JSON", "lang": "en"})
            resp.raise_for_status()
            data = resp.json()

        values = data.get("value") or {}
        dims = data.get("id") or []
        sample = [
            {"cell": key, "value": value}
            for key, value in list(values.items())[:limit]
        ]

        return {
            "portal": "eurostat",
            "dataset_id": dataset_id,
            "title": data.get("label", dataset_id),
            "latest": sample,
            "dimensions": dims,
            "data_points": len(values),
            "updated": data.get("updated"),
            "url": url,
        }
