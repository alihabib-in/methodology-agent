# Real-Time AI Meeting UI & Methodology Assistant
## Coding Agent Implementation Prompt

### 1. Mission

You are implementing the **real-time AI meeting experience** for the SCAD Methodology AI Platform.

The platform combines:

- Self-hosted Jitsi Meet for audio/video meetings
- React + TypeScript frontend
- FastAPI backend
- PostgreSQL as the authoritative database
- Qdrant for semantic knowledge retrieval
- Local AI/LLM inference
- Arabic/English speech understanding
- Methodology elicitation and gap detection
- Human-in-the-loop approval

The objective of this task is to transform the current meeting interface from a static application into a **living, real-time methodology workspace**.

The user should feel that the AI is:

1. Listening
2. Understanding
3. Detecting methodology requirements
4. Identifying gaps
5. Refining the objective
6. Generating questions
7. Recording answers
8. Updating the methodology state
9. Preparing the candidate methodology

However, the interface must remain professional and appropriate for a government/statistical organization.

**Do not create a flashy "AI demo".**

The experience should feel:

- intelligent
- calm
- responsive
- modern
- professional
- lightweight
- trustworthy
- information-dense without being cluttered

---

# 2. Critical Instruction: Inspect Existing Repository First

Before writing code:

1. Inspect the entire existing repository.
2. Identify the existing:
   - React application
   - routes
   - components
   - state management
   - API clients
   - WebSocket implementation
   - Jitsi integration
   - methodology components
   - question components
   - methodology state models
   - backend WebSocket/event infrastructure
   - existing CSS/design system
   - authentication
3. Reuse existing architecture wherever possible.
4. Do not create duplicate implementations.
5. Do not replace working components unnecessarily.
6. Preserve existing functionality.

Create:

```text
docs/REALTIME_AI_UX_IMPLEMENTATION_ASSESSMENT.md
```

Document:

- existing frontend architecture
- existing real-time/event infrastructure
- existing Jitsi integration
- existing methodology state flow
- components that can be reused
- components that need modification
- gaps in the current architecture
- proposed implementation approach

Only after this assessment should implementation begin.

---

# 3. Core UX Concept

The meeting screen should have two primary areas.

```text
┌───────────────────────────────────────────────────────────────┐
│ SCAD Methodology Assistant                         User/Menu │
├───────────────────────────────────┬───────────────────────────┤
│                                   │                           │
│                                   │ ✦ AI METHODOLOGY          │
│                                   │   ● Listening              │
│                                   │                           │
│          JITSI MEETING             │ OBJECTIVE                 │
│                                   │ ───────────────────────   │
│                                   │ Define monthly indicator  │
│                                   │ for active establishments │
│                                   │                           │
│                                   │ METHODOLOGY GAPS          │
│                                   │ ✓ Population               │
│                                   │ ◐ Reference period         │
│                                   │ ○ Statistical unit         │
│                                   │                           │
│                                   │ ✦ NEW QUESTION             │
│                                   │                           │
│                                   │ What should be the        │
│                                   │ reference period?         │
│                                   │                           │
│                                   │ Why I'm asking            │
│                                   │ Determines measurement    │
│                                   │ frequency and reporting.  │
│                                   │                           │
│                                   │ [ Ask Question ]          │
│                                   │                           │
├───────────────────────────────────┴───────────────────────────┤
│ ✦ AI Activity                                                 │
│ ● Objective refined  ● Gap detected  ● Question generated    │
└───────────────────────────────────────────────────────────────┘
```

The left side is primarily the meeting.

The right side is the **living AI methodology workspace**.

The right side must update in real time without requiring page refreshes.

---

# 4. Real-Time First Architecture

Do NOT implement this through aggressive REST polling.

The preferred architecture is:

```text
Jitsi
  │
  ▼
Meeting / Transcript Events
  │
  ▼
FastAPI
  │
  ├── Methodology Engine
  ├── Gap Detection
  ├── Question Generation
  ├── Answer Interpretation
  └── Methodology State
          │
          ▼
      WebSocket
          │
          ▼
    React Event Store
          │
          ▼
      UI Components
          │
          ▼
     Lightweight Animation
```

The frontend should maintain a real-time application state.

Use the project's existing state-management technology if one already exists.

If no state manager exists, prefer a lightweight solution such as Zustand rather than introducing Redux solely for this task.

---

# 5. Event-Driven UI

The backend should emit structured events.

Reuse existing events if already implemented.

Required logical events include:

```text
meeting.created
meeting.ready
meeting.started
meeting.ended

participant.joined
participant.left

transcript.segment

ai.status.changed

objective.detected
objective.updated

methodology.updated

gap.detected
gap.updated
gap.resolved

question.generated
question.presented
question.asked

answer.received
answer.interpreted

insight.created

candidate_scope.updated
candidate_scope.ready

knowledge.candidate
knowledge.approved
knowledge.published

system.error
```

Every event should contain enough information for the frontend to update the appropriate state.

Example:

```json
{
  "event_type": "gap.detected",
  "event_id": "evt-123",
  "session_id": "session-001",
  "timestamp": "2026-09-15T10:12:22Z",
  "payload": {
    "gap_id": "gap-004",
    "concept": "reference_period",
    "label": "Reference period",
    "status": "open",
    "priority": 0.91
  }
}
```

---

# 6. Event Envelope

Standardize the WebSocket event envelope.

Use something equivalent to:

```json
{
  "event_id": "uuid",
  "event_type": "gap.detected",
  "session_id": "uuid",
  "meeting_id": "uuid",
  "timestamp": "ISO-8601",
  "sequence": 124,
  "payload": {}
}
```

Requirements:

- unique event ID
- session correlation
- meeting correlation where applicable
- server timestamp
- monotonic sequence number if practical
- structured payload
- schema validation

The frontend must handle duplicate events safely.

---

# 7. Connection Handling

The UI must gracefully handle WebSocket problems.

Implement:

```text
CONNECTED
    ↓
RECONNECTING
    ↓
CONNECTED
```

If disconnected:

```text
● Live connection lost
  Reconnecting...
```

Do not freeze the entire UI.

When reconnected:

1. reconnect WebSocket
2. request current session state
3. reconcile state
4. resume receiving events

Do not rely solely on missed events.

The server's authoritative current state must always be recoverable through REST/API.

---

# 8. AI Status Indicator

At the top of the right panel create:

```text
✦ AI METHODOLOGY ASSISTANT
● Listening
```

The status should dynamically change.

Suggested statuses:

```text
listening
analyzing
detecting_gaps
generating_question
waiting_for_user
processing_answer
updating_methodology
ready
offline
error
```

Examples:

### Listening

```text
● Listening
  Understanding the discussion
```

### Analyzing

```text
◌ Analyzing
  Identifying methodology requirements
```

### Gap detection

```text
◌ Reviewing methodology
  Checking for missing information
```

### Question generation

```text
✦ Preparing question
  Prioritizing the most important gap
```

### Waiting

```text
● Waiting for response
```

### Ready

```text
✓ Up to date
```

Do NOT continuously display "AI is thinking".

Status changes should communicate meaningful system activity.

---

# 9. AI Status Animation

Use lightweight CSS or the existing animation library.

If introducing a library is necessary, prefer:

```text
Motion / Framer Motion
```

Do not introduce heavy animation frameworks.

The status indicator may use:

- subtle pulse
- opacity transition
- small rotation
- soft glow
- animated dots

Avoid:

- large spinning graphics
- excessive particle effects
- flashing
- bouncing elements
- distracting gradients
- continuous motion everywhere

Animation should stop or settle when the s