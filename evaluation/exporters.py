"""Write structured JSON artifacts and reports for a run."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationState, MeetingTranscript
from .report import build_html, build_markdown


def write_outputs(transcript: MeetingTranscript, state: EvaluationState, output_dir: str) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "report.md").write_text(build_markdown(transcript, state), encoding="utf-8")
    (out / "report.html").write_text(build_html(transcript, state), encoding="utf-8")
    (out / "state_history.json").write_text(
        json.dumps([h.model_dump() for h in state.history], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "evaluation_state.json").write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    (out / "candidate_scope.json").write_text(
        state.candidate_scope.model_dump_json(indent=2), encoding="utf-8"
    )
    (out / "knowledge_candidates.json").write_text(
        json.dumps([k.model_dump() for k in state.knowledge_candidates], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return sorted(out.iterdir())
