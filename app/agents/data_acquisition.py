"""Data Acquisition Agent.

Discovers and retrieves relevant datasets from public data portals (World Bank,
Eurostat) based on the case brief, and produces a structured *data evidence
package* that downstream agents cite in the methodology document.

Topic-agnostic: search queries are generated from the case (via the LLM, with a
deterministic fallback) — never from a hardcoded topic. Retrieval is
deterministic and best-effort; if no relevant data is found, the workflow
continues with an empty evidence package.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.research.portals import fetch_portal, search_portal
from app.workflow.contracts import Agent, AgentContract, AgentResult

_QUERY_SYSTEM_PROMPT = """You are a data-discovery assistant for a statistical
methodology agent.

Given a methodology case, propose short search phrases (2-4 words) that are
likely to appear in the TITLES of datasets on public statistical portals such
as the World Bank World Development Indicators and Eurostat.

Map the topic to its underlying measurable statistics. For example, "AI
adoption" maps to digital/ICT adoption statistics: "internet users",
"broadband subscriptions", "research and development expenditure",
"ICT service exports", "high technology exports", "digital skills".

Rules:
- Use common statistical terms, 2-4 words each.
- Do NOT include geography (e.g. "abu dhabi"), years, or the words "rate",
  "index", "methodology", "survey".
- Return 4-6 queries.

Return valid JSON only."""

_QUERY_TEMPLATE = """Case:
Objective: {objective}
Domain: {domain}
Topic: {topic}
Key concepts: {key_concepts}

Return JSON with 4-6 concrete search queries:
{{"queries": ["...", "..."]}}"""

_STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "or", "in", "on", "at", "to", "from",
    "with", "by", "we", "need", "develop", "create", "build", "methodology",
    "based", "data", "index", "indicator", "using", "that", "this", "is", "are",
    "be", "will", "should", "can", "would", "please", "our", "as", "it",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}")


def _significant_words(text: str) -> list[str]:
    words = []
    for word in _WORD_RE.findall(text or ""):
        if word.lower() not in _STOPWORDS and len(word) > 2:
            words.append(word)
    return words


def _deterministic_queries(objective, domain, topic, key_concepts, research_scope) -> list[str]:
    terms: list[str] = []
    for chunk in [objective, topic, domain] + list(key_concepts or []) + list(research_scope or []):
        for word in _significant_words(chunk):
            lowered = word.lower()
            if lowered not in terms:
                terms.append(lowered)
    queries = terms[:5]
    for i in range(min(3, len(terms) - 1)):
        queries.append(f"{terms[i]} {terms[i + 1]}")
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:6]


# Topic keyword -> concrete portal search terms. Maps a statistical domain to
# the measurable datasets behind it (e.g. "AI adoption" -> internet/ICT/R&D
# statistics). This is a generic topic taxonomy, not a single hardcoded topic.
TOPIC_QUERIES: dict[str, list[str]] = {
    "ai": ["internet users", "broadband subscriptions", "research and development expenditure", "high technology exports", "ICT service exports"],
    "artificial": ["internet users", "broadband subscriptions", "research and development expenditure", "high technology exports"],
    "intelligence": ["internet users", "broadband subscriptions", "research and development expenditure", "high technology exports"],
    "digital": ["internet users", "broadband subscriptions", "ICT service exports", "digital skills"],
    "ict": ["ICT service exports", "internet users", "broadband subscriptions"],
    "internet": ["internet users", "broadband subscriptions", "secure internet servers"],
    "broadband": ["broadband subscriptions", "internet users"],
    "technology": ["high technology exports", "research and development expenditure", "ICT service exports"],
    "automation": ["research and development expenditure", "high technology exports", "internet users"],
    "education": ["school enrollment", "education expenditure", "literacy rate", "pupils enrolled"],
    "graduate": ["school enrollment", "education expenditure", "tertiary enrollment"],
    "employment": ["unemployment", "employment rate", "labor force participation"],
    "unemployment": ["unemployment", "labor force participation", "employment rate"],
    "labour": ["unemployment", "labor force participation"],
    "labor": ["unemployment", "labor force participation"],
    "health": ["life expectancy", "mortality rate", "health expenditure"],
    "energy": ["energy intensity", "renewable energy", "electric power consumption"],
    "renewable": ["renewable energy", "electric power consumption"],
    "gdp": ["gdp", "gdp per capita", "gdp growth"],
    "economy": ["gdp", "gdp growth", "inflation"],
    "economic": ["gdp", "gdp growth", "inflation"],
    "inflation": ["inflation", "consumer price index"],
    "price": ["consumer price index", "inflation", "producer price index"],
    "cpi": ["consumer price index", "inflation"],
    "poverty": ["poverty headcount", "poverty gap"],
    "trade": ["exports of goods", "imports of goods", "trade as percentage of gdp"],
    "export": ["exports of goods", "high technology exports"],
    "transport": ["air transport", "rail lines", "container port traffic"],
    "agriculture": ["agricultural land", "agriculture value added", "crop production index"],
    "water": ["water stress", "access to clean water"],
    "population": ["population growth", "population density", "urban population"],
    "tourism": ["international tourism", "tourism receipts"],
    "environment": ["co2 emissions", "renewable energy", "air pollution"],
}


def _topic_queries(objective: str, domain: str, topic: str) -> list[str]:
    text = " ".join([objective, domain, topic]).lower()
    queries: list[str] = []
    for keyword, qs in TOPIC_QUERIES.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            for q in qs:
                if q not in queries:
                    queries.append(q)
    return queries


def _data_text(datasets: list[dict]) -> str:
    if not datasets:
        return "- (no real data retrieved)"
    lines = []
    for d in datasets:
        latest = d.get("latest") or []
        if d.get("portal") == "worldbank":
            sample = "; ".join(f"{v.get('year', '?')}: {v.get('value')}" for v in latest[:3])
        else:
            sample = f"{d.get('data_points', len(latest))} data points"
        lines.append(f"- [{d['portal']}] {d.get('title')} ({d.get('dataset_id')}): {sample}")
    return "\n".join(lines)


class DataAcquisitionAgent(Agent):
    contract = AgentContract(
        id="data_acquisition_agent",
        version="1.0",
        purpose="Discover and retrieve relevant datasets from public data portals for the case.",
        input_schema={"objective": "string", "case_analysis": "object"},
        output_schema={"evidence_package": "object", "datasets": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def _llm_queries(self, objective, domain, topic, key_concepts) -> list[str]:
        prompt = _QUERY_TEMPLATE.format(
            objective=objective or "unspecified",
            domain=domain or "unspecified",
            topic=topic or "unspecified",
            key_concepts=", ".join(key_concepts) or "- (none)",
        )
        try:
            raw = self._llm.chat(_QUERY_SYSTEM_PROMPT, prompt, max_tokens=300)
            data = json.loads(extract_json(raw))
            queries = [q for q in data.get("queries", []) if isinstance(q, str) and q.strip()]
            if queries:
                return queries[:6]
        except Exception:  # noqa: BLE001 - fall back to deterministic queries
            pass
        return []

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        brief = ((inputs or {}).get("case_analysis") or {}).get("case_brief") or {}
        domain = (inputs or {}).get("domain") or brief.get("domain") or ""
        topic = (inputs or {}).get("topic") or brief.get("topic") or ""
        key_concepts = brief.get("key_concepts") or []
        research_scope = brief.get("research_scope") or []

        queries: list[str] = []
        for q in (
            _topic_queries(objective, domain, topic)
            + self._llm_queries(objective, domain, topic, key_concepts)
            + _deterministic_queries(objective, domain, topic, key_concepts, research_scope)
        ):
            if q not in queries:
                queries.append(q)
        queries = queries[:10]

        candidates: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for portal in ("worldbank", "eurostat"):
            for q in queries:
                for ref in search_portal(portal, q, limit=5):
                    key = (ref["portal"], ref["dataset_id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(ref)

        datasets: list[dict] = []
        for ref in candidates:
            if ref["portal"] == "worldbank":
                data = fetch_portal("worldbank", ref["dataset_id"], country="ARE")
            else:
                data = fetch_portal("eurostat", ref["dataset_id"])
            if data:
                datasets.append(data)
            if len(datasets) >= 4:
                break

        evidence = {
            "objective": objective,
            "queries": queries,
            "datasets": datasets,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "evidence_package": evidence,
                "datasets": datasets,
                "reasoning": [
                    f"Generated {len(queries)} search queries for the case.",
                    f"Searched World Bank and Eurostat; found {len(candidates)} candidate datasets.",
                    f"Retrieved {len(datasets)} datasets with real values.",
                ],
            },
            status="succeeded",
        )
