"""Public data portal connectors for the data acquisition agent.

Each connector exposes ``search(query)`` and ``fetch(dataset_id)`` so the agent
can dynamically discover and retrieve datasets by topic, without knowing any
dataset in advance. Retrieval is deterministic (real API calls) and failures
degrade gracefully (empty results) rather than crashing the workflow.
"""

from __future__ import annotations

from app.research.portals.eurostat import EurostatClient
from app.research.portals.worldbank import WorldBankClient

PORTALS: dict[str, object] = {
    "worldbank": WorldBankClient(),
    "eurostat": EurostatClient(),
}


def search_portal(name: str, query: str, limit: int = 5) -> list[dict]:
    portal = PORTALS.get(name)
    if portal is None:
        return []
    try:
        return portal.search(query, limit=limit)
    except Exception:  # noqa: BLE001 - best-effort retrieval
        return []


def fetch_portal(name: str, dataset_id: str, **kwargs) -> dict | None:
    portal = PORTALS.get(name)
    if portal is None:
        return None
    try:
        return portal.fetch(dataset_id, **kwargs)
    except Exception:  # noqa: BLE001 - best-effort retrieval
        return None
