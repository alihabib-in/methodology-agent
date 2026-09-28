# Methodology Discussion Portal — Overview for Developers

This document explains, end-to-end, how this portal works. It is written for a
developer (or another AI "Vibe coding" platform) who needs a complete and
accurate mental model before making changes. It describes only what has
actually been built — no aspirational features.

---

## 1. Business Requirement

### 1.1 The problem

A statistical methodology team (in this case modelled on a national statistics
authority) holds **unstructured, bilingual business discussions** about how a
statistical indicator should be defined and produced. These discussions are in
Arabic, English, or a mix of both ("code switching"). The goal of the portal is
to turn those raw conversations into a **structured, auditable statistical
methodology** — the set of definitions, statistical units, populations,
reference periods, frequencies, data sources, and constraints that a statistician
needs before building an indicator.

### 1.2 What the portal must do

1. **Host a real meeting** — participants join a video conference (Jitsi) in the
   same place where the AI works.
2. **Understand Arabic and English** — detect the language of a discussion and
   extract methodology facts regardless of language or code switching.
3. **Extract structured facts** from free-form discussion: requirements,
   definitions, statistical units, target populations, reference periods,
   frequencies, geographic scope, indicators, dimensions, data sources,
   business rules, quality rules, constraints, decisions, and open questions.
4. **Separate inference from fact** — an AI must never silently turn a guess
   into a confirmed fact.
5. **Find gaps** — determine which methodology elements are still missing or
   only guessed at.
6. **Ask the right question** — generate a single, highest-priority, plain
   English question that moves the discussion forward, and speak it aloud.
7. **Keep a human in the loop** — the AI only *proposes* knowledge; a human
   approves it before it becomes authoritative.
8. **Build a knowledge base** — accumulate reusable, approved methodology
   knowledge and feed relevant pieces back into future analyses (RAG).
9. **Evaluate itself** — replay historical transcripts through the same
   pipeline and produce evidence-linked reports.

### 1.3 Hard constraints

- **Fully self-hosted.** No cloud AI providers, no API keys, no public internet
  dependency for the core path. The LLM and embedding models run locally.
- **Corporate intranet.** No public domain name; the platform is reached by LAN
  IP (`10.50.128.97`) with a self-signed TLS certificate.
- **Free / open components only.** LLM (Qwen3), embeddings, Jitsi, and TTS are
  all free. The one internet-dependent feature (TTS) uses Microsoft Edge's free
  neural voices and has a graceful fallback.
- **The LLM is a reasoning component, not the agent itself.** The "agent" is the
  LLM plus deterministic state, rules, gap detection, question prioritization,
  validation, and human approval.

---

## 2. High-Level Architecture

```
                       ┌─────────────────────────────────────────────┐
                       │                 Browser (React)              │
                       │  login → choose meeting → Jitsi iframe + AI  │
                       │  panels (Questions / Activity / Methodology /│
                       │  Knowledge graph) + FAB assistant            │
                       └───────────────┬─────────────────────────────┘
                                       │  REST  +  WebSocket (/ws/{id})
                                       ▼
                       ┌─────────────────────────────────────────────┐
                       │       Methodology API  (FastAPI, :8000)       │
                       │   orchestrates the methodology pipeline and   │
                       │   publishes real-time events to the browser   │
                       └──┬───────────┬───────────┬───────────┬───────┘
                          │           │           │           │
              ┌───────────▼──┐  ┌─────▼──────┐  ┌─▼─────────┐ │
              │   LLM server │  │ Embedding  │  │  Postgres │ │
              │  (llama.cpp) │  │  service   │  │  (SQLAlc) │ │
              │   Qwen3-4B   │  │ e5-small   │  │  Qdrant   │ │
              │    :8080     │  │   :8001    │  │  :6333    │ │
              └──────────────┘  └────────────┘  └───────────┘ │
                                                               ▼
                                        ┌──────────────────────────────┐
                                        │       Jitsi Meet stack        │
                                        │  web(:8443) + prosody +       │
                                        │  jicofo + jvb  (video/audio)  │
                                        └──────────────────────────────┘
```

All components are Docker services defined in `docker-compose.yml` (the main
stack) and `jitsi/docker-compose.yml` (the Jitsi stack). The frontend runs as a
Vite dev server during development.

---

## 3. Repository Layout

```
methodology-agent/
├── app/                      # Backend (FastAPI) — the core
│   ├── main.py               # App wiring, routers, shared state
│   ├── api/                  # HTTP endpoints
│   │   ├── health.py         # /health
│   │   ├── routes.py         # /analyze, /extract, /question, /methodology-state
│   │   ├── meetings.py       # /meetings (methodology session) + analyze/answer/state
│   │   ├── meeting.py        # /api/v1/meetings (Jitsi meeting session) + events
│   │   ├── knowledge.py      # /knowledge CRUD + approve/reject + search
│   │   └── tts.py            # /tts (edge-tts neural speech)
│   ├── agent/                # The methodology reasoning pipeline
│   │   ├── methodology_agent.py  # orchestrator
│   │   ├── extractor.py      # LLM extraction (only LLM caller in agent)
│   │   ├── state_manager.py  # deterministic structured state
│   │   ├── gap_detector.py   # deterministic gap detection
│   │   ├── question_generator.py # deterministic question generation
│   │   ├── prompts.py        # prompt strings + JSON schema
│   │   └── terminology.py    # Arabic/English terms + language detection
│   ├── models/               # Pydantic models
│   │   ├── extraction.py     # ExtractionResult shape
│   │   ├── methodology_state.py # MethodologyState + FieldState
│   │   ├── question.py       # MethodologyQuestion
│   │   └── orm.py            # SQLAlchemy tables
│   ├── meeting/              # Meeting lifecycle + Jitsi adapter
│   │   ├── service.py        # MeetingService (create/start/end)
│   │   └── jitsi/adapter.py  # room naming, URL, JWT token
│   ├── knowledge/            # Persistence + RAG
│   │   ├── repository.py     # DB read/write helpers
│   │   ├── rag.py            # index + retrieve
│   │   ├── embedding_client.py # HTTP client to embedding service
│   │   └── vector_store.py   # Qdrant wrapper
│   ├── realtime/             # In-process pub/sub + WebSocket
│   │   ├── events.py         # event types + envelope
│   │   ├── broker.py         # EventBroker (per-session queues)
│   │   ├── service.py        # snapshot builder
│   │   └── websocket.py      # /ws/{session_id} endpoint
│   ├── speech/transcriber.py # faster-whisper wrapper (optional, unused live)
│   ├── llm/client.py         # OpenAI-compatible LLM client
│   └── core/                 # config, db, logging
├── frontend/                 # React + Vite + Tailwind + shadcn/ui (JSX)
│   └── src/
│       ├── App.jsx           # main app, phases, panels
│       ├── api.js            # REST client
│       ├── lib/speech.js     # TTS playback + fallback
│       ├── store/store.js    # realtime store (useSyncExternalStore)
│       ├── realtime/socket.js# WebSocket client with reconnect
│       ├── hooks/useRealtime.js
│       └── components/       # JitsiMeeting, panels, graph, overlay…
├── evaluation/               # Standalone transcript-replay harness
├── embedding_service/        # sentence-transformers HTTP service
├── jitsi/                    # Jitsi stack config + certs + branding
├── tests/                    # pytest unit tests (LLM mocked)
├── models/                   # GGUF model (not committed)
├── docker-compose.yml
├── Dockerfile                # API image
├── Dockerfile.embedding      # embedding image
└── requirements*.txt
```

---

## 4. Technical Building Blocks

### 4.1 Services and ports

| Service | Container | Image | Port (host) | Role |
|---|---|---|---|---|
| LLM | `methodology-llm` | `ghcr.io/ggml-org/llama.cpp:server-cuda` | `127.0.0.1:8080` | OpenAI-compatible chat/completions |
| API | `methodology-api` | local build (`Dockerfile`) | `127.0.0.1:8000` | FastAPI methodology backend |
| Embedding | `methodology-embedding` | local build (`Dockerfile.embedding`) | `127.0.0.1:8001` | sentence-transformers embeddings |
| Postgres | `methodology-postgres` | `postgres:17-alpine` | `127.0.0.1:5432` | methodology state + knowledge |
| Qdrant | `methodology-qdrant` | `qdrant/qdrant:v1.14.0` | `127.0.0.1:6333/6334` | vector store for approved knowledge |
| Jitsi web | `jitsi-web` | `ghcr.io/jitsi/web` | `8443` | video UI + external_api.js |
| Jitsi prosody | `jitsi-prosody` | `ghcr.io/jitsi/prosody` | internal | XMPP signaling |
| Jitsi jicofo | `jitsi-jicofo` | `ghcr.io/jitsi/jicofo` | internal | conference focus |
| Jitsi jvb | `jitsi-jvb` | `ghcr.io/jitsi/jvb` | `10000/udp` | media (SFU) |
| Frontend (dev) | — | Vite | `5173` | React app (HTTPS, self-signed cert) |

The LLM runs on the GPU (`--ngl 999`); embeddings run on CPU (the LLM owns the
GPU). The model is `Qwen3-4B-Instruct-2507` (`Q4_K_M` GGUF). The embedding model
is `intfloat/multilingual-e5-small` (384-dim).

### 4.2 Two "meeting" concepts (important)

There are two distinct, linked concepts and two tables:

1. **Methodology session** — `Meeting` table (id `M-000021`, etc.). This holds the
   `methodology_state` JSON. The frontend calls it `sessionId`. The WebSocket and
   the AI pipeline are scoped to this id.
2. **Jitsi meeting session** — `MeetingSession` table (id is a UUID). This links a
   methodology session to a `jitsi_room_name` (e.g. `scad-m-000021-c968f789`) and
   holds the JWT for joining.

The room name is generated by `JitsiAdapter.build_room_name(session_id, suffix)`:
`scad-` + slug of the session id + an 8-hex suffix (`scad-m-000021-c968f789`).

### 4.3 Data model (PostgreSQL)

- `meetings` — `id` (M-prefixed), `status`, `language`, `methodology_state` (JSONB).
- `knowledge_items` — `id` (K-prefixed), `concept`, `statement`, `domain`,
  `status` (lifecycle), `source`, `evidence`, `confidence`, `validated_by`,
  `effective_from`, `meeting_id`, `parent_id` (tree), `qdrant_point_id`.
- `meeting_sessions` — UUID id, `session_id`, `jitsi_room_name` (unique),
  `meeting_title`, `created_by`, `status`, timestamps.
- `meeting_events` — audit log (`event_type`, `session_id`, `meeting_id`, `payload`).

### 4.4 Methodology state (the core data structure)

`MethodologyState` (Pydantic) is the single source of truth for what the AI has
learned. It has **scalar fields** with a `value` + `status` + `confidence`, and
**list fields**:

- Scalars: `objective`, `target_population`, `statistical_unit`,
  `reference_period`, `frequency`, `geographic_scope`, `budget`, `scope`.
- Lists: `indicators`, `dimensions`, `data_sources`, `definitions`,
  `business_rules`, `quality_rules`, `constraints`, `decisions`,
  `open_questions`, `roles`, `success_metrics`, `training_needs`.

Each scalar is a `FieldState` with:

- `value: str | None`
- `status`: one of `unknown | inferred | proposed | confirmed | rejected | conflicting`
- `confidence: float` (0..1)

The status taxonomy is the heart of the "inference is not fact" rule.

---

## 5. How the AI Agents Orchestrate the Work

This is the most important section. The system is **not a swarm of independent
agents**. There is a single orchestrator — `MethodologyAgent` — that composes
four specialized components. Only one of them (the `Extractor`) talks to the LLM;
the other three are pure, deterministic Python. This split is deliberate: the
LLM does the fuzzy semantic work once, and everything downstream is reproducible.

```
                 MethodologyAgent (orchestrator)
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
   Extractor              StateManager             GapDetector
   (LLM, fuzzy)          (deterministic)          (deterministic)
        │                       │                        │
        │  ExtractionResult      │  MethodologyState      │  list[gap]
        │  (Pydantic, validated) │  (applies, never       │
        │                       │   downgrades confirmed) │
        │                       └───────────┬────────────┘
        │                                   ▼
        └──────────────────────►  QuestionGenerator
                                 (deterministic; prefers
                                  LLM-recommended question)
```

### 5.1 The four components

**`Extractor`** (`app/agent/extractor.py`)
- The **only** component that calls the LLM.
- Sends a system prompt + user prompt to the LLM asking for JSON matching a
  fixed schema (`EXTRACTION_JSON_SCHEMA`).
- The LLM returns a JSON document; the extractor strips markdown fences, finds
  the first balanced JSON object, sanitizes list fields, and validates with
  Pydantic (`ExtractionResult`).
- If JSON parsing/validation fails, it retries once with an explicit
  "return only valid JSON" instruction.
- Optionally appends "existing approved knowledge" to the prompt (RAG context)
  so extraction reuses canonical definitions and does not contradict them.
- Language is detected first (Arabic/English/mixed) by `terminology.py`.

**`StateManager`** (`app/agent/state_manager.py`)
- Takes an `ExtractionResult` and applies it to a `MethodologyState`.
- Contains the key invariant: **a `confirmed` field is never downgraded** by an
  `inferred`/`proposed` value.
- Maps concepts to scalar fields via `CONCEPT_TO_FIELD` (e.g. `target_population`
  and `population` both map to `target_population`).
- Appends list items (indicators, definitions, data sources, etc.).

**`GapDetector`** (`app/agent/gap_detector.py`)
- Pure, LLM-free. Iterates a fixed table of methodology gaps (definition,
  objective, statistical unit, target population, reference period, data source,
  frequency, geographic scope), each with a `methodology_impact` and a
  `downstream_dependency` weight.
- A gap is "resolved" only when its field `status == "confirmed"`. Inferred and
  proposed values remain open gaps.
- Priority = `impact × uncertainty × dependency × confidence_gap`, where the
  `uncertainty`/`confidence_gap` factors come from the field's status.
- Returns a priority-sorted list of gap dictionaries.

**`QuestionGenerator`** (`app/agent/question_generator.py`)
- Also deterministic. Maps the top gap to a domain question template.
- Prefers the LLM's `recommended_question` when its domain aligns with the top
  gap; otherwise falls back to the template.
- `generate_many()` produces a broad list of plain-English questions across every
  part of the state (gaps, indicators, dimensions, definitions, sources, open
  questions, scope, budget, constraints, roles, success metrics, training needs,
  timeline, audience) — this is what populates the Questions panel.

### 5.2 The pipeline (`analyze`)

`MethodologyAgent.analyze(text, language, state)` runs this fixed sequence:

1. **Detect language** (unless provided).
2. **Retrieve relevant knowledge** (RAG, best-effort) — `_retrieve()`.
3. **Extract** via `Extractor` (LLM). If this fails, return a `parse_error`
   result; the state is not changed.
4. **Apply** the extraction to a `StateManager` (either the passed-in state or
   the agent's in-memory state) → new `MethodologyState`.
5. **Detect gaps** via `GapDetector`.
6. **Generate a question** via `QuestionGenerator` (using the LLM's recommended
   question when aligned).

`analyze` returns a dict containing: language, summary, extraction, the new
methodology state, gaps, the recommended question, and the retrieved knowledge.

The `answer` path (`answer_meeting` endpoint) is **the same `analyze`** but with
the human's answer as the input text and the current state passed in, so an answer
is treated as new evidence to re-extract, re-apply, re-detect, re-question.

### 5.3 Where state lives

Two places, reconciled by the API:

- The API holds a process-level `MethodologyAgent` (`app.state.agent`) whose
  `StateManager` has an in-memory `MethodologyState`.
- The database `meetings.methodology_state` is the **authoritative persisted**
  copy.

For every request the API **loads state from the DB**, passes it into
`agent.analyze(..., state=loaded)`, then **saves the resulting state back**. The
in-memory default state is only a fallback for the stateless `/analyze` demo
endpoints.

### 5.4 Human-in-the-loop knowledge

The AI never publishes knowledge by itself. The lifecycle is:

`candidate` → (human) → `approved` / `rejected` → `published`

- `POST /knowledge/candidate` creates a `candidate` (also used by the frontend
  "add node" action in the knowledge graph).
- `POST /knowledge/{id}/approve` with `decision=approve|reject` transitions it.
- **Only approved** knowledge is embedded and indexed into Qdrant (`_index_knowledge`).
- RAG retrieval (`rag.retrieve`) therefore only ever surfaces approved knowledge.

### 5.5 RAG (retrieval-augmented extraction)

`app/knowledge/rag.py`:

- `index_knowledge()` — embeds the statement (`passage` task) via the embedding
  service, upserts into Qdrant with payload (knowledge_id, concept, domain,
  statement), returns the Qdrant point id.
- `retrieve(query)` — embeds the query (`query` task), searches Qdrant, returns
  top-k matches with scores.
- Retrieval is **best-effort and never fatal**: any error returns `[]`, and the
  pipeline continues without context.

The embedding service prefixes text with `"query: "` or `"passage: "` (required
by `multilingual-e5-small`) and normalizes embeddings.

---

## 6. Real-Time Event System

The backend pushes progress to the browser over a WebSocket, and the frontend
reacts by updating UI state. This is a **pub/sub fan-out**, not a request/response.

### 6.1 Backend (`app/realtime/`)

- **`EventBroker`** (`broker.py`) — in-process broker. Each connected WebSocket
  registers a `Subscription` (an `asyncio.Queue`) keyed by `session_id`.
  `publish()` is thread-safe: it uses `loop.call_soon_threadsafe` so synchronous
  (threadpool) endpoints can publish without blocking.
- **Event envelope** (`events.py`) — every event is an `EventEnvelope` with
  `event_id`, `event_type`, `session_id`, `meeting_id`, `timestamp`, `sequence`,
  and `payload`. Many event-type constants are defined (`meeting.ready`,
  `ai.status.changed`, `gap.detected`, `question.generated`, `answer.received`,
  `knowledge.approved`, `state.snapshot`, etc.).
- **WebSocket endpoint** (`websocket.py`) — `GET /ws/{session_id}`. On connect it
  first sends a `state.snapshot` (authoritative, rebuilt from the DB), then
  streams queued events until disconnect.
- **Snapshot builder** (`service.py`) — loads the meeting state from the DB,
  re-runs gap detection + question generation, and returns the full snapshot.

### 6.2 Frontend (`store/store.js`, `realtime/socket.js`, `hooks/useRealtime.js`)

- `socket.js` — a WebSocket client with exponential-backoff reconnect.
- `useRealtime(sessionId)` — opens/closes the socket on session change.
- `store.js` — a tiny external store (via `useSyncExternalStore`). It receives
  envelopes, deduplicates by `event_id`, and reduces each `event_type` into state:
  `aiStatus`, `methodologyState`, `gaps`, `questions`, `objective`, and an
  `activity` feed. It exposes `applyAnalysis` (used by the initial REST analysis)
  and `setStatus`.

The AI activity bar and the questions/activity/methodology panels are all derived
from this store.

---

## 7. Frontend Flow (React)

Phases in `App.jsx`:

1. **`login`** — name entry (`LoginScreen`).
2. **`setup`** — a chip toggle chooses **New Meeting** or **Existing Meeting**:
   - *New Meeting*: a discussion-name input → `handleCreateSession()` → creates a
     methodology session (`POST /meetings`), then a Jitsi meeting
     (`POST /api/v1/meetings`), then enters the meeting phase.
   - *Existing Meeting*: a dropdown of demo meetings (`c968f789 - Impact of
     Social Media on Youth`) → joins room `scad-m-000021-c968f789` with session
     `M-000021`.
3. **`meeting`** — the live meeting screen:
   - Left: `JitsiMeeting` iframe (external_api.js loaded from the Jitsi domain).
   - Right: tabs — **Questions**, **Activity**, **Methodology**, **Knowledge**
     (a Cytoscape/Dagre tree graph, left-to-right).
   - Header: logo + centered `AIActivityBar`.
   - Floating action button opens the **AI Methodology Assistant** dialog.

### 7.1 How the AI is triggered during a meeting

- On participant join, when the participant count reaches 2 (the first remote
  participant), `loadAssistantContext()` calls
  `analyzeSession(sessionId, objective || 'Methodology session')`.
- This runs the full pipeline on the discussion text and stores the result
  (`applyAnalysis`).
- The generated questions appear in the Questions panel; clicking **Ask** shows
  the question as an overlay, sends it to the Jitsi chat
  (`sendChatMessage`), sets the AI status, and **speaks it aloud** (TTS).
- Answering a question (`answerSession`) re-runs the pipeline with the answer.

> **Current scope note:** the live pipeline is triggered with the discussion
> *objective text*, not with automatic real-time audio transcription. A
> `faster-whisper` transcriber module exists (`app/speech/transcriber.py`) but is
> an optional dependency (`requirements-asr.txt`) and is not wired into the live
> flow yet.

### 7.2 TTS (text-to-speech)

`frontend/src/lib/speech.js` + `app/api/tts.py`:

- The frontend requests `GET /tts?text=...&voice=...`.
- The backend uses `edge-tts` (Microsoft Edge neural voices, free, no API key) to
  synthesize MP3 audio; default voice `en-US-JennyNeural`.
- The frontend plays the returned audio; if the backend/network is unavailable it
  falls back to the browser's `speechSynthesis`.

---

## 8. Knowledge Graph (Cytoscape)

`frontend/src/components/KnowledgeGraph.jsx` renders the knowledge items as a
**left-to-right tree** (`dagre` layout, `rankDir: 'LR'`). Nodes are built from
`parent_id` relationships. Features:

- Click a parent to collapse/expand its children.
- Select a node to see its statement, delete it, or add a child.
- Deletion cascades to descendants (`DELETE /knowledge/{id}` removes the subtree).
- The view auto-fits to the panel on each layout change.

---

## 9. Evaluation Harness (`evaluation/`)

A standalone Python package that replays prerecorded multilingual transcripts
through the same production pipeline and produces evidence-linked reports.

- `cli.py` — `run` and `review` subcommands.
- `engine.py` — simulates incremental meeting progression: processes transcript
  batches, updates state, records facts with evidence, detects conflicts, tracks
  question lifecycle (candidate → presented → asked → answered), and versions the
  state history.
- `adapters.py` — three modes:
  - `mock` — deterministic keyword extraction (no LLM); still uses the real
    `StateManager`/`GapDetector`/`QuestionGenerator`.
  - `local` — real `MethodologyAgent` against the local LLM gateway.
  - `production` — same as `local` here.
- Outputs per meeting: `report.html`, `report.md`, `state_history.json`,
  `evaluation_state.json`, `candidate_scope.json`, `knowledge_candidates.json`,
  and (after `review`) `review.json`.
- `_readiness_score` computes a readiness percentage from confirmed core fields,
  with unresolved conflicts capping the score at 60.

---

## 10. Testing

`tests/` contains pytest unit tests. The LLM is mocked, so tests need no GPU,
Docker, or internet:

- `test_extraction.py`, `test_bilingual.py`, `test_questions.py`,
  `test_answer_loop.py`, `test_knowledge.py`, `test_rag.py`,
  `test_jitsi_meeting.py`.

Run with `py -m pytest -q`.

---

## 11. Configuration

Backend config is read from environment variables (`app/core/config.py`):

| Variable | Default |
|---|---|
| `LLM_BASE_URL` | `http://llm:8080/v1` |
| `LLM_MODEL` | `qwen3-4b-instruct-2507` |
| `LLM_TIMEOUT_SECONDS` | `120` |
| `LLM_TEMPERATURE` | `0.1` |
| `LLM_MAX_TOKENS` | `1200` |
| `DATABASE_URL` | `postgresql+psycopg://methodology:methodology@postgres:5432/methodology` |
| `QDRANT_URL` | `http://qdrant:6333` |
| `EMBEDDING_URL` | `http://embedding:8001` |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` |
| `JITSI_BASE_URL` | `https://localhost:8443` |
| `JITSI_JWT_SECRET` | (Jitsi JWT shared secret) |

The frontend uses `VITE_JITSI_DOMAIN`, `VITE_API_URL`, `VITE_WS_URL`.

---

## 12. Key Design Principles (do not violate)

1. **The LLM is a reasoning component, not the agent.** State, gap detection,
   question generation, and validation are deterministic code.
2. **Inference is not fact.** A field is only "resolved" when `confirmed`;
   inferred/proposed values remain open gaps and must not downgrade a confirmed
   field.
3. **Human approval is mandatory** before knowledge becomes authoritative and
   enters the RAG index.
4. **Questions are always in English**, even when the discussion is Arabic.
5. **Never invent facts; preserve uncertainty; never silently resolve
   contradictions.**
6. **Best-effort external dependencies.** RAG and TTS degrade gracefully rather
   than fail the request.
7. **Self-hosted and free** — no cloud AI, no API keys on the core path.

---

## 13. Known Limitations / Current State

- **No live audio transcription** wired into the meeting flow (the transcriber
  module is optional and unused in the live portal).
- **TTS requires outbound internet** to Microsoft's edge TTS endpoint; falls back
  to the robotic browser voice if unreachable.
- **Single-instance realtime broker** — the pub/sub state is in-process and not
  shared across multiple API replicas (fine for a single-node deployment).
- **Self-signed TLS** — corporate users must trust the certificate (manual import
  or GPO) since there is no public domain.
- The LLM (4 GB quantized model on a 4 GB GPU) can be slow and occasionally
  times out; the API surfaces this as an `LLMError`.
