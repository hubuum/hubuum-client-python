"""Security request invariants and secret-safe diagnostics at the API boundary."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from hubuum_client import (
    AuthenticationInteractionRequest,
    AuthenticationMethods,
    AuthenticationProviderInput,
    ProviderCredentialInput,
    RuntimeAuthorizationConnection,
    SecurityCandidateReport,
    SecurityCandidateRequest,
)


@pytest.mark.parametrize(
    ("action", "values"),
    [
        ("keep", {}),
        ("clear", {}),
        ("reference", {"alias": "private-ref"}),
        ("replace", {"value": SecretStr("private-value")}),
    ],
)
def test_explicit_credential_actions(action: str, values: dict[str, Any]) -> None:
    value = ProviderCredentialInput(action=action, **values)
    assert value.wire_payload()["action"] == action
    assert "private-" not in repr(value)
    assert "private-value" not in value.model_dump_json()


@pytest.mark.parametrize(
    "values",
    [
        {"action": "keep", "value": "private-value"},
        {"action": "replace"},
        {"action": "replace", "value": ""},
        {"action": "reference"},
        {"action": "reference", "alias": "bad private-ref"},
        {"action": "clear", "alias": "private-ref"},
        {"action": "reference", "alias": "private-ref", "value": "private-value"},
        {"action": "unknown-private-action"},
    ],
)
def test_invalid_credential_inputs_never_survive_validation_errors(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as failed:
        ProviderCredentialInput.model_validate(values)
    assert "private-" not in str(failed.value)
    assert "private-" not in repr(failed.value.errors())
    assert failed.value.__context__ is None


@pytest.mark.parametrize("version", [True, 1.0, "1", 2])
def test_discovery_rejects_non_integer_or_unknown_versions(version: object) -> None:
    with pytest.raises(ValidationError):
        AuthenticationMethods.model_validate({"interaction_version": version, "methods": []})


@pytest.mark.parametrize(
    "changes",
    [
        {"client_id": "bad client"},
        {"client_id": ""},
        {"provider_id": str(uuid4())[:-1] + "/"},
        {"provider_id": "00000000-0000-0000-0000-000000000000"},
        {"delivery": "bff"},
        {"return_target_id": "private-target"},
        {
            "delivery": "bff",
            "return_target_id": "private-target",
            "return_nonce": "too-short-private-nonce",
        },
        {"delivery": "bff", "return_target_id": "private-target", "return_nonce": "n" * 32 + "\n"},
        {"profile": {"subject": "private-client-supplied-identity"}},
    ],
)
def test_invalid_interaction_inputs_are_not_wire_requests(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as failed:
        AuthenticationInteractionRequest.model_validate(
            {"client_id": "fixture", "provider_id": "local"} | changes
        )
    assert "private-" not in str(failed.value)
    assert "private-" not in repr(failed.value.errors())


def test_bff_nonce_is_only_revealed_for_explicit_wire_transmission() -> None:
    nonce = "private-" + "n" * 32
    request = AuthenticationInteractionRequest(
        client_id="hubuum-frontend",
        provider_id=uuid4(),
        delivery="bff",
        return_target_id="registered-target",
        return_nonce=SecretStr(nonce),
    )
    assert nonce not in repr(request)
    assert nonce not in request.model_dump_json()
    assert request.wire_payload()["return_nonce"] == nonce


@pytest.mark.parametrize("clear", [False, True])
def test_ldap_keep_and_clear_are_distinct(clear: bool) -> None:
    values: dict[str, Any] = {
        "name": "employees",
        "kind": "ldap",
        "configuration": {"url": "ldaps://directory.example"},
    }
    if clear:
        values["bind_password"] = None
    provider = AuthenticationProviderInput.model_validate(values)
    definition = provider.wire_payload()["configuration"]
    assert isinstance(definition, dict)
    if clear:
        assert definition["bind_password"] is None
    else:
        assert "bind_password" not in definition


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "local"},
        {"name": " "},
        {"name": "bad\nprivate-name"},
        {"name": "é" * 128},
        {"provider_id": "00000000-0000-0000-0000-000000000000"},
        {"source": "runtime", "configuration": None},
        {"kind": "oidc", "credential": None},
        {"source": "deployment", "configuration": {"url": "ldaps://directory.example"}},
        {"source": "deployment", "configuration": None, "bind_password": None},
        {
            "source": "runtime",
            "configuration": {"url": "ldaps://user:private-password@directory.example"},
        },
        {"configuration": {"url": "ldap://directory.example?private-password"}},
        {
            "configuration": {
                "url": "ldaps://directory.example",
                "bind_password": "private-password",
            }
        },
        {
            "configuration": {
                "url": "ldaps://directory.example",
                "bind_password_ref": "private-ref",
            },
            "bind_password": "private-password",
        },
        {"credential": {"action": "keep"}},
    ],
)
def test_provider_definition_boundaries_are_secret_safe(changes: dict[str, Any]) -> None:
    values = {
        "name": "employees",
        "kind": "ldap",
        "configuration": {"url": "ldaps://directory.example"},
    } | changes
    with pytest.raises(ValidationError) as failed:
        AuthenticationProviderInput.model_validate(values)
    assert "private-" not in str(failed.value)
    assert "private-" not in repr(failed.value.errors())


@pytest.mark.parametrize(
    "values",
    [
        {"group": "authentication", "expected_revision": 0, "providers": []},
        {"group": "authentication", "expected_revision": 1},
        {"group": "authentication", "expected_revision": 1, "providers": [], "backend": "local"},
        {
            "group": "authorization",
            "expected_revision": 1,
            "backend": "treetop",
            "source": "runtime",
        },
        {
            "group": "authorization",
            "expected_revision": 1,
            "backend": "local",
            "source": "runtime",
            "providers": [],
        },
    ],
)
def test_candidate_groups_do_not_accept_incomplete_or_mixed_state(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        SecurityCandidateRequest.model_validate(values)


@pytest.mark.parametrize(
    ("url", "connect", "request_timeout"),
    [
        ("http://policy.example", 1000, 1000),
        ("https://user:private-password@policy.example", 1000, 1000),
        ("https://policy.example?private-password", 1000, 1000),
        ("https://policy.example", 0, 1000),
        ("https://policy.example", 2000, 1000),
        ("https://policy.example", 1000, 30_001),
    ],
)
def test_remote_authorization_requires_tls_and_bounded_timeouts(
    url: str, connect: int, request_timeout: int
) -> None:
    with pytest.raises(ValidationError) as failed:
        RuntimeAuthorizationConnection(
            url=url,
            connect_timeout_ms=connect,
            request_timeout_ms=request_timeout,
            trust_profile_id="system",
        )
    assert "private-" not in str(failed.value)


@pytest.mark.parametrize(
    ("backend", "source"),
    [
        ("local", "runtime"),
        ("local", "deployment"),
        ("treetop", "deployment"),
        ("treetop", "runtime"),
    ],
)
def test_authorization_candidates_serialize_explicit_ownership(backend: str, source: str) -> None:
    connection = (
        RuntimeAuthorizationConnection(url="https://policy.example", trust_profile_id="system")
        if (backend, source) == ("treetop", "runtime")
        else None
    )
    request = SecurityCandidateRequest(
        group="authorization",
        expected_revision=7,
        backend=backend,
        source=source,
        connection=connection,
    )
    body = request.wire_payload()
    assert body["backend"] == backend
    assert body["source"] == source


@pytest.mark.parametrize(
    ("state", "expired", "receipt"),
    [
        ("unverified", False, True),
        ("failed", False, True),
        ("activated", False, True),
        ("verified", True, True),
        ("verified", False, False),
    ],
)
def test_activation_requires_a_current_verified_receipt(
    state: str, expired: bool, receipt: bool
) -> None:
    value: dict[str, Any] = {
        "id": str(uuid4()),
        "group": "authentication",
        "base_revision": 7,
        "checks": [],
        "providers": [],
        "state": state,
        "expires_at": (datetime.now(UTC) + timedelta(minutes=-1 if expired else 5)).isoformat(),
    }
    if receipt:
        value["verification_receipt"] = "hcv1." + "b" * 64
    report = SecurityCandidateReport.model_validate(value)
    with pytest.raises(ValueError, match="unverified, expired or has no activation receipt"):
        report.activation_operation()
