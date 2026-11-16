"""Pinned client wire vectors, not a simulation of server/provider effects."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from hubuum_client import (
    APIError,
    AuthenticationInteractionRequest,
    AuthenticationInteractionStatus,
    AuthenticationMethods,
    CreateTokenOperation,
    CredentialApprovalResponse,
    NewTokenRequest,
    PrincipalId,
    SecurityCandidateActivated,
    SecurityCandidateReport,
    SecurityCandidateVerification,
    SessionResponse,
)
from hubuum_client import _interactions as policy
from hubuum_client._transport import raise_api_error
from hubuum_client.models import AuthenticationInteractionBegun

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
FIXTURE = ROOT / "fixtures/authentication/fixtures.json"
CORPUS = json.loads(FIXTURE.read_text())
IDS = {
    name: f"aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaa{index}"
    for index, name in enumerate(
        [
            "interaction-fixture",
            "bff-interaction-fixture",
            "verification-interaction-fixture",
            "candidate-fixture",
        ],
        start=1,
    )
}


def materialize(value: Any, offset: timedelta | None = None) -> Any:
    """Only tests replace public placeholders and the historical fixture clock."""
    if offset is None:
        offset = datetime.now(UTC) - datetime.fromisoformat(CORPUS["clock"])
    if isinstance(value, dict):
        return {key: materialize(item, offset) for key, item in value.items()}
    if isinstance(value, list):
        return [materialize(item, offset) for item in value]
    if not isinstance(value, str):
        return value
    if value in IDS:
        return IDS[value]
    if value == "FIXTURE-REDEMPTION-SECRET-NEVER-USE-IN-PRODUCTION":
        return "hai1." + "a" * 64
    if value == "FIXTURE-VERIFICATION-RECEIPT-NEVER-USE-IN-PRODUCTION":
        return "hcv1." + "b" * 64
    if value.startswith("hca1."):
        return "hca1." + "c" * 64
    try:
        date = datetime.fromisoformat(value)
    except ValueError:
        return value
    return (date + offset).isoformat()


def test_project_contract_and_shared_fixture_pins() -> None:
    source = json.loads((REPO / "docs/authentication-project-source.json").read_text())
    snapshot = json.loads((REPO / "src/hubuum_client/api/authentication-project.json").read_text())
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == source["source_fixture_sha256"]
    assert len(CORPUS["cases"]) == source["source_fixture_cases"] == 48
    assert (
        hashlib.sha256(
            (REPO / "src/hubuum_client/api/authentication-project.json").read_bytes()
        ).hexdigest()
        == source["source_project_snapshot_sha256"]
    )
    assert snapshot["spec_sha256"] == source["source_canonical_spec_sha256"]
    assert snapshot["operation_count"] == len(snapshot["operations"]) == 32


@pytest.mark.parametrize("fixture", CORPUS["cases"], ids=lambda fixture: fixture["id"])
def test_shared_authentication_wire_case(fixture: dict[str, Any]) -> None:
    case = materialize(fixture)
    response = case["response"]
    status = response["status"]
    body = response.get("body")
    operation = case["operation_id"]
    if status >= httpx.codes.BAD_REQUEST:
        error_request = httpx.Request("POST", "https://hubuum.example.invalid/fixture")
        http_response = httpx.Response(
            status, json=body, headers=response.get("headers"), request=error_request
        )
        with pytest.raises(APIError) as failed:
            raise_api_error(http_response)
        assert failed.value.status_code == status
        assert failed.value.reason == body["reason"]
        return
    if operation == "discoverAuthentication":
        assert len(AuthenticationMethods.model_validate(body).methods) == 3
    elif operation == "beginInteraction":
        begun = AuthenticationInteractionBegun.model_validate(body)
        raw_request = case["request"]
        request = AuthenticationInteractionRequest.model_validate(
            {
                key: value
                for key, value in raw_request.items()
                if key not in {"purpose", "candidate_id"}
            }
        )
        binding = policy.InteractionBinding.receive(
            begun, request, "https://hubuum.example.invalid/"
        )
        assert binding.client_id == raw_request["client_id"]
        assert "hai1." not in repr(binding)
    elif operation in {"interactionStatus", "continueCredentials"}:
        result = AuthenticationInteractionStatus.model_validate(body)
        assert result.state == body["state"]
    elif operation == "completeInteraction" and "session_id" in body:
        session = SessionResponse.model_validate(body)
        assert str(session.session_id) == body["session_id"]
        assert body["refresh_token"] not in repr(session)
    elif operation == "completeInteraction" and case["id"] == "candidate_browser_verified":
        verified = SecurityCandidateVerification.model_validate(body)
        assert not verified.verification.issued_session
        assert not verified.verification.provisioned
        verified.candidate.activation_operation()
    elif operation == "completeInteraction" and case["id"] == "fresh_approval_success":
        approval = CredentialApprovalResponse.model_validate(body)
        operation = CreateTokenOperation(
            principal_id=PrincipalId(42), token=NewTokenRequest(name="fixture-token")
        )
        assert (
            policy.approved_request(operation, approval).path == "/api/v1/iam/principals/42/tokens"
        )
    elif operation == "verifySecurityCandidate":
        candidate = SecurityCandidateReport.model_validate(body)
        with pytest.raises(ValueError, match="unverified"):
            candidate.activation_operation()
    elif operation == "activateSecurityCandidate":
        assert SecurityCandidateActivated.model_validate(body).changed
    else:
        assert operation in {"cancelInteraction", "revokeUndeliveredSession"}
        assert status == httpx.codes.NO_CONTENT
