# Real-Time AI UX — Implementation Assessment

## Scope

This document records the repository inspection required before implementing the
real-time methodology workspace (see `RealTime_AI Prompt.md`). It maps the
existing architecture to the target real-time architecture and lists the
changes needed.

## Existing frontend architecture

- Framework: **React 18 + Vite** (plain JSX, not TypeScript — see "Language"
  below).
- No router, no state manager. State lives in a single `App` component via
  `useState`/`useRef`.
- Components:
  - `App.jsx` — phases (`login` → `setup` → `meeting`), tab bar, journals.
  - `JitsiMeeting.jsx` — owns the JitsiMeetExternalAPI iframe lifecycle.
  - `MethodologyAssistant.jsx` — static objective / gaps / question panel.
- API client: `api.js` (fetch wrappers, no WebSocket).

## Existing real-time / event infrastructure

- **None.** No WebSocket, no SSE, no Redis/pub-sub, no polling loop.
- `uvicorn[standard]` is already the ASGI server, so native FastAPI WebSocket
  support is available with no new runtime dependency.
- Meeting/participant events are already persisted via
  `POST /api/v1/meetings/{id}/events` (`MeetingEvent` table) — reusable as the
  source for broadcasting.

## Existing Jitsi integration

- `JitsiMeeting.jsx` emits normalized callbacks (`onReady`,
  `onParticipantJoined`, `onParticipantLeft`, `onMeetingEnded`) which `App`
  forwards to `logEvent(...)` → `POST /api/v1/meetings/{id}/events`.

## Existing methodology state flow

- `MethodologyAgent.analyze(text, language, state)` → deterministic
  `StateManager` + `GapDetector` + `QuestionGenerator` (LLM only for
  extraction). Returns `summary`, `methodology_state`, `gaps`,
  `recommended_question`.
- Session-scoped endpoints in `app/api/meetings.py`
  (`POST /meetings`, `POST /meetings/{id}/analyze`, `/answer`, `/state`).
- Jitsi meeting endpoints in `app/api/meeting.py`
  (`POST /api/v1/meetings`, start/end, events).
- Persistence: `Meeting` (session + methodology_state JSON), `MeetingSession`
  (Jitsi room), `MeetingEvent` (audit), `KnowledgeItem`.

## Components that can be reused

- `MethodologyAgent` pipeline (gaps/question/state) — unchanged.
- `MeetingEvent` + the `/events` endpoint — becomes the broadcast path for
  participant/lifecycle events.
- `GET /meetings/{id}/state` — the authoritative state source for reconnect
  reconciliation.
- `JitsiMeeting.jsx` callbacks — already emit the participant/lifecycle events.

## Components that need modification

- `MethodologyAssistant.jsx` — replace static props with store-driven values +
  AI status indicator.
- `App.jsx` — connect the realtime store, drive the assistant from events,
  render the AI activity bar.
- `app/api/meetings.py`, `app/api/meeting.py`, `app/api/knowledge.py` — publish
  structured events.

## Gaps in the current architecture

1. No WebSocket / push channel.
2. No standardized event envelope or sequence numbering.
3. No client-side event store or reconnect/reconciliation logic.
4. No AI status model/indicator.
5. No live transcript ingestion (audio capture remains Stage 2, out of scope).

## Proposed implementation approach

1. **Backend realtime package** (`app/realtime/`):
   - `events.py` — event type constants + Pydantic `EventEnvelope`
     (`event_id`, `event_type`, `session_id`, `meeting_id`, `timestamp`,
     `sequence`, `payload`).
   - `broker.py` — in-process thread-safe pub/sub fanning events out by
     `session_id` to per-connection asyncio queues.
   - `websocket.py` — `GET /ws/{session_id}`; sends a state snapshot on connect,
     then relays events.
   - Wire the broker onto `app.state` in `main.py`.
2. **Emit events** from the existing endpoints (no duplicate logic):
   - `meetings.py` analyze/answer → `ai.status.changed`, `methodology.updated`,
     `objective.updated`, `gap.detected`, `question.generated`.
   - `meeting.py` create/start/end/events → `meeting.*`, and re-broadcast
     `participant.*` (already logged by the frontend).
   - `knowledge.py` approve/publish → `knowledge.*`.
3. **Frontend realtime** (no new dependency; lightweight store):
   - `store/store.js` — minimal subscription store + `useSyncExternalStore`.
   - `realtime/socket.js` + `hooks/useRealtime.js` — connect/reconnect, dedup by
     `event_id`, reconcile via `GET /meetings/{id}/state`.
   - `AIStatus.jsx`, `AIActivityBar.jsx`, updated `MethodologyAssistant.jsx`.
4. **Animation** — pure CSS (pulse/opacity), no animation framework.

## Language

The prompt references "React + TypeScript"; the repository frontend is JSX.
Converting to TypeScript is out of scope (would replace working components and
violate "reuse existing architecture"). The realtime layer is implemented in
JSX to match the existing codebase.

## Known limitations

- Single-worker in-process broker (no cross-process Redis). Fine for the
  current single-node deployment; the broker abstraction isolates the swap to
  Redis later.
- Live transcript `transcript.segment` events are defined but not yet produced
  (audio capture is a separate phase).
