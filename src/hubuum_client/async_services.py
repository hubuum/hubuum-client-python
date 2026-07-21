"""Typed asynchronous resource services."""

from __future__ import annotations

import asyncio
import builtins
from collections.abc import AsyncIterator
from time import monotonic
from typing import TYPE_CHECKING, Generic, TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from ._transport import safe_response_url
from .errors import DecodeError, ResultCardinalityError
from .models import (
    ClassCreate,
    ClassRelation,
    ClassRelationCreate,
    ClassUpdate,
    Collection,
    CollectionCreate,
    CollectionUpdate,
    Group,
    GroupCreate,
    GroupUpdate,
    HubuumClass,
    HubuumObject,
    ObjectCreate,
    ObjectRelation,
    ObjectRelationCreate,
    ObjectUpdate,
    Task,
    User,
    UserCreate,
    UserUpdate,
)
from .query import Page, Query
from .types import ClassId, CollectionId, GroupId, PrincipalId, TaskId, UserId

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


class AsyncResourceService(Generic[ModelT, CreateT, UpdateT]):
    """Async counterpart to the synchronous typed CRUD service."""

    def __init__(
        self,
        client: AsyncClient,
        *,
        collection_path: str,
        item_path: str,
        model: type[ModelT],
    ) -> None:
        self._client = client
        self._collection_path = collection_path
        self._item_path = item_path
        self._model = model

    async def page(self, query: Query | None = None) -> Page[ModelT]:
        response = await self._client._request_response(
            "GET", self._collection_path, params=(query or Query()).as_params()
        )
        items = _decode_model_list(response, self._model)
        return Page(
            items=tuple(items),
            next_cursor=response.headers.get("x-next-cursor"),
            total_count=_header_int(response.headers.get("x-total-count")),
            page_limit=_header_int(response.headers.get("x-page-limit")),
        )

    async def list(self, query: Query | None = None) -> builtins.list[ModelT]:
        return builtins.list(await self.page(query))

    async def pages(
        self, query: Query | None = None, *, max_pages: int = 100
    ) -> AsyncIterator[Page[ModelT]]:
        current = query or Query()
        seen: set[str] = set()
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
        items: builtins.list[ModelT] = []
        async for page in self.pages(query, max_pages=max_pages):
            items.extend(page)
            if len(items) > max_items:
                raise RuntimeError(f"pagination exceeded max_items={max_items}")
        return items

    async def one(self, query: Query) -> ModelT:
        items = await self.list(query.limit(2))
        if len(items) != 1:
            raise ResultCardinalityError(f"expected exactly one result, received {len(items)}")
        return items[0]

    async def get(self, resource_id: object) -> ModelT:
        return await self._client.request(
            "GET",
            self._item_path.format(id=_segment(resource_id)),
            response_model=self._model,
        )

    async def create(self, payload: CreateT) -> ModelT:
        return await self._client.request(
            "POST", self._collection_path, json=payload, response_model=self._model
        )

    async def update(self, resource_id: object, payload: UpdateT) -> ModelT:
        return await self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=self._model,
        )

    async def delete(self, resource_id: object) -> None:
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

    async def members(self, group_id: GroupId | int) -> list[dict[str, object]]:
        value = await self._client.request(
            "GET", f"/api/v1/iam/groups/{_segment(group_id)}/members"
        )
        return value if isinstance(value, list) else []

    async def add_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        await self._client.request(
            "POST",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )

    async def remove_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        await self._client.request(
            "DELETE",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )


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
    def __init__(self, client: AsyncClient) -> None:
        self._service = AsyncResourceService[Task, BaseModel, BaseModel](
            client,
            collection_path="/api/v1/tasks",
            item_path="/api/v1/tasks/{id}",
            model=Task,
        )

    async def list(self, query: Query | None = None) -> builtins.list[Task]:
        return await self._service.list(query)

    async def get(self, task_id: TaskId | int) -> Task:
        return await self._service.get(task_id)

    async def wait(
        self,
        task_id: TaskId | int,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> Task:
        deadline = monotonic() + timeout_seconds
        while True:
            task = await self.get(task_id)
            if task.status.terminal:
                return task
            if monotonic() >= deadline:
                raise TimeoutError(
                    f"task {task_id} did not finish within {timeout_seconds} seconds"
                )
            await asyncio.sleep(poll_interval)


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
            str(error),
        ) from error
