"""Typed asynchronous resource services."""

from __future__ import annotations

import asyncio
import builtins
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime
from math import isfinite
from time import monotonic
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
from .streaming import AsyncResponseStream
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
    from .async_client import AsyncClient

ModelT = TypeVar("ModelT", bound=BaseModel)
PointModelT = TypeVar("PointModelT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def _segment(value: object) -> str:
    return quote(str(value), safe="")


def _header_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class _AsyncCursorService(Generic[ModelT]):
    """Internal async cursor pagination shared by all list endpoints."""

    def __init__(
        self,
        client: AsyncClient,
        *,
        collection_path: str,
        model: type[ModelT],
        fixed_params: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self._client = client
        self._collection_path = collection_path
        self._model = model
        self._fixed_params = fixed_params

    async def page(self, query: Query | None = None) -> Page[ModelT]:
        """Return one cursor page using immutable query controls."""
        response = await self._client._request_response(
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

    async def list(self, query: Query | None = None) -> builtins.list[ModelT]:
        """Return one cursor page as a list."""
        return builtins.list(await self.page(query))

    async def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> AsyncIterator[Page[ModelT]]:
        """Iterate pages with cursor-cycle and page-count guards."""
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        current = query or Query()
        seen = {current.cursor_value} if current.cursor_value is not None else set()
        for _ in range(max_pages):
            page = await self.page(current)
            yield page
            if page.next_cursor is None:
                return
            if page.next_cursor in seen:
                raise RuntimeError("Hubuum returned a repeated pagination cursor")
            seen.add(page.next_cursor)
            current = current.cursor(page.next_cursor)
        raise RuntimeError(f"pagination exceeded max_pages={max_pages}")

    async def all(
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
        async for page in self.pages(query, max_pages=max_pages):
            if len(page) > max_items - len(items):
                raise RuntimeError(f"pagination exceeded max_items={max_items}")
            items.extend(page)
        return items

    async def one(self, query: Query) -> ModelT:
        """Return exactly one matching item or raise a cardinality error."""
        items = await self.list(query.limit(2))
        if len(items) != 1:
            raise ResultCardinalityError(f"expected exactly one result, received {len(items)}")
        return items[0]


class AsyncResourceService(
    _AsyncCursorService[ModelT], Generic[ModelT, PointModelT, CreateT, UpdateT]
):
    """Async CRUD with independently typed collection and point responses."""

    def __init__(
        self,
        client: AsyncClient,
        *,
        collection_path: str,
        item_path: str,
        list_model: type[ModelT],
        point_model: type[PointModelT],
    ) -> None:
        super().__init__(client, collection_path=collection_path, model=list_model)
        self._item_path = item_path
        self._point_model = point_model

    async def get(self, resource_id: object) -> PointModelT:
        """Return one resource by its path identifier."""
        return await self._client.request(
            "GET",
            self._item_path.format(id=_segment(resource_id)),
            response_model=self._point_model,
        )

    async def create(self, payload: CreateT) -> PointModelT:
        """Create and return a resource from a strict request model."""
        return await self._client.request(
            "POST", self._collection_path, json=payload, response_model=self._point_model
        )

    async def update(self, resource_id: object, payload: UpdateT) -> PointModelT:
        """Patch and return one resource by its path identifier."""
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=self._point_model,
        )

    async def delete(self, resource_id: object) -> None:
        """Delete one resource by its path identifier."""
        await self._client.request("DELETE", self._item_path.format(id=_segment(resource_id)))


class AsyncCollectionsService(
    AsyncResourceService[Collection, Collection, CollectionCreate, CollectionUpdate]
):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/collections",
            item_path="/api/v1/collections/{id}",
            list_model=Collection,
            point_model=Collection,
        )

    def permissions(self, collection_id: CollectionId | int) -> AsyncCollectionPermissionsService:
        return AsyncCollectionPermissionsService(self._client, collection_id)

    def event_sinks(self, collection_id: CollectionId | int) -> AsyncCollectionEventSinksService:
        """Permitted destinations and owned-webhook management (server v0.0.18 and newer)."""
        return AsyncCollectionEventSinksService(self._client, CollectionId(collection_id))

    def event_subscriptions(
        self, collection_id: CollectionId | int
    ) -> AsyncEventSubscriptionsService:
        """Collection subscriptions; writes require management and audit permissions."""
        return AsyncEventSubscriptionsService(self._client, CollectionId(collection_id))

    async def children(self, collection_id: CollectionId | int) -> builtins.list[Collection]:
        return await _model_list(
            self._client,
            f"/api/v1/collections/{_segment(collection_id)}/children",
            Collection,
        )

    async def ancestors(self, collection_id: CollectionId | int) -> builtins.list[Collection]:
        return await _model_list(
            self._client,
            f"/api/v1/collections/{_segment(collection_id)}/ancestors",
            Collection,
        )

    async def move(
        self, collection_id: CollectionId | int, parent_id: CollectionId | int | None
    ) -> Collection:
        return await self._client.request(
            "PUT",
            f"/api/v1/collections/{_segment(collection_id)}/parent",
            json={"parent_collection_id": parent_id},
            response_model=Collection,
        )


class AsyncClassesService(AsyncResourceService[HubuumClass, HubuumClass, ClassCreate, ClassUpdate]):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/classes",
            item_path="/api/v1/classes/{id}",
            list_model=HubuumClass,
            point_model=HubuumClass,
        )

    async def get_by_name(self, name: str) -> HubuumClass:
        return await self._client.request(
            "GET", f"/api/v1/classes/by-name/{_segment(name)}", response_model=HubuumClass
        )

    async def update_by_name(self, name: str, payload: ClassUpdate) -> HubuumClass:
        return await self._client.request(
            "PATCH",
            f"/api/v1/classes/by-name/{_segment(name)}",
            json=payload,
            response_model=HubuumClass,
        )

    async def delete_by_name(self, name: str) -> None:
        await self._client.request("DELETE", f"/api/v1/classes/by-name/{_segment(name)}")

    def by_id(self, class_id: ClassId | int) -> AsyncClassService:
        """Select a class and its nested resources by numeric ID."""
        return AsyncClassService(self._client, ClassId(class_id))

    def by_name(self, name: str) -> AsyncNamedClassService:
        """Select the complete natural-key-addressed class surface."""
        return AsyncNamedClassService(self._client, name)


class AsyncClassService:
    """An async class and its nested resources addressed by numeric ID."""

    def __init__(self, client: AsyncClient, class_id: ClassId) -> None:
        self._client = client
        self.class_id = class_id
        self._base = f"/api/v1/classes/{_segment(class_id)}"

    async def fields(self, options: FieldDiscoveryOptions | None = None) -> ClassFieldInventory:
        """Discover authorized fields in one bounded request without downloading object data."""
        return await self._client.request(
            "GET",
            f"{self._base}/fields",
            response_model=ClassFieldInventory,
            options=RequestOptions(params=(options or FieldDiscoveryOptions()).as_params()),
        )

    @property
    def computed_fields(self) -> AsyncClassComputedFieldsService:
        return AsyncClassComputedFieldsService(self._client, self.class_id)

    @property
    def permissions(self) -> _AsyncCursorService[wire.GroupPermission]:
        return _AsyncCursorService(
            self._client, collection_path=f"{self._base}/permissions", model=wire.GroupPermission
        )

    @property
    def schema(self) -> AsyncClassSchemaService:
        return AsyncClassSchemaService(self._client, self.class_id)

    @property
    def objects(self) -> AsyncObjectsService:
        return AsyncObjectsService(self._client, self.class_id)

    async def get(self) -> HubuumClass:
        return await self._client.request("GET", self._base, response_model=HubuumClass)

    async def update(self, payload: ClassUpdate) -> HubuumClass:
        return await self._client.request(
            "PATCH",
            self._base,
            json=payload,
            response_model=HubuumClass,
        )

    async def delete(self) -> None:
        await self._client.request("DELETE", self._base)


class AsyncClassSchemaService:
    """Stage, inspect, and explicitly activate one class's schema revisions."""

    def __init__(self, client: AsyncClient, class_id: ClassId) -> None:
        self._client = client
        self._base = f"/api/v1/classes/{_segment(class_id)}/schema"

    async def profile(
        self,
        payload: SchemaProfileRequest | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> Task:
        """Queue a suggestion; this never stages or activates a schema."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return await self._client.request(
            "POST",
            f"{self._base}/profiles",
            json=payload or SchemaProfileRequest(),
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    async def profile_report(self, task_id: TaskId | int) -> SchemaProfileReport:
        """Read a completed suggestion. Expired reports return HTTP 410 after 24 hours."""
        return await self._client.request(
            "GET",
            f"{self._base}/profiles/{_segment(TaskId(task_id))}",
            response_model=SchemaProfileReport,
        )

    async def suggest(
        self,
        payload: SchemaProfileRequest | None = None,
        *,
        idempotency_key: str | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> SchemaProfileReport:
        """Submit, wait, and fetch a suggestion for explicit review and staging."""
        submitted = await self.profile(payload, idempotency_key=idempotency_key)
        task = await self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return await self.profile_report(task.id)

    async def get(self) -> ClassSchemaResponse:
        """Return the active schema and administrator compliance counts."""
        return await self._client.request("GET", self._base, response_model=ClassSchemaResponse)

    async def revisions(
        self, options: SchemaPageOptions | None = None
    ) -> builtins.list[SchemaRevisionResponse]:
        """Read one bounded revision page; resume after its last revision."""
        response = await self._client._request_response(
            "GET",
            f"{self._base}/revisions",
            options=RequestOptions(params=(options or SchemaPageOptions()).as_params()),
        )
        return decode_model_list(response, SchemaRevisionResponse)

    async def revision(self, revision: SchemaRevision) -> SchemaRevisionResponse:
        """Read one immutable schema revision."""
        return await self._client.request(
            "GET",
            f"{self._base}/revisions/{_segment(revision)}",
            response_model=SchemaRevisionResponse,
        )

    async def stage(self, payload: SchemaStageRequest) -> SchemaRevisionResponse:
        """Stage a policy without changing active validation."""
        return await self._client.request(
            "POST",
            f"{self._base}/revisions",
            json=payload,
            response_model=SchemaRevisionResponse,
        )

    async def abandon(self, revision: SchemaRevision) -> SchemaRevisionResponse:
        """Abandon a staged revision."""
        return await self._client.request(
            "DELETE",
            f"{self._base}/revisions/{_segment(revision)}",
            response_model=SchemaRevisionResponse,
        )

    async def impact(self, revision: SchemaRevision) -> SchemaWorkResponse:
        """Queue an impact analysis against the current object population."""
        return await self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/impact",
            response_model=SchemaWorkResponse,
        )

    async def activate(
        self, revision: SchemaRevision, payload: SchemaActivationRequest
    ) -> SchemaActivationResponse:
        """Activate with an explicit policy and expected active schema revision."""
        return await self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/activate",
            json=payload,
            response_model=SchemaActivationResponse,
        )

    async def revalidate(self, revision: SchemaRevision) -> SchemaWorkResponse:
        """Queue revalidation of the active revision without changing object data."""
        return await self._client.request(
            "POST",
            f"{self._base}/revisions/{_segment(revision)}/revalidate",
            response_model=SchemaWorkResponse,
        )

    async def objects(
        self, options: SchemaPageOptions | None = None, *, status: ComplianceStatus | None = None
    ) -> SchemaCompliancePage:
        """Read authorized evidence; resume with next_after even after an empty page."""
        params = (options or SchemaPageOptions()).as_params()
        if status is not None:
            params.append(("status", status.value))
        return await self._client.request(
            "GET",
            f"{self._base}/objects",
            response_model=SchemaCompliancePage,
            options=RequestOptions(params=params),
        )

    async def work(self, task_id: TaskId | int) -> SchemaWorkResponse:
        """Read saved diagnostics and current readiness for a schema task."""
        return await self._client.request(
            "GET",
            f"{self._base}/tasks/{_segment(task_id)}",
            response_model=SchemaWorkResponse,
        )

    async def cancel(self, task_id: TaskId | int) -> SchemaWorkResponse:
        """Cancel schema work while retaining already committed findings."""
        return await self._client.request(
            "DELETE",
            f"{self._base}/tasks/{_segment(task_id)}",
            response_model=SchemaWorkResponse,
        )

    async def generate_report(
        self, task_id: TaskId | int, payload: SchemaRepairReportRequest
    ) -> str:
        """Generate and retain HTML from saved diagnostics."""
        response = await self._client._request_response(
            "POST",
            f"{self._base}/tasks/{_segment(task_id)}/report",
            json=payload,
            options=RequestOptions(headers={"Accept": "text/html"}),
        )
        return decode_html(response)

    async def report(self, task_id: TaskId | int, *, download: bool = False) -> str:
        """Read retained HTML, optionally requesting an attachment response."""
        response = await self._client._request_response(
            "GET",
            f"{self._base}/tasks/{_segment(task_id)}/report",
            options=RequestOptions(params={"download": download}, headers={"Accept": "text/html"}),
        )
        return decode_html(response)


class AsyncObjectsService(
    AsyncResourceService[HubuumObject, HubuumObject, ObjectCreate, ObjectUpdate]
):
    def __init__(self, client: AsyncClient, class_id: ClassId) -> None:
        self.class_id = class_id
        base = f"/api/v1/classes/{_segment(class_id)}"
        super().__init__(
            client,
            collection_path=f"{base}/",
            item_path=f"{base}/{{id}}",
            list_model=HubuumObject,
            point_model=HubuumObject,
        )

    async def get_by_name(self, name: str) -> HubuumObject:
        return await self.one(Query().where("name", name))

    async def update_by_name(self, name: str, payload: ObjectUpdate) -> HubuumObject:
        return await self.update((await self.get_by_name(name)).id, payload)

    async def delete_by_name(self, name: str) -> None:
        await self.delete((await self.get_by_name(name)).id)

    async def patch_data(
        self,
        object_id: object,
        operations: builtins.list[ObjectDataPatchInput],
    ) -> HubuumObject:
        """Atomically apply RFC 6902 operations relative to the object's data root."""
        return await self._client.request(
            "PATCH",
            f"/api/v1/classes/{_segment(self.class_id)}/{_segment(object_id)}/data",
            json=_object_data_patch_payload(operations),
            response_model=HubuumObject,
            options=RequestOptions(headers={"Content-Type": "application/json-patch+json"}),
        )


class AsyncNamedObjectsService:
    """Async objects addressed through a globally unique class name."""

    def __init__(self, client: AsyncClient, class_name: str) -> None:
        if not class_name.strip():
            raise ValueError("class name must not be empty")
        self._client = client
        self.class_name = class_name
        base = f"/api/v1/classes/by-name/{_segment(class_name)}/objects"
        self._service = AsyncResourceService[
            HubuumObject, HubuumObject, ObjectCreate, ObjectUpdate
        ](
            client,
            collection_path=base,
            item_path=f"{base}/by-name/{{id}}",
            list_model=HubuumObject,
            point_model=HubuumObject,
        )

    async def page(self, query: Query | None = None) -> Page[HubuumObject]:
        return await self._service.page(query)

    async def list(self, query: Query | None = None) -> builtins.list[HubuumObject]:
        return await self._service.list(query)

    async def pages(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> AsyncIterator[Page[HubuumObject]]:
        async for page in self._service.pages(query, max_pages=max_pages):
            yield page

    async def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[HubuumObject]:
        return await self._service.all(query, max_pages=max_pages, max_items=max_items)

    async def one(self, query: Query) -> HubuumObject:
        return await self._service.one(query)

    async def get(self, object_name: str) -> HubuumObject:
        return await self._service.get(_required_name(object_name, "object"))

    async def create(self, payload: ObjectCreate) -> HubuumObject:
        return await self._service.create(payload)

    async def update(self, object_name: str, payload: ObjectUpdate) -> HubuumObject:
        return await self._service.update(_required_name(object_name, "object"), payload)

    async def delete(self, object_name: str) -> None:
        await self._service.delete(_required_name(object_name, "object"))

    async def patch_data(
        self,
        object_name: str,
        operations: builtins.list[ObjectDataPatchInput],
    ) -> HubuumObject:
        """Atomically patch object data with class/object rename safety."""
        path = (
            f"/api/v1/classes/by-name/{_segment(self.class_name)}"
            f"/objects/by-name/{_segment(_required_name(object_name, 'object'))}/data"
        )
        return await self._client.request(
            "PATCH",
            path,
            json=_object_data_patch_payload(operations),
            response_model=HubuumObject,
            options=RequestOptions(headers={"Content-Type": "application/json-patch+json"}),
        )

    async def related_objects(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> builtins.list[dict[str, object]]:
        return await _json_object_list(
            self._client,
            self._related_path(object_name, "objects"),
            params=params,
        )

    async def related_relations(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> builtins.list[dict[str, object]]:
        return await _json_object_list(
            self._client,
            self._related_path(object_name, "relations"),
            params=params,
        )

    async def related_graph(
        self,
        object_name: str,
        *,
        params: Params = None,
    ) -> dict[str, object]:
        return await _json_object(
            self._client,
            self._related_path(object_name, "graph"),
            params=params,
        )

    def _related_path(self, object_name: str, view: str) -> str:
        return (
            f"/api/v1/classes/by-name/{_segment(self.class_name)}"
            f"/objects/by-name/{_segment(_required_name(object_name, 'object'))}"
            f"/related/{view}"
        )


class AsyncNamedClassService:
    """Async class endpoints rooted at ``classes/by-name/{class_name}``."""

    def __init__(self, client: AsyncClient, class_name: str) -> None:
        self._client = client
        self.class_name = _required_name(class_name, "class")
        self._base = f"/api/v1/classes/by-name/{_segment(self.class_name)}"

    async def fields(self, options: FieldDiscoveryOptions | None = None) -> ClassFieldInventory:
        """Discover by exact name, using an ID route for URL dot segments."""
        if self.class_name in {".", ".."}:
            matches = await self._client.classes.list(
                Query().where("name", self.class_name).limit(2).include_total(False)
            )
            if len(matches) != 1:
                raise ResultCardinalityError("expected exactly one class for field discovery")
            return await self._client.classes.by_id(matches[0].id).fields(options)
        return await self._client.request(
            "GET",
            f"{self._base}/fields",
            response_model=ClassFieldInventory,
            options=RequestOptions(params=(options or FieldDiscoveryOptions()).as_params()),
        )

    @property
    def objects(self) -> AsyncNamedObjectsService:
        return AsyncNamedObjectsService(self._client, self.class_name)

    async def get(self) -> HubuumClass:
        return await self._client.request("GET", self._base, response_model=HubuumClass)

    async def update(self, payload: ClassUpdate) -> HubuumClass:
        return await self._client.request(
            "PATCH", self._base, json=payload, response_model=HubuumClass
        )

    async def delete(self) -> None:
        await self._client.request("DELETE", self._base)

    async def permissions(self, *, params: Params = None) -> builtins.list[wire.GroupPermission]:
        response = await self._client._request_response(
            "GET", f"{self._base}/permissions", options=RequestOptions(params=params)
        )
        decode_json_object_list(response)
        return decode_model_list(response, wire.GroupPermission)

    async def related_classes(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return await _json_object_list(self._client, f"{self._base}/related/classes", params=params)

    async def related_relations(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return await _json_object_list(
            self._client, f"{self._base}/related/relations", params=params
        )

    async def related_graph(self, *, params: Params = None) -> dict[str, object]:
        return await _json_object(self._client, f"{self._base}/related/graph", params=params)

    async def object_aggregates(self, *, params: Params) -> Page[ObjectAggregateRow]:
        return await _model_page(
            self._client,
            f"{self._base}/object-aggregates",
            ObjectAggregateRow,
            params=params,
        )


class AsyncCredentialApprovalsService:
    """Obtain single-use password approval and inspect retained evidence."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def create(self, payload: CredentialApprovalRequest) -> CredentialApprovalResponse:
        return await self._client.request(
            "POST",
            "/api/v1/iam/credential-approvals",
            json=payload,
            response_model=CredentialApprovalResponse,
        )

    async def get(self, approval_id: CredentialApprovalId | int) -> CredentialApprovalRecord:
        return await self._client.request(
            "GET",
            f"/api/v1/iam/credential-approvals/{_segment(approval_id)}",
            response_model=CredentialApprovalRecord,
        )


class AsyncUsersService(AsyncResourceService[User, UserPoint, UserCreate, UserUpdate]):
    """Async user lists with canonical point responses for reads and mutations."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/users",
            item_path="/api/v1/iam/users/{id}",
            list_model=User,
            point_model=UserPoint,
        )

    async def create(
        self, payload: UserCreate, *, approval: CredentialApprovalResponse | None = None
    ) -> UserPoint:
        """Create a local user using an operation-bound approval."""
        return await self._client.request(
            "POST",
            self._collection_path,
            json=payload,
            response_model=UserPoint,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )

    async def update(
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
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=UserPoint,
            options=replace(request_options, headers=headers),
        )

    async def get_by_name(self, name: str) -> User:
        return await self.one(Query().where("name", name))

    async def anonymize(self, user_id: UserId | int) -> None:
        await self._client.request("POST", f"/api/v1/iam/users/{_segment(user_id)}/anonymize")


class AsyncServiceAccountsService(
    AsyncResourceService[
        ServiceAccount, ServiceAccountPoint, ServiceAccountCreate, ServiceAccountUpdate
    ]
):
    """Manage automation identities with guarded lists and revision-owned mutations."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/service-accounts",
            item_path="/api/v1/iam/service-accounts/{id}",
            list_model=ServiceAccount,
            point_model=ServiceAccountPoint,
        )

    async def get_by_name(self, name: str, *, identity_scope: str | None = None) -> ServiceAccount:
        """Find exactly one account, optionally restricting its identity scope."""
        query = Query().where("name", name)
        if identity_scope is not None:
            query = query.where("identity_scope", identity_scope)
        return await self.one(query)

    async def update(
        self,
        resource_id: object,
        payload: ServiceAccountUpdate,
        *,
        if_match: str | None = None,
    ) -> ServiceAccountPoint:
        """Edit description or ownership, optionally requiring the current ETag."""
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=ServiceAccountPoint,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    async def disable(
        self, service_account_id: ServiceAccountId | int, *, if_match: str | None = None
    ) -> ServiceAccountPoint:
        """Disable the account and revoke its tokens, with an optional ETag check."""
        return await self._client.request(
            "POST",
            f"{self._item_path.format(id=_segment(service_account_id))}/disable",
            response_model=ServiceAccountPoint,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    async def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        """Delete the account, optionally requiring the current ETag."""
        await self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )


class AsyncGroupsService(AsyncResourceService[Group, GroupPoint, GroupCreate, GroupUpdate]):
    """Async group lists with revision-owned point responses for reads and mutations."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/groups",
            item_path="/api/v1/iam/groups/{id}",
            list_model=Group,
            point_model=GroupPoint,
        )

    async def get_by_name(self, name: str) -> Group:
        return await self.one(Query().where("groupname", name))

    def _members_service(
        self, group_id: GroupId | int
    ) -> AsyncResourceService[PrincipalMember, PrincipalMember, BaseModel, BaseModel]:
        path = f"/api/v1/iam/groups/{_segment(group_id)}/members"
        return AsyncResourceService(
            self._client,
            collection_path=path,
            item_path=f"{path}/{{id}}",
            list_model=PrincipalMember,
            point_model=PrincipalMember,
        )

    async def members_page(
        self, group_id: GroupId | int, query: Query | None = None
    ) -> Page[PrincipalMember]:
        return await self._members_service(group_id).page(query)

    async def members(
        self, group_id: GroupId | int, query: Query | None = None
    ) -> builtins.list[PrincipalMember]:
        return await self._members_service(group_id).list(query)

    async def member_pages(
        self,
        group_id: GroupId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> AsyncIterator[Page[PrincipalMember]]:
        async for page in self._members_service(group_id).pages(query, max_pages=max_pages):
            yield page

    async def all_members(
        self,
        group_id: GroupId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalMember]:
        return await self._members_service(group_id).all(
            query,
            max_pages=max_pages,
            max_items=max_items,
        )

    async def add_member(
        self, group_id: GroupId | int, principal_id: PrincipalId | int
    ) -> PrincipalMember:
        return await self._client.request(
            "POST",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
            response_model=PrincipalMember,
        )

    async def remove_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        await self._client.request(
            "DELETE",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )


class _AsyncTokenListService:
    """Shared async lifecycle-aware token pagination behavior."""

    def __init__(self, client: AsyncClient, collection_path: str) -> None:
        self._client = client
        self._collection_path = collection_path

    def _service(self, state: TokenListState) -> _AsyncCursorService[PrincipalTokenMetadata]:
        return _AsyncCursorService(
            self._client,
            collection_path=self._collection_path,
            model=PrincipalTokenMetadata,
            fixed_params=(("state", state.value),),
        )

    async def page(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
    ) -> Page[PrincipalTokenMetadata]:
        return await self._service(state).page(query)

    async def list(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return await self._service(state).list(query)

    async def pages(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
        max_pages: int = 100,
    ) -> AsyncIterator[Page[PrincipalTokenMetadata]]:
        async for page in self._service(state).pages(query, max_pages=max_pages):
            yield page

    async def all(
        self,
        query: Query | None = None,
        *,
        state: TokenListState = TokenListState.ACTIVE,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return await self._service(state).all(query, max_pages=max_pages, max_items=max_items)


class AsyncTokensService(_AsyncTokenListService):
    """Async token metadata visible to the current human user."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client, "/api/v1/iam/me/tokens")

    def for_principal(self, principal_id: PrincipalId | int) -> AsyncPrincipalTokensService:
        return AsyncPrincipalTokensService(self._client, PrincipalId(principal_id))


class AsyncPrincipalTokensService(_AsyncTokenListService):
    """Async list, inspect, mint, renew, and revoke operations for one principal."""

    def __init__(self, client: AsyncClient, principal_id: PrincipalId) -> None:
        self.principal_id = principal_id
        self._base = f"/api/v1/iam/principals/{_segment(principal_id)}/tokens"
        super().__init__(client, self._base)

    async def get(self, token_id: TokenId | int) -> PrincipalTokenPoint:
        return await self._client.request(
            "GET",
            f"{self._base}/{_segment(token_id)}",
            response_model=PrincipalTokenPoint,
        )

    async def create(
        self, payload: NewTokenRequest, *, approval: CredentialApprovalResponse | None = None
    ) -> AccessToken:
        response = await self._client.request(
            "POST",
            self._base,
            json=approval.token_request(payload) if approval else payload,
            response_model=LoginResponse,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )
        return AccessToken(response.token, expires_at=response.expires_at)

    async def revoke(self, token_id: TokenId | int) -> None:
        await self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/revoke",
        )

    async def renew(
        self,
        token_id: TokenId | int,
        payload: RenewTokenRequest | None = None,
        *,
        approval: CredentialApprovalResponse | None = None,
    ) -> AccessToken:
        response = await self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/renew",
            json=approval.token_request(payload or RenewTokenRequest())
            if approval
            else payload or RenewTokenRequest(),
            response_model=LoginResponse,
            options=RequestOptions(headers=approval.headers() if approval else None),
        )
        return AccessToken(response.token, expires_at=response.expires_at)


class AsyncClassRelationsService:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client
        self._service = AsyncResourceService[
            ClassRelation, ClassRelation, ClassRelationCreate, BaseModel
        ](
            client,
            collection_path="/api/v1/relations/classes",
            item_path="/api/v1/relations/classes/{id}",
            list_model=ClassRelation,
            point_model=ClassRelation,
        )

    async def page(self, query: Query | None = None) -> Page[ClassRelation]:
        """Return one cursor page of class relations."""
        return await self._service.page(query)

    async def list(self, query: Query | None = None) -> builtins.list[ClassRelation]:
        return await self._service.list(query)

    async def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> AsyncIterator[Page[ClassRelation]]:
        """Iterate class relation pages with cursor-cycle and page-count guards."""
        async for page in self._service.pages(query, max_pages=max_pages):
            yield page

    async def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ClassRelation]:
        """Collect class relations with explicit page and item bounds."""
        return await self._service.all(query, max_pages=max_pages, max_items=max_items)

    async def one(self, query: Query) -> ClassRelation:
        return await self._service.one(query)

    async def get(self, relation_id: int) -> ClassRelation:
        return await self._service.get(relation_id)

    async def create(self, payload: ClassRelationCreate) -> ClassRelation:
        return await self._service.create(payload)

    async def update(
        self, relation_id: int, payload: ClassRelationUpdate, *, if_match: str | None = None
    ) -> ClassRelation:
        """Edit labels, optionally requiring the resource's current strong ETag."""
        return await self._client.request(
            "PATCH",
            f"/api/v1/relations/classes/{_segment(relation_id)}",
            json=payload,
            response_model=ClassRelation,
            options=RequestOptions(headers={"If-Match": if_match} if if_match else None),
        )

    async def delete(self, relation_id: int) -> None:
        await self._service.delete(relation_id)


class AsyncObjectRelationsService:
    def __init__(self, client: AsyncClient) -> None:
        self._service = AsyncResourceService[
            ObjectRelation, ObjectRelation, ObjectRelationCreate, BaseModel
        ](
            client,
            collection_path="/api/v1/relations/objects",
            item_path="/api/v1/relations/objects/{id}",
            list_model=ObjectRelation,
            point_model=ObjectRelation,
        )

    async def page(self, query: Query | None = None) -> Page[ObjectRelation]:
        """Return one cursor page of object relations."""
        return await self._service.page(query)

    async def list(self, query: Query | None = None) -> builtins.list[ObjectRelation]:
        return await self._service.list(query)

    async def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> AsyncIterator[Page[ObjectRelation]]:
        """Iterate object relation pages with cursor-cycle and page-count guards."""
        async for page in self._service.pages(query, max_pages=max_pages):
            yield page

    async def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ObjectRelation]:
        """Collect object relations with explicit page and item bounds."""
        return await self._service.all(query, max_pages=max_pages, max_items=max_items)

    async def one(self, query: Query) -> ObjectRelation:
        return await self._service.one(query)

    async def get(self, relation_id: int) -> ObjectRelation:
        return await self._service.get(relation_id)

    async def create(self, payload: ObjectRelationCreate) -> ObjectRelation:
        return await self._service.create(payload)

    async def delete(self, relation_id: int) -> None:
        await self._service.delete(relation_id)


class AsyncTasksService:
    """Inspect, paginate, and wait for asynchronous Hubuum tasks."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client
        self._service = _AsyncCursorService[Task](
            client,
            collection_path="/api/v1/tasks",
            model=Task,
        )

    async def page(self, query: Query | None = None) -> Page[Task]:
        """Return one cursor page of visible tasks."""
        return await self._service.page(query)

    async def list(self, query: Query | None = None) -> builtins.list[Task]:
        """Return one page of visible tasks as a list."""
        return await self._service.list(query)

    async def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> AsyncIterator[Page[Task]]:
        """Iterate bounded cursor pages of visible tasks."""
        async for page in self._service.pages(query, max_pages=max_pages):
            yield page

    async def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[Task]:
        """Collect visible tasks with explicit page and item safety bounds."""
        return await self._service.all(query, max_pages=max_pages, max_items=max_items)

    async def get(self, task_id: TaskId | int) -> Task:
        """Return a task by numeric ID."""
        return await self._client.request(
            "GET", f"/api/v1/tasks/{_segment(task_id)}", response_model=Task
        )

    async def cancel(self, task_id: TaskId | int, payload: TaskCancelRequest | None = None) -> Task:
        """Request cancellation; 202 means cleanup is pending, so use wait() for completion."""
        return await self._client.request(
            "POST",
            f"/api/v1/tasks/{_segment(task_id)}/cancel",
            json=payload if payload is not None else TaskCancelRequest(),
            response_model=Task,
        )

    async def events_page(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> Page[TaskEvent]:
        """Return one cursor page from a task's event history."""
        return await _AsyncCursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        ).page(query)

    async def events(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> builtins.list[TaskEvent]:
        """Return one page from a task's event history as a list."""
        return builtins.list(await self.events_page(task_id, query))

    async def event_pages(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> AsyncIterator[Page[TaskEvent]]:
        """Iterate bounded cursor pages from a task's event history."""
        service = _AsyncCursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        )
        async for page in service.pages(query, max_pages=max_pages):
            yield page

    async def all_events(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[TaskEvent]:
        """Collect a task's events with explicit page and item bounds."""
        return await _AsyncCursorService[TaskEvent](
            self._client,
            collection_path=f"/api/v1/tasks/{_segment(task_id)}/events",
            model=TaskEvent,
        ).all(query, max_pages=max_pages, max_items=max_items)

    async def wait(
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
            task = await self.get(task_id)
            if task.status.terminal:
                return task
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"task {task_id} did not finish within {timeout_seconds} seconds"
                )
            await asyncio.sleep(min(poll_interval, remaining))


class AsyncImportsService:
    """Async import submission and per-entity outcome inspection."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def submit(
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
        return await self._client.request(
            "POST",
            "/api/v1/imports",
            json=payload,
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    async def get(self, task_id: TaskId | int) -> Task:
        """Return an import task through its domain-specific route."""
        return await self._client.request(
            "GET", f"/api/v1/imports/{_segment(task_id)}", response_model=Task
        )

    async def results_page(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> Page[ImportTaskResult]:
        """Return one cursor page of per-entity import outcomes."""
        return await self._results_service(task_id).page(query)

    async def results(
        self, task_id: TaskId | int, query: Query | None = None
    ) -> builtins.list[ImportTaskResult]:
        """Return one page of per-entity import outcomes as a list."""
        return await self._results_service(task_id).list(query)

    async def result_pages(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> AsyncIterator[Page[ImportTaskResult]]:
        """Iterate bounded cursor pages of per-entity import outcomes."""
        async for page in self._results_service(task_id).pages(query, max_pages=max_pages):
            yield page

    async def all_results(
        self,
        task_id: TaskId | int,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[ImportTaskResult]:
        """Collect import outcomes with explicit page and item bounds."""
        return await self._results_service(task_id).all(
            query, max_pages=max_pages, max_items=max_items
        )

    # Preserve the existing keyword API while matching all_results()'s bounds.
    async def run(  # noqa: PLR0913
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
        submitted = await self.submit(payload, idempotency_key=idempotency_key, approval=approval)
        task = await self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if not task.status.successful:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return ImportRunResult(
            task=task,
            results=tuple(
                await self.all_results(task.id, max_pages=max_pages, max_items=max_items)
            ),
        )

    def _results_service(self, task_id: TaskId | int) -> _AsyncCursorService[ImportTaskResult]:
        return _AsyncCursorService(
            self._client,
            collection_path=f"/api/v1/imports/{_segment(task_id)}/results",
            model=ImportTaskResult,
        )


class AsyncExportsService:
    """Async export submission and typed or rendered output retrieval."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def submit(self, payload: ExportRequest, *, idempotency_key: str | None = None) -> Task:
        """Submit an export task, optionally with a replay-safe idempotency key."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return await self._client.request(
            "POST",
            "/api/v1/exports",
            json=payload,
            response_model=Task,
            options=RequestOptions(headers=headers),
        )

    async def get(self, task_id: TaskId | int) -> Task:
        """Return an export task through its domain-specific route."""
        return await self._client.request(
            "GET", f"/api/v1/exports/{_segment(task_id)}", response_model=Task
        )

    async def output(self, task_id: TaskId | int) -> ExportOutput:
        """Return JSON output as a model and rendered output as text."""
        response = await self._client._request_response(
            "GET", f"/api/v1/exports/{_segment(task_id)}/output"
        )
        content_type = decode_content_type(
            response, ExportContentType, default=ExportContentType.JSON
        )
        if content_type is ExportContentType.JSON:
            return decode_model(response, ExportJsonResponse)
        return RenderedExport(content_type=content_type, body=response.text)

    @asynccontextmanager
    async def output_stream(self, task_id: TaskId | int) -> AsyncIterator[AsyncResponseStream]:
        """Stream export output while keeping the response lifetime bounded."""
        async with self._client.stream(
            "GET", f"/api/v1/exports/{_segment(task_id)}/output"
        ) as stream:
            yield stream

    async def run(
        self,
        payload: ExportRequest,
        *,
        idempotency_key: str | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> ExportOutput:
        """Submit and await an export, then return its generated output."""
        submitted = await self.submit(payload, idempotency_key=idempotency_key)
        task = await self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if not task.status.successful:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return await self.output(task.id)


async def _model_list(client: AsyncClient, path: str, model: type[ModelT]) -> builtins.list[ModelT]:
    response = await client._request_response("GET", path)
    return decode_model_list(response, model)


def _required_name(value: str, resource: str) -> str:
    if not value.strip():
        raise ValueError(f"{resource} name must not be empty")
    return value


async def _json_object(
    client: AsyncClient,
    path: str,
    *,
    params: Params = None,
) -> dict[str, object]:
    response = await client._request_response("GET", path, options=RequestOptions(params=params))
    return decode_json_object(response)


async def _json_object_list(
    client: AsyncClient,
    path: str,
    *,
    params: Params = None,
) -> builtins.list[dict[str, object]]:
    response = await client._request_response("GET", path, options=RequestOptions(params=params))
    return decode_json_object_list(response)


async def _model_page(
    client: AsyncClient,
    path: str,
    model: type[ModelT],
    *,
    params: Params,
) -> Page[ModelT]:
    response = await client._request_response("GET", path, options=RequestOptions(params=params))
    value = decode_model_list(response, model)
    return Page(
        items=tuple(value),
        next_cursor=response.headers.get("x-next-cursor"),
        total_count=_header_int(response.headers.get("x-total-count")),
        page_limit=_header_int(response.headers.get("x-page-limit")),
    )


class AsyncCollectionEventSinksService(
    AsyncResourceService[CollectionEventSink, CollectionEventSink, EventSinkCreate, EventSinkUpdate]
):
    """Create fixed-destination webhooks owned by a collection and discover permitted sinks."""

    def __init__(self, client: AsyncClient, collection_id: CollectionId) -> None:
        base = f"/api/v1/collections/{_segment(collection_id)}/event-sinks"
        super().__init__(
            client,
            collection_path=base,
            item_path=base + "/{id}",
            list_model=CollectionEventSink,
            point_model=CollectionEventSink,
        )


class AsyncEventSubscriptionsService(
    AsyncResourceService[
        EventSubscription, EventSubscription, EventSubscriptionCreate, EventSubscriptionUpdate
    ]
):
    """Collection event subscriptions with bounded cursor pagination."""

    def __init__(self, client: AsyncClient, collection_id: CollectionId) -> None:
        base = f"/api/v1/collections/{_segment(collection_id)}/event-subscriptions"
        super().__init__(
            client,
            collection_path=base,
            item_path=base + "/{id}",
            list_model=EventSubscription,
            point_model=EventSubscription,
        )


class AsyncEventSinksService(
    AsyncResourceService[EventSink, EventSink, EventSinkCreate, EventSinkUpdate]
):
    """Administrator sink CRUD and explicit collection-use grants."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/event-sinks",
            item_path="/api/v1/event-sinks/{id}",
            list_model=EventSink,
            point_model=EventSink,
        )

    async def collections(self, sink_id: EventSinkId | int) -> builtins.list[CollectionId]:
        """List direct grants; requires server collection-integration support."""
        result = await self._client.request(
            "GET",
            f"/api/v1/event-sinks/{_segment(sink_id)}/collections",
            response_model=_EventSinkCollectionIds,
        )
        return result.root

    async def grant(self, sink_id: EventSinkId | int, collection_id: CollectionId | int) -> None:
        """Permit one collection to use a global sink."""
        await self._client.request(
            "PUT", f"/api/v1/event-sinks/{_segment(sink_id)}/collections/{_segment(collection_id)}"
        )

    async def revoke(self, sink_id: EventSinkId | int, collection_id: CollectionId | int) -> None:
        """Revoke a grant, including admission of queued deliveries."""
        await self._client.request(
            "DELETE",
            f"/api/v1/event-sinks/{_segment(sink_id)}/collections/{_segment(collection_id)}",
        )


class AsyncEventsService(_AsyncCursorService[wire.EventResponse]):
    """A bounded global or resource-scoped audit feed; requires audit permission."""

    def __init__(self, client: AsyncClient, path: str = "/api/v1/events") -> None:
        super().__init__(client, collection_path=path, model=wire.EventResponse)


class AsyncHistoryService(_AsyncCursorService[ModelT]):
    """Bounded versions and a point-in-time read of one supported resource."""

    async def as_of(self, at: datetime) -> ModelT:
        return await self._client.request(
            "GET",
            f"{self._collection_path}/as-of",
            response_model=self._model,
            options=RequestOptions(params={"at": aware_timestamp(at)}),
        )


class AsyncResourceAuditService(Generic[ModelT]):
    def __init__(self, client: AsyncClient, path: str, model: type[ModelT]) -> None:
        self.events = AsyncEventsService(client, f"{path}/events")
        self.history = AsyncHistoryService(client, collection_path=f"{path}/history", model=model)


class AsyncAuditService:
    """Audit and temporal reads, exposing only routes supported by the server."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client
        self.events = AsyncEventsService(client)

    def collection(
        self, collection_id: CollectionId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseCollectionHistory]:
        return AsyncResourceAuditService(
            self._client,
            f"/api/v1/collections/{_segment(collection_id)}",
            wire.HistoryResponseCollectionHistory,
        )

    def class_(
        self, class_id: ClassId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseHubuumClassHistory]:
        return AsyncResourceAuditService(
            self._client,
            f"/api/v1/classes/{_segment(class_id)}",
            wire.HistoryResponseHubuumClassHistory,
        )

    def object(
        self, class_id: ClassId | int, object_id: ObjectId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseHubuumObjectHistory]:
        return AsyncResourceAuditService(
            self._client,
            f"/api/v1/classes/{_segment(class_id)}/{_segment(object_id)}",
            wire.HistoryResponseHubuumObjectHistory,
        )

    def export_template(
        self, template_id: ExportTemplateId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseExportTemplateHistory]:
        return AsyncResourceAuditService(
            self._client,
            f"/api/v1/export-templates/{_segment(template_id)}",
            wire.HistoryResponseExportTemplateHistory,
        )

    def remote_target(
        self, target_id: RemoteTargetId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseRemoteTargetHistory]:
        return AsyncResourceAuditService(
            self._client,
            f"/api/v1/remote-targets/{_segment(target_id)}",
            wire.HistoryResponseRemoteTargetHistory,
        )

    def user(self, user_id: UserId | int) -> AsyncEventsService:
        return AsyncEventsService(self._client, f"/api/v1/iam/users/{_segment(user_id)}/events")

    def group(self, group_id: GroupId | int) -> AsyncEventsService:
        return AsyncEventsService(self._client, f"/api/v1/iam/groups/{_segment(group_id)}/events")


class AsyncCollectionPermissionsService(_AsyncCursorService[wire.Permission]):
    """Assignments, inherited grants, and explicit group delegation."""

    def __init__(self, client: AsyncClient, collection_id: CollectionId | int) -> None:
        super().__init__(
            client,
            collection_path=f"/api/v1/collections/{_segment(collection_id)}/permissions",
            model=wire.Permission,
        )

    async def page(self, query: Query | None = None) -> Page[wire.Permission]:
        response = await self._client._request_response(
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

    async def assignments(self, query: Query | None = None) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "GET",
            self._collection_path,
            response_model=wire.CollectionPermissionSet,
            options=RequestOptions(params=(query or Query()).as_params()),
        )

    async def group(self, group_id: GroupId | int) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "GET",
            f"{self._collection_path}/group/{_segment(group_id)}",
            response_model=wire.CollectionPermissionSet,
        )

    def principal(
        self, principal_id: PrincipalId | int
    ) -> _AsyncCursorService[wire.GroupPermission]:
        return _AsyncCursorService(
            self._client,
            collection_path=f"{self._collection_path}/principal/{_segment(principal_id)}",
            model=wire.GroupPermission,
        )

    async def effective_group(
        self, group_id: GroupId | int
    ) -> builtins.list[wire.EffectiveGroupPermission]:
        return await _model_list(
            self._client,
            f"{self._collection_path}/effective/group/{_segment(group_id)}",
            wire.EffectiveGroupPermission,
        )

    async def effective_principal(
        self, principal_id: PrincipalId | int
    ) -> builtins.list[wire.EffectiveGroupPermission]:
        return await _model_list(
            self._client,
            f"{self._collection_path}/effective/principal/{_segment(principal_id)}",
            wire.EffectiveGroupPermission,
        )

    def with_permission(self, permission: Permission) -> _AsyncCursorService[wire.GroupResponse]:
        path = self._collection_path.removesuffix("/permissions")
        return _AsyncCursorService(
            self._client,
            collection_path=f"{path}/has_permissions/{_segment(permission.value)}",
            model=wire.GroupResponse,
        )

    async def check(self, group_id: GroupId | int, permission: Permission) -> bool:
        try:
            await self._client.request(
                "GET",
                f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            )
        except NotFoundError:
            return False
        return True

    async def grant(
        self,
        group_id: GroupId | int,
        permissions: Sequence[Permission],
        *,
        if_match: str | None = None,
    ) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/group/{_segment(group_id)}",
            json=[p.value for p in permissions],
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    async def replace(
        self,
        group_id: GroupId | int,
        permissions: Sequence[Permission],
        *,
        if_match: str | None = None,
    ) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "PUT",
            f"{self._collection_path}/group/{_segment(group_id)}",
            json=[p.value for p in permissions],
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    async def revoke(
        self, group_id: GroupId | int, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "DELETE",
            f"{self._collection_path}/group/{_segment(group_id)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    async def grant_permission(
        self, group_id: GroupId | int, permission: Permission, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )

    async def revoke_permission(
        self, group_id: GroupId | int, permission: Permission, *, if_match: str | None = None
    ) -> wire.CollectionPermissionSet:
        return await self._client.request(
            "DELETE",
            f"{self._collection_path}/group/{_segment(group_id)}/{_segment(permission.value)}",
            response_model=wire.CollectionPermissionSet,
            options=_conditional_options(if_match),
        )


class AsyncEventDeliveriesService(_AsyncCursorService[wire.EventDeliveryResponse]):
    """Inspect deliveries and explicitly retry or mark one delivery dead."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client, collection_path="/api/v1/event-deliveries", model=wire.EventDeliveryResponse
        )

    async def get(self, delivery_id: EventDeliveryId | int) -> wire.EventDeliveryResponse:
        return await self._client.request(
            "GET",
            f"{self._collection_path}/{_segment(delivery_id)}",
            response_model=wire.EventDeliveryResponse,
        )

    async def health(self) -> wire.EventDeliveryHealthResponse:
        return await self._client.request(
            "GET",
            f"{self._collection_path}/health",
            response_model=wire.EventDeliveryHealthResponse,
        )

    async def retry(self, delivery_id: EventDeliveryId | int) -> wire.EventDeliveryUpdateResponse:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(delivery_id)}/retry",
            response_model=wire.EventDeliveryUpdateResponse,
        )

    async def mark_dead(
        self, delivery_id: EventDeliveryId | int
    ) -> wire.EventDeliveryUpdateResponse:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(delivery_id)}/dead",
            response_model=wire.EventDeliveryUpdateResponse,
        )


class AsyncExportTemplatesService(
    AsyncResourceService[
        wire.ExportTemplate, wire.ExportTemplate, ExportTemplateCreate, ExportTemplateUpdate
    ]
):
    """Reusable exports with bounded discovery, conditional writes, and task output."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/export-templates",
            item_path="/api/v1/export-templates/{id}",
            list_model=wire.ExportTemplate,
            point_model=wire.ExportTemplate,
        )

    async def update(
        self, resource_id: object, payload: ExportTemplateUpdate, *, if_match: str | None = None
    ) -> wire.ExportTemplate:
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=wire.ExportTemplate,
            options=_conditional_options(if_match),
        )

    async def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        await self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=_conditional_options(if_match),
        )

    def audit(
        self, template_id: ExportTemplateId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseExportTemplateHistory]:
        return self._client.audit.export_template(template_id)

    async def submit(
        self, template_id: ExportTemplateId | int, payload: ExportTemplateRunRequest | None = None
    ) -> Task:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(template_id)}/exports",
            json=payload or ExportTemplateRunRequest(),
            response_model=Task,
        )

    async def run(
        self,
        template_id: ExportTemplateId | int,
        payload: ExportTemplateRunRequest | None = None,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> ExportOutput:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = await self.submit(template_id, payload)
        task = await self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return await self._client.exports.output(task.id)


class AsyncRemoteTargetsService(
    AsyncResourceService[
        wire.RemoteTarget, wire.RemoteTarget, RemoteTargetCreate, RemoteTargetUpdate
    ]
):
    """Remote invocation configuration and explicit queued execution."""

    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/remote-targets",
            item_path="/api/v1/remote-targets/{id}",
            list_model=wire.RemoteTarget,
            point_model=wire.RemoteTarget,
        )

    async def update(
        self, resource_id: object, payload: RemoteTargetUpdate, *, if_match: str | None = None
    ) -> wire.RemoteTarget:
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=wire.RemoteTarget,
            options=_conditional_options(if_match),
        )

    async def delete(self, resource_id: object, *, if_match: str | None = None) -> None:
        await self._client.request(
            "DELETE",
            self._item_path.format(id=_segment(resource_id)),
            options=_conditional_options(if_match),
        )

    def audit(
        self, target_id: RemoteTargetId | int
    ) -> AsyncResourceAuditService[wire.HistoryResponseRemoteTargetHistory]:
        return self._client.audit.remote_target(target_id)

    async def invoke(
        self, target_id: RemoteTargetId | int, payload: RemoteTargetInvokeRequest
    ) -> Task:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/{_segment(target_id)}/invoke",
            json=payload,
            response_model=Task,
        )

    async def run(
        self,
        target_id: RemoteTargetId | int,
        payload: RemoteTargetInvokeRequest,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> Task:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = await self.invoke(target_id, payload)
        task = await self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return task


class AsyncClassComputedFieldsService:
    """Shared definitions, previews, and asynchronous class computation state."""

    def __init__(self, client: AsyncClient, class_id: ClassId | int) -> None:
        self._client = client
        self._base = f"/api/v1/classes/{_segment(class_id)}/computed-fields"

    async def list(self) -> wire.ComputedFieldListResponse:
        return await self._client.request(
            "GET", self._base, response_model=wire.ComputedFieldListResponse
        )

    async def get(self, field_id: ComputedFieldId | int) -> wire.ComputedFieldDefinition:
        return await self._client.request(
            "GET", f"{self._base}/{_segment(field_id)}", response_model=wire.ComputedFieldDefinition
        )

    async def create(self, payload: ComputedFieldCreate) -> wire.ComputedFieldMutationResponse:
        return await self._client.request(
            "POST", self._base, json=payload, response_model=wire.ComputedFieldMutationResponse
        )

    async def update(
        self,
        field_id: ComputedFieldId | int,
        payload: ComputedFieldUpdate,
        *,
        if_match: str | None = None,
    ) -> wire.ComputedFieldMutationResponse:
        return await self._client.request(
            "PATCH",
            f"{self._base}/{_segment(field_id)}",
            json=payload,
            response_model=wire.ComputedFieldMutationResponse,
            options=_conditional_options(if_match),
        )

    async def delete(
        self, field_id: ComputedFieldId | int, *, if_match: str | None = None
    ) -> wire.ComputedFieldDeleteResponse:
        return await self._client.request(
            "DELETE",
            f"{self._base}/{_segment(field_id)}",
            response_model=wire.ComputedFieldDeleteResponse,
            options=_conditional_options(if_match),
        )

    async def preview(
        self, payload: ComputedFieldPreviewRequest
    ) -> wire.ComputedFieldPreviewResponse:
        return await self._client.request(
            "POST",
            f"{self._base}/preview",
            json=payload,
            response_model=wire.ComputedFieldPreviewResponse,
        )

    async def rebuild(self) -> wire.ClassComputationState:
        return await self._client.request(
            "POST", f"{self._base}/rebuild", response_model=wire.ClassComputationState
        )


class AsyncPersonalComputedFieldsService(_AsyncCursorService[wire.ComputedFieldDefinition]):
    """Definitions owned by the current principal, evaluated independently of shared fields."""

    def __init__(self, client: AsyncClient, *, class_id: ClassId | int | None = None) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/me/computed-fields",
            model=wire.ComputedFieldDefinition,
            fixed_params=() if class_id is None else (("class_id", str(class_id)),),
        )

    def for_class(self, class_id: ClassId | int) -> AsyncPersonalComputedFieldsService:
        return AsyncPersonalComputedFieldsService(self._client, class_id=class_id)

    async def get(self, field_id: ComputedFieldId | int) -> wire.ComputedFieldDefinition:
        return await self._client.request(
            "GET",
            f"{self._collection_path}/{_segment(field_id)}",
            response_model=wire.ComputedFieldDefinition,
        )

    async def create(self, payload: PersonalComputedFieldCreate) -> wire.ComputedFieldDefinition:
        return await self._client.request(
            "POST", self._collection_path, json=payload, response_model=wire.ComputedFieldDefinition
        )

    async def update(
        self,
        field_id: ComputedFieldId | int,
        payload: ComputedFieldUpdate,
        *,
        if_match: str | None = None,
    ) -> wire.ComputedFieldDefinition:
        return await self._client.request(
            "PATCH",
            f"{self._collection_path}/{_segment(field_id)}",
            json=payload,
            response_model=wire.ComputedFieldDefinition,
            options=_conditional_options(if_match),
        )

    async def delete(self, field_id: ComputedFieldId | int, *, if_match: str | None = None) -> None:
        await self._client.request(
            "DELETE",
            f"{self._collection_path}/{_segment(field_id)}",
            options=_conditional_options(if_match),
        )

    async def preview(
        self, payload: ComputedFieldPreviewRequest
    ) -> wire.ComputedFieldPreviewResponse:
        return await self._client.request(
            "POST",
            f"{self._collection_path}/preview",
            json=payload,
            response_model=wire.ComputedFieldPreviewResponse,
        )


class AsyncBackupsService:
    """Submit full backups and retrieve the exact backup document."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def submit(self, payload: BackupRequest | None = None) -> Task:
        return await self._client.request(
            "POST", "/api/v1/backups", json=payload or BackupRequest(), response_model=Task
        )

    async def get(self, task_id: TaskId | int) -> Task:
        return await self._client.request(
            "GET", f"/api/v1/backups/{_segment(task_id)}", response_model=Task
        )

    async def output(self, task_id: TaskId | int) -> wire.BackupDocument:
        return await self._client.request(
            "GET", f"/api/v1/backups/{_segment(task_id)}/output", response_model=wire.BackupDocument
        )

    async def run(
        self,
        payload: BackupRequest | None = None,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> wire.BackupDocument:
        _validate_polling(timeout_seconds, poll_interval)
        submitted = await self.submit(payload)
        task = await self._client.tasks.wait(
            submitted.id, timeout_seconds=timeout_seconds, poll_interval=poll_interval
        )
        if task.status is not TaskStatus.SUCCEEDED:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return await self.output(task.id)


class AsyncRestoresService:
    """Destructive restore staging, explicit approved confirmation, and capability polling."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def stage(self, backup: wire.BackupDocument) -> wire.RestoreStageResponse:
        return await self._client.request(
            "POST", "/api/v1/restores", json=backup, response_model=wire.RestoreStageResponse
        )

    async def confirm(
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
        return await self._client.request(
            "POST",
            f"/api/v1/restores/{_segment(restore_id)}/confirm",
            json=payload,
            response_model=wire.RestoreStageResponse,
            options=RequestOptions(headers={"X-Hubuum-Credential-Approval": approval}),
        )

    async def status(
        self, restore_id: RestoreJobId | int, *, capability: SecretStr | str
    ) -> wire.RestoreStageResponse:
        secret = capability.get_secret_value() if isinstance(capability, SecretStr) else capability
        return await self._client.request(
            "GET",
            f"/api/v1/restores/{_segment(restore_id)}/status",
            response_model=wire.RestoreStageResponse,
            options=RequestOptions(
                authenticated=False, headers={"X-Hubuum-Restore-Capability": secret}
            ),
        )

    async def wait(
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
            result = await self.status(restore_id, capability=capability)
            if result.status in {"succeeded", "failed", "expired"}:
                return result
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError("restore did not finish before the polling deadline")
            await asyncio.sleep(min(poll_interval, remaining))


def _conditional_options(if_match: str | None) -> RequestOptions:
    return RequestOptions(headers={"If-Match": if_match} if if_match is not None else None)


def _validate_polling(timeout_seconds: float, poll_interval: float) -> None:
    if not isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("timeout_seconds must be finite and non-negative")
    if not isfinite(poll_interval) or poll_interval <= 0:
        raise ValueError("poll_interval must be finite and greater than 0")


class AsyncSettingsService:
    """Principal settings with explicit JSON Patch/Merge Patch media and ETag controls."""

    def __init__(self, client: AsyncClient, path: str) -> None:
        self._client = client
        self._path = path

    async def get(self) -> wire.PrincipalSettingsResponse:
        return await self._client.request(
            "GET", self._path, response_model=wire.PrincipalSettingsResponse
        )

    async def replace(
        self, payload: SettingsRequest, *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        return await self._client.request(
            "PUT",
            self._path,
            json=payload.settings,
            response_model=wire.PrincipalSettingsResponse,
            options=_conditional_options(if_match),
        )

    async def merge_patch(
        self, payload: SettingsRequest, *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        headers = {"Content-Type": "application/merge-patch+json"}
        if if_match is not None:
            headers["If-Match"] = if_match
        return await self._client.request(
            "PATCH",
            self._path,
            json=payload.settings,
            response_model=wire.PrincipalSettingsResponse,
            options=RequestOptions(headers=headers),
        )

    async def json_patch(
        self, operations: Sequence[SettingsPatchOperation], *, if_match: str | None = None
    ) -> wire.PrincipalSettingsResponse:
        headers = {"Content-Type": "application/json-patch+json"}
        if if_match is not None:
            headers["If-Match"] = if_match
        return await self._client.request(
            "PATCH",
            self._path,
            json=[operation.payload() for operation in operations],
            response_model=wire.PrincipalSettingsResponse,
            options=RequestOptions(headers=headers),
        )

    async def delete(self, *, if_match: str | None = None) -> None:
        await self._client.request("DELETE", self._path, options=_conditional_options(if_match))


class AsyncPrincipalsService:
    """Current-principal or explicitly addressed settings, groups, and permissions."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    def settings(self, principal_id: PrincipalId | int | None = None) -> AsyncSettingsService:
        return AsyncSettingsService(self._client, f"{_principal_path(principal_id)}/settings")

    def groups(
        self, principal_id: PrincipalId | int | None = None
    ) -> _AsyncCursorService[wire.GroupResponse]:
        return _AsyncCursorService(
            self._client,
            collection_path=f"{_principal_path(principal_id)}/groups",
            model=wire.GroupResponse,
        )

    async def permissions(
        self, principal_id: PrincipalId | int | None = None
    ) -> builtins.list[wire.PrincipalCollectionPermissions]:
        return await _model_list(
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


class AsyncAuthService:
    """Provider discovery, validation, and explicit administrative revocation.

    Use Client.login_session()/logout() for managed client session state.
    Administrative revocation does not silently replace local credentials.
    """

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def providers(self) -> wire.AuthProvidersResponse:
        return await self._client.request(
            "GET",
            "/api/v1/auth/providers",
            response_model=wire.AuthProvidersResponse,
            options=RequestOptions(authenticated=False),
        )

    async def validate(self) -> wire.MessageResponse:
        return await self._client.request(
            "GET", "/api/v1/auth/validate", response_model=wire.MessageResponse
        )

    async def revoke_token(self, token: AccessToken | str) -> wire.MessageResponse:
        return await self._client.request(
            "POST",
            "/api/v1/auth/logout/token",
            json=wire.LogoutTokenRequest(
                token=SecretStr(token.value if isinstance(token, AccessToken) else token)
            ),
            response_model=wire.MessageResponse,
        )

    async def revoke_user(self, user_id: UserId | int) -> wire.MessageResponse:
        return await self._client.request(
            "POST",
            f"/api/v1/auth/logout/uid/{_segment(user_id)}",
            response_model=wire.MessageResponse,
        )

    async def revoke_all(self) -> wire.MessageResponse:
        return await self._client.request(
            "POST", "/api/v1/auth/logout_all", response_model=wire.MessageResponse
        )


class AsyncAdminService:
    """Running configuration and operational state; authorization remains server-enforced."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def config(self) -> wire.RunningConfig:
        return await self._client.request(
            "GET", "/api/v1/admin/config", response_model=wire.RunningConfig
        )

    async def counts(self) -> wire.CountsResponse:
        return await self._client.request(
            "GET", "/api/v0/meta/counts", response_model=wire.CountsResponse
        )

    async def database(self) -> wire.DbStateResponse:
        return await self._client.request(
            "GET", "/api/v0/meta/db", response_model=wire.DbStateResponse
        )

    async def tasks(self) -> wire.TaskQueueStateResponse:
        return await self._client.request(
            "GET", "/api/v0/meta/tasks", response_model=wire.TaskQueueStateResponse
        )

    async def rate_limits(
        self, *, include: str | None = None, scope: str | None = None, q: str | None = None
    ) -> wire.LoginRateLimitStateResponse:
        params = {
            key: value
            for (key, value) in (("include", include), ("scope", scope), ("q", q))
            if value is not None
        }
        return await self._client.request(
            "GET",
            "/api/v0/meta/login-rate-limit",
            response_model=wire.LoginRateLimitStateResponse,
            options=RequestOptions(params=params),
        )

    async def release_rate_limit(self, entry_id: str) -> wire.ReleaseRateLimitResponse:
        return await self._client.request(
            "DELETE",
            f"/api/v0/meta/login-rate-limit/{_segment(entry_id)}",
            response_model=wire.ReleaseRateLimitResponse,
        )

    async def clear_rate_limits(self) -> wire.ClearRateLimitResponse:
        return await self._client.request(
            "DELETE", "/api/v0/meta/login-rate-limit", response_model=wire.ClearRateLimitResponse
        )
