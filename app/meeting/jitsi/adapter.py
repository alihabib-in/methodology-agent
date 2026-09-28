"""Jitsi adapter: room naming, URLs, and JWT token generation.

Keeps Jitsi specifics behind a small interface so the rest of the platform
never touches Jitsi internals directly.
"""

from __future__ import annotations

import re
import time

import jwt

from app.core.config import settings


class JitsiAdapter:
    def __init__(self, base_url: str | None = None, jwt_secret: str | None = None) -> None:
        self.base_url = (base_url or settings.jitsi_base_url).rstrip("/")
        self.jwt_secret = jwt_secret or settings.jitsi_jwt_secret

    def build_room_name(self, session_id: str, suffix: str | None = None) -> str:
        # Controlled, traceable room naming — never derived from raw user input.
        slug = re.sub(r"[^a-z0-9-]+", "", (session_id or "").lower()).strip("-")
        name = f"{settings.jitsi_room_prefix}-{slug}"
        if suffix:
            name = f"{name}-{suffix}"
        return name

    def build_url(self, room_name: str) -> str:
        return f"{self.base_url}/{room_name}"

    def validate_room(self, room_name: str) -> bool:
        return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,120}", room_name or ""))

    def create_token(
        self,
        room_name: str,
        user_id: str | None = None,
        display_name: str | None = None,
        moderator: bool = False,
        email: str | None = None,
        ttl_seconds: int = 3600,
    ) -> str:
        """Generate a Jitsi JWT. Returns '' when auth is not configured."""
        if not self.jwt_secret:
            return ""

        now = int(time.time())
        payload = {
            "iss": settings.jitsi_jwt_accepted_issuers,
            "sub": user_id or "anonymous",
            "aud": settings.jitsi_jwt_accepted_audiences,
            "room": room_name,
            "exp": now + ttl_seconds,
            "nbf": now - 10,
            "context": {
                "user": {
                    "name": display_name or "Participant",
                    "email": email or "",
                }
            },
            "moderator": bool(moderator),
        }
        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm="HS256",
            headers={"kid": settings.jitsi_jwt_app_id, "typ": "JWT"},
        )
