# Jitsi Architecture

## High level

```
                   Browser
                      │ HTTPS (meet.scad.local:8443, self-signed)
                      ▼
              Jitsi Web (nginx)
                 ┌────┴────────┐
                 │             │
                 ▼             ▼
              Prosody        Jicofo ──► JVB (UDP 10000)
              (XMPP)           (focus)    (videobridge)
```

Jitsi remains an **AV/meeting subsystem** only. It contains no methodology,
RAG, knowledge, or approval logic.

## Boundary

```
React frontend (JitsiMeeting iframe)
        │ create meeting / fetch URL+JWT
        ▼
FastAPI backend (MeetingService → JitsiAdapter)
        │
        ▼
meeting_sessions table (PostgreSQL)   ── links jitsi_room_name → methodology session
```

The methodology agent never depends on Jitsi internals; it talks to
`MeetingService`, which can later be swapped for Teams/Webex/custom WebRTC.

## Components

| Component | Image | Role |
|---|---|---|
| web | `ghcr.io/jitsi/web` | nginx + Jitsi Meet UI, TLS termination, `/external_api.js` |
| prosody | `ghcr.io/jitsi/prosody` | XMPP signalling server |
| jicofo | `ghcr.io/jitsi/jicofo` | conference focus (room management) |
| jvb | `ghcr.io/jitsi/jvb` | videobridge (media routing, UDP) |

## Networks

Jitsi runs on its own network `jitsi_meet.jitsi` (isolated). The methodology
stack runs on the default compose network. The backend reaches Jitsi only via
the configured public URL (`JITSI_BASE_URL`); it does not share a network.

## Room naming

Controlled and traceable: `scad-<methodology-session-id-lower>` (e.g.
`scad-m-000001`). Never derived from raw user input. The methodology session id
remains the authoritative identifier; the Jitsi room name is an alias.

## Meeting lifecycle

`created → ready → live → ended` persisted in `meeting_sessions`
(`status`, `created_at`, `started_at`, `ended_at`).

## Audio strategy (for the next phase)

This deployment does **not** capture audio. Jitsi audio is not automatically
available server-side. The recommended strategy for the ASR phase is
Jigasi-based capture or per-participant audio, documented in the final report —
not browser audio scraping.
