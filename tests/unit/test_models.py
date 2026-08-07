from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hubuum_client import (
    AccessToken,
    ClassCreate,
    ClassId,
    ClassRelationCreate,
    Collection,
    CollectionId,
    Credentials,
    ExportContentType,
    ExportRequest,
    ExportScope,
    ExportScopeKind,
    GroupKey,
    HubuumClass,
    ImportCollectionPermissionInput,
    ImportGraph,
    ImportObjectInput,
    ImportRequest,
    ImportWriteCondition,
    ImportWriteMode,
    NewTokenRequest,
    ObjectAggregateMeasureOperation,
    ObjectAggregateMeasureState,
    ObjectAggregateRow,
    Permission,
    PrincipalId,
    PrincipalTokenMetadata,
    RenderedExport,
    RestoreTimestamps,
    Task,
    TaskStatus,
    TaskUnsuccessfulError,
    TokenId,
    TokenResourceKind,
    TokenResourceScope,
    TokenScope,
    User,
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
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        Collection.model_validate(collection_json | {"revision": 0})


def test_v009_user_point_shape_uses_stable_identity_scope_id() -> None:
    user = User.model_validate(
        {
            "id": 21,
            "identity_scope_id": 1,
            "provider_managed": False,
            "name": "alice",
            "email": "alice@example.com",
            "proper_name": "Alice",
            "created_at": "2026-08-07T10:00:00Z",
            "updated_at": "2026-08-07T10:00:00Z",
            "revision": 3,
        }
    )

    assert user.identity_scope_id == 1
    assert user.identity_scope is None
    assert user.provider_kind is None
    assert user.revision == 3


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
                "revision": 1,
            },
            "validate_schema": None,
            "created_at": "2026-07-21T10:00:00Z",
            "updated_at": "2026-07-21T10:00:00Z",
            "revision": 1,
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
                "revision": 1,
            }
        )


def test_secret_values_are_redacted_but_can_produce_wire_values() -> None:
    credentials = Credentials("alice", "super-secret", "local")
    expiry = datetime(2026, 7, 27, 12, tzinfo=UTC)
    token = AccessToken("token-secret", expires_at=expiry)

    assert "super-secret" not in repr(credentials)
    assert credentials.as_payload() == {
        "name": "alice",
        "password": "super-secret",
        "identity_scope": "local",
    }
    assert "token-secret" not in repr(token)
    assert "token-secret" not in str(token)
    assert token.value == "token-secret"
    assert token.expires_at == expiry
    assert AccessToken("  token-secret\n").value == "token-secret"
    with pytest.raises(ValueError, match="must not be empty"):
        AccessToken(" ")
    with pytest.raises(ValueError, match="login name"):
        Credentials("x" * 256, "secret")
    with pytest.raises(ValueError, match="login password"):
        Credentials("alice", "x" * 4_097)
    with pytest.raises(ValueError, match="identity scope"):
        Credentials("alice", "secret", "x" * 256)

    login_response = LoginResponse(
        token="login-token-secret",
        expires_at="2026-07-27T12:00:00Z",
    )
    assert "login-token-secret" not in repr(login_response)
    assert login_response.token == "login-token-secret"
    assert login_response.expires_at == expiry


def test_v005_token_scope_uses_nested_strict_wire_shape() -> None:
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


def test_v005_token_metadata_and_aggregate_measures_are_typed() -> None:
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
            "active": True,
            "expired": False,
            "revision": 1,
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
    ("status", "terminal", "successful"),
    [
        (TaskStatus.QUEUED, False, False),
        (TaskStatus.RUNNING, False, False),
        (TaskStatus.SUCCEEDED, True, True),
        (TaskStatus.FAILED, True, False),
        (TaskStatus.PARTIALLY_SUCCEEDED, True, True),
        (TaskStatus.CANCELLED, True, False),
    ],
)
def test_task_status_properties(status: TaskStatus, terminal: bool, successful: bool) -> None:
    assert status.terminal is terminal
    assert status.successful is successful


def test_v009_import_v2_conditions_and_timestamps_use_wire_names() -> None:
    timestamps = RestoreTimestamps(
        created_at=datetime(2024, 1, 2, 3, 4, 5),
        updated_at=datetime(2024, 1, 2, 3, 4, 6),
    )
    request = ImportRequest(
        graph=ImportGraph(
            objects=(
                ImportObjectInput(
                    ref_="object-1",
                    name="server-1",
                    description="Server",
                    data={"credential": "never-show-this"},
                    class_ref="class-1",
                    timestamps=timestamps,
                    condition=ImportWriteCondition(
                        mode=ImportWriteMode.IF_REVISION,
                        expected_revision=7,
                    ),
                ),
            ),
            collection_permissions=(
                ImportCollectionPermissionInput(
                    ref_="permission-1",
                    collection_ref="collection-1",
                    group_key=GroupKey(groupname="admin"),
                    permissions=(Permission.READ_COLLECTION,),
                ),
            ),
        )
    )
    relation = ClassRelationCreate(
        from_hubuum_class_id=ClassId(1),
        to_hubuum_class_id=ClassId(2),
        from_max_relations=1,
        to_max_relations=2,
    )

    assert relation.payload()["from_max_relations"] == 1
    assert request.payload()["version"] == 2
    assert request.payload()["graph"]["objects"][0]["ref"] == "object-1"
    assert request.payload()["graph"]["collection_permissions"][0] == {
        "ref": "permission-1",
        "collection_ref": "collection-1",
        "group_key": {"groupname": "admin"},
        "permissions": ["ReadCollection"],
    }
    assert request.payload()["graph"]["objects"][0]["timestamps"] == {
        "created_at": "2024-01-02T03:04:05",
        "updated_at": "2024-01-02T03:04:06",
    }
    assert request.payload()["graph"]["objects"][0]["condition"] == {
        "mode": "if_revision",
        "expected_revision": 7,
    }
    assert "never-show-this" not in repr(request)
    with pytest.raises(ValidationError, match="requires expected_revision"):
        ImportWriteCondition(mode=ImportWriteMode.IF_REVISION)
    with pytest.raises(ValidationError, match="only valid for if_revision"):
        ImportWriteCondition(
            mode=ImportWriteMode.CREATE_ONLY,
            expected_revision=1,
        )
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        ClassRelationCreate(
            from_hubuum_class_id=ClassId(1),
            to_hubuum_class_id=ClassId(2),
            from_max_relations=0,
        )


def test_v009_timestamp_and_export_scope_validation_happens_before_io() -> None:
    with pytest.raises(ValidationError, match="updated_at must not be earlier"):
        RestoreTimestamps(
            created_at=datetime(2024, 1, 2),
            updated_at=datetime(2024, 1, 1),
        )
    with pytest.raises(ValidationError, match="must be timezone-free"):
        RestoreTimestamps(
            created_at=datetime(2024, 1, 2, tzinfo=UTC),
            updated_at=datetime(2024, 1, 3, tzinfo=UTC),
        )
    with pytest.raises(ValidationError, match="requires class_id"):
        ExportScope(kind=ExportScopeKind.OBJECTS_IN_CLASS)
    with pytest.raises(ValidationError, match="does not accept identifiers"):
        ExportScope(kind=ExportScopeKind.COLLECTIONS, class_id=ClassId(1))

    export = ExportRequest(
        scope=ExportScope(
            kind=ExportScopeKind.RELATED_OBJECTS,
            class_id=ClassId(1),
            object_id=2,
        )
    )
    assert export.payload()["scope"] == {
        "kind": "related_objects",
        "class_id": 1,
        "object_id": 2,
    }


def test_task_and_export_diagnostics_do_not_expose_content() -> None:
    task = Task.model_validate(
        {
            "id": 40,
            "kind": "import",
            "status": "failed",
            "created_at": "2026-07-21T10:00:00Z",
            "summary": "submitted-data-secret",
            "progress": {
                "total_items": 1,
                "processed_items": 1,
                "success_items": 0,
                "failed_items": 1,
            },
            "links": {
                "task": "/api/v1/tasks/40",
                "events": "/api/v1/tasks/40/events",
            },
        }
    )
    rendered = RenderedExport(content_type=ExportContentType.TEXT, body="export-body-secret")
    error = TaskUnsuccessfulError(40, task.status.value)

    assert "submitted-data-secret" not in repr(task)
    assert "export-body-secret" not in repr(rendered)
    assert "submitted-data-secret" not in str(error)
