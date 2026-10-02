# Build & Run Guide

This document explains how to run the platform and what each agent does.

---

## 1. Overview

The platform is a Docker-based, self-hosted system with these moving parts:

| Component | How it runs |
|---|---|
| LLM server (llama.cpp + Qwen3-4B) | Docker (GPU) |
| API + workflow engine (FastAPI) | Docker |
| Embedding service (sentence-transformers) | Docker (CPU) |
| Postgres (case/workflow/knowledge state) | Docker |
| Qdrant (vector store) | Docker |
| Jitsi (video conference) | Docker (separate compose) |
| Frontend (React + Vite) | Local dev server (`npm`) |

---

## 2. Prerequisites

- Docker Desktop (WSL2 backend recommended on Windows)
- NVIDIA GPU passthrough into Docker
- Node.js + npm (for the frontend)
- Python (`py`) for the test suite and model download
- ~2.5 GB free disk for the model, plus Docker images

---

## 3. Run the project

### 3.1 Verify GPU access

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
```

### 3.2 Download the model

```powershell
py -m pip install -U huggingface_hub
huggingface-cli download `
  unsloth/Qwen3-4B-Instruct-2507-GGUF `
  Qwen3-4B-Instruct-2507-Q4_K_M.gguf `
  --local-dir .\models
```

Or use the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_model.ps1
```

### 3.3 Build and start the main stack

```powershell
docker compose build
docker compose up -d
docker compose ps
```

This starts: `llm`, `api`, `postgres`, `qdrant`, `embedding`.

### 3.4 Start the Jitsi video-conference stack (optional)

The Jitsi stack is separate — see `docs/JITSI_DEPLOYMENT.md` for setup and
certificates:

```powershell
# within the jitsi/ directory
docker compose up -d
```

### 3.5 Start the frontend (development)

The frontend runs as a Vite dev server (HTTPS, self-signed cert from the Jitsi
key store):

```powershell
cd frontend
npm install
npm run dev
```

The dev server listens on `https://localhost:5173` (and is exposed on the LAN).
API calls are proxied to the backend, so no separate API URL is required.
Set `VITE_JITSI_DOMAIN` in `frontend/.env` to your Jitsi host.

### 3.6 Verify health

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8080/health
```

Or use the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\healthcheck.ps1
```

---

## 4. Smoke-test the workflow

### 4.1 Create a methodology case from a bilingual discussion

```powershell
$body = @{
    text = "نريد مؤشر شهري عن المنشآت النشطة. البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه."
    language = "ar"
} | ConvertTo-Json

$case = Invoke-RestMethod -Uri http://127.0.0.1:8000/cases `
    -Method POST -ContentType "application/json" -Body $body
$caseId = $case.case.case_id
```

### 4.2 Confirm the requirement case

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/$caseId/confirm" `
    -Method POST -ContentType "application/json" `
    -Body '{"decision":"confirm"}'
```

### 4.3 Advance the workflow (runs ready stages)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/$caseId/advance" `
    -Method POST -ContentType "application/json" -Body '{}'
```

### 4.4 Upload SCAD current-practice documents (activates SCAD stages)

```powershell
# multipart upload; supports .docx and .pdf
curl.exe -F "files=@C:\path\to\current-practice.docx" `
    http://127.0.0.1:8000/cases/$caseId/scad-documents
```

### 4.5 Approve gated stages

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/$caseId/stages/standardized_methodology/approve" `
    -Method POST -ContentType "application/json" `
    -Body '{"decision":"approved"}'
```

### 4.6 Inspect a case, its stages, and stage output

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/$caseId" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/$caseId/stages/scad_methodology/output" -Method GET
```

---

## 5. What each agent does

All agents live in `app/agents/` (plus the research agent in `app/research/`).
Each exposes an `AgentContract` (inputs, outputs, approval, failure policy) and
is registered in `app/main.py`. Agents return structured `AgentResult` objects;
they never own state.

### Intake agents

**Methodology Requirement Elicitation Agent** — `app/agents/elicitation.py`
- ID: `methodology_requirement_elicitation_agent`
- Wraps the deterministic reasoning pipeline (`MethodologyAgent`: extract →
  state → gap → question).
- Inputs: meeting/discussion text + language.
- Outputs: `summary`, `extraction`, `methodology_state`, `gaps`,
  `recommended_question`.
- Purpose: convert a bilingual business meeting into a structured understanding
  of the methodology request (creates the case proposal).

**Requirement Document Analysis Agent** — `app/agents/document_analysis.py`
- ID: `requirement_document_analysis_agent`
- Same pipeline as elicitation, but for Word documents (via `document_parser.py`).
- Inputs: document text + language + filename.
- Purpose: create a case proposal from requirement documents.

**Methodology Request Detector** — `app/agents/request_detector.py`
- Not a workflow stage; a guard used at intake.
- Determines whether the input is a methodology request
  (`is_methodology_request`, confidence, reason). Non-methodology inputs are
  rejected before a case is created.

### Workflow agents

**International Research Agent** — `app/research/agent.py`
- ID: `international_research_agent`
- Stage: `international_research`
- Identifies authoritative international standards, frameworks, classifications,
  and NSO best practices (UN/UNSD/UNECE, ILO, OECD, IMF, World Bank, Eurostat,
  SDMX, GCC-Stat).
- Outputs: `source_register`, `findings`, `research_report`,
  `unresolved_questions`.
- A credibility policy (`app/research/sources.py`) discards user-generated
  content and annotates the rest.

**Standardized Methodology Development Agent** — `app/agents/standardized_methodology.py`
- ID: `standardized_methodology_agent`
- Stage: `standardized_methodology` (approval gate)
- Synthesizes the research into a generic, internationally informed methodology
  (the "ideal", independent of SCAD constraints).
- Outputs: a `StandardizedMethodology` with 12 fixed sections and `source_refs`.

**SCAD Input / Current Practice Analysis Agent** — `app/agents/scad_input.py`
- ID: `scad_input_agent`
- Stage: `scad_input_analysis` (conditional on `scad_documents_available`)
- Reads SCAD current-practice documents and maps them against the standardized
  methodology.
- Outputs: `current_practice`, `mapping_matrix` (implemented/partial/missing),
  `gaps`, `questions`.

**Methodology Q&A / Clarification Agent** — `app/agents/methodology_qa.py`
- ID: `methodology_qa_agent`
- Stage: `clarification` (conditional on `unresolved_scad_requirements`)
- Generates prioritized, non-leading questions for the remaining material
  uncertainty; avoids re-asking what evidence already resolved.
- Outputs: `question_set` (question, reason, dimension, priority).

**Indicator Conceptualization Agent** — `app/agents/indicator.py`
- ID: `indicator_agent`
- Stage: `indicator_development` (conditional on `indicators_required`)
- Develops candidate indicator specifications (name EN/AR, definition, unit,
  population, numerator/denominator, frequency, data sources, classifications,
  derivation rule, quality) with traceability. Max 6 indicators.

**SCAD-Specific Methodology Development Agent** — `app/agents/scad_methodology.py`
- ID: `scad_methodology_agent`
- Stage: `scad_methodology` (approval gate)
- Produces the final SCAD-specific methodology document by adapting the
  standardized methodology to SCAD practice, clarification answers, and
  indicator specs. Applies annotations inline: `[Aligned with: source]`,
  `[Abu Dhabi exception]`, `[To be confirmed by SCAD]`.
- Outputs: a `SCADMethodology` with 9 fixed sections, `source_refs`,
  `indicator_codes`.

**Compliance / QA Agent** — `app/agents/compliance.py`
- ID: `compliance_agent`
- Stage: `compliance`
- Validates the SCAD methodology for completeness, consistency, provenance,
  annotations, and template requirements. Read-only (never modifies state).
- Runs deterministic checks (empty sections, missing citations, unconfirmed
  fields) plus an advisory LLM review.
- Outputs: `qa_report`, `blocking_issues`, `non_blocking_issues`,
  `approval_recommendation`.

**Gap Assessment Agent** — `app/agents/gap_assessment.py`
- ID: `gap_assessment_agent`
- Stage: `gap_assessment` (conditional on `gap_assessment_required`)
- Compares the SCAD methodology against the standardized (international) one and
  produces a formal gap assessment (matrix classified None/Minor/Moderate/Major,
  priority areas, compliance summary, recommendations).

### Cross-cutting helper

**Document Generation** — `app/agents/document_generation.py`
- Not an LLM agent; renders structured schemas to DOCX:
  - `render_standardized_methodology_docx` (A4, Arial, 1-inch margins)
  - `render_scad_methodology_docx` (SCAD template; red-italic
    `[To be confirmed by SCAD]`)
  - `render_gap_assessment_docx` (matrix table)
  - `review_docx` (structural compliance check)

---

## 6. The workflow (stage graph)

Declared as data in `app/workflow/definitions_registry.py`:

```
requirement_case ──► international_research ──► standardized_methodology (approval)
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

- `depends_on` — a stage runs only after its dependencies are `COMPLETED`.
- `condition` — a boolean fact that activates/deactivates a stage. A deactivated
  stage counts as satisfied for its dependents but still runs if its condition
  later becomes true.
- `approval_required` — after a successful run the stage enters
  `WAITING_FOR_HUMAN` instead of `COMPLETED`.

Stage statuses: `PENDING`, `READY`, `RUNNING`, `WAITING_FOR_AGENT`,
`WAITING_FOR_HUMAN`, `COMPLETED`, `SKIPPED`, `FAILED`, `BLOCKED`, `CANCELLED`.

The `requirement_case` stage is not an autonomous agent — it is created and
confirmed by the intake endpoints (`POST /cases`, `POST /cases/{id}/confirm`).

---

## 7. Configuration

Environment variables (see `.env.example`):

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

Frontend env: `VITE_JITSI_DOMAIN` (in `frontend/.env`).

---

## 8. Testing

Unit tests mock the LLM and require no GPU, Docker, or internet:

```powershell
py -m pytest -q
```

---

## 9. Useful endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API + LLM health |
| POST | `/cases` | Create a case from a discussion |
| POST | `/cases/intake-document` | Create a case from a Word document |
| GET | `/cases` | List cases |
| GET | `/cases/{id}` | Case + stages + audit trail |
| POST | `/cases/{id}/confirm` | Confirm / edit / request-more / cancel |
| POST | `/cases/{id}/scad-documents` | Upload SCAD documents |
| POST | `/cases/{id}/advance` | Run ready workflow stages |
| POST | `/cases/{id}/stages/{stage}/approve` | Approve a gated stage |
| GET | `/cases/{id}/stages/{stage}/output` | Latest stage output |
| POST | `/analyze` | Single-shot pipeline |
| POST | `/meetings` | Create a methodology session |
| POST | `/knowledge/candidate` | Propose knowledge |
| POST | `/knowledge/{id}/approve` | Approve / reject knowledge (RAG index) |
| GET | `/knowledge/search` | RAG search |
| GET | `/tts` | Text-to-speech |
| WS | `/ws/{session_id}` | Real-time events |

---

## 10. Troubleshooting

- **LLM health fails** — check `docker compose logs llm`; ensure the model is
  present at `.\models\Qwen3-4B-Instruct-2507-Q4_K_M.gguf`.
- **API can't reach LLM** — the API waits for `llm` to be healthy
  (`depends_on: condition: service_healthy`); confirm the GPU is visible in the
  container.
- **Case stuck in `requirements_review`** — call `/cases/{id}/confirm`.
- **Stage stuck in `WAITING_FOR_HUMAN`** — call
  `/cases/{id}/stages/{stage}/approve` with `approved`.
- **SCAD stages skipped** — upload documents via
  `/cases/{id}/scad-documents` (activates `scad_documents_available`).
- **Frontend cert errors** — the dev server reads certs from
  `jitsi/config/storage/web/keys`; generate them (see `docs/JITSI_DEPLOYMENT.md`)
  or temporarily run Vite without HTTPS.
