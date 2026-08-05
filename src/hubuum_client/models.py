"""Typed Hubuum request and response models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError, model_validator

from .types import (
    ClassId,
    ClassRelationId,
    CollectionId,
    GroupId,
    ImportResultId,
    ObjectId,
    ObjectRelationId,
    PrincipalId,
    TaskEventId,
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
        """Return the JSON-ready wire representation using declared field aliases."""
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
        )


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
    json_schema: JsonValue | None = Field(default=None, repr=False)
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
    json_schema: JsonValue | None = Field(default=None, repr=False)
    validate_schema: bool | None = None


class ClassUpdate(RequestModel):
    name: str | None = None
    collection_id: CollectionId | None = None
    description: str | None = None
    json_schema: JsonValue | None = Field(default=None, repr=False)
    validate_schema: bool | None = None


class HubuumObject(HubuumModel):
    id: ObjectId
    name: str
    collection_id: CollectionId
    hubuum_class_id: ClassId
    data: JsonValue = Field(repr=False)
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
    data: JsonValue = Field(repr=False)
    description: str
    collection_id: CollectionId | None = None
    hubuum_class_id: ClassId | None = None


class ObjectUpdate(RequestModel):
    name: str | None = None
    data: JsonValue | None = Field(default=None, repr=False)
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
    """Mutable fields accepted when updating a group."""

    groupname: str | None = None


ObjectRelationLimit: TypeAlias = Annotated[int, Field(ge=1)]
"""Positive maximum number of relations allowed on one side of a class relation."""


class ClassRelation(HubuumModel):
    """A class-to-class relation and its optional per-object cardinality limits."""

    id: ClassRelationId
    from_hubuum_class_id: ClassId
    to_hubuum_class_id: ClassId
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None
    created_at: datetime
    updated_at: datetime


class ClassRelationCreate(RequestModel):
    """Create a class relation, optionally bounding either object's relation count.

    ``from_max_relations`` applies independently to each object in the source
    class; ``to_max_relations`` applies independently to each object in the
    destination class. Omit a limit for unlimited cardinality.
    """

    from_hubuum_class_id: ClassId
    to_hubuum_class_id: ClassId
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None


class ObjectRelation(HubuumModel):
    id: ObjectRelationId
    from_hubuum_object_id: ObjectId
    to_hubuum_object_id: ObjectId
    class_relation_id: ClassRelationId
    created_at: datetime
    updated_at: datetime


class ObjectRelationCreate(RequestModel):
    """Create an object relation governed by an existing class relation."""

    from_hubuum_object_id: ObjectId
    to_hubuum_object_id: ObjectId
    class_relation_id: ClassRelationId


class ExportScopeKind(StrEnum):
    """Resource set accepted by Hubuum's export task endpoint."""

    COLLECTIONS = "collections"
    CLASSES = "classes"
    OBJECTS_IN_CLASS = "objects_in_class"
    CLASS_RELATIONS = "class_relations"
    OBJECT_RELATIONS = "object_relations"
    RELATED_OBJECTS = "related_objects"


class ExportScope(RequestModel):
    """Validated resource boundary for an export request.

    Global collection, class, and relation scopes do not accept identifiers.
    ``objects_in_class`` requires only ``class_id``; ``related_objects``
    requires both identifiers.
    """

    kind: ExportScopeKind
    class_id: ClassId | None = Field(default=None, ge=1)
    object_id: ObjectId | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_identifiers(self) -> Self:
        """Reject ambiguous scope/identifier combinations before submission."""
        if self.kind is ExportScopeKind.OBJECTS_IN_CLASS:
            if self.class_id is None:
                raise ValueError("objects_in_class export scope requires class_id")
            if self.object_id is not None:
                raise ValueError("objects_in_class export scope does not accept object_id")
            return self
        if self.kind is ExportScopeKind.RELATED_OBJECTS:
            if self.class_id is None or self.object_id is None:
                raise ValueError("related_objects export scope requires class_id and object_id")
            return self
        if self.class_id is not None or self.object_id is not None:
            raise ValueError(f"{self.kind.value} export scope does not accept identifiers")
        return self


class ExportMissingDataPolicy(StrEnum):
    """How an export handles values missing from an item or template lookup."""

    STRICT = "strict"
    NULL = "null"
    OMIT = "omit"


class ExportLimits(RequestModel):
    """Optional item and output-size limits for one export."""

    max_items: int | None = Field(default=None, ge=0)
    max_output_bytes: int | None = Field(default=None, ge=0)


class ExportIncludeRelatedDirection(StrEnum):
    """Direction used while including related objects in an export."""

    ANY = "any"
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class ExportIncludeRelatedSort(StrEnum):
    """Stable ordering for a related-object export selection."""

    PATH = "path"
    NAME = "name"
    CREATED_AT = "created_at"


class ExportIncludeRelatedObject(RequestModel):
    """One named related-object selection included in an export."""

    class_id: ClassId
    class_relation_id: ClassRelationId | None = None
    direction: ExportIncludeRelatedDirection | None = None
    limit: int | None = None
    max_depth: int | None = None
    sort: ExportIncludeRelatedSort | None = None


class ExportInclude(RequestModel):
    """Additional named data selections included with each exported item."""

    related_objects: dict[str, ExportIncludeRelatedObject] | None = None


class ExportRelationContext(RequestModel):
    """Traversal context applied to relation-oriented exports."""

    depth: int | None = None


class ExportRequest(RequestModel):
    """Typed request submitted to Hubuum's asynchronous export endpoint."""

    scope: ExportScope
    include: ExportInclude | None = None
    limits: ExportLimits | None = None
    missing_data_policy: ExportMissingDataPolicy | None = None
    query: str | None = None
    relation_context: ExportRelationContext | None = None


class ExportContentType(StrEnum):
    """Media types produced by Hubuum's export output endpoint."""

    JSON = "application/json"
    TEXT = "text/plain"
    HTML = "text/html"
    CSV = "text/csv"


class ExportWarning(HubuumModel):
    """One non-fatal problem encountered while producing an export."""

    code: str
    message: str
    path: str | None = None


class ExportMeta(HubuumModel):
    """Metadata accompanying a JSON export document."""

    count: int = Field(ge=0)
    truncated: bool
    scope: ExportScope
    content_type: ExportContentType


class ExportJsonResponse(HubuumModel):
    """Structured output returned for ``application/json`` exports."""

    items: tuple[JsonValue, ...] = Field(repr=False)
    meta: ExportMeta
    warnings: tuple[ExportWarning, ...]


class RestoreTimestamps(RequestModel):
    """Original UTC timestamps restored by an authorized import.

    Hubuum v0.0.8 accepts timezone-free ISO 8601 values and interprets them as
    UTC. The update timestamp must not precede the creation timestamp.
    """

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        """Reject an impossible timestamp order before any network request."""
        if self.created_at.utcoffset() is not None or self.updated_at.utcoffset() is not None:
            raise ValueError("restore timestamps must be timezone-free and are interpreted as UTC")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")
        return self


class CollectionKey(RequestModel):
    """Natural key used to identify a collection inside an import graph."""

    name: str
    path: tuple[str, ...] | None = None


class GroupKey(RequestModel):
    """Natural key used to identify a group inside an import graph."""

    groupname: str
    identity_scope: str | None = None


class ClassKey(RequestModel):
    """Natural key used to identify a class inside an import graph."""

    name: str
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None


class ObjectKey(RequestModel):
    """Natural key used to identify an object inside an import graph."""

    name: str
    class_ref: str | None = None
    class_key: ClassKey | None = None


class ImportCollectionInput(RequestModel):
    """Collection definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    parent_collection_ref: str | None = None
    parent_collection_key: CollectionKey | None = None
    timestamps: RestoreTimestamps | None = None


class ImportClassInput(RequestModel):
    """Class definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    json_schema: JsonValue | None = Field(default=None, repr=False)
    validate_schema: bool | None = None
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    timestamps: RestoreTimestamps | None = None


class ImportObjectInput(RequestModel):
    """Object definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    data: JsonValue = Field(repr=False)
    class_ref: str | None = None
    class_key: ClassKey | None = None
    timestamps: RestoreTimestamps | None = None


class ImportClassRelationInput(RequestModel):
    """Class relation definition, including v0.0.8 cardinality and timestamps."""

    ref_: str | None = Field(default=None, alias="ref")
    from_class_ref: str | None = None
    from_class_key: ClassKey | None = None
    to_class_ref: str | None = None
    to_class_key: ClassKey | None = None
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None
    timestamps: RestoreTimestamps | None = None


class ImportObjectRelationInput(RequestModel):
    """Object relation definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    from_object_ref: str | None = None
    from_object_key: ObjectKey | None = None
    to_object_ref: str | None = None
    to_object_key: ObjectKey | None = None
    timestamps: RestoreTimestamps | None = None


class ImportCollectionPermissionInput(RequestModel):
    """Collection permissions granted to a naturally identified group."""

    ref_: str | None = Field(default=None, alias="ref")
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    group_key: GroupKey
    permissions: tuple[Permission, ...]
    replace_existing: bool | None = None


class ImportAtomicity(StrEnum):
    """Transaction boundary used while applying an import."""

    STRICT = "strict"
    BEST_EFFORT = "best_effort"


class ImportCollisionPolicy(StrEnum):
    """Behavior when an imported natural key already exists."""

    ABORT = "abort"
    OVERWRITE = "overwrite"


class ImportPermissionPolicy(StrEnum):
    """Behavior after a permission failure in a best-effort import."""

    ABORT = "abort"
    CONTINUE = "continue"


class ImportMode(RequestModel):
    """Optional atomicity, collision, and permission controls for an import."""

    atomicity: ImportAtomicity | None = None
    collision_policy: ImportCollisionPolicy | None = None
    permission_policy: ImportPermissionPolicy | None = None


class ImportGraph(RequestModel):
    """Complete import graph with typed core resources.

    Identity and integration sections remain JSON-object sequences so the
    complete v0.0.8 graph is accepted without exposing unstable or
    secret-bearing integration configuration in representations. Core
    collection, class, object, relation, and collection-permission sections
    are fully typed.
    """

    collections: tuple[ImportCollectionInput, ...] = ()
    classes: tuple[ImportClassInput, ...] = ()
    objects: tuple[ImportObjectInput, ...] = Field(default=(), repr=False)
    class_relations: tuple[ImportClassRelationInput, ...] = ()
    object_relations: tuple[ImportObjectRelationInput, ...] = ()
    identity_scopes: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    groups: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    principals: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    group_memberships: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    collection_permissions: tuple[ImportCollectionPermissionInput, ...] = ()
    export_templates: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    remote_targets: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    event_sinks: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)
    event_subscriptions: tuple[dict[str, JsonValue], ...] = Field(default=(), repr=False)

    @property
    def total_items(self) -> int:
        """Return the number of top-level entities submitted by this graph."""
        return sum(
            len(items)
            for items in (
                self.collections,
                self.classes,
                self.objects,
                self.class_relations,
                self.object_relations,
                self.identity_scopes,
                self.groups,
                self.principals,
                self.group_memberships,
                self.collection_permissions,
                self.export_templates,
                self.remote_targets,
                self.event_sinks,
                self.event_subscriptions,
            )
        )


CURRENT_IMPORT_VERSION: Literal[1] = 1


class ImportRequest(RequestModel):
    """Versioned asynchronous import request for the complete Hubuum graph."""

    graph: ImportGraph = Field(repr=False)
    version: Literal[1] = CURRENT_IMPORT_VERSION
    dry_run: bool | None = None
    mode: ImportMode | None = None

    def payload(self) -> dict[str, Any]:
        """Return the wire payload, always including the required format version."""
        value = super().payload()
        value["version"] = self.version
        return value


class ImportTaskResult(HubuumModel):
    """Outcome for one entity processed by an import task."""

    id: ImportResultId
    task_id: TaskId
    entity_kind: str
    action: str
    outcome: str
    created_at: datetime
    identifier: str | None = None
    item_ref: str | None = None
    error: str | None = Field(default=None, repr=False)
    details: JsonValue | None = Field(default=None, repr=False)


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
    """Lifecycle state reported for an asynchronous Hubuum task."""

    QUEUED = "queued"
    VALIDATING = "validating"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        """Return whether the task will perform no further work."""
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.PARTIALLY_SUCCEEDED,
            TaskStatus.CANCELLED,
        }

    @property
    def successful(self) -> bool:
        """Return whether the terminal task produced usable results."""
        return self in {TaskStatus.SUCCEEDED, TaskStatus.PARTIALLY_SUCCEEDED}


class TaskKind(StrEnum):
    """Operation category executed by Hubuum's task workers."""

    IMPORT = "import"
    EXPORT = "export"
    BACKUP = "backup"
    REINDEX = "reindex"
    REMOTE_CALL = "remote_call"


class TaskProgress(HubuumModel):
    """Typed item counters reported by an asynchronous task."""

    total_items: int
    processed_items: int
    success_items: int
    failed_items: int


class TaskLinks(HubuumModel):
    """Server-provided relative links associated with a task."""

    task: str
    events: str
    import_: str | None = Field(default=None, alias="import", repr=False)
    import_results: str | None = Field(default=None, repr=False)
    export: str | None = Field(default=None, repr=False)
    export_output: str | None = Field(default=None, repr=False)
    backup: str | None = Field(default=None, repr=False)
    backup_output: str | None = Field(default=None, repr=False)


class ImportTaskDetails(HubuumModel):
    """Import-specific task metadata."""

    results_url: str = Field(repr=False)


class ExportTaskDetails(HubuumModel):
    """Export output state and v0.0.8 phase-duration measurements."""

    output_url: str = Field(repr=False)
    output_available: bool
    output_expired: bool
    output_content_type: str | None = None
    output_expires_at: datetime | None = None
    template_name: str | None = None
    truncated: bool | None = None
    warning_count: int | None = None
    total_duration_ms: int | None = None
    query_duration_ms: int | None = None
    hydration_duration_ms: int | None = None
    render_duration_ms: int | None = None


class BackupTaskDetails(HubuumModel):
    """Backup output state attached to a generic task response."""

    output_url: str = Field(repr=False)
    output_available: bool
    output_expired: bool
    byte_size: int | None = None
    output_expires_at: datetime | None = None
    sha256: str | None = None


class TaskDetails(HubuumModel):
    """Kind-specific task metadata exposed by Hubuum v0.0.8."""

    import_: ImportTaskDetails | None = Field(default=None, alias="import")
    export: ExportTaskDetails | None = None
    backup: BackupTaskDetails | None = None


class Task(HubuumModel):
    """Generic asynchronous task with typed progress, links, and details."""

    id: TaskId
    kind: TaskKind
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    submitted_by: PrincipalId | None = None
    summary: str | None = Field(default=None, repr=False)
    request_redacted_at: datetime | None = None
    progress: TaskProgress
    links: TaskLinks = Field(repr=False)
    details: TaskDetails | None = Field(default=None, repr=False)


class TaskEvent(HubuumModel):
    """One event in a task's cursor-paginated lifecycle history."""

    id: TaskEventId
    task_id: TaskId
    event_type: str
    message: str
    created_at: datetime
    provenance: Provenance
    data: JsonValue | None = Field(default=None, repr=False)


class ProvenancePrincipal(HubuumModel):
    """Durable principal identity attached to provenance records."""

    principal_id: PrincipalId
    name: str | None = None


class ProvenanceActor(HubuumModel):
    """Immediate actor that performed a mutation or task operation."""

    kind: str | None = None
    principal: ProvenancePrincipal | None = None


class Provenance(HubuumModel):
    """Shared actor, initiator, and root-task provenance."""

    actor: ProvenanceActor
    initiator: ProvenancePrincipal | None = None
    task_id: TaskId | None = None


@dataclass(frozen=True, slots=True)
class RenderedExport:
    """Non-JSON export output and the media type selected by the server."""

    content_type: ExportContentType
    body: str = dataclass_field(repr=False)


ExportOutput: TypeAlias = ExportJsonResponse | RenderedExport
"""Fully typed JSON output or rendered text returned by an export task."""


@dataclass(frozen=True, slots=True)
class ImportRunResult:
    """Terminal import task and its per-entity result rows."""

    task: Task
    results: tuple[ImportTaskResult, ...] = dataclass_field(repr=False)

    @property
    def succeeded(self) -> int:
        """Return the number of successful entity outcomes."""
        return sum(result.outcome == "succeeded" for result in self.results)

    @property
    def failed(self) -> int:
        """Return the number of unsuccessful entity outcomes."""
        return len(self.results) - self.succeeded


class ApiErrorResponse(HubuumModel):
    error: str
    message: str
