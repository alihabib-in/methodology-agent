# Evaluation Harness — Implementation Assessment

This document records the repository inspection required before building the
standalone evaluation harness (`benchmarkTest.md`). It maps existing production
components to what the harness can reuse versus what it must add.

## 1. Existing methodology pipeline

- `app/agent/methodology_agent.py` — `MethodologyAgent` orchestrates the full
  pipeline: `extract` (LLM) → `StateManager.apply` → `GapDetector.detect` →
  `QuestionGenerator.generate`. Its `analyze(text, language, state, use_rag)`
  returns `summary`, `extraction`, `methodology_state`, `gaps`,
  `recommended_question`, `relevant_knowledge`, and `parse_error` on failure.
- `app/agent/extractor.py` — `Extractor` runs the LLM and validates output
  against `ExtractionResult` (with one retry).
- `app/agent/state_manager.py` — `StateManager` applies extracted requirements
  to a `MethodologyState` (a confirmed field is never downgraded by inference).
- `app/agent/gap_detector.py` — `GapDetector` is deterministic (LLM-free) and
  computes gap priority from impact × uncertainty × dependency.
- `app/agent/question_generator.py` — `QuestionGenerator` is deterministic;
  `generate_many` produces plain-language questions from gaps + state.

## 2. LLM gateway

- `app/llm/client.py` — `LLMClient(base_url, model, timeout, temperature)` with
  `.chat(system_prompt, user_prompt, max_tokens)` against any OpenAI-compatible
  server (the portal uses a local llama.cpp server). Reused directly by the
  harness; `base_url` is configurable (`LLM_BASE_URL`, default
  `http://localhost:8080/v1` from the VDI).

## 3. Prompts

- `app/agent/prompts.py` — `SYSTEM_PROMPT`, `EXTRACTION_JSON_SCHEMA`,
  `EXTRACTION_PROMPT_TEMPLATE`, `QUESTION_GENERATION_PROMPT_TEMPLATE`,
  `KNOWLEDGE_CONSOLIDATION_PROMPT`. Reused as-is (the harness never invents
  its own extraction schema).

## 4. State model

- `app/models/methodology_state.py` — `MethodologyState` (6 scalar `FieldState`
  fields + `budget`/`scope` + lists: indicators, dimensions, data_sources,
  definitions, constraints, decisions, open_questions, roles,
  success_metrics, training_needs). Reused as the authoritative state; the
  harness layers versioning/evidence on top without modifying it.

## 5–8. Gap / question / candidate-scope / knowledge models

- `Gap` is a frozen dataclass in `gap_detector.py` (domain, label, reason,
  methodology_impact, downstream_dependency); `detect` returns dicts.
- `MethodologyQuestion` (`app/models/question.py`): question, domain, reason,
  priority, status.
- No dedicated candidate-scope model exists — the harness adds one.
- `KnowledgeItem` (`app/models/orm.py`) + `app/knowledge/repository.py`; RAG
  retrieval via `app/knowledge/rag.py` (`retrieve(query, limit)`). The harness
  adds a lightweight `KnowledgeCandidate` model and reuses `rag.retrieve` where
  a running Qdrant/embedding service is available, else returns empty.

## 9. Components reusable by the harness (directly)

- `MethodologyAgent` (orchestration + extraction + gaps + questions).
- `MethodologyState`, `StateManager`, `GapDetector`, `QuestionGenerator`.
- `LLMClient` (local gateway).
- `detect_language` / `normalize_language` (`app/agent/terminology.py`).
- `rag.retrieve` (best-effort knowledge retrieval).
- `ExtractionResult` / `Requirement` / `Definition` etc. (`app/models/extraction.py`).

## 10. Components that need adapters

- The **LLM/extraction** step: production `Extractor` needs a running LLM;
  mock mode substitutes a deterministic keyword extractor with the **same
  `analyze` interface**, so `StateManager`/`GapDetector`/`QuestionGenerator`
  remain unchanged.
- **Segment-level evidence**: production extraction operates on a text blob and
  returns `Evidence.text` (not segment IDs). The harness links each extracted
  fact back to the transcript segments that formed the input batch.

## 11. Missing functionality (added by the harness)

- Incremental batch processing with per-batch state versions.
- Full state-history (`state_history.json`) and evidence tracking.
- Question lifecycle (`candidate → presented → asked → answered/…`) and
  **answer detection** (a later batch resolving an earlier gap marks the
  question answered).
- **Contradiction detection** (a new value conflicting with a confirmed value is
  flagged, not silently overwritten).
- Candidate methodology scope + **readiness score** reflecting gaps/conflicts.
- Knowledge-candidate extraction + simulated human review (CLI).
- HTML/Markdown/JSON report generation.

## 12. Recommended integration approach

Build `evaluation/` as a thin orchestration layer that **imports the production
`app.*` modules in-process** (no HTTP round-trip to the portal API; the harness
is standalone and runs from the repo). Three adapters:

- `production` — `MethodologyAgent` + `LLMClient` against `LLM_BASE_URL`.
- `local` — same `MethodologyAgent`; explicitly local gateway (no cloud).
- `mock` — deterministic keyword extractor feeding the same
  `StateManager`/`GapDetector`/`QuestionGenerator`.

The structure was consolidated (single `models.py`, single `adapters.py`,
single `engine.py`) rather than the literal 20-file layout, per the
"adapt / do not blindly create files" instruction — functionality is unchanged.

## Known limitations

- No live transcription; transcripts are prerecorded files.
- Evidence is batch-granular (linked to the segments in each processed batch),
  not token-granular.
- `rag.retrieve` requires the embedding/Qdrant services; without them retrieval
  is a no-op (the harness still runs).
- Mock mode is deterministic but coarse (keyword/pattern based); it is for
  testing pipeline mechanics only, never a substitute for the LLM.
