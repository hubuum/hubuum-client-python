from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

import hubuum_client.async_services as async_services_module
import hubuum_client.services as services_module
from hubuum_client import (
    AsyncClient,
    ClassId,
    ClassRelationCreate,
    ClassRelationId,
    ClassUpdate,
    Client,
    CollectionId,
    CollectionUpdate,
    DecodeError,
    ExportContentType,
    ExportJsonResponse,
    ExportRequest,
    ExportScope,
    ExportScopeKind,
    GroupCreate,
    GroupId,
    GroupUpdate,
    ImportGraph,
    ImportRequest,
    NewTokenRequest,
    ObjectCreate,
    ObjectId,
    ObjectRelationCreate,
    ObjectRelationId,
    ObjectUpdate,
    Permission,
    PrincipalId,
    PrincipalMember,
    Query,
    RenderedExport,
    RequestOptions,
    ResultCardinalityError,
    TaskId,
    TokenId,
    TokenResourceKind,
    TokenResourceScope,
    TokenScope,
    UserCreate,
    UserId,
    UserUpdate,
)
from hubuum_client.async_services import (
    AsyncClassesService,
    AsyncClassRelationsService,
    AsyncClassService,
    AsyncCollectionsService,
    AsyncExportsService,
    AsyncGroupsService,
    AsyncImportsService,
    AsyncObjectRelationsService,
    AsyncObjectsService,
    AsyncPrincipalTokensService,
    AsyncResourceService,
    AsyncTasksService,
    AsyncTokensService,
    AsyncUsersService,
)
from hubuum_client.models import Group, User
from hubuum_client.services import (
    ClassesService,
    ClassRelationsService,
    ClassService,
    CollectionsService,
    ExportsService,
    GroupsService,
    ImportsService,
    ObjectRelationsService,
    ObjectsService,
    PrincipalTokensService,
    ResourceService,
    TasksService,
    TokensService,
    UsersService,
)


def _group_json() -> dict[str, Any]:
    return {
        "id": 20,
        "groupname": "ops",
        "description": "Operations",
        "identity_scope": "local",
        "managed_by": "local",
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
    }


def _user_json() -> dict[str, Any]:
    return {
        "id": 21,
        "identity_scope": "local",
        "provider_kind": "local",
        "provider_managed": False,
        "name": "alice",
        "email": "alice@example.com",
        "proper_name": "Alice",
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
    }


def _principal_member_json() -> dict[str, Any]:
    return {
        "principal_id": 21,
        "identity_scope": "local",
        "kind": "user",
        "name": "alice",
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
    }


def _class_relation_json() -> dict[str, Any]:
    return {
        "id": 30,
        "from_hubuum_class_id": 12,
        "to_hubuum_class_id": 14,
        "forward_template_alias": "hosts",
        "reverse_template_alias": "room",
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
    }


def _object_relation_json() -> dict[str, Any]:
    return {
        "id": 31,
        "from_hubuum_object_id": 13,
        "to_hubuum_object_id": 15,
        "class_relation_id": 30,
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
    }


def _task_json(status: str = "succeeded") -> dict[str, Any]:
    return {
        "id": 40,
        "kind": "import",
        "status": status,
        "created_at": "2026-07-21T10:00:00Z",
        "progress": {
            "total_items": 1,
            "processed_items": 1,
            "success_items": 1 if status == "succeeded" else 0,
            "failed_items": 1 if status == "failed" else 0,
        },
        "links": {
            "task": "/api/v1/tasks/40",
            "events": "/api/v1/tasks/40/events",
            "import": "/api/v1/imports/40",
            "import_results": "/api/v1/imports/40/results",
        },
    }


def _token_metadata_json() -> dict[str, Any]:
    return {
        "id": 50,
        "principal_id": 21,
        "issued": "2026-07-25T10:00:00Z",
        "name": "inventory-reader",
        "scope": {
            "permissions": ["ReadCollection"],
            "resources": [{"kind": "collection", "id": 11}],
        },
    }


def test_sync_and_async_services_keep_public_method_parity() -> None:
    pairs = [
        (ResourceService, AsyncResourceService),
        (CollectionsService, AsyncCollectionsService),
        (ClassesService, AsyncClassesService),
        (ClassService, AsyncClassService),
        (ObjectsService, AsyncObjectsService),
        (UsersService, AsyncUsersService),
        (GroupsService, AsyncGroupsService),
        (TokensService, AsyncTokensService),
        (PrincipalTokensService, AsyncPrincipalTokensService),
        (ClassRelationsService, AsyncClassRelationsService),
        (ObjectRelationsService, AsyncObjectRelationsService),
        (TasksService, AsyncTasksService),
        (ImportsService, AsyncImportsService),
        (ExportsService, AsyncExportsService),
    ]

    for sync_service, async_service in pairs:
        sync_methods = {
            name
            for name, value in sync_service.__dict__.items()
            if not name.startswith("_") and callable(value)
        }
        async_methods = {
            name
            for name, value in async_service.__dict__.items()
            if not name.startswith("_") and callable(value)
        }
        assert sync_methods == async_methods


def test_sync_v005_token_service_uses_nested_scope_and_returns_authoritative_expiry() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/iam/me":
            token = _token_metadata_json()
            token.pop("principal_id")
            return httpx.Response(
                200,
                json={"principal": _principal_member_json(), "token": token},
            )
        if request.method == "GET":
            return httpx.Response(
                200,
                json=[_token_metadata_json()],
                headers={"X-Total-Count": "1", "X-Page-Limit": "25"},
            )
        if request.url.path.endswith("/revoke"):
            return httpx.Response(204)
        return httpx.Response(
            201,
            json={
                "token": "minted-token-secret",
                "expires_at": "2026-07-27T12:00:00Z",
            },
        )

    payload = NewTokenRequest(
        name="inventory-reader",
        scope=TokenScope(
            permissions=(Permission.READ_COLLECTION,),
            resources=(TokenResourceScope(kind=TokenResourceKind.COLLECTION, id=11),),
        ),
    )
    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        assert client.me().token.scope is not None
        current = client.tokens
        assert current.page(Query().limit(25)).items[0].id == TokenId(50)
        assert current.list()[0].scope is not None
        assert len(list(current.pages())) == 1
        assert current.all()[0].principal_id == PrincipalId(21)

        principal = current.for_principal(PrincipalId(21))
        assert principal.principal_id == PrincipalId(21)
        assert principal.page().total_count == 1
        assert principal.list()[0].id == TokenId(50)
        assert len(list(principal.pages())) == 1
        assert principal.all()[0].name == "inventory-reader"
        created = principal.create(payload)
        principal.revoke(TokenId(50))

    assert created.value == "minted-token-secret"
    assert created.expires_at == datetime(2026, 7, 27, 12, tzinfo=UTC)
    assert "minted-token-secret" not in repr(created)
    create_request = next(
        request
        for request in requests
        if request.method == "POST" and not request.url.path.endswith("/revoke")
    )
    assert json.loads(create_request.content) == {
        "name": "inventory-reader",
        "scope": {
            "permissions": ["ReadCollection"],
            "resources": [{"kind": "collection", "id": 11}],
        },
    }
    assert requests[-1].url.path == "/api/v1/iam/principals/21/tokens/50/revoke"


async def test_async_v005_token_service_matches_sync_behavior() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/iam/me":
            token = _token_metadata_json()
            token.pop("principal_id")
            return httpx.Response(
                200,
                json={"principal": _principal_member_json(), "token": token},
            )
        if request.method == "GET":
            return httpx.Response(200, json=[_token_metadata_json()])
        if request.url.path.endswith("/revoke"):
            return httpx.Response(204)
        return httpx.Response(
            201,
            json={
                "token": "async-minted-secret",
                "expires_at": "2026-07-27T13:00:00Z",
            },
        )

    payload = NewTokenRequest(scope=TokenScope(permissions=(Permission.READ_OBJECT,)))
    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        assert (await client.me()).token.scope is not None
        current = client.tokens
        assert (await current.page()).items[0].id == TokenId(50)
        assert (await current.list())[0].principal_id == PrincipalId(21)
        assert len([page async for page in current.pages()]) == 1
        assert (await current.all())[0].scope is not None

        principal = current.for_principal(21)
        assert (await principal.page()).items[0].id == TokenId(50)
        assert (await principal.list())[0].name == "inventory-reader"
        assert len([page async for page in principal.pages()]) == 1
        assert (await principal.all())[0].scope is not None
        created = await principal.create(payload)
        await principal.revoke(50)

    assert created.value == "async-minted-secret"
    assert created.expires_at == datetime(2026, 7, 27, 13, tzinfo=UTC)
    assert json.loads(requests[-2].content) == {
        "scope": {"permissions": ["ReadObject"]},
    }
    assert requests[-1].url.path == "/api/v1/iam/principals/21/tokens/50/revoke"


def test_sync_collection_and_class_specific_methods(
    collection_json: dict[str, Any], class_json: dict[str, Any]
) -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if "/collections/" in request.url.path:
            if request.method == "GET" and request.url.path.endswith(("/children", "/ancestors")):
                return httpx.Response(200, json=[collection_json])
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(200, json=collection_json)
        if "/classes/by-name/" in request.url.path:
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(200, json=class_json)
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json=collection_json)

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        assert client.collections.get(11).id == CollectionId(11)
        assert client.collections.update(11, CollectionUpdate(name="renamed")).name == "inventory"
        assert client.collections.children(11)[0].id == CollectionId(11)
        assert client.collections.ancestors(11)[0].id == CollectionId(11)
        assert client.collections.move(11, None).id == CollectionId(11)
        client.collections.delete(11)
        assert client.classes.update_by_name(
            "server", ClassUpdate(description="new")
        ).id == ClassId(12)
        client.classes.delete_by_name("server")

    assert ("PUT", "/api/v1/collections/11/parent") in seen
    assert ("PATCH", "/api/v1/classes/by-name/server") in seen


def test_sync_object_user_and_group_methods(object_json: dict[str, Any]) -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        path = request.url.path
        if path.startswith("/api/v1/classes/"):
            if request.method == "DELETE":
                return httpx.Response(204)
            if request.method == "GET" and path.endswith("/12/"):
                return httpx.Response(200, json=[object_json])
            return httpx.Response(200, json=object_json)
        if "/iam/users" in path:
            if request.method in {"DELETE", "POST"} and path != "/api/v1/iam/users":
                return httpx.Response(204)
            if request.method == "GET" and path == "/api/v1/iam/users":
                return httpx.Response(200, json=[_user_json()])
            return httpx.Response(200, json=_user_json())
        if path.endswith("/members"):
            return httpx.Response(
                200,
                headers={"x-total-count": "1", "x-page-limit": "25"},
                json=[_principal_member_json()],
            )
        if "/members/" in path:
            return httpx.Response(204)
        if request.method == "GET" and path == "/api/v1/iam/groups":
            return httpx.Response(200, json=[_group_json()])
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json=_group_json())

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        objects = client.classes.by_id(12).objects
        assert objects.create(ObjectCreate(name="web", data={}, description="Web")).id == ObjectId(
            13
        )
        assert objects.update(13, ObjectUpdate(description="Updated")).id == ObjectId(13)
        assert objects.update_by_name("web", ObjectUpdate(name="web-2")).id == ObjectId(13)
        assert objects.patch_data(
            13,
            [{"op": "add", "path": "/verified", "value": True}],
        ).id == ObjectId(13)
        assert objects.list()[0].id == ObjectId(13)
        objects.delete(13)
        objects.delete_by_name("web")

        assert client.users.create(UserCreate(name="alice", password="secret")).id == UserId(21)
        assert client.users.get(21).name == "alice"
        assert client.users.get_by_name("alice").id == UserId(21)
        assert client.users.update(21, UserUpdate(proper_name="Alice A.")).id == UserId(21)
        client.users.anonymize(21)
        client.users.delete(21)

        assert client.groups.create(GroupCreate(groupname="ops")).id == GroupId(20)
        assert client.groups.get(20).groupname == "ops"
        assert client.groups.get_by_name("ops").id == GroupId(20)
        assert client.groups.update(20, GroupUpdate(groupname="platform")).id == GroupId(20)
        member: PrincipalMember = client.groups.members(20)[0]
        assert member.principal_id == PrincipalId(21)
        page = client.groups.members_page(20, Query().limit(25).include_total())
        assert page.items == (member,)
        assert page.total_count == 1
        assert page.page_limit == 25
        assert [item for page in client.groups.member_pages(20) for item in page] == [member]
        assert client.groups.all_members(20) == [member]
        client.groups.add_member(20, PrincipalId(21))
        client.groups.remove_member(20, PrincipalId(21))
        client.groups.delete(20)

    assert ("PATCH", "/api/v1/classes/12/13") in seen
    assert ("POST", "/api/v1/iam/groups/20/members/21") in seen


def test_sync_group_members_reject_non_array_response() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    with (
        Client("https://hubuum.test", token="token", transport=transport) as client,
        pytest.raises(DecodeError, match="expected a JSON array"),
    ):
        client.groups.members(20)


def test_sync_relations_tasks_probes_and_service_properties() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in {"/healthz", "/readyz"}:
            return httpx.Response(200, json={"status": "ok"})
        if path == "/api/v1/config":
            return httpx.Response(
                200,
                json={
                    "authentication": {"default_token_lifetime_hours": 48},
                    "pagination": {"default_page_limit": 100, "max_page_limit": 250},
                },
            )
        if "/relations/classes" in path:
            if request.method == "DELETE":
                return httpx.Response(204)
            body: Any = (
                [_class_relation_json()]
                if path.endswith("/classes") and request.method == "GET"
                else _class_relation_json()
            )
            return httpx.Response(200, json=body)
        if "/relations/objects" in path:
            if request.method == "DELETE":
                return httpx.Response(204)
            body = (
                [_object_relation_json()]
                if path.endswith("/objects") and request.method == "GET"
                else _object_relation_json()
            )
            return httpx.Response(200, json=body)
        if path == "/api/v1/tasks":
            return httpx.Response(200, json=[_task_json()])
        return httpx.Response(200, json=_task_json())

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        assert client.healthz().status == "ok"
        assert client.readyz().status == "ok"
        assert client.config().authentication.default_token_lifetime_hours == 48

        assert client.class_relations.list()[0].id == ClassRelationId(30)
        assert client.class_relations.one(Query().where("id", 30)).id == ClassRelationId(30)
        assert client.class_relations.get(30).id == ClassRelationId(30)
        created_class_relation = client.class_relations.create(
            ClassRelationCreate(from_hubuum_class_id=ClassId(12), to_hubuum_class_id=ClassId(14))
        )
        assert created_class_relation.id == ClassRelationId(30)
        client.class_relations.delete(30)

        assert client.object_relations.list()[0].id == ObjectRelationId(31)
        assert client.object_relations.one(Query().where("id", 31)).id == ObjectRelationId(31)
        assert client.object_relations.get(31).id == ObjectRelationId(31)
        created_object_relation = client.object_relations.create(
            ObjectRelationCreate(
                from_hubuum_object_id=ObjectId(13),
                to_hubuum_object_id=ObjectId(15),
                class_relation_id=ClassRelationId(30),
            )
        )
        assert created_object_relation.id == ObjectRelationId(31)
        client.object_relations.delete(31)

        assert client.tasks.list()[0].id == TaskId(40)
        assert client.tasks.get(40).id == TaskId(40)
        assert client.tasks.wait(40, timeout_seconds=0).status.value == "succeeded"
        with pytest.raises(ValueError, match="timeout_seconds"):
            client.tasks.wait(40, timeout_seconds=float("nan"))
        with pytest.raises(ValueError, match="poll_interval"):
            client.tasks.wait(40, poll_interval=float("inf"))


def test_sync_pagination_and_decode_guards(class_json: dict[str, Any]) -> None:
    calls = 0

    def endless_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json=[class_json],
            headers={"X-Next-Cursor": str(calls), "X-Total-Count": "invalid"},
        )

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(endless_handler)
    ) as client:
        assert client.classes.page().total_count is None
        with pytest.raises(RuntimeError, match="max_pages"):
            client.classes.all(max_pages=1)
        with pytest.raises(ValueError, match="max_items"):
            client.classes.all(max_items=0)
        with pytest.raises(ValueError, match="max_pages"):
            client.classes.all(max_pages=0)

        calls_before_cycle = calls
        with pytest.raises(RuntimeError, match="repeated"):
            client.classes.all(Query().cursor(str(calls + 1)))
        assert calls == calls_before_cycle + 1

    with (
        Client(
            "https://hubuum.test",
            token="token",
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
        ) as client,
        pytest.raises(Exception, match="expected a JSON array"),
    ):
        client.classes.list()


async def test_async_crud_specific_services_and_relations(
    collection_json: dict[str, Any], class_json: dict[str, Any], object_json: dict[str, Any]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in {"/healthz", "/readyz"}:
            return httpx.Response(200, json={"status": "ok"})
        if "/collections/" in path:
            if request.method == "GET" and path.endswith(("/children", "/ancestors")):
                return httpx.Response(200, json=[collection_json])
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(200, json=collection_json)
        if "/classes/by-name/" in path:
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(200, json=class_json)
        if path.startswith("/api/v1/classes/"):
            if request.method == "DELETE":
                return httpx.Response(204)
            if request.method == "GET" and path.endswith("/12/"):
                return httpx.Response(200, json=[object_json])
            return httpx.Response(200, json=object_json)
        if "/relations/classes" in path:
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(
                200,
                json=[_class_relation_json()]
                if path.endswith("/classes") and request.method == "GET"
                else _class_relation_json(),
            )
        if "/relations/objects" in path:
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(
                200,
                json=[_object_relation_json()]
                if path.endswith("/objects") and request.method == "GET"
                else _object_relation_json(),
            )
        if path == "/api/v1/tasks":
            return httpx.Response(200, json=[_task_json()])
        return httpx.Response(200, json=_task_json())

    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        assert (await client.healthz()).status == "ok"
        assert (await client.readyz()).status == "ok"
        assert (await client.collections.get(11)).id == CollectionId(11)
        assert (await client.collections.update(11, CollectionUpdate(name="new"))).id == 11
        assert (await client.collections.children(11))[0].id == 11
        assert (await client.collections.ancestors(11))[0].id == 11
        assert (await client.collections.move(11, None)).id == 11
        await client.collections.delete(11)

        assert (
            await client.classes.update_by_name("server", ClassUpdate(description="x"))
        ).id == 12
        await client.classes.delete_by_name("server")

        objects = client.classes.by_id(12).objects
        assert (await objects.create(ObjectCreate(name="web", data={}, description="Web"))).id == 13
        assert (await objects.update(13, ObjectUpdate(description="new"))).id == 13
        assert (await objects.update_by_name("web", ObjectUpdate(name="web-2"))).id == 13
        assert (
            await objects.patch_data(
                13,
                [{"op": "add", "path": "/verified", "value": True}],
            )
        ).id == 13
        assert (await objects.list())[0].id == 13
        await objects.delete(13)
        await objects.delete_by_name("web")

        assert (await client.class_relations.list())[0].id == 30
        assert (await client.class_relations.one(Query().where("id", 30))).id == 30
        assert (await client.class_relations.get(30)).id == 30
        assert (
            await client.class_relations.create(
                ClassRelationCreate(
                    from_hubuum_class_id=ClassId(12), to_hubuum_class_id=ClassId(14)
                )
            )
        ).id == 30
        await client.class_relations.delete(30)

        assert (await client.object_relations.list())[0].id == 31
        assert (await client.object_relations.one(Query().where("id", 31))).id == 31
        assert (await client.object_relations.get(31)).id == 31
        assert (
            await client.object_relations.create(
                ObjectRelationCreate(
                    from_hubuum_object_id=ObjectId(13),
                    to_hubuum_object_id=ObjectId(15),
                    class_relation_id=ClassRelationId(30),
                )
            )
        ).id == 31
        await client.object_relations.delete(31)

        assert (await client.tasks.list())[0].id == 40
        assert (await client.tasks.get(40)).id == 40
        assert (await client.tasks.wait(40, timeout_seconds=0)).status.value == "succeeded"


async def test_async_user_group_methods() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/iam/users" in path:
            if request.method in {"DELETE", "POST"} and path != "/api/v1/iam/users":
                return httpx.Response(204)
            if request.method == "GET" and path == "/api/v1/iam/users":
                return httpx.Response(200, json=[_user_json()])
            return httpx.Response(200, json=_user_json())
        if path.endswith("/members"):
            return httpx.Response(
                200,
                headers={"x-total-count": "1", "x-page-limit": "25"},
                json=[_principal_member_json()],
            )
        if "/members/" in path:
            return httpx.Response(204)
        if request.method == "GET" and path == "/api/v1/iam/groups":
            return httpx.Response(200, json=[_group_json()])
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json=_group_json())

    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        user: User = await client.users.create(UserCreate(name="alice", password="secret"))
        assert user.id == 21
        assert (await client.users.get(21)).id == 21
        assert (await client.users.get_by_name("alice")).id == 21
        assert (await client.users.update(21, UserUpdate(email="new@example.com"))).id == 21
        await client.users.anonymize(21)
        await client.users.delete(21)

        group: Group = await client.groups.create(GroupCreate(groupname="ops"))
        assert group.id == 20
        assert (await client.groups.get(20)).id == 20
        assert (await client.groups.get_by_name("ops")).id == 20
        assert (await client.groups.update(20, GroupUpdate(groupname="platform"))).id == 20
        member: PrincipalMember = (await client.groups.members(20))[0]
        assert member.principal_id == PrincipalId(21)
        page = await client.groups.members_page(20, Query().limit(25).include_total())
        assert page.items == (member,)
        assert page.total_count == 1
        assert page.page_limit == 25
        pages = [page async for page in client.groups.member_pages(20)]
        assert [item for page in pages for item in page] == [member]
        assert await client.groups.all_members(20) == [member]
        await client.groups.add_member(20, PrincipalId(21))
        await client.groups.remove_member(20, PrincipalId(21))
        await client.groups.delete(20)


async def test_async_group_members_reject_non_array_response() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    async with AsyncClient("https://hubuum.test", token="token", transport=transport) as client:
        with pytest.raises(DecodeError, match="expected a JSON array"):
            await client.groups.members(20)


async def test_async_timeout_and_transport_error() -> None:
    def queued(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_task_json("queued"))

    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(queued)
    ) as client:
        with pytest.raises(ValueError, match="timeout_seconds"):
            await client.tasks.wait(40, timeout_seconds=float("nan"))
        with pytest.raises(ValueError, match="poll_interval"):
            await client.tasks.wait(40, poll_interval=float("inf"))
        with pytest.raises(TimeoutError, match="did not finish"):
            await client.tasks.wait(40, timeout_seconds=0)

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async with AsyncClient("https://hubuum.test", transport=httpx.MockTransport(offline)) as client:
        with pytest.raises(Exception, match="offline"):
            await client.request("GET", "/healthz", options=RequestOptions(authenticated=False))


async def test_async_pagination_and_decode_guards(class_json: dict[str, Any]) -> None:
    def paginated(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[class_json, class_json | {"id": 13}],
            headers={"X-Next-Cursor": "same", "X-Total-Count": "invalid"},
        )

    async with AsyncClient(
        "https://hubuum.test",
        token="token",
        transport=httpx.MockTransport(paginated),
    ) as client:
        assert (await client.classes.page()).total_count is None
        with pytest.raises(ValueError, match="max_pages"):
            await client.classes.all(max_pages=0)
        with pytest.raises(ValueError, match="max_items"):
            await client.classes.all(max_items=0)
        with pytest.raises(RuntimeError, match="max_pages"):
            await client.classes.all(max_pages=1)
        with pytest.raises(RuntimeError, match="repeated"):
            await client.classes.all(Query().cursor("same"))
        with pytest.raises(RuntimeError, match="max_items"):
            await client.classes.all(max_items=1)
        with pytest.raises(ResultCardinalityError, match="received 2"):
            await client.classes.one(Query())

    async with AsyncClient(
        "https://hubuum.test",
        token="token",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    ) as client:
        with pytest.raises(DecodeError, match="expected a JSON array"):
            await client.classes.list()


def test_sync_task_wait_times_out_after_a_nonterminal_response() -> None:
    with (
        Client(
            "https://hubuum.test",
            token="token",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=_task_json("queued"))
            ),
        ) as client,
        pytest.raises(TimeoutError, match="did not finish"),
    ):
        client.tasks.wait(40, timeout_seconds=0)


def test_sync_task_wait_caps_sleep_to_remaining_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []
    clock = iter((10.0, 10.75))

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_task_json("queued" if calls == 1 else "succeeded"))

    monkeypatch.setattr(services_module, "monotonic", lambda: next(clock))
    monkeypatch.setattr(services_module, "sleep", sleeps.append)

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        task = client.tasks.wait(40, timeout_seconds=1.0, poll_interval=5.0)

    assert task.status.value == "succeeded"
    assert sleeps == [0.25]


async def test_async_task_wait_caps_sleep_to_remaining_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    sleeps: list[float] = []
    clock = iter((20.0, 20.25))

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_task_json("queued" if calls == 1 else "succeeded"))

    async def record_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(async_services_module, "monotonic", lambda: next(clock))
    monkeypatch.setattr(asyncio, "sleep", record_sleep)

    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        task = await client.tasks.wait(40, timeout_seconds=0.5, poll_interval=5.0)

    assert task.status.value == "succeeded"
    assert sleeps == [0.25]


def _task_event_json() -> dict[str, Any]:
    return {
        "id": 81,
        "task_id": 40,
        "event_type": "completed",
        "message": "Task completed",
        "created_at": "2026-07-21T10:00:01Z",
        "provenance": {
            "actor": {
                "kind": "principal",
                "principal": {"principal_id": 21, "name": "admin"},
            },
            "task_id": 40,
        },
    }


def _import_result_json() -> dict[str, Any]:
    return {
        "id": 91,
        "task_id": 40,
        "entity_kind": "collection",
        "action": "create",
        "outcome": "succeeded",
        "created_at": "2026-07-21T10:00:01Z",
        "item_ref": "collection:inventory",
    }


def test_sync_v008_task_import_and_export_services() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path == "/api/v1/tasks/40/events":
            return httpx.Response(200, json=[_task_event_json()])
        if path == "/api/v1/imports/40/results":
            return httpx.Response(200, json=[_import_result_json()])
        if path == "/api/v1/exports/40/output":
            return httpx.Response(
                200,
                headers={"content-type": "text/csv; charset=utf-8"},
                text="id,name\n1,inventory\n",
            )
        return httpx.Response(200 if request.method == "GET" else 202, json=_task_json())

    with Client(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        event = client.tasks.events(40)[0]
        imported = client.imports.run(
            ImportRequest(graph=ImportGraph()),
            idempotency_key="import-v008",
            timeout_seconds=0,
        )
        exported = client.exports.run(
            ExportRequest(scope=ExportScope(kind=ExportScopeKind.COLLECTIONS)),
            idempotency_key="export-v008",
            timeout_seconds=0,
        )

    assert event.provenance.actor.principal is not None
    assert event.provenance.actor.principal.name == "admin"
    assert imported.succeeded == 1
    assert imported.failed == 0
    assert isinstance(exported, RenderedExport)
    assert exported.content_type is ExportContentType.CSV
    assert exported.body.endswith("inventory\n")
    submissions = [request for request in requests if request.method == "POST"]
    assert [request.headers["idempotency-key"] for request in submissions] == [
        "import-v008",
        "export-v008",
    ]
    assert json.loads(submissions[0].content) == {"graph": {}, "version": 1}


async def test_async_v008_task_import_and_export_services() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path == "/api/v1/tasks/40/events":
            return httpx.Response(200, json=[_task_event_json()])
        if path == "/api/v1/imports/40/results":
            return httpx.Response(200, json=[_import_result_json()])
        if path == "/api/v1/exports/40/output":
            return httpx.Response(
                200,
                headers={"content-type": "application/json; charset=utf-8"},
                json={
                    "items": [{"id": 1}],
                    "meta": {
                        "count": 1,
                        "truncated": False,
                        "scope": {"kind": "collections"},
                        "content_type": "application/json",
                    },
                    "warnings": [],
                },
            )
        return httpx.Response(200 if request.method == "GET" else 202, json=_task_json())

    async with AsyncClient(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    ) as client:
        event = (await client.tasks.events(40))[0]
        imported = await client.imports.run(
            ImportRequest(graph=ImportGraph()),
            idempotency_key="async-import-v008",
            timeout_seconds=0,
        )
        exported = await client.exports.run(
            ExportRequest(scope=ExportScope(kind=ExportScopeKind.COLLECTIONS)),
            idempotency_key="async-export-v008",
            timeout_seconds=0,
        )

    assert event.task_id == TaskId(40)
    assert imported.succeeded == 1
    assert isinstance(exported, ExportJsonResponse)
    assert exported.meta.count == 1
    submissions = [request for request in requests if request.method == "POST"]
    assert [request.headers["idempotency-key"] for request in submissions] == [
        "async-import-v008",
        "async-export-v008",
    ]
