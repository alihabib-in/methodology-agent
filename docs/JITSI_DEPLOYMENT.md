# Jitsi Deployment

Self-hosted Jitsi Meet as a **separate** Docker Compose stack, isolated from the
methodology stack.

## Directory layout

```
jitsi/
├── docker-compose.yml   # official docker-jitsi-meet compose (web/prosody/jicofo/jvb)
├── .env                 # secrets + config (NOT committed)
├── .env.example         # placeholders
└── config/              # generated at runtime + certs (NOT committed)
    └── storage/web/keys/cert.{crt,key}
```

## Prerequisites

- Docker + Docker Compose
- A hosts-file entry for `meet.scad.local` (see `JITSI_LOCAL_DNS.md`)

## Configuration

Copy `jitsi/.env.example` to `jitsi/.env` and set at least:

```
JICOFO_AUTH_PASSWORD=<strong>
JVB_AUTH_PASSWORD=<strong>
JICOFO_COMPONENT_SECRET=<strong>
JWT_APP_SECRET=<strong>          # matches the backend JITSI_JWT_SECRET
```

## TLS (self-signed)

Generate a self-signed cert for `meet.scad.local`. The `subjectAltName` MUST
include the host LAN IP (keep it in sync with `frontend/.env`
`VITE_JITSI_DOMAIN`), otherwise the browser blocks `external_api.js` and the
Jitsi iframe stays blank:

```bash
mkdir -p jitsi/config/storage/web/keys
docker run --rm --entrypoint sh \
  -v "$(pwd)/jitsi/config/storage/web/keys:/certs" alpine/openssl \
  -c "openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout /certs/cert.key -out /certs/cert.crt -days 825 \
      -subj '/CN=meet.scad.local' \
      -addext 'subjectAltName=DNS:meet.scad.local,DNS:localhost,IP:127.0.0.1,IP:10.50.128.97' && \
      chmod 644 /certs/cert.key /certs/cert.crt"
```

## Start / stop

```bash
# start (from the jitsi/ directory)
cd jitsi && docker compose up -d

# check
docker compose ps
docker compose logs --tail=100 web
docker compose logs --tail=100 prosody
docker compose logs --tail=100 jicofo
docker compose logs --tail=100 jvb

# stop
docker compose down        # (do NOT use -v; preserves config/volume)
```

## Ports

| Service | Host port | Purpose |
|---|---|---|
| web HTTP | 8880 | redirects to HTTPS |
| web HTTPS | 8443 | Jitsi UI + signalling (BOSH/WebSocket) |
| JVB | 10000/udp | media (WebRTC) |
| JVB colibri | 9080 (127.0.0.1) | REST/health |
| Jicofo REST | 8888 (127.0.0.1) | stats/health |

## Authentication

`ENABLE_AUTH=0` for the initial local prototype (stack is bound to localhost).
JWT auth is implemented in the backend and enabled by setting:

```
ENABLE_AUTH=1
AUTH_TYPE=jwt
```

together with `JWT_APP_SECRET`, `JWT_APP_ID`, `JWT_ACCEPTED_ISSUERS`,
`JWT_ACCEPTED_AUDIENCES` (see `jitsi/.env.example`).
