"""Typed Hubuum request and response models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError, model_validator

from .types import (
    ClassId,
    ClassRelationId,
    CollectionId,
    GroupId,
    ObjectId,
    ObjectRelationId,
    PrincipalId,
    TaskId,
    TokenId,
    UserId,
)


class HubuumModel(BaseModel):
    """Forward-compatible base for server responses."""

    model_config = ConfigDict(extra="allow", frozen=True, populate_by_name=True)


class RequestModel(BaseModel):
    """Strict base for request payloads."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude_unset=True)


class ProbeResponse(HubuumModel):
    status: str
    message: str | None = None


class ClientAuthenticationConfig(HubuumModel):
    """Public authentication settings needed by API consumers."""

    default_token_lifetime_hours: int = Field(ge=1)


class ClientPaginationConfig(HubuumModel):
    """Effective pagination settings exposed by the server."""

    default_page_limit: int = Field(ge=1)
    max_page_limit: int = Field(ge=1)


class ClientConfig(HubuumModel):
    """Public client-safe server configuration."""

    authentication: ClientAuthenticationConfig
    pagination: ClientPaginationConfig


class LoginResponse(HubuumModel):
    token: str = Field(repr=False)
    expires_at: datetime


class Collection(HubuumModel):
    id: CollectionId
    name: str
    description: str
    parent_collection_id: CollectionId | None = None
    created_at: datetime
    updated_at: datetime


class CollectionCreate(RequestModel):
    name: str
    description: str
    group_id: GroupId
    parent_collection_id: CollectionId | None = None


class CollectionUpdate(RequestModel):
    name: str | None = None
    description: str | None = None


class HubuumClass(HubuumModel):
    id: ClassId
    name: str
    collection_id: CollectionId
    collection: Collection | None = None
    validate_schema: bool | None = None
    description: str
    json_schema: JsonValue | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def normalize_runtime_collection(cls, value: Any) -> Any:
        """Normalize the server's embedded collection representation."""
        if not isinstance(value, dict) or "collection_id" in value:
            return value
        collection = value.get("collection")
        if not isinstance(collection, dict) or "id" not in collection:
            return value
        normalized = dict(value)
        normalized["collection_id"] = collection["id"]
        return normalized


class ClassCreate(RequestModel):
    name: str
    collection_id: CollectionId
    description: str
    json_schema: JsonValue | None = None
    validate_schema: bool | None = None


class ClassUpdate(RequestModel):
    name: str | None = None
    collection_id: CollectionId | None = None
    description: str | None = None
    json_schema: JsonValue | None = None
    validate_schema: bool | None = None


class HubuumObject(HubuumModel):
    id: ObjectId
    name: str
    collection_id: CollectionId
    hubuum_class_id: ClassId
    data: JsonValue
    description: str
    created_at: datetime
    updated_at: datetime


class ObjectAggregateValueState(StrEnum):
    VALUE = "value"
    NULL = "null"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"


class ObjectAggregateMeasureOperation(StrEnum):
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"


class ObjectAggregateMeasureState(StrEnum):
    VALUE = "value"
    EMPTY = "empty"


class ObjectAggregateDimensionValue(HubuumModel):
    field: str
    state: ObjectAggregateValueState
    value: JsonValue | None = None


class ObjectAggregateMeasureValue(HubuumModel):
    field: str
    operation: ObjectAggregateMeasureOperation
    state: ObjectAggregateMeasureState
    value_count: int
    skipped_count: int
    value: JsonValue | None = None


class ObjectAggregateRow(HubuumModel):
    dimensions: tuple[ObjectAggregateDimensionValue, ...]
    object_count: int
    measures: tuple[ObjectAggregateMeasureValue, ...] = ()


class ObjectCreate(RequestModel):
    name: str
    data: JsonValue
    description: str
    collection_id: CollectionId | None = None
    hubuum_class_id: ClassId | None = None


class ObjectUpdate(RequestModel):
    name: str | None = None
    data: JsonValue | None = None
    description: str | None = None
    collection_id: CollectionId | None = None
    hubuum_class_id: ClassId | None = None


class ObjectDataPatchOperation(RequestModel):
    """One validated RFC 6902 operation relative to an object's ``data`` root."""

    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str
    from_path: str | None = Field(default=None, alias="from")
    value: JsonValue | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_operation_members(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        operation = value.get("op")
        has_from = "from" in value or "from_path" in value
        has_value = "value" in value
        if operation in {"add", "replace", "test"} and not has_value:
            raise ValueError("add, replace, and test operations require value")
        if operation in {"move", "copy"} and not has_from:
            raise ValueError("move and copy operations require from")
        if operation not in {"move", "copy"} and has_from:
            raise ValueError("from is only valid for move and copy operations")
        if operation not in {"add", "replace", "test"} and has_value:
            raise ValueError("value is only valid for add, replace, and test operations")
        return value

    def payload(self) -> dict[str, Any]:
        """Keep explicit JSON-null values while omitting unused operation members."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)


ObjectDataPatchInput: TypeAlias = ObjectDataPatchOperation | Mapping[str, Any]
_MAX_OBJECT_DATA_PATCH_OPERATIONS = 1_000


def _object_data_patch_payload(
    operations: Sequence[ObjectDataPatchInput],
) -> list[dict[str, Any]]:
    if len(operations) > _MAX_OBJECT_DATA_PATCH_OPERATIONS:
        raise ValueError("object data patch must not contain more than 1000 operations")
    result: list[dict[str, Any]] = []
    for index, operation in enumerate(operations):
        try:
            parsed = ObjectDataPatchOperation.model_validate(operation)
        except ValidationError as error:
            details = error.errors(include_input=False, include_url=False)
            raise ValueError(
                f"invalid object data patch operation at index {index}: {details}"
            ) from None
        result.append(parsed.payload())
    return result


class User(HubuumModel):
    id: UserId
    identity_scope: str
    provider_kind: str
    provider_managed: bool
    name: str
    email: str | None = None
    proper_name: str | None = None
    created_at: datetime
    updated_at: datetime
    last_sync_attempted_at: datetime | None = None
    last_sync_success_at: datetime | None = None


class UserCreate(RequestModel):
    name: str
    password: str = Field(repr=False)
    identity_scope: str | None = None
    email: str | None = None
    proper_name: str | None = None


class UserUpdate(RequestModel):
    password: str | None = Field(default=None, repr=False)
    email: str | None = None
    proper_name: str | None = None


class Group(HubuumModel):
    id: GroupId
    groupname: str
    description: str
    # The runtime can return the scope name while OpenAPI declares
    # identity_scope_id. Accept both until the server contract converges.
    identity_scope: str | None = None
    identity_scope_id: int | None = None
    managed_by: str
    external_key: str | None = None
    created_at: datetime
    updated_at: datetime
    last_sync_attempted_at: datetime | None = None
    last_sync_success_at: datetime | None = None


class GroupCreate(RequestModel):
    groupname: str
    description: str | None = None
    identity_scope: str | None = None


class GroupUpdate(RequestModel):
    groupname: str | None = None


class ClassRelation(HubuumModel):
    id: ClassRelationId
    from_hubuum_class_id: ClassId
    to_hubuum_class_id: ClassId
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    created_at: datetime
    updated_at: datetime


class ClassRelationCreate(RequestModel):
    from_hubuum_class_id: ClassId
    to_hubuum_class_id: ClassId
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None


class ObjectRelation(HubuumModel):
    id: ObjectRelationId
    from_hubuum_object_id: ObjectId
    to_hubuum_object_id: ObjectId
    class_relation_id: ClassRelationId
    created_at: datetime
    updated_at: datetime


class ObjectRelationCreate(RequestModel):
    from_hubuum_object_id: ObjectId
    to_hubuum_object_id: ObjectId
    class_relation_id: ClassRelationId


class PrincipalMember(HubuumModel):
    principal_id: PrincipalId
    identity_scope: str
    kind: str
    name: str
    created_at: datetime
    updated_at: datetime


class Permission(StrEnum):
    READ_COLLECTION = "ReadCollection"
    UPDATE_COLLECTION = "UpdateCollection"
    DELETE_COLLECTION = "DeleteCollection"
    DELEGATE_COLLECTION = "DelegateCollection"
    CREATE_CLASS = "CreateClass"
    READ_CLASS = "ReadClass"
    UPDATE_CLASS = "UpdateClass"
    DELETE_CLASS = "DeleteClass"
    CREATE_OBJECT = "CreateObject"
    READ_OBJECT = "ReadObject"
    UPDATE_OBJECT = "UpdateObject"
    DELETE_OBJECT = "DeleteObject"
    CREATE_CLASS_RELATION = "CreateClassRelation"
    READ_CLASS_RELATION = "ReadClassRelation"
    UPDATE_CLASS_RELATION = "UpdateClassRelation"
    DELETE_CLASS_RELATION = "DeleteClassRelation"
    CREATE_OBJECT_RELATION = "CreateObjectRelation"
    READ_OBJECT_RELATION = "ReadObjectRelation"
    UPDATE_OBJECT_RELATION = "UpdateObjectRelation"
    DELETE_OBJECT_RELATION = "DeleteObjectRelation"
    READ_TEMPLATE = "ReadTemplate"
    CREATE_TEMPLATE = "CreateTemplate"
    UPDATE_TEMPLATE = "UpdateTemplate"
    DELETE_TEMPLATE = "DeleteTemplate"
    READ_REMOTE_TARGET = "ReadRemoteTarget"
    CREATE_REMOTE_TARGET = "CreateRemoteTarget"
    UPDATE_REMOTE_TARGET = "UpdateRemoteTarget"
    DELETE_REMOTE_TARGET = "DeleteRemoteTarget"
    EXECUTE_REMOTE_TARGET = "ExecuteRemoteTarget"
    READ_AUDIT = "ReadAudit"
    MANAGE_EVENT_SUBSCRIPTION = "ManageEventSubscription"


class TokenResourceKind(StrEnum):
    COLLECTION = "collection"
    CLASS = "class"
    OBJECT = "object"


class TokenResourceScope(RequestModel):
    """One collection, class, or object included in a token boundary."""

    kind: TokenResourceKind
    id: int


class TokenScope(RequestModel):
    """Independent permission and resource boundaries for a newly minted token."""

    permissions: tuple[Permission, ...] | None = None
    resources: tuple[TokenResourceScope, ...] | None = Field(default=None, max_length=1_000)


class NewTokenRequest(RequestModel):
    """Hubuum v0.0.5 token-mint request using the nested ``scope`` wire field."""

    description: str | None = None
    expires_at: datetime | None = None
    name: str | None = None
    scope: TokenScope | None = None


class TokenResourceScopeDetails(HubuumModel):
    """One resource returned in token scope metadata."""

    kind: TokenResourceKind
    id: int


class TokenScopeDetails(HubuumModel):
    """Exact permission and resource dimensions returned for a scoped token."""

    permissions: tuple[Permission, ...] | None = None
    resources: tuple[TokenResourceScopeDetails, ...] | None = None


class CurrentTokenMetadata(HubuumModel):
    id: TokenId
    issued: datetime
    description: str | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    name: str | None = None
    revoked_at: datetime | None = None
    scope: TokenScopeDetails | None = None


class PrincipalTokenMetadata(CurrentTokenMetadata):
    principal_id: PrincipalId


class MeResponse(HubuumModel):
    principal: PrincipalMember
    token: CurrentTokenMetadata


class TaskStatus(StrEnum):
    QUEUED = "queued"
    VALIDATING = "validating"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.PARTIALLY_SUCCEEDED,
            TaskStatus.CANCELLED,
        }


class Task(HubuumModel):
    id: TaskId
    kind: str
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    submitted_by: PrincipalId | None = None
    summary: str | None = None
    progress: dict[str, JsonValue]
    links: dict[str, JsonValue]
    details: JsonValue | None = None


class ApiErrorResponse(HubuumModel):
    error: str
    message: str
