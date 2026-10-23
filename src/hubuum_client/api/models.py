"""Generated from docs/openapi.json; run scripts/generate-typed-api.py."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from pydantic import AwareDatetime, ConfigDict, Field, JsonValue, SecretStr

from hubuum_client.models import APIModel


class AddOperation(APIModel):
    path: str
    value: JsonValue


class ApiErrorResponse(APIModel):
    error: str
    message: str
    reason: str | None = None


class AuthProvidersResponse(APIModel):
    providers: list[str]


class BackupConfig(APIModel):
    max_active_tasks_per_user: Annotated[int, Field(ge=0)]
    max_capture_rows: Annotated[int, Field(ge=0)]
    max_output_bytes: Annotated[int, Field(ge=0)]
    output_retention_hours: int


class BackupHistory(APIModel):
    model_config = ConfigDict(extra="forbid")
    sections: dict[str, JsonValue]


class BackupManifest(APIModel):
    exclusions: list[str]
    item_counts: dict[str, JsonValue]


class BackupRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    include_history: bool | None = None


class BackupState(APIModel):
    model_config = ConfigDict(extra="forbid")
    sections: dict[str, JsonValue]


class ClassComputationState(APIModel):
    active_task_id: int | None = None
    class_id: int
    created_at: AwareDatetime
    evaluation_revision: int
    last_error: str | None = None
    rebuild_status: str
    updated_at: AwareDatetime


class ClearRateLimitResponse(APIModel):
    cleared: Annotated[int, Field(ge=0)]


class ClientAllowlistStatus(APIModel):
    allows_any: bool
    network_count: Annotated[int, Field(ge=0)]


class ClientAuthenticationConfig(APIModel):
    default_token_lifetime_hours: Annotated[int, Field(ge=1)]
    max_token_lifetime_hours: Annotated[int, Field(ge=1)]
    session_absolute_seconds: int
    session_access_seconds: int
    session_idle_seconds: int
    session_retention_seconds: int


class ClientPaginationConfig(APIModel):
    default_page_limit: Annotated[int, Field(ge=1)]
    max_page_limit: Annotated[int, Field(ge=1)]


class CollectionKey(APIModel):
    name: str
    path: list[str] | None = None


class ComputedFieldDeleteResponse(APIModel):
    deleted_definition_id: int
    state: ClassComputationState


class ComputedFieldErrorResponse(APIModel):
    code: str
    message: str
    path: str | None = None


class ComputedFieldPreviewResponse(APIModel):
    error: ComputedFieldErrorResponse | None = None
    value: JsonValue


class ComputedScopeResponse(APIModel):
    errors: dict[str, ComputedFieldErrorResponse]
    values: dict[str, JsonValue]


class CopyOperation(APIModel):
    from_: Annotated[str, Field(alias="from")]
    path: str


class CredentialCreationResponse(APIModel):
    address: str | None = None
    address_method: str
    issuance_method: str
    issued_at: AwareDatetime
    issuer_id: int | None = None


class CredentialSourceResponse(APIModel):
    address: str | None = None
    address_method: str
    first_seen: AwareDatetime
    last_seen: AwareDatetime


class DbStateResponse(APIModel):
    acquisition_wait_time_ms: Annotated[int, Field(ge=0)]
    acquisitions_direct: Annotated[int, Field(ge=0)]
    acquisitions_started: Annotated[int, Field(ge=0)]
    acquisitions_timed_out: Annotated[int, Field(ge=0)]
    acquisitions_waited: Annotated[int, Field(ge=0)]
    active_connections: int
    available_connections: Annotated[int, Field(ge=0)]
    connections_closed_broken: Annotated[int, Field(ge=0)]
    connections_closed_idle_timeout: Annotated[int, Field(ge=0)]
    connections_closed_invalid: Annotated[int, Field(ge=0)]
    connections_closed_max_lifetime: Annotated[int, Field(ge=0)]
    connections_created: Annotated[int, Field(ge=0)]
    db_size: int
    idle_connections: Annotated[int, Field(ge=0)]
    in_use_connections: Annotated[int, Field(ge=0)]
    last_vacuum_time: str | None = None
    max_connections: Annotated[int, Field(ge=0)]
    pending_acquisitions: Annotated[int, Field(ge=0)]
    total_connections: Annotated[int, Field(ge=0)]


class EventConfig(APIModel):
    delivery_batch_size: Annotated[int, Field(ge=0)]
    delivery_lock_timeout_ms: Annotated[int, Field(ge=0)]
    delivery_max_attempts: int
    delivery_poll_interval_ms: Annotated[int, Field(ge=0)]
    delivery_retention_days: int
    delivery_retry_backoff_base_ms: Annotated[int, Field(ge=0)]
    delivery_retry_backoff_max_ms: Annotated[int, Field(ge=0)]
    delivery_transport_timeout_ms: Annotated[int, Field(ge=0)]
    delivery_workers: Annotated[int, Field(ge=0)]
    fanout_batch_size: Annotated[int, Field(ge=0)]
    fanout_lock_timeout_ms: Annotated[int, Field(ge=0)]
    fanout_poll_interval_ms: Annotated[int, Field(ge=0)]
    fanout_workers: Annotated[int, Field(ge=0)]
    retention_archive_path_configured: bool
    retention_days: int
    retention_file_archive_enabled: bool
    retention_purge_batch_size: Annotated[int, Field(ge=0)]
    retention_purge_enabled: bool
    retention_purge_interval_seconds: Annotated[int, Field(ge=0)]


class EventDeliveryPolicy(APIModel):
    min_interval_ms: Annotated[int | None, Field(ge=1, le=86400000)] = None


class EventDeliveryResponse(APIModel):
    attempts: int
    created_at: AwareDatetime
    deferred_reason: str | None = None
    event_id: int
    id: int
    last_error: str | None = None
    locked_until: AwareDatetime | None = None
    next_attempt_at: AwareDatetime
    purpose: Literal["event", "test"]
    status: str
    subscription_id: int
    updated_at: AwareDatetime


class EventDeliveryStatusCounts(APIModel):
    dead: int
    failed: int
    in_flight: int
    pending: int
    retryable: int
    succeeded: int
    total: int


class EventDeliveryUpdateResponse(APIModel):
    delivery: EventDeliveryResponse


class EventSinkDeliveryHealth(APIModel):
    counts: EventDeliveryStatusCounts
    oldest_due_age_seconds: int | None = None
    sink_enabled: bool
    sink_id: int
    sink_kind: str
    sink_name: str
    stale_claims: int
    subscription_count: int


class EventSinkKey(APIModel):
    name: str


class EventSubscriptionDeliveryHealth(APIModel):
    collection_id: int | None = None
    counts: EventDeliveryStatusCounts
    oldest_due_age_seconds: int | None = None
    sink_enabled: bool
    sink_id: int
    sink_kind: str
    sink_name: str
    stale_claims: int
    subscription_enabled: bool
    subscription_id: int
    subscription_name: str


class EventWorkerWakeupStats(APIModel):
    notification_wakeups: Annotated[int, Field(ge=0)]
    notifications_sent: Annotated[int, Field(ge=0)]
    poll_wakeups: Annotated[int, Field(ge=0)]


class ExportConfig(APIModel):
    database_statement_timeout_ms: Annotated[int, Field(ge=0)]
    max_output_bytes: Annotated[int, Field(ge=0)]
    output_cleanup_interval_seconds: Annotated[int, Field(ge=0)]
    output_retention_hours: int
    stage_timeout_ms: Annotated[int, Field(ge=0)]
    storage_query_budget_ms: Annotated[int, Field(ge=0)]
    template_fuel: Annotated[int, Field(ge=0)]
    template_max_objects: Annotated[int, Field(ge=0)]
    template_recursion_limit: Annotated[int, Field(ge=0)]


class ExportLimits(APIModel):
    max_items: Annotated[int | None, Field(ge=0)] = None
    max_output_bytes: Annotated[int | None, Field(ge=0)] = None


class ExportRelationContext(APIModel):
    model_config = ConfigDict(extra="forbid")
    depth: int | None = None


class ExportTemplateRunRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    limits: ExportLimits | None = None
    missing_data_policy: Literal["strict", "null", "omit"] | None = None
    object_id: int | None = None
    query: str | None = None


class ExportWarning(APIModel):
    code: str
    message: str
    path: str | None = None


class GroupKey(APIModel):
    groupname: str
    identity_scope: str | None = None


class HistoricalComputedFieldEvaluated(APIModel):
    status: Literal["evaluated"]
    value: JsonValue


class HistoricalComputedFieldError(APIModel):
    error: ComputedFieldErrorResponse
    status: Literal["error"]


class HistoricalComputedFieldDisabled(APIModel):
    status: Literal["disabled"]


class HistoricalComputedFieldResultEvaluated(APIModel):
    status: Literal["evaluated"]
    value: JsonValue


class HistoricalComputedFieldResultError(APIModel):
    error: ComputedFieldErrorResponse
    status: Literal["error"]


class HistoricalComputedFieldResultDisabled(APIModel):
    status: Literal["disabled"]


class HistoricalSharedComputedFieldsUnavailable(APIModel):
    reason: Literal[
        "definition_history_unavailable",
        "class_history_unavailable",
        "unsupported_evaluator_version",
        "unsupported_definition_semantics",
    ]
    status: Literal["unavailable"]


class IdentityScopeKey(APIModel):
    name: str


class ImportPrincipalInputHuman(APIModel):
    anonymized_at: AwareDatetime | None = None
    email: str | None = None
    kind: Literal["human"]
    password: SecretStr | None = None
    password_hash: SecretStr | None = None
    proper_name: str | None = None


class ImportPrincipalSubtypeHuman(APIModel):
    anonymized_at: AwareDatetime | None = None
    email: str | None = None
    kind: Literal["human"]
    password: SecretStr | None = None
    password_hash: SecretStr | None = None
    proper_name: str | None = None


class ImportWriteConditionCreateOnly(APIModel):
    mode: Literal["create_only"]


class ImportWriteConditionOverwrite(APIModel):
    mode: Literal["overwrite"]


class LoginRateLimitConfigResponse(APIModel):
    backend: str
    backoff_base_seconds: Annotated[int, Field(ge=0)]
    backoff_max_seconds: Annotated[int, Field(ge=0)]
    enabled: bool
    max_attempts: Annotated[int, Field(ge=0)]
    max_attempts_per_account: Annotated[int, Field(ge=0)]
    max_attempts_per_ip: Annotated[int, Field(ge=0)]
    max_attempts_per_subnet: Annotated[int, Field(ge=0)]
    subnet_prefix_v4: Annotated[int, Field(ge=0)]
    subnet_prefix_v6: Annotated[int, Field(ge=0)]
    window_seconds: Annotated[int, Field(ge=0)]


class LoginRateLimitEntryResponse(APIModel):
    attempts: Annotated[int, Field(ge=0)]
    id: str
    identifier: str
    locked: bool
    locked_for_seconds: Annotated[int | None, Field(ge=0)] = None
    lockout_level: Annotated[int, Field(ge=0)]
    scope: str


class LoginRateLimitStateResponse(APIModel):
    config: LoginRateLimitConfigResponse
    entries: list[LoginRateLimitEntryResponse]
    locked_entries: Annotated[int, Field(ge=0)]
    returned_entries: Annotated[int, Field(ge=0)]
    tracked_entries: Annotated[int, Field(ge=0)]


class LoginResponse(APIModel):
    expires_at: AwareDatetime
    token: SecretStr


class LoginUser(APIModel):
    identity_scope: Annotated[str | None, Field(max_length=255)] = None
    name: Annotated[str, Field(max_length=255)]
    password: Annotated[SecretStr, Field(max_length=4096, min_length=1)]


class LogoutTokenRequest(APIModel):
    token: SecretStr


class MessageResponse(APIModel):
    message: str


class MoveOperation(APIModel):
    from_: Annotated[str, Field(alias="from")]
    path: str


class NetworkConfig(APIModel):
    client_allowlist: ClientAllowlistStatus
    trust_ip_headers: bool
    trusted_proxy_hops: Annotated[int, Field(ge=0)]
    trusted_proxy_networks: Annotated[int, Field(ge=0)]


class NewCollectionWithAssignee(APIModel):
    description: str
    group_id: Annotated[int, Field(ge=1)]
    name: str
    parent_collection_id: CollectionID | None = None


class NewEventSink(APIModel):
    config: JsonValue | None = None
    delivery_policy: EventDeliveryPolicy | None = None
    enabled: bool | None = None
    kind: Literal["webhook", "amqp", "valkey_stream", "email"]
    name: str
    secret_ref: str | None = None


class NewGroup(APIModel):
    description: str | None = None
    groupname: str
    identity_scope: str | None = None


class NewHubuumClass(APIModel):
    collection_id: int
    description: str
    json_schema: JsonValue | None = None
    name: str
    validate_schema: bool | None = None


class NewHubuumObject(APIModel):
    collection_id: int
    data: JsonValue
    description: str
    hubuum_class_id: int
    name: str


class NewHubuumObjectRelation(APIModel):
    class_relation_id: int
    from_hubuum_object_id: int
    to_hubuum_object_id: int


class NewHubuumObjectRequest(APIModel):
    collection_id: int | None = None
    data: JsonValue
    description: str
    hubuum_class_id: int | None = None
    name: str


class NewServiceAccount(APIModel):
    description: str | None = None
    identity_scope: str | None = None
    name: str
    owner_group_id: Annotated[int, Field(ge=1)]


class NewUser(APIModel):
    email: str | None = None
    identity_scope: str | None = None
    name: str
    password: Annotated[SecretStr, Field(max_length=4096, min_length=1)]
    proper_name: str | None = None


class ObjectAggregateMeasureValue(APIModel):
    field: str
    operation: Literal["sum", "average", "min", "max"]
    skipped_count: int
    state: Literal["value", "empty"]
    value: JsonValue | None = None
    value_count: int


class ObjectDataPatchDocument1(AddOperation):
    op: Literal["add"]


class ObjectDataPatchDocument4(MoveOperation):
    op: Literal["move"]


class ObjectDataPatchDocument5(CopyOperation):
    op: Literal["copy"]


class ObjectsByClass(APIModel):
    count: int
    hubuum_class_id: int


class PaginationConfig(APIModel):
    default_page_limit: Annotated[int, Field(ge=0)]
    max_page_limit: Annotated[int, Field(ge=0)]
    max_transitive_depth: int
    max_traversal_work_rows: int


class PatchOperation1(AddOperation):
    op: Literal["add"]


class PatchOperation4(MoveOperation):
    op: Literal["move"]


class PatchOperation5(CopyOperation):
    op: Literal["copy"]


class Permission(APIModel):
    collection_id: int
    created_at: AwareDatetime
    group_id: int
    has_create_class: bool
    has_create_class_relation: bool
    has_create_object: bool
    has_create_object_relation: bool
    has_create_remote_target: bool
    has_create_template: bool
    has_delegate_collection: bool
    has_delete_class: bool
    has_delete_class_relation: bool
    has_delete_collection: bool
    has_delete_object: bool
    has_delete_object_relation: bool
    has_delete_remote_target: bool
    has_delete_template: bool
    has_execute_remote_target: bool
    has_manage_event_subscription: bool
    has_read_audit: bool
    has_read_class: bool
    has_read_class_relation: bool
    has_read_collection: bool
    has_read_object: bool
    has_read_object_relation: bool
    has_read_remote_target: bool
    has_read_template: bool
    has_update_class: bool
    has_update_class_relation: bool
    has_update_collection: bool
    has_update_object: bool
    has_update_object_relation: bool
    has_update_remote_target: bool
    has_update_template: bool
    id: int
    updated_at: AwareDatetime


class PrincipalKey(APIModel):
    identity_scope: str | None = None
    name: str


class PrincipalSettingsPatchDocument1(AddOperation):
    op: Literal["add"]


class PrincipalSettingsPatchDocument4(MoveOperation):
    op: Literal["move"]


class PrincipalSettingsPatchDocument5(CopyOperation):
    op: Literal["copy"]


class ProbeResponse(APIModel):
    status: str


class ProvenancePrincipal(APIModel):
    name: str | None = None
    principal_id: Annotated[int, Field(ge=1)]


class QueryObservationConfig(APIModel):
    enabled: bool
    max_patterns: Annotated[int, Field(ge=0)]
    max_patterns_per_class: Annotated[int, Field(ge=0)]
    max_predicates_per_query: Annotated[int, Field(ge=0)]
    retention_seconds: Annotated[int, Field(ge=0)]
    runtime_override: bool | None = None
    sample_every: Annotated[int, Field(ge=0)]


class QueryObservationSettings(APIModel):
    enabled: bool
    max_patterns: Annotated[int, Field(ge=0)]
    max_patterns_per_class: Annotated[int, Field(ge=0)]
    max_predicates_per_query: Annotated[int, Field(ge=0)]
    retention_seconds: Annotated[int, Field(ge=0)]
    sample_every: Annotated[int, Field(ge=0)]


class QueryObservationUpdateRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class QueryUsageAdapterProgress(APIModel):
    declaration_owners: Annotated[int, Field(ge=0)]
    last_error: str | None = None
    reference: str
    state: str
    updated_at: AwareDatetime


class RebuildTaskDetails(APIModel):
    class_id: HubuumClassID | None = None
    computation_revision: int | None = None


class ReleaseRateLimitResponse(APIModel):
    released: bool


class RemoteAuthConfigNone(APIModel):
    type: Literal["none"]


class RemoteAuthConfigBearerSecret(APIModel):
    secret: SecretStr
    type: Literal["bearer_secret"]


class RemoteAuthConfigBasicSecret(APIModel):
    secret: SecretStr
    type: Literal["basic_secret"]
    username: str


class RemoteAuthConfigApiKeySecret(APIModel):
    header: str
    secret: SecretStr
    type: Literal["api_key_secret"]


class RemoteCallConfig(APIModel):
    allow_private_targets: bool
    max_response_bytes: Annotated[int, Field(ge=0)]
    timeout_ms: Annotated[int, Field(ge=0)]


class RemoteCallResult(APIModel):
    created_at: AwareDatetime
    duration_ms: int
    error: str | None = None
    id: int
    method: str
    rendered_url: str
    response_body_preview: str | None = None
    response_headers: JsonValue | None = None
    response_status: int | None = None
    subject_id: int
    subject_type: str
    success: bool
    target_id: int | None = None
    task_id: int


class RemoteInvocationSubjectCollection(APIModel):
    collection_id: Annotated[int, Field(ge=1)]
    type: Literal["collection"]


class RemoteInvocationSubjectClass(APIModel):
    class_id: Annotated[int, Field(ge=1)]
    type: Literal["class"]


class RemoteInvocationSubjectObject(APIModel):
    class_id: Annotated[int, Field(ge=1)]
    object_id: Annotated[int, Field(ge=1)]
    type: Literal["object"]


class RemoteInvocationSubjectClassRelation(APIModel):
    relation_id: Annotated[int, Field(ge=1)]
    type: Literal["class_relation"]


class RemoteInvocationSubjectObjectRelation(APIModel):
    relation_id: Annotated[int, Field(ge=1)]
    type: Literal["object_relation"]


class RemoteTargetInvokeRequest(APIModel):
    body_override: JsonValue | None = None
    parameters: JsonValue | None = None
    subject: (
        RemoteInvocationSubjectCollection
        | RemoteInvocationSubjectClass
        | RemoteInvocationSubjectObject
        | RemoteInvocationSubjectClassRelation
        | RemoteInvocationSubjectObjectRelation
    )


class RemoveOperation(APIModel):
    path: str


class RenewTokenRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    expires_at: AwareDatetime | None = None


class ReplaceOperation(APIModel):
    path: str
    value: JsonValue


class RestoreConfig(APIModel):
    max_upload_bytes: Annotated[int, Field(ge=0)]
    stage_retention_minutes: int


class RestoreConfirmRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    confirmation: str
    restore_capability: str
    sha256: str


class RestoreTimestamps(APIModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class RestoreValidationSummary(APIModel):
    backup_version: int
    includes_history: bool
    source_version: str
    total_items: int


class RetainedImportDetails(APIModel):
    atomicity: Literal["strict", "best_effort"] | None = None
    collision_policy: Literal["abort", "overwrite"] | None = None
    dry_run: bool | None = None
    has_failed_items: bool | None = None
    permission_policy: Literal["abort", "continue"] | None = None


class String(APIModel):
    characters: Annotated[int, Field(ge=0)]


class SchemaActualValueString(APIModel):
    string: String


class Array(APIModel):
    items: Annotated[int, Field(ge=0)]


class SchemaActualValueArray(APIModel):
    array: Array


class Object(APIModel):
    properties: Annotated[int, Field(ge=0)]


class SchemaActualValueObject(APIModel):
    object: Object


class SchemaComplianceCounts(APIModel):
    invalid: Annotated[int, Field(ge=0)]
    not_required: Annotated[int, Field(ge=0)]
    pending: Annotated[int, Field(ge=0)]
    valid: Annotated[int, Field(ge=0)]


class SchemaExpectedValueAvailable(APIModel):
    status: Literal["available"]
    value: JsonValue


class SchemaExpectedValueOmitted(APIModel):
    status: Literal["omitted"]


class SchemaFailure(APIModel):
    keyword: str
    missing_property: str | None = None
    schema_path: str | None = None


class SchemaFailureGroup(APIModel):
    objects: Annotated[int, Field(ge=0)]
    reason: SchemaFailure
    samples: list[int]


class SchemaImpactCounts(APIModel):
    newly_invalid: Annotated[int, Field(ge=0)]
    newly_required_valid: Annotated[int, Field(ge=0)]
    newly_valid: Annotated[int, Field(ge=0)]
    no_longer_required: Annotated[int, Field(ge=0)]
    still_invalid: Annotated[int, Field(ge=0)]
    still_valid: Annotated[int, Field(ge=0)]
    unchanged_not_required: Annotated[int, Field(ge=0)]
    uninspectable: Annotated[int, Field(ge=0)]


class SchemaIssue(APIModel):
    actual: (
        Literal["null"]
        | Literal["boolean"]
        | Literal["number"]
        | SchemaActualValueString
        | SchemaActualValueArray
        | SchemaActualValueObject
    )
    alternative: bool
    expected: SchemaExpectedValueAvailable | SchemaExpectedValueOmitted
    instance_path: str | None = None
    message: str
    omissions: list[
        Literal[
            "actual_value_redacted",
            "instance_path_redacted_or_too_long",
            "schema_constraint_unavailable_or_too_large",
        ]
    ]
    reason: SchemaFailure


class SchemaRepairReportRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    object_url_template: str
    template_id: ExportTemplateID | None = None


class SchemaStageRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    json_schema: JsonValue | None = None
    validate_schema: bool


class SchemaValidationConfig(APIModel):
    max_expanded_work: Annotated[int, Field(ge=0)]
    max_instance_bytes: Annotated[int, Field(ge=0)]
    max_instance_work: Annotated[int, Field(ge=0)]
    max_schema_bytes: Annotated[int, Field(ge=0)]


class SearchHydrationPath(APIModel):
    object_ids: list[int]
    relation_ids: list[int]


class SecretSourceConfig(APIModel):
    cache_capacity_per_consumer: Annotated[int, Field(ge=0)]
    cache_total_bytes_per_consumer: Annotated[int, Field(ge=0)]
    cache_ttl_seconds: Annotated[int, Field(ge=0)]
    file_root_configured: bool
    projected_symlinks_confined_to_root: bool
    provider: str
    stale_values_allowed: bool


class SecretStatus(APIModel):
    configured: bool


class ServiceAccountPointResponse(APIModel):
    created_at: AwareDatetime
    created_by: int | None = None
    description: str
    disabled_at: AwareDatetime | None = None
    id: int
    identity_scope_id: int
    name: str
    owner_group_id: int
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class ServiceAccountResponse(APIModel):
    created_at: AwareDatetime
    created_by: int | None = None
    description: str
    disabled_at: AwareDatetime | None = None
    id: int
    identity_scope: str
    name: str
    owner_group_id: int
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class SessionLoginRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str
    identity_scope: str | None = None
    name: str
    password: SecretStr


class SessionRefreshRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str
    refresh_token: SecretStr


class SessionResponse(APIModel):
    absolute_expires_at: AwareDatetime
    access_expires_at: AwareDatetime
    access_token: SecretStr
    refresh_expires_at: AwareDatetime
    refresh_token: SecretStr
    session_id: UUID
    token_type: str


class SharedComputedScopeResponse(APIModel):
    errors: dict[str, ComputedFieldErrorResponse]
    materialization_stale: bool
    revision: int
    values: dict[str, JsonValue]


class StructuredClassSelectorId(APIModel):
    id: Annotated[int, Field(ge=1)]


class StructuredClassSelectorName(APIModel):
    name: Annotated[str, Field(min_length=1)]


class StructuredSearchResultServiceAccount(APIModel):
    kind: Literal["service_account"]
    resource: ServiceAccountResponse


class StructuredSearchStartedEvent(APIModel):
    kind: Literal[
        "collection", "class", "object", "audit_event", "user", "group", "service_account"
    ]
    version: Annotated[int, Field(ge=0)]


class StructuredSearchTargetCollection(APIModel):
    kind: Literal["collection"]


class StructuredSearchTargetClass(APIModel):
    kind: Literal["class"]


class StructuredSearchTargetObject(APIModel):
    class_: Annotated[
        StructuredClassSelectorId | StructuredClassSelectorName | None, Field(alias="class")
    ] = None
    kind: Literal["object"]


class StructuredSearchTargetAuditEvent(APIModel):
    kind: Literal["audit_event"]


class StructuredSearchTargetUser(APIModel):
    kind: Literal["user"]


class StructuredSearchTargetGroup(APIModel):
    kind: Literal["group"]


class StructuredSearchTargetServiceAccount(APIModel):
    kind: Literal["service_account"]


class TaskConfig(APIModel):
    backup_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    computed_reindex_batch_size: Annotated[int, Field(ge=0)]
    export_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    export_max_active_per_user: Annotated[int, Field(ge=0)]
    heartbeat_seconds: Annotated[int, Field(ge=0)]
    import_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    import_max_active_per_user: Annotated[int, Field(ge=0)]
    lease_seconds: Annotated[int, Field(ge=0)]
    poll_interval_ms: Annotated[int, Field(ge=0)]
    recovery_interval_seconds: Annotated[int, Field(ge=0)]
    reindex_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    remote_call_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    remote_call_max_active_per_user: Annotated[int, Field(ge=0)]
    schema_validation_execution_timeout_seconds: Annotated[int, Field(ge=0)]
    workers: Annotated[int, Field(ge=0)]


class TaskDiscoveryTargetCollection(APIModel):
    collection_id: Annotated[int, Field(ge=1)]
    type: Literal["collection"]


class TaskDiscoveryTargetClass(APIModel):
    class_id: Annotated[int, Field(ge=1)]
    type: Literal["class"]


class TaskDiscoveryTargetObject(APIModel):
    class_id: HubuumClassID | None = None
    object_id: Annotated[int, Field(ge=1)]
    type: Literal["object"]


class TaskDiscoveryTargetClassRelation(APIModel):
    relation_id: Annotated[int, Field(ge=1)]
    type: Literal["class_relation"]


class TaskDiscoveryTargetObjectRelation(APIModel):
    relation_id: Annotated[int, Field(ge=1)]
    type: Literal["object_relation"]


class TaskLinks(APIModel):
    backup: str | None = None
    backup_output: str | None = None
    events: str
    export: str | None = None
    export_output: str | None = None
    import_: Annotated[str | None, Field(alias="import")] = None
    import_results: str | None = None
    task: str


class TaskProgress(APIModel):
    failed_items: int
    processed_items: int
    success_items: int
    total_items: int


class TaskQueueStateResponse(APIModel):
    active_tasks: int
    actix_workers: Annotated[int, Field(ge=0)]
    cancelled_tasks: int
    configured_task_workers: Annotated[int, Field(ge=0)]
    export_tasks: int
    failed_tasks: int
    import_tasks: int
    oldest_active_at: str | None = None
    oldest_queued_at: str | None = None
    partially_succeeded_tasks: int
    queued_tasks: int
    reindex_tasks: int
    running_tasks: int
    succeeded_tasks: int
    task_poll_interval_ms: Annotated[int, Field(ge=0)]
    total_import_result_rows: int
    total_task_events: int
    total_tasks: int
    validating_tasks: int


class TestOperation(APIModel):
    path: str
    value: JsonValue


class TlsConfig(APIModel):
    backend: str | None = None
    certificate_path_configured: bool
    enabled: bool
    private_key_passphrase: SecretStatus
    private_key_path: SecretStatus


class TokenResourceScopeCollection(APIModel):
    id: Annotated[int, Field(ge=1)]
    kind: Literal["collection"]


class TokenResourceScopeClass(APIModel):
    id: Annotated[int, Field(ge=1)]
    kind: Literal["class"]


class TokenResourceScopeObject(APIModel):
    id: Annotated[int, Field(ge=1)]
    kind: Literal["object"]


class TokenScopeDetails(APIModel):
    model_config = ConfigDict(extra="forbid")
    permissions: (
        list[
            Literal[
                "ReadCollection",
                "UpdateCollection",
                "DeleteCollection",
                "DelegateCollection",
                "CreateClass",
                "ReadClass",
                "UpdateClass",
                "DeleteClass",
                "CreateObject",
                "ReadObject",
                "UpdateObject",
                "DeleteObject",
                "CreateClassRelation",
                "ReadClassRelation",
                "UpdateClassRelation",
                "DeleteClassRelation",
                "CreateObjectRelation",
                "ReadObjectRelation",
                "UpdateObjectRelation",
                "DeleteObjectRelation",
                "ReadTemplate",
                "CreateTemplate",
                "UpdateTemplate",
                "DeleteTemplate",
                "ReadRemoteTarget",
                "CreateRemoteTarget",
                "UpdateRemoteTarget",
                "DeleteRemoteTarget",
                "ExecuteRemoteTarget",
                "ReadAudit",
                "ManageEventSubscription",
            ]
        ]
        | None
    ) = None
    resources: Annotated[
        list[TokenResourceScopeCollection | TokenResourceScopeClass | TokenResourceScopeObject]
        | None,
        Field(max_length=1000),
    ] = None


class TracingConfig(APIModel):
    batch_size: Annotated[int, Field(ge=0)]
    ca_certificate_configured: bool
    client_certificate_configured: bool
    client_private_key: SecretStatus
    connect_timeout_ms: Annotated[int, Field(ge=0)]
    deployment_environment: str
    enabled: bool
    endpoint: SecretStatus
    export_timeout_ms: Annotated[int, Field(ge=0)]
    flush_timeout_ms: Annotated[int, Field(ge=0)]
    propagate_outbound: bool
    protocol: str
    queue_capacity: Annotated[int, Field(ge=0)]
    sampling_mode: str
    sampling_ratio: float
    service_name: str
    service_namespace: str
    static_headers: SecretStatus
    trust_incoming_sampling: bool


class UnifiedSearchDoneEvent(APIModel):
    query: str


class UnifiedSearchErrorEvent(APIModel):
    message: str


class UnifiedSearchNext(APIModel):
    classes: str | None = None
    collections: str | None = None
    objects: str | None = None


class UnifiedSearchStartedEvent(APIModel):
    query: str


class UpdateClassRelationLabels(APIModel):
    model_config = ConfigDict(extra="forbid")
    forward_label: RelationLabel | None = None
    reverse_label: RelationLabel | None = None


class UpdateCollection(APIModel):
    description: str | None = None
    name: str | None = None


class UpdateCollectionParent(APIModel):
    parent_collection_id: Annotated[int, Field(ge=1)]


class UpdateEventSink(APIModel):
    config: JsonValue | None = None
    delivery_policy: EventDeliveryPolicy | None = None
    enabled: bool | None = None
    kind: Literal["webhook", "amqp", "valkey_stream", "email"] | None = None
    name: str | None = None
    secret_ref: str | None = None


class UpdateGroup(APIModel):
    groupname: str | None = None


class UpdateHubuumClass(APIModel):
    collection_id: int | None = None
    description: str | None = None
    json_schema: JsonValue | None = None
    name: str | None = None
    validate_schema: bool | None = None


class UpdateHubuumObject(APIModel):
    collection_id: int | None = None
    data: JsonValue | None = None
    description: str | None = None
    hubuum_class_id: int | None = None
    name: str | None = None


class UpdateHubuumObjectRequest(APIModel):
    collection_id: int | None = None
    data: JsonValue | None = None
    description: str | None = None
    hubuum_class_id: int | None = None
    name: str | None = None


class UpdateRemoteTarget(APIModel):
    allowed_subject_types: (
        list[Literal["collection", "class", "object", "class_relation", "object_relation"]] | None
    ) = None
    auth_config: (
        RemoteAuthConfigNone
        | RemoteAuthConfigBearerSecret
        | RemoteAuthConfigBasicSecret
        | RemoteAuthConfigApiKeySecret
        | None
    ) = None
    body_template: str | None = None
    class_id: int | None = None
    collection_id: CollectionID | None = None
    description: str | None = None
    enabled: bool | None = None
    headers_template: JsonValue | None = None
    method: Literal["get", "post", "patch", "delete"] | None = None
    name: str | None = None
    timeout_ms: int | None = None
    url_template: str | None = None


class UpdateServiceAccount(APIModel):
    description: str | None = None
    owner_group_id: int | None = None


class UpdateUser(APIModel):
    email: str | None = None
    password: Annotated[SecretStr | None, Field(max_length=4096, min_length=1)] = None
    proper_name: str | None = None


class UserPointResponse(APIModel):
    created_at: AwareDatetime
    email: str | None = None
    id: int
    identity_scope_id: int
    name: str
    proper_name: str | None = None
    provider_managed: bool
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class UserResponse(APIModel):
    created_at: AwareDatetime
    email: str | None = None
    id: int
    identity_scope: str
    last_sync_attempted_at: AwareDatetime | None = None
    last_sync_success_at: AwareDatetime | None = None
    name: str
    proper_name: str | None = None
    provider_kind: str
    provider_managed: bool
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class BackupDocument(APIModel):
    model_config = ConfigDict(extra="forbid")
    backup_version: int
    created_at: AwareDatetime
    history: BackupHistory | None = None
    manifest: BackupManifest
    source_version: str
    state: BackupState


class ClassKey(APIModel):
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    name: str


class ClientConfig(APIModel):
    authentication: ClientAuthenticationConfig
    pagination: ClientPaginationConfig


class Collection(APIModel):
    created_at: AwareDatetime
    description: str
    id: int
    name: str
    parent_collection_id: int | None = None
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class CollectionEventSink(APIModel):
    collection_id: int | None = None
    enabled: bool
    id: int
    kind: Literal["webhook", "amqp", "valkey_stream", "email"]
    name: str
    revision: Annotated[int, Field(ge=1)]
    routing: Literal["fixed", "webhook_url", "email_recipients", "valkey_stream", "amqp"]


class CollectionHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    created_at: AwareDatetime
    description: str
    history_id: int
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    parent_collection_id: int | None = None
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class CollectionPermissionSet(APIModel):
    collection_id: int
    permissions: list[Permission]
    revision: Annotated[int, Field(ge=1)]


class ComputedFieldDefinition(APIModel):
    class_id: int
    created_at: AwareDatetime
    created_by: int | None = None
    description: str
    enabled: bool
    id: int
    key: str
    label: str
    operation: dict[str, JsonValue]
    owner_user_id: int | None = None
    result_type: str
    revision: Annotated[int, Field(ge=1)]
    semantics_version: int
    updated_at: AwareDatetime
    updated_by: int | None = None
    visibility: str


class ComputedFieldDefinitionPatch(APIModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    enabled: bool | None = None
    key: str | None = None
    label: str | None = None
    operation: dict[str, JsonValue] | None = None
    result_type: Literal["string", "number", "integer", "boolean", "object", "array"] | None = None


class ComputedFieldDefinitionRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    enabled: bool | None = None
    key: str
    label: str
    operation: dict[str, JsonValue]
    result_type: Literal["string", "number", "integer", "boolean", "object", "array"]


class ComputedFieldListResponse(APIModel):
    definitions: list[ComputedFieldDefinition]
    state: ClassComputationState


class ComputedFieldMutationResponse(APIModel):
    definition: ComputedFieldDefinition
    state: ClassComputationState


class ComputedFieldPreviewRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    class_id: int | None = None
    data: dict[str, JsonValue] | None = None
    definition: ComputedFieldDefinitionRequest
    object_id: int | None = None


class ComputedObjectScopesResponse(APIModel):
    personal: ComputedScopeResponse | None = None
    shared: SharedComputedScopeResponse


class CountsResponse(APIModel):
    objects_per_class: list[ObjectsByClass]
    total_classes: int
    total_collections: int
    total_objects: int


class CredentialActivityResponse(APIModel):
    best_effort: bool
    collection_enabled: bool
    creation: CredentialCreationResponse | None = None
    limit: Annotated[int, Field(ge=0)]
    next_offset: Annotated[int | None, Field(ge=0)] = None
    offset: Annotated[int, Field(ge=0)]
    overflow_since: AwareDatetime | None = None
    retention_days: int
    session_id: UUID | None = None
    source_cap: Annotated[int, Field(ge=0)]
    sources: list[CredentialSourceResponse]
    total: Annotated[int, Field(ge=0)]


class CredentialApprovalRecord(APIModel):
    actor_id: Annotated[int, Field(ge=1)]
    authenticated_at: AwareDatetime
    consumed_at: AwareDatetime | None = None
    expires_at: AwareDatetime
    id: int
    invalidated_at: AwareDatetime | None = None
    operation: str
    restore_job_id: RestoreJobID | None = None
    target_id: PrincipalID | None = None
    token_id: Annotated[int, Field(ge=1)]


class CredentialApprovalResponse(APIModel):
    approval: SecretStr
    record: CredentialApprovalRecord
    token_expires_at: AwareDatetime | None = None


class CredentialOperationConfirmRestore(APIModel):
    confirmation: RestoreConfirmRequest
    kind: Literal["confirm_restore"]
    restore_id: Annotated[int, Field(ge=1)]


class CredentialOperationRenewToken(APIModel):
    kind: Literal["renew_token"]
    principal_id: Annotated[int, Field(ge=1)]
    token: RenewTokenRequest
    token_id: Annotated[int, Field(ge=1)]


class CredentialOperationCreateUser(APIModel):
    kind: Literal["create_user"]
    user: NewUser


class CredentialOperationUpdateUser(APIModel):
    kind: Literal["update_user"]
    user: UpdateUser
    user_id: Annotated[int, Field(ge=1)]


class CurrentTokenMetadata(APIModel):
    description: str | None = None
    expires_at: AwareDatetime | None = None
    id: Annotated[int, Field(ge=1)]
    issued: AwareDatetime
    last_used_at: AwareDatetime | None = None
    name: str | None = None
    revision: Annotated[int, Field(ge=1)]
    scope: TokenScopeDetails | None = None


class DatabaseConfig(APIModel):
    backend: str
    migrator_role: str
    owner_role: str
    pool_acquire_timeout_ms: Annotated[int, Field(ge=0)]
    pool_size: Annotated[int, Field(ge=0)]
    privilege_mode: str
    role_mode: str
    runtime_role: str
    statement_timeout_ms: Annotated[int, Field(ge=0)]
    url: SecretStatus


class EventNotificationPreview(APIModel):
    payload: JsonValue
    sink_kind: Literal["webhook", "amqp", "valkey_stream", "email"]


class EventNotificationRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    subscription_id: Annotated[int, Field(ge=1)]


class EventSink(APIModel):
    collection_id: int | None = None
    config: JsonValue
    created_at: AwareDatetime
    delivery_policy: EventDeliveryPolicy | None = None
    enabled: bool
    id: int
    kind: Literal["webhook", "amqp", "valkey_stream", "email"]
    name: str
    revision: Annotated[int, Field(ge=1)]
    secret_ref: str | None = None
    updated_at: AwareDatetime


class EventSubject(APIModel):
    authentication_provider_kind: str
    identity_scope: str
    is_admin: bool
    kind: Literal["human", "service_account"]
    name: str
    principal_id: Annotated[int, Field(ge=1)]


class EventSubscriptionFilter(APIModel):
    actor_kinds: list[str] | None = None
    actor_user_ids: list[PrincipalID] | None = None
    collection_ids: list[CollectionID] | None = None
    correlation_ids: list[str] | None = None
    entity_ids: list[EventEntityId] | None = None
    entity_names: list[str] | None = None
    initiator_user_ids: list[PrincipalID] | None = None
    related_collection_ids: list[CollectionID] | None = None
    request_ids: list[UUID] | None = None
    subject_identity_scopes: list[str] | None = None
    subject_is_admin: bool | None = None
    subject_principal_ids: list[PrincipalID] | None = None
    task_kinds: (
        list[Literal["import", "export", "backup", "reindex", "remote_call", "schema_validation"]]
        | None
    ) = None


class EventWorkerHealth(APIModel):
    batch_size: Annotated[int, Field(ge=0)]
    lock_timeout_ms: Annotated[int, Field(ge=0)]
    poll_interval_ms: Annotated[int, Field(ge=0)]
    wakeups: EventWorkerWakeupStats
    workers_configured: Annotated[int, Field(ge=0)]


class ExportIncludeRelatedObject(APIModel):
    class_id: int
    class_relation_id: int | None = None
    direction: Literal["any", "outgoing", "incoming"] | None = None
    limit: int | None = None
    max_depth: int | None = None
    sort: Literal["path", "name", "created_at"] | None = None


class ExportScope(APIModel):
    class_id: Annotated[int | None, Field(ge=1)] = None
    kind: Literal[
        "collections",
        "classes",
        "objects_in_class",
        "class_relations",
        "object_relations",
        "related_objects",
    ]
    object_id: Annotated[int | None, Field(ge=1)] = None


class ExportTemplateHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    class_id: int | None = None
    collection_id: int
    content_type: str
    created_at: AwareDatetime
    default_limits: JsonValue | None = None
    default_missing_data_policy: str | None = None
    default_query: str | None = None
    description: str
    history_id: int
    id: int
    include: JsonValue | None = None
    initiator_user_id: int | None = None
    kind: str
    name: str
    op: str
    relation_context: JsonValue | None = None
    revision: Annotated[int, Field(ge=1)]
    scope_kind: str | None = None
    task_id: int | None = None
    template: str
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class Group(APIModel):
    created_at: AwareDatetime
    description: str
    external_key: str | None = None
    groupname: str
    id: int
    identity_scope_id: int
    last_sync_attempted_at: AwareDatetime | None = None
    last_sync_success_at: AwareDatetime | None = None
    managed_by: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class GroupGrant(APIModel):
    group_id: int
    groupname: str
    permissions: list[
        Literal[
            "ReadCollection",
            "UpdateCollection",
            "DeleteCollection",
            "DelegateCollection",
            "CreateClass",
            "ReadClass",
            "UpdateClass",
            "DeleteClass",
            "CreateObject",
            "ReadObject",
            "UpdateObject",
            "DeleteObject",
            "CreateClassRelation",
            "ReadClassRelation",
            "UpdateClassRelation",
            "DeleteClassRelation",
            "CreateObjectRelation",
            "ReadObjectRelation",
            "UpdateObjectRelation",
            "DeleteObjectRelation",
            "ReadTemplate",
            "CreateTemplate",
            "UpdateTemplate",
            "DeleteTemplate",
            "ReadRemoteTarget",
            "CreateRemoteTarget",
            "UpdateRemoteTarget",
            "DeleteRemoteTarget",
            "ExecuteRemoteTarget",
            "ReadAudit",
            "ManageEventSubscription",
        ]
    ]


class GroupPermission(APIModel):
    group: Group
    permission: Permission


class GroupPointResponse(APIModel):
    created_at: AwareDatetime
    description: str
    external_key: str | None = None
    groupname: str
    id: int
    identity_scope: str
    managed_by: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class GroupResponse(APIModel):
    created_at: AwareDatetime
    description: str
    external_key: str | None = None
    groupname: str
    id: int
    identity_scope: str
    last_sync_attempted_at: AwareDatetime | None = None
    last_sync_success_at: AwareDatetime | None = None
    managed_by: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class HistoricalComputedFieldUnavailable(APIModel):
    reason: Literal[
        "definition_history_unavailable",
        "class_history_unavailable",
        "unsupported_evaluator_version",
        "unsupported_definition_semantics",
    ]
    status: Literal["unavailable"]


class HistoricalComputedField1(APIModel):
    definition_id: int
    key: str
    label: str
    revision: Annotated[int, Field(ge=1)]
    semantics_version: int


class HistoricalComputedField2(HistoricalComputedFieldEvaluated, HistoricalComputedField1):
    pass


class HistoricalComputedFieldEvaluationError(
    HistoricalComputedFieldError, HistoricalComputedField1
):
    pass


class HistoricalComputedField4(HistoricalComputedFieldDisabled, HistoricalComputedField1):
    pass


class HistoricalComputedField5(HistoricalComputedFieldUnavailable, HistoricalComputedField1):
    pass


class HistoricalComputedFieldResultUnavailable(APIModel):
    reason: Literal[
        "definition_history_unavailable",
        "class_history_unavailable",
        "unsupported_evaluator_version",
        "unsupported_definition_semantics",
    ]
    status: Literal["unavailable"]


class HistoricalComputedObjectSource(APIModel):
    class_id: int
    history_id: int
    object_id: int
    revision: Annotated[int, Field(ge=1)]
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class HistoricalEndpointContextUnavailable(APIModel):
    reason: Literal["history_unavailable"]
    status: Literal["unavailable"]


class HistoricalRelationEndpoint(APIModel):
    collection_id: int
    history_id: int
    hubuum_class_id: int | None = None
    id: int
    name: str
    revision: Annotated[int, Field(ge=1)]
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class HistoricalSharedComputedFieldsAvailable(APIModel):
    definition_history_id: int
    evaluator_version: int
    fields: list[
        HistoricalComputedField2
        | HistoricalComputedFieldEvaluationError
        | HistoricalComputedField4
        | HistoricalComputedField5
    ]
    status: Literal["available"]
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class HistoryMarker(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    history_id: int
    hubuum_class_id: int | None = None
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class HubuumClass(APIModel):
    collection_id: int
    created_at: AwareDatetime
    description: str
    id: int
    json_schema: JsonValue | None = None
    name: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime
    validate_schema: bool


class HubuumClassExpanded(APIModel):
    collection: Collection
    created_at: AwareDatetime
    description: str
    id: int
    json_schema: JsonValue | None = None
    name: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime
    validate_schema: bool


class HubuumClassHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    created_at: AwareDatetime
    description: str
    history_id: int
    id: int
    initiator_user_id: int | None = None
    json_schema: JsonValue | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    validate_schema: bool


class HubuumClassRelation(APIModel):
    created_at: AwareDatetime
    forward_label: RelationLabel | None = None
    forward_template_alias: str | None = None
    from_hubuum_class_id: int
    from_max_relations: ObjectRelationLimit | None = None
    id: int
    reverse_label: RelationLabel | None = None
    reverse_template_alias: str | None = None
    revision: Annotated[int, Field(ge=1)]
    to_hubuum_class_id: int
    to_max_relations: ObjectRelationLimit | None = None
    updated_at: AwareDatetime


class HubuumClassWithPath(APIModel):
    collection_id: int
    created_at: AwareDatetime
    description: str
    id: int
    json_schema: JsonValue | None = None
    name: str
    path: list[int]
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime
    validate_schema: bool


class HubuumObject(APIModel):
    collection_id: int
    created_at: AwareDatetime
    data: JsonValue
    description: str
    hubuum_class_id: int
    id: int
    name: str
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class HubuumObjectComputedResponse(HubuumObject):
    computed: ComputedObjectScopesResponse


class HubuumObjectHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    created_at: AwareDatetime
    data: JsonValue
    description: str
    history_id: int
    hubuum_class_id: int
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class HubuumObjectRelation(APIModel):
    class_relation_id: int
    created_at: AwareDatetime
    from_hubuum_object_id: int
    id: int
    revision: Annotated[int, Field(ge=1)]
    to_hubuum_object_id: int
    updated_at: AwareDatetime


class HubuumObjectWithPath(APIModel):
    collection_id: int
    created_at: AwareDatetime
    data: JsonValue
    description: str
    hubuum_class_id: int
    id: int
    name: str
    path: list[int]
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class ImportMembershipSourceInput(APIModel):
    source: str
    source_key: str
    source_scope_key: IdentityScopeKey | None = None
    source_scope_ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportMode(APIModel):
    atomicity: Literal["strict", "best_effort"] | None = None
    collision_policy: Literal["abort", "overwrite"] | None = None
    permission_policy: Literal["abort", "continue"] | None = None


class ImportPrincipalInputServiceAccount(APIModel):
    created_by_key: PrincipalKey | None = None
    created_by_ref: str | None = None
    description: str
    disabled_at: AwareDatetime | None = None
    kind: Literal["service_account"]
    owner_group_key: GroupKey | None = None
    owner_group_ref: str | None = None


class ImportPrincipalSubtypeServiceAccount(APIModel):
    created_by_key: PrincipalKey | None = None
    created_by_ref: str | None = None
    description: str
    disabled_at: AwareDatetime | None = None
    kind: Literal["service_account"]
    owner_group_key: GroupKey | None = None
    owner_group_ref: str | None = None


class ImportSchemaActivation(APIModel):
    model_config = ConfigDict(extra="forbid")
    expected_active_revision: Annotated[int, Field(ge=1)]
    impact_task_id: TaskID | None = None
    policy: Literal["reject_incompatible", "allow_pending"]
    revision: Annotated[int, Field(ge=1)]


class ImportTaskDetails(APIModel):
    results_url: str
    retained: RetainedImportDetails | None = None


class ImportTaskResultResponse(APIModel):
    action: str
    created_at: AwareDatetime
    details: JsonValue | None = None
    entity_kind: str
    error: str | None = None
    id: int
    identifier: str | None = None
    item_ref: str | None = None
    observed_revision: ResourceRevision | None = None
    outcome: str
    task_id: int


class ImportWriteConditionIfRevision(APIModel):
    expected_revision: Annotated[int, Field(ge=1)]
    mode: Literal["if_revision"]


class LoginRateLimitConfig(APIModel):
    backend: str
    backoff_base_seconds: Annotated[int, Field(ge=0)]
    backoff_max_seconds: Annotated[int, Field(ge=0)]
    enabled: bool
    max_attempts: Annotated[int, Field(ge=0)]
    max_attempts_per_account: Annotated[int, Field(ge=0)]
    max_attempts_per_ip: Annotated[int, Field(ge=0)]
    max_attempts_per_subnet: Annotated[int, Field(ge=0)]
    subnet_prefix_v4: Annotated[int, Field(ge=0)]
    subnet_prefix_v6: Annotated[int, Field(ge=0)]
    valkey_io_timeout_ms: Annotated[int, Field(ge=0)]
    valkey_prefix: str
    valkey_url: SecretStatus
    window_seconds: Annotated[int, Field(ge=0)]


class MembershipPrincipalResponse(APIModel):
    created_at: AwareDatetime
    identity_scope: str
    kind: Literal["human", "service_account"]
    name: str
    principal_id: int
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class NewEventSubscription(APIModel):
    actions: list[str]
    description: str | None = None
    enabled: bool | None = None
    entity_types: list[str]
    filter: EventSubscriptionFilter | None = None
    name: str
    routing: JsonValue | None = None
    sink_id: Annotated[int, Field(ge=1)]


class NewHubuumClassRelation(APIModel):
    forward_label: RelationLabel | None = None
    forward_template_alias: str | None = None
    from_hubuum_class_id: int
    from_max_relations: ObjectRelationLimit | None = None
    reverse_label: RelationLabel | None = None
    reverse_template_alias: str | None = None
    to_hubuum_class_id: int
    to_max_relations: ObjectRelationLimit | None = None


class NewHubuumClassRelationFromClass(APIModel):
    forward_label: RelationLabel | None = None
    forward_template_alias: str | None = None
    from_max_relations: ObjectRelationLimit | None = None
    reverse_label: RelationLabel | None = None
    reverse_template_alias: str | None = None
    to_hubuum_class_id: int
    to_max_relations: ObjectRelationLimit | None = None


class NewRemoteTarget(APIModel):
    allowed_subject_types: list[
        Literal["collection", "class", "object", "class_relation", "object_relation"]
    ]
    auth_config: (
        RemoteAuthConfigNone
        | RemoteAuthConfigBearerSecret
        | RemoteAuthConfigBasicSecret
        | RemoteAuthConfigApiKeySecret
        | None
    ) = None
    body_template: str | None = None
    class_id: HubuumClassID | None = None
    collection_id: Annotated[int, Field(ge=1)]
    description: str
    enabled: bool | None = None
    headers_template: JsonValue | None = None
    method: Literal["get", "post", "patch", "delete"]
    name: str
    timeout_ms: int | None = None
    url_template: str


class NewTokenRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    expires_at: AwareDatetime | None = None
    name: str | None = None
    scope: TokenScopeDetails | None = None


class ObjectAggregateDimensionValue(APIModel):
    field: str
    state: Literal["value", "null", "missing", "unavailable"]
    value: JsonValue | None = None


class ObjectAggregateRow(APIModel):
    dimensions: list[ObjectAggregateDimensionValue]
    measures: list[ObjectAggregateMeasureValue] | None = None
    object_count: int


class ObjectDataPatchDocument2(RemoveOperation):
    op: Literal["remove"]


class ObjectDataPatchDocument3(ReplaceOperation):
    op: Literal["replace"]


class ObjectDataPatchDocument6(TestOperation):
    op: Literal["test"]


class ObjectKey(APIModel):
    class_key: ClassKey | None = None
    class_ref: str | None = None
    name: str


class PatchOperation2(RemoveOperation):
    op: Literal["remove"]


class PatchOperation3(ReplaceOperation):
    op: Literal["replace"]


class PatchOperation6(TestOperation):
    op: Literal["test"]


class PermissionConfig(APIModel):
    backend: str
    treetop_accept_invalid_certificates: bool
    treetop_ca_certificate_configured: bool
    treetop_connect_timeout_ms: Annotated[int, Field(ge=0)]
    treetop_request_timeout_ms: Annotated[int, Field(ge=0)]
    treetop_url: SecretStatus


class PersonalComputedFieldDefinitionRequest(ComputedFieldDefinitionRequest):
    class_id: int


class PrincipalCollectionPermissions(APIModel):
    collection_id: int
    collection_name: str
    grants: list[GroupGrant]


class PrincipalMemberResponse(APIModel):
    created_at: AwareDatetime
    group_id: int
    principal: MembershipPrincipalResponse | None = None
    principal_id: int
    revision: Annotated[int, Field(ge=1)]
    updated_at: AwareDatetime


class PrincipalSettingsPatchDocument2(RemoveOperation):
    op: Literal["remove"]


class PrincipalSettingsPatchDocument3(ReplaceOperation):
    op: Literal["replace"]


class PrincipalSettingsPatchDocument6(TestOperation):
    op: Literal["test"]


class PrincipalSettingsResponse(APIModel):
    revision: Annotated[int, Field(ge=1)]
    settings: dict[str, JsonValue]


class PrincipalTokenMetadata(APIModel):
    active: bool
    description: str | None = None
    expired: bool
    expires_at: AwareDatetime | None = None
    id: Annotated[int, Field(ge=1)]
    issued: AwareDatetime
    last_used_at: AwareDatetime | None = None
    name: str | None = None
    principal_id: Annotated[int, Field(ge=1)]
    revision: Annotated[int, Field(ge=1)]
    revoked_at: AwareDatetime | None = None
    scope: TokenScopeDetails | None = None


class PrincipalTokenPointResponse(APIModel):
    description: str | None = None
    expires_at: AwareDatetime | None = None
    id: Annotated[int, Field(ge=1)]
    issued: AwareDatetime
    name: str | None = None
    principal_id: Annotated[int, Field(ge=1)]
    revision: Annotated[int, Field(ge=1)]
    revoked_at: AwareDatetime | None = None
    scope: TokenScopeDetails | None = None


class ProvenanceActor(APIModel):
    kind: str | None = None
    principal: ProvenancePrincipal | None = None


class QueryUsagePatternSchema(APIModel):
    model_config = ConfigDict(extra="forbid")
    operations: list[Literal["equals", "gt", "gte", "lt", "lte", "between"]]
    path: str
    value_type: Literal["string", "numeric", "boolean"]


class QueryUsageReplaceRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: Annotated[int, Field(ge=1)]
    pattern: QueryUsagePatternSchema


class QueryUsageResource(APIModel):
    bytes: Annotated[int, Field(ge=0)]
    cleanup_eligible_if_removed: bool
    declaration_owners: Annotated[int | None, Field(ge=0)] = None
    native_scan_count: Annotated[int | None, Field(ge=0)] = None
    ownership: Literal["independently_managed", "declaration_managed"]
    reference: str


class QueryUsageResponse(APIModel):
    class_id: Annotated[int, Field(ge=1)]
    created_at: AwareDatetime
    created_by: PrincipalID | None = None
    id: Annotated[int, Field(ge=1)]
    pattern: QueryUsagePatternSchema
    revision: Annotated[int, Field(ge=1)]
    schema_compatibility: Literal["compatible", "incompatible", "unknown"]
    updated_at: AwareDatetime
    updated_by: PrincipalID | None = None


class RelatedClassGraph(APIModel):
    classes: list[HubuumClassWithPath]
    relations: list[HubuumClassRelation]


class RelatedObjectGraph(APIModel):
    class_relations: list[HubuumClassRelation]
    objects: list[HubuumObjectWithPath]
    relations: list[HubuumObjectRelation]


class RemoteCallTaskDetails(APIModel):
    remote_target_id: RemoteTargetID | None = None
    target: (
        TaskDiscoveryTargetCollection
        | TaskDiscoveryTargetClass
        | TaskDiscoveryTargetObject
        | TaskDiscoveryTargetClassRelation
        | TaskDiscoveryTargetObjectRelation
        | None
    ) = None


class RemoteTarget(APIModel):
    allowed_subject_types: list[
        Literal["collection", "class", "object", "class_relation", "object_relation"]
    ]
    auth_config: (
        RemoteAuthConfigNone
        | RemoteAuthConfigBearerSecret
        | RemoteAuthConfigBasicSecret
        | RemoteAuthConfigApiKeySecret
    )
    body_template: str | None = None
    class_id: int | None = None
    collection_id: int
    created_at: AwareDatetime
    description: str
    enabled: bool
    headers_template: JsonValue
    id: int
    method: Literal["get", "post", "patch", "delete"]
    name: str
    revision: Annotated[int, Field(ge=1)]
    timeout_ms: int
    updated_at: AwareDatetime
    url_template: str


class RemoteTargetHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    allowed_subject_types: JsonValue
    auth_config: JsonValue
    body_template: str | None = None
    class_id: int | None = None
    collection_id: int
    created_at: AwareDatetime
    description: str
    enabled: bool
    headers_template: JsonValue
    history_id: int
    id: int
    initiator_user_id: int | None = None
    method: str
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    timeout_ms: int
    updated_at: AwareDatetime
    url_template: str
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None


class RestoreStageResponse(APIModel):
    byte_size: int
    confirmed_at: AwareDatetime | None = None
    created_at: AwareDatetime
    error: str | None = None
    expires_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    id: int
    requested_by: int | None = None
    requested_by_identity_scope: str
    requested_by_name: str
    restore_capability: str | None = None
    sha256: str
    started_at: AwareDatetime | None = None
    status: Literal["validated", "confirmed", "succeeded", "failed", "expired"]
    updated_at: AwareDatetime
    validation: RestoreValidationSummary


class RetainedBackupDetails(APIModel):
    include_history: bool | None = None
    output_state: Literal["available", "expired", "not_produced", "unknown"]


class RetainedExportDetails(APIModel):
    max_items: Annotated[int | None, Field(ge=0)] = None
    max_output_bytes: Annotated[int | None, Field(ge=0)] = None
    missing_data_policy: Literal["strict", "null", "omit"] | None = None
    output_state: Literal["available", "expired", "not_produced", "unknown"]
    scope_kind: (
        Literal[
            "collections",
            "classes",
            "objects_in_class",
            "class_relations",
            "object_relations",
            "related_objects",
        ]
        | None
    ) = None
    target: (
        TaskDiscoveryTargetCollection
        | TaskDiscoveryTargetClass
        | TaskDiscoveryTargetObject
        | TaskDiscoveryTargetClassRelation
        | TaskDiscoveryTargetObjectRelation
        | None
    ) = None
    template_id: ExportTemplateID | None = None
    truncated: bool | None = None
    warning_count: int | None = None


class SchemaActivationRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    expected_active_revision: Annotated[int, Field(ge=1)]
    impact_task_id: TaskID | None = None
    policy: Literal["reject_incompatible", "allow_pending"]


class SchemaDiagnostics(APIModel):
    issues: list[SchemaIssue]
    truncated: bool


class SchemaReference(APIModel):
    class_id: Annotated[int, Field(ge=1)]
    revision: Annotated[int, Field(ge=1)]


class SchemaRevisionResponse(APIModel):
    activated_at: AwareDatetime | None = None
    activation_policy: Literal["reject_incompatible", "allow_pending"] | None = None
    class_id: Annotated[int, Field(ge=1)]
    created_at: AwareDatetime
    created_by: int | None = None
    json_schema: JsonValue | None = None
    revision: Annotated[int, Field(ge=1)]
    status: Literal["staged", "active", "retired", "abandoned"]
    validate_schema: bool


class SchemaTaskDetails(APIModel):
    class_id: HubuumClassID | None = None
    results_url: str | None = None
    schema_revision: SchemaRevision | None = None
    work_kind: Literal["impact", "revalidation"] | None = None
    work_status: Literal["running", "failed", "complete", "cancelled", "superseded"] | None = None


class SearchHydrationRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    class_: Annotated[StructuredClassSelectorId | StructuredClassSelectorName, Field(alias="class")]
    depth: Annotated[int, Field(ge=1, le=10)]
    limit: Annotated[int, Field(ge=1, le=50)]
    root_class_id: Annotated[int, Field(ge=1)]
    root_object_id: Annotated[int, Field(ge=1)]
    version: Annotated[int, Field(ge=1, le=1)]


class SearchHydrationResponse(APIModel):
    depth: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=0)]
    objects: list[HubuumObject]
    paths: list[SearchHydrationPath]
    relations: list[HubuumObjectRelation]
    root_object_id: int
    target_class_id: int
    truncated: bool
    version: Annotated[int, Field(ge=0)]


class ServerConfig(APIModel):
    actix_workers: Annotated[int, Field(ge=0)]
    bind_ip: str
    bind_port: Annotated[int, Field(ge=0)]
    log_level: str
    metrics_enabled: bool
    metrics_path: str
    runtime_role: str
    tls: TlsConfig


class StructuredSearchDoneEvent(APIModel):
    kind: Literal[
        "collection", "class", "object", "audit_event", "user", "group", "service_account"
    ]
    next: str | None = None
    page_limit: Annotated[int, Field(ge=0)]
    total: int | None = None
    version: Annotated[int, Field(ge=0)]


class StructuredSearchErrorEvent(APIModel):
    kind: Literal[
        "collection", "class", "object", "audit_event", "user", "group", "service_account"
    ]
    message: str
    version: Annotated[int, Field(ge=0)]


class StructuredSearchFieldPredicate(APIModel):
    model_config = ConfigDict(extra="forbid")
    field: Literal[
        "id",
        "name",
        "description",
        "collection_id",
        "created_at",
        "updated_at",
        "revision",
        "json_data",
        "validate_schema",
        "json_schema",
        "identity_scope",
        "proper_name",
        "email",
        "occurred_at",
        "entity_type",
        "entity_id",
        "entity_name",
        "action",
        "actor_kind",
        "actor_user_id",
        "initiator_user_id",
        "summary",
        "metadata",
        "managed_by",
        "external_key",
        "last_sync_attempted_at",
        "last_sync_success_at",
        "owner_group_id",
        "created_by",
        "disabled_at",
    ]
    operator: Literal[
        "equals",
        "iequals",
        "contains",
        "icontains",
        "startswith",
        "istartswith",
        "endswith",
        "iendswith",
        "like",
        "regex",
        "gt",
        "gte",
        "lt",
        "lte",
        "between",
        "within_network",
        "contains_network",
        "contains_ip",
        "overlaps_network",
        "inet_equals",
        "in",
        "all",
        "array_length",
        "has_key",
        "is_null",
    ]
    path: Annotated[str | None, Field(min_length=1)] = None
    value: JsonValue | None = None


class StructuredSearchResultCollection(APIModel):
    kind: Literal["collection"]
    resource: Collection


class StructuredSearchResultClass(APIModel):
    kind: Literal["class"]
    resource: HubuumClassExpanded


class StructuredSearchResultObject(APIModel):
    kind: Literal["object"]
    resource: HubuumObject


class StructuredSearchResultUser(APIModel):
    kind: Literal["user"]
    resource: UserResponse


class StructuredSearchResultGroup(APIModel):
    kind: Literal["group"]
    resource: GroupResponse


class StructuredSearchSort(APIModel):
    model_config = ConfigDict(extra="forbid")
    direction: Literal["asc", "desc"] | None = None
    field: Literal[
        "id",
        "name",
        "description",
        "collection_id",
        "created_at",
        "updated_at",
        "revision",
        "json_data",
        "validate_schema",
        "json_schema",
        "identity_scope",
        "proper_name",
        "email",
        "occurred_at",
        "entity_type",
        "entity_id",
        "entity_name",
        "action",
        "actor_kind",
        "actor_user_id",
        "initiator_user_id",
        "summary",
        "metadata",
        "managed_by",
        "external_key",
        "last_sync_attempted_at",
        "last_sync_success_at",
        "owner_group_id",
        "created_by",
        "disabled_at",
    ]


class SystemEventSubscription(APIModel):
    actions: list[str]
    created_at: AwareDatetime
    description: str
    enabled: bool
    entity_types: list[str]
    filter: EventSubscriptionFilter | None = None
    id: int
    name: str
    revision: Annotated[int, Field(ge=1)]
    routing: JsonValue
    sink_id: int
    updated_at: AwareDatetime


class TaskCancelRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    expected_status: (
        Literal[
            "queued",
            "validating",
            "running",
            "succeeded",
            "failed",
            "partially_succeeded",
            "cancelled",
        ]
        | None
    ) = None
    reason: Annotated[str | None, Field(max_length=512)] = None


class UnifiedSearchBatchResponse(APIModel):
    classes: list[HubuumClassExpanded]
    collections: list[Collection]
    kind: str
    next: str | None = None
    objects: list[HubuumObject]


class UnifiedSearchResults(APIModel):
    classes: list[HubuumClassExpanded]
    collections: list[Collection]
    objects: list[HubuumObject]


class UpdateEventSubscription(APIModel):
    actions: list[str] | None = None
    description: str | None = None
    enabled: bool | None = None
    entity_types: list[str] | None = None
    filter: EventSubscriptionFilter | None = None
    name: str | None = None
    routing: JsonValue | None = None
    sink_id: EventSinkID | None = None


class AuthenticationConfig(APIModel):
    active_token_hash_key_id: str
    admin_groupname: str
    admin_identity_scope: str | None = None
    credential_activity_enabled: bool
    credential_activity_retention_days: int
    credential_activity_source_cap: Annotated[int, Field(ge=0)]
    login_rate_limit: LoginRateLimitConfig
    max_token_lifetime_hours: int
    previous_token_hash_key_ids: list[str]
    provider_config_path: SecretStatus
    require_stable_token_hash_key: bool
    session_absolute_seconds: int
    session_access_seconds: int
    session_idle_seconds: int
    session_retention_seconds: int
    stable_token_hash_key_configured: bool
    token_hash_key_mode: str
    token_hash_key_ring_identity: str
    token_lifetime_hours: int
    token_retention_days: int
    token_retention_purge_batch_size: Annotated[int, Field(ge=10)]
    token_retention_purge_enabled: bool
    token_retention_purge_interval_seconds: Annotated[int, Field(ge=0)]


class BackupTaskDetails(APIModel):
    byte_size: int | None = None
    output_available: bool
    output_expired: bool
    output_expires_at: AwareDatetime | None = None
    output_url: str
    retained: RetainedBackupDetails | None = None
    sha256: str | None = None


class ClassSchemaResponse(APIModel):
    active: SchemaRevisionResponse
    counts: SchemaComplianceCounts
    object_epoch: Annotated[int, Field(ge=0)]


class CredentialOperationCreateToken(APIModel):
    kind: Literal["create_token"]
    principal_id: Annotated[int, Field(ge=1)]
    token: NewTokenRequest


class EffectiveGroupPermission(APIModel):
    depth: int
    group: Group
    inherited: bool
    permission: Permission
    source_collection: Collection
    target_collection: Collection


class EventDeliveryQueueHealth(APIModel):
    counts: EventDeliveryStatusCounts
    oldest_due_age_seconds: int | None = None
    stale_claims: int
    worker: EventWorkerHealth


class EventFanoutHealth(APIModel):
    in_flight_events: int
    oldest_pending_age_seconds: int | None = None
    pending_events: int
    stale_claims: int
    worker: EventWorkerHealth


class EventSubscription(APIModel):
    actions: list[str]
    collection_id: int
    created_at: AwareDatetime
    description: str
    enabled: bool
    entity_types: list[str]
    filter: EventSubscriptionFilter | None = None
    id: int
    name: str
    revision: Annotated[int, Field(ge=1)]
    routing: JsonValue
    sink_id: int
    updated_at: AwareDatetime


class ExportInclude(APIModel):
    related_objects: dict[str, ExportIncludeRelatedObject] | None = None


class ExportMeta(APIModel):
    content_type: Literal["application/json", "text/plain", "text/html", "text/csv"]
    count: Annotated[int, Field(ge=0)]
    scope: ExportScope
    truncated: bool


class ExportRequest(APIModel):
    include: ExportInclude | None = None
    limits: ExportLimits | None = None
    missing_data_policy: Literal["strict", "null", "omit"] | None = None
    query: str | None = None
    relation_context: ExportRelationContext | None = None
    scope: ExportScope


class ExportTaskDetails(APIModel):
    hydration_duration_ms: int | None = None
    output_available: bool
    output_content_type: str | None = None
    output_expired: bool
    output_expires_at: AwareDatetime | None = None
    output_url: str
    query_duration_ms: int | None = None
    render_duration_ms: int | None = None
    retained: RetainedExportDetails | None = None
    template_name: str | None = None
    total_duration_ms: int | None = None
    truncated: bool | None = None
    warning_count: int | None = None


class ExportTemplate(APIModel):
    class_id: int | None = None
    collection_id: int
    content_type: Literal["application/json", "text/plain", "text/html", "text/csv"]
    created_at: AwareDatetime
    default_limits: ExportLimits | None = None
    default_missing_data_policy: Literal["strict", "null", "omit"] | None = None
    default_query: str | None = None
    description: str
    id: int
    include: ExportInclude | None = None
    kind: Literal["export", "fragment"]
    name: str
    relation_context: ExportRelationContext | None = None
    revision: Annotated[int, Field(ge=1)]
    scope_kind: (
        Literal[
            "collections",
            "classes",
            "objects_in_class",
            "class_relations",
            "object_relations",
            "related_objects",
        ]
        | None
    ) = None
    template: str
    updated_at: AwareDatetime


class HistoricalComputedValues(APIModel):
    at: AwareDatetime
    mode: Literal["historical_recomputation"]
    object: HistoricalComputedObjectSource
    personal: Literal["unsupported"]
    shared: HistoricalSharedComputedFieldsAvailable | HistoricalSharedComputedFieldsUnavailable


class HistoricalEndpointContextAvailable(APIModel):
    snapshot: HistoricalRelationEndpoint
    status: Literal["available"]


class HistoricalRelationValueClass(APIModel):
    kind: Literal["class"]
    relation: HubuumClassRelation


class HistoricalRelationValueObject(APIModel):
    kind: Literal["object"]
    relation: HubuumObjectRelation


class HistoryResponseHistoricalRelationClass(APIModel):
    kind: Literal["class"]
    relation: HubuumClassRelation


class HistoryResponseHistoricalRelationObject(APIModel):
    kind: Literal["object"]
    relation: HubuumObjectRelation


class ImportClassInput(APIModel):
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str
    json_schema: JsonValue | None = None
    name: str
    ref: str | None = None
    schema_activation: ImportSchemaActivation | None = None
    timestamps: RestoreTimestamps | None = None
    validate_schema: bool | None = None


class ImportClassRelationInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    forward_label: RelationLabel | None = None
    forward_template_alias: str | None = None
    from_class_key: ClassKey | None = None
    from_class_ref: str | None = None
    from_max_relations: ObjectRelationLimit | None = None
    ref: str | None = None
    reverse_label: RelationLabel | None = None
    reverse_template_alias: str | None = None
    timestamps: RestoreTimestamps | None = None
    to_class_key: ClassKey | None = None
    to_class_ref: str | None = None
    to_max_relations: ObjectRelationLimit | None = None


class ImportCollectionInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str
    name: str
    parent_collection_key: CollectionKey | None = None
    parent_collection_ref: str | None = None
    ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportCollectionPermissionInput(APIModel):
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    group_key: GroupKey
    permissions: list[
        Literal[
            "ReadCollection",
            "UpdateCollection",
            "DeleteCollection",
            "DelegateCollection",
            "CreateClass",
            "ReadClass",
            "UpdateClass",
            "DeleteClass",
            "CreateObject",
            "ReadObject",
            "UpdateObject",
            "DeleteObject",
            "CreateClassRelation",
            "ReadClassRelation",
            "UpdateClassRelation",
            "DeleteClassRelation",
            "CreateObjectRelation",
            "ReadObjectRelation",
            "UpdateObjectRelation",
            "DeleteObjectRelation",
            "ReadTemplate",
            "CreateTemplate",
            "UpdateTemplate",
            "DeleteTemplate",
            "ReadRemoteTarget",
            "CreateRemoteTarget",
            "UpdateRemoteTarget",
            "DeleteRemoteTarget",
            "ExecuteRemoteTarget",
            "ReadAudit",
            "ManageEventSubscription",
        ]
    ]
    ref: str | None = None
    replace_existing: bool | None = None


class ImportComputedFieldInput(APIModel):
    class_key: ClassKey | None = None
    class_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str | None = None
    enabled: bool
    key: str
    label: str
    operation: dict[str, JsonValue]
    owner_key: PrincipalKey | None = None
    owner_ref: str | None = None
    ref: str | None = None
    result_type: Literal["string", "number", "integer", "boolean", "object", "array"]
    timestamps: RestoreTimestamps | None = None
    visibility: Literal["shared", "personal"]


class ImportEventSinkInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    config: JsonValue | None = None
    delivery_policy: EventDeliveryPolicy | None = None
    enabled: bool
    kind: Literal["webhook", "amqp", "valkey_stream", "email"]
    name: str
    ref: str | None = None
    secret_ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportEventSubscriptionInput(APIModel):
    actions: list[str]
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str
    enabled: bool
    entity_types: list[str]
    filter: JsonValue | None = None
    name: str
    ref: str | None = None
    routing: JsonValue | None = None
    sink_key: EventSinkKey | None = None
    sink_ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportExportTemplateInput(APIModel):
    class_key: ClassKey | None = None
    class_ref: str | None = None
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    content_type: Literal["application/json", "text/plain", "text/html", "text/csv"]
    default_limits: ExportLimits | None = None
    default_missing_data_policy: Literal["strict", "null", "omit"] | None = None
    default_query: str | None = None
    description: str
    include: ExportInclude | None = None
    kind: Literal["export", "fragment"]
    name: str
    ref: str | None = None
    relation_context: ExportRelationContext | None = None
    scope_kind: (
        Literal[
            "collections",
            "classes",
            "objects_in_class",
            "class_relations",
            "object_relations",
            "related_objects",
        ]
        | None
    ) = None
    template: str
    timestamps: RestoreTimestamps | None = None


class ImportGroupInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str
    external_key: str | None = None
    groupname: str
    identity_scope_key: IdentityScopeKey | None = None
    identity_scope_ref: str | None = None
    last_sync_attempted_at: AwareDatetime | None = None
    last_sync_success_at: AwareDatetime | None = None
    managed_by: str
    ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportGroupMembershipInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    group_key: GroupKey | None = None
    group_ref: str | None = None
    principal_key: PrincipalKey | None = None
    principal_ref: str | None = None
    ref: str | None = None
    sources: list[ImportMembershipSourceInput] | None = None
    timestamps: RestoreTimestamps | None = None


class ImportIdentityScopeInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    name: str
    provider_kind: str
    ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportObjectInput(APIModel):
    class_key: ClassKey | None = None
    class_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    data: JsonValue
    description: str
    name: str
    ref: str | None = None
    timestamps: RestoreTimestamps | None = None


class ImportObjectRelationInput(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    from_object_key: ObjectKey | None = None
    from_object_ref: str | None = None
    ref: str | None = None
    timestamps: RestoreTimestamps | None = None
    to_object_key: ObjectKey | None = None
    to_object_ref: str | None = None


class ImportPrincipalInput1(APIModel):
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    external_subject: str | None = None
    identity_scope_key: IdentityScopeKey | None = None
    identity_scope_ref: str | None = None
    last_sync_attempted_at: AwareDatetime | None = None
    last_sync_success_at: AwareDatetime | None = None
    name: str
    provider_managed: bool
    ref: str | None = None
    settings: JsonValue | None = None
    timestamps: RestoreTimestamps | None = None


class ImportPrincipalInput2(ImportPrincipalInputHuman, ImportPrincipalInput1):
    pass


class ImportPrincipalInput3(ImportPrincipalInputServiceAccount, ImportPrincipalInput1):
    pass


class ImportRemoteTargetInput(APIModel):
    allowed_subject_types: list[
        Literal["collection", "class", "object", "class_relation", "object_relation"]
    ]
    auth_config: (
        RemoteAuthConfigNone
        | RemoteAuthConfigBearerSecret
        | RemoteAuthConfigBasicSecret
        | RemoteAuthConfigApiKeySecret
        | None
    ) = None
    body_template: str | None = None
    class_key: ClassKey | None = None
    class_ref: str | None = None
    collection_key: CollectionKey | None = None
    collection_ref: str | None = None
    condition: (
        ImportWriteConditionCreateOnly
        | ImportWriteConditionOverwrite
        | ImportWriteConditionIfRevision
        | None
    ) = None
    description: str
    enabled: bool
    headers_template: JsonValue | None = None
    method: Literal["get", "post", "patch", "delete"]
    name: str
    ref: str | None = None
    timeout_ms: int
    timestamps: RestoreTimestamps | None = None
    url_template: str


class MeResponse(APIModel):
    principal: MembershipPrincipalResponse
    token: CurrentTokenMetadata


class NewExportTemplate(APIModel):
    class_id: int | None = None
    collection_id: int
    content_type: Literal["application/json", "text/plain", "text/html", "text/csv"]
    default_limits: ExportLimits | None = None
    default_missing_data_policy: Literal["strict", "null", "omit"] | None = None
    default_query: str | None = None
    description: str
    include: ExportInclude | None = None
    kind: Literal["export", "fragment"]
    name: str
    relation_context: ExportRelationContext | None = None
    scope_kind: (
        Literal[
            "collections",
            "classes",
            "objects_in_class",
            "class_relations",
            "object_relations",
            "related_objects",
        ]
        | None
    ) = None
    template: str


class ObjectSchemaEvidence(APIModel):
    object_revision: Annotated[int, Field(ge=1)]
    schema_: Annotated[SchemaReference, Field(alias="schema")]
    valid: bool
    validated_at: AwareDatetime


class Provenance(APIModel):
    actor: ProvenanceActor
    initiator: ProvenancePrincipal | None = None
    task_id: TaskID | None = None


class QueryPatternObservation(APIModel):
    first_observed_at: AwareDatetime
    last_observed_at: AwareDatetime
    pattern: QueryUsagePatternSchema
    sampled_queries: Annotated[int, Field(ge=0)]
    whole_query_duration_micros: Annotated[int, Field(ge=0)]


class QueryUsageAnalysisRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    proposed: Annotated[list[QueryUsagePatternSchema] | None, Field(max_length=32)] = None


class QueryUsageAssessment(APIModel):
    adapter_progress: QueryUsageAdapterProgress | None = None
    can_prepare: bool
    declaration_id: ResourceID | None = None
    pattern: QueryUsagePatternSchema
    rationale: str
    resources: list[QueryUsageResource]
    schema_compatibility: Literal["compatible", "incompatible", "unknown"]


class QueryUsageCreateRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    pattern: QueryUsagePatternSchema


class QueryUsageSuggestion(APIModel):
    observations: list[QueryPatternObservation]
    proposed: QueryUsagePatternSchema
    rationale: str


class RunningConfig(APIModel):
    authentication: AuthenticationConfig
    backups: BackupConfig
    database: DatabaseConfig
    events: EventConfig
    exports: ExportConfig
    network: NetworkConfig
    pagination: PaginationConfig
    permissions: PermissionConfig
    query_observations: QueryObservationConfig
    remote_calls: RemoteCallConfig
    restores: RestoreConfig
    schema_validation: SchemaValidationConfig
    secrets: SecretSourceConfig
    server: ServerConfig
    tasks: TaskConfig
    tracing: TracingConfig


class SchemaActivationResponse(APIModel):
    active: SchemaRevisionResponse
    dependent_rebuild_task_id: TaskID | None = None
    task_id: TaskID | None = None


class SchemaDiagnosticSnapshotResponse(APIModel):
    diagnostics: SchemaDiagnostics
    inspected_at: AwareDatetime
    object_revision: Annotated[int, Field(ge=1)]


class SchemaImpactFindingResponse(APIModel):
    object_id: int
    reason: SchemaFailure
    snapshot: SchemaDiagnosticSnapshotResponse | None = None


class SchemaImpactResponse(APIModel):
    baseline: SchemaReference
    counts: SchemaImpactCounts
    failures: list[SchemaFailureGroup]
    findings: list[SchemaImpactFindingResponse] | None = None
    ungrouped_failures: Annotated[int, Field(ge=0)]


class SchemaWorkResponse(APIModel):
    batches: Annotated[int, Field(ge=0)]
    created_at: AwareDatetime
    current_active_schema: SchemaReference | None = None
    current_epoch: Annotated[int | None, Field(ge=0)] = None
    cursor: int
    elapsed_millis: Annotated[int, Field(ge=0)]
    end_epoch: Annotated[int | None, Field(ge=0)] = None
    examined: Annotated[int, Field(ge=0)]
    impact: SchemaImpactResponse | None = None
    invalid: Annotated[int, Field(ge=0)]
    invalid_samples: list[int]
    kind: Literal["impact", "revalidation"]
    not_required: Annotated[int, Field(ge=0)]
    readiness: Literal["compatible", "incompatible", "inconclusive"] | None = None
    stale: Annotated[int, Field(ge=0)]
    start_epoch: Annotated[int, Field(ge=0)]
    status: Literal["running", "failed", "complete", "cancelled", "superseded"]
    target: SchemaReference
    task_id: Annotated[int, Field(ge=1)]
    uninspectable: Annotated[int, Field(ge=0)]
    upper_bound: int
    valid: Annotated[int, Field(ge=0)]


class StructuredRelatedPredicate(APIModel):
    model_config = ConfigDict(extra="forbid")
    class_: Annotated[StructuredClassSelectorId | StructuredClassSelectorName, Field(alias="class")]
    depth: Annotated[int | None, Field(ge=1, le=10)] = None
    filters: Annotated[list[StructuredSearchFieldPredicate] | None, Field(max_length=16)] = None


class StructuredSearchExpressionField(APIModel):
    op: Literal["field"]
    predicate: StructuredSearchFieldPredicate


class StructuredSearchExpressionRelated(APIModel):
    op: Literal["related"]
    predicate: StructuredRelatedPredicate


class TaskDetails(APIModel):
    model_config = ConfigDict(extra="forbid")
    backup: BackupTaskDetails | None = None
    export: ExportTaskDetails | None = None
    import_: Annotated[ImportTaskDetails | None, Field(alias="import")] = None
    reindex: RebuildTaskDetails | None = None
    remote_call: RemoteCallTaskDetails | None = None
    schema_validation: SchemaTaskDetails | None = None


class TaskEventResponse(APIModel):
    created_at: AwareDatetime
    data: JsonValue | None = None
    event_type: str
    id: int
    message: str
    provenance: Provenance
    task_id: int


class TaskResponse(APIModel):
    cancel_reason: str | None = None
    cancel_requested_at: AwareDatetime | None = None
    cancel_requested_by: int | None = None
    created_at: AwareDatetime
    details: TaskDetails | None = None
    execution_deadline_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    id: int
    kind: Literal["import", "export", "backup", "reindex", "remote_call", "schema_validation"]
    links: TaskLinks
    progress: TaskProgress
    remote_side_effect_state: Literal["not_sent", "possibly_sent", "legacy_unknown"] | None = None
    request_redacted_at: AwareDatetime | None = None
    started_at: AwareDatetime | None = None
    status: Literal[
        "queued", "validating", "running", "succeeded", "failed", "partially_succeeded", "cancelled"
    ]
    submitted_by: int | None = None
    summary: str | None = None
    terminal_reason: str | None = None
    unattempted_items: int


class UnifiedSearchResponse(APIModel):
    next: UnifiedSearchNext
    query: str
    results: UnifiedSearchResults


class UpdateExportTemplate(APIModel):
    class_id: int | None = None
    collection_id: int | None = None
    default_limits: ExportLimits | None = None
    default_missing_data_policy: Literal["strict", "null", "omit"] | None = None
    default_query: str | None = None
    description: str | None = None
    include: ExportInclude | None = None
    kind: Literal["export", "fragment"] | None = None
    name: str | None = None
    relation_context: ExportRelationContext | None = None
    scope_kind: (
        Literal[
            "collections",
            "classes",
            "objects_in_class",
            "class_relations",
            "object_relations",
            "related_objects",
        ]
        | None
    ) = None
    template: str | None = None


class EventDeliveryHealthResponse(APIModel):
    delivery: EventDeliveryQueueHealth
    fanout: EventFanoutHealth
    sinks: list[EventSinkDeliveryHealth]
    subscriptions: list[EventSubscriptionDeliveryHealth]


class EventResponse(APIModel):
    action: str
    actor_kind: str
    actor_user_id: int | None = None
    after: JsonValue | None = None
    after_revision: ResourceRevision | None = None
    before: JsonValue | None = None
    before_revision: ResourceRevision | None = None
    collection_id: int | None = None
    correlation_id: str | None = None
    entity_id: int | None = None
    entity_name: str | None = None
    entity_type: str
    event_id: UUID
    id: int
    metadata: JsonValue
    occurred_at: AwareDatetime
    provenance: Provenance
    request_id: UUID | None = None
    schema_version: int
    summary: str


class ExportJsonResponse(APIModel):
    items: list[JsonValue]
    meta: ExportMeta
    warnings: list[ExportWarning]


class HistoryResponseCollectionHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    created_at: AwareDatetime
    description: str
    history_id: int
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    parent_collection_id: int | None = None
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseExportTemplateHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    class_id: int | None = None
    collection_id: int
    content_type: str
    created_at: AwareDatetime
    default_limits: JsonValue | None = None
    default_missing_data_policy: str | None = None
    default_query: str | None = None
    description: str
    history_id: int
    id: int
    include: JsonValue | None = None
    initiator_user_id: int | None = None
    kind: str
    name: str
    op: str
    relation_context: JsonValue | None = None
    revision: Annotated[int, Field(ge=1)]
    scope_kind: str | None = None
    task_id: int | None = None
    template: str
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseHistoricalRelation1(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    context_at: AwareDatetime
    from_: Annotated[
        HistoricalEndpointContextAvailable | HistoricalEndpointContextUnavailable,
        Field(alias="from"),
    ]
    history_id: int
    initiator_user_id: int | None = None
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    to: HistoricalEndpointContextAvailable | HistoricalEndpointContextUnavailable
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseHistoricalRelation2(
    HistoryResponseHistoricalRelationClass, HistoryResponseHistoricalRelation1
):
    pass


class HistoryResponseHistoricalRelation3(
    HistoryResponseHistoricalRelationObject, HistoryResponseHistoricalRelation1
):
    pass


class HistoryResponseHistoryMarker(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    history_id: int
    hubuum_class_id: int | None = None
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseHubuumClassHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    created_at: AwareDatetime
    description: str
    history_id: int
    id: int
    initiator_user_id: int | None = None
    json_schema: JsonValue | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    validate_schema: bool
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseHubuumObjectHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    collection_id: int
    created_at: AwareDatetime
    data: JsonValue
    description: str
    history_id: int
    hubuum_class_id: int
    id: int
    initiator_user_id: int | None = None
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    updated_at: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class HistoryResponseRemoteTargetHistory(APIModel):
    actor_id: int | None = None
    actor_kind: str | None = None
    allowed_subject_types: JsonValue
    auth_config: JsonValue
    body_template: str | None = None
    class_id: int | None = None
    collection_id: int
    created_at: AwareDatetime
    description: str
    enabled: bool
    headers_template: JsonValue
    history_id: int
    id: int
    initiator_user_id: int | None = None
    method: str
    name: str
    op: str
    revision: Annotated[int, Field(ge=1)]
    task_id: int | None = None
    timeout_ms: int
    updated_at: AwareDatetime
    url_template: str
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    actor_username: str | None = None
    provenance: Provenance


class ImportGraph(APIModel):
    class_relations: list[ImportClassRelationInput] | None = None
    classes: list[ImportClassInput] | None = None
    collection_permissions: list[ImportCollectionPermissionInput] | None = None
    collections: list[ImportCollectionInput] | None = None
    computed_fields: list[ImportComputedFieldInput] | None = None
    event_sinks: list[ImportEventSinkInput] | None = None
    event_subscriptions: list[ImportEventSubscriptionInput] | None = None
    export_templates: list[ImportExportTemplateInput] | None = None
    group_memberships: list[ImportGroupMembershipInput] | None = None
    groups: list[ImportGroupInput] | None = None
    identity_scopes: list[ImportIdentityScopeInput] | None = None
    object_relations: list[ImportObjectRelationInput] | None = None
    objects: list[ImportObjectInput] | None = None
    principals: list[ImportPrincipalInput2 | ImportPrincipalInput3] | None = None
    remote_targets: list[ImportRemoteTargetInput] | None = None


class ImportRequest(APIModel):
    dry_run: bool | None = None
    graph: ImportGraph
    mode: ImportMode | None = None
    version: int


class ObjectComplianceResponse(APIModel):
    active_schema: SchemaReference
    evidence: ObjectSchemaEvidence | None = None
    object_id: int
    object_revision: Annotated[int, Field(ge=1)]
    status: Literal["valid", "invalid", "pending", "not_required"]


class QueryObservationSnapshot(APIModel):
    capacity_drops: Annotated[int, Field(ge=0)]
    captured_at: AwareDatetime
    patterns: list[QueryPatternObservation]
    process_started_at: AwareDatetime
    settings: QueryObservationSettings
    source: str


class QueryUsageAnalysisResponse(APIModel):
    assessed_at: AwareDatetime
    assessments: list[QueryUsageAssessment]
    limitations: list[str]
    observations: QueryObservationSnapshot
    status: Literal["unavailable", "insufficient_evidence", "complete"]
    suggestions: list[QueryUsageSuggestion]


class SchemaCompliancePage(APIModel):
    items: list[ObjectComplianceResponse]
    next_after: int | None = None


class StructuredSearchResultAuditEvent(APIModel):
    kind: Literal["audit_event"]
    resource: EventResponse


class CredentialOperationImportCredentials(APIModel):
    import_: Annotated[ImportRequest, Field(alias="import")]
    kind: Literal["import_credentials"]


class HistoricalClassObjects(APIModel):
    at: AwareDatetime
    class_: Annotated[HistoryResponseHubuumClassHistory, Field(alias="class")]
    coverage: Literal["retained_history"]
    objects: list[HistoryResponseHubuumObjectHistory]


class HistoricalRelationships(APIModel):
    at: AwareDatetime | None = None
    coverage: Literal["retained_history"]
    relations: list[HistoryResponseHistoricalRelation2 | HistoryResponseHistoricalRelation3]


class StructuredSearchResponse(APIModel):
    kind: Literal[
        "collection", "class", "object", "audit_event", "user", "group", "service_account"
    ]
    next: str | None = None
    results: list[
        StructuredSearchResultCollection
        | StructuredSearchResultClass
        | StructuredSearchResultObject
        | StructuredSearchResultAuditEvent
        | StructuredSearchResultUser
        | StructuredSearchResultGroup
        | StructuredSearchResultServiceAccount
    ]
    total: int | None = None
    version: Annotated[int, Field(ge=0)]


class CredentialApprovalRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    operation: (
        CredentialOperationImportCredentials
        | CredentialOperationConfirmRestore
        | CredentialOperationCreateToken
        | CredentialOperationRenewToken
        | CredentialOperationCreateUser
        | CredentialOperationUpdateUser
    )
    password: SecretStr


class StructuredSearchExpressionAnd(APIModel):
    args: Annotated[
        list[
            StructuredSearchExpressionAnd
            | StructuredSearchExpressionOr
            | StructuredSearchExpressionNot
            | StructuredSearchExpressionField
            | StructuredSearchExpressionRelated
        ],
        Field(max_length=64, min_length=2),
    ]
    op: Literal["and"]


class StructuredSearchExpressionOr(APIModel):
    args: Annotated[
        list[
            StructuredSearchExpressionAnd
            | StructuredSearchExpressionOr
            | StructuredSearchExpressionNot
            | StructuredSearchExpressionField
            | StructuredSearchExpressionRelated
        ],
        Field(max_length=64, min_length=2),
    ]
    op: Literal["or"]


class StructuredSearchExpressionNot(APIModel):
    arg: (
        StructuredSearchExpressionAnd
        | StructuredSearchExpressionOr
        | StructuredSearchExpressionNot
        | StructuredSearchExpressionField
        | StructuredSearchExpressionRelated
    )
    op: Literal["not"]


class StructuredSearchRequest(APIModel):
    model_config = ConfigDict(extra="forbid")
    cursor: Annotated[str | None, Field(min_length=1)] = None
    filter: (
        StructuredSearchExpressionAnd
        | StructuredSearchExpressionOr
        | StructuredSearchExpressionNot
        | StructuredSearchExpressionField
        | StructuredSearchExpressionRelated
        | None
    ) = None
    include_total: bool | None = None
    limit: Annotated[int | None, Field(ge=1)] = None
    sort: Annotated[list[StructuredSearchSort] | None, Field(max_length=8)] = None
    target: (
        StructuredSearchTargetCollection
        | StructuredSearchTargetClass
        | StructuredSearchTargetObject
        | StructuredSearchTargetAuditEvent
        | StructuredSearchTargetUser
        | StructuredSearchTargetGroup
        | StructuredSearchTargetServiceAccount
    )
    version: Annotated[int, Field(ge=1, le=1)]


CollectionID: TypeAlias = Annotated[int, Field(ge=1)]
ComplianceStatus: TypeAlias = Literal["valid", "invalid", "pending", "not_required"]
ComputedResultType: TypeAlias = Literal["string", "number", "integer", "boolean", "object", "array"]
CredentialApprovalSecret: TypeAlias = SecretStr
CredentialOperation: TypeAlias = (
    CredentialOperationImportCredentials
    | CredentialOperationConfirmRestore
    | CredentialOperationCreateToken
    | CredentialOperationRenewToken
    | CredentialOperationCreateUser
    | CredentialOperationUpdateUser
)
EventDeliveryPurpose: TypeAlias = Literal["event", "test"]
EventDeliveryStatus: TypeAlias = Literal["pending", "in_flight", "succeeded", "failed", "dead"]
EventEntityId: TypeAlias = Annotated[int, Field(ge=1)]
EventSinkID: TypeAlias = Annotated[int, Field(ge=1)]
EventSinkKind: TypeAlias = Literal["webhook", "amqp", "valkey_stream", "email"]
EventSinkRouting: TypeAlias = Literal[
    "fixed", "webhook_url", "email_recipients", "valkey_stream", "amqp"
]
EventSubscriptionID: TypeAlias = Annotated[int, Field(ge=1)]
ExportContentType: TypeAlias = Literal["application/json", "text/plain", "text/html", "text/csv"]
ExportIncludeRelatedDirection: TypeAlias = Literal["any", "outgoing", "incoming"]
ExportIncludeRelatedSort: TypeAlias = Literal["path", "name", "created_at"]
ExportMissingDataPolicy: TypeAlias = Literal["strict", "null", "omit"]
ExportScopeKind: TypeAlias = Literal[
    "collections",
    "classes",
    "objects_in_class",
    "class_relations",
    "object_relations",
    "related_objects",
]
ExportTemplateID: TypeAlias = Annotated[int, Field(ge=1)]
ExportTemplateKind: TypeAlias = Literal["export", "fragment"]
HistoricalComputationMode: TypeAlias = Literal["historical_recomputation"]
HistoricalComputedField: TypeAlias = (
    HistoricalComputedField2
    | HistoricalComputedFieldEvaluationError
    | HistoricalComputedField4
    | HistoricalComputedField5
)
HistoricalComputedFieldResult: TypeAlias = (
    HistoricalComputedFieldResultEvaluated
    | HistoricalComputedFieldResultError
    | HistoricalComputedFieldResultDisabled
    | HistoricalComputedFieldResultUnavailable
)
HistoricalComputedUnavailableReason: TypeAlias = Literal[
    "definition_history_unavailable",
    "class_history_unavailable",
    "unsupported_evaluator_version",
    "unsupported_definition_semantics",
]
HistoricalEndpointContext: TypeAlias = (
    HistoricalEndpointContextAvailable | HistoricalEndpointContextUnavailable
)
HistoricalEndpointUnavailableReason: TypeAlias = Literal["history_unavailable"]
HistoricalPersonalFields: TypeAlias = Literal["unsupported"]
HistoricalPopulationCoverage: TypeAlias = Literal["retained_history"]
HistoricalRelationValue: TypeAlias = HistoricalRelationValueClass | HistoricalRelationValueObject
HistoricalSharedComputedFields: TypeAlias = (
    HistoricalSharedComputedFieldsAvailable | HistoricalSharedComputedFieldsUnavailable
)
HistoryDirection: TypeAlias = Literal["older", "newer"]
HistoryResponse_CollectionHistory: TypeAlias = HistoryResponseCollectionHistory
HistoryResponse_ExportTemplateHistory: TypeAlias = HistoryResponseExportTemplateHistory
HistoryResponse_HistoricalRelation: TypeAlias = (
    HistoryResponseHistoricalRelation2 | HistoryResponseHistoricalRelation3
)
HistoryResponse_HistoryMarker: TypeAlias = HistoryResponseHistoryMarker
HistoryResponse_HubuumClassHistory: TypeAlias = HistoryResponseHubuumClassHistory
HistoryResponse_HubuumObjectHistory: TypeAlias = HistoryResponseHubuumObjectHistory
HistoryResponse_RemoteTargetHistory: TypeAlias = HistoryResponseRemoteTargetHistory
HubuumClassID: TypeAlias = Annotated[int, Field(ge=1)]
HubuumClassRelationID: TypeAlias = Annotated[int, Field(ge=1)]
HubuumObjectID: TypeAlias = Annotated[int, Field(ge=1)]
HubuumObjectReadResponse: TypeAlias = HubuumObject | HubuumObjectComputedResponse
HubuumObjectRelationID: TypeAlias = Annotated[int, Field(ge=1)]
ImportAtomicity: TypeAlias = Literal["strict", "best_effort"]
ImportCollisionPolicy: TypeAlias = Literal["abort", "overwrite"]
ImportComputedFieldVisibility: TypeAlias = Literal["shared", "personal"]
ImportPermissionPolicy: TypeAlias = Literal["abort", "continue"]
ImportPrincipalInput: TypeAlias = ImportPrincipalInput2 | ImportPrincipalInput3
ImportPrincipalSubtype: TypeAlias = (
    ImportPrincipalSubtypeHuman | ImportPrincipalSubtypeServiceAccount
)
ImportWriteCondition: TypeAlias = (
    ImportWriteConditionCreateOnly | ImportWriteConditionOverwrite | ImportWriteConditionIfRevision
)
ObjectAggregateMeasureOperation: TypeAlias = Literal["sum", "average", "min", "max"]
ObjectAggregateMeasureState: TypeAlias = Literal["value", "empty"]
ObjectAggregateValueState: TypeAlias = Literal["value", "null", "missing", "unavailable"]
ObjectDataPatchDocument: TypeAlias = Annotated[
    list[
        ObjectDataPatchDocument1
        | ObjectDataPatchDocument2
        | ObjectDataPatchDocument3
        | ObjectDataPatchDocument4
        | ObjectDataPatchDocument5
        | ObjectDataPatchDocument6
    ],
    Field(max_length=1000),
]
ObjectRelationLimit: TypeAlias = Annotated[int, Field(ge=1)]
PatchOperation: TypeAlias = (
    PatchOperation1
    | PatchOperation2
    | PatchOperation3
    | PatchOperation4
    | PatchOperation5
    | PatchOperation6
)
Permissions: TypeAlias = Literal[
    "ReadCollection",
    "UpdateCollection",
    "DeleteCollection",
    "DelegateCollection",
    "CreateClass",
    "ReadClass",
    "UpdateClass",
    "DeleteClass",
    "CreateObject",
    "ReadObject",
    "UpdateObject",
    "DeleteObject",
    "CreateClassRelation",
    "ReadClassRelation",
    "UpdateClassRelation",
    "DeleteClassRelation",
    "CreateObjectRelation",
    "ReadObjectRelation",
    "UpdateObjectRelation",
    "DeleteObjectRelation",
    "ReadTemplate",
    "CreateTemplate",
    "UpdateTemplate",
    "DeleteTemplate",
    "ReadRemoteTarget",
    "CreateRemoteTarget",
    "UpdateRemoteTarget",
    "DeleteRemoteTarget",
    "ExecuteRemoteTarget",
    "ReadAudit",
    "ManageEventSubscription",
]
PrincipalID: TypeAlias = Annotated[int, Field(ge=1)]
PrincipalKind: TypeAlias = Literal["human", "service_account"]
PrincipalSettings: TypeAlias = dict[str, JsonValue]
PrincipalSettingsPatchDocument: TypeAlias = Annotated[
    list[
        PrincipalSettingsPatchDocument1
        | PrincipalSettingsPatchDocument2
        | PrincipalSettingsPatchDocument3
        | PrincipalSettingsPatchDocument4
        | PrincipalSettingsPatchDocument5
        | PrincipalSettingsPatchDocument6
    ],
    Field(max_length=1000),
]
QueryUsageAnalysisStatus: TypeAlias = Literal["unavailable", "insufficient_evidence", "complete"]
QueryUsageCompatibility: TypeAlias = Literal["compatible", "incompatible", "unknown"]
QueryUsageOperation: TypeAlias = Literal["equals", "gt", "gte", "lt", "lte", "between"]
QueryUsageResourceOwnership: TypeAlias = Literal["independently_managed", "declaration_managed"]
QueryUsageValueType: TypeAlias = Literal["string", "numeric", "boolean"]
RefreshToken: TypeAlias = SecretStr
RelationLabel: TypeAlias = Annotated[str, Field(max_length=128, min_length=1)]
RemoteAuthConfig: TypeAlias = (
    RemoteAuthConfigNone
    | RemoteAuthConfigBearerSecret
    | RemoteAuthConfigBasicSecret
    | RemoteAuthConfigApiKeySecret
)
RemoteHttpMethod: TypeAlias = Literal["get", "post", "patch", "delete"]
RemoteInvocationBodyOverride: TypeAlias = JsonValue
RemoteInvocationParameters: TypeAlias = JsonValue
RemoteInvocationSubject: TypeAlias = (
    RemoteInvocationSubjectCollection
    | RemoteInvocationSubjectClass
    | RemoteInvocationSubjectObject
    | RemoteInvocationSubjectClassRelation
    | RemoteInvocationSubjectObjectRelation
)
RemoteTargetID: TypeAlias = Annotated[int, Field(ge=1)]
RemoteTargetSubjectType: TypeAlias = Literal[
    "collection", "class", "object", "class_relation", "object_relation"
]
ResourceID: TypeAlias = Annotated[int, Field(ge=1)]
ResourceRevision: TypeAlias = Annotated[int, Field(ge=1)]
RestoreJobID: TypeAlias = Annotated[int, Field(ge=1)]
RestoreJobStatus: TypeAlias = Literal["validated", "confirmed", "succeeded", "failed", "expired"]
SchemaActivationPolicy: TypeAlias = Literal["reject_incompatible", "allow_pending"]
SchemaActualValue: TypeAlias = (
    Literal["null"]
    | Literal["boolean"]
    | Literal["number"]
    | SchemaActualValueString
    | SchemaActualValueArray
    | SchemaActualValueObject
)
SchemaDiagnosticOmission: TypeAlias = Literal[
    "actual_value_redacted",
    "instance_path_redacted_or_too_long",
    "schema_constraint_unavailable_or_too_large",
]
SchemaExpectedValue: TypeAlias = SchemaExpectedValueAvailable | SchemaExpectedValueOmitted
SchemaImpactReadiness: TypeAlias = Literal["compatible", "incompatible", "inconclusive"]
SchemaObjectUrlTemplate: TypeAlias = str
SchemaRevision: TypeAlias = Annotated[int, Field(ge=1)]
SchemaRevisionStatus: TypeAlias = Literal["staged", "active", "retired", "abandoned"]
SchemaWorkKind: TypeAlias = Literal["impact", "revalidation"]
SchemaWorkStatus: TypeAlias = Literal["running", "failed", "complete", "cancelled", "superseded"]
StructuredClassSelector: TypeAlias = StructuredClassSelectorId | StructuredClassSelectorName
StructuredSearchExpression: TypeAlias = (
    StructuredSearchExpressionAnd
    | StructuredSearchExpressionOr
    | StructuredSearchExpressionNot
    | StructuredSearchExpressionField
    | StructuredSearchExpressionRelated
)
StructuredSearchField: TypeAlias = Literal[
    "id",
    "name",
    "description",
    "collection_id",
    "created_at",
    "updated_at",
    "revision",
    "json_data",
    "validate_schema",
    "json_schema",
    "identity_scope",
    "proper_name",
    "email",
    "occurred_at",
    "entity_type",
    "entity_id",
    "entity_name",
    "action",
    "actor_kind",
    "actor_user_id",
    "initiator_user_id",
    "summary",
    "metadata",
    "managed_by",
    "external_key",
    "last_sync_attempted_at",
    "last_sync_success_at",
    "owner_group_id",
    "created_by",
    "disabled_at",
]
StructuredSearchOperator: TypeAlias = Literal[
    "equals",
    "iequals",
    "contains",
    "icontains",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "like",
    "regex",
    "gt",
    "gte",
    "lt",
    "lte",
    "between",
    "within_network",
    "contains_network",
    "contains_ip",
    "overlaps_network",
    "inet_equals",
    "in",
    "all",
    "array_length",
    "has_key",
    "is_null",
]
StructuredSearchResourceKind: TypeAlias = Literal[
    "collection", "class", "object", "audit_event", "user", "group", "service_account"
]
StructuredSearchResult: TypeAlias = (
    StructuredSearchResultCollection
    | StructuredSearchResultClass
    | StructuredSearchResultObject
    | StructuredSearchResultAuditEvent
    | StructuredSearchResultUser
    | StructuredSearchResultGroup
    | StructuredSearchResultServiceAccount
)
StructuredSearchSortDirection: TypeAlias = Literal["asc", "desc"]
StructuredSearchTarget: TypeAlias = (
    StructuredSearchTargetCollection
    | StructuredSearchTargetClass
    | StructuredSearchTargetObject
    | StructuredSearchTargetAuditEvent
    | StructuredSearchTargetUser
    | StructuredSearchTargetGroup
    | StructuredSearchTargetServiceAccount
)
TaskDiscoveryTarget: TypeAlias = (
    TaskDiscoveryTargetCollection
    | TaskDiscoveryTargetClass
    | TaskDiscoveryTargetObject
    | TaskDiscoveryTargetClassRelation
    | TaskDiscoveryTargetObjectRelation
)
TaskID: TypeAlias = Annotated[int, Field(ge=1)]
TaskKind: TypeAlias = Literal[
    "import", "export", "backup", "reindex", "remote_call", "schema_validation"
]
TaskOutputDiscoveryState: TypeAlias = Literal["available", "expired", "not_produced", "unknown"]
TaskRemoteSideEffectState: TypeAlias = Literal["not_sent", "possibly_sent", "legacy_unknown"]
TaskStatus: TypeAlias = Literal[
    "queued", "validating", "running", "succeeded", "failed", "partially_succeeded", "cancelled"
]
TokenID: TypeAlias = Annotated[int, Field(ge=1)]
TokenListState: TypeAlias = Literal["active", "expired", "revoked", "all"]
TokenResourceScope: TypeAlias = (
    TokenResourceScopeCollection | TokenResourceScopeClass | TokenResourceScopeObject
)
UnifiedSearchKind: TypeAlias = Literal["collection", "class", "object"]
UserID: TypeAlias = Annotated[int, Field(ge=1)]

StructuredSearchExpressionAnd.model_rebuild()
StructuredSearchExpressionOr.model_rebuild()
StructuredSearchExpressionNot.model_rebuild()

UnifiedSearchEvent: TypeAlias = (
    UnifiedSearchStartedEvent
    | UnifiedSearchBatchResponse
    | UnifiedSearchDoneEvent
    | UnifiedSearchErrorEvent
)

StructuredSearchEvent: TypeAlias = (
    StructuredSearchStartedEvent
    | StructuredSearchResult
    | StructuredSearchDoneEvent
    | StructuredSearchErrorEvent
)
