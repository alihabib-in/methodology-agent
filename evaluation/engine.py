"""Incremental methodology evaluation engine.

Simulates the real meeting progression: processes transcript segments in
batches, updating the methodology state each time, and records facts (with
evidence), gaps, questions (with lifecycle), answers, conflicts, and state
history.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.agent.terminology import detect_language
from app.models.methodology_state import MethodologyState

from .adapters import Adapter
from .config import EvalConfig
from .models import (
    CandidateScope,
    Conflict,
    EvaluationState,
    Evidence,
    Fact,
    Gap,
    KnowledgeCandidate,
    Question,
    QuestionStatus,
    StateVersion,
)

_REQUIREMENT_LISTS = (
    "statistical_units",
    "populations",
    "reference_periods",
    "frequencies",
    "geographic_scopes",
    "indicators",
    "dimensions",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_batch(batch) -> str:
    lines = []
    for s in batch:
        speaker = s.speaker_id or "unknown"
        lines.append(f"[{speaker} @ {s.timestamp_start}] {s.text}")
    return "\n".join(lines)


def _batch_evidence(batch) -> list[Evidence]:
    return [
        Evidence(
            segment_id=s.segment_id,
            speaker_id=s.speaker_id,
            timestamp_start=s.timestamp_start,
            timestamp_end=s.timestamp_end,
            original_text=s.text,
            language=s.language,
        )
        for s in batch
    ]


def _facts_from_extraction(extraction: dict, evidence: list[Evidence]) -> list[Fact]:
    facts: list[Fact] = []
    for req in extraction.get("requirements", []):
        facts.append(Fact(concept=req.get("concept", ""), value=req.get("value"),
                          status=req.get("status", "unknown"), confidence=req.get("confidence", 0.0), evidence=evidence))
    for d in extraction.get("definitions", []):
        facts.append(Fact(concept=f"definition:{d.get('concept', '')}", value=d.get("statement"),
                          status=d.get("status", "unknown"), confidence=d.get("confidence", 0.0), evidence=evidence))
    for d in extraction.get("data_sources", []):
        facts.append(Fact(concept="data_source", value=d.get("name"),
                          status=d.get("status", "unknown"), confidence=d.get("confidence", 0.0), evidence=evidence))
    for list_name in _REQUIREMENT_LISTS:
        for item in extraction.get(list_name, []):
            concept = item.get("concept") or {
                "statistical_units": "statistical_unit",
                "populations": "target_population",
                "reference_periods": "reference_period",
                "frequencies": "frequency",
                "geographic_scopes": "geographic_scope",
                "indicators": "indicator",
                "dimensions": "dimension",
            }.get(list_name, list_name)
            facts.append(Fact(concept=concept, value=item.get("value"),
                              status=item.get("status", "unknown"), confidence=item.get("confidence", 0.0), evidence=evidence))
    return [f for f in facts if f.concept and (f.value or f.status != "unknown")]


class EvaluationEngine:
    def __init__(self, adapter: Adapter, config: EvalConfig) -> None:
        self.adapter = adapter
        self.config = config

    def run(self, transcript) -> EvaluationState:
        state = EvaluationState(meeting_id=transcript.meeting_id, title=transcript.title)
        methodology = MethodologyState()
        segments = transcript.segments
        batches = [segments[i:i + self.config.batch_size] for i in range(0, len(segments), self.config.batch_size)]

        for batch in batches:
            text = format_batch(batch)
            language = detect_language(text)
            result = self.adapter.analyze(text, language, methodology)

            if result.get("parse_error"):
                self._record_version(state, "Parse error (LLM output invalid)", methodology)
                continue

            evidence = _batch_evidence(batch)
            new_facts = _facts_from_extraction(result.get("extraction", {}), evidence)
            self._merge_facts(state, new_facts)

            objective = result.get("methodology_state", {}).get("objective") or {}
            if objective.get("value"):
                self._record_objective(state, objective, evidence)

            state.gaps = [Gap(concept=g.get("domain", ""), status=g.get("status", "open"),
                              priority=g.get("priority", 0.0), reason=g.get("reason", ""))
                          for g in result.get("gaps", [])]

            self._detect_answers(state)
            self._maybe_generate_question(state, result.get("recommended_question"))

            self._record_version(state, f"Processed {len(batch)} segments", methodology)

        state.candidate_scope = self._build_candidate_scope(methodology, state)
        state.knowledge_candidates = self._extract_knowledge(methodology)
        return state

    # -- fact merging + conflict detection ---------------------------------

    def _merge_facts(self, state: EvaluationState, new_facts: list[Fact]) -> None:
        for new in new_facts:
            existing = next((f for f in state.facts if f.concept == new.concept), None)
            if existing is None:
                state.facts.append(new)
                continue
            if (existing.value or "").strip().lower() == (new.value or "").strip().lower():
                existing.confidence = max(existing.confidence, new.confidence)
                existing.evidence = (existing.evidence + new.evidence)[:20]
                continue
            if existing.status == "confirmed" and new.status in ("confirmed", "proposed", "inferred"):
                if not any(c.concept == new.concept and c.status == "unresolved" for c in state.conflicts):
                    state.conflicts.append(
                        Conflict(
                            concept=new.concept,
                            existing_value=existing.value,
                            new_value=new.value,
                            evidence=new.evidence,
                        )
                    )
                existing.status = "contradicted"
                continue
            existing.value = new.value
            existing.status = new.status
            existing.confidence = new.confidence
            existing.evidence = new.evidence

    def _record_objective(self, state: EvaluationState, objective: dict, evidence: list[Evidence]) -> None:
        fact = Fact(concept="objective", value=objective.get("value"),
                    status=objective.get("status", "unknown"), confidence=objective.get("confidence", 0.0), evidence=evidence)
        if not state.objective_history or state.objective_history[-1].value != fact.value:
            state.objective_history.append(fact)

    # -- questions ----------------------------------------------------------

    def _maybe_generate_question(self, state: EvaluationState, recommended: dict | None) -> None:
        if not state.gaps:
            return
        top = state.gaps[0]
        existing = [q for q in state.questions if q.target_gap == top.concept and q.current_status in ("candidate", "presented", "asked")]
        if existing:
            return
        question = (recommended or {}).get("question") or f"Please clarify: {top.reason}"
        why = (recommended or {}).get("reason") or top.reason
        q = Question(
            question_id=f"Q{len(state.questions) + 1:03d}",
            question=question,
            target_gap=top.concept,
            priority=top.priority,
            why_asked=why,
            status_history=[QuestionStatus(status="candidate", timestamp=_now())],
        )
        state.questions.append(q)

    def _detect_answers(self, state: EvaluationState) -> None:
        open_gap_concepts = {g.concept for g in state.gaps}
        for q in state.questions:
            if q.current_status in ("candidate", "presented", "asked") and q.target_gap not in open_gap_concepts:
                q.status_history.append(QuestionStatus(status="answered", timestamp=_now()))

    # -- versioning ---------------------------------------------------------

    def _record_version(self, state: EvaluationState, note: str, methodology: MethodologyState) -> None:
        state.state_version += 1
        state.history.append(
            StateVersion(
                version=state.state_version,
                note=note,
                timestamp=_now(),
                snapshot=methodology.model_dump(),
            )
        )

    # -- finalization -------------------------------------------------------

    @staticmethod
    def _build_candidate_scope(methodology: MethodologyState, state: EvaluationState) -> CandidateScope:
        def value(field) -> str:
            f = getattr(methodology, field, None)
            return (f.value or "") if f else ""

        return CandidateScope(
            objective=value("objective"),
            population=value("target_population"),
            statistical_unit=value("statistical_unit"),
            reference_period=value("reference_period"),
            geographic_scope=value("geographic_scope"),
            indicators=[i.get("value") or i.get("concept", "") for i in methodology.indicators],
            dimensions=[d.get("value") or d.get("concept", "") for d in methodology.dimensions],
            data_sources=[s.get("name") or s.get("concept", "") for s in methodology.data_sources],
            definitions=[{d.get("concept", ""): d.get("statement", "")} for d in methodology.definitions],
            constraints=[c.get("value") or c.get("concept", "") for c in methodology.constraints],
            open_questions=[q.question for q in state.questions if q.current_status not in ("answered",)],
            readiness_score=_readiness_score(methodology, state),
            readiness_status=_readiness_status(methodology, state),
        )

    @staticmethod
    def _extract_knowledge(methodology: MethodologyState) -> list[KnowledgeCandidate]:
        items: list[KnowledgeCandidate] = []
        for d in methodology.definitions:
            items.append(KnowledgeCandidate(
                knowledge_type="definition",
                concept=d.get("concept", "definition"),
                statement=d.get("statement", ""),
                status="candidate",
                confidence=d.get("confidence", 0.0),
            ))
        for s in methodology.data_sources:
            items.append(KnowledgeCandidate(
                knowledge_type="data_source",
                concept=s.get("name", "data_source"),
                statement=s.get("name", ""),
                status="candidate",
                confidence=s.get("confidence", 0.0),
            ))
        return items


CORE_FIELDS = ("objective", "target_population", "statistical_unit", "reference_period", "frequency", "geographic_scope")


def _readiness_score(methodology: MethodologyState, state: EvaluationState) -> float:
    total = len(CORE_FIELDS)
    resolved = sum(1 for f in CORE_FIELDS if getattr(methodology, f).status == "confirmed")
    # Definitions and data sources contribute as well.
    total += 2
    resolved += 1 if methodology.definitions else 0
    resolved += 1 if methodology.data_sources else 0
    score = round(resolved / max(1, total) * 100)
    # Unresolved conflicts cap the score.
    if state.conflicts:
        score = min(score, 60)
    return score


def _readiness_status(methodology: MethodologyState, state: EvaluationState) -> str:
    if state.conflicts:
        return "in_progress"
    if _readiness_score(methodology, state) >= 80:
        return "ready_for_review"
    if _readiness_score(methodology, state) >= 50:
        return "in_progress"
    return "insufficient"
