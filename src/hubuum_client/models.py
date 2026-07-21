"""Typed Hubuum v0.0.3 request and response models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

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


class Principal(HubuumModel):
    principal_id: PrincipalId
    name: str
    kind: str | None = None


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
