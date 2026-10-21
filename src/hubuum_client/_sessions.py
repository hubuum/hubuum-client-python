"""Shared in-memory session policy; no persistence or retained passwords."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from .errors import ConfigurationError, SessionExpiredError
from .models import SessionResponse


def validate_client_id(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is None:
        raise ConfigurationError(
            "client_id must contain 1-128 ASCII letters, digits, '-', '.', '_' or ':'"
        )
    return value


@dataclass(frozen=True, slots=True)
class SessionState:
    credentials: SessionResponse
    client_id: str
    refresh_at: float

    @classmethod
    def receive(
        cls, credentials: SessionResponse, client_id: str, previous: SessionState | None = None
    ) -> SessionState:
        if previous is not None and (
            credentials.session_id != previous.credentials.session_id
            or credentials.absolute_expires_at != previous.credentials.absolute_expires_at
            or credentials.refresh_token == previous.credentials.refresh_token
        ):
            raise SessionExpiredError("Invalid session rotation; authenticate again")
        now = datetime.now(UTC)
        remaining = (credentials.access_expires_at - now).total_seconds()
        if remaining <= 0:
            raise SessionExpiredError("Received expired session; authenticate again")
        return cls(credentials, client_id, time.monotonic() + remaining - min(30, remaining / 10))

    def needs_refresh(self) -> bool:
        return (
            time.monotonic() >= self.refresh_at
            or datetime.now(UTC) >= self.credentials.access_expires_at
        )

    def require_refreshable(self) -> None:
        if datetime.now(UTC) >= self.credentials.refresh_expires_at:
            raise SessionExpiredError("Session expired; authenticate again")
