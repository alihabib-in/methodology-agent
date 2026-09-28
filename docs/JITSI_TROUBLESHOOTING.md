# Jitsi Troubleshooting

## Jitsi iframe is blank / never loads

The frontend loads `https://<JITSI_DOMAIN>/external_api.js`. If that script is
blocked, the meeting panel stays blank (the app now shows a red error message).

Causes:

1. **TLS certificate does not cover the address** — the self-signed cert must
   include the LAN IP in `subjectAltName` (match `frontend/.env`
   `VITE_JITSI_DOMAIN`). Regenerate the cert per `JITSI_DEPLOYMENT.md`, then
   restart: `docker compose -f jitsi/docker-compose.yml up -d`.
2. **Jitsi web not reachable** — `curl -k https://<JITSI_DOMAIN>/external_api.js`
   should return the script.
3. **Browser has not trusted the cert** — import `cert.crt` into the OS/browser
   trust store (or accept the warning for the exact host/IP used in the iframe).

## Web page loads but no media (most common)

Check the JVB and browser console:

```bash
docker compose -f jitsi/docker-compose.yml logs --tail=100 jvb
```

Common causes:

1. **JVB advertised address wrong** — set `JVB_ADVERTISE_IPS` to the address
   the browser can reach (127.0.0.1 for same-host, LAN IP for remote).
2. **UDP blocked** — JVB uses UDP 10000. Corporate firewalls/NAT may block UDP;
   enable `JVB_TCP_HARVESTER_DISABLED=false` for TCP fallback (slower).
3. **STUN disabled** — `JVB_DISABLE_STUN=1` is fine for localhost-only, but for
   remote clients re-enable STUN and/or configure a TURN server.

## Docker cannot see GPU / media issues in WSL2

Confirm `docker run --rm --gpus all nvidia/cuda:... nvidia-smi` works. This
affects the LLM, not Jitsi (Jitsi is CPU-only here).

## nginx cert error

```
cannot load certificate key "/storage/keys/cert.key"
```

- "No such file": the cert is missing from `jitsi/config/storage/web/keys/`.
- "Permission denied": the key file is not world-readable. Regenerate with 644
  (see `JITSI_DEPLOYMENT.md`).

## Prosody/Jicofo/JVB not connecting

Check the logs in order:

```bash
docker compose -f jitsi/docker-compose.yml logs --tail=100 prosody
docker compose -f jitsi/docker-compose.yml logs --tail=100 jicofo
docker compose -f jitsi/docker-compose.yml logs --tail=100 jvb
```

Look for "Authenticated", "Connected", "Added new videobridge" (healthy signs).

## Images not found

The current registry is `ghcr.io/jitsi` (not Docker Hub). Ensure
`JITSI_IMAGE_REPO=ghcr.io/jitsi` and `JITSI_IMAGE_VERSION=unstable` (or a
pinned versioned tag).

## Port conflicts

Jitsi uses 8880, 8443, 10000/udp, 9080, 8888 — verify none are taken by the
methodology stack (8000/8001/8080/5432/6333/6334).
