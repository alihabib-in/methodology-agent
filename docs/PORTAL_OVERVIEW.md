# Methodology Discussion Portal — Overview for Developers

This document explains, end-to-end, how this platform works. It is written for a
developer (or another AI "Vibe coding" platform) who needs a complete and
accurate mental model before making changes. It describes only what has
actually been built — no aspirational features.

The platform has evolved from a single `MethodologyAgent` (extract → state →
gap → question) into an **orchestrated multi-agent workflow** that takes a
methodology request through to a full methodology document. This document covers
both: the reasoning pipeline (still the foundation of the meeting portal) and
the workflow orchestration layer built on top of it.

---

## 1. Business Requirement

### 1.1 The problem

A statistical methodology team (in this case modelled on a national statistics
authority — SCAD) holds **unstructured, bilingual business discussions** about
how a statistical indicator should be defined and produced. These discussions
are in Arabic, English, or a mix of both ("code switching"). The goal of the
platform is to turn those raw conversations into a **structured, auditable
statistical methodology** — and, through a governed multi-agent workflow, into
an actual **methodology document**.

### 1.2 What the platform must do

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
9. **Orchestrate methodology development** — once a methodology request is
   confirmed, a workflow engine drives specialized agents to produce a
   standardized methodology, a SCAD-specific methodology, and QA/gap reports.
10. **Evaluate itself** — replay historical transcripts through the same
    pipeline and produce evidence-linked reports.

### 1.3 Hard constraints

- **Fully self-hosted.** No cloud AI providers, no API keys, no public internet
  dependency for the core path. The LLM and embedding models run locally.
- **Corporate intranet.** No public domain name; the platform is reached by LAN
  IP (`10.50.128.97`) with a self-signed TLS certificate.
- **Free / open components only.** LLM (Qwen3), embeddings, Jitsi, and TTS are
  all free. The one internet-dependent feature (TTS) uses Microsoft Edge's free
  neural voices and has a graceful fallback.
- **The LLM is a reasoning component, not the agent.** The "agent" is the LLM
  plus deterministic state, rules, gap detection, question prioritization,
  validation, and human approval.
- **Agents own tasks; the platform owns workflow and case state.** Individual
  LLM agents must never become independent systems of record.

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
                       │  ┌───────────────────────────────────────┐   │
                       │  │  Workflow engine (orchestrator)        │   │
                       │  │   agent registry + stage graph         │   │
                       │  │   + deterministic reasoning pipeline   │   │
                       │  └───────────────────────────────────────┘   │
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

The API hosts two cooperating layers:

1. **The reasoning pipeline** (`app/agent/`) — the deterministic
   extract → state → gap → question flow that powers the meeting portal and
   the intake agents.
2. **The workflow orchestration layer** (`app/workflow/` + `app/agents/`) — a
   declarative stage graph that schedules specialized agents to produce the
   methodology document.

---

## 3. Repository Layout

```
methodology-agent/
├── app/                      # Backend (FastAPI) — the core
│   ├── main.py               # App wiring, agent registry, workflow service
│   ├── api/                  # HTTP endpoints
│   │   ├── health.py         # /health
│   │   ├── routes.py         # /analyze, /extract, /question, /methodology-state
│   │   ├── cases.py          # /cases (intake, confirm, advance, approve)
│   │   ├── meetings.py       # /meetings (methodology session) + analyze/answer/state
│   │   ├── meeting.py        # /api/v1/meetings (Jitsi meeting session) + events
│   │   ├── knowledge.py      # /knowledge CRUD + approve/reject + search
│   │   └── tts.py            # /tts (edge-tts neural speech)
│   ├── workflow/             # orchestration layer
│   │   ├── engine.py         # WorkflowEngine — the control plane
│   │   ├── definitions.py    # WorkflowDefinition / StageDefinition (data)
│   │   ├── definitions_registry.py # the methodology_development workflow
│   │   ├── contracts.py      # Agent + AgentContract + AgentResult
│   │   ├── registry.py       # AgentRegistry (discoverable by id)
│   │   ├── service.py        # WorkflowService (engine + persistence + events)
│   │   ├── repository.py     # stage states, tasks, approvals, audit log
│   │   ├── states.py         # StageStatus / TaskStatus / ApprovalDecision
│   │   └── conditions.py     # boolean condition facts
│   ├── agents/               # specialized agents (one file each)
│   │   ├── elicitation.py            # meeting → case proposal
│   │   ├── document_analysis.py      # Word doc → case proposal
│   │   ├── request_detector.py       # "is this a methodology request?"
│   │   ├── document_parser.py        # docx/pdf parsing
│   │   ├── scad_input.py             # current-practice analysis
│   │   ├── methodology_qa.py         # clarification questions
│   │   ├── indicator.py              # indicator specifications
│   │   ├── scad_methodology.py       # SCAD-specific methodology
│   │   ├── compliance.py             # QA / compliance review
│   │   ├── gap_assessment.py         # gap assessment report
│   │   └── document_generation.py    # DOCX rendering (cross-cutting)
│   ├── research/             # international research agent + source policy
│   │   ├── agent.py          # InternationalResearchAgent
│   │   └── sources.py        # source categories + credibility filtering
│   ├── case/                 # case domain layer
│   │   ├── consolidation.py  # build_case_proposal (deterministic)
│   │   ├── repository.py     # Source / Evidence / Case / Artifact persistence
│   │   └── service.py        # CaseService
│   ├── agent/                # the deterministic reasoning pipeline
│   │   ├── methodology_agent.py  # orchestrator
│   │   ├── extractor.py      # LLM extraction (only LLM caller in agent)
│   │   ├── state_manager.py  # deterministic structured state
│   │   ├── gap_detector.py   # deterministic gap detection
│   │   ├── question_generator.py # deterministic question generation
│   │   ├── prompts.py        # prompt strings + JSON schema
│   │   └── terminology.py    # Arabic/English terms + language detection
│   ├── models/               # Pydantic models + SQLAlchemy ORM
│   │   ├── case.py           # MethodologyCase / Source / Evidence / Artifact
│   │   ├── extraction.py     # ExtractionResult shape
│   │   ├── methodology_state.py # MethodologyState + FieldState
│   │   ├── standardized_methodology.py # standardized document schema
│   │   ├── scad_methodology.py   # SCAD document schema
│   │   ├── indicator.py      # IndicatorSpecification
│   │   ├── gap_assessment.py # GapAssessment
│   │   ├── compliance.py     # QAReport / QAFinding
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
│   │   ├── dashboard.py      # dashboard websocket
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
├── scripts/                  # download / benchmark / healthcheck / workflow spec
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
| API | `methodology-api` | local build (`Dockerfile`) | `127.0.0.1:8000` | FastAPI backend + workflow engine |
| Embedding | `methodology-embedding` | local build (`Dockerfile.embedding`) | `127.0.0.1:8001` | sentence-transformers embeddings |
| Postgres | `methodology-postgres` | `postgres:17-alpine` | `127.0.0.1:5432` | case/workflow/knowledge state |
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

Separate from both is the **Methodology Case** (see §4.3), the source-independent
business object the multi-agent workflow operates on.

### 4.3 Data model (PostgreSQL)

The DB has two layers of tables.

**Meeting / knowledge layer** (the portal):

- `meetings` — `id` (M-prefixed), `status`, `language`, `methodology_state` (JSONB).
- `knowledge_items` — `id` (K-prefixed), `concept`, `statement`, `domain`,
  `status` (lifecycle), `source`, `evidence`, `confidence`, `validated_by`,
  `effective_from`, `meeting_id`, `parent_id` (tree), `qdrant_point_id`.
- `meeting_sessions` — UUID id, `session_id`, `jitsi_room_name` (unique),
  `meeting_title`, `created_by`, `status`, timestamps.
- `meeting_events` — audit log (`event_type`, `session_id`, `meeting_id`, `payload`).

**Workflow layer** (the multi-agent system):

- `sources` — `SRC-*` original inputs (meeting / word_document / pdf_document).
- `evidence` — `E-*` traceable statements pointing back to a source.
- `methodology_cases` — `METH-*` the single authoritative case (JSON document).
- `case_artifacts` — `ART-*` versioned artifacts produced per stage.
- `workflow_stages` — one row per (case, stage) with current `status`.
- `agent_tasks` — append-only record of every agent execution (inputs/outputs).
- `approvals` — append-only human approval decisions.
- `audit_log` — append-only workflow event trail.

The JSON document is authoritative; the indexed columns exist only for querying
(the same pattern as `meetings.methodology_state`).

### 4.4 Methodology state (the core data structure)

`MethodologyState` (Pydantic) is the single source of truth for what the AI has
learned in a **meeting**. It has **scalar fields** with a `value` + `status` +
`confidence`, and **list fields**:

- Scalars: `objective`, `target_population`, `statistical_unit`,
  `reference_period`, `frequency`, `geographic_scope`, `budget`, `scope`.
- Lists: `indicators`, `dimensions`, `data_sources`, `definitions`,
  `business_rules`, `quality_rules`, `constraints`, `decisions`,
  `open_questions`, `roles`, `success_metrics`, `training_needs`.

Each scalar is a `FieldState` with:

- `value: str | None`
- `status`: one of `unknown | inferred | proposed | confirmed | rejected | conflicting`
- `confidence: float` (0..1)

The status taxonomy is the heart of the "inference is not fact" rule. The
`MethodologyCase` reuses the same epistemic status for its evidence.

---

## 5. How the AI Agents Orchestrate the Work

This is the most important section. The system has **two layers of
orchestration**, both deliberately LLM-constrained:

1. **The deterministic reasoning pipeline** (`MethodologyAgent`) — used by the
   meeting portal and the intake agents. Only the `Extractor` talks to the LLM;
   everything else is pure Python.
2. **The workflow engine** (`WorkflowEngine`) — a declarative stage graph that
   schedules specialized agents to produce the methodology document. Agents
   produce structured results; the engine validates, persists, and transitions.

### 5.1 The reasoning pipeline (used for intake)

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

**`Extractor`** (`app/agent/extractor.py`)
- The **only** component in the pipeline that calls the LLM.
- Sends a system prompt + user prompt asking for JSON matching a fixed schema.
- Strips markdown fences, finds the first balanced JSON object, sanitizes lists,
  validates with Pydantic (`ExtractionResult`); retries once on failure.
- Optionally appends "existing approved knowledge" (RAG context) so extraction
  reuses canonical definitions.

**`StateManager`** (`app/agent/state_manager.py`)
- Applies an `ExtractionResult` to a `MethodologyState`.
- Key invariant: **a `confirmed` field is never downgraded** by an
  `inferred`/`proposed` value.

**`GapDetector`** (`app/agent/gap_detector.py`)
- Pure, LLM-free. A gap is "resolved" only when its field `status == "confirmed"`.
- Priority = `impact × uncertainty × dependency × confidence_gap`.

**`QuestionGenerator`** (`app/agent/question_generator.py`)
- Deterministic. Maps the top gap to a domain question template; prefers the
  LLM's `recommended_question` when aligned. `generate_many()` populates the
  Questions panel.

`analyze` runs: detect language → RAG retrieve → extract → apply → detect gaps →
generate question. The `answer` path is the same `analyze` with the human's
answer as input text.

### 5.2 The workflow layer (produces the methodology document)

The workflow engine (`app/workflow/engine.py`) is the control plane. The workflow
itself is **data**, declared in `app/workflow/definitions_registry.py`:

```
requirement_case  ──► international_research ──► standardized_methodology (approval)
                                                     │
                          ┌──────────────────────────┤
                          ▼                          │
                    scad_input_analysis              │
                          │                          │
                          ▼                          │
                      clarification                  │
                          │                          │
                          ▼                          ▼
              indicator_development ─────────► scad_methodology (approval)
                                                    │
                                         ┌──────────┴──────────┐
                                         ▼                     ▼
                                     compliance           gap_assessment
```

Stage properties:

- `depends_on` — a stage runs only when its dependencies are `COMPLETED`.
- `condition` — a boolean fact that activates/deactivates a stage
  (e.g. `scad_input_analysis` needs `scad_documents_available`). A deactivated
  stage counts as satisfied for its dependents but still runs if its condition
  later becomes true.
- `approval_required` — after a successful run the stage enters
  `WAITING_FOR_HUMAN` instead of `COMPLETED`.

Stage statuses (`app/workflow/states.py`): `PENDING`, `READY`, `RUNNING`,
`WAITING_FOR_AGENT`, `WAITING_FOR_HUMAN`, `COMPLETED`, `SKIPPED`, `FAILED`,
`BLOCKED`, `CANCELLED`.

**Agents** (`app/agents/*.py`) each expose an `AgentContract` (id, input/output
schema, `approval_required`, `failure_policy`, `can_modify_case`,
`can_propose_case_updates`) and implement `run(inputs) -> AgentResult`. They
never own state; the engine injects upstream outputs keyed by dependency stage
id, validates required outputs, and persists results. Agents registered in
`main.py`:

| Agent id | Stage | LLM? | Purpose |
|---|---|---|---|
| `methodology_requirement_elicitation_agent` | intake | extractor only | meeting → case proposal |
| `requirement_document_analysis_agent` | intake | extractor only | Word doc → case proposal |
| `international_research_agent` | `international_research` | yes | standards / NSO practices |
| `standardized_methodology_agent` | `standardized_methodology` | yes | generic best-practice methodology |
| `scad_input_agent` | `scad_input_analysis` | yes | current-practice mapping |
| `methodology_qa_agent` | `clarification` | yes | targeted questions |
| `indicator_agent` | `indicator_development` | yes | candidate indicator specs |
| `scad_methodology_agent` | `scad_methodology` | yes | SCAD-specific methodology |
| `compliance_agent` | `compliance` | yes (advisory) | QA / completeness review |
| `gap_assessment_agent` | `gap_assessment` | yes | gap assessment report |

`document_generation.py` is a cross-cutting, non-LLM helper that renders the
structured `StandardizedMethodology`, `SCADMethodology`, and `GapAssessment`
schemas to DOCX (default A4/Arial rules, or the SCAD template with red-italic
`[To be confirmed by SCAD]` annotations).

### 5.3 Case lifecycle (end to end)

The workflow operates on a `MethodologyCase` (`app/models/case.py`), the single
authoritative business object, created source-independently from a meeting or a
document.

1. **Intake** — `POST /cases` (meeting) or `POST /cases/intake-document` (Word).
   A `request_detector` first asks *"is this a methodology request?"*; if not,
   the request is rejected (422). Otherwise the intake agent runs the reasoning
   pipeline, evidence is created (traceable to the source), a case proposal is
   built (`build_case_proposal`), and the case is set to
   `requirements_review` with stage `requirement_case = WAITING_FOR_HUMAN`.
2. **Human confirmation** — `POST /cases/{id}/confirm` with
   `confirm | edit | request_more | cancel`. `confirm` approves
   `requirement_case`, unblocking the workflow.
3. **Advance** — `POST /cases/{id}/advance` runs ready stages level-by-level
   until a gate or completion. The engine emits events, records tasks, and
   persists stage states and audit entries.
4. **Approval gates** — `POST /cases/{id}/stages/{stage_id}/approve` with
   `approved | request_changes | rejected`. `request_changes` resets the stage to
   `READY` for re-run; `rejected` blocks it.
5. **Conditional stages** — activated by `condition_context` / derived facts
   (`scad_documents_available`, `unresolved_scad_requirements`,
   `indicators_required`, `gap_assessment_required`). SCAD documents are
   uploaded via `POST /cases/{id}/scad-documents` and stored as
   `scad_document` artifacts.

`WorkflowService` (`app/workflow/service.py`) binds the pure engine to
persistence + the real-time broker, records every transition to the audit log,
and syncs the case summary (`completed_stages`, `pending_actions`,
`current_stage`, `status`).

### 5.4 Where state lives

Two places, reconciled by the API:

- The API holds a process-level `MethodologyAgent` (`app.state.agent`) whose
  `StateManager` has an in-memory `MethodologyState` — used by the stateless
  meeting endpoints.
- The database `meetings.methodology_state` is the **authoritative persisted**
  copy for meetings.

The case workflow is fully DB-backed: `methodology_cases`, `workflow_stages`,
`agent_tasks`, `approvals`, and `audit_log` are the system of record.

### 5.5 Human-in-the-loop knowledge

The AI never publishes knowledge by itself. The lifecycle is:

`candidate` → (human) → `approved` / `rejected` → `published`

- `POST /knowledge/candidate` creates a `candidate` (also used by the frontend
  "add node" action in the knowledge graph).
- `POST /knowledge/{id}/approve` with `decision=approve|reject` transitions it.
- **Only approved** knowledge is embedded and indexed into Qdrant
  (`_index_knowledge`); RAG retrieval therefore only ever surfaces approved
  knowledge.

The workflow's approval gates are the analogous control for methodology
artifacts: `standardized_methodology` and `scad_methodology` cannot complete
without a human `approved` decision.

### 5.6 RAG (retrieval-augmented extraction)

`app/knowledge/rag.py`:

- `index_knowledge()` — embeds the statement (`passage` task) and upserts into
  Qdrant with payload (knowledge_id, concept, domain, statement).
- `retrieve(query)` — embeds the query (`query` task) and returns top-k matches.
- Retrieval is **best-effort and never fatal**: any error returns `[]`.

The embedding service prefixes text with `"query: "` / `"passage: "` (required
by `multilingual-e5-small`) and normalizes embeddings.

---

## 6. Real-Time Event System

The backend pushes progress to the browser over a WebSocket, and the frontend
reacts by updating UI state. This is a **pub/sub fan-out**, not a request/response.

### 6.1 Backend (`app/realtime/`)

- **`EventBroker`** (`broker.py`) — in-process broker. Each connected WebSocket
  registers a `Subscription` (an `asyncio.Queue`) keyed by `session_id`.
  `publish()` is thread-safe via `loop.call_soon_threadsafe`.
- **Event envelope** (`events.py`) — every event is an `EventEnvelope` with
  `event_id`, `event_type`, `session_id`, `meeting_id`, `timestamp`, `sequence`,
  and `payload`. Workflow events (`stage.started`, `approval.requested`, etc.)
  flow through the same broker keyed by `case_id`.
- **WebSocket endpoint** (`websocket.py`) — `GET /ws/{session_id}`. Sends a
  `state.snapshot` first, then streams queued events until disconnect.
- **Snapshot builder** (`service.py`) — loads meeting state from the DB, re-runs
  gap detection + question generation, returns the full snapshot.

### 6.2 Frontend (`store/store.js`, `realtime/socket.js`, `hooks/useRealtime.js`)

- `socket.js` — WebSocket client with exponential-backoff reconnect.
- `useRealtime(sessionId)` — opens/closes the socket on session change.
- `store.js` — a tiny external store (via `useSyncExternalStore`); dedupes by
  `event_id` and reduces each `event_type` into state.

---

## 7. Frontend Flow (React)

Phases in `App.jsx`:

1. **`login`** — name entry (`LoginScreen`).
2. **`setup`** — a chip toggle chooses **New Meeting** or **Existing Meeting**:
   - *New Meeting*: creates a methodology session (`POST /meetings`), then a
     Jitsi meeting (`POST /api/v1/meetings`), then enters the meeting phase.
   - *Existing Meeting*: a dropdown of demo meetings joins the saved room.
3. **`meeting`** — the live meeting screen:
   - Left: `JitsiMeeting` iframe.
   - Right: tabs — **Questions**, **Activity**, **Methodology**, **Knowledge**.
   - Floating action button opens the **AI Methodology Assistant** dialog.

> **Current scope note:** the frontend implements the *live meeting portal*. The
> multi-agent case workflow (§5.2–5.3) is currently exercised through the REST
> API (`/cases/*`); there is no dedicated case-workflow UI yet.

### 7.1 How the AI is triggered during a meeting

- On participant join (participant count reaches 2), `loadAssistantContext()`
  calls `analyzeSession(sessionId, objective || 'Methodology session')`.
- Generated questions appear in the Questions panel; clicking **Ask** shows the
  question, sends it to the Jitsi chat, and **speaks it aloud** (TTS).
- Answering (`answerSession`) re-runs the pipeline with the answer.

### 7.2 TTS (text-to-speech)

`frontend/src/lib/speech.js` + `app/api/tts.py`:

- Frontend requests `GET /tts?text=...&voice=...`; backend uses `edge-tts`
  (free, no API key) with default voice `en-US-JennyNeural`.
- Falls back to the browser's `speechSynthesis` if unavailable.

---

## 8. Knowledge Graph (Cytoscape)

`frontend/src/components/KnowledgeGraph.jsx` renders knowledge items as a
**left-to-right tree** (`dagre` layout, `rankDir: 'LR'`). Click a parent to
collapse/expand; select a node to see its statement, delete it, or add a child.
Deletion cascades to descendants.

---

## 9. Evaluation Harness (`evaluation/`)

A standalone Python package that replays prerecorded multilingual transcripts
through the same production pipeline and produces evidence-linked reports.

- `cli.py` — `run` and `review` subcommands.
- `engine.py` — simulates incremental meeting progression.
- `adapters.py` — `mock` (deterministic, no LLM), `local`/`production` (real LLM).
- Outputs per meeting: `report.html`, `report.md`, `state_history.json`, etc.

---

## 10. Testing

`tests/` contains pytest unit tests. The LLM is mocked, so tests need no GPU,
Docker, or internet. Run with `py -m pytest -q`.

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
| `QDRANT_COLLECTION` | `methodology_knowledge` |
| `EMBEDDING_URL` | `http://embedding:8001` |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` |
| `JITSI_BASE_URL` | `https://localhost:8443` |
| `JITSI_JWT_SECRET` | (Jitsi JWT shared secret) |

The frontend uses `VITE_JITSI_DOMAIN`, `VITE_API_URL`, `VITE_WS_URL`.

---

## 12. Key Design Principles (do not violate)

1. **The LLM is a reasoning component, not the agent.** State, gap detection,
   question generation, and validation are deterministic code.
2. **Agents own tasks; the platform owns workflow and case state.** Agents return
   structured results and never maintain a separate system of record.
3. **LLMs do not control workflow transitions.** They may *recommend*; the
   orchestrator decides.
4. **Inference is not fact.** A field is only "resolved" when `confirmed`;
   inferred/proposed values remain open gaps and must not downgrade a confirmed
   field.
5. **Human approval is mandatory** before knowledge or gated methodology stages
   become authoritative.
6. **Questions are always in English**, even when the discussion is Arabic.
7. **Provenance is mandatory.** Agent-generated statements must trace to source
   evidence, research, a human response, or explicit inference.
8. **Never invent facts; preserve uncertainty; never silently resolve
   contradictions.**
9. **Best-effort external dependencies.** RAG and TTS degrade gracefully rather
   than fail the request.
10. **Self-hosted and free** — no cloud AI, no API keys on the core path.

---

## 13. Known Limitations / Current State

- **No dedicated case-workflow UI** — the multi-agent workflow is driven via the
  `/cases/*` REST API; the frontend implements only the live meeting portal.
- **No live audio transcription** wired into the meeting flow (the transcriber
  module is optional and unused in the live portal).
- **TTS requires outbound internet** to Microsoft's edge TTS endpoint; falls back
  to the robotic browser voice if unreachable.
- **Single-instance realtime broker** — pub/sub state is in-process and not shared
  across multiple API replicas.
- **Single-instance workflow engine** — stage/task/audit state is DB-backed, but
  the engine runs synchronously within a single API process (no distributed
  task queue yet).
- **Self-signed TLS** — corporate users must trust the certificate.
- The LLM (4 GB quantized model on a 4 GB GPU) can be slow and occasionally
  times out; the API surfaces this as an `LLMError`.
- The `requirement_case` stage's agent id (`methodology_case_agent`) is not an
  autonomous agent; case creation and confirmation are handled by the intake
  endpoints (§5.3) rather than the engine.
