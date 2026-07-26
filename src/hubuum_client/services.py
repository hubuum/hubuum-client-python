"""Typed synchronous resource services."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from math import isfinite
from time import monotonic, sleep
from typing import TYPE_CHECKING, Generic, TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from ._transport import safe_response_url, validation_error_reason
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
    Task,
    User,
    UserCreate,
    UserUpdate,
    _object_data_patch_payload,
)
from .options import Params, RequestOptions
from .query import Page, Query
from .types import AccessToken, ClassId, CollectionId, GroupId, PrincipalId, TaskId, TokenId, UserId

if TYPE_CHECKING:
    from .client import Client

ModelT = TypeVar("ModelT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def _segment(value: object) -> str:
    return quote(str(value), safe="")


class ResourceService(Generic[ModelT, CreateT, UpdateT]):
    """Shared typed CRUD and cursor pagination behavior."""

    def __init__(
        self,
        client: Client,
        *,
        collection_path: str,
        item_path: str,
        model: type[ModelT],
    ) -> None:
        self._client = client
        self._collection_path = collection_path
        self._item_path = item_path
        self._model = model

    def page(self, query: Query | None = None) -> Page[ModelT]:
        response = self._client._request_response(
            "GET",
            self._collection_path,
            options=RequestOptions(params=(query or Query()).as_params()),
        )
        items = _decode_model_list(response, self._model)
        return Page(
            items=tuple(items),
            next_cursor=response.headers.get("x-next-cursor"),
            total_count=_header_int(response.headers.get("x-total-count")),
            page_limit=_header_int(response.headers.get("x-page-limit")),
        )

    def list(self, query: Query | None = None) -> builtins.list[ModelT]:
        return builtins.list(self.page(query))

    def pages(self, query: Query | None = None, *, max_pages: int = 100) -> Iterator[Page[ModelT]]:
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
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        items: builtins.list[ModelT] = []
        for page in self.pages(query, max_pages=max_pages):
            if len(page) > max_items - len(items):
                raise RuntimeError(f"pagination exceeded max_items={max_items}")
            items.extend(page)
        return items

    def one(self, query: Query) -> ModelT:
        items = self.list(query.limit(2))
        if len(items) != 1:
            raise ResultCardinalityError(f"expected exactly one result, received {len(items)}")
        return items[0]

    def get(self, resource_id: object) -> ModelT:
        return self._client.request(
            "GET",
            self._item_path.format(id=_segment(resource_id)),
            response_model=self._model,
        )

    def create(self, payload: CreateT) -> ModelT:
        return self._client.request(
            "POST", self._collection_path, json=payload, response_model=self._model
        )

    def update(self, resource_id: object, payload: UpdateT) -> ModelT:
        return self._client.request(
            "PATCH",
            self._item_path.format(id=_segment(resource_id)),
            json=payload,
            response_model=self._model,
        )

    def delete(self, resource_id: object) -> None:
        self._client.request("DELETE", self._item_path.format(id=_segment(resource_id)))


def _header_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class CollectionsService(ResourceService[Collection, CollectionCreate, CollectionUpdate]):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/collections",
            item_path="/api/v1/collections/{id}",
            model=Collection,
        )

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


class ClassesService(ResourceService[HubuumClass, ClassCreate, ClassUpdate]):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/classes",
            item_path="/api/v1/classes/{id}",
            model=HubuumClass,
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


class ObjectsService(ResourceService[HubuumObject, ObjectCreate, ObjectUpdate]):
    def __init__(self, client: Client, class_id: ClassId) -> None:
        self.class_id = class_id
        base = f"/api/v1/classes/{_segment(class_id)}"
        super().__init__(
            client,
            collection_path=f"{base}/",
            item_path=f"{base}/{{id}}",
            model=HubuumObject,
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
        self._service = ResourceService[HubuumObject, ObjectCreate, ObjectUpdate](
            client,
            collection_path=base,
            item_path=f"{base}/by-name/{{id}}",
            model=HubuumObject,
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

    @property
    def objects(self) -> NamedObjectsService:
        return NamedObjectsService(self._client, self.class_name)

    def get(self) -> HubuumClass:
        return self._client.request("GET", self._base, response_model=HubuumClass)

    def update(self, payload: ClassUpdate) -> HubuumClass:
        return self._client.request("PATCH", self._base, json=payload, response_model=HubuumClass)

    def delete(self) -> None:
        self._client.request("DELETE", self._base)

    def permissions(self, *, params: Params = None) -> builtins.list[dict[str, object]]:
        return _json_object_list(self._client, f"{self._base}/permissions", params=params)

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


class UsersService(ResourceService[User, UserCreate, UserUpdate]):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/users",
            item_path="/api/v1/iam/users/{id}",
            model=User,
        )

    def get_by_name(self, name: str) -> User:
        return self.one(Query().where("name", name))

    def anonymize(self, user_id: UserId | int) -> None:
        self._client.request("POST", f"/api/v1/iam/users/{_segment(user_id)}/anonymize")


class GroupsService(ResourceService[Group, GroupCreate, GroupUpdate]):
    def __init__(self, client: Client) -> None:
        super().__init__(
            client,
            collection_path="/api/v1/iam/groups",
            item_path="/api/v1/iam/groups/{id}",
            model=Group,
        )

    def get_by_name(self, name: str) -> Group:
        return self.one(Query().where("groupname", name))

    def _members_service(
        self, group_id: GroupId | int
    ) -> ResourceService[PrincipalMember, BaseModel, BaseModel]:
        path = f"/api/v1/iam/groups/{_segment(group_id)}/members"
        return ResourceService(
            self._client,
            collection_path=path,
            item_path=f"{path}/{{id}}",
            model=PrincipalMember,
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

    def add_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        self._client.request(
            "POST",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )

    def remove_member(self, group_id: GroupId | int, principal_id: PrincipalId | int) -> None:
        self._client.request(
            "DELETE",
            f"/api/v1/iam/groups/{_segment(group_id)}/members/{_segment(principal_id)}",
        )


class TokensService:
    """Token metadata visible to the current human user."""

    def __init__(self, client: Client) -> None:
        self._service = ResourceService[PrincipalTokenMetadata, BaseModel, BaseModel](
            client,
            collection_path="/api/v1/iam/me/tokens",
            item_path="/api/v1/iam/me/tokens/{id}",
            model=PrincipalTokenMetadata,
        )
        self._client = client

    def page(self, query: Query | None = None) -> Page[PrincipalTokenMetadata]:
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[PrincipalTokenMetadata]:
        return self._service.list(query)

    def pages(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[PrincipalTokenMetadata]]:
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def for_principal(self, principal_id: PrincipalId | int) -> PrincipalTokensService:
        return PrincipalTokensService(self._client, PrincipalId(principal_id))


class PrincipalTokensService:
    """List, mint, and revoke tokens for one principal."""

    def __init__(self, client: Client, principal_id: PrincipalId) -> None:
        self._client = client
        self.principal_id = principal_id
        self._base = f"/api/v1/iam/principals/{_segment(principal_id)}/tokens"
        self._service = ResourceService[PrincipalTokenMetadata, NewTokenRequest, BaseModel](
            client,
            collection_path=self._base,
            item_path=f"{self._base}/{{id}}",
            model=PrincipalTokenMetadata,
        )

    def page(self, query: Query | None = None) -> Page[PrincipalTokenMetadata]:
        return self._service.page(query)

    def list(self, query: Query | None = None) -> builtins.list[PrincipalTokenMetadata]:
        return self._service.list(query)

    def pages(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
    ) -> Iterator[Page[PrincipalTokenMetadata]]:
        return self._service.pages(query, max_pages=max_pages)

    def all(
        self,
        query: Query | None = None,
        *,
        max_pages: int = 100,
        max_items: int = 10_000,
    ) -> builtins.list[PrincipalTokenMetadata]:
        return self._service.all(query, max_pages=max_pages, max_items=max_items)

    def create(self, payload: NewTokenRequest) -> AccessToken:
        response = self._client.request(
            "POST",
            self._base,
            json=payload,
            response_model=LoginResponse,
        )
        return AccessToken(response.token)

    def revoke(self, token_id: TokenId | int) -> None:
        self._client.request(
            "POST",
            f"{self._base}/{_segment(token_id)}/revoke",
        )


class ClassRelationsService:
    def __init__(self, client: Client) -> None:
        self._service = ResourceService[ClassRelation, ClassRelationCreate, BaseModel](
            client,
            collection_path="/api/v1/relations/classes",
            item_path="/api/v1/relations/classes/{id}",
            model=ClassRelation,
        )

    def list(self, query: Query | None = None) -> builtins.list[ClassRelation]:
        return self._service.list(query)

    def one(self, query: Query) -> ClassRelation:
        return self._service.one(query)

    def get(self, relation_id: int) -> ClassRelation:
        return self._service.get(relation_id)

    def create(self, payload: ClassRelationCreate) -> ClassRelation:
        return self._service.create(payload)

    def delete(self, relation_id: int) -> None:
        self._service.delete(relation_id)


class ObjectRelationsService:
    def __init__(self, client: Client) -> None:
        self._service = ResourceService[ObjectRelation, ObjectRelationCreate, BaseModel](
            client,
            collection_path="/api/v1/relations/objects",
            item_path="/api/v1/relations/objects/{id}",
            model=ObjectRelation,
        )

    def list(self, query: Query | None = None) -> builtins.list[ObjectRelation]:
        return self._service.list(query)

    def one(self, query: Query) -> ObjectRelation:
        return self._service.one(query)

    def get(self, relation_id: int) -> ObjectRelation:
        return self._service.get(relation_id)

    def create(self, payload: ObjectRelationCreate) -> ObjectRelation:
        return self._service.create(payload)

    def delete(self, relation_id: int) -> None:
        self._service.delete(relation_id)


class TasksService:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._service = ResourceService[Task, BaseModel, BaseModel](
            client,
            collection_path="/api/v1/tasks",
            item_path="/api/v1/tasks/{id}",
            model=Task,
        )

    def list(self, query: Query | None = None) -> builtins.list[Task]:
        return self._service.list(query)

    def get(self, task_id: TaskId | int) -> Task:
        return self._service.get(task_id)

    def wait(
        self,
        task_id: TaskId | int,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 0.5,
    ) -> Task:
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


def _model_list(client: Client, path: str, model: type[ModelT]) -> builtins.list[ModelT]:
    response = client._request_response("GET", path)
    return _decode_model_list(response, model)


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
    value = client.request("GET", path, options=RequestOptions(params=params))
    if not isinstance(value, dict):
        raise TypeError("expected a JSON object")
    return value


def _json_object_list(
    client: Client,
    path: str,
    *,
    params: Params = None,
) -> builtins.list[dict[str, object]]:
    value = client.request("GET", path, options=RequestOptions(params=params))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise TypeError("expected a JSON array of objects")
    return value


def _model_page(
    client: Client,
    path: str,
    model: type[ModelT],
    *,
    params: Params,
) -> Page[ModelT]:
    response = client._request_response("GET", path, options=RequestOptions(params=params))
    value = _decode_model_list(response, model)
    return Page(
        items=tuple(value),
        next_cursor=response.headers.get("x-next-cursor"),
        total_count=_header_int(response.headers.get("x-total-count")),
        page_limit=_header_int(response.headers.get("x-page-limit")),
    )
