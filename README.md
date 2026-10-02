# Bilingual (Arabic/English) Methodology Agent

A local, Docker-based, open-source AI platform that turns unstructured bilingual
business discussion into structured statistical methodology knowledge — and
orchestrates a set of specialized agents to produce a full methodology document.

The platform:

- understands Arabic, English, and Arabic/English code switching;
- extracts structured methodology requirements, definitions, data sources,
  constraints, and decisions;
- identifies missing methodology information (gaps);
- generates precise, non-leading, English methodology questions;
- separates inference from confirmed fact;
- orchestrates multiple specialized agents over shared case state to produce a
  methodology document (research → standardized methodology → SCAD-specific
  methodology → compliance → gap assessment);
- never finalizes methodology without human approval.

## Architecture

The system is **not a swarm of independent agents**. A central workflow
orchestrator controls what runs, in what order, with what inputs, and only the
orchestrator owns workflow state and authoritative case state. Agents are
specialized, LLM-backed workers that produce structured outputs; a human
approves at explicit gates.

```
Meeting / Word document
        │
        ▼
  Requirement intake            (Elicitation / Document Analysis agent)
        │
        ▼
  Methodology Case              (shared business object)
        │
        ▼
  Human confirmation gate
        │
        ▼
  Workflow engine (orchestrator)
        │
        ├─► International research
        ├─► Standardized methodology          ◄── approval gate
        ├─► SCAD input / current-practice analysis
        ├─► Clarification (Q&A)
        ├─► Indicator conceptualization
        ├─► SCAD-specific methodology         ◄── approval gate
        ├─► Compliance / QA
        └─► Gap assessment
        │
        ▼
  Methodology documents (DOCX) + reports
```

The platform owns the state machine; agents own individual tasks. LLMs recommend,
the engine validates and transitions. The final output is a structured
**methodology document** (standardized and SCAD-specific) plus QA and gap
assessment reports.

## The agents

| Agent (id)                              | Stage                     | Purpose                                                        |
| --------------------------------------- | ------------------------- | -------------------------------------------------------------- |
| Elicitation (`methodology_requirement_elicitation_agent`) | intake | Convert a bilingual meeting into a case proposal |
| Document analysis (`requirement_document_analysis_agent`) | intake | Convert Word requirement documents into a case proposal |
| International research (`international_research_agent`) | `international_research` | Identify relevant international standards / NSO best practices |
| Standardized methodology (`standardized_methodology_agent`) | `standardized_methodology` | Generic, internationally informed methodology (approval gate) |
| SCAD input (`scad_input_agent`) | `scad_input_analysis` | Analyze SCAD current-practice documents vs. the standardized methodology |
| Methodology Q&A (`methodology_qa_agent`) | `clarification` | Targeted, prioritized clarification questions |
| Indicator (`indicator_agent`) | `indicator_development` | Candidate indicator specifications |
| SCAD methodology (`scad_methodology_agent`) | `scad_methodology` | Final SCAD-specific methodology document (approval gate) |
| Compliance (`compliance_agent`) | `compliance` | QA / completeness / consistency review |
| Gap assessment (`gap_assessment_agent`) | `gap_assessment` | SCAD practice vs. standardized methodology gap report |
| Document generation (cross-cutting) | — | Render structured artifacts to DOCX |

## The workflow

Stages are declared as data (`app/workflow/definitions_registry.py`), with
dependencies, conditions, and approval gates. Conditional stages activate only
when their condition is true (e.g. `scad_input_analysis` runs only when SCAD
documents are available). Stages requiring human sign-off are `standardized_methodology`
and `scad_methodology`.

Every agent exposes a contract (inputs, outputs, approval, failure policy) and
returns structured results that the engine validates and persists; agents never
own authoritative state.

## Prerequisites

- Docker Desktop (WSL2 backend recommended on Windows)
- NVIDIA GPU passthrough into Docker
- ~2.5 GB free disk for the model, plus Docker images

## Quick Start

1. Verify GPU access:

   ```powershell
   docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
   ```

2. Download the model:

   ```powershell
   py -m pip install -U huggingface_hub
   huggingface-cli download `
     unsloth/Qwen3-4B-Instruct-2507-GGUF `
     Qwen3-4B-Instruct-2507-Q4_K_M.gguf `
     --local-dir .\models
   ```

3. Build and start the stack (LLM, API, Postgres, Qdrant, embedding):

   ```powershell
   docker compose build
   docker compose up -d
   docker compose ps
   ```

   The Jitsi video-conference stack is separate — see `docs/JITSI_DEPLOYMENT.md`
   and `jitsi/`.

4. Verify:

   ```powershell
   curl.exe http://127.0.0.1:8000/health
   curl.exe http://127.0.0.1:8080/health
   ```

5. Create a methodology case from a bilingual discussion:

   ```powershell
   $body = @{
       text = "نريد مؤشر شهري عن المنشآت النشطة. البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه."
       language = "ar"
   } | ConvertTo-Json

   Invoke-RestMethod `
       -Uri http://127.0.0.1:8000/cases `
       -Method POST `
       -ContentType "application/json" `
       -Body $body
   ```

6. Confirm the case, then advance the workflow:

   ```powershell
   # Confirm the requirement case (decision: confirm | edit | request_more | cancel)
   Invoke-RestMethod -Uri http://127.0.0.1:8000/cases/$caseId/confirm `
       -Method POST -ContentType "application/json" `
       -Body '{"decision":"confirm"}'

   # Run ready stages up to the next approval gate
   Invoke-RestMethod -Uri http://127.0.0.1:8000/cases/$caseId/advance `
       -Method POST -ContentType "application/json" -Body '{}'
   ```

   Approve gated stages with
   `POST /cases/{id}/stages/{stage_id}/approve` (`approved | request_changes | rejected`).

## API

| Method | Endpoint                              | Description                                      |
| ------ | ------------------------------------- | ------------------------------------------------ |
| GET    | `/health`                             | API + LLM health status                          |
| POST   | `/cases`                              | Create a methodology case from a discussion       |
| POST   | `/cases/intake-document`              | Create a case from a Word document                |
| GET    | `/cases`                              | List cases                                        |
| GET    | `/cases/{id}`                         | Case + workflow stages + audit trail              |
| POST   | `/cases/{id}/confirm`                 | Confirm / edit / request-more / cancel a case     |
| POST   | `/cases/{id}/scad-documents`          | Upload SCAD current-practice documents            |
| POST   | `/cases/{id}/advance`                 | Run ready workflow stages                         |
| POST   | `/cases/{id}/stages/{stage}/approve`  | Approve a gated stage                             |
| GET    | `/cases/{id}/stages/{stage}/output`   | Latest output of a stage                          |
| POST   | `/analyze`                            | Single-shot pipeline (extract + state + gap + question) |
| POST   | `/extract`                            | Structured methodology extraction                 |
| POST   | `/question`                           | Gap detection + question generation               |
| POST   | `/methodology-state`                  | Current structured methodology state              |
| POST   | `/meetings`                           | Create a methodology session                      |
| POST   | `/meetings/{id}/analyze`              | Analyze discussion within a session               |
| POST   | `/meetings/{id}/answer`               | Re-run pipeline with a human answer               |
| POST   | `/api/v1/meetings`                    | Jitsi meeting lifecycle (create/start/end/events) |
| POST   | `/knowledge/candidate`                | Propose a knowledge item                          |
| POST   | `/knowledge/{id}/approve`             | Approve / reject knowledge (approve indexes to RAG) |
| GET    | `/knowledge/search`                   | RAG search over approved knowledge                |
| GET    | `/tts`                                | Neural text-to-speech (edge-tts)                  |
| WS     | `/ws/{session_id}`                    | Real-time event stream                            |

All endpoints return JSON. Methodology questions are always produced in English.

## Configuration

Configuration is read from environment variables (see `.env.example`):

| Variable                | Default                                                              |
| ----------------------- | -------------------------------------------------------------------- |
| `LLM_BASE_URL`          | `http://llm:8080/v1`                                                 |
| `LLM_MODEL`             | `qwen3-4b-instruct-2507`                                             |
| `LLM_TIMEOUT_SECONDS`   | `120`                                                                |
| `LLM_TEMPERATURE`       | `0.1`                                                                |
| `LLM_MAX_TOKENS`        | `1200`                                                               |
| `DATABASE_URL`          | `postgresql+psycopg://methodology:methodology@postgres:5432/methodology` |
| `QDRANT_URL`            | `http://qdrant:6333`                                                 |
| `QDRANT_COLLECTION`     | `methodology_knowledge`                                              |
| `EMBEDDING_URL`         | `http://embedding:8001`                                              |
| `EMBEDDING_MODEL`       | `intfloat/multilingual-e5-small`                                     |
| `JITSI_BASE_URL`        | `https://localhost:8443`                                             |
| `JITSI_JWT_SECRET`      | (Jitsi JWT shared secret)                                            |

The default is fully local: no cloud AI provider and no API keys are required.

## Services

| Service    | Container              | Port (host)          | Role                                  |
| ---------- | ---------------------- | -------------------- | ------------------------------------- |
| LLM        | `methodology-llm`      | `127.0.0.1:8080`     | OpenAI-compatible chat (llama.cpp)    |
| API        | `methodology-api`      | `127.0.0.1:8000`     | FastAPI backend + workflow engine     |
| Embedding  | `methodology-embedding`| `127.0.0.1:8001`     | sentence-transformers embeddings      |
| Postgres   | `methodology-postgres` | `127.0.0.1:5432`     | case / workflow / knowledge state     |
| Qdrant     | `methodology-qdrant`   | `127.0.0.1:6333/6334`| vector store for approved knowledge   |
| Jitsi      | `jitsi-*`              | `8443`               | video conference (separate stack)     |

The LLM runs on the GPU; embeddings run on CPU. Model: `Qwen3-4B-Instruct-2507`
(`Q4_K_M` GGUF). Embedding model: `intfloat/multilingual-e5-small` (384-dim).

## Testing

Unit tests mock the LLM and require no GPU, Docker, or internet:

```powershell
py -m pytest -q
```

## Project Layout

```
methodology-agent/
├── app/
│   ├── main.py               # App wiring, agent registry, workflow service
│   ├── api/                  # FastAPI routes (cases, meetings, knowledge, tts, ...)
│   ├── workflow/             # orchestration: engine, definitions, contracts, registry
│   ├── agents/               # specialized agents + document generation/parsing
│   ├── agent/                # the reasoning pipeline (extractor, state, gap, question)
│   ├── case/                 # case domain (repository, consolidation, service)
│   ├── research/             # international research agent + source credibility policy
│   ├── models/               # Pydantic schemas + SQLAlchemy ORM
│   ├── knowledge/            # knowledge lifecycle + RAG
│   ├── meeting/              # meeting lifecycle + Jitsi adapter
│   ├── realtime/             # in-process pub/sub + WebSocket
│   ├── speech/               # faster-whisper transcriber (optional)
│   ├── llm/                  # OpenAI-compatible LLM client
│   └── core/                 # config, db, logging
├── frontend/                 # React + Vite + Tailwind + shadcn/ui
├── embedding_service/        # sentence-transformers HTTP service
├── jitsi/                    # Jitsi stack config + certs
├── evaluation/               # transcript-replay evaluation harness
├── tests/                    # pytest unit tests (LLM mocked)
├── models/                   # GGUF model (not committed)
├── docker-compose.yml
├── Dockerfile                # API image
├── Dockerfile.embedding      # embedding image
└── requirements*.txt
```

For an in-depth, developer-facing overview of the platform (data model, real-time
events, frontend flow, design principles), see `docs/PORTAL_OVERVIEW.md`. The
full multi-agent workflow specification is in
`scripts/SCAD_Methodology_Agentic_Workflow_Context.md`.

## License

See [LICENSE](LICENSE). The application is Apache-2.0. The Qwen3 model is
Apache-2.0. Review the license of every dependency before organizational
deployment.
