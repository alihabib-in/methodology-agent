# AI Methodology Meeting Platform
## Self-Hosted Docker Infrastructure & VDI Implementation Specification

**Document type:** Instruction set for an LLM Coding Agent  
**Target environment:** Developer VDI / Virtual Desktop Infrastructure  
**Deployment model:** Docker / Docker Compose, self-hosted, on-premises capable  
**Primary requirement:** Integrated audio/video meeting application with a real-time AI methodology agent  
**Runtime cloud dependency:** None

---

# 1. Coding-Agent Mission

You are an expert software architect, DevOps engineer, full-stack engineer, AI/ML engineer, and security engineer.

Your task is to **implement a working, self-hosted AI Methodology Meeting Platform** on the user's VDI machine using Docker.

This is not merely an architecture exercise. You must create the repository, configuration, Dockerfiles, Compose files, application scaffolding, database schema, health checks, scripts, tests, documentation, and a runnable local environment.

The platform must provide:

1. Audio/video meetings.
2. Screen sharing.
3. Participant management.
4. Real-time speech processing.
5. Arabic speech recognition.
6. English speech recognition.
7. Arabic-English code-switching support.
8. Speaker attribution where technically feasible.
9. Live transcript.
10. AI methodology reasoning.
11. Detection of missing methodology information.
12. Real-time English questions to participants.
13. Meeting journal.
14. Structured methodology state.
15. Post-meeting knowledge consolidation.
16. Shared organizational methodology knowledge.
17. Semantic knowledge retrieval.
18. APIs for downstream AI agents.
19. Local authentication and RBAC.
20. Fully local persistent storage.
21. Docker-based deployment.
22. CPU fallback where GPU is unavailable.
23. GPU acceleration where available.
24. Backup and restore.
25. Health checks and observability.

The application must initially run on the VDI and later be transferable to internal/on-premises infrastructure without a fundamental redesign.

---

# 2. Critical Architectural Decision

Do **not** build a WebRTC conferencing engine from scratch.

Use **self-hosted Jitsi Meet** for the audio/video meeting infrastructure.

Jitsi is an open-source video conferencing platform with a self-hosting Docker deployment. Its current self-hosting documentation describes a Docker Compose deployment consisting of components including the web interface, XMPP server, conference focus, and video bridge. It also documents the need for HTTPS/WebRTC and UDP media connectivity. Use the current stable Jitsi Docker release rather than cloning its development repository. [Jitsi self-hosting documentation](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/)

The application itself owns:

- meeting lifecycle
- methodology intelligence
- transcript
- AI state
- questions
- answers
- meeting journal
- knowledge
- approvals
- business data
- audit records

Jitsi owns:

- WebRTC
- audio/video transport
- media routing
- participant media
- screen sharing
- conferencing functionality

---

# 3. Non-Negotiable Requirements

## 3.1 Local processing

Runtime processing must not require:

- OpenAI API
- Azure OpenAI
- Anthropic API
- Google AI APIs
- AWS AI services
- cloud speech recognition
- cloud vector databases
- cloud meeting infrastructure

All AI inference must run locally.

Internet access may be used during initial installation to obtain approved open-source images/models, subject to corporate policy.

The architecture must also support a future offline/air-gapped deployment.

## 3.2 Data locality

Persistent data must remain on local Docker volumes or explicitly mounted host directories.

At minimum:

```text
PostgreSQL
Qdrant
MinIO
Keycloak
Jitsi configuration/state
AI models
application configuration
```

must not depend on an external cloud storage service.

## 3.3 Audio/video

The user must be able to:

- join a meeting
- use microphone
- use camera
- see participants
- share screen
- leave meeting
- view connection state

## 3.4 AI

The AI must operate during the meeting.

It must not simply wait for a meeting recording and summarize it.

## 3.5 Language

The system must understand:

- Arabic
- English
- Arabic-English mixed speech
- technical/statistical terminology
- acronyms
- UAE/Gulf business terminology

AI-generated methodology questions must be in English.

Formal methodology outputs must be English by default.

Original transcript must remain available in its original language.

---

# 4. VDI Assumptions

Assume the developer is initially working on a corporate VDI.

The exact hardware is unknown.

The implementation must therefore begin with a system preflight.

Support:

- Windows 10/11 with Docker Desktop + WSL2
- Linux desktop/VDI with Docker Engine + Docker Compose
- NVIDIA GPU if available
- CPU-only fallback

Do not assume that Docker has unrestricted access to:

- host networking
- privileged mode
- GPU
- arbitrary firewall configuration
- internet access

Detect these conditions and report them.

---

# 5. Required VDI Preflight

Create:

```text
scripts/preflight.sh
scripts/preflight.ps1
```

The scripts must report:

```text
OS
architecture
CPU cores
RAM
available disk
Docker version
Docker Compose version
Docker daemon status
GPU
NVIDIA Container Toolkit
WSL2 status where applicable
network connectivity
available ports
```

Linux command examples:

```bash
uname -a
uname -m
nproc
free -h
df -h
docker version
docker compose version
docker info
```

Windows PowerShell equivalents should be provided in `preflight.ps1`.

GPU detection:

```bash
nvidia-smi
```

If unavailable, report:

```text
GPU: not detected
Mode: CPU fallback
```

Do not fail the entire installation merely because no GPU exists.

---

# 6. Minimum Recommended Development Resources

Document resource tiers.

## Tier A — GPU development

Target approximately:

```text
CPU: 8+ cores
RAM: 32+ GB
GPU: NVIDIA GPU
VRAM: 12+ GB preferred
Disk: 100+ GB free
```

## Tier B — CPU/light development

Target approximately:

```text
CPU: 8+ cores
RAM: 16+ GB
Disk: 60+ GB free
```

For Tier B:

- use smaller speech models
- use smaller LLM
- disable nonessential monitoring
- optionally disable diarization
- process speech in less aggressive real time

Do not hard-code these values as absolute requirements. Detect actual resources and recommend a profile.

---

# 7. Docker and Compose Requirements

Use:

- current supported Docker Engine or Docker Desktop
- Docker Compose V2

Do not use legacy:

```text
docker-compose
```

unless compatibility with a corporate environment requires it.

Preferred command:

```bash
docker compose
```

Docker's current documentation treats the Compose Specification as the recommended Compose format; the old top-level `version` field is obsolete. Do not add a `version:` field to the Compose file unless there is a documented compatibility reason. [Docker Compose Specification](https://docs.docker.com/reference/compose-file/)

Verify:

```bash
docker version
docker compose version
```

---

# 8. Repository Structure

Create:

```text
ai-methodology-platform/
│
├── README.md
├── QUICKSTART.md
├── ARCHITECTURE.md
├── SECURITY.md
├── TROUBLESHOOTING.md
├── .gitignore
├── .dockerignore
├── .env.example
├── Makefile
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.gpu.yml
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   └── app/
│       ├── main.py
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── repositories/
│       ├── services/
│       ├── agents/
│       ├── websocket/
│       └── prompts/
│
├── services/
│   ├── speech/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── llm/
│   │   └── README.md
│   └── embeddings/
│       ├── Dockerfile
│       └── app/
│
├── jitsi/
│   ├── README.md
│   ├── .env.example
│   └── config/
│
├── database/
│   ├── seeds/
│   └── fixtures/
│
├── infra/
│   ├── nginx/
│   ├── keycloak/
│   ├── prometheus/
│   └── grafana/
│
├── scripts/
│   ├── preflight.sh
│   ├── preflight.ps1
│   ├── setup.sh
│   ├── setup.ps1
│   ├── start.sh
│   ├── stop.sh
│   ├── healthcheck.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── download_models.sh
│
├── tests/
│   ├── backend/
│   ├── frontend/
│   ├── integration/
│   └── fixtures/
│
└── data/
    ├── postgres/
    ├── qdrant/
    ├── redis/
    ├── minio/
    ├── keycloak/
    ├── jitsi/
    └── models/
```

Do not commit `data/` contents.

---

# 9. Environment Configuration

Create `.env.example`.

Use this structure:

```dotenv
# ============================================================
# APPLICATION
# ============================================================

APP_NAME=ai-methodology-platform
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_LOG_LEVEL=INFO

# ============================================================
# DATABASE
# ============================================================

POSTGRES_DB=methodology
POSTGRES_USER=methodology_app
POSTGRES_PASSWORD=CHANGE_ME

DATABASE_URL=postgresql+psycopg://methodology_app:CHANGE_ME@postgres:5432/methodology

# ============================================================
# REDIS
# ============================================================

REDIS_URL=redis://redis:6379/0

# ============================================================
# QDRANT
# ============================================================

QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=CHANGE_ME

# ============================================================
# MINIO
# ============================================================

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=CHANGE_ME
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=methodology

# ============================================================
# KEYCLOAK
# ============================================================

KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=CHANGE_ME
KEYCLOAK_REALM=methodology
KEYCLOAK_CLIENT_ID=methodology-web

# ============================================================
# JITSI
# ============================================================

JITSI_DOMAIN=meet.local
JITSI_PUBLIC_URL=https://meet.local

# ============================================================
# SPEECH
# ============================================================

ASR_MODEL=large-v3
ASR_DEVICE=auto
ASR_COMPUTE_TYPE=auto
ENABLE_DIARIZATION=true
ENABLE_VAD=true

# ============================================================
# LLM
# ============================================================

LLM_MODEL=CHANGE_ME
LLM_BASE_URL=http://llm:8000
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048

# ============================================================
# EMBEDDINGS
# ============================================================

EMBEDDING_MODEL=CHANGE_ME

# ============================================================
# PRIVACY
# ============================================================

STORE_RAW_AUDIO=false
STORE_VIDEO=false
STORE_TRANSCRIPT=true
STORE_ORIGINAL_LANGUAGE=true
PII_REDACTION_ENABLED=true

# ============================================================
# RETENTION
# ============================================================

RETENTION_DAYS=90
```

The setup script must replace placeholder secrets with generated secrets.

Never commit the real `.env`.

---

# 10. Secrets

For local development, environment variables may be used.

For production-like deployment, prefer Docker secrets or mounted secret files.

Do not:

```text
hard-code passwords
hard-code API keys
commit .env
print secrets in logs
```

Generate secrets using:

```bash
openssl rand -hex 32
```

For example:

```bash
POSTGRES_PASSWORD="$(openssl rand -hex 32)"
QDRANT_API_KEY="$(openssl rand -hex 32)"
MINIO_ROOT_PASSWORD="$(openssl rand -hex 32)"
KEYCLOAK_ADMIN_PASSWORD="$(openssl rand -hex 32)"
```

The generated values must be written to a local protected environment/secrets file and never displayed in terminal output.

---

# 11. Main Docker Compose

Create a Compose file based on the current Compose Specification.

Do not add a `version:` field.

Initial services:

```text
frontend
backend
postgres
redis
qdrant
minio
keycloak
speech
llm
embeddings
nginx
prometheus
grafana
```

Jitsi should be deployed using its official Docker Compose release structure rather than trying to recreate all Jitsi services manually.

Jitsi's current Docker documentation explicitly recommends downloading the latest release package rather than cloning the repository for stable deployments, creating `.env`, generating passwords, preparing configuration directories, and running `docker compose up -d`. Follow the current release documentation rather than assuming a fixed Jitsi image tag. [Jitsi Docker deployment](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/)

---

# 12. Main Compose Template

Create a file conceptually equivalent to:

```yaml
name: ai-methodology-platform

services:

  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - ./data/redis:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10

  qdrant:
    image: qdrant/qdrant:<PINNED_VERSION>
    restart: unless-stopped
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    volumes:
      - ./data/qdrant:/qdrant/storage
    networks:
      - backend
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "curl -fsS http://localhost:6333/readyz || exit 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 10

  minio:
    image: minio/minio:<PINNED_VERSION>
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - ./data/minio:/data
    networks:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    networks:
      - frontend
      - backend
      - ai
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "curl -fsS http://localhost:8000/health || exit 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 10

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    networks:
      - frontend

  speech:
    build:
      context: ./services/speech
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data/models:/models
    networks:
      - ai
    profiles:
      - ai

  llm:
    image: <LOCAL_LLM_IMAGE>
    restart: unless-stopped
    command: <MODEL_SERVER_COMMAND>
    volumes:
      - ./data/models:/models
    networks:
      - ai
    profiles:
      - ai

  embeddings:
    build:
      context: ./services/embeddings
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data/models:/models
    networks:
      - ai
    profiles:
      - ai

  keycloak:
    image: quay.io/keycloak/keycloak:<PINNED_VERSION>
    restart: unless-stopped
    command:
      - start
      - --optimized
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: ${KEYCLOAK_ADMIN}
      KC_BOOTSTRAP_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    networks:
      - frontend
      - backend
    profiles:
      - core

  nginx:
    image: nginx:<PINNED_VERSION>
    restart: unless-stopped
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/certs:/etc/nginx/certs:ro
    ports:
      - "443:443"
      - "80:80"
    depends_on:
      - frontend
      - backend
    networks:
      - frontend
      - backend

networks:
  frontend:
    driver: bridge

  backend:
    driver: bridge
    internal: true

  ai:
    driver: bridge
    internal: true
```

Important:

- Replace placeholder images with verified compatible versions.
- Do not blindly copy this file without validating current image tags and application compatibility.
- Do not expose PostgreSQL, Redis, Qdrant, MinIO or LLM ports directly to the host unless explicitly needed for development.
- Prefer access through backend services.

Qdrant's official local deployment supports Docker storage on the host, but its documentation warns that a default unsecured deployment allows anyone who can reach the service to read/write/delete data. Keep Qdrant on an internal Docker network and configure authentication where applicable. [Qdrant local deployment](https://qdrant.tech/documentation/quick-start/) [Qdrant security](https://qdrant.tech/documentation/tutorials-operations/secure-qdrant/)

---

# 13. Keycloak

Use Keycloak for authentication and RBAC.

Do not use development mode for the production-like configuration.

The current Keycloak documentation supports container deployment and recommends optimized images/configuration for appropriate deployments. Health endpoints are available through the management interface. [Keycloak containers](https://www.keycloak.org/server/containers)

Create:

```text
infra/keycloak/
```

with realm configuration where practical.

Initial roles:

```text
ADMIN
METHODOLOGY_LEAD
METHODOLOGY_ANALYST
MEETING_FACILITATOR
REVIEWER
AI_AGENT
READ_ONLY
```

Permissions must distinguish:

```text
meeting access
transcript access
knowledge read
knowledge create
knowledge approve
knowledge reject
knowledge administer
system administer
```

---

# 14. Jitsi Deployment

Do not implement a fake minimal Jitsi service.

Use the current official Jitsi Docker release.

The coding agent must:

1. Determine the current stable release.
2. Download the release package.
3. Place it under:

```text
jitsi/
```

4. Create `.env` from its supplied `env.example`.
5. Configure:
   - timezone
   - HTTP port
   - HTTPS port
   - public/internal URL
   - JVB advertised IP
6. Generate strong Jitsi internal passwords.
7. Create required writable configuration directories.
8. Start Jitsi with:

```bash
docker compose up -d
```

Jitsi's current documentation notes that HTTPS is important for browser microphone/camera access and documents the media port `10000/udp`; LAN deployments may require configuring `JVB_ADVERTISE_IPS`. [Jitsi Docker self-hosting](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/)

For a VDI-only local development deployment, use a local hostname and local TLS certificate.

Do not assume that `localhost` is sufficient for every browser/WebRTC scenario.

---

# 15. Local DNS / Hostname

Use a local development domain such as:

```text
methodology.local
meet.methodology.local
auth.methodology.local
```

For a single VDI, document the hosts-file approach.

Windows:

```text
C:\Windows\System32\drivers\etc\hosts
```

Linux:

```text
/etc/hosts
```

Example:

```text
127.0.0.1 methodology.local
127.0.0.1 meet.methodology.local
127.0.0.1 auth.methodology.local
```

If the meeting must be accessed by other machines on the corporate LAN, do not use `127.0.0.1`.

Instead use the VDI's reachable IP address and an appropriate internal DNS entry.

The coding agent must detect and document the distinction.

---

# 16. TLS

Create local development certificates.

Preferred development approach:

```text
mkcert
```

If mkcert is unavailable, provide an OpenSSL fallback.

Never instruct the user to disable browser security.

Create:

```text
infra/nginx/certs/
```

and:

```text
jitsi/config/
```

as appropriate.

For production/internal deployment, replace local certificates with organization-approved certificates.

---

# 17. Backend Dockerfile

Create a multi-stage Dockerfile.

Example:

```dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

COPY --from=builder /wheels /wheels

RUN pip install \
    --no-cache-dir \
    /wheels/*

COPY app ./app
COPY alembic.ini .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add only required system packages.

Do not run the application as root.

---

# 18. Frontend Dockerfile

Use a multi-stage build.

Example:

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build


FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Use pinned versions in the actual implementation.

---

# 19. Speech Service

Create:

```text
services/speech/
```

The speech service must support:

```text
VAD
ASR
language detection
timestamps
speaker attribution integration
```

Primary technologies:

```text
faster-whisper
Silero VAD
pyannote.audio
```

Use a configurable model.

Do not hard-code a model size that will exceed VDI resources.

The service should expose an internal API such as:

```text
POST /transcribe
POST /transcribe/chunk
GET /health
GET /ready
```

Streaming transport may use WebSockets.

---

# 20. Speech Data Contract

Every transcript segment should resemble:

```json
{
  "meeting_id": "M-2026-000001",
  "segment_id": "SEG-000001",
  "speaker_id": "P-000002",
  "start_ms": 12500,
  "end_ms": 18800,
  "language": "ar",
  "text_original": "...",
  "text_normalized_en": "...",
  "confidence": 0.91,
  "is_final": true
}
```

Do not discard:

```text
original language
speaker
timestamps
confidence
```

These are required for provenance.

---

# 21. LLM Service

Run the LLM locally.

Prefer:

```text
Qwen-family multilingual instruction model
+
vLLM
```

where VDI hardware supports it.

The exact model must be selected based on:

- Arabic performance
- English performance
- code switching
- context length
- VRAM
- inference speed
- licensing
- model availability

Do not invent model capabilities.

Create a model abstraction:

```python
class LLMGateway:

    async def chat(self, messages, **kwargs):
        ...

    async def extract(self, text, schema):
        ...

    async def classify(self, text, labels):
        ...

    async def generate_question(self, context):
        ...

    async def consolidate_knowledge(self, context):
        ...
```

The rest of the application must not directly call the model server.

---

# 22. Embedding Service

Create:

```text
services/embeddings/
```

Use a multilingual embedding model.

Expose:

```text
POST /embed
GET /health
```

Keep the model configurable.

---

# 23. PostgreSQL Data Model

Create migrations for:

```text
users
roles
user_roles

meetings
meeting_participants
meeting_events

speakers
transcript_segments

methodology_sessions
methodology_state_versions

requirements
definitions
business_rules
constraints
indicators
dimensions
data_sources
decisions

ai_questions
ai_answers

meeting_journal

knowledge_items
knowledge_versions
knowledge_relationships
knowledge_provenance
knowledge_conflicts
knowledge_approvals

terminology
terminology_aliases

audit_events
system_settings
```

Use UUID primary keys.

Also create human-readable IDs:

```text
M-2026-000001
Q-2026-000001
K-2026-000001
```

---

# 24. Methodology State

The core reasoning state must contain at least:

```json
{
  "objective": {
    "value": null,
    "status": "unknown",
    "confidence": 0
  },
  "population": {
    "value": null,
    "status": "unknown",
    "confidence": 0
  },
  "statistical_unit": {
    "value": null,
    "status": "unknown",
    "confidence": 0
  },
  "reference_period": {
    "value": null,
    "status": "unknown",
    "confidence": 0
  },
  "geographic_scope": {
    "value": null,
    "status": "unknown",
    "confidence": 0
  },
  "indicators": [],
  "dimensions": [],
  "data_sources": [],
  "definitions": [],
  "business_rules": [],
  "quality_rules": [],
  "constraints": [],
  "decisions": [],
  "open_questions": []
}
```

Every update must retain evidence.

---

# 25. Methodology Intelligence Pipeline

Implement:

```text
Audio
  ↓
VAD
  ↓
ASR
  ↓
Speaker attribution
  ↓
Transcript segment
  ↓
Conversation buffer
  ↓
Signal extraction
  ↓
Methodology state update
  ↓
Gap detection
  ↓
Question candidate generation
  ↓
Priority scoring
  ↓
Human presentation
```

Do not send every sentence to the LLM.

Use batching/context windows and deterministic filtering to reduce inference load.

---

# 26. Gap Detection

The system should identify missing or ambiguous items such as:

```text
objective
population
statistical unit
reference period
geographic scope
definition
indicator
dimension
data source
calculation rule
business rule
quality rule
missing data treatment
exclusions
validation
frequency
output
constraints
assumptions
```

The framework must be configurable.

---

# 27. Question Generation

Question example:

```text
What criteria should be used to classify an establishment as active?
```

The question generator must:

- ask only when necessary
- avoid duplicate questions
- use current context
- consider existing knowledge
- prioritize high-impact gaps
- produce English questions
- keep questions concise

Question schema:

```json
{
  "question_id": "Q-2026-000001",
  "meeting_id": "M-2026-000001",
  "question": "What reference period should be used?",
  "domain": "measurement",
  "priority": 0.92,
  "reason": "The reference period is required to define the indicator.",
  "status": "candidate"
}
```

---

# 28. Meeting Journal

The journal must capture:

```text
timestamp
speaker
original statement
normalized interpretation
type
status
confidence
evidence
```

Types:

```text
requirement
definition
business_rule
decision
assumption
constraint
question
answer
unresolved_issue
```

---

# 29. Knowledge Consolidation

At meeting closure:

```text
Meeting End
     ↓
Completeness Check
     ↓
Extract Requirements
     ↓
Extract Definitions
     ↓
Extract Decisions
     ↓
Extract Rules
     ↓
Extract Constraints
     ↓
Normalize Terminology
     ↓
Compare Existing Knowledge
     ↓
Detect Conflicts
     ↓
Create Candidate Knowledge
     ↓
Approval
     ↓
Publish
```

The system must not automatically convert every AI extraction into authoritative knowledge.

---

# 30. Knowledge Status

Support:

```text
CAPTURED
EXTRACTED
NORMALIZED
VALIDATED
CANDIDATE
APPROVED
PUBLISHED
REJECTED
CONFLICTED
SUPERSEDED
```

---

# 31. Knowledge Precedence

Use:

```text
APPROVED METHODOLOGY
        >
APPROVED ORGANIZATIONAL STANDARD
        >
VALIDATED BUSINESS REQUIREMENT
        >
MEETING-DERIVED KNOWLEDGE
        >
AI INFERENCE
        >
AI HYPOTHESIS
```

When new information conflicts with higher-authority information:

```text
DO NOT OVERWRITE.
```

Create a conflict record.

---

# 32. Knowledge Object

Implement:

```json
{
  "knowledge_id": "K-2026-000001",
  "domain": "business_activity",
  "knowledge_type": "definition",
  "concept": "active_establishment",
  "statement": "An establishment is considered active when...",
  "status": "candidate",
  "scope": "business_activity_statistics",
  "confidence": 0.94,
  "source_type": "meeting",
  "source_meeting_id": "M-2026-000001",
  "evidence": [
    {
      "transcript_segment_id": "SEG-000102",
      "timestamp_start": "00:32:14",
      "timestamp_end": "00:34:52"
    }
  ],
  "validated_by": null,
  "effective_from": null,
  "supersedes": null,
  "related_concepts": []
}
```

---

# 33. Knowledge Retrieval

PostgreSQL is authoritative.

Qdrant is the semantic retrieval index.

Never make Qdrant the system of record.

Retrieval:

```text
Question
   ↓
Knowledge API
   ├── structured filters → PostgreSQL
   └── semantic search → Qdrant
              ↓
        authority filter
              ↓
        scope filter
              ↓
        version filter
              ↓
        relevant knowledge
```

---

# 34. Knowledge API

Implement:

```text
GET    /api/v1/knowledge/search
GET    /api/v1/knowledge/{id}
POST   /api/v1/knowledge/candidate
POST   /api/v1/knowledge/{id}/approve
POST   /api/v1/knowledge/{id}/reject
GET    /api/v1/knowledge/conflicts
GET    /api/v1/knowledge/domain/{domain}
```

Downstream AI agents must use this API.

They must not directly query PostgreSQL or Qdrant.

---

# 35. Other AI Agents

Design interfaces for:

```text
Planning Agent
Data Agent
Statistical Agent
Quality Agent
Documentation Agent
Review Agent
```

All agents consume shared knowledge.

Example:

```text
Documentation Agent
       ↓
Knowledge API
       ↓
Approved definitions
Approved rules
Approved decisions
Approved methodology
       ↓
Methodology document
```

---

# 36. API Design

Implement:

```text
/api/v1/auth
/api/v1/meetings
/api/v1/participants
/api/v1/transcripts
/api/v1/questions
/api/v1/methodology
/api/v1/journal
/api/v1/knowledge
/api/v1/agents
/api/v1/system
```

FastAPI should expose OpenAPI documentation.

Use Pydantic schemas.

Never accept arbitrary LLM-generated SQL.

---

# 37. WebSocket Events

Implement a meeting event channel.

Events:

```text
meeting.status
participant.joined
participant.left

transcript.partial
transcript.final
speaker.changed

methodology.updated
gap.detected

question.candidate
question.presented
question.asked
question.skipped
question.deferred

answer.detected
decision.detected

knowledge.candidate
knowledge.published

ai.status
```

Example:

```json
{
  "event": "question.candidate",
  "meeting_id": "M-2026-000001",
  "question_id": "Q-2026-000001",
  "question": "What reference period should be used?",
  "priority": 0.92
}
```

---

# 38. Frontend Requirements

Build a single integrated application.

Main layout:

```text
+-------------------------------------------------------------------+
| AI METHODOLOGY DISCOVERY SESSION                   AI: ACTIVE     |
+--------------------------------------+----------------------------+
|                                      | AI METHODOLOGY ASSISTANT |
|                                      |                            |
|            VIDEO MEETING             | Current Topic             |
|                                      |                            |
|  Participant A     Participant B     | Methodology Completeness |
|                                      | ████████░░ 78%            |
|  Participant C     Participant D     |                            |
|                                      | Potential Gap             |
|                                      | Reference Period          |
|                                      |                            |
|                                      | Suggested Question        |
|                                      |                            |
|                                      | What reference period    |
|                                      | should be used?          |
|                                      |                            |
|                                      | [ASK NOW] [SKIP]         |
|--------------------------------------+----------------------------|
| LIVE TRANSCRIPT                      | METHODOLOGY STATE         |
|                                      |                            |
| Ahmed: ...                           | Objective ✓               |
| Sara: ...                            | Population ✓              |
|                                      | Unit ✓                    |
|                                      | Reference Period ⚠        |
+--------------------------------------+----------------------------+
```

---

# 39. Frontend Components

Create:

```text
MeetingPage
VideoConference
ParticipantGrid
MeetingControls
TranscriptPanel
AIAssistantPanel
MethodologyStatePanel
QuestionCard
MeetingJournal
KnowledgeCandidates
MeetingSummary
```

The AI panel should update without refreshing the meeting.

---

# 40. Privacy UI

Show:

```text
AI ACTIVE
```

when the AI is processing meeting audio.

Allow authorized users to:

```text
Pause AI
Resume AI
Disable transcript
End AI processing
```

Recording must be separately controlled.

Default:

```text
STORE_RAW_AUDIO=false
STORE_VIDEO=false
```

---

# 41. Terminology Normalization

Create terminology tables:

```text
terminology
terminology_aliases
```

Example:

```json
{
  "source_term": "المنشأة",
  "canonical_term": "establishment",
  "language": "ar",
  "domain": "statistics",
  "status": "approved"
}
```

The system must support organization-specific terminology.

---

# 42. Security Architecture

Use least privilege.

Docker services should not run privileged unless strictly required.

Do not use:

```yaml
privileged: true
```

unless there is a documented technical necessity.

Avoid:

```yaml
network_mode: host
```

unless required by a specific Jitsi/WebRTC configuration and documented.

Do not expose:

```text
5432
6379
6333
6334
9000
9001
LLM ports
speech ports
```

to the host by default.

Use internal Docker networks.

---

# 43. Network Architecture

Use:

```text
frontend
backend
ai
```

Docker networks.

Preferred:

```text
Browser
   |
   v
Nginx
   |
   +----> Frontend
   |
   +----> Backend
              |
              +----> PostgreSQL
              +----> Redis
              +----> Qdrant
              +----> MinIO
              +----> Speech
              +----> LLM
              +----> Embeddings
```

Jitsi requires special WebRTC/media networking and must be configured according to its official deployment documentation.

---

# 44. Database Security

PostgreSQL should:

- use a dedicated application user
- not use the postgres superuser for application queries
- not be publicly exposed
- use migrations
- use parameterized queries
- log important administrative operations
- have backups

---

# 45. Qdrant Security

Do not expose Qdrant publicly.

Configure an API key.

The official Qdrant security documentation explicitly warns that unsecured instances allow clients that can reach the port to read, write, or delete data. Treat Qdrant as an internal service. [Qdrant security documentation](https://qdrant.tech/documentation/tutorials-operations/secure-qdrant/)

---

# 46. Audit Logging

Record:

```text
login
logout
meeting creation
meeting join
meeting end
transcript access
question asked
question skipped
knowledge created
knowledge approved
knowledge rejected
knowledge superseded
knowledge conflict
configuration changes
administrator actions
```

Audit records must include:

```text
timestamp
actor
action
resource
result
IP where appropriate
metadata
```

Do not put passwords or tokens into audit records.

---

# 47. Docker Image Security

Use:

```bash
docker build --pull
```

for application images.

Pin image versions.

Avoid:

```text
latest
```

in production-like deployments.

Where feasible:

- use trusted official images
- verify image provenance
- scan images
- use SBOM generation
- use non-root users
- use read-only filesystems where compatible
- drop unnecessary Linux capabilities

Do not blindly add security options that break Jitsi/WebRTC.

---

# 48. Build Commands

After repository creation:

```bash
docker version
docker compose version
docker info
```

Validate Compose:

```bash
docker compose config
```

Build application images:

```bash
docker compose build --pull
```

Build without cache when required:

```bash
docker compose build --pull --no-cache
```

---

# 49. Start Commands

Core infrastructure:

```bash
docker compose --profile core up -d
```

AI services:

```bash
docker compose --profile ai up -d
```

Full application:

```bash
docker compose --profile core --profile ai up -d
```

If the final implementation does not require profiles, provide:

```bash
docker compose up -d
```

as the primary command.

Do not use Docker Swarm for the VDI MVP.

Do not run:

```bash
docker swarm init
```

unless the user explicitly requests Swarm.

Kubernetes is a future infrastructure option, not an MVP requirement.

---

# 50. Setup Script

Create:

```bash
scripts/setup.sh
```

It must:

```text
1. verify prerequisites
2. run preflight
3. create directories
4. create .env
5. generate secrets
6. prepare certificates
7. prepare Jitsi
8. validate Compose
9. pull/build images
10. start services
11. wait for health
12. run database migrations
13. initialize Qdrant collections
14. initialize MinIO bucket
15. initialize Keycloak realm
16. print non-secret service URLs
```

Example:

```bash
set -euo pipefail

echo "Running preflight..."
./scripts/preflight.sh

echo "Creating directories..."
mkdir -p data/{postgres,qdrant,redis,minio,keycloak,jitsi,models}

echo "Validating Docker..."
docker version
docker compose version

echo "Validating Compose..."
docker compose config >/dev/null

echo "Building images..."
docker compose build --pull

echo "Starting services..."
docker compose up -d

echo "Waiting for services..."
./scripts/healthcheck.sh
```

Never print generated passwords.

---

# 51. Health Check Script

Create:

```bash
scripts/healthcheck.sh
```

Check:

```text
PostgreSQL
Redis
Qdrant
MinIO
Keycloak
Backend
Frontend
Speech
LLM
Embeddings
Jitsi
Nginx
```

Commands may include:

```bash
docker compose ps
docker compose logs --tail=50
curl -fsS https://methodology.local/health
```

Do not mark the entire system healthy if a required component is unavailable.

Distinguish:

```text
healthy
degraded
unavailable
disabled
```

---

# 52. Database Migration

Use Alembic.

Migration command:

```bash
docker compose exec backend alembic upgrade head
```

Do not run schema creation manually in application startup.

Application startup may verify schema state but must not silently mutate production schema.

---

# 53. Verification Test

After startup:

```bash
docker compose ps
```

Expected:

```text
postgres       healthy
redis          healthy
qdrant         healthy
minio          running/healthy
keycloak       healthy
backend        healthy
frontend       running
```

Then:

```bash
curl -k https://methodology.local/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

# 54. Meeting Verification

Open the application.

Create meeting:

```text
M-2026-000001
```

Open two browser sessions.

Verify:

```text
camera
microphone
participant video
participant audio
screen sharing
join/leave
```

If Jitsi fails:

```bash
docker compose -f jitsi/docker-compose.yml ps
```

Then:

```bash
docker compose -f jitsi/docker-compose.yml logs --tail=100
```

Check Jitsi's advertised IP and required UDP media connectivity.

---

# 55. Speech Verification

Use a controlled test meeting.

Test:

```text
English
Arabic
Arabic + English
technical terms
statistical terminology
acronyms
```

Verify transcript contains:

```text
speaker
language
timestamp
original text
confidence
```

Do not claim production-grade diarization accuracy until measured.

---

# 56. AI Verification

Test:

```text
Participant:
"We want a monthly indicator for active establishments."

Expected:

Objective identified:
Monthly indicator.

Statistical unit:
Potentially establishment.

Gap:
Definition of active establishment.

Candidate question:
"What criteria should be used to classify an establishment as active?"
```

The system must not invent the definition.

---

# 57. Knowledge Verification

Conduct:

```text
Meeting A
```

Establish a confirmed business rule.

Close meeting.

Approve knowledge.

Then start a separate agent/request:

```text
How is an active establishment defined?
```

The system should retrieve the knowledge from:

```text
PostgreSQL
+
Qdrant
```

and show provenance.

---

# 58. Testing Strategy

Implement:

## Unit tests

```text
methodology state
gap detection
question prioritization
knowledge lifecycle
conflict detection
terminology normalization
authorization
```

## API tests

```text
authentication
meetings
transcripts
questions
journal
knowledge
```

## Integration tests

```text
transcript
→ methodology state
→ gap
→ question
→ answer
→ knowledge
→ approval
→ retrieval
```

## AI fixture tests

Create deterministic fixtures for:

```text
Arabic
English
mixed-language
ambiguous requirement
confirmed requirement
contradiction
duplicate question
```

Mock the LLM in unit tests.

Do not require GPU inference for every test.

---

# 59. End-to-End Test

Create:

```text
tests/integration/test_end_to_end.py
```

Flow:

```text
1. authenticate
2. create meeting
3. add participant
4. submit transcript fixture
5. process signal
6. update methodology state
7. detect gap
8. generate question
9. submit answer
10. update state
11. close meeting
12. create knowledge candidate
13. approve candidate
14. index Qdrant
15. retrieve knowledge
16. verify provenance
```

---

# 60. Backup

Create:

```bash
scripts/backup.sh
```

Backup:

```text
PostgreSQL
Qdrant
MinIO
Keycloak
configuration
```

Example:

```bash
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > backups/$(date +%Y%m%d_%H%M%S)/postgres.sql
```

Also document Qdrant and MinIO backup procedures.

Do not assume filesystem copying while services are running is always a consistent database backup.

---

# 61. Restore

Create:

```bash
scripts/restore.sh
```

Require explicit confirmation:

```text
WARNING: restore will replace current data.
Type RESTORE to continue.
```

Never overwrite current data without confirmation.

Recommend taking a backup before restore.

---

# 62. Rollback

For application images:

```bash
docker compose down
```

Restore the previous image tag/configuration.

For database migrations:

- never blindly downgrade production migrations
- prefer forward migration
- restore from backup for destructive rollback

For knowledge:

- use versioning
- use `SUPERSEDED`
- never delete authoritative history merely to roll back

---

# 63. Logging

Use structured JSON logs from the application.

Every AI operation should log:

```text
meeting_id
operation
model
latency
status
```

Do not log:

```text
password
token
secret
full sensitive transcript
```

unless explicitly required for controlled debugging.

---

# 64. Observability

Include:

```text
Prometheus
Grafana
```

Monitor:

```text
CPU
RAM
GPU
ASR latency
LLM latency
transcript delay
WebSocket connections
active meetings
question generation latency
database connections
Qdrant status
service health
errors
```

Monitoring should be optional on low-resource VDIs.

---

# 65. CI/CD

CI/CD is optional for the first local implementation but scaffold it.

Create:

```text
.github/workflows/build.yml
```

Example:

```yaml
name: Build and Test

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend dependencies
        working-directory: backend
        run: pip install -r requirements.txt

      - name: Run backend tests
        run: pytest tests/backend -q

      - name: Validate Compose
        run: docker compose config

      - name: Build application images
        run: docker compose build --pull
```

Do not assume GitHub Actions can deploy directly into a corporate VDI.

For local deployment, provide a local runner option or simple:

```bash
git pull
docker compose build --pull
docker compose up -d
```

Do not expose the VDI Docker daemon publicly.

---

# 66. Optional Local Deployment Script

Create:

```bash
scripts/deploy.sh
```

Example:

```bash
#!/usr/bin/env bash

set -euo pipefail

git pull --ff-only

docker compose config >/dev/null

docker compose build --pull

docker compose up -d

./scripts/healthcheck.sh
```

Do not automatically run destructive migrations.

---

# 67. Troubleshooting

## Docker unavailable

Run:

```bash
docker info
```

If it fails:

- start Docker Desktop or Docker Engine
- verify WSL2 if using Windows
- retry

## Compose unavailable

Run:

```bash
docker compose version
```

Install/update Docker Compose V2.

Do not use legacy `docker-compose` unless required.

## Port already in use

Run:

```bash
docker ps
```

Windows:

```powershell
Get-NetTCPConnection -LocalPort 443
```

Linux:

```bash
ss -ltnp | grep ':443'
```

Change application port only after checking the implications for Jitsi/WebRTC.

## Jitsi microphone/camera failure

Check:

```text
HTTPS
browser permissions
Jitsi HTTPS configuration
JVB advertised IP
UDP 10000
corporate firewall
```

Jitsi documentation specifically warns that direct HTTP access can cause browser microphone/camera failures. Use HTTPS. [Jitsi Docker guide](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/)

## Jitsi works locally but not from another machine

Check:

```text
VDI network reachability
DNS/hosts file
firewall
JVB_ADVERTISE_IPS
UDP 10000
TLS certificate trust
```

## Qdrant unavailable

Run:

```bash
docker compose logs qdrant
```

Then:

```bash
docker compose ps qdrant
```

Verify its internal URL:

```text
http://qdrant:6333
```

Do not use `localhost` between containers.

## Qdrant permission problems on Windows/WSL

Prefer a Docker named volume if bind mounts cause filesystem/permission problems. Qdrant's documentation specifically notes filesystem issues with Docker/WSL mounts on Windows. [Qdrant installation documentation](https://qdrant.tech/documentation/installation/)

## PostgreSQL unavailable

Run:

```bash
docker compose logs postgres
```

Check:

```bash
docker compose exec postgres pg_isready
```

## LLM out of memory

Reduce:

```text
model size
context length
batch size
concurrency
```

or switch to CPU/smaller-model profile.

Do not redesign the application.

## ASR too slow

Reduce model size.

Disable diarization temporarily.

Use GPU if available.

Increase chunk size only after measuring latency.

## VDI disk fills up

Run:

```bash
docker system df
```

Inspect:

```bash
docker system df -v
```

Remove only known-unused resources.

Do not run destructive prune commands automatically.

---

# 68. Docker Cleanup

Safe inspection:

```bash
docker system df
```

List unused images:

```bash
docker images
```

Never automatically execute:

```bash
docker system prune -a
```

because it can remove useful images and development resources.

If cleanup is necessary, explain exactly what will be removed first.

---

# 69. Development Profiles

Support:

```text
core
ai
monitoring
```

Example:

```bash
docker compose --profile core up -d
```

```bash
docker compose --profile core --profile ai up -d
```

```bash
docker compose --profile core --profile ai --profile monitoring up -d
```

A minimal VDI profile should be possible without Grafana/Prometheus.

---

# 70. GPU Compose Override

Create:

```text
docker-compose.gpu.yml
```

Expose GPU only to:

```text
speech
llm
embeddings
```

Do not expose GPU to:

```text
postgres
redis
qdrant
minio
frontend
keycloak
nginx
```

Use the appropriate NVIDIA container runtime configuration for the installed Docker environment.

Verify with:

```bash
docker run --rm --gpus all nvidia/cuda:<verified-tag> nvidia-smi
```

Only use an image/tag verified against the installed driver.

---

# 71. Air-Gapped Future

Design the system so model images and Docker images can be exported.

Example:

```bash
docker save -o ai-methodology-images.tar <image1> <image2>
```

On the target environment:

```bash
docker load -i ai-methodology-images.tar
```

Model files must be stored under:

```text
data/models/
```

and configurable without modifying application source code.

---

# 72. No Cloud Leakage

The coding agent must inspect dependencies and configuration for accidental external calls.

Search for:

```text
api.openai.com
anthropic.com
googleapis.com
amazonaws.com
azure.com
```

and similar external AI endpoints.

No runtime AI request should leave the internal environment.

If a dependency performs telemetry, disable it where technically and legally appropriate.

---

# 73. Resource Management

Because the target is a VDI, prioritize:

```text
stability
predictability
low idle resource usage
```

Do not run every optional service by default.

Recommended MVP:

```text
frontend
backend
postgres
redis
qdrant
keycloak
jitsi
speech
llm
```

Add:

```text
minio
prometheus
grafana
```

when required.

---

# 74. Architecture Decision: No Kafka in MVP

Do not introduce Kafka initially.

Use:

```text
FastAPI
Redis
PostgreSQL
WebSockets
background workers
```

Design event interfaces so Kafka can be introduced later.

Future event topics:

```text
audio.transcript
conversation.events
methodology.signals
question.candidates
question.asked
meeting.decisions
knowledge.candidates
knowledge.published
```

---

# 75. Architecture Decision: No Kubernetes in MVP

Do not deploy Kubernetes on the VDI.

Docker Compose is sufficient for the initial environment.

The code should remain container-friendly so that later deployment to:

```text
Kubernetes
OpenShift
internal VM cluster
```

is possible.

---

# 76. Required Documentation

Create:

```text
README.md
QUICKSTART.md
ARCHITECTURE.md
SECURITY.md
TROUBLESHOOTING.md
API.md
AI_AGENTS.md
DEPLOYMENT.md
```

README must include:

```text
purpose
requirements
VDI sizing
installation
startup
shutdown
health
URLs
logs
GPU
AI models
backup
restore
troubleshooting
```

---

# 77. Required Makefile

Create:

```makefile
setup:
	./scripts/setup.sh

preflight:
	./scripts/preflight.sh

build:
	docker compose build --pull

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs --tail=200 -f

health:
	./scripts/healthcheck.sh

test:
	pytest -q

backup:
	./scripts/backup.sh

restore:
	./scripts/restore.sh
```

Add Windows alternatives in documentation.

---

# 78. Development Workflow

The coding agent must follow:

```text
Inspect
 ↓
Preflight
 ↓
Implement infrastructure
 ↓
Validate Compose
 ↓
Build
 ↓
Start
 ↓
Health check
 ↓
Implement backend
 ↓
Test
 ↓
Implement frontend
 ↓
Test
 ↓
Integrate Jitsi
 ↓
Test audio/video
 ↓
Implement speech
 ↓
Test Arabic/English
 ↓
Implement AI
 ↓
Test questions
 ↓
Implement knowledge
 ↓
Test retrieval
 ↓
Run end-to-end test
 ↓
Document
```

Do not implement the entire platform in one untested pass.

---

# 79. Coding Standards

Backend:

```text
Python
type hints
Pydantic
async where appropriate
SQLAlchemy
Alembic
pytest
ruff
```

Frontend:

```text
TypeScript
React
ESLint
Prettier
Vitest
```

Use clear service boundaries.

Avoid unnecessary abstractions.

Do not create dozens of microservices for simple CRUD functions.

---

# 80. Definition of Done

The infrastructure MVP is complete only when:

```text
[ ] Docker installed and validated
[ ] Docker Compose validated
[ ] VDI preflight works
[ ] Secrets generated securely
[ ] Compose configuration validates
[ ] PostgreSQL healthy
[ ] Redis healthy
[ ] Qdrant healthy
[ ] Keycloak healthy
[ ] Frontend starts
[ ] Backend starts
[ ] Jitsi starts
[ ] HTTPS works
[ ] Two users can join a meeting
[ ] Camera works
[ ] Microphone works
[ ] Screen sharing works
[ ] Live transcript works
[ ] Arabic transcription works
[ ] English transcription works
[ ] Mixed-language processing works
[ ] Methodology state updates
[ ] Gaps are detected
[ ] English questions are generated
[ ] Questions can be asked/skipped
[ ] Meeting journal is created
[ ] Meeting closure works
[ ] Knowledge candidate is generated
[ ] Knowledge approval works
[ ] Knowledge is stored in PostgreSQL
[ ] Knowledge is indexed in Qdrant
[ ] Knowledge retrieval works
[ ] Provenance works
[ ] RBAC works
[ ] Audit logging works
[ ] Backup works
[ ] Restore is documented/tested
[ ] Health checks work
[ ] Integration tests pass
[ ] No runtime cloud AI dependency exists
```

---

# 81. Required Final Coding-Agent Report

At the end of implementation, produce a concise report containing:

```text
1. What was implemented
2. Docker services
3. Docker images and versions
4. Model names and sizes
5. VDI resources detected
6. GPU status
7. URLs
8. Ports
9. Database schema status
10. Tests executed
11. Test results
12. Known limitations
13. Security considerations
14. Backup location/procedure
15. How to stop/start the system
16. Recommended next development step
```

Never include secret values in this report.

---

# 82. Final Deliverables Checklist

The coding agent must deliver:

- [ ] Docker Compose infrastructure
- [ ] VDI preflight scripts
- [ ] Setup scripts
- [ ] Windows PowerShell support
- [ ] Backend Dockerfile
- [ ] Frontend Dockerfile
- [ ] Speech Dockerfile
- [ ] GPU Compose override
- [ ] `.env.example`
- [ ] Secret generation
- [ ] PostgreSQL migrations
- [ ] Qdrant integration
- [ ] Redis integration
- [ ] MinIO integration
- [ ] Keycloak integration
- [ ] Jitsi self-hosted integration
- [ ] HTTPS configuration
- [ ] React meeting interface
- [ ] AI assistant interface
- [ ] WebSocket infrastructure
- [ ] ASR pipeline
- [ ] Arabic/English handling
- [ ] Methodology state engine
- [ ] Gap detection
- [ ] Question generation
- [ ] Meeting journal
- [ ] Knowledge consolidation
- [ ] Knowledge lifecycle
- [ ] Knowledge provenance
- [ ] Conflict detection
- [ ] Knowledge retrieval
- [ ] Downstream agent API
- [ ] RBAC
- [ ] Audit logging
- [ ] Monitoring
- [ ] Backup
- [ ] Restore
- [ ] Unit tests
- [ ] Integration tests
- [ ] End-to-end test
- [ ] README
- [ ] Quickstart
- [ ] Architecture documentation
- [ ] Security documentation
- [ ] Troubleshooting guide
- [ ] CI scaffold

---

# 83. Expected Outcome

**The final outcome must be a fully self-hosted Docker-based audio/video methodology meeting platform running on the user's VDI, where live Arabic/English conversation is converted into structured methodology intelligence, targeted English questions, a traceable meeting journal, and reusable organizational knowledge for future AI agents—without requiring cloud AI services at runtime.**
