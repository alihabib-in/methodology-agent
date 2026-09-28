# Jitsi Acceptance Test (manual)

Prerequisite: hosts entry for `meet.scad.local`, self-signed cert trusted in
browser, Jitsi stack + API running.

1. Open the methodology application (React dev server, `cd frontend && npm run dev`).
2. Click "Create Meeting".
3. Verify the Jitsi room loads in the iframe.
4. Verify the microphone works (audio level indicator moves when speaking).
5. Verify the camera works (self-view visible).
6. Join with a second participant (second browser/profile on same or another host).
7. Verify both participants are visible.
8. Verify two-way audio between participants.
9. Verify two-way video.
10. Verify screen sharing.
11. Leave the meeting.
12. Verify backend meeting status (`GET /api/v1/meetings/{id}` → `ended`).

Record the result of each step in `JITSI_FINAL_IMPLEMENTATION_REPORT.md`.
