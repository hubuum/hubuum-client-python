"""Public exception hierarchy for the Hubuum client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class HubuumError(Exception):
    """Base class for every library-defined exception."""


class ResultCardinalityError(HubuumError):
    """A query expected exactly one result but returned another cardinality."""


@dataclass(eq=False, frozen=True, slots=True)
class TaskUnsuccessfulError(HubuumError):
    """A task reached a terminal state that does not represent full success.

    Only the task ID and status are retained. In particular, the server's task
    summary is excluded because it can contain details derived from submitted
    data.
    """

    task_id: int
    status: str

    def __str__(self) -> str:
        return f"task {self.task_id} finished with status {self.status}"


class ConfigurationError(HubuumError, ValueError):
    """Raised when client configuration is unsafe or invalid."""


@dataclass(eq=False)
class TransportError(HubuumError):
    """A request failed before a valid HTTP response was received."""

    method: str
    url: str
    reason: str

    def __str__(self) -> str:
        return f"{self.method} {self.url} failed: {self.reason}"


@dataclass(eq=False)
class DecodeError(HubuumError):
    """The server returned a successful response with an unexpected body."""

    method: str
    url: str
    status_code: int
    reason: str

    def __str__(self) -> str:
        return (
            f"{self.method} {self.url} returned an invalid response "
            f"({self.status_code}): {self.reason}"
        )


@dataclass(eq=False)
class APIError(HubuumError):
    """A non-successful Hubuum API response.

    The access token and request body are intentionally never retained.
    """

    method: str
    url: str
    status_code: int
    error: str | None = None
    message: str | None = None
    response_body: Any = None
    request_id: str | None = None

    def __str__(self) -> str:
        detail = self.message or self.error or "request failed"
        request_id = f" [request_id={self.request_id}]" if self.request_id else ""
        return f"{self.method} {self.url} returned {self.status_code}: {detail}{request_id}"


class AuthenticationError(APIError):
    """Authentication is missing or was rejected."""


class PermissionDeniedError(APIError):
    """The authenticated principal cannot perform the operation."""


class NotFoundError(APIError):
    """The requested resource does not exist or is not visible."""


class ConflictError(APIError):
    """The operation conflicts with existing server state."""


class RateLimitError(APIError):
    """The server rejected the request because a rate limit was exceeded."""

    retry_after: float | None = None
