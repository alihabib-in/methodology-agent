#!/usr/bin/env bash
# Jitsi smoke test — verifies the Jitsi stack and meeting integration.
# Run from the repository root. Requires docker compose and curl.
set -euo pipefail

FAIL=0
PASS=0

report() {
  local label="$1" ok="$2"
  if [[ "$ok" == "PASS" ]]; then
    echo "  PASS  $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Jitsi smoke test ==="

# 1. Jitsi web reachable over HTTPS (self-signed -> -k)
if curl -sk -o /dev/null "https://127.0.0.1:8443/"; then
  report "Jitsi web HTTPS reachable" PASS
else
  report "Jitsi web HTTPS reachable" FAIL
fi

# 2. HTTP redirects to HTTPS
CODE=$(curl -sk -o /dev/null -w '%{http_code}' "http://127.0.0.1:8880/")
if [[ "$CODE" == "301" || "$CODE" == "302" || "$CODE" == "308" ]]; then
  report "Jitsi HTTP redirects to HTTPS" PASS
else
  report "Jitsi HTTP redirects to HTTPS (got $CODE)" FAIL
fi

# 3. Jitsi services running
for svc in web prosody jicofo jvb; do
  if docker compose -f jitsi/docker-compose.yml ps --status running "$svc" | grep -q "$svc"; then
    report "Jitsi $svc running" PASS
  else
    report "Jitsi $svc running" FAIL
  fi
done

# 4. Application can create a meeting
MEETING_JSON=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/meetings" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SMOKE-0001","title":"smoke test","created_by":"smoke","display_name":"Smoke"}')

if echo "$MEETING_JSON" | grep -q '"jitsi_room_name"'; then
  report "Application can create a meeting" PASS
else
  report "Application can create a meeting" FAIL
fi

# 5. Meeting URL generated
if echo "$MEETING_JSON" | grep -q '"jitsi_url"'; then
  report "Meeting URL generated" PASS
else
  report "Meeting URL generated" FAIL
fi

echo ""
echo "Result: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
