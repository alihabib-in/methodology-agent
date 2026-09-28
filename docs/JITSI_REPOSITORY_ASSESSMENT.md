# Jitsi Repository Assessment

Pre-deployment inspection of the existing `methodology-agent` repository.

## 1. Existing architecture

Backend-only FastAPI service (`app/`) with these phases already complete:

- LLM service (`llama.cpp` + Qwen3-4B, GPU) — Phase 1
- Methodology agent (extraction, gap detection, question generation) — Phases 2–5
- ASR transcript ingestion (`faster-whisper` + `run_audio_test.py`) — Phase 6
- RAG + persistence (`PostgreSQL`, `Qdrant`, embedding service) — Phase 7
- Meeting/session + knowledge lifecycle (in the methodology sense) — Phase 7

There is **no** React frontend, **no** reverse proxy/TLS, **no** Keycloak/Redis/MinIO,
and **no** `git` repository in the working copy.

## 2. Existing network

Single Docker Compose project `methodology-agent` with one default network.
Services: `api` (8000), `embedding` (8001), `llm` (8080), `postgres` (5432),
`qdrant` (6333/6334).

## 3. Existing reverse proxy

None. The methodology API is exposed directly on `127.0.0.1:8000`.

## 4. Existing authentication

None at the transport level. The backend is authoritative for methodology
sessions and knowledge approval (human-in-the-loop via API endpoints).

## 5. DNS / hostname approach

No hostname convention yet. `localhost`/`127.0.0.1` used everywhere.

## 6. Port conflicts

| Port | Existing service |
|---|---|
| 8000 | methodology-api |
| 8001 | embedding service |
| 8080 | llama.cpp LLM |
| 5432 | PostgreSQL |
| 6333/6334 | Qdrant |

Jitsi ports chosen to avoid these: HTTP 8880, HTTPS 8443, JVB UDP 10000,
JVB colibri 9080 (localhost), Jicofo REST 8888 (localhost).

## 7. Required Jitsi components

`web` (nginx + UI), `prosody` (XMPP), `jicofo` (focus), `jvb` (videobridge).
No Jibri/Jigasi (recording/SIP) for the first prototype.

## 8. Integration approach

- Jitsi runs as a **separate compose stack** (`jitsi/docker-compose.yml`) with its
  own network `jitsi_meet.jitsi`, isolated from the methodology stack.
- The FastAPI backend gains a `MeetingService` + `JitsiAdapter` (room naming,
  URL, JWT tokens) with a new `meeting_sessions` table.
- A React frontend (`frontend/`) embeds Jitsi via the IFrame API.

## 9. Risks

- **WebRTC UDP** through Docker Desktop (WSL2) + corporate VDI/NAT — the single
  biggest risk; cannot be verified headlessly.
- Self-signed cert requires manual browser trust.
- `ghcr.io/jitsi/*:unstable` tags are rolling (not pinned) — pin for production.

## 10. Recommended implementation

Deploy Jitsi (web/prosody/jicofo/jvb) with self-signed HTTPS, document local DNS,
add the backend meeting service/adapter/API, and a minimal React IFrame host.
