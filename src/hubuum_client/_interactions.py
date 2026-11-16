"""Shared policy for private, origin-bound authentication capabilities."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeAlias
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from ._transport import _parse_retry_after
from .api import models as wire
from .errors import AuthenticationInteractionError
from .models import (
    AuthenticationBrowserNext,
    AuthenticationInteractionBegun,
    AuthenticationInteractionRequest,
    AuthenticationInteractionStatus,
    ConfirmRestoreOperation,
    CreateTokenOperation,
    CreateUserOperation,
    CredentialApprovalResponse,
    CredentialOperation,
    ImportCredentialsOperation,
    LoginResponse,
    RenewTokenOperation,
    SecurityCandidateActivated,
    SecurityCandidateVerification,
    Task,
    UpdateUserOperation,
    UserPoint,
    _valid_authentication_proof,
)
from .types import AccessToken, AuthenticationProviderId

METHODS = "/api/v1/auth/methods"
INTERACTIONS = "/api/v1/auth/interactions"
CANDIDATES = "/api/v1/admin/runtime-settings/security-candidates"
MAX_AUTHENTICATION_BODY_BYTES = 1024 * 1024
MAX_AUTHENTICATION_SECONDS = 30.0
MAX_INTERACTION_SECONDS = 600

CredentialWireResult: TypeAlias = (
    LoginResponse | UserPoint | Task | wire.RestoreStageResponse | SecurityCandidateActivated
)
CredentialResult: TypeAlias = (
    AccessToken | UserPoint | Task | wire.RestoreStageResponse | SecurityCandidateActivated
)


def candidate_path(candidate_id: UUID) -> str:
    if not isinstance(candidate_id, UUID) or not candidate_id.int:
        raise AuthenticationInteractionError("A valid candidate identifier is required")
    return f"{CANDIDATES}/{candidate_id}"


def verified_preview(
    result: SecurityCandidateVerification, candidate_id: UUID, provider_id: AuthenticationProviderId
) -> SecurityCandidateVerification:
    preview = result.verification
    if (
        result.candidate.id != candidate_id
        or result.candidate.group != "authentication"
        or preview.candidate_id != candidate_id
        or preview.provider_id != provider_id
        or preview.issued_session
        or preview.provisioned
    ):
        raise AuthenticationInteractionError(
            "Candidate verification binding or effects are invalid"
        )
    return result


@dataclass(frozen=True, repr=False)
class ApprovedRequest:
    method: str
    path: str
    body: dict[str, Any]
    response_model: type[CredentialWireResult]
    headers: dict[str, str]
    evidence: CredentialApprovalResponse


def approved_request(
    operation: CredentialOperation, approval: CredentialApprovalResponse
) -> ApprovedRequest:
    _valid_authentication_proof(approval.approval, "hca1.")
    expiry = approval.record.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    if (
        approval.record.operation != operation.kind
        or approval.record.consumed_at is not None
        or approval.record.invalidated_at is not None
        or expiry <= datetime.now(UTC)
    ):
        raise AuthenticationInteractionError("Approval is invalid or does not match the operation")
    model: type[CredentialWireResult]
    method = "POST"
    if isinstance(operation, (CreateTokenOperation, RenewTokenOperation)):
        path = f"/api/v1/iam/principals/{operation.principal_id}/tokens"
        if isinstance(operation, RenewTokenOperation):
            body = approval.token_request(operation.token).payload()
            path += f"/{operation.token_id}/renew"
        else:
            body = approval.token_request(operation.token).payload()
        model = LoginResponse
    elif isinstance(operation, (CreateUserOperation, UpdateUserOperation)):
        body = operation.user.payload()
        path = "/api/v1/iam/users"
        if isinstance(operation, UpdateUserOperation):
            path += f"/{operation.user_id}"
            method = "PATCH"
        model = UserPoint
    elif isinstance(operation, ImportCredentialsOperation):
        body = operation.import_.payload()
        path = "/api/v1/imports"
        model = Task
    elif isinstance(operation, ConfirmRestoreOperation):
        body = operation.confirmation.payload()
        path = f"/api/v1/restores/{operation.restore_id}/confirm"
        model = wire.RestoreStageResponse
    else:
        body = {
            "expected_revision": operation.expected_revision,
            "verification_receipt": operation.verification_receipt.get_secret_value(),
        }
        path = candidate_path(operation.candidate_id) + "/activate"
        model = SecurityCandidateActivated
    return ApprovedRequest(method, path, body, model, approval.headers(), approval)


def credential_result(result: CredentialWireResult) -> CredentialResult:
    if isinstance(result, LoginResponse):
        return AccessToken(result.token, expires_at=result.expires_at)
    return result


def authentication_timeout(timeout: httpx.Timeout) -> dict[str, float]:
    return {
        name: min(value, MAX_AUTHENTICATION_SECONDS)
        if value is not None
        else MAX_AUTHENTICATION_SECONDS
        for name, value in timeout.as_dict().items()
    }


def completed_response(response: httpx.Response, body: bytearray) -> httpx.Response:
    return httpx.Response(
        response.status_code,
        headers=response.headers,
        content=bytes(body),
        request=response.request,
    )


def append_authentication_body(body: bytearray, chunk: bytes, deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise AuthenticationInteractionError("Authentication response deadline exceeded")
    if len(body) + len(chunk) > MAX_AUTHENTICATION_BODY_BYTES:
        raise AuthenticationInteractionError("Authentication response exceeds the allowed size")
    body.extend(chunk)


def origin(value: str) -> tuple[str, str | None, int | None]:
    parsed = urlsplit(value)
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or any(not char.isprintable() for char in value)
    ):
        raise AuthenticationInteractionError("Invalid verification origin")
    return (
        parsed.scheme,
        parsed.hostname,
        parsed.port or {"http": 80, "https": 443}.get(parsed.scheme),
    )


@dataclass(repr=False)
class InteractionBinding:
    begun: AuthenticationInteractionBegun
    client_id: str
    deadline: float
    interval: float
    next_poll: float
    closed: bool = False

    @classmethod
    def receive(
        cls,
        begun: AuthenticationInteractionBegun,
        request: AuthenticationInteractionRequest,
        base: str,
    ) -> InteractionBinding:
        remaining = min(
            (begun.expires_at - datetime.now(UTC)).total_seconds(), MAX_INTERACTION_SECONDS
        )
        if remaining <= 0 or not begun.id.int:
            raise AuthenticationInteractionError("Interaction has expired or is invalid")
        if isinstance(begun.next, AuthenticationBrowserNext):
            try:
                valid = origin(begun.next.verification_uri) == origin(base)
            except ValueError:
                valid = False
            if not valid or any(not char.isprintable() for char in begun.next.user_code):
                raise AuthenticationInteractionError("Invalid verification origin or user code")
        now = time.monotonic()
        return cls(
            begun,
            request.client_id,
            now + remaining,
            begun.interval_seconds,
            now + begun.interval_seconds,
        )

    def __repr__(self) -> str:
        return "InteractionBinding(<redacted>)"

    @property
    def authorization(self) -> str:
        return "Hubuum-Interaction " + self.begun.redemption_secret.get_secret_value()

    @property
    def body(self) -> dict[str, Any]:
        return {"client_id": self.client_id}

    def path(self, action: str) -> str:
        return f"{INTERACTIONS}/{self.begun.id}/{action}"

    def require_live(self) -> None:
        if self.closed:
            raise AuthenticationInteractionError("Interaction is terminal; begin a new interaction")
        if time.monotonic() >= self.deadline or datetime.now(UTC) >= self.begun.expires_at:
            raise AuthenticationInteractionError("Interaction expired; begin a new interaction")

    @property
    def poll_after(self) -> float:
        return max(0, min(self.next_poll, self.deadline) - time.monotonic())

    def before_poll(self) -> None:
        self.require_live()
        if time.monotonic() < self.next_poll:
            raise AuthenticationInteractionError("Polling interval has not elapsed")

    def after_poll(self, status: int, headers: httpx.Headers) -> None:
        if httpx.codes.is_client_error(status) and status != httpx.codes.TOO_MANY_REQUESTS:
            self.closed = True
        if status in {httpx.codes.TOO_MANY_REQUESTS, httpx.codes.SERVICE_UNAVAILABLE}:
            retry = (
                _parse_retry_after(headers.get("retry-after"), received_at=datetime.now(UTC)) or 0
            )
            self.interval = min(MAX_INTERACTION_SECONDS, max(self.interval + 5, retry))
        self._schedule()

    def transport_failure(self) -> None:
        self.interval = min(MAX_INTERACTION_SECONDS, self.interval * 2)
        self._schedule()

    def _schedule(self) -> None:
        self.next_poll = time.monotonic() + self.interval * (1 + secrets.randbelow(201) / 1000)

    def status(self, status: AuthenticationInteractionStatus) -> AuthenticationInteractionStatus:
        if status.id != self.begun.id or status.expires_at != self.begun.expires_at:
            raise AuthenticationInteractionError("Interaction status binding does not match")
        self.closed = status.terminal
        return status

    def consume(self) -> None:
        self.require_live()
        self.closed = True
