# Jitsi Meet Self-Hosted Deployment — Coding Agent Implementation Prompt

## Role

You are a senior DevOps/platform engineer responsible for deploying and integrating **self-hosted Jitsi Meet** into an existing Docker-based AI Methodology Platform.

Your task is to deploy a **fully local, production-structured Jitsi Meet environment** that can later be integrated with the existing SCAD Methodology Agent.

The environment is currently running on a **local VDI/developer machine**, not a production server.

The solution must therefore:

- run locally using Docker Compose
- use open-source/self-hosted components
- require no cloud service
- require no external AI service
- preserve the existing Phase 1–6 infrastructure
- avoid unnecessary architectural changes
- be portable later to SCAD internal/on-prem infrastructure

---

# 1. IMPORTANT: INSPECT BEFORE MODIFYING

Do NOT immediately create files or replace the existing Docker configuration.

First inspect the repository.

Run:

```bash
git status
find . -maxdepth 3 -type f | sort
docker compose ps
docker compose config
```

Inspect:

```text
docker-compose.yml
compose.yaml
.env
.env.example
README.md
docs/
backend/
frontend/
scripts/
```

Identify:

- existing Docker network(s)
- reverse proxy
- TLS configuration
- frontend
- backend
- PostgreSQL
- Qdrant
- Redis
- MinIO
- Keycloak
- existing ports
- existing hostnames
- existing health checks
- existing volume strategy
- existing authentication architecture

DO NOT duplicate services that already exist.

Before implementation, create:

```text
docs/JITSI_REPOSITORY_ASSESSMENT.md
```

Document:

1. Existing architecture
2. Existing network
3. Existing reverse proxy
4. Existing authentication
5. Existing DNS/hostname approach
6. Port conflicts
7. Required Jitsi components
8. Integration approach
9. Risks
10. Recommended implementation

---

# 2. OBJECTIVE

Deploy:

```text
Self-hosted Jitsi Meet
```

inside the existing Docker environment.

Target architecture:

```text
                   Browser
                      │
                      │ HTTPS
                      ▼
              Reverse Proxy / TLS
                 ┌────┴─────┐
                 │          │
                 ▼          ▼
          Methodology    Jitsi Meet
             UI             │
                            │
                  ┌─────────┼─────────┐
                  │         │         │
                  ▼         ▼         ▼
               Prosody    Jicofo    JVB
```

Jitsi should remain a **meeting/AV subsystem**.

It must NOT contain:

- methodology logic
- RAG logic
- PostgreSQL methodology state
- knowledge management
- approval workflow
- LLM logic

Those remain in the existing platform.

---

# 3. JITSI COMPONENTS

Use the official self-hosted Jitsi Docker distribution and current compatible images/configuration.

The deployment normally includes:

```text
web
prosody
jicofo
jvb
```

Add other components only if required by the chosen current Jitsi deployment.

Do not invent custom replacements for Jitsi's standard components.

Use the official Jitsi Docker repository/documentation as the implementation reference.

Official references:

https://github.com/jitsi/docker-jitsi-meet

https://jitsi.github.io/handbook/docs/intro/

https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe/

Verify current configuration requirements rather than relying on outdated examples.

---

# 4. DOCKER REQUIREMENT

Jitsi must run through Docker Compose.

Do NOT use:

```text
docker swarm
Kubernetes
cloud-managed services
```

Do not require Docker Swarm.

The normal startup must remain:

```bash
docker compose up -d
```

The existing platform must continue to work.

---

# 5. NETWORK ARCHITECTURE

Inspect the existing Docker networks.

Prefer integration with the existing application network where appropriate.

However, isolate Jitsi internal traffic where practical.

Conceptually:

```text
                     Reverse Proxy
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
           Application             Jitsi
                │                   │
                │             ┌─────┴─────┐
                │             │           │
                │          Prosody       JVB
                │             │
                │            Jicofo
                │
          PostgreSQL
          Qdrant
```

Do not expose PostgreSQL or Qdrant to the browser.

---

# 6. HOSTNAME

Use a configurable hostname.

Example development hostname:

```text
meet.scad.local
```

Do NOT hard-code `localhost` throughout the application.

Create configuration such as:

```env
JITSI_DOMAIN=meet.scad.local
JITSI_HTTP_PORT=8000
JITSI_HTTPS_PORT=8443
```

Use the actual ports required by the existing environment.

If the project already has a domain convention, reuse it.

---

# 7. LOCAL DNS

The development environment must be able to resolve:

```text
meet.scad.local
```

to the VDI/local host.

If corporate DNS is unavailable, document a development-only hosts-file approach.

For example:

```text
127.0.0.1 meet.scad.local
```

Do not require this to be manually edited without documenting it.

Create:

```text
docs/JITSI_LOCAL_DNS.md
```

Explain:

- hostname
- DNS resolution
- development hosts-file option
- eventual corporate DNS requirement

---

# 8. HTTPS / TLS

Jitsi should be accessible over HTTPS.

Do not design the final architecture around plain HTTP.

Use the existing reverse proxy/TLS architecture if one already exists.

For local development, a self-signed/internal CA certificate is acceptable.

Document:

```text
certificate generation
certificate location
certificate trust
browser trust requirements
certificate renewal
```

Do not commit private keys to Git.

---

# 9. PORT MANAGEMENT

Before deploying, inspect current ports:

```bash
docker compose ps
docker ps
```

Identify conflicts.

Jitsi requires both HTTP-level services and WebRTC media connectivity.

Do not blindly assign ports.

Document all exposed ports.

In particular, verify Jitsi Videobridge UDP connectivity.

The final documentation must clearly identify:

```text
HTTP/HTTPS
JVB UDP media port
JVB TCP fallback if configured
```

---

# 10. WEBRTC NETWORKING

This is a critical requirement.

Do not consider the deployment successful merely because:

```text
https://meet.scad.local
```

opens.

Verify actual:

```text
browser
 ↓
Jitsi
 ↓
Jitsi Videobridge
 ↓
browser
```

media connectivity.

Test:

- microphone
- speaker
- camera
- video
- two participants
- screen sharing
- participant join/leave
- network connectivity
- UDP media
- TCP fallback where configured

Check browser developer tools and Jitsi logs if media fails.

---

# 11. JVB CONFIGURATION

Configure Jitsi Videobridge correctly for the local VDI environment.

Do not assume Docker's internal IP is the address that browsers should use for media.

Determine the appropriate:

```text
public/local advertised address
```

for the development environment.

Document the difference between:

```text
Docker container IP
host IP
browser-accessible IP
JVB advertised address
```

This is especially important when the VDI is accessed from another machine.

---

# 12. VDI ACCESS

The system must work in the actual VDI development scenario.

Test at least:

### Test A

Browser running inside the VDI:

```text
Browser
 ↓
meet.scad.local
```

### Test B

If supported by the corporate network:

```text
Second client
 ↓
VDI host/network
 ↓
Jitsi
```

Do not claim remote functionality unless actually tested.

If remote WebRTC is impossible because of VDI/network restrictions, document the exact limitation and configure the architecture so it can later work on an internal server.

---

# 13. JITSI AUTHENTICATION

Do not leave the deployment as an unrestricted public meeting system.

Determine the most appropriate authentication mechanism supported by the selected Jitsi version.

The application architecture should eventually support:

```text
User
 ↓
SCAD Application Authentication
 ↓
Authorized Methodology Session
 ↓
Jitsi Meeting
```

Important:

Jitsi room membership must NOT be the source of truth for SCAD application authorization.

The FastAPI backend remains authoritative for:

- session access
- methodology permissions
- approval permissions
- knowledge permissions

---

# 14. ROOM CREATION

Do not generate arbitrary room names from user input.

Create a controlled room naming strategy.

Example:

```text
SCAD-M-2026-000001
```

or:

```text
methodology-{UUID}
```

The room name must be associated with:

```text
methodology_session_id
```

in PostgreSQL.

Never rely on the Jitsi room name alone as the methodology session identifier.

---

# 15. DATABASE INTEGRATION

If the existing schema supports meeting sessions, extend it.

Otherwise create a table conceptually similar to:

```text
meeting_sessions
```

Recommended:

```text
id
session_id
jitsi_room_name
meeting_title
created_by
status
created_at
started_at
ended_at
```

Relationship:

```text
Jitsi Meeting
     │
     ▼
meeting_session
     │
     ▼
methodology_session
```

Do not store Jitsi configuration secrets in PostgreSQL.

---

# 16. BACKEND MEETING SERVICE

Create or extend:

```text
backend/meeting/
```

Suggested structure:

```text
backend/
└── meeting/
    ├── __init__.py
    ├── service.py
    ├── schemas.py
    ├── models.py
    └── jitsi/
        ├── adapter.py
        ├── events.py
        └── config.py
```

Adapt to the existing repository structure.

The meeting service should abstract Jitsi.

For example:

```python
class MeetingService:
    async def create_meeting(...):
        ...

    async def start_meeting(...):
        ...

    async def end_meeting(...):
        ...
```

The rest of the application should not depend directly on Jitsi implementation details.

---

# 17. JITSI ADAPTER

Create an adapter:

```python
class JitsiAdapter:
    def create_room(...):
        ...

    def get_room(...):
        ...

    def validate_room(...):
        ...
```

Do not expose Jitsi-specific details throughout the methodology code.

This allows a future replacement with:

```text
Microsoft Teams
Webex
custom WebRTC
another meeting system
```

without rewriting the methodology platform.

---

# 18. FRONTEND INTEGRATION

Use the Jitsi IFrame API for the first prototype.

Do not build a custom WebRTC client.

Conceptually:

```text
React Application
┌─────────────────────────────────────┐
│                                     │
│  Jitsi Meeting                      │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  │         Jitsi IFrame          │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  Methodology Assistant              │
│  ┌───────────────────────────────┐  │
│  │ Current Question              │  │
│  │                               │  │
│  │ [ Ask ] [ Skip ] [ Defer ]   │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

Use the existing React architecture.

Do not create a second frontend application.

---

# 19. JITSI IFRAME COMPONENT

Create something conceptually similar to:

```text
JitsiMeeting.tsx
```

Responsibilities:

- initialize Jitsi
- pass room name
- configure display name
- configure audio/video defaults
- listen to meeting lifecycle events
- destroy meeting cleanly
- report events to backend/application

Do not put methodology business logic inside this component.

---

# 20. FRONTEND EVENT HANDLING

The Jitsi component may expose normalized events such as:

```text
meeting.ready
meeting.joined
participant.joined
participant.left
meeting.left
meeting.ended
```

These should be translated into application events.

Do not make the methodology agent dependent on raw Jitsi JavaScript events.

---

# 21. MEETING LIFECYCLE

Implement:

```text
CREATED
   ↓
READY
   ↓
LIVE
   ↓
ENDED
   ↓
PROCESSING
   ↓
COMPLETED
```

For the initial prototype:

```text
CREATED
READY
LIVE
ENDED
```

is sufficient if the repository does not yet have post-processing.

The lifecycle must be persisted.

---

# 22. APPLICATION API

Create or extend APIs such as:

```http
POST /api/v1/meetings
GET /api/v1/meetings/{id}
POST /api/v1/meetings/{id}/start
POST /api/v1/meetings/{id}/end
```

Response example:

```json
{
  "meeting_id": "uuid",
  "session_id": "uuid",
  "jitsi_room_name": "SCAD-M-2026-000001",
  "jitsi_url": "https://meet.scad.local/SCAD-M-2026-000001",
  "status": "ready"
}
```

Do not expose unnecessary Jitsi internals.

---

# 23. JITSI URL

The frontend should receive the Jitsi meeting URL from configuration/API.

Do not hard-code:

```text
https://meet.scad.local
```

in multiple components.

Use:

```env
JITSI_BASE_URL=https://meet.scad.local
```

or the existing configuration system.

---

# 24. SECURITY

Implement:

- authenticated application users
- session authorization
- controlled room creation
- secure configuration
- TLS
- no secrets in Git
- no credentials in frontend source
- backend validation
- audit logging

Do not expose:

```text
PostgreSQL
Qdrant
Redis
internal LLM endpoints
```

to the browser.

---

# 25. JITSI SECRETS

Inspect the official Jitsi Docker configuration for required secrets.

Generate secure development secrets.

Do not use obvious values such as:

```text
password
secret
admin
123456
```

Do not commit `.env` containing secrets.

Provide:

```text
.env.example
```

with placeholders.

---

# 26. HEALTH CHECKS

Implement/verify health checks for:

```text
Jitsi Web
Prosody
Jicofo
JVB
```

Use:

```bash
docker compose ps
```

and service-specific health endpoints/logs as appropriate.

The final documentation should include:

```bash
docker compose ps
docker compose logs --tail=100 jitsi-web
docker compose logs --tail=100 prosody
docker compose logs --tail=100 jicofo
docker compose logs --tail=100 jvb
```

Use actual service names from the deployment.

---

# 27. LOGGING

Do not log:

- passwords
- tokens
- authentication secrets
- private meeting content unnecessarily

Useful logs include:

```text
meeting_id
session_id
room_name
meeting lifecycle event
participant count
Jitsi service health
media connection errors
```

---

# 28. DATA PRIVACY

The eventual platform will handle corporate meeting content.

Design for privacy from the beginning.

Clearly distinguish:

```text
Meeting metadata
Transcript
Audio recording
Video recording
Methodology state
Knowledge
Audit records
```

Do not automatically retain audio/video forever.

Make retention configurable.

Example:

```env
MEETING_RECORDING_ENABLED=false
MEETING_TRANSCRIPT_ENABLED=true
MEETING_RETENTION_DAYS=30
```

Use equivalent existing configuration if already present.

---

# 29. RECORDING

For the first prototype, recording should NOT be required for Jitsi integration to be considered complete.

First prove:

```text
live meeting
audio
video
participants
```

Then integrate recording/transcription separately.

Do not make the methodology platform dependent on recording.

---

# 30. AUDIO ARCHITECTURE

This is important for the next phase.

Do NOT assume that embedding Jitsi automatically provides an easy server-side audio stream to the methodology agent.

Document the selected strategy for:

```text
Jitsi audio
 ↓
speech acquisition
 ↓
VAD
 ↓
Whisper
 ↓
transcript events
```

Possible strategies should be evaluated based on the current Jitsi deployment.

The coding agent must document:

1. selected approach
2. why it was selected
3. limitations
4. how speaker attribution works
5. how it can be replaced later

Do not implement brittle browser audio scraping.

---

# 31. Transcript Contract

Prepare an internal contract for the next phase.

Example:

```json
{
  "event_type": "transcript_segment",
  "meeting_id": "M-001",
  "session_id": "S-001",
  "speaker_id": "participant-17",
  "timestamp_start": "00:32:14.120",
  "timestamp_end": "00:32:18.600",
  "language": "ar",
  "text": "نريد مؤشر شهري عن المنشآت النشطة",
  "confidence": 0.94
}
```

The Jitsi implementation should not directly call the methodology LLM.

---

# 32. Methodology Agent Boundary

The final architecture must remain:

```text
Jitsi
  ↓
Meeting Adapter
  ↓
Audio/Transcript Layer
  ↓
Methodology Agent
  ↓
PostgreSQL / Qdrant
```

NOT:

```text
Jitsi
  ↓
LLM
  ↓
Database
```

---

# 33. Methodology UI Integration

The main application should eventually look like:

```text
┌────────────────────────────────────────────────────────┐
│ SCAD Methodology Session                               │
├────────────────────────────────────────────────────────┤
│                                                        │
│                 JITSI MEETING                         │
│                                                        │
│       Participant       Participant                    │
│                                                        │
├────────────────────────────────────────────────────────┤
│ METHODOLOGY AGENT                                      │
│                                                        │
│ Current understanding                                  │
│ • Population: Establishments                           │
│ • Frequency: Monthly                                   │
│ • Definition: Pending                                  │
│                                                        │
│ Suggested Question                                     │
│ "How should an active establishment be defined?"       │
│                                                        │
│ [ ASK QUESTION ] [ SKIP ] [ DEFER ]                    │
│                                                        │
├────────────────────────────────────────────────────────┤
│ LIVE JOURNAL                                           │
└────────────────────────────────────────────────────────┘
```

Do not attempt to redesign Jitsi's internal interface.

---

# 34. DO NOT IMPLEMENT AUTOMATIC AI INTERRUPTION

For this prototype:

```text
Agent generates question
        ↓
Human reviews question
        ↓
Human clicks ASK
```

Do not implement AI voice interruption.

This will be a future feature.

---

# 35. Meeting Event Storage

Persist key lifecycle events.

Example:

```text
meeting.created
meeting.ready
meeting.started
participant.joined
participant.left
meeting.ended
```

Use the existing audit/event infrastructure if available.

---

# 36. Testing

Create:

```text
tests/integration/test_jitsi_meeting.py
```

and appropriate frontend tests.

At minimum test:

### Test 1 — Create

```text
POST /meetings
```

Assert:

- meeting created
- methodology session associated
- Jitsi room generated

### Test 2 — Join

Assert:

- Jitsi URL generated correctly
- frontend can load Jitsi

### Test 3 — Lifecycle

```text
created
 ↓
ready
 ↓
started
 ↓
ended
```

Assert PostgreSQL state.

### Test 4 — Two participants

Actually test:

```text
Browser A
Browser B
```

Both can join.

### Test 5 — Audio

Verify audio.

### Test 6 — Video

Verify video.

### Test 7 — Screen sharing

Verify screen sharing.

---

# 37. WebRTC Troubleshooting Test

If meeting loads but media does not work:

Check:

```bash
docker compose logs jvb
```

and browser console.

Verify:

```text
JVB advertised address
UDP connectivity
firewall
TLS
NAT
corporate network
```

Do not incorrectly conclude that Jitsi is functional simply because the web page loads.

---

# 38. Automated Smoke Test

Create:

```text
scripts/test_jitsi.sh
```

It should check:

```text
Jitsi web reachable
Prosody healthy
Jicofo healthy
JVB healthy
HTTPS reachable
application can create meeting
meeting URL generated
```

It should return non-zero on failure.

---

# 39. Manual Acceptance Test

Create:

```text
docs/JITSI_ACCEPTANCE_TEST.md
```

Include:

```text
1. Open methodology application
2. Create meeting
3. Join Jitsi
4. Verify microphone
5. Verify camera
6. Join with second participant
7. Verify participant visibility
8. Verify audio
9. Verify video
10. Verify screen sharing
11. Leave meeting
12. Verify backend meeting status
```

---

# 40. Documentation

Create/update:

```text
docs/JITSI_DEPLOYMENT.md
docs/JITSI_ARCHITECTURE.md
docs/JITSI_LOCAL_DNS.md
docs/JITSI_TROUBLESHOOTING.md
docs/JITSI_ACCEPTANCE_TEST.md
```

Document:

- architecture
- Docker services
- configuration
- environment variables
- DNS
- TLS
- ports
- WebRTC
- authentication
- room creation
- frontend integration
- backend integration
- troubleshooting
- limitations

---

# 41. Do Not Break Existing Services

After implementation run:

```bash
docker compose config
docker compose up -d
docker compose ps
```

Then verify:

```text
Frontend
Backend
PostgreSQL
Qdrant
Redis
MinIO
Keycloak
Jitsi
```

where applicable.

The introduction of Jitsi must not break:

- existing APIs
- PostgreSQL
- Qdrant
- RAG
- frontend
- authentication

---

# 42. Existing Data Must Survive

Do not:

```text
docker compose down -v
```

unless explicitly instructed and only after confirming it is safe.

Do not delete existing volumes.

Do not reset PostgreSQL.

Do not recreate Qdrant data unnecessarily.

---

# 43. Backup Before Changes

Before modifying infrastructure:

```bash
docker compose ps
```

Identify existing volumes.

Use the repository's existing backup procedure.

If no backup procedure exists, document a safe backup before making destructive changes.

---

# 44. Git Discipline

Before changes:

```bash
git status
```

Create a branch if appropriate:

```bash
git checkout -b feature/jitsi-deployment
```

Suggested commits:

```text
feat: add self-hosted jitsi deployment
feat: integrate jitsi with methodology meetings
feat: add jitsi meeting lifecycle
feat: add jitsi iframe integration
test: add jitsi health and meeting smoke tests
docs: document jitsi deployment
```

Never commit secrets.

---

# 45. Definition of Done

Jitsi deployment is complete only when:

- [ ] repository inspected
- [ ] existing architecture documented
- [ ] Jitsi deployed using Docker Compose
- [ ] Prosody running
- [ ] Jicofo running
- [ ] JVB running
- [ ] Jitsi web running
- [ ] hostname configured
- [ ] HTTPS working
- [ ] local DNS documented
- [ ] no port conflicts
- [ ] JVB networking verified
- [ ] browser can open meeting
- [ ] microphone works
- [ ] camera works
- [ ] two participants can join
- [ ] participant events work
- [ ] screen sharing works
- [ ] application can create meeting
- [ ] Jitsi room linked to methodology session
- [ ] meeting lifecycle persisted
- [ ] React Jitsi integration works
- [ ] backend abstraction exists
- [ ] Jitsi-specific details isolated behind adapter
- [ ] secrets protected
- [ ] PostgreSQL/Qdrant remain internal
- [ ] existing Phase 1–6 functionality remains operational
- [ ] smoke test passes
- [ ] acceptance test passes
- [ ] documentation completed

---

# 46. Final Architecture Acceptance Test

The final prototype should demonstrate:

```text
SCAD Methodology Application
            │
            ▼
      Create Meeting
            │
            ▼
       Jitsi Room
            │
            ▼
      Multiple Users
            │
       ┌────┴────┐
       │         │
      Audio     Video
       │         │
       └────┬────┘
            ▼
       Meeting Layer
            │
            ▼
     Transcript Layer
            │
            ▼
   Methodology Agent
            │
     ┌──────┴──────┐
     ▼             ▼
PostgreSQL       Qdrant
```

The Jitsi deployment itself should remain independent of the methodology intelligence.

---

# 47. Final Report

At completion create:

```text
docs/JITSI_FINAL_IMPLEMENTATION_REPORT.md
```

Include:

1. Existing architecture discovered
2. Jitsi architecture implemented
3. Docker services added/changed
4. Network configuration
5. Ports
6. DNS
7. TLS
8. Authentication
9. Room creation
10. Backend integration
11. Frontend integration
12. WebRTC configuration
13. Audio strategy
14. Tests performed
15. Test results
16. Known limitations
17. Recommended next step for speech/ASR integration

Include actual commands used and actual service names.

---

# 48. Most Important Constraint

Do not over-engineer this implementation.

The objective is NOT to build the final enterprise meeting platform yet.

The immediate objective is:

> **Deploy a reliable self-hosted Jitsi Meet environment on the existing local Docker infrastructure, integrate it cleanly into the React/FastAPI application, associate each meeting with a methodology session, verify real audio/video communication, and establish clean interfaces for the subsequent speech-to-text and methodology-agent integration.**

Once this is working, the next development stage can connect:

```text
Jitsi
 ↓
Audio
 ↓
faster-whisper
 ↓
Transcript Events
 ↓
Methodology Agent
 ↓
Answer Loop
 ↓
Human Approval
 ↓
PostgreSQL
 ↓
Qdrant
```

Do not implement that entire chain as part of the Jitsi deployment unless the existing repository already contains the relevant components and the integration is trivial.

---

# 49. Required Final Response From Coding Agent

At the end of implementation, report:

```text
JITSI DEPLOYMENT STATUS: PASS / FAIL

Docker:
    PASS / FAIL

Jitsi Web:
    PASS / FAIL

Prosody:
    PASS / FAIL

Jicofo:
    PASS / FAIL

JVB:
    PASS / FAIL

HTTPS:
    PASS / FAIL

Two-user meeting:
    PASS / FAIL

Audio:
    PASS / FAIL

Video:
    PASS / FAIL

Screen sharing:
    PASS / FAIL

Backend meeting integration:
    PASS / FAIL

Frontend integration:
    PASS / FAIL

Meeting persistence:
    PASS / FAIL

Existing platform regression:
    PASS / FAIL

Smoke tests:
    PASS / FAIL

Documentation:
    PASS / FAIL
```

Then provide:

```text
Files added
Files modified
Docker changes
Environment variables
Database migrations
Commands to start
Commands to stop
Commands to test
Known limitations
Recommended next implementation step
```

Do not claim PASS for any item that was not actually tested.