from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import quote_plus

import httpx
import pytest

from hubuum_client import (
    APIError,
    AsyncClient,
    ClassId,
    ClassUpdate,
    ClientOptions,
    CollectionId,
    ConfigurationError,
    Credentials,
    DecodeError,
    Query,
    RateLimitError,
    RequestOptions,
    TransportError,
)


def _client(
    handler: Callable[[httpx.Request], httpx.Response], *, token: str | None = None
) -> AsyncClient:
    return AsyncClient("https://hubuum.test", token=token, transport=httpx.MockTransport(handler))


async def test_async_login_and_typed_service(class_json: dict[str, Any]) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/login"):
            assert json.loads(request.content)["password"] == "secret"
            return httpx.Response(200, json={"token": "async-token"})
        assert request.headers["authorization"] == "Bearer async-token"
        return httpx.Response(200, json=[class_json])

    async with _client(handler) as client:
        returned = await client.login(Credentials("admin", "secret"))
        page = await client.classes.page(Query().data("metrics", "cpu_count").gte(4).limit(10))

    assert returned is client
    assert page[0].id == ClassId(12)
    assert [request.method for request in requests] == ["POST", "GET"]
    assert requests[1].url.params["json_data__gte"] == "metrics,cpu_count=4"


async def test_async_cursor_pagination(class_json: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        headers = {"X-Next-Cursor": "two"} if cursor is None else {}
        return httpx.Response(
            200,
            json=[class_json | {"id": 12 if cursor is None else 14}],
            headers=headers,
        )

    async with _client(handler, token="token") as client:
        items = await client.classes.all(max_items=2)

    assert [item.id for item in items] == [12, 14]


async def test_async_exact_name_and_public_config(class_json: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/config":
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"pagination": {"default_page_limit": 100}})
        return httpx.Response(200, json=class_json)

    async with _client(handler, token="token") as client:
        config = await client.config()
        model = await client.classes.get_by_name("server")

    assert config["pagination"]["default_page_limit"] == 100
    assert model.collection_id == CollectionId(11)


async def test_async_classes_by_id_selects_class_and_nested_objects(
    class_json: dict[str, Any],
    object_json: dict[str, Any],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path.endswith("/12/"):
            return httpx.Response(
                200,
                json=[object_json],
                headers={"X-Total-Count": "1"},
            )
        return httpx.Response(200, json=class_json)

    async with _client(handler, token="token") as client:
        assert not hasattr(client, "objects")
        assert not hasattr(client, "objects_by_class_name")
        selected = client.classes.by_id(ClassId(12))
        assert selected.class_id == ClassId(12)
        assert selected.objects.class_id == ClassId(12)
        assert (await selected.get()).id == ClassId(12)
        assert (await selected.update(ClassUpdate(description="updated"))).id == ClassId(12)
        page = await selected.objects.page(Query().where("name", "web-01").include_total())
        await selected.delete()

    assert page[0].id == object_json["id"]
    assert page.total_count == 1
    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", "/api/v1/classes/12"),
        ("PATCH", "/api/v1/classes/12"),
        ("GET", "/api/v1/classes/12/"),
        ("DELETE", "/api/v1/classes/12"),
    ]
    assert requests[2].url.params["name__equals"] == "web-01"
    assert requests[2].url.params["include_total"] == "true"


async def test_async_logout_clears_token_on_server_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Failure", "message": "failed"})

    async with _client(handler, token="token") as client:
        with pytest.raises(Exception, match="failed"):
            await client.logout()
        assert not client.is_authenticated


async def test_async_rate_limit_error_parses_retry_after_http_date() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": "RateLimited", "message": "slow down"},
            headers={"Retry-After": "Thu, 23 Jul 2099 12:02:00 GMT"},
        )

    async with _client(handler) as client:
        with pytest.raises(RateLimitError) as raised:
            await client.request("GET", "/api/v1/classes")

    assert raised.value.retry_after is not None
    assert raised.value.retry_after > 0


async def test_async_headers_and_exceptions_are_secret_safe() -> None:
    def authenticated(request: httpx.Request) -> httpx.Response:
        assert request.headers.get_list("authorization") == ["Bearer async-token"]
        return httpx.Response(200, json={})

    async with _client(authenticated, token="async-token") as client:
        await client.request(
            "GET",
            "/api/v1/custom",
            options=RequestOptions(headers={"AUTHORIZATION": "Bearer caller-token"}),
        )
        with pytest.raises(ConfigurationError, match="Host header"):
            await client.request(
                "GET",
                "/api/v1/custom",
                options=RequestOptions(headers={"host": "evil.test"}),
            )

    async with AsyncClient(
        "https://hubuum.test",
        options=ClientOptions(user_agent="hubuum-async-test"),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200 if request.headers["user-agent"] == "hubuum-async-test" else 400,
                json={},
            )
        ),
    ) as client:
        assert (
            await client.request("GET", "/healthz", options=RequestOptions(authenticated=False))
            == {}
        )

    password = "async-password-secret"

    def rejected(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text=f"rejected {password}")

    async with _client(rejected) as client:
        with pytest.raises(APIError) as raised:
            await client.login(Credentials("admin", password))

    assert password not in str(raised.value)
    assert password not in repr(raised.value)

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with {request.headers['authorization']}", request=request)

    async with _client(offline, token="transport-secret") as client:
        with pytest.raises(TransportError) as raised_transport:
            await client.request("GET", "/api/v1/custom")

    assert "transport-secret" not in str(raised_transport.value)


async def test_async_metadata_config_fallback_and_raw_decode_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/config":
            return httpx.Response(200, json=[])
        return httpx.Response(
            200,
            content=b"{",
            headers={"Content-Type": "application/json"},
        )

    async with _client(handler, token="token") as client:
        assert client.base_url == "https://hubuum.test/"
        assert client.token is not None
        assert await client.config() == {}
        with pytest.raises(DecodeError):
            await client.request("GET", "/api/v1/custom-invalid-json")


async def test_async_query_secrets_are_redacted() -> None:
    query_secret = "async /+% café secret"
    encoded_query_secret = quote_plus(query_secret, safe="")

    def rejected(request: httpx.Request) -> httpx.Response:
        assert request.url.params["token"] == query_secret
        return httpx.Response(400, text=f"rejected {query_secret}")

    async with _client(rejected) as client:
        with pytest.raises(APIError) as raised:
            await client.request(
                "GET",
                "/api/v1/custom",
                options=RequestOptions(params={"token": query_secret}),
            )

    assert query_secret not in str(raised.value)
    assert query_secret not in repr(raised.value)

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed while sending {request.url}", request=request)

    async with _client(offline) as client:
        with pytest.raises(TransportError) as raised_transport:
            await client.request(
                "GET",
                "/api/v1/custom",
                options=RequestOptions(params={"access-token": query_secret}),
            )

    assert query_secret not in str(raised_transport.value)
    assert encoded_query_secret not in str(raised_transport.value)
    assert query_secret not in repr(raised_transport.value)
