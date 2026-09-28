"""Generate human-readable evaluation reports (Markdown + self-contained HTML)."""

from __future__ import annotations

import re

from .models import EvaluationState, MeetingTranscript
from .transcript_normalizer import language_breakdown


def _lang_pct(t: MeetingTranscript) -> str:
    bd = language_breakdown(t)
    return ", ".join(f"{k.upper()} {v}%" for k, v in bd.items()) or "Unknown"


def _duration(t: MeetingTranscript) -> str:
    if not t.segments:
        return "0:00"
    return t.segments[-1].timestamp_end or t.segments[-1].timestamp_start or "0:00"


def _speakers(t: MeetingTranscript) -> int:
    return len({s.speaker_id for s in t.segments if s.speaker_id})


def _objective(eval_state: EvaluationState) -> str:
    if eval_state.objective_history:
        return eval_state.objective_history[-1].value or "(not detected)"
    return "(not detected)"


def build_markdown(t: MeetingTranscript, s: EvaluationState) -> str:
    lines: list[str] = []
    lines.append(f"# Methodology Evaluation Report — {t.title or t.meeting_id}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Meeting**: {t.title or t.meeting_id}")
    lines.append(f"- **Languages**: {_lang_pct(t)}")
    lines.append(f"- **Duration**: {_duration(t)}")
    lines.append(f"- **Speakers**: {_speakers(t)}")
    lines.append(f"- **Segments**: {len(t.segments)}")
    lines.append(f"- **Final objective**: {_objective(s)}")
    lines.append(f"- **Methodology readiness**: {s.candidate_scope.readiness_score}% ({s.candidate_scope.readiness_status})")
    lines.append(f"- **Unresolved gaps**: {len(s.gaps)}")
    lines.append(f"- **Unresolved conflicts**: {len(s.conflicts)}")
    lines.append("")

    lines.append("## 1. Meeting Understanding")
    lines.append("")
    lines.append(f"Languages: {_lang_pct(t)}")
    lines.append("")

    lines.append("## 2. Objective Evolution")
    lines.append("")
    if s.objective_history:
        for i, o in enumerate(s.objective_history):
            lines.append(f"{i + 1}. **{o.value}** ({o.status}, confidence {o.confidence:.2f})")
    else:
        lines.append("No objective detected.")
    lines.append("")

    lines.append("## 3. Methodology Gaps")
    lines.append("")
    if s.gaps:
        for g in s.gaps:
            lines.append(f"- **{g.concept}** [{g.status}] — priority {g.priority:.2f}: {g.reason}")
    else:
        lines.append("No gaps remaining.")
    lines.append("")

    lines.append("## 4. Questions")
    lines.append("")
    if s.questions:
        for q in s.questions:
            status = q.current_status
            lines.append(f"- **{q.question_id}** ({status}) — *{q.question}*")
            lines.append(f"  - Target gap: {q.target_gap}; why: {q.why_asked}")
            lines.append(f"  - Lifecycle: {' → '.join(h.status for h in q.status_history)}")
    else:
        lines.append("No questions generated.")
    lines.append("")

    lines.append("## 5. Conflicts")
    lines.append("")
    if s.conflicts:
        for c in s.conflicts:
            lines.append(f"- ⚠ **{c.concept}**: existing “{c.existing_value}” vs new “{c.new_value}” ({c.status})")
    else:
        lines.append("No unresolved conflicts.")
    lines.append("")

    lines.append("## 6. Candidate Methodology Scope")
    lines.append("")
    cs = s.candidate_scope
    lines.append(f"- Objective: {cs.objective or '—'}")
    lines.append(f"- Population: {cs.population or '—'}")
    lines.append(f"- Statistical unit: {cs.statistical_unit or '—'}")
    lines.append(f"- Reference period: {cs.reference_period or '—'}")
    lines.append(f"- Geographic scope: {cs.geographic_scope or '—'}")
    lines.append(f"- Indicators: {', '.join(cs.indicators) or '—'}")
    lines.append(f"- Dimensions: {', '.join(cs.dimensions) or '—'}")
    lines.append(f"- Data sources: {', '.join(cs.data_sources) or '—'}")
    lines.append(f"- Open questions: {len(cs.open_questions)}")
    lines.append(f"- **Readiness: {cs.readiness_score}% ({cs.readiness_status})**")
    lines.append("")

    lines.append("## 7. Knowledge Candidates")
    lines.append("")
    if s.knowledge_candidates:
        for k in s.knowledge_candidates:
            lines.append(f"- [{k.knowledge_type}] **{k.concept}**: {k.statement} (confidence {k.confidence:.2f})")
    else:
        lines.append("No knowledge candidates extracted.")
    lines.append("")

    lines.append("## 8. State History")
    lines.append("")
    for h in s.history:
        lines.append(f"{h.version}. {h.note} ({h.timestamp})")
    lines.append("")

    return "\n".join(lines)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Methodology Evaluation Report</title>
<style>
body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;background:#f5f7fa;color:#1a1c1e}}
.wrap{{max-width:880px;margin:0 auto;padding:2rem 1.5rem}}
h1{{font-size:1.5rem;margin:0 0 1rem}} h2{{font-size:1.1rem;border-bottom:2px solid #0b2a4a;padding-bottom:.3rem;margin:2rem 0 1rem}}
.card{{background:#fff;border:1px solid #e3e8ee;border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem}}
.badge{{display:inline-block;padding:.1rem .5rem;border-radius:999px;font-size:.72rem;background:#e3e8ee}}
.badge.confirmed{{background:#e6f4ea;color:#1e6b32}} .badge.proposed{{background:#fff6e0;color:#8a6d1a}}
.badge.conflict{{background:#fdeaea;color:#a32222}}
.muted{{color:#73777f}} ul{{margin:.5rem 0}} li{{margin:.3rem 0}}
pre{{white-space:pre-wrap;background:#f0f2f5;border-radius:8px;padding:.75rem}}
</style></head><body><div class="wrap">
{body}
</div></body></html>
"""


def _html_escape(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(t: MeetingTranscript, s: EvaluationState) -> str:
    md = build_markdown(t, s)
    # Minimal Markdown -> HTML conversion for headings, bold, lists, paragraphs.
    out: list[str] = []
    for raw in md.splitlines():
        line = _html_escape(raw)
        if line.startswith("# "):
            out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("- "):
            out.append(f"<li>{_inline_md(line[2:])}</li>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{_inline_md(line)}</p>")
    body = "\n".join(out)
    return _HTML_TEMPLATE.replace("{body}", body)


def _inline_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text
