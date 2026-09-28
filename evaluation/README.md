# Evaluation Harness

Standalone Python harness that replays prerecorded multilingual (Arabic/English)
meeting transcripts through the portal's methodology pipeline and produces
transparent, evidence-linked evaluation artifacts.

## Requirements

- Python 3.10+ (the repo already uses it).
- The production `app/` package (imported in-process — no server needed).
- For `production`/`local` modes only: a running OpenAI-compatible LLM gateway
  (default `http://localhost:8080/v1`). `mock` mode needs nothing.

## Usage

From the repository root:

```bash
# Deterministic mock (no LLM) — exercises the full pipeline logic.
python -m evaluation.cli run --input evaluation/data/meeting_001 --mode mock

# Real local LLM gateway.
python -m evaluation.cli run --input evaluation/data/meeting_001 --mode local

# Production methodology services (same as local here; uses the gateway).
python -m evaluation.cli run --input evaluation/data/meeting_001 --mode production

# Simulated human review of a completed run.
python -m evaluation.cli review --run evaluation/output/M-001
```

## Input formats

- A meeting folder containing `metadata.json` + `transcript.json`.
- A standalone `.json` transcript (structured segments).
- `.csv` (columns: `segment_id`, `speaker_id`, `timestamp_start`,
  `timestamp_end`, `language`, `text`).
- `.txt` / `.md` plain-text fallback (speaker + timestamp + text lines).

## Outputs (per meeting)

```text
evaluation/output/M-001/
├── report.html                # rich, self-contained evaluation report
├── report.md                  # Markdown report
├── state_history.json         # every methodology state version
├── evaluation_state.json      # full evaluation state (facts, gaps, questions…)
├── candidate_scope.json       # final candidate methodology + readiness
├── knowledge_candidates.json  # extracted reusable knowledge
└── review.json                # (after `review`) human decision + edits
```

## Modes

| Mode | Extraction | Notes |
|---|---|---|
| `mock` | deterministic keyword rules | no LLM, no network; for pipeline mechanics |
| `local` | `MethodologyAgent` + local gateway | real LLM, no cloud |
| `production` | `MethodologyAgent` + local gateway | real portal logic |

Mock mode never silently substitutes for the real LLM — it is explicitly
selected and only for testing.
