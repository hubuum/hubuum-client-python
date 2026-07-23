from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hubuum_client import (
    AccessToken,
    ClassCreate,
    Collection,
    CollectionId,
    Credentials,
    HubuumClass,
    TaskStatus,
)
from hubuum_client.models import LoginResponse


def test_response_model_decodes_ids_datetimes_and_forward_fields(
    collection_json: dict[str, object],
) -> None:
    collection_json["future_field"] = "accepted"
    model = Collection.model_validate(collection_json)

    assert model.id == CollectionId(11)
    assert model.created_at == datetime(2026, 7, 21, 10, tzinfo=UTC)
    assert model.model_extra == {"future_field": "accepted"}
    with pytest.raises(ValidationError, match="frozen"):
        model.name = "changed"  # type: ignore[misc]


def test_request_model_is_strict_and_excludes_optional_values() -> None:
    request = ClassCreate(name="server", collection_id=CollectionId(1), description="Servers")

    assert request.payload() == {
        "name": "server",
        "collection_id": 1,
        "description": "Servers",
    }
    with pytest.raises(ValidationError, match="Extra inputs"):
        ClassCreate.model_validate(
            {
                "name": "server",
                "collection_id": 1,
                "description": "Servers",
                "unsupported": True,
            }
        )


def test_class_normalizes_live_embedded_collection() -> None:
    hubuum_class = HubuumClass.model_validate(
        {
            "id": 7,
            "name": "server",
            "description": "Servers",
            "collection": {
                "id": 3,
                "name": "inventory",
                "description": "Inventory",
                "parent_collection_id": None,
                "created_at": "2026-07-21T10:00:00Z",
                "updated_at": "2026-07-21T10:00:00Z",
            },
            "validate_schema": None,
            "created_at": "2026-07-21T10:00:00Z",
            "updated_at": "2026-07-21T10:00:00Z",
        }
    )

    assert hubuum_class.collection_id == CollectionId(3)
    assert hubuum_class.collection is not None
    assert hubuum_class.collection.name == "inventory"
    assert hubuum_class.validate_schema is None


def test_secret_values_are_redacted_but_can_produce_wire_values() -> None:
    credentials = Credentials("alice", "super-secret", "local")
    token = AccessToken("token-secret")

    assert "super-secret" not in repr(credentials)
    assert credentials.as_payload() == {
        "name": "alice",
        "password": "super-secret",
        "identity_scope": "local",
    }
    assert "token-secret" not in repr(token)
    assert "token-secret" not in str(token)
    assert token.value == "token-secret"
    with pytest.raises(ValueError, match="must not be empty"):
        AccessToken(" ")

    login_response = LoginResponse(token="login-token-secret")
    assert "login-token-secret" not in repr(login_response)
    assert login_response.token == "login-token-secret"


@pytest.mark.parametrize(
    ("status", "terminal"),
    [
        (TaskStatus.QUEUED, False),
        (TaskStatus.RUNNING, False),
        (TaskStatus.SUCCEEDED, True),
        (TaskStatus.FAILED, True),
        (TaskStatus.PARTIALLY_SUCCEEDED, True),
        (TaskStatus.CANCELLED, True),
    ],
)
def test_task_terminal_status(status: TaskStatus, terminal: bool) -> None:
    assert status.terminal is terminal
