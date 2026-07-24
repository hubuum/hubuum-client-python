from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from hubuum_client import (
    AsyncClient,
    ClassUpdate,
    Client,
    ObjectCreate,
    ObjectUpdate,
    Query,
)


def _response_for_named_route(
    request: httpx.Request,
    *,
    class_json: dict[str, Any],
    object_json: dict[str, Any],
) -> httpx.Response:
    path = request.url.path
    if request.method == "DELETE":
        return httpx.Response(204)
    if path.endswith("/object-aggregates"):
        return httpx.Response(
            200,
            json=[{"dimensions": [], "object_count": 1}],
            headers={"X-Total-Count": "1", "X-Page-Limit": "10"},
        )
    if path.endswith("/permissions"):
        return httpx.Response(200, json=[{"permission": "ReadClass"}])
    if path.endswith("/related/classes"):
        return httpx.Response(200, json=[{"id": 12, "path": [12]}])
    if path.endswith("/related/relations"):
        return httpx.Response(200, json=[{"id": 30}])
    if path.endswith("/related/objects"):
        return httpx.Response(200, json=[object_json | {"path": [13]}])
    if path.endswith("/related/graph"):
        return httpx.Response(200, json={"objects": [], "relations": []})
    if path.endswith("/data"):
        return httpx.Response(200, json=object_json | {"data": {"facts": {"serial": "A"}}})
    if "/objects/by-name/" in path:
        return httpx.Response(200, json=object_json)
    if path.endswith("/objects"):
        return httpx.Response(
            200,
            json=[object_json] if request.method == "GET" else object_json,
        )
    return httpx.Response(200, json=class_json)


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> Client:
    return Client("https://hubuum.test", token="token", transport=httpx.MockTransport(handler))


def _async_client(handler: Callable[[httpx.Request], httpx.Response]) -> AsyncClient:
    return AsyncClient(
        "https://hubuum.test",
        token="token",
        transport=httpx.MockTransport(handler),
    )


def test_complete_by_name_surface_and_miami_workflow(
    class_json: dict[str, Any],
    object_json: dict[str, Any],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _response_for_named_route(
            request,
            class_json=class_json,
            object_json=object_json,
        )

    with _client(handler) as client:
        selected = client.classes.by_name("Hosts 2")
        assert selected.get().id == 12
        assert selected.update(ClassUpdate(description="updated")).id == 12
        assert selected.permissions()[0]["permission"] == "ReadClass"
        assert selected.related_classes()[0]["id"] == 12
        assert selected.related_relations()[0]["id"] == 30
        assert selected.related_graph()["objects"] == []
        assert selected.object_aggregates(params=[("group_by", "description")]).total_count == 1

        objects = client.objects_by_class_name("Hosts 2")
        query = Query().data("status").equals("active").sort("id.asc").include_total(False)
        assert objects.page(query)[0].id == 13
        assert objects.list()[0].id == 13
        assert next(objects.pages())[0].id == 13
        assert objects.all()[0].id == 13
        assert objects.one(Query().where("name", "host/name")).id == 13
        assert objects.get("host/name").id == 13
        assert objects.create(ObjectCreate(name="new", description="new", data={})).id == 13
        assert objects.update("host/name", ObjectUpdate(description="updated")).id == 13
        patched = objects.patch_data(
            "host/name",
            [{"op": "add", "path": "/facts", "value": {"serial": "A"}}],
        )
        assert patched.data == {"facts": {"serial": "A"}}
        assert objects.related_objects("host/name")[0]["id"] == 13
        assert objects.related_relations("host/name")[0]["id"] == 30
        assert objects.related_graph("host/name")["relations"] == []
        objects.delete("host/name")
        selected.delete()

    raw_paths = [request.url.raw_path for request in requests]
    assert b"/api/v1/classes/by-name/Hosts%202/objects" in raw_paths
    assert b"/api/v1/classes/by-name/Hosts%202/objects/by-name/host%2Fname/data" in raw_paths
    patch = next(request for request in requests if request.url.path.endswith("/data"))
    assert patch.headers["content-type"] == "application/json-patch+json"
    assert json.loads(patch.content)[0]["path"] == "/facts"
    assert {(request.method, request.url.path) for request in requests} == {
        ("DELETE", "/api/v1/classes/by-name/Hosts 2"),
        (
            "DELETE",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name",
        ),
        ("GET", "/api/v1/classes/by-name/Hosts 2"),
        ("GET", "/api/v1/classes/by-name/Hosts 2/object-aggregates"),
        ("GET", "/api/v1/classes/by-name/Hosts 2/objects"),
        (
            "GET",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name",
        ),
        (
            "GET",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name/related/graph",
        ),
        (
            "GET",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name/related/objects",
        ),
        (
            "GET",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name/related/relations",
        ),
        ("GET", "/api/v1/classes/by-name/Hosts 2/permissions"),
        ("GET", "/api/v1/classes/by-name/Hosts 2/related/classes"),
        ("GET", "/api/v1/classes/by-name/Hosts 2/related/graph"),
        ("GET", "/api/v1/classes/by-name/Hosts 2/related/relations"),
        ("PATCH", "/api/v1/classes/by-name/Hosts 2"),
        (
            "PATCH",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name",
        ),
        (
            "PATCH",
            "/api/v1/classes/by-name/Hosts 2/objects/by-name/host/name/data",
        ),
        ("POST", "/api/v1/classes/by-name/Hosts 2/objects"),
    }


async def test_async_complete_by_name_surface(
    class_json: dict[str, Any],
    object_json: dict[str, Any],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response_for_named_route(
            request,
            class_json=class_json,
            object_json=object_json,
        )

    async with _async_client(handler) as client:
        selected = client.classes.by_name("Hosts")
        assert (await selected.get()).id == 12
        assert (await selected.update(ClassUpdate(description="updated"))).id == 12
        assert (await selected.permissions())[0]["permission"] == "ReadClass"
        assert (await selected.related_classes())[0]["id"] == 12
        assert (await selected.related_relations())[0]["id"] == 30
        assert (await selected.related_graph())["objects"] == []
        assert (
            await selected.object_aggregates(params=[("group_by", "description")])
        ).total_count == 1

        objects = client.objects_by_class_name("Hosts")
        assert (await objects.page())[0].id == 13
        assert (await objects.list())[0].id == 13
        pages = [page async for page in objects.pages()]
        assert pages[0][0].id == 13
        assert (await objects.all())[0].id == 13
        assert (await objects.one(Query().where("name", "host"))).id == 13
        assert (await objects.get("host")).id == 13
        assert (await objects.create(ObjectCreate(name="new", description="new", data={}))).id == 13
        assert (await objects.update("host", ObjectUpdate(description="updated"))).id == 13
        assert (
            await objects.patch_data(
                "host",
                [{"op": "add", "path": "/facts", "value": {"serial": "A"}}],
            )
        ).data == {"facts": {"serial": "A"}}
        assert (await objects.related_objects("host"))[0]["id"] == 13
        assert (await objects.related_relations("host"))[0]["id"] == 30
        assert (await objects.related_graph("host"))["relations"] == []
        await objects.delete("host")
        await selected.delete()
