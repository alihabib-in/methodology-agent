"""Meeting subsystem: abstracts Jitsi behind a stable service interface.

The methodology agent never depends on Jitsi implementation details; it talks
to MeetingService, which can later be swapped for Teams/Webex/custom WebRTC.
"""
