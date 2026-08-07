"""Typed asynchronous resource services."""

from __future__ import annotations

import asyncio
import builtins
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from math import isfinite
from time import monotonic
from typing import TYPE_CHECKING, Generic, TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from ._transport import (
    decode_content_type,
    decode_model,
    safe_response_url,
    validation_error_reason,
)
from .errors import DecodeError, ResultCardinalityError, TaskUnsuccessfulError
from .models import (
    ClassCreate,
    ClassRelation,
    ClassRelationCreate,
    ClassUpdate,
    Collection,
    CollectionCreate,
    CollectionUpdate,
    ExportContentType,
    ExportJsonResponse,
    ExportOutput,
    ExportRequest,
    Group,
    GroupCreate,
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
    PrincipalMember,
    PrincipalTokenMetadata,
    PrincipalTokenPoint,
    RenderedExport,
    RenewTokenRequest,
    Task,
    TaskEvent,
    TokenListState,
    User,
    UserCreate,
    UserUpdate,
    _object_data_patch_payload,
)
from .options import Params, RequestOptions
from .query import Page, Query
from .streaming import AsyncResponseStream
from .types import AccessToken, ClassId, CollectionId, GroupId, PrincipalId, TaskId, TokenId, UserId

if TYPE_CHECKING:
    from .async_client import AsyncClient

ModelT = TypeVar("ModelT", bound=BaseModel)
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
        items = _decode_model_list(response, self._model)
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


class AsyncResourceService(_AsyncCursorService[ModelT], Generic[ModelT, CreateT, UpdateT]):
    """Async counterpart to the synchronous typed CRUD service."""

    def __init__(
        self,
        client: AsyncClient,
        *,
        collection_path: str,
        item_path: str,
        model: type[ModelT],
    ) -> None:
        super().__init__(client, collection_path=collection_path, model=model)
        self._item_path = item_path

    async def get(self, resource_id: object) -> ModelT:
        """Return one resource by its path identifier."""
        return await self._client.request(
            "GET",
            self._item_path.format(id=_segment(resource_id)),
            response_model=self._model,
        )

    async def create(self, payload: CreateT) -> ModelT:
        """Create and return a resource from a strict request model."""
        return await self._client.request(
            "POST", self._collection_path, json=payload, response_model=self._model
        )

    async def update(self, resource_id: object, payload: UpdateT) -> ModelT:
        """Patch and return one resource by its path identifier."""
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=self._model,
        )

    async def delete(self, resource_id: object) -> None:
        """Delete one resource by its path identifier."""
        await self._client.request("DELETE", self._item_path.format(id=_segment(resource_id)))


class AsyncCollectionsService(AsyncResourceService[Collection, CollectionCreate, CollectionUpdate]):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/collections",
            item_path="/api/v1/collections/{id}",
            model=Collection,
        )

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


class AsyncClassesService(AsyncResourceService[HubuumClass, ClassCreate, ClassUpdate]):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/classes",
            item_path="/api/v1/classes/{id}",
            model=HubuumClass,
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


class AsyncObjectsService(AsyncResourceService[HubuumObject, ObjectCreate, ObjectUpdate]):
    def __init__(self, client: AsyncClient, class_id: ClassId) -> None:
        self.class_id = class_id
        base = f"/api/v1/classes/{_segment(class_id)}"
        super().__init__(
            client,
            collection_path=f"{base}/",
            item_path=f"{base}/{{id}}",
            model=HubuumObject,
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
        self._service = AsyncResourceService[HubuumObject, ObjectCreate, ObjectUpdate](
            client,
            collection_path=base,
            item_path=f"{base}/by-name/{{id}}",
            model=HubuumObject,
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

    async def permissions(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return await _json_object_list(self._client, f"{self._base}/permissions", params=params)

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


class AsyncUsersService(AsyncResourceService[User, UserCreate, UserUpdate]):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/users",
            item_path="/api/v1/iam/users/{id}",
            model=User,
        )

    async def get_by_name(self, name: str) -> User:
        return await self.one(Query().where("name", name))

    async def anonymize(self, user_id: UserId | int) -> None:
        await self._client.request("POST", f"/api/v1/iam/users/{_segment(user_id)}/anonymize")


class AsyncGroupsService(AsyncResourceService[Group, GroupCreate, GroupUpdate]):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/groups",
            item_path="/api/v1/iam/groups/{id}",
            model=Group,
        )

    async def get_by_name(self, name: str) -> Group:
        return await self.one(Query().where("groupname", name))

    def _members_service(
        self, group_id: GroupId | int
    ) -> AsyncResourceService[PrincipalMember, BaseModel, BaseModel]:
        path = f"/api/v1/iam/groups/{_segment(group_id)}/members"
        return AsyncResourceService(
            self._client,
            collection_path=path,
            item_path=f"{path}/{{id}}",
            model=PrincipalMember,
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


class AsyncTokensService:
    """Async token metadata visible to the current human user."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    def _service(self, state: TokenListState) -> _AsyncCursorService[PrincipalTokenMetadata]:
        return _AsyncCursorService(
            self._client,
            collection_path="/api/v1/iam/me/tokens",
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

    def for_principal(self, principal_id: PrincipalId | int) -> AsyncPrincipalTokensService:
        return AsyncPrincipalTokensService(self._client, PrincipalId(principal_id))


class AsyncPrincipalTokensService:
    """Async list, inspect, mint, renew, and revoke operations for one principal."""

    def __init__(self, client: AsyncClient, principal_id: PrincipalId) -> None:
        self._client = client
        self.principal_id = principal_id
        self._base = f"/api/v1/iam/principals/{_segment(principal_id)}/tokens"

    def _service(self, state: TokenListState) -> _AsyncCursorService[PrincipalTokenMetadata]:
        return _AsyncCursorService(
            self._client,
            collection_path=self._base,
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

    async def get(self, token_id: TokenId | int) -> PrincipalTokenPoint:
        return await self._client.request(
            "GET",
            f"{self._base}/{_segment(token_id)}",
            response_model=PrincipalTokenPoint,
        )

    async def create(self, payload: NewTokenRequest) -> AccessToken:
        response = await self._client.request(
            "POST",
            self._base,
            json=payload,
            response_model=LoginResponse,
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
    ) -> AccessToken:
        response = await self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/renew",
            json=payload or RenewTokenRequest(),
            response_model=LoginResponse,
        )
        return AccessToken(response.token, expires_at=response.expires_at)


class AsyncClassRelationsService:
    def __init__(self, client: AsyncClient) -> None:
        self._service = AsyncResourceService[ClassRelation, ClassRelationCreate, BaseModel](
            client,
            collection_path="/api/v1/relations/classes",
            item_path="/api/v1/relations/classes/{id}",
            model=ClassRelation,
        )

    async def list(self, query: Query | None = None) -> builtins.list[ClassRelation]:
        return await self._service.list(query)

    async def one(self, query: Query) -> ClassRelation:
        return await self._service.one(query)

    async def get(self, relation_id: int) -> ClassRelation:
        return await self._service.get(relation_id)

    async def create(self, payload: ClassRelationCreate) -> ClassRelation:
        return await self._service.create(payload)

    async def delete(self, relation_id: int) -> None:
        await self._service.delete(relation_id)


class AsyncObjectRelationsService:
    def __init__(self, client: AsyncClient) -> None:
        self._service = AsyncResourceService[ObjectRelation, ObjectRelationCreate, BaseModel](
            client,
            collection_path="/api/v1/relations/objects",
            item_path="/api/v1/relations/objects/{id}",
            model=ObjectRelation,
        )

    async def list(self, query: Query | None = None) -> builtins.list[ObjectRelation]:
        return await self._service.list(query)

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

    async def submit(self, payload: ImportRequest, *, idempotency_key: str | None = None) -> Task:
        """Submit an import task, optionally with a replay-safe idempotency key."""
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
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

    async def run(
        self,
        payload: ImportRequest,
        *,
        idempotency_key: str | None = None,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> ImportRunResult:
        """Submit, await, and collect all outcomes for one import task."""
        submitted = await self.submit(payload, idempotency_key=idempotency_key)
        task = await self._client.tasks.wait(
            submitted.id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        if not task.status.successful:
            raise TaskUnsuccessfulError(int(task.id), task.status.value)
        return ImportRunResult(
            task=task,
            results=tuple(await self.all_results(task.id)),
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
    return _decode_model_list(response, model)


def _decode_model_list(response: httpx.Response, model: type[ModelT]) -> builtins.list[ModelT]:
    try:
        value = response.json()
        if not isinstance(value, builtins.list):
            raise TypeError("expected a JSON array")
        return [model.model_validate(item) for item in value]
    except (TypeError, ValueError, ValidationError) as error:
        raise DecodeError(
            response.request.method,
            safe_response_url(response),
            response.status_code,
            validation_error_reason(error, response),
        ) from error


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
    value = await client.request("GET", path, options=RequestOptions(params=params))
    if not isinstance(value, dict):
        raise TypeError("expected a JSON object")
    return value


async def _json_object_list(
    client: AsyncClient,
    path: str,
    *,
    params: Params = None,
) -> builtins.list[dict[str, object]]:
    value = await client.request("GET", path, options=RequestOptions(params=params))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise TypeError("expected a JSON array of objects")
    return value


async def _model_page(
    client: AsyncClient,
    path: str,
    model: type[ModelT],
    *,
    params: Params,
) -> Page[ModelT]:
    response = await client._request_response("GET", path, options=RequestOptions(params=params))
    value = _decode_model_list(response, model)
    return Page(
        items=tuple(value),
        next_cursor=response.headers.get("x-next-cursor"),
        total_count=_header_int(response.headers.get("x-total-count")),
        page_limit=_header_int(response.headers.get("x-page-limit")),
    )
