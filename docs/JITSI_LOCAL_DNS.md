# Jitsi Local DNS

The deployment uses the hostname `meet.scad.local` and non-standard HTTPS port
8443. Browsers must be able to resolve this name to the local host.

## Development hosts-file entry

Add to the OS hosts file (Windows: `C:\Windows\System32\drivers\etc\hosts`,
run the editor as Administrator):

```
127.0.0.1  meet.scad.local
```

For a second client on the LAN, replace `127.0.0.1` with the VDI host LAN IP
and set `JVB_ADVERTISE_IPS` in `jitsi/.env` to that IP.

## Why a hostname (not just localhost)

- WebRTC `getUserMedia` requires a secure context. `localhost` is treated as
  secure, but a real hostname is needed to exercise the actual DNS/TLS path and
  to allow a second participant on the network.
- `PUBLIC_URL` and the Jitsi BOSH/WebSocket URLs are derived from the hostname.

## Corporate DNS (eventual)

In production, register `meet.scad.local` (or a real FQDN) in corporate DNS
pointing at the server, and replace the self-signed cert with an internal-CA
signed certificate.

## HTTPS / self-signed trust

1. The cert lives at `jitsi/config/storage/web/keys/cert.{crt,key}`.
2. Trust it in the browser by importing `cert.crt` into the OS/browser trust
   store (or accept the "not secure" warning on first visit).
3. The private key must never be committed to git.
