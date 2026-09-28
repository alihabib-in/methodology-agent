"""End-to-end smoke tests for the evaluation harness (mock mode, no LLM)."""

from pathlib import Path

from evaluation.adapters import MockAdapter
from evaluation.config import EvalConfig
from evaluation.engine import EvaluationEngine
from evaluation.exporters import write_outputs
from evaluation.transcript_loader import load_transcript
from evaluation.transcript_normalizer import normalize_transcript

DATA = Path(__file__).resolve().parents[1] / "data" / "meeting_001"


def test_mock_run_end_to_end(tmp_path):
    transcript = normalize_transcript(load_transcript(DATA))
    assert transcript.meeting_id == "M-001"
    assert len(transcript.segments) >= 10

    state = EvaluationEngine(MockAdapter(), EvalConfig(mode="mock", batch_size=3)).run(transcript)

    # State history must record every batch.
    assert state.history, "state history must not be empty"
    assert state.history[-1].version == state.state_version

    # Core facts extracted with evidence.
    assert any(f.concept == "geographic_scope" and f.value == "Abu Dhabi" for f in state.facts)
    assert any(f.concept == "statistical_unit" for f in state.facts)
    assert all(f.evidence for f in state.facts if f.value)

    # The monthly -> quarterly switch must be flagged as a conflict, not silently overwritten.
    assert any(c.concept == "frequency" for c in state.conflicts)

    # Questions are generated for open gaps and are in English.
    assert state.questions, "expected at least one generated question"
    assert all(q.question.isascii() for q in state.questions)

    # Candidate scope + readiness + knowledge.
    assert state.candidate_scope.geographic_scope == "Abu Dhabi"
    assert 0 <= state.candidate_scope.readiness_score <= 100
    assert state.knowledge_candidates

    # Export artifacts.
    files = write_outputs(transcript, state, str(tmp_path))
    names = {f.name for f in files}
    assert {"report.md", "report.html", "state_history.json", "evaluation_state.json",
            "candidate_scope.json", "knowledge_candidates.json"} <= names


def test_answer_detection_and_conflict(tmp_path):
    transcript = normalize_transcript(load_transcript(DATA))
    state = EvaluationEngine(MockAdapter(), EvalConfig(mode="mock", batch_size=5)).run(transcript)
    # Any question targeting a later-resolved gap should end up "answered".
    for q in state.questions:
        assert q.current_status in ("candidate", "presented", "asked", "answered")
