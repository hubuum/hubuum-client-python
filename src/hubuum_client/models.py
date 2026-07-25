"""Typed Hubuum v0.0.3 request and response models."""

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


class LoginResponse(HubuumModel):
    token: str = Field(repr=False)


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
        """Normalize the live v0.0.3 embedded collection representation."""
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
    # The v0.0.3 runtime returns the scope name while its OpenAPI Group schema
    # declares identity_scope_id. Accept both until the server contract converges.
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
