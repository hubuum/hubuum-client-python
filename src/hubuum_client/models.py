"""Typed Hubuum request and response models."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, Self, TypeAlias, TypeVar, cast
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ModelWrapValidatorHandler,
    RootModel,
    SecretStr,
    ValidationError,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from .types import (
    ClassId,
    ClassRelationId,
    CollectionId,
    CredentialApprovalId,
    CredentialApprovalSecret,
    EventSinkId,
    EventSubscriptionId,
    GroupId,
    ImportResultId,
    ObjectId,
    ObjectRelationId,
    PrincipalId,
    ResourceRevision,
    RestoreJobId,
    SchemaRevision,
    ServiceAccountId,
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


_APIModelT = TypeVar("_APIModelT", bound=BaseModel)
_APIValueT = TypeVar("_APIValueT")


def _api_validation_error(model: type[BaseModel]) -> ValidationError:
    return ValidationError.from_exception_data(
        model.__name__,
        [
            {
                "type": PydanticCustomError("api_model", "Invalid API model"),
                "loc": (),
                "input": "<redacted>",
            }
        ],
        hide_input=True,
    )


def _validate_api_model(
    model: type[_APIModelT], value: Any, handler: ModelWrapValidatorHandler[_APIModelT]
) -> _APIModelT:
    try:
        return handler(value)
    except ValidationError:
        error = _api_validation_error(model)
    # Even a hidden exception context can retain a password-bearing input.
    raise error


def _api_json_default(value: object) -> str:
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError("Unsupported API payload value")


def _api_payload(model: BaseModel) -> JsonValue:
    return cast(
        JsonValue,
        json.loads(
            json.dumps(
                model.model_dump(mode="python", by_alias=True, exclude_unset=True),
                default=_api_json_default,
            )
        ),
    )


class APIModel(BaseModel):
    """Base for exact-contract models, with secret-safe diagnostics.

    ``wire_payload()`` intentionally reveals request secrets for transmission and
    preserves explicit nulls. Ordinary representations omit all field values.
    """

    model_config = ConfigDict(
        extra="allow", frozen=True, populate_by_name=True, hide_input_in_errors=True
    )

    def __repr_args__(self) -> Iterator[tuple[str | None, Any]]:
        return iter(())

    @classmethod
    def _safe_mutation_error(cls, error: ValidationError) -> ValidationError:
        # Frozen-instance guards bypass model validators and can disclose both
        # replacement values and caller-supplied attribute names.
        details: list[InitErrorDetails] = [
            {
                "type": PydanticCustomError(item["type"], "Cannot mutate API model"),
                "loc": item["loc"][:1]
                if item["loc"] and item["loc"][0] in cls.model_fields
                else (),
                "input": "<redacted>",
            }
            for item in error.errors(include_input=False, include_context=False, include_url=False)
        ]
        return ValidationError.from_exception_data(cls.__name__, details, hide_input=True)

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            super().__setattr__(name, value)
        except ValidationError as error:
            safe_error = self._safe_mutation_error(error)
        else:
            return
        # Raise outside the handler so the original input is not retained in context.
        raise safe_error

    def __delattr__(self, name: str) -> None:
        try:
            super().__delattr__(name)
        except ValidationError as error:
            safe_error = self._safe_mutation_error(error)
        else:
            return
        raise safe_error

    @model_validator(mode="wrap")
    @classmethod
    def _safe_validation(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        return _validate_api_model(cls, value, handler)

    def wire_payload(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], _api_payload(self))


@dataclass(frozen=True, slots=True)
class APIResponse(Generic[_APIValueT]):
    """Typed body plus status, pagination, and revision headers."""

    body: _APIValueT = dataclass_field(repr=False)
    status_code: int
    headers: Mapping[str, str] = dataclass_field(repr=False)

    @property
    def next_cursor(self) -> str | None:
        return self.headers.get("x-next-cursor")

    @property
    def total_count(self) -> int | None:
        value = self.headers.get("x-total-count")
        return int(value) if value is not None else None

    @property
    def etag(self) -> str | None:
        return self.headers.get("etag")


@dataclass(frozen=True, slots=True)
class ServerEvent(Generic[_APIValueT]):
    """One named SSE event with a validated, secret-safe payload."""

    event: str
    data: _APIValueT = dataclass_field(repr=False)


class ProbeResponse(HubuumModel):
    status: str
    message: str | None = None


class ClientAuthenticationConfig(HubuumModel):
    """Public authentication settings needed by API consumers."""

    default_token_lifetime_hours: int = Field(ge=1)
    max_token_lifetime_hours: int = Field(ge=1)
    session_access_seconds: int | None = None
    session_idle_seconds: int | None = None
    session_absolute_seconds: int | None = None
    session_retention_seconds: int | None = None


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


class SessionResponse(HubuumModel):
    """Versioned interactive credentials; secret representations and dumps are redacted."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    session_id: UUID
    token_type: Literal["Bearer"]
    access_token: SecretStr = Field(min_length=1, repr=False)
    refresh_token: SecretStr = Field(min_length=1, repr=False)
    access_expires_at: AwareDatetime
    refresh_expires_at: AwareDatetime
    absolute_expires_at: AwareDatetime

    @model_validator(mode="after")
    def valid_deadlines(self) -> Self:
        if self.access_token == self.refresh_token:
            raise ValueError("access and refresh credentials must differ")
        if not self.access_expires_at <= self.refresh_expires_at <= self.absolute_expires_at:
            raise ValueError("session deadlines must be ordered access <= refresh <= absolute")
        return self

    @model_validator(mode="wrap")
    @classmethod
    def redact_validation_errors(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        try:
            return handler(value)
        except ValidationError:
            safe_error = ValidationError.from_exception_data(
                cls.__name__,
                [
                    {
                        "type": PydanticCustomError("session_response", "Invalid session response"),
                        "loc": (),
                        "input": "<redacted>",
                    }
                ],
                hide_input=True,
            )
        raise safe_error


class Collection(HubuumModel):
    id: CollectionId
    name: str
    description: str
    parent_collection_id: CollectionId | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


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
    revision: ResourceRevision

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
    revision: ResourceRevision


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


class _UserBase(HubuumModel):
    """Fields shared by user list and canonical point responses."""

    id: UserId
    provider_managed: bool
    name: str
    email: str | None = None
    proper_name: str | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


class User(_UserBase):
    """User metadata returned by collection endpoints."""

    identity_scope: str
    provider_kind: str
    last_sync_attempted_at: datetime | None = None
    last_sync_success_at: datetime | None = None


class UserPoint(_UserBase):
    """Canonical revision-owned user returned by point mutations and reads."""

    identity_scope_id: int


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


class _ServiceAccountBase(HubuumModel):
    """Service-account lifecycle fields shared by list and point responses."""

    id: ServiceAccountId
    name: str
    description: str
    owner_group_id: GroupId
    created_by: PrincipalId | None = None
    disabled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision

    @property
    def principal_id(self) -> PrincipalId:
        """Return the same identity for principal-token and membership operations."""
        return PrincipalId(self.id)


class ServiceAccount(_ServiceAccountBase):
    """Service-account list record, including its identity-scope name."""

    identity_scope: str


class ServiceAccountPoint(_ServiceAccountBase):
    """Revision-owned point response, including the identity-scope ID."""

    identity_scope_id: int


class ServiceAccountCreate(RequestModel):
    """Create an automation identity owned by a group; no password is accepted."""

    name: str
    owner_group_id: GroupId = Field(ge=1)
    description: str | None = None
    identity_scope: str | None = None


class ServiceAccountUpdate(RequestModel):
    """Edit description or ownership. Use an empty string to clear description."""

    description: str | None = None
    owner_group_id: GroupId | None = None


class GroupPoint(HubuumModel):
    """Canonical revision-owned group returned by point mutations and reads."""

    id: GroupId
    groupname: str
    description: str
    identity_scope: str
    managed_by: str
    external_key: str | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


class Group(GroupPoint):
    """Group metadata returned by collection endpoints."""

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

RelationLabel: TypeAlias = Annotated[str, Field(min_length=1, max_length=128)]
"""Human-facing directional wording, independent of a template alias."""


class ClassRelation(HubuumModel):
    """A class-to-class relation and its optional per-object cardinality limits."""

    id: ClassRelationId
    from_hubuum_class_id: ClassId
    to_hubuum_class_id: ClassId
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    forward_label: RelationLabel | None = None
    reverse_label: RelationLabel | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


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
    forward_label: RelationLabel | None = None
    reverse_label: RelationLabel | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None


class ClassRelationUpdate(RequestModel):
    """Edit directional labels; explicit null clears a label, omission preserves it."""

    forward_label: RelationLabel | None = None
    reverse_label: RelationLabel | None = None

    def payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)


class ObjectRelation(HubuumModel):
    id: ObjectRelationId
    from_hubuum_object_id: ObjectId
    to_hubuum_object_id: ObjectId
    class_relation_id: ClassRelationId
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


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

    Hubuum v0.0.18 accepts timezone-free ISO 8601 values and interprets them as
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


class ImportWriteMode(StrEnum):
    """Per-item collision and revision behavior for Hubuum import v2."""

    CREATE_ONLY = "create_only"
    OVERWRITE = "overwrite"
    IF_REVISION = "if_revision"


class ImportWriteCondition(RequestModel):
    """One import-v2 write condition checked by the queued worker."""

    mode: ImportWriteMode
    expected_revision: ResourceRevision | None = None

    @model_validator(mode="after")
    def validate_expected_revision(self) -> Self:
        if self.mode is ImportWriteMode.IF_REVISION and self.expected_revision is None:
            raise ValueError("if_revision requires expected_revision")
        if self.mode is not ImportWriteMode.IF_REVISION and self.expected_revision is not None:
            raise ValueError("expected_revision is only valid for if_revision")
        return self


class ImportCollectionInput(RequestModel):
    """Collection definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    parent_collection_ref: str | None = None
    parent_collection_key: CollectionKey | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


SchemaActualValue: TypeAlias = Literal["null", "boolean", "number"] | dict[str, dict[str, int]]
"""Redacted diagnostic context: scalar type names or container type/size metadata."""


class ComplianceStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    NOT_REQUIRED = "not_required"


class SchemaActivationPolicy(StrEnum):
    REJECT_INCOMPATIBLE = "reject_incompatible"
    ALLOW_PENDING = "allow_pending"


class SchemaRevisionStatus(StrEnum):
    STAGED = "staged"
    ACTIVE = "active"
    RETIRED = "retired"
    ABANDONED = "abandoned"


class SchemaWorkKind(StrEnum):
    IMPACT = "impact"
    REVALIDATION = "revalidation"


class SchemaWorkStatus(StrEnum):
    RUNNING = "running"
    FAILED = "failed"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class SchemaImpactReadiness(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    INCONCLUSIVE = "inconclusive"


class SchemaDiagnosticOmission(StrEnum):
    ACTUAL_VALUE_REDACTED = "actual_value_redacted"
    INSTANCE_PATH_REDACTED_OR_TOO_LONG = "instance_path_redacted_or_too_long"
    SCHEMA_CONSTRAINT_UNAVAILABLE_OR_TOO_LARGE = "schema_constraint_unavailable_or_too_large"


class SchemaReference(HubuumModel):
    class_id: ClassId
    revision: SchemaRevision


class FieldSource(StrEnum):
    DATA = "data"
    SHARED_COMPUTED = "shared_computed"
    PERSONAL_COMPUTED = "personal_computed"


class ObservedFieldType(StrEnum):
    NULL = "null"
    BOOL = "bool"
    NUMBER = "number"
    STRING = "string"
    ARRAY = "array"
    OBJECT = "object"


class FieldDiscoveryTruncation(StrEnum):
    SAMPLE_LIMIT = "sample_limit"
    CANDIDATE_LIMIT = "candidate_limit"
    DEPTH = "depth"
    WORK_LIMIT = "work_limit"
    FIELD_LIMIT = "field_limit"
    PATH_LIMIT = "path_limit"
    RESPONSE_LIMIT = "response_limit"


class FieldPropertySegment(APIModel):
    """A literal property name, including names containing dots or brackets."""

    kind: Literal["property"]
    name: str


class FieldArrayItemSegment(APIModel):
    """Traversal of every array item, distinct from a literal property name."""

    kind: Literal["array_item"]


FieldPathSegment: TypeAlias = Annotated[
    FieldPropertySegment | FieldArrayItemSegment, Field(discriminator="kind")
]


class DiscoveredField(APIModel):
    """Sample observations; example is a bounded display preview, not raw JSON."""

    field: str
    source: FieldSource
    path: tuple[FieldPathSegment, ...]
    observation_count: int = Field(ge=0)
    object_count: int = Field(ge=0)
    types: dict[ObservedFieldType, int]
    example: str | None = None
    example_truncated: bool
    error_count: int = Field(ge=0)


class ClassFieldInventory(APIModel):
    """Bounded, permission-filtered fields; counts never imply whole-class totals."""

    sampled: bool
    sampled_objects: int = Field(ge=0)
    effective_sample_limit: int
    max_depth: int
    include_containers: bool
    truncation: tuple[FieldDiscoveryTruncation, ...]
    fields: tuple[DiscoveredField, ...]


class SchemaProfilePreset(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    EXPANSIVE = "expansive"


class SchemaProfileRequest(RequestModel):
    """Validated inference controls. Suggestions never activate a schema."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    preset: SchemaProfilePreset = SchemaProfilePreset.BALANCED
    sample_limit: int = Field(default=100, ge=1, le=250, strict=True)


class ProfileSuggestionStatus(StrEnum):
    CANDIDATE = "candidate"
    BLOCKED = "blocked"
    INSUFFICIENT = "insufficient"


class SchemaProfileReport(APIModel):
    """A retained suggestion, available for 24 hours and subject to current access."""

    class_id: ClassId
    sampled: bool
    sampled_objects: int = Field(ge=0)
    effective_sample_limit: int
    truncation: FieldDiscoveryTruncation | None = None
    options: SchemaProfileRequest
    status: ProfileSuggestionStatus
    schema_: JsonValue = Field(default=None, alias="schema")
    profile: JsonValue = None
    findings: tuple[JsonValue, ...]
    replay: JsonValue = None
    sample_valid: bool | None = None

    def stage_request(self, *, validate_schema: bool) -> SchemaStageRequest:
        """Copy a reviewed candidate into a request; whole-class impact is still required."""
        if self.status != ProfileSuggestionStatus.CANDIDATE or self.sample_valid is not True:
            raise ValueError(
                "report has no sample-valid candidate; inspect findings or suggest again"
            )
        if self.schema_ is None:
            raise ValueError("candidate report is missing its schema")
        return SchemaStageRequest(json_schema=self.schema_, validate_schema=validate_schema)


class SchemaStageRequest(RequestModel):
    json_schema: JsonValue = Field(default=None, repr=False)
    validate_schema: bool


class SchemaActivationRequest(RequestModel):
    expected_active_revision: SchemaRevision
    impact_task_id: TaskId | None = None
    policy: SchemaActivationPolicy


class ImportSchemaActivation(RequestModel):
    expected_active_revision: SchemaRevision
    impact_task_id: TaskId | None = None
    policy: SchemaActivationPolicy
    revision: SchemaRevision


class SchemaRepairReportRequest(RequestModel):
    object_url_template: str = Field(repr=False)
    template_id: int | None = Field(default=None, ge=1)


class SchemaRevisionResponse(HubuumModel):
    activated_at: datetime | None = None
    activation_policy: SchemaActivationPolicy | None = None
    class_id: ClassId
    created_at: datetime
    created_by: int | None = None
    json_schema: JsonValue = Field(default=None, repr=False)
    revision: SchemaRevision
    status: SchemaRevisionStatus
    validate_schema: bool


class SchemaActivationResponse(HubuumModel):
    active: SchemaRevisionResponse
    dependent_rebuild_task_id: TaskId | None = None
    task_id: TaskId | None = None


class ObjectSchemaEvidence(HubuumModel):
    object_revision: ResourceRevision
    schema_: SchemaReference = Field(alias="schema")
    valid: bool
    validated_at: datetime


class ObjectComplianceResponse(HubuumModel):
    active_schema: SchemaReference
    evidence: ObjectSchemaEvidence | None = None
    object_id: ObjectId
    object_revision: ResourceRevision
    status: ComplianceStatus


class SchemaComplianceCounts(HubuumModel):
    invalid: int
    not_required: int
    pending: int
    valid: int


class SchemaCompliancePage(HubuumModel):
    items: tuple[ObjectComplianceResponse, ...]
    next_after: int | None = None


class ClassSchemaResponse(HubuumModel):
    active: SchemaRevisionResponse
    counts: SchemaComplianceCounts
    object_epoch: int


class SchemaFailure(HubuumModel):
    keyword: str
    missing_property: str | None = Field(default=None, repr=False)
    schema_path: str | None = Field(default=None, repr=False)


class SchemaFailureGroup(HubuumModel):
    objects: int
    reason: SchemaFailure
    samples: tuple[ObjectId, ...]


class SchemaImpactCounts(HubuumModel):
    newly_invalid: int
    newly_required_valid: int
    newly_valid: int
    no_longer_required: int
    still_invalid: int
    still_valid: int
    unchanged_not_required: int
    uninspectable: int


class SchemaExpectedValue(HubuumModel):
    """Use status to distinguish an available JSON null from an omitted constraint."""

    status: Literal["available", "omitted"]
    value: JsonValue = Field(default=None, repr=False)


class SchemaIssue(HubuumModel):
    actual: SchemaActualValue = Field(repr=False)
    alternative: bool
    expected: SchemaExpectedValue = Field(repr=False)
    instance_path: str | None = Field(default=None, repr=False)
    message: str = Field(repr=False)
    omissions: tuple[SchemaDiagnosticOmission, ...]
    reason: SchemaFailure


class SchemaDiagnostics(HubuumModel):
    issues: tuple[SchemaIssue, ...]
    truncated: bool


class SchemaDiagnosticSnapshotResponse(HubuumModel):
    diagnostics: SchemaDiagnostics
    inspected_at: datetime
    object_revision: ResourceRevision


class SchemaImpactFindingResponse(HubuumModel):
    object_id: ObjectId
    reason: SchemaFailure
    snapshot: SchemaDiagnosticSnapshotResponse | None = None


class SchemaImpactResponse(HubuumModel):
    baseline: SchemaReference
    counts: SchemaImpactCounts
    failures: tuple[SchemaFailureGroup, ...]
    findings: tuple[SchemaImpactFindingResponse, ...] = ()
    ungrouped_failures: int


class SchemaWorkResponse(HubuumModel):
    batches: int
    created_at: datetime
    current_active_schema: SchemaReference | None = None
    current_epoch: int | None = None
    cursor: int
    elapsed_millis: int
    end_epoch: int | None = None
    examined: int
    impact: SchemaImpactResponse | None = None
    invalid: int
    invalid_samples: tuple[ObjectId, ...]
    kind: SchemaWorkKind
    not_required: int
    readiness: SchemaImpactReadiness | None = None
    stale: int
    start_epoch: int
    status: SchemaWorkStatus
    target: SchemaReference
    task_id: TaskId
    uninspectable: int
    upper_bound: int
    valid: int


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
    condition: ImportWriteCondition | None = None
    schema_activation: ImportSchemaActivation | None = None


class ImportObjectInput(RequestModel):
    """Object definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    data: JsonValue = Field(repr=False)
    class_ref: str | None = None
    class_key: ClassKey | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


class ImportClassRelationInput(RequestModel):
    """Class relation definition, including cardinality and import-v2 controls."""

    ref_: str | None = Field(default=None, alias="ref")
    from_class_ref: str | None = None
    from_class_key: ClassKey | None = None
    to_class_ref: str | None = None
    to_class_key: ClassKey | None = None
    forward_template_alias: str | None = None
    reverse_template_alias: str | None = None
    forward_label: RelationLabel | None = None
    reverse_label: RelationLabel | None = None
    from_max_relations: ObjectRelationLimit | None = None
    to_max_relations: ObjectRelationLimit | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


class ImportObjectRelationInput(RequestModel):
    """Object relation definition in a Hubuum import graph."""

    ref_: str | None = Field(default=None, alias="ref")
    from_object_ref: str | None = None
    from_object_key: ObjectKey | None = None
    to_object_ref: str | None = None
    to_object_key: ObjectKey | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


class ImportCollectionPermissionInput(RequestModel):
    """Collection permissions granted to a naturally identified group."""

    ref_: str | None = Field(default=None, alias="ref")
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    group_key: GroupKey
    permissions: tuple[Permission, ...]
    replace_existing: bool | None = None
    condition: ImportWriteCondition | None = None


class _ImportModel(RequestModel):
    """Strict import input with redacted representations and validation failures."""

    model_config = ConfigDict(hide_input_in_errors=True)

    def __repr_args__(self) -> Iterator[tuple[str | None, Any]]:
        return iter(())

    @model_validator(mode="wrap")
    @classmethod
    def _safe_validation(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        try:
            return handler(value)._validate_import()
        except (ValidationError, ValueError):
            error = _api_validation_error(cls)
        raise error

    def _validate_import(self) -> Self:
        # Keep selector checks inside the wrapper so Pydantic cannot attach the
        # original import body to an error raised by a subclass validator.
        return self

    @classmethod
    def model_validate_json(cls, json_data: str | bytes | bytearray, **kwargs: Any) -> Self:
        try:
            return super().model_validate_json(json_data, **kwargs)
        except ValidationError:
            error = _api_validation_error(cls)
        raise error

    def payload(self) -> dict[str, Any]:
        """Return wire fields, preserving explicitly supplied JSON nulls."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)


def _import_selector(
    reference: str | None, key: RequestModel | None, *, required: bool = True
) -> None:
    if reference is not None and key is not None:
        raise ValueError("reference and natural key are mutually exclusive")
    if required and reference is None and key is None:
        raise ValueError("a reference or natural key is required")


def _import_class_selector(
    reference: str | None, key: ClassKey | None, *, required: bool = False
) -> None:
    _import_selector(reference, key, required=required)
    if key is not None:
        _import_selector(key.collection_ref, key.collection_key)


class IdentityScopeKey(_ImportModel):
    """Natural key of an imported or existing identity scope."""

    name: str


class PrincipalKey(_ImportModel):
    """Principal name, optionally qualified by its identity scope."""

    name: str
    identity_scope: str | None = None


class EventSinkKey(_ImportModel):
    """Natural key of an existing event sink."""

    name: str


class ImportIdentityScopeInput(_ImportModel):
    """Identity scope definition in an administrator import."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    provider_kind: str
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


class ImportGroupInput(_ImportModel):
    """Group definition, with exactly one identity-scope selector."""

    ref_: str | None = Field(default=None, alias="ref")
    groupname: str
    description: str
    managed_by: str
    identity_scope_ref: str | None = None
    identity_scope_key: IdentityScopeKey | None = None
    external_key: str | None = None
    last_sync_attempted_at: datetime | None = None
    last_sync_success_at: datetime | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.identity_scope_ref, self.identity_scope_key)
        return self


class _ImportPrincipalInput(_ImportModel):
    ref_: str | None = Field(default=None, alias="ref")
    name: str
    provider_managed: bool
    identity_scope_ref: str | None = None
    identity_scope_key: IdentityScopeKey | None = None
    external_subject: str | None = None
    settings: JsonValue = None
    last_sync_attempted_at: datetime | None = None
    last_sync_success_at: datetime | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.identity_scope_ref, self.identity_scope_key)
        return self


class ImportPrincipalInputHuman(_ImportPrincipalInput):
    """Human principal; credentials require an import_credentials approval."""

    kind: Literal["human"]
    email: str | None = None
    proper_name: str | None = None
    password: str | None = None
    password_hash: str | None = None
    anonymized_at: datetime | None = None

    def _validate_import(self) -> Self:
        super()._validate_import()
        if self.password is not None and self.password_hash is not None:
            raise ValueError("password and password_hash are mutually exclusive")
        return self


class ImportPrincipalInputServiceAccount(_ImportPrincipalInput):
    """Service account with an owner group and optional creator selector."""

    kind: Literal["service_account"]
    description: str
    owner_group_ref: str | None = None
    owner_group_key: GroupKey | None = None
    created_by_ref: str | None = None
    created_by_key: PrincipalKey | None = None
    disabled_at: datetime | None = None

    def _validate_import(self) -> Self:
        super()._validate_import()
        _import_selector(self.owner_group_ref, self.owner_group_key)
        _import_selector(self.created_by_ref, self.created_by_key, required=False)
        return self


ImportPrincipalInput: TypeAlias = Annotated[
    ImportPrincipalInputHuman | ImportPrincipalInputServiceAccount, Field(discriminator="kind")
]


class ImportMembershipSourceInput(_ImportModel):
    """Membership provenance with its own identity scope and restore timestamps."""

    source: str
    source_key: str
    source_scope_ref: str | None = None
    source_scope_key: IdentityScopeKey | None = None
    timestamps: RestoreTimestamps | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.source_scope_ref, self.source_scope_key)
        return self


class ImportGroupMembershipInput(_ImportModel):
    """Membership linking one principal and one group."""

    ref_: str | None = Field(default=None, alias="ref")
    principal_ref: str | None = None
    principal_key: PrincipalKey | None = None
    group_ref: str | None = None
    group_key: GroupKey | None = None
    sources: tuple[ImportMembershipSourceInput, ...] = ()
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.principal_ref, self.principal_key)
        _import_selector(self.group_ref, self.group_key)
        return self


class ImportExportTemplateInput(_ImportModel):
    """Reusable export or fragment owned by a collection."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    content_type: ExportContentType
    template: str
    kind: Literal["export", "fragment"]
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    class_ref: str | None = None
    class_key: ClassKey | None = None
    scope_kind: ExportScopeKind | None = None
    default_query: str | None = None
    include: ExportInclude | None = None
    relation_context: ExportRelationContext | None = None
    default_missing_data_policy: ExportMissingDataPolicy | None = None
    default_limits: ExportLimits | None = None
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.collection_ref, self.collection_key)
        _import_class_selector(self.class_ref, self.class_key)
        return self


class RemoteAuthConfigNone(_ImportModel):
    """Remote target without configured authentication."""

    type: Literal["none"]


class RemoteAuthConfigBearerSecret(_ImportModel):
    """Bearer authentication resolved from a server secret reference."""

    type: Literal["bearer_secret"]
    secret: str


class RemoteAuthConfigBasicSecret(_ImportModel):
    """Basic authentication with a username and server secret reference."""

    type: Literal["basic_secret"]
    username: str
    secret: str


class RemoteAuthConfigApiKeySecret(_ImportModel):
    """API key header resolved from a server secret reference."""

    type: Literal["api_key_secret"]
    header: str
    secret: str


RemoteAuthConfig: TypeAlias = Annotated[
    RemoteAuthConfigNone
    | RemoteAuthConfigBearerSecret
    | RemoteAuthConfigBasicSecret
    | RemoteAuthConfigApiKeySecret,
    Field(discriminator="type"),
]


class ImportRemoteTargetInput(_ImportModel):
    """Remote invocation configuration; importing it does not invoke the target."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    class_ref: str | None = None
    class_key: ClassKey | None = None
    method: Literal["get", "post", "patch", "delete"]
    url_template: str
    headers_template: JsonValue = None
    body_template: str | None = None
    auth_config: RemoteAuthConfig = Field(default_factory=lambda: RemoteAuthConfigNone(type="none"))
    allowed_subject_types: tuple[
        Literal["collection", "class", "object", "class_relation", "object_relation"], ...
    ]
    timeout_ms: int
    enabled: bool
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.collection_ref, self.collection_key)
        _import_class_selector(self.class_ref, self.class_key)
        return self


class EventDeliveryPolicy(_ImportModel):
    """Optional minimum interval between admissions to an event sink."""

    min_interval_ms: Annotated[int, Field(ge=1, le=86_400_000)] | None = None


class ImportEventSinkInput(_ImportModel):
    """Event sink configuration in an administrator import."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    kind: Literal["webhook", "amqp", "valkey_stream", "email"]
    config: JsonValue = None
    secret_ref: str | None = None
    delivery_policy: EventDeliveryPolicy | None = None
    enabled: bool
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None


class ImportEventSubscriptionInput(_ImportModel):
    """Collection subscription linked to one imported or existing event sink."""

    ref_: str | None = Field(default=None, alias="ref")
    name: str
    description: str
    collection_ref: str | None = None
    collection_key: CollectionKey | None = None
    sink_ref: str | None = None
    sink_key: EventSinkKey | None = None
    entity_types: tuple[str, ...]
    actions: tuple[str, ...]
    filter: JsonValue = None
    routing: JsonValue = None
    enabled: bool
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_selector(self.collection_ref, self.collection_key)
        _import_selector(self.sink_ref, self.sink_key)
        return self


class ImportComputedFieldInput(_ImportModel):
    """Class computed field, optionally owned by a personal principal."""

    ref_: str | None = Field(default=None, alias="ref")
    visibility: Literal["shared", "personal"]
    class_ref: str | None = None
    class_key: ClassKey | None = None
    owner_ref: str | None = None
    owner_key: PrincipalKey | None = None
    key: str
    label: str
    description: str = ""
    operation: dict[str, JsonValue]
    result_type: Literal["string", "number", "integer", "boolean", "object", "array"]
    enabled: bool
    timestamps: RestoreTimestamps | None = None
    condition: ImportWriteCondition | None = None

    def _validate_import(self) -> Self:
        _import_class_selector(self.class_ref, self.class_key, required=True)
        if self.visibility == "personal":
            _import_selector(self.owner_ref, self.owner_key)
        elif self.owner_ref is not None or self.owner_key is not None:
            raise ValueError("shared computed fields cannot have an owner")
        return self


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


class ImportGraph(_ImportModel):
    """Strictly typed Hubuum v0.0.21 graph, including identity and integrations."""

    collections: tuple[ImportCollectionInput, ...] = ()
    classes: tuple[ImportClassInput, ...] = ()
    objects: tuple[ImportObjectInput, ...] = Field(default=(), repr=False)
    class_relations: tuple[ImportClassRelationInput, ...] = ()
    object_relations: tuple[ImportObjectRelationInput, ...] = ()
    identity_scopes: tuple[ImportIdentityScopeInput, ...] = ()
    groups: tuple[ImportGroupInput, ...] = ()
    principals: tuple[ImportPrincipalInput, ...] = ()
    group_memberships: tuple[ImportGroupMembershipInput, ...] = ()
    collection_permissions: tuple[ImportCollectionPermissionInput, ...] = ()
    export_templates: tuple[ImportExportTemplateInput, ...] = ()
    remote_targets: tuple[ImportRemoteTargetInput, ...] = ()
    event_sinks: tuple[ImportEventSinkInput, ...] = ()
    event_subscriptions: tuple[ImportEventSubscriptionInput, ...] = ()
    computed_fields: tuple[ImportComputedFieldInput, ...] = ()

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
                self.computed_fields,
            )
        )


CURRENT_IMPORT_VERSION: Literal[2] = 2


class ImportRequest(_ImportModel):
    """Versioned asynchronous import request for the complete Hubuum graph."""

    graph: ImportGraph = Field(repr=False)
    version: Literal[2] = CURRENT_IMPORT_VERSION
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
    observed_revision: ResourceRevision | None = None


class MembershipPrincipal(HubuumModel):
    """Principal details nested in a membership or current-user response."""

    principal_id: PrincipalId
    identity_scope: str
    kind: str
    name: str
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


class PrincipalMember(HubuumModel):
    """Revision-owned membership between a principal and a group."""

    principal_id: PrincipalId
    group_id: GroupId
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision
    principal: MembershipPrincipal | None = None


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
    """Token-mint request using Hubuum's nested ``scope`` wire field."""

    description: str | None = None
    expires_at: datetime | None = None
    name: str | None = None
    scope: TokenScope | None = None


class RenewTokenRequest(RequestModel):
    """Optional expiry override for a renewed token."""

    expires_at: datetime | None = None


TokenRequestT = TypeVar("TokenRequestT", NewTokenRequest, RenewTokenRequest)


class RestoreConfirmRequest(APIModel):
    """Exact confirmation bound to a staged restore and its capability."""

    model_config = ConfigDict(extra="forbid")

    restore_capability: str = Field(repr=False)
    sha256: str
    confirmation: str

    def payload(self) -> dict[str, JsonValue]:
        return self.wire_payload()


class CreateTokenOperation(RequestModel):
    kind: Literal["create_token"] = "create_token"
    principal_id: PrincipalId
    token: NewTokenRequest


class RenewTokenOperation(RequestModel):
    kind: Literal["renew_token"] = "renew_token"
    principal_id: PrincipalId
    token_id: TokenId
    token: RenewTokenRequest


class CreateUserOperation(RequestModel):
    kind: Literal["create_user"] = "create_user"
    user: UserCreate = Field(repr=False)


class UpdateUserOperation(RequestModel):
    kind: Literal["update_user"] = "update_user"
    user_id: UserId
    user: UserUpdate = Field(repr=False)


class ImportCredentialsOperation(RequestModel):
    kind: Literal["import_credentials"] = "import_credentials"
    import_: ImportRequest = Field(alias="import", repr=False)


class ConfirmRestoreOperation(RequestModel):
    kind: Literal["confirm_restore"] = "confirm_restore"
    restore_id: RestoreJobId
    confirmation: RestoreConfirmRequest = Field(repr=False)


CredentialOperation: TypeAlias = Annotated[
    CreateTokenOperation
    | RenewTokenOperation
    | CreateUserOperation
    | UpdateUserOperation
    | ImportCredentialsOperation
    | ConfirmRestoreOperation,
    Field(discriminator="kind"),
]


class CredentialApprovalRequest(RequestModel):
    """Authenticate the acting human for exactly one intended mutation."""

    model_config = ConfigDict(hide_input_in_errors=True)

    password: str = Field(repr=False)
    operation: CredentialOperation = Field(repr=False)

    @classmethod
    def _safe_validation_error(cls, error: ValidationError) -> ValidationError:
        # Nested inputs, messages, context, and even unknown field names can
        # contain credentials. Retain only error codes and known root fields.
        details: list[InitErrorDetails] = [
            {
                "type": PydanticCustomError(item["type"], "Invalid credential approval input"),
                "loc": item["loc"][:1]
                if item["loc"] and item["loc"][0] in cls.model_fields
                else (),
                "input": "<redacted>",
            }
            for item in error.errors(include_input=False, include_context=False, include_url=False)
        ]
        return ValidationError.from_exception_data(cls.__name__, details, hide_input=True)

    @model_validator(mode="wrap")
    @classmethod
    def _validate_without_secret_inputs(
        cls, value: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        try:
            return handler(value)
        except ValidationError as error:
            safe_error = cls._safe_validation_error(error)
        # Raising outside the handler avoids retaining the original exception.
        raise safe_error

    @classmethod
    def model_validate_json(cls, json_data: str | bytes | bytearray, **kwargs: Any) -> Self:
        """Validate JSON without retaining credentials in JSON-parser errors."""
        try:
            return super().model_validate_json(json_data, **kwargs)
        except ValidationError as error:
            safe_error = cls._safe_validation_error(error)
        raise safe_error

    def payload(self) -> dict[str, Any]:
        # Defaulted discriminator values must survive exclude_unset serialization.
        result = super().payload()
        result["operation"]["kind"] = self.operation.kind
        if isinstance(self.operation, ImportCredentialsOperation):
            result["operation"]["import"] = self.operation.import_.payload()
        return result


class CredentialApprovalRecord(HubuumModel):
    """Retained non-secret evidence, including consumption and invalidation."""

    id: CredentialApprovalId
    actor_id: PrincipalId
    token_id: TokenId
    operation: str
    authenticated_at: datetime
    expires_at: datetime
    target_id: PrincipalId | None = None
    restore_job_id: RestoreJobId | None = None
    consumed_at: datetime | None = None
    invalidated_at: datetime | None = None


class CredentialApprovalResponse(HubuumModel):
    """Transient approval; token expiry must be copied into the final mutation."""

    model_config = ConfigDict(hide_input_in_errors=True)

    approval: CredentialApprovalSecret = Field(repr=False)
    record: CredentialApprovalRecord
    token_expires_at: datetime | None = None

    def headers(self) -> dict[str, str]:
        """Explicitly expose the approval header for one protected request."""
        return {"X-Hubuum-Credential-Approval": self.approval.get_secret_value()}

    def token_request(self, payload: TokenRequestT) -> TokenRequestT:
        """Copy the server-normalized expiry without changing the original request."""
        if self.token_expires_at is None:
            raise ValueError("token approval must include token_expires_at")
        return payload.model_copy(update={"expires_at": self.token_expires_at})


class TokenResourceScopeDetails(HubuumModel):
    """One resource returned in token scope metadata."""

    kind: TokenResourceKind
    id: int


class TokenScopeDetails(HubuumModel):
    """Exact permission and resource dimensions returned for a scoped token."""

    permissions: tuple[Permission, ...] | None = None
    resources: tuple[TokenResourceScopeDetails, ...] | None = None


class _TokenMetadataBase(HubuumModel):
    """Fields shared by current, point, and list token representations."""

    id: TokenId
    issued: datetime
    description: str | None = None
    expires_at: datetime | None = None
    name: str | None = None
    scope: TokenScopeDetails | None = None
    revision: ResourceRevision


class CurrentTokenMetadata(_TokenMetadataBase):
    """Metadata for the token authenticating the current request."""

    last_used_at: datetime | None = None


class PrincipalTokenPoint(_TokenMetadataBase):
    """Canonical point-in-time token metadata without routine usage state."""

    principal_id: PrincipalId
    revoked_at: datetime | None = None


class PrincipalTokenMetadata(PrincipalTokenPoint):
    """Lifecycle-aware token metadata returned by retained-token lists."""

    active: bool
    expired: bool
    last_used_at: datetime | None = None


class MeResponse(HubuumModel):
    principal: MembershipPrincipal
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
    SCHEMA_VALIDATION = "schema_validation"
    SCHEMA_PROFILING = "schema_profiling"


class TaskRemoteSideEffectState(StrEnum):
    """Conservative dispatch evidence; cancellation cannot undo a remote side effect."""

    NOT_SENT = "not_sent"
    POSSIBLY_SENT = "possibly_sent"
    LEGACY_UNKNOWN = "legacy_unknown"


class TaskCancelRequest(RequestModel):
    """Idempotent cancellation, optionally conditional on the current task status."""

    expected_status: TaskStatus | None = None
    reason: str | None = Field(default=None, max_length=512, repr=False)


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


class TaskOutputDiscoveryState(StrEnum):
    AVAILABLE = "available"
    EXPIRED = "expired"
    NOT_PRODUCED = "not_produced"
    UNKNOWN = "unknown"


class TaskCollectionTarget(HubuumModel):
    type: Literal["collection"]
    collection_id: CollectionId


class TaskClassTarget(HubuumModel):
    type: Literal["class"]
    class_id: ClassId


class TaskObjectTarget(HubuumModel):
    type: Literal["object"]
    object_id: ObjectId
    class_id: ClassId | None = None


class TaskClassRelationTarget(HubuumModel):
    type: Literal["class_relation"]
    relation_id: ClassRelationId


class TaskObjectRelationTarget(HubuumModel):
    type: Literal["object_relation"]
    relation_id: ObjectRelationId


TaskDiscoveryTarget: TypeAlias = Annotated[
    TaskCollectionTarget
    | TaskClassTarget
    | TaskObjectTarget
    | TaskClassRelationTarget
    | TaskObjectRelationTarget,
    Field(discriminator="type"),
]


class RetainedImportDetails(HubuumModel):
    atomicity: ImportAtomicity | None = None
    collision_policy: ImportCollisionPolicy | None = None
    permission_policy: ImportPermissionPolicy | None = None
    dry_run: bool | None = None
    has_failed_items: bool | None = None


class RetainedExportDetails(HubuumModel):
    output_state: TaskOutputDiscoveryState
    max_items: int | None = None
    max_output_bytes: int | None = None
    missing_data_policy: ExportMissingDataPolicy | None = None
    scope_kind: ExportScopeKind | None = None
    target: TaskDiscoveryTarget | None = None
    template_id: int | None = None
    truncated: bool | None = None
    warning_count: int | None = None


class RetainedBackupDetails(HubuumModel):
    output_state: TaskOutputDiscoveryState
    include_history: bool | None = None


class SchemaProfileTaskDetails(APIModel):
    class_id: ClassId | None = None
    output_url: str | None = None


class SchemaTaskDetails(HubuumModel):
    class_id: ClassId | None = None
    schema_revision: SchemaRevision | None = None
    work_kind: SchemaWorkKind | None = None
    work_status: SchemaWorkStatus | None = None
    results_url: str | None = Field(default=None, repr=False)


class RebuildTaskDetails(HubuumModel):
    class_id: ClassId | None = None
    computation_revision: int | None = None


class RemoteCallTaskDetails(APIModel):
    remote_target_id: int | None = None
    target: TaskDiscoveryTarget | None = None


class ImportTaskDetails(HubuumModel):
    """Import-specific task metadata."""

    results_url: str = Field(repr=False)
    retained: RetainedImportDetails | None = None


class ExportTaskDetails(HubuumModel):
    """Export output state and v0.0.18 phase-duration measurements."""

    output_url: str = Field(repr=False)
    output_available: bool
    output_expired: bool
    output_content_type: str | None = None
    output_expires_at: datetime | None = None
    retained: RetainedExportDetails | None = None
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
    retained: RetainedBackupDetails | None = None
    byte_size: int | None = None
    output_expires_at: datetime | None = None
    sha256: str | None = None


class TaskDetails(HubuumModel):
    """Kind-specific task metadata exposed by Hubuum v0.0.18."""

    import_: ImportTaskDetails | None = Field(default=None, alias="import")
    export: ExportTaskDetails | None = None
    backup: BackupTaskDetails | None = None
    schema_validation: SchemaTaskDetails | None = None
    schema_profiling: SchemaProfileTaskDetails | None = None
    reindex: RebuildTaskDetails | None = None
    remote_call: RemoteCallTaskDetails | None = None


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
    cancel_requested_at: datetime | None = None
    cancel_requested_by: PrincipalId | None = None
    cancel_reason: str | None = Field(default=None, repr=False)
    execution_deadline_at: datetime | None = None
    remote_side_effect_state: TaskRemoteSideEffectState | None = None
    terminal_reason: str | None = Field(default=None, repr=False)
    unattempted_items: int = 0
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
        """Return successful entity outcomes, including planned dry-run items."""
        return sum(result.outcome in {"succeeded", "planned"} for result in self.results)

    @property
    def failed(self) -> int:
        """Return the number of unsuccessful entity outcomes."""
        return len(self.results) - self.succeeded


class ApiErrorResponse(HubuumModel):
    error: str
    message: str
    reason: str | None = None


class EventSinkRouting(StrEnum):
    FIXED = "fixed"
    WEBHOOK_URL = "webhook_url"
    EMAIL_RECIPIENTS = "email_recipients"
    VALKEY_STREAM = "valkey_stream"
    AMQP = "amqp"


class CollectionEventSink(HubuumModel):
    """Permitted destination metadata, without URLs, configuration or credentials."""

    id: EventSinkId
    name: str
    kind: str
    enabled: bool
    collection_id: CollectionId | None
    revision: ResourceRevision
    routing: EventSinkRouting


class EventSink(APIModel):
    """Administrator sink configuration; sensitive values are hidden from repr."""

    id: EventSinkId
    name: str
    kind: str
    config: dict[str, JsonValue] = Field(repr=False)
    enabled: bool
    collection_id: CollectionId | None = None
    secret_ref: str | None = Field(default=None, repr=False)
    delivery_policy: dict[str, JsonValue] | None = None
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


class EventSinkCreate(RequestModel, APIModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: Literal["webhook", "email", "amqp", "valkey_stream"]
    config: dict[str, JsonValue] = Field(default_factory=dict, repr=False)
    enabled: bool | None = None
    secret_ref: str | None = Field(default=None, repr=False)
    delivery_policy: dict[str, JsonValue] | None = None

    def wire_payload(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], self.payload())


class EventSinkUpdate(RequestModel, APIModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    kind: Literal["webhook", "email", "amqp", "valkey_stream"] | None = None
    config: dict[str, JsonValue] | None = Field(default=None, repr=False)
    enabled: bool | None = None
    secret_ref: str | None = Field(default=None, repr=False)
    delivery_policy: dict[str, JsonValue] | None = None

    def payload(self) -> dict[str, Any]:
        """Preserve explicit credential removal without clearing omitted fields."""
        payload = super().payload()
        if "secret_ref" in self.model_fields_set:
            payload["secret_ref"] = self.secret_ref
        return payload

    def wire_payload(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], self.payload())


class EventSubscription(HubuumModel):
    id: EventSubscriptionId
    collection_id: CollectionId | None
    sink_id: EventSinkId
    name: str
    description: str | None = None
    entity_types: tuple[str, ...]
    actions: tuple[str, ...]
    filter: dict[str, JsonValue] = Field(default_factory=dict, repr=False)
    routing: dict[str, JsonValue] = Field(default_factory=dict, repr=False)
    enabled: bool
    created_at: datetime
    updated_at: datetime
    revision: ResourceRevision


class EventSubscriptionCreate(RequestModel):
    sink_id: EventSinkId
    name: str
    description: str | None = None
    entity_types: tuple[str, ...]
    actions: tuple[str, ...]
    filter: dict[str, JsonValue] | None = Field(default=None, repr=False)
    routing: dict[str, JsonValue] | None = Field(default=None, repr=False)
    enabled: bool | None = None


class EventSubscriptionUpdate(RequestModel):
    sink_id: EventSinkId | None = None
    name: str | None = None
    description: str | None = None
    entity_types: tuple[str, ...] | None = None
    actions: tuple[str, ...] | None = None
    filter: dict[str, JsonValue] | None = Field(default=None, repr=False)
    routing: dict[str, JsonValue] | None = Field(default=None, repr=False)
    enabled: bool | None = None


class _EventSinkCollectionIds(RootModel[list[CollectionId]]):
    """Internal decoder for the administrator's direct collection grant list."""


# Exact wire models depend on APIModel above. Import them only after the shared
# bases are defined; convenience requests retain their contract and redaction.
from .api import models as _wire_models  # noqa: E402


class BackupRequest(_wire_models.BackupRequest):
    model_config = ConfigDict(extra="forbid")


class ExportTemplateCreate(_wire_models.NewExportTemplate):
    model_config = ConfigDict(extra="forbid")


class ExportTemplateUpdate(_wire_models.UpdateExportTemplate):
    model_config = ConfigDict(extra="forbid")


class ExportTemplateRunRequest(_wire_models.ExportTemplateRunRequest):
    model_config = ConfigDict(extra="forbid")


class RemoteTargetCreate(_wire_models.NewRemoteTarget):
    model_config = ConfigDict(extra="forbid")


class RemoteTargetUpdate(_wire_models.UpdateRemoteTarget):
    model_config = ConfigDict(extra="forbid")


class RemoteTargetInvokeRequest(_wire_models.RemoteTargetInvokeRequest):
    model_config = ConfigDict(extra="forbid")


class ComputedFieldCreate(_wire_models.ComputedFieldDefinitionRequest):
    model_config = ConfigDict(extra="forbid")


class PersonalComputedFieldCreate(_wire_models.PersonalComputedFieldDefinitionRequest):
    model_config = ConfigDict(extra="forbid")


class ComputedFieldUpdate(_wire_models.ComputedFieldDefinitionPatch):
    model_config = ConfigDict(extra="forbid")


class ComputedFieldPreviewRequest(_wire_models.ComputedFieldPreviewRequest):
    model_config = ConfigDict(extra="forbid")


class SettingsRequest(APIModel):
    """Strict JSON object for settings replacement or merge patch; keys are application-defined."""

    model_config = ConfigDict(extra="forbid")
    settings: dict[str, JsonValue]


class SettingsPatchOperation(ObjectDataPatchOperation, APIModel):
    """Strict RFC 6902 operation with redacted validation and explicit null preservation."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


RemoteTargetCreate.model_rebuild(_types_namespace=vars(_wire_models))
RemoteTargetUpdate.model_rebuild(_types_namespace=vars(_wire_models))
