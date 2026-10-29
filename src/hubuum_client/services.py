"""Typed synchronous resource services."""

from __future__ import annotations

import builtins
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from math import isfinite
from time import monotonic, sleep
from typing import TYPE_CHECKING, Generic, TypeVar
from urllib.parse import quote

from pydantic import BaseModel, SecretStr

from ._transport import (
    decode_content_type,
    decode_html,
    decode_json_object,
    decode_json_object_list,
    decode_model,
    decode_model_list,
)
from .api import models as wire
from .errors import NotFoundError, ResultCardinalityError, TaskUnsuccessfulError
from .models import (
    BackupRequest,
    ClassCreate,
    ClassFieldInventory,
    ClassRelation,
    ClassRelationCreate,
    ClassRelationUpdate,
    ClassSchemaResponse,
    ClassUpdate,
    Collection,
    CollectionCreate,
    CollectionEventSink,
    CollectionUpdate,
    ComplianceStatus,
    ComputedFieldCreate,
    ComputedFieldPreviewRequest,
    ComputedFieldUpdate,
    CredentialApprovalRecord,
    CredentialApprovalRequest,
    CredentialApprovalResponse,
    EventSink,
    EventSinkCreate,
    EventSinkUpdate,
    EventSubscription,
    EventSubscriptionCreate,
    EventSubscriptionUpdate,
    ExportContentType,
    ExportJsonResponse,
    ExportOutput,
    ExportRequest,
    ExportTemplateCreate,
    ExportTemplateRunRequest,
    ExportTemplateUpdate,
    Group,
    GroupCreate,
    GroupPoint,
    GroupUpdate,
    HubuumClass,
    HubuumObject,
    ImportRequest,
    ImportRunResult,
    ImportTaskResult,
    LoginResponse,
    NewTokenRequest,
    ObjectAggregateRow,
    ObjectCreate,
    ObjectDataPatchInput,
    ObjectRelation,
    ObjectRelationCreate,
    ObjectUpdate,
    Permission,
    PersonalComputedFieldCreate,
    PrincipalMember,
    PrincipalTokenMetadata,
    PrincipalTokenPoint,
    RemoteTargetCreate,
    RemoteTargetInvokeRequest,
    RemoteTargetUpdate,
    RenderedExport,
    RenewTokenRequest,
    RestoreConfirmRequest,
    SchemaActivationRequest,
    SchemaActivationResponse,
    SchemaCompliancePage,
    SchemaProfileReport,
    SchemaProfileRequest,
    SchemaRepairReportRequest,
    SchemaRevisionResponse,
    SchemaStageRequest,
    SchemaWorkResponse,
    ServiceAccount,
    ServiceAccountCreate,
    ServiceAccountPoint,
    ServiceAccountUpdate,
    SettingsPatchOperation,
    SettingsRequest,
    Task,
    TaskCancelRequest,
    TaskEvent,
    TaskStatus,
    User,
    UserCreate,
    UserPoint,
    UserUpdate,
    _EventSinkCollectionIds,
    _object_data_patch_payload,
)
from .options import Params, RequestOptions
from .query import (
    FieldDiscoveryOptions,
    Page,
    Query,
    SchemaPageOptions,
    TokenListState,
    aware_timestamp,
)
from .streaming import ResponseStream
from .types import (
    AccessToken,
    ClassId,
    CollectionId,
    ComputedFieldId,
    CredentialApprovalId,
    CredentialApprovalSecret,
    EventDeliveryId,
    EventSinkId,
    ExportTemplateId,
    GroupId,
    ObjectId,
    PrincipalId,
    RemoteTargetId,
    RestoreJobId,
    SchemaRevision,
    ServiceAccountId,
    TaskId,
    TokenId,
    UserId,
)

if TYPE_CHECKING:
    from .client import Client

ModelT = TypeVar("ModelT", bound=BaseModel)
PointModelT = TypeVar("PointModelT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def _segment(value: object) -> str:
    return quote(str(value), safe="")


class _CursorService(Generic[ModelT]):
    """Internal typed cursor pagination shared by all list endpoints."""

    def __init__(
        self,
        client: Client,
        *,
        collection_path: str,
        model: type[ModelT],
        fixed_params: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self._client = client
        self._collection_path = collection_path
        self._model = model
        self._fixed_params = fixed_params

    def page(self, query: Query | None = None) -> Page[ModelT]:
        """Return one cursor page using immutable query controls."""
        response = self._client._request_response(
            "GET",
            self._collection_path,
            options=RequestOptions(params=[*self._fixed_params, *(query or Query()).as_params()]),
        )
        items = decode_model_list(response, self._model)
        return Page(
            items=tuple(items),
            next_cursor=response.headers.get("x-next-cursor"),
            total_count=_header_int(response.headers.get("x-total-count")),
            page_limit=_header_int(response.headers.get("x-page-limit")),
        )

    def list(self, query: Query | None = None) -> builtins.list[ModelT]:
        """Return one cursor page as a list."""
        return builtins.list(self.page(query))

    def pages(self, query: Query | None = None, *, max_pages: int = 100) -> Iterator[Page[ModelT]]:
        """Iterate pages with cursor-cycle and page-count guards."""
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        current = query or Query()
        seen = {current.cursor_value} if current.cursor_value is not None else set()
        for _ in range(max_pages):
            page = self.page(current)
            yield page
            if page.next_cursor is None:
                return
            if page.next_cursor in seen:
                raise RuntimeError("Hubuum returned a repeated pagination cursor")
            seen.add(page.next_cursor)
            current = current.cursor(page.next_cursor)
        raise RuntimeError(f"pagination exceeded max_pages={max_pages}")

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ModelT]:
        """Collect items with explicit page-count and item-count guards."""
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        items: builtins.list[ModelT] = []
        for page in self.pages(query, max_pages=max_pages):
            if len(page) > max_items - len(items):
                raise RuntimeError(f"pagination exceeded max_items={max_items}")
            items.extend(page)
        return items

    def one(self, query: Query) -> ModelT:
        """Return exactly one matching item or raise a cardinality error."""
        items = self.list(query.limit(2))
        if len(items) != 1:
            raise ResultCardinalityError(f"expected exactly one result, received {len(items)}")
        return items[0]


class ResourceService(_CursorService[ModelT], Generic[ModelT, PointModelT, CreateT, UpdateT]):
    """Shared CRUD with independently typed collection and point responses."""

    def __init__(
        self,
        client: Client,
        *,
        collection_path: str,
        item_path: str,
        list_model: type[ModelT],
        point_model: type[PointModelT],
    ) -> None:
        super().__init__(client, collection_path=collection_path, model=list_model)
        self._item_path = item_path
        self._point_model = point_model

    def get(self, resource_id: object) -> PointModelT:
        """Return one resource by its path identifier."""
        return self._client.request(
            "GET",
            self._item_path.format(id=_segment(resource_id)),
            response_model=self._point_model,
        )

    def create(self, payload: CreateT) -> PointModelT:
        """Create and return a resource from a strict request model."""
        return self._client.request(
            "POST", self._collection_path, json=payload, response_model=self._point_model
        )

    def update(self, resource_id: object, payload: UpdateT) -> PointModelT:
        """Patch and return one resource by its path identifier."""
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=self._point_model,
        )

    def delete(self, resource_id: object) -> None:
        """Delete one resource by its path identifier."""
        self._client.request("DELETE", self._item_path.format(id=_segment(resource_id)))


def _header_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class CollectionsService(
    ResourceService[Collection, Collection, CollectionCreate, CollectionUpdate]
):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/collections",
            item_path="/api/v1/collections/{id}",
            list_model=Collection,
            point_model=Collection,
        )

    def permissions(self, collection_id: CollectionId | int) -> CollectionPermissionsService:
        return CollectionPermissionsService(self._client, collection_id)

    def event_sinks(self, collection_id: CollectionId | int) -> CollectionEventSinksService:
        """Permitted destinations and owned-webhook management (server v0.0.18 and newer)."""
        return CollectionEventSinksService(self._client, CollectionId(collection_id))

    def event_subscriptions(self, collection_id: CollectionId | int) -> EventSubscriptionsService:
        """Collection subscriptions; writes require management and audit permissions."""
        return EventSubscriptionsService(self._client, CollectionId(collection_id))

    def children(self, collection_id: CollectionId | int) -> builtins.list[Collection]:
        path = f"/api/v1/collections/{_segment(collection_id)}/children"
        return _model_list(self._client, path, Collection)

    def ancestors(self, collection_id: CollectionId | int) -> builtins.list[Collection]:
        path = f"/api/v1/collections/{_segment(collection_id)}/ancestors"
        return _model_list(self._client, path, Collection)

    def move(
        self, collection_id: CollectionId | int, parent_id: CollectionId | int | None
    ) -> Collection:
        path = f"/api/v1/collections/{_segment(collection_id)}/parent"
        return self._client.request(
            "PUT",
            path,
            json={"parent_collection_id": parent_id},
            response_model=Collection,
        )


class ClassesService(ResourceService[HubuumClass, HubuumClass, ClassCreate, ClassUpdate]):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/classes",
            item_path="/api/v1/classes/{id}",
            list_model=HubuumClass,
            point_model=HubuumClass,
        )

    def get_by_name(self, name: str) -> HubuumClass:
        return self._client.request(
            "GET", f"/api/v1/classes/by-name/{_segment(name)}", response_model=HubuumClass
        )

    def update_by_name(self, name: str, payload: ClassUpdate) -> HubuumClass:
        return self._client.request(
            "PATCH",
            f"/api/v1/classes/by-name/{_segment(name)}",
            json=payload,
            response_model=HubuumClass,
        )

    def delete_by_name(self, name: str) -> None:
        self._client.request("DELETE", f"/api/v1/classes/by-name/{_segment(name)}")

    def by_id(self, class_id: ClassId | int) -> ClassService:
        """Select a class and its nested resources by numeric ID."""
        return ClassService(self._client, ClassId(class_id))

    def by_name(self, name: str) -> NamedClassService:
        """Select the complete natural-key-addressed class surface."""
        return NamedClassService(self._client, name)


class ClassService:
    """A class and its nested resources addressed by numeric ID."""

    def __init__(self, client: Client, class_id: ClassId) -> None:
        self._client = client
        self.class_id = class_id
        self._base = f"/api/v1/classes/{_segment(class_id)}"

    def fields(self, options: FieldDiscoveryOptions | None = None) -> ClassFieldInventory:
        """Discover authorized fields in one bounded request without downloading object data."""
        return self._client.request(
            "GET",
            f"{self._base}/fields",
            response_model=ClassFieldInventory,
            options=RequestOptions(params=(options or FieldDiscoveryOptions()).as_params()),
        )

    @property
    def computed_fields(self) -> ClassComputedFieldsService:
        return ClassComputedFieldsService(self._client, self.class_id)

    @property
    def permissions(self) -> _CursorService[wire.GroupPermission]:
        return _CursorService(
            self._client, collection_path=f"{self._base}/permissions", model=wire.GroupPermission
        )

    @property
    def schema(self) -> ClassSchemaService:
        return ClassSchemaService(self._client, self.class_id)

    @property
    def objects(self) -> ObjectsService:
        return ObjectsService(self._client, self.class_id)

    def get(self) -> HubuumClass:
        return self._client.request("GET", self._base, response_model=HubuumClass)

    def update(self, payload: ClassUpdate) -> HubuumClass:
        return self._client.request(
            "PATCH",
            self._base,
            json=payload,
            response_model=HubuumClass,
        )

    def delete(self) -> None:
        self._client.request("DELETE", self._base)


class ClassSchemaService:
    """Stage, inspect, and explicitly activate one class's schema revisions."""

    def __init__(self, client: Client, class_id: ClassId) -> None:
        self._client = client
        self._base = f"/api/v1/classes/{_segment(class_id)}/schema"

    def profile(
        self,
        payload: SchemaProfileRequest | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> Task:
        """Queue a suggestion; this never stages or activates a schema."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return self._client.request(
            "POST",
            f"{self._base}/profiles",
            json=payload or SchemaProfileRequest(),
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    def profile_report(self, task_id: TaskId | int) -> SchemaProfileReport:
        """Read a completed suggestion. Expired reports return HTTP 410 after 24 hours."""
        return self._client.request(
            "GET",
            f"{self._base}/profiles/{_segment(TaskId(task_id))}",
            response_model=SchemaProfileReport,
        )

    def suggest(
        self,
        payload: SchemaProfileRequest | None = None,
        *,
        idempotency_key: str | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> SchemaProfileReport:
        """Submit, wait, and fetch a suggestion for explicit review and staging."""
        submitted = self.profile(payload, idempotency_key=idempotency_key)
        task = self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return self.profile_report(task.id)

    def get(self) -> ClassSchemaResponse:
        """Return the active schema and administrator compliance counts."""
        return self._client.request("GET", self._base, response_model=ClassSchemaResponse)

    def revisions(
        self, options: SchemaPageOptions | None = None
    ) -> builtins.list[SchemaRevisionResponse]:
        """Read one bounded revision page; resume after its last revision."""
        response = self._client._request_response(
            "GET",
            f"{self._base}/revisions",
            options=RequestOptions(params=(options or SchemaPageOptions()).as_params()),
        )
        return decode_model_list(response, SchemaRevisionResponse)

    def revision(self, revision: SchemaRevision) -> SchemaRevisionResponse:
        """Read one immutable schema revision."""
        return self._client.request(
            "GET",
            f"{self._base}/revisions/{_segment(revision)}",
            response_model=SchemaRevisionResponse,
        )

    def stage(self, payload: SchemaStageRequest) -> SchemaRevisionResponse:
        """Stage a policy without changing active validation."""
        return self._client.request(
            "POST",
            f"{self._base}/revisions",
            json=payload,
            response_model=SchemaRevisionResponse,
        )

    def abandon(self, revision: SchemaRevision) -> SchemaRevisionResponse:
        """Abandon a staged revision."""
        return self._client.request(
            "DELETE",
            f"{self._base}/revisions/{_segment(revision)}",
            response_model=SchemaRevisionResponse,
        )

    def impact(self, revision: SchemaRevision) -> SchemaWorkResponse:
        """Queue an impact analysis against the current object population."""
        return self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/impact",
            response_model=SchemaWorkResponse,
        )

    def activate(
        self, revision: SchemaRevision, payload: SchemaActivationRequest
    ) -> SchemaActivationResponse:
        """Activate with an explicit policy and expected active schema revision."""
        return self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/activate",
            json=payload,
            response_model=SchemaActivationResponse,
        )

    def revalidate(self, revision: SchemaRevision) -> SchemaWorkResponse:
        """Queue revalidation of the active revision without changing object data."""
        return self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/revalidate",
            response_model=SchemaWorkResponse,
        )

    def objects(
        self, options: SchemaPageOptions | None = None, *, status: ComplianceStatus | None = None
    ) -> SchemaCompliancePage:
        """Read authorized evidence; resume with next_after even after an empty page."""
        params = (options or SchemaPageOptions()).as_params()
        if status is not None:
            params.append(("status", status.value))
        return self._client.request(
            "GET",
            f"{self._base}/objects",
            response_model=SchemaCompliancePage,
            options=RequestOptions(params=params),
        )

    def work(self, task_id: TaskId | int) -> SchemaWorkResponse:
        """Read saved diagnostics and current readiness for a schema task."""
        return self._client.request(
            "GET",
            f"{self._base}/tasks/{_segment(task_id)}",
            response_model=SchemaWorkResponse,
        )

    def cancel(self, task_id: TaskId | int) -> SchemaWorkResponse:
        """Cancel schema work while retaining already committed findings."""
        return self._client.request(
            "DELETE",
            f"{self._base}/tasks/{_segment(task_id)}",
            response_model=SchemaWorkResponse,
        )

    def generate_report(self, task_id: TaskId | int, payload: SchemaRepairReportRequest) -> str:
        """Generate and retain HTML from saved diagnostics."""
        response = self._client._request_response(
            "POST",
            f"{self._base}/tasks/{_segment(task_id)}/report",
            json=payload,
            options=RequestOptions(headers={"Accept": "text/html"}),
        )
        return decode_html(response)

    def report(self, task_id: TaskId | int, *, download: bool = False) -> str:
        """Read retained HTML, optionally requesting an attachment response."""
        response = self._client._request_response(
            "GET",
            f"{self._base}/tasks/{_segment(task_id)}/report",
            options=RequestOptions(params={"download": download}, headers={"Accept": "text/html"}),
        )
        return decode_html(response)


class ObjectsService(ResourceService[HubuumObject, HubuumObject, ObjectCreate, ObjectUpdate]):
    def __init__(self, client: Client, class_id: ClassId) -> None:
        self.class_id = class_id
        base = f"/api/v1/classes/{_segment(class_id)}"
        super().__init__(
            client,
            collection_path=f"{base}/",
            item_path=f"{base}/{{id}}",
            list_model=HubuumObject,
            point_model=HubuumObject,
        )

    def get_by_name(self, name: str) -> HubuumObject:
        return self.one(Query().where("name", name))

    def update_by_name(self, name: str, payload: ObjectUpdate) -> HubuumObject:
        return self.update(self.get_by_name(name).id, payload)

    def delete_by_name(self, name: str) -> None:
        self.delete(self.get_by_name(name).id)

    def patch_data(
        self,
        object_id: object,
        operations: builtins.list[ObjectDataPatchInput],
    ) -> HubuumObject:
        """Atomically apply RFC 6902 operations relative to the object's data root."""
        return self._client.request(
            "PATCH",
            f"/api/v1/classes/{_segment(self.class_id)}/{_segment(object_id)}/data",
            json=_object_data_patch_payload(operations),
            response_model=HubuumObject,
            options=RequestOptions(headers={"Content-Type": "application/json-patch+json"}),
        )


class NamedObjectsService:
    """Objects addressed through a globally unique class name."""

    def __init__(self, client: Client, class_name: str) -> None:
        if not class_name.strip():
            raise ValueError("class name must not be empty")
        self._client = client
        self.class_name = class_name
        base = f"/api/v1/classes/by-name/{_segment(class_name)}/objects"
        self._service = ResourceService[HubuumObject, HubuumObject, ObjectCreate, ObjectUpdate](
            client,
            collection_path=base,
            item_path=f"{base}/by-name/{{id}}",
            list_model=HubuumObject,
            point_model=HubuumObject,
        )

    def page(self, query: Query | None = None) -> Page[HubuumObject]:
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[HubuumObject]:
        return self._service.list(query)

    def pages(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[HubuumObject]]:
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[HubuumObject]:
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def one(self, query: Query) -> HubuumObject:
        return self._service.one(query)

    def get(self, object_name: str) -> HubuumObject:
        return self._service.get(_required_name(object_name, "object"))

    def create(self, payload: ObjectCreate) -> HubuumObject:
        return self._service.create(payload)

    def update(self, object_name: str, payload: ObjectUpdate) -> HubuumObject:
        return self._service.update(_required_name(object_name, "object"), payload)

    def delete(self, object_name: str) -> None:
        self._service.delete(_required_name(object_name, "object"))

    def patch_data(
        self,
        object_name: str,
        operations: builtins.list[ObjectDataPatchInput],
    ) -> HubuumObject:
        """Atomically patch object data with class/object rename safety."""
        path = (
            f"/api/v1/classes/by-name/{_segment(self.class_name)}"
            f"/objects/by-name/{_segment(_required_name(object_name, 'object'))}/data"
        )
        return self._client.request(
            "PATCH",
            path,
            json=_object_data_patch_payload(operations),
            response_model=HubuumObject,
            options=RequestOptions(headers={"Content-Type": "application/json-patch+json"}),
        )

    def related_objects(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> builtins.list[dict[str, object]]:
        path = self._related_path(object_name, "objects")
        return _json_object_list(self._client, path, params=params)

    def related_relations(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> builtins.list[dict[str, object]]:
        path = self._related_path(object_name, "relations")
        return _json_object_list(self._client, path, params=params)

    def related_graph(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> dict[str, object]:
        path = self._related_path(object_name, "graph")
        return _json_object(self._client, path, params=params)

    def _related_path(self, object_name: str, view: str) -> str:
        return (
            f"/api/v1/classes/by-name/{_segment(self.class_name)}"
            f"/objects/by-name/{_segment(_required_name(object_name, 'object'))}"
            f"/related/{view}"
        )


class NamedClassService:
    """Class endpoints rooted at ``classes/by-name/{class_name}``."""

    def __init__(self, client: Client, class_name: str) -> None:
        self._client = client
        self.class_name = _required_name(class_name, "class")
        self._base = f"/api/v1/classes/by-name/{_segment(self.class_name)}"

    def fields(self, options: FieldDiscoveryOptions | None = None) -> ClassFieldInventory:
        """Discover by exact name, using an ID route for URL dot segments."""
        if self.class_name in {".", ".."}:
            matches = self._client.classes.list(
                Query().where("name", self.class_name).limit(2).include_total(False)
            )
            if len(matches) != 1:
                raise ResultCardinalityError("expected exactly one class for field discovery")
            return self._client.classes.by_id(matches[0].id).fields(options)
        return self._client.request(
            "GET",
            f"{self._base}/fields",
            response_model=ClassFieldInventory,
            options=RequestOptions(params=(options or FieldDiscoveryOptions()).as_params()),
        )

    @property
    def objects(self) -> NamedObjectsService:
        return NamedObjectsService(self._client, self.class_name)

    def get(self) -> HubuumClass:
        return self._client.request("GET", self._base, response_model=HubuumClass)

    def update(self, payload: ClassUpdate) -> HubuumClass:
        return self._client.request("PATCH", self._base, json=payload, response_model=HubuumClass)

    def delete(self) -> None:
        self._client.request("DELETE", self._base)

    def permissions(self, *, params: Params = None) -> builtins.list[wire.GroupPermission]:
        response = self._client._request_response(
            "GET", f"{self._base}/permissions", options=RequestOptions(params=params)
        )
        decode_json_object_list(response)
        return decode_model_list(response, wire.GroupPermission)

    def related_classes(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return _json_object_list(self._client, f"{self._base}/related/classes", params=params)

    def related_relations(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return _json_object_list(self._client, f"{self._base}/related/relations", params=params)

    def related_graph(self, *, params: Params = None) -> dict[str, object]:
        return _json_object(self._client, f"{self._base}/related/graph", params=params)

    def object_aggregates(self, *, params: Params) -> Page[ObjectAggregateRow]:
        return _model_page(
            self._client,
            f"{self._base}/object-aggregates",
            ObjectAggregateRow,
            params=params,
        )


class CredentialApprovalsService:
    """Obtain single-use password approval and inspect retained evidence."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def create(self, payload: CredentialApprovalRequest) -> CredentialApprovalResponse:
        return self._client.request(
            "POST",
            "/api/v1/iam/credential-approvals",
            json=payload,
            response_model=CredentialApprovalResponse,
        )

    def get(self, approval_id: CredentialApprovalId | int) -> CredentialApprovalRecord:
        return self._client.request(
            "GET",
            f"/api/v1/iam/credential-approvals/{_segment(approval_id)}",
            response_model=CredentialApprovalRecord,
        )


class UsersService(ResourceService[User, UserPoint, UserCreate, UserUpdate]):
    """User lists with canonical point responses for reads and mutations."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/users",
            item_path="/api/v1/iam/users/{id}",
            list_model=User,
            point_model=UserPoint,
        )

    def create(
        self, payload: UserCreate, *, approval: CredentialApprovalResponse | None = None
    ) -> UserPoint:
        """Create a local user using an operation-bound approval."""
        return self._client.request(
            "POST",
            self._collection_path,
            json=payload,
            response_model=UserPoint,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )

    def update(
        self,
        resource_id: object,
        payload: UserUpdate,
        *,
        approval: CredentialApprovalResponse | None = None,
        options: RequestOptions | None = None,
    ) -> UserPoint:
        """Update a profile or approved password, preserving revision preconditions."""
        request_options = options or RequestOptions()
        headers = dict(request_options.headers or {})
        if approval is not None:
            headers.update(approval.headers())
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=UserPoint,
            options=replace(request_options, headers=headers),
        )

    def get_by_name(self, name: str) -> User:
        return self.one(Query().where("name", name))

    def anonymize(self, user_id: UserId | int) -> None:
        self._client.request("POST", f"/api/v1/iam/users/{_segment(user_id)}/anonymize")


class ServiceAccountsService(
    ResourceService[ServiceAccount, ServiceAccountPoint, ServiceAccountCreate, ServiceAccountUpdate]
):
    """Manage automation identities with guarded lists and revision-owned mutations."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/service-accounts",
            item_path="/api/v1/iam/service-accounts/{id}",
            list_model=ServiceAccount,
            point_model=ServiceAccountPoint,
        )

    def get_by_name(self, name: str, *, identity_scope: str | None = None) -> ServiceAccount:
        """Find exactly one account, optionally restricting its identity scope."""
        query = Query().where("name", name)
        if identity_scope is not None:
            query = query.where("identity_scope", identity_scope)
        return self.one(query)

    def update(
        self,
        resource_id: object,
        payload: ServiceAccountUpdate,
        *,
        if_match: str | None = None,
    ) -> ServiceAccountPoint:
        """Edit description or ownership, optionally requiring the current ETag."""
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=ServiceAccountPoint,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    def disable(
        self, service_account_id: ServiceAccountId | int, *, if_match: str | None = None
    ) -> ServiceAccountPoint:
        """Disable the account and revoke its tokens, with an optional ETag check."""
        return self._client.request(
            "POST",
            f"{self._item_path.format(id=_segment(service_account_id))}/disable",
            response_model=ServiceAccountPoint,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        """Delete the account, optionally requiring the current ETag."""
        self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )


class GroupsService(ResourceService[Group, GroupPoint, GroupCreate, GroupUpdate]):
    """Group lists with revision-owned point responses for reads and mutations."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/groups",
            item_path="/api/v1/iam/groups/{id}",
            list_model=Group,
            point_model=GroupPoint,
        )

    def get_by_name(self, name: str) -> Group:
        return self.one(Query().where("groupname", name))

    def _members_service(
        self, group_id: GroupId | int
    ) -> ResourceService[PrincipalMember, PrincipalMember, BaseModel, BaseModel]:
        path = f"/api/v1/iam/groups/{_segment(group_id)}/members"
        return ResourceService(
            self._client,
            collection_path=path,
            item_path=f"{path}/{{id}}",
            list_model=PrincipalMember,
            point_model=PrincipalMember,
        )

    def members_page(
        self, group_id: GroupId | int, query: Query | None = None
    ) -> Page[PrincipalMember]:
        return self._members_service(group_id).page(query)

    def members(
        self, group_id: GroupId | int, query: Query | None = None
    ) -> builtins.list[PrincipalMember]:
        return self._members_service(group_id).list(query)

    def member_pages(
        self,
        group_id: GroupId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[PrincipalMember]]:
        return self._members_service(group_id).pages(query, max_pages=max_pages)

    def all_members(
        self,
        group_id: GroupId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalMember]:
        return self._members_service(group_id).all(
            query,
            max_pages=max_pages,
            max_items=max_items,
        )

    def add_member(
        self, group_id: GroupId | int, principal_id: PrincipalId | int
    ) -> PrincipalMember:
        return self._client.request(
            "POST",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
            response_model=PrincipalMember,
        )

    def remove_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        self._client.request(
            "DELETE",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )


class _TokenListService:
    """Shared lifecycle-aware token pagination behavior."""

    def __init__(self, client: Client, collection_path: str) -> None:
        self._client = client
        self._collection_path = collection_path

    def _service(self, state: TokenListState) -> _CursorService[PrincipalTokenMetadata]:
        return _CursorService(
            self._client,
            collection_path=self._collection_path,
            model=PrincipalTokenMetadata,
            fixed_params=(("state", state.value),),
        )

    def page(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
    ) -> Page[PrincipalTokenMetadata]:
        return self._service(state).page(query)

    def list(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return self._service(state).list(query)

    def pages(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
        max_pages: int = 100,
    ) -> Iterator[Page[PrincipalTokenMetadata]]:
        return self._service(state).pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return self._service(state).all(query, max_pages=max_pages, max_items=max_items)


class TokensService(_TokenListService):
    """Token metadata visible to the current human user."""

    def __init__(self, client: Client) -> None:
        super().__init__(client, "/api/v1/iam/me/tokens")

    def for_principal(self, principal_id: PrincipalId | int) -> PrincipalTokensService:
        return PrincipalTokensService(self._client, PrincipalId(principal_id))


class PrincipalTokensService(_TokenListService):
    """List, inspect, mint, renew, and revoke tokens for one principal."""

    def __init__(self, client: Client, principal_id: PrincipalId) -> None:
        self.principal_id = principal_id
        self._base = f"/api/v1/iam/principals/{_segment(principal_id)}/tokens"
        super().__init__(client, self._base)

    def get(self, token_id: TokenId | int) -> PrincipalTokenPoint:
        return self._client.request(
            "GET",
            f"{self._base}/{_segment(token_id)}",
            response_model=PrincipalTokenPoint,
        )

    def create(
        self, payload: NewTokenRequest, *, approval: CredentialApprovalResponse | None = None
    ) -> AccessToken:
        response = self._client.request(
            "POST",
            self._base,
            json=approval.token_request(payload) if approval else payload,
            response_model=LoginResponse,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )
        return AccessToken(response.token, expires_at=response.expires_at)

    def revoke(self, token_id: TokenId | int) -> None:
        self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/revoke",
        )

    def renew(
        self,
        token_id: TokenId | int,
        payload: RenewTokenRequest | None = None,
        *,
        approval: CredentialApprovalResponse | None = None,
    ) -> AccessToken:
        response = self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/renew",
            json=approval.token_request(payload or RenewTokenRequest())
            if approval
            else payload or RenewTokenRequest(),
            response_model=LoginResponse,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )
        return AccessToken(response.token, expires_at=response.expires_at)


class ClassRelationsService:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._service = ResourceService[
            ClassRelation, ClassRelation, ClassRelationCreate, BaseModel
        ](
            client,
            collection_path="/api/v1/relations/classes",
            item_path="/api/v1/relations/classes/{id}",
            list_model=ClassRelation,
            point_model=ClassRelation,
        )

    def page(self, query: Query | None = None) -> Page[ClassRelation]:
        """Return one cursor page of class relations."""
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[ClassRelation]:
        return self._service.list(query)

    def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> Iterator[Page[ClassRelation]]:
        """Iterate class relation pages with cursor-cycle and page-count guards."""
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ClassRelation]:
        """Collect class relations with explicit page and item bounds."""
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def one(self, query: Query) -> ClassRelation:
        return self._service.one(query)

    def get(self, relation_id: int) -> ClassRelation:
        return self._service.get(relation_id)

    def create(self, payload: ClassRelationCreate) -> ClassRelation:
        return self._service.create(payload)

    def update(
        self, relation_id: int, payload: ClassRelationUpdate, *, if_match: str | None = None
    ) -> ClassRelation:
        """Edit labels, optionally requiring the resource's current strong ETag."""
        return self._client.request(
            "PATCH",
            f"/api/v1/relations/classes/{_segment(relation_id)}",
            json=payload,
            response_model=ClassRelation,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    def delete(self, relation_id: int) -> None:
        self._service.delete(relation_id)


class ObjectRelationsService:
    def __init__(self, client: Client) -> None:
        self._service = ResourceService[
            ObjectRelation, ObjectRelation, ObjectRelationCreate, BaseModel
        ](
            client,
            collection_path="/api/v1/relations/objects",
            item_path="/api/v1/relations/objects/{id}",
            list_model=ObjectRelation,
            point_model=ObjectRelation,
        )

    def page(self, query: Query | None = None) -> Page[ObjectRelation]:
        """Return one cursor page of object relations."""
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[ObjectRelation]:
        return self._service.list(query)

    def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> Iterator[Page[ObjectRelation]]:
        """Iterate object relation pages with cursor-cycle and page-count guards."""
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ObjectRelation]:
        """Collect object relations with explicit page and item bounds."""
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def one(self, query: Query) -> ObjectRelation:
        return self._service.one(query)

    def get(self, relation_id: int) -> ObjectRelation:
        return self._service.get(relation_id)

    def create(self, payload: ObjectRelationCreate) -> ObjectRelation:
        return self._service.create(payload)

    def delete(self, relation_id: int) -> None:
        self._service.delete(relation_id)


class TasksService:
    """Inspect, paginate, and wait for asynchronous Hubuum tasks."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self._service = _CursorService[Task](
            client,
            collection_path="/api/v1/tasks",
            model=Task,
        )

    def page(self, query: Query | None = None) -> Page[Task]:
        """Return one cursor page of visible tasks."""
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[Task]:
        """Return one page of visible tasks as a list."""
        return self._service.list(query)

    def pages(self, query: Query | None = None, *, max_pages: int = 100) -> Iterator[Page[Task]]:
        """Iterate bounded cursor pages of visible tasks."""
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[Task]:
        """Collect visible tasks with explicit page and item safety bounds."""
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def get(self, task_id: TaskId | int) -> Task:
        """Return a task by numeric ID."""
        return self._client.request(
            "GET", f"/api/v1/tasks/{_segment(task_id)}", response_model=Task
        )

    def cancel(self, task_id: TaskId | int, payload: TaskCancelRequest | None = None) -> Task:
        """Request cancellation; 202 means cleanup is pending, so use wait() for completion."""
        return self._client.request(
            "POST",
            f"/api/v1/tasks/{_segment(task_id)}/cancel",
            json=payload if payload is not None else TaskCancelRequest(),
            response_model=Task,
        )

    def events_page(self, task_id: TaskId | int, query: Query | None = None) -> Page[TaskEvent]:
        """Return one cursor page from a task's event history."""
        return _CursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        ).page(query)

    def events(self, task_id: TaskId | int, query: Query | None = None) -> builtins.list[TaskEvent]:
        """Return one page from a task's event history as a list."""
        return builtins.list(self.events_page(task_id, query))

    def event_pages(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[TaskEvent]]:
        """Iterate bounded cursor pages from a task's event history."""
        return _CursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        ).pages(query, max_pages=max_pages)

    def all_events(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[TaskEvent]:
        """Collect a task's events with explicit page and item bounds."""
        return _CursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        ).all(query, max_pages=max_pages, max_items=max_items)

    def wait(
        self,
        task_id: TaskId | int,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> Task:
        """Poll until a task reaches a terminal state or the timeout expires."""
        if not isfinite(timeout_seconds) or timeout_seconds < 0:
            raise ValueError("timeout_seconds must be finite and non-negative")
        if not isfinite(poll_interval) or poll_interval <= 0:
            raise ValueError("poll_interval must be finite and greater than 0")
        deadline = monotonic() + timeout_seconds
        while True:
            task = self.get(task_id)
            if task.status.terminal:
                return task
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"task {task_id} did not finish within {timeout_seconds} seconds"
                )
            sleep(min(poll_interval, remaining))


class ImportsService:
    """Submit imports and inspect their task and per-entity outcomes."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def submit(
        self,
        payload: ImportRequest,
        *,
        idempotency_key: str | None = None,
        approval: CredentialApprovalResponse | None = None,
    ) -> Task:
        """Submit an import task, optionally with a replay-safe idempotency key."""
        headers = approval.headers() if approval else {}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return self._client.request(
            "POST",
            "/api/v1/imports",
            json=payload,
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    def get(self, task_id: TaskId | int) -> Task:
        """Return an import task through its domain-specific route."""
        return self._client.request(
            "GET", f"/api/v1/imports/{_segment(task_id)}", response_model=Task
        )

    def results_page(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> Page[ImportTaskResult]:
        """Return one cursor page of per-entity import outcomes."""
        return self._results_service(task_id).page(query)

    def results(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> builtins.list[ImportTaskResult]:
        """Return one page of per-entity import outcomes as a list."""
        return self._results_service(task_id).list(query)

    def result_pages(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[ImportTaskResult]]:
        """Iterate bounded cursor pages of per-entity import outcomes."""
        return self._results_service(task_id).pages(query, max_pages=max_pages)

    def all_results(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ImportTaskResult]:
        """Collect import outcomes with explicit page and item bounds."""
        return self._results_service(task_id).all(query, max_pages=max_pages, max_items=max_items)

    # Preserve the existing keyword API while matching all_results()'s bounds.
    def run(  # noqa: PLR0913
        self,
        payload: ImportRequest,
        *,
        idempotency_key: str | None = None,
        approval: CredentialApprovalResponse | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> ImportRunResult:
        """Submit, await, and collect outcomes within the result page and item bounds.

        Both bounds must be positive and are validated before submission. A result
        limit failure does not undo the import; retrieve the existing task's
        outcomes with all_results() and larger bounds instead of resubmitting.
        """
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        submitted = self.submit(payload, idempotency_key=idempotency_key, approval=approval)
        task = self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if not task.status.successful:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return ImportRunResult(
            task=task,
            results=tuple(self.all_results(task.id, max_pages=max_pages, max_items=max_items)),
        )

    def _results_service(self, task_id: TaskId | int) -> _CursorService[ImportTaskResult]:
        return _CursorService(
            self._client,
            collection_path=f"/api/v1/imports/{_segment(task_id)}/results",
            model=ImportTaskResult,
        )


class ExportsService:
    """Submit exports and retrieve their typed or rendered output."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def submit(self, payload: ExportRequest, *, idempotency_key: str | None = None) -> Task:
        """Submit an export task, optionally with a replay-safe idempotency key."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return self._client.request(
            "POST",
            "/api/v1/exports",
            json=payload,
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    def get(self, task_id: TaskId | int) -> Task:
        """Return an export task through its domain-specific route."""
        return self._client.request(
            "GET", f"/api/v1/exports/{_segment(task_id)}", response_model=Task
        )

    def output(self, task_id: TaskId | int) -> ExportOutput:
        """Return JSON output as a model and rendered output as text."""
        response = self._client._request_response(
            "GET", f"/api/v1/exports/{_segment(task_id)}/output"
        )
        content_type = decode_content_type(
            response, ExportContentType, default=ExportContentType.JSON
        )
        if content_type is ExportContentType.JSON:
            return decode_model(response, ExportJsonResponse)
        return RenderedExport(content_type=content_type, body=response.text)

    @contextmanager
    def output_stream(self, task_id: TaskId | int) -> Iterator[ResponseStream]:
        """Stream export output while keeping the response lifetime bounded."""
        with self._client.stream("GET", f"/api/v1/exports/{_segment(task_id)}/output") as stream:
            yield stream

    def run(
        self,
        payload: ExportRequest,
        *,
        idempotency_key: str | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> ExportOutput:
        """Submit and await an export, then return its generated output."""
        submitted = self.submit(payload, idempotency_key=idempotency_key)
        task = self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if not task.status.successful:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return self.output(task.id)


def _model_list(client: Client, path: str, model: type[ModelT]) -> builtins.list[ModelT]:
    response = client._request_response("GET", path)
    return decode_model_list(response, model)


def _required_name(value: str, resource: str) -> str:
    if not value.strip():
        raise ValueError(f"{resource} name must not be empty")
    return value


def _json_object(
    client: Client,
    path: str,
    *,
    params: Params = None,
) -> dict[str, object]:
    response = client._request_response("GET", path, options=RequestOptions(params=params))
    return decode_json_object(response)


def _json_object_list(
    client: Client,
    path: str,
    *,
    params: Params = None,
) -> builtins.list[dict[str, object]]:
    response = client._request_response("GET", path, options=RequestOptions(params=params))
    return decode_json_object_list(response)


def _model_page(
    client: Client,
    path: str,
    model: type[ModelT],
    *,
    params: Params,
) -> Page[ModelT]:
    response = client._request_response("GET", path, options=RequestOptions(params=params))
    value = decode_model_list(response, model)
    return Page(
        items=tuple(value),
        next_cursor=response.headers.get("x-next-cursor"),
        total_count=_header_int(response.headers.get("x-total-count")),
        page_limit=_header_int(response.headers.get("x-page-limit")),
    )


class CollectionEventSinksService(
    ResourceService[CollectionEventSink, CollectionEventSink, EventSinkCreate, EventSinkUpdate]
):
    """Create fixed-destination webhooks owned by a collection and discover permitted sinks."""

    def __init__(self, client: Client, collection_id: CollectionId) -> None:
        base = f"/api/v1/collections/{_segment(collection_id)}/event-sinks"
        super().__init__(
            client,
            collection_path=base,
            item_path=base + "/{id}",
            list_model=CollectionEventSink,
            point_model=CollectionEventSink,
        )


class EventSubscriptionsService(
    ResourceService[
        EventSubscription, EventSubscription, EventSubscriptionCreate, EventSubscriptionUpdate
    ]
):
    """Collection event subscriptions with bounded cursor pagination."""

    def __init__(self, client: Client, collection_id: CollectionId) -> None:
        base = f"/api/v1/collections/{_segment(collection_id)}/event-subscriptions"
        super().__init__(
            client,
            collection_path=base,
            item_path=base + "/{id}",
            list_model=EventSubscription,
            point_model=EventSubscription,
        )


class EventSinksService(ResourceService[EventSink, EventSink, EventSinkCreate, EventSinkUpdate]):
    """Administrator sink CRUD and explicit collection-use grants."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/event-sinks",
            item_path="/api/v1/event-sinks/{id}",
            list_model=EventSink,
            point_model=EventSink,
        )

    def collections(self, sink_id: EventSinkId | int) -> builtins.list[CollectionId]:
        """List direct grants; requires server collection-integration support."""
        result = self._client.request(
            "GET",
            f"/api/v1/event-sinks/{_segment(sink_id)}/collections",
            response_model=_EventSinkCollectionIds,
        )
        return result.root

    def grant(self, sink_id: EventSinkId | int, collection_id: CollectionId | int) -> None:
        """Permit one collection to use a global sink."""
        self._client.request(
            "PUT", f"/api/v1/event-sinks/{_segment(sink_id)}/collections/{_segment(collection_id)}"
        )

    def revoke(self, sink_id: EventSinkId | int, collection_id: CollectionId | int) -> None:
        """Revoke a grant, including admission of queued deliveries."""
        self._client.request(
            "DELETE",
            f"/api/v1/event-sinks/{_segment(sink_id)}/collections/{_segment(collection_id)}",
        )


class EventsService(_CursorService[wire.EventResponse]):
    """A bounded global or resource-scoped audit feed; requires audit permission."""

    def __init__(self, client: Client, path: str = "/api/v1/events") -> None:
        super().__init__(client, collection_path=path, model=wire.EventResponse)


class HistoryService(_CursorService[ModelT]):
    """Bounded versions and a point-in-time read of one supported resource."""

    def as_of(self, at: datetime) -> ModelT:
        return self._client.request(
            "GET",
            f"{self._collection_path}/as-of",
            response_model=self._model,
            options=RequestOptions(params={"at": aware_timestamp(at)}),
        )


class ResourceAuditService(Generic[ModelT]):
    def __init__(self, client: Client, path: str, model: type[ModelT]) -> None:
        self.events = EventsService(client, f"{path}/events")
        self.history = HistoryService(client, collection_path=f"{path}/history", model=model)


class AuditService:
    """Audit and temporal reads, exposing only routes supported by the server."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self.events = EventsService(client)

    def collection(
        self, collection_id: CollectionId | int
    ) -> ResourceAuditService[wire.HistoryResponseCollectionHistory]:
        return ResourceAuditService(
            self._client,
            f"/api/v1/collections/{_segment(collection_id)}",
            wire.HistoryResponseCollectionHistory,
        )

    def class_(
        self, class_id: ClassId | int
    ) -> ResourceAuditService[wire.HistoryResponseHubuumClassHistory]:
        return ResourceAuditService(
            self._client,
            f"/api/v1/classes/{_segment(class_id)}",
            wire.HistoryResponseHubuumClassHistory,
        )

    def object(
        self, class_id: ClassId | int, object_id: ObjectId | int
    ) -> ResourceAuditService[wire.HistoryResponseHubuumObjectHistory]:
        return ResourceAuditService(
            self._client,
            f"/api/v1/classes/{_segment(class_id)}/{_segment(object_id)}",
            wire.HistoryResponseHubuumObjectHistory,
        )

    def export_template(
        self, template_id: ExportTemplateId | int
    ) -> ResourceAuditService[wire.HistoryResponseExportTemplateHistory]:
        return ResourceAuditService(
            self._client,
            f"/api/v1/export-templates/{_segment(template_id)}",
            wire.HistoryResponseExportTemplateHistory,
        )

    def remote_target(
        self, target_id: RemoteTargetId | int
    ) -> ResourceAuditService[wire.HistoryResponseRemoteTargetHistory]:
        return ResourceAuditService(
            self._client,
            f"/api/v1/remote-targets/{_segment(target_id)}",
            wire.HistoryResponseRemoteTargetHistory,
        )

    def user(self, user_id: UserId | int) -> EventsService:
        return EventsService(self._client, f"/api/v1/iam/users/{_segment(user_id)}/events")

    def group(self, group_id: GroupId | int) -> EventsService:
        return EventsService(self._client, f"/api/v1/iam/groups/{_segment(group_id)}/events")


class CollectionPermissionsService(_CursorService[wire.Permission]):
    """Assignments, inherited grants, and explicit group delegation."""

    def __init__(self, client: Client, collection_id: CollectionId | int) -> None:
        super().__init__(
            client,
            collection_path=f"/api/v1/collections/{_segment(collection_id)}/permissions",
            model=wire.Permission,
        )

    def page(self, query: Query | None = None) -> Page[wire.Permission]:
        response = self._client._request_response(
            "GET",
            self._collection_path,
            options=RequestOptions(params=(query or Query()).as_params()),
        )
        body = decode_model(response, wire.CollectionPermissionSet)
        return Page(
            items=tuple(body.permissions),
            next_cursor=response.headers.get("x-next-cursor"),
            total_count=_header_int(response.headers.get("x-total-count")),
            page_limit=_header_int(response.headers.get("x-page-limit")),
        )

    def assignments(self, query: Query | None = None) -> wire.CollectionPermissionSet:
        return self._client.request(
            "GET",
            self._collection_path,
            response_model=wire.CollectionPermissionSet,
            options=RequestOptions(params=(query or Query()).as_params()),
        )

    def group(self, group_id: GroupId | int) -> wire.CollectionPermissionSet:
        return self._client.request(
            "GET",
            f"{self._collection_path}/group/{_segment(group_id)}",
            response_model=wire.CollectionPermissionSet,
        )

    def principal(self, principal_id: PrincipalId | int) -> _CursorService[wire.GroupPermission]:
        return _CursorService(
            self._client,
            collection_path=f"{self._collection_path}/principal/{_segment(principal_id)}",
            model=wire.GroupPermission,
        )

    def effective_group(
        self, group_id: GroupId | int
    ) -> builtins.list[wire.EffectiveGroupPermission]:
        return _model_list(
            self._client,
            f"{self._collection_path}/effective/group/{_segment(group_id)}",
            wire.EffectiveGroupPermission,
        )

    def effective_principal(
        self, principal_id: PrincipalId | int
    ) -> builtins.list[wire.EffectiveGroupPermission]:
        return _model_list(
            self._client,
            f"{self._collection_path}/effective/principal/{_segment(principal_id)}",
            wire.EffectiveGroupPermission,
        )

    def with_permission(self, permission: Permission) -> _CursorService[wire.GroupResponse]:
        path = self._collection_path.removesuffix("/permissions")
        return _CursorService(
            self._client,
            collection_path=f"{path}/has_permissions/{_segment(permission.value)}",
            model=wire.GroupResponse,
        )

    def check(self, group_id: GroupId | int, permission: Permission) -> bool:
        try:
            self._client.request(
                "GET",
                f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            )
        except NotFoundError:
            return False
        return True

    def grant(
        self,
        group_id: GroupId | int,
        permissions: Sequence[Permission],
        *,
        if_match: str | None = None,
    ) -> wire.CollectionPermissionSet:
        return self._client.request(
            "POST",
            f"{self._collection_path}/group/{_segment(group_id)}",
            json=[p.value for p in permissions],
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    def replace(
        self,
        group_id: GroupId | int,
        permissions: Sequence[Permission],
        *,
        if_match: str | None = None,
    ) -> wire.CollectionPermissionSet:
        return self._client.request(
            "PUT",
            f"{self._collection_path}/group/{_segment(group_id)}",
            json=[p.value for p in permissions],
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    def revoke(
        self, group_id: GroupId | int, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return self._client.request(
            "DELETE",
            f"{self._collection_path}/group/{_segment(group_id)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    def grant_permission(
        self, group_id: GroupId | int, permission: Permission, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return self._client.request(
            "POST",
            f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    def revoke_permission(
        self, group_id: GroupId | int, permission: Permission, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return self._client.request(
            "DELETE",
            f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )


class EventDeliveriesService(_CursorService[wire.EventDeliveryResponse]):
    """Inspect deliveries and explicitly retry or mark one delivery dead."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client, collection_path="/api/v1/event-deliveries", model=wire.EventDeliveryResponse
        )

    def get(self, delivery_id: EventDeliveryId | int) -> wire.EventDeliveryResponse:
        return self._client.request(
            "GET",
            f"{self._collection_path}/{_segment(delivery_id)}",
            response_model=wire.EventDeliveryResponse,
        )

    def health(self) -> wire.EventDeliveryHealthResponse:
        return self._client.request(
            "GET",
            f"{self._collection_path}/health",
            response_model=wire.EventDeliveryHealthResponse,
        )

    def retry(self, delivery_id: EventDeliveryId | int) -> wire.EventDeliveryUpdateResponse:
        return self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(delivery_id)}/retry",
            response_model=wire.EventDeliveryUpdateResponse,
        )

    def mark_dead(self, delivery_id: EventDeliveryId | int) -> wire.EventDeliveryUpdateResponse:
        return self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(delivery_id)}/dead",
            response_model=wire.EventDeliveryUpdateResponse,
        )


class ExportTemplatesService(
    ResourceService[
        wire.ExportTemplate, wire.ExportTemplate, ExportTemplateCreate, ExportTemplateUpdate
    ]
):
    """Reusable exports with bounded discovery, conditional writes, and task output."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/export-templates",
            item_path="/api/v1/export-templates/{id}",
            list_model=wire.ExportTemplate,
            point_model=wire.ExportTemplate,
        )

    def update(
        self, resource_id: object, payload: ExportTemplateUpdate, *, if_match: str | None = None
    ) -> wire.ExportTemplate:
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=wire.ExportTemplate,
            options=_conditional_options(if_match),
        )

    def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=_conditional_options(if_match),
        )

    def audit(
        self, template_id: ExportTemplateId | int
    ) -> ResourceAuditService[wire.HistoryResponseExportTemplateHistory]:
        return self._client.audit.export_template(template_id)

    def submit(
        self, template_id: ExportTemplateId | int, payload: ExportTemplateRunRequest | None = None
    ) -> Task:
        return self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(template_id)}/exports",
            json=payload or ExportTemplateRunRequest(),
            response_model=Task,
        )

    def run(
        self,
        template_id: ExportTemplateId | int,
        payload: ExportTemplateRunRequest | None = None,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> ExportOutput:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = self.submit(template_id, payload)
        task = self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return self._client.exports.output(task.id)


class RemoteTargetsService(
    ResourceService[wire.RemoteTarget, wire.RemoteTarget, RemoteTargetCreate, RemoteTargetUpdate]
):
    """Remote invocation configuration and explicit queued execution."""

    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/remote-targets",
            item_path="/api/v1/remote-targets/{id}",
            list_model=wire.RemoteTarget,
            point_model=wire.RemoteTarget,
        )

    def update(
        self, resource_id: object, payload: RemoteTargetUpdate, *, if_match: str | None = None
    ) -> wire.RemoteTarget:
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=wire.RemoteTarget,
            options=_conditional_options(if_match),
        )

    def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=_conditional_options(if_match),
        )

    def audit(
        self, target_id: RemoteTargetId | int
    ) -> ResourceAuditService[wire.HistoryResponseRemoteTargetHistory]:
        return self._client.audit.remote_target(target_id)

    def invoke(self, target_id: RemoteTargetId | int, payload: RemoteTargetInvokeRequest) -> Task:
        return self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(target_id)}/invoke",
            json=payload,
            response_model=Task,
        )

    def run(
        self,
        target_id: RemoteTargetId | int,
        payload: RemoteTargetInvokeRequest,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> Task:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = self.invoke(target_id, payload)
        task = self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return task


class ClassComputedFieldsService:
    """Shared definitions, previews, and asynchronous class computation state."""

    def __init__(self, client: Client, class_id: ClassId | int) -> None:
        self._client = client
        self._base = f"/api/v1/classes/{_segment(class_id)}/computed-fields"

    def list(self) -> wire.ComputedFieldListResponse:
        return self._client.request(
            "GET", self._base, response_model=wire.ComputedFieldListResponse
        )

    def get(self, field_id: ComputedFieldId | int) -> wire.ComputedFieldDefinition:
        return self._client.request(
            "GET", f"{self._base}/{_segment(field_id)}", response_model=wire.ComputedFieldDefinition
        )

    def create(self, payload: ComputedFieldCreate) -> wire.ComputedFieldMutationResponse:
        return self._client.request(
            "POST", self._base, json=payload, response_model=wire.ComputedFieldMutationResponse
        )

    def update(
        self,
        field_id: ComputedFieldId | int,
        payload: ComputedFieldUpdate,
        *,
        if_match: str | None = None,
    ) -> wire.ComputedFieldMutationResponse:
        return self._client.request(
            "PATCH",
            f"{self._base}/{_segment(field_id)}",
            json=payload,
            response_model=wire.ComputedFieldMutationResponse,
            options=_conditional_options(if_match),
        )

    def delete(
        self, field_id: ComputedFieldId | int, *, if_match: str | None = None
    ) -> wire.ComputedFieldDeleteResponse:
        return self._client.request(
            "DELETE",
            f"{self._base}/{_segment(field_id)}",
            response_model=wire.ComputedFieldDeleteResponse,
            options=_conditional_options(if_match),
        )

    def preview(self, payload: ComputedFieldPreviewRequest) -> wire.ComputedFieldPreviewResponse:
        return self._client.request(
            "POST",
            f"{self._base}/preview",
            json=payload,
            response_model=wire.ComputedFieldPreviewResponse,
        )

    def rebuild(self) -> wire.ClassComputationState:
        return self._client.request(
            "POST", f"{self._base}/rebuild", response_model=wire.ClassComputationState
        )


class PersonalComputedFieldsService(_CursorService[wire.ComputedFieldDefinition]):
    """Definitions owned by the current principal, evaluated independently of shared fields."""

    def __init__(self, client: Client, *, class_id: ClassId | int | None = None) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/me/computed-fields",
            model=wire.ComputedFieldDefinition,
            fixed_params=() if class_id is None else (("class_id", str(class_id)),),
        )

    def for_class(self, class_id: ClassId | int) -> PersonalComputedFieldsService:
        return PersonalComputedFieldsService(self._client, class_id=class_id)

    def get(self, field_id: ComputedFieldId | int) -> wire.ComputedFieldDefinition:
        return self._client.request(
            "GET",
            f"{self._collection_path}/{_segment(field_id)}",
            response_model=wire.ComputedFieldDefinition,
        )

    def create(self, payload: PersonalComputedFieldCreate) -> wire.ComputedFieldDefinition:
        return self._client.request(
            "POST", self._collection_path, json=payload, response_model=wire.ComputedFieldDefinition
        )

    def update(
        self,
        field_id: ComputedFieldId | int,
        payload: ComputedFieldUpdate,
        *,
        if_match: str | None = None,
    ) -> wire.ComputedFieldDefinition:
        return self._client.request(
            "PATCH",
            f"{self._collection_path}/{_segment(field_id)}",
            json=payload,
            response_model=wire.ComputedFieldDefinition,
            options=_conditional_options(if_match),
        )

    def delete(self, field_id: ComputedFieldId | int, *, if_match: str | None = None) -> None:
        self._client.request(
            "DELETE",
            f"{self._collection_path}/{_segment(field_id)}",
            options=_conditional_options(if_match),
        )

    def preview(self, payload: ComputedFieldPreviewRequest) -> wire.ComputedFieldPreviewResponse:
        return self._client.request(
            "POST",
            f"{self._collection_path}/preview",
            json=payload,
            response_model=wire.ComputedFieldPreviewResponse,
        )


class BackupsService:
    """Submit full backups and retrieve the exact backup document."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def submit(self, payload: BackupRequest | None = None) -> Task:
        return self._client.request(
            "POST", "/api/v1/backups", json=payload or BackupRequest(), response_model=Task
        )

    def get(self, task_id: TaskId | int) -> Task:
        return self._client.request(
            "GET", f"/api/v1/backups/{_segment(task_id)}", response_model=Task
        )

    def output(self, task_id: TaskId | int) -> wire.BackupDocument:
        return self._client.request(
            "GET", f"/api/v1/backups/{_segment(task_id)}/output", response_model=wire.BackupDocument
        )

    def run(
        self,
        payload: BackupRequest | None = None,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> wire.BackupDocument:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = self.submit(payload)
        task = self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return self.output(task.id)


class RestoresService:
    """Destructive restore staging, explicit approved confirmation, and capability polling."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def stage(self, backup: wire.BackupDocument) -> wire.RestoreStageResponse:
        return self._client.request(
            "POST", "/api/v1/restores", json=backup, response_model=wire.RestoreStageResponse
        )

    def confirm(
        self,
        restore_id: RestoreJobId | int,
        payload: RestoreConfirmRequest,
        *,
        credential_approval: CredentialApprovalSecret | str,
    ) -> wire.RestoreStageResponse:
        approval = (
            credential_approval.get_secret_value()
            if isinstance(credential_approval, CredentialApprovalSecret)
            else credential_approval
        )
        return self._client.request(
            "POST",
            f"/api/v1/restores/{_segment(restore_id)}/confirm",
            json=payload,
            response_model=wire.RestoreStageResponse,
            options=RequestOptions(headers={"X-Hubuum-Credential-Approval": approval}),
        )

    def status(
        self, restore_id: RestoreJobId | int, *, capability: SecretStr | str
    ) -> wire.RestoreStageResponse:
        secret = capability.get_secret_value() if isinstance(capability, SecretStr) else capability
        return self._client.request(
            "GET",
            f"/api/v1/restores/{_segment(restore_id)}/status",
            response_model=wire.RestoreStageResponse,
            options=RequestOptions(
                authenticated=False, headers={"X-Hubuum-Restore-Capability": secret}
            ),
        )

    def wait(
        self,
        restore_id: RestoreJobId | int,
        *,
        capability: SecretStr | str,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> wire.RestoreStageResponse:
        _validate_polling(timeout_seconds, poll_interval)
        deadline = monotonic() + timeout_seconds
        while True:
            result = self.status(restore_id, capability=capability)
            if result.status in {"succeeded", "failed", "expired"}:
                return result
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError("restore did not finish before the polling deadline")
            sleep(min(poll_interval, remaining))


def _conditional_options(if_match: str | None) -> RequestOptions:
    return RequestOptions(headers={"If-Match": if_match} if if_match is not None else None)


def _validate_polling(timeout_seconds: float, poll_interval: float) -> None:
    if not isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("timeout_seconds must be finite and non-negative")
    if not isfinite(poll_interval) or poll_interval <= 0:
        raise ValueError("poll_interval must be finite and greater than 0")


class SettingsService:
    """Principal settings with explicit JSON Patch/Merge Patch media and ETag controls."""

    def __init__(self, client: Client, path: str) -> None:
        self._client = client
        self._path = path

    def get(self) -> wire.PrincipalSettingsResponse:
        return self._client.request(
            "GET", self._path, response_model=wire.PrincipalSettingsResponse
        )

    def replace(
        self, payload: SettingsRequest, *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        return self._client.request(
            "PUT",
            self._path,
            json=payload.settings,
            response_model=wire.PrincipalSettingsResponse,
            options=_conditional_options(if_match),
        )

    def merge_patch(
        self, payload: SettingsRequest, *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        headers = {"Content-Type": "application/merge-patch+json"}
        if if_match is not None:
            headers["If-Match"] = if_match
        return self._client.request(
            "PATCH",
            self._path,
            json=payload.settings,
            response_model=wire.PrincipalSettingsResponse,
            options=RequestOptions(headers=headers),
        )

    def json_patch(
        self, operations: Sequence[SettingsPatchOperation], *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        headers = {"Content-Type": "application/json-patch+json"}
        if if_match is not None:
            headers["If-Match"] = if_match
        return self._client.request(
            "PATCH",
            self._path,
            json=[operation.payload() for operation in operations],
            response_model=wire.PrincipalSettingsResponse,
            options=RequestOptions(headers=headers),
        )

    def delete(self, *, if_match: str | None = None) -> None:
        self._client.request("DELETE", self._path, options=_conditional_options(if_match))


class PrincipalsService:
    """Current-principal or explicitly addressed settings, groups, and permissions."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def settings(self, principal_id: PrincipalId | int | None = None) -> SettingsService:
        return SettingsService(self._client, f"{_principal_path(principal_id)}/settings")

    def groups(
        self, principal_id: PrincipalId | int | None = None
    ) -> _CursorService[wire.GroupResponse]:
        return _CursorService(
            self._client,
            collection_path=f"{_principal_path(principal_id)}/groups",
            model=wire.GroupResponse,
        )

    def permissions(
        self, principal_id: PrincipalId | int | None = None
    ) -> builtins.list[wire.PrincipalCollectionPermissions]:
        return _model_list(
            self._client,
            f"{_principal_path(principal_id)}/permissions",
            wire.PrincipalCollectionPermissions,
        )


def _principal_path(principal_id: PrincipalId | int | None) -> str:
    return (
        "/api/v1/iam/me"
        if principal_id is None
        else f"/api/v1/iam/principals/{_segment(principal_id)}"
    )


class AuthService:
    """Provider discovery, validation, and explicit administrative revocation.

    Use Client.login_session()/logout() for managed client session state.
    Administrative revocation does not silently replace local credentials.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def providers(self) -> wire.AuthProvidersResponse:
        return self._client.request(
            "GET",
            "/api/v1/auth/providers",
            response_model=wire.AuthProvidersResponse,
            options=RequestOptions(authenticated=False),
        )

    def validate(self) -> wire.MessageResponse:
        return self._client.request(
            "GET", "/api/v1/auth/validate", response_model=wire.MessageResponse
        )

    def revoke_token(self, token: AccessToken | str) -> wire.MessageResponse:
        return self._client.request(
            "POST",
            "/api/v1/auth/logout/token",
            json=wire.LogoutTokenRequest(
                token=SecretStr(token.value if isinstance(token, AccessToken) else token)
            ),
            response_model=wire.MessageResponse,
        )

    def revoke_user(self, user_id: UserId | int) -> wire.MessageResponse:
        return self._client.request(
            "POST",
            f"/api/v1/auth/logout/uid/{_segment(user_id)}",
            response_model=wire.MessageResponse,
        )

    def revoke_all(self) -> wire.MessageResponse:
        return self._client.request(
            "POST", "/api/v1/auth/logout_all", response_model=wire.MessageResponse
        )


class AdminService:
    """Running configuration and operational state; authorization remains server-enforced."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def config(self) -> wire.RunningConfig:
        return self._client.request(
            "GET", "/api/v1/admin/config", response_model=wire.RunningConfig
        )

    def counts(self) -> wire.CountsResponse:
        return self._client.request(
            "GET", "/api/v0/meta/counts", response_model=wire.CountsResponse
        )

    def database(self) -> wire.DbStateResponse:
        return self._client.request("GET", "/api/v0/meta/db", response_model=wire.DbStateResponse)

    def tasks(self) -> wire.TaskQueueStateResponse:
        return self._client.request(
            "GET", "/api/v0/meta/tasks", response_model=wire.TaskQueueStateResponse
        )

    def rate_limits(
        self, *, include: str | None = None, scope: str | None = None, q: str | None = None
    ) -> wire.LoginRateLimitStateResponse:
        params = {
            key: value
            for key, value in (("include", include), ("scope", scope), ("q", q))
            if value is not None
        }
        return self._client.request(
            "GET",
            "/api/v0/meta/login-rate-limit",
            response_model=wire.LoginRateLimitStateResponse,
            options=RequestOptions(params=params),
        )

    def release_rate_limit(self, entry_id: str) -> wire.ReleaseRateLimitResponse:
        return self._client.request(
            "DELETE",
            f"/api/v0/meta/login-rate-limit/{_segment(entry_id)}",
            response_model=wire.ReleaseRateLimitResponse,
        )

    def clear_rate_limits(self) -> wire.ClearRateLimitResponse:
        return self._client.request(
            "DELETE", "/api/v0/meta/login-rate-limit", response_model=wire.ClearRateLimitResponse
        )
