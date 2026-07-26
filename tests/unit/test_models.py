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
    NewTokenRequest,
    ObjectAggregateMeasureOperation,
    ObjectAggregateMeasureState,
    ObjectAggregateRow,
    Permission,
    PrincipalId,
    PrincipalTokenMetadata,
    TaskStatus,
    TokenId,
    TokenResourceKind,
    TokenResourceScope,
    TokenScope,
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

    with pytest.raises(ValidationError, match="collection_id"):
        HubuumClass.model_validate(
            {
                "id": 7,
                "name": "invalid",
                "description": "No usable collection",
                "collection": {"name": "missing-id"},
                "created_at": "2026-07-21T10:00:00Z",
                "updated_at": "2026-07-21T10:00:00Z",
            }
        )


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
    assert AccessToken("  token-secret\n").value == "token-secret"
    with pytest.raises(ValueError, match="must not be empty"):
        AccessToken(" ")

    login_response = LoginResponse(token="login-token-secret")
    assert "login-token-secret" not in repr(login_response)
    assert login_response.token == "login-token-secret"


def test_v004_token_scope_uses_nested_strict_wire_shape() -> None:
    request = NewTokenRequest(
        name="read-inventory",
        scope=TokenScope(
            permissions=(Permission.READ_COLLECTION, Permission.READ_CLASS),
            resources=(
                TokenResourceScope(kind=TokenResourceKind.COLLECTION, id=11),
                TokenResourceScope(kind=TokenResourceKind.CLASS, id=12),
            ),
        ),
    )

    assert request.payload() == {
        "name": "read-inventory",
        "scope": {
            "permissions": ["ReadCollection", "ReadClass"],
            "resources": [
                {"kind": "collection", "id": 11},
                {"kind": "class", "id": 12},
            ],
        },
    }
    with pytest.raises(ValidationError, match="Extra inputs"):
        NewTokenRequest.model_validate({"scopes": ["ReadCollection"]})
    with pytest.raises(ValidationError, match="at most 1000"):
        TokenScope(
            resources=tuple(
                TokenResourceScope(kind=TokenResourceKind.OBJECT, id=value)
                for value in range(1_001)
            )
        )


def test_v004_token_metadata_and_aggregate_measures_are_typed() -> None:
    metadata = PrincipalTokenMetadata.model_validate(
        {
            "id": 7,
            "principal_id": 21,
            "issued": "2026-07-25T10:00:00Z",
            "scope": {
                "permissions": ["ReadObject"],
                "resources": [{"kind": "object", "id": 13}],
                "future_dimension": True,
            },
        }
    )
    aggregate = ObjectAggregateRow.model_validate(
        {
            "dimensions": [],
            "object_count": 3,
            "measures": [
                {
                    "field": "json_data.metrics,cpu",
                    "operation": "average",
                    "state": "value",
                    "value": 4.5,
                    "value_count": 2,
                    "skipped_count": 1,
                }
            ],
        }
    )

    assert metadata.id == TokenId(7)
    assert metadata.principal_id == PrincipalId(21)
    assert metadata.scope is not None
    assert metadata.scope.model_extra == {"future_dimension": True}
    assert aggregate.measures[0].operation is ObjectAggregateMeasureOperation.AVERAGE
    assert aggregate.measures[0].state is ObjectAggregateMeasureState.VALUE
    assert aggregate.measures[0].value == 4.5


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
