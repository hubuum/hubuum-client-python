from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from hubuum_client import (
    APIError,
    AuthenticationError,
    ClassCreate,
    ClassId,
    ClassUpdate,
    Client,
    ClientOptions,
    CollectionCreate,
    CollectionId,
    ConfigurationError,
    ConflictError,
    Credentials,
    DecodeError,
    FilterOperator,
    GroupId,
    NotFoundError,
    PermissionDeniedError,
    Query,
    RateLimitError,
    RequestOptions,
    ResultCardinalityError,
    TransportError,
)


def _client(
    handler: Callable[[httpx.Request], httpx.Response], *, token: str | None = None
) -> Client:
    return Client("https://hubuum.test", token=token, transport=httpx.MockTransport(handler))


def test_login_authentication_and_logout_are_redacted() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/login"):
            assert "authorization" not in request.headers
            assert json.loads(request.content) == {"name": "admin", "password": "secret"}
            return httpx.Response(200, json={"token": "bearer-secret"})
        if request.url.path.endswith("/logout"):
            assert request.headers["authorization"] == "Bearer bearer-secret"
            return httpx.Response(204)
        raise AssertionError(request.url)

    with _client(handler) as client:
        returned = client.login(Credentials("admin", "secret"))
        assert returned is client
        assert client.token is not None
        assert "bearer-secret" not in repr(client.token)
        client.logout()
        assert not client.is_authenticated
        assert [request.method for request in requests] == ["POST", "POST"]


def test_typed_crud_and_cursor_page(
    collection_json: dict[str, Any], class_json: dict[str, Any]
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET" and request.url.path.endswith("/classes"):
            return httpx.Response(
                200,
                json=[class_json],
                headers={"X-Next-Cursor": "next", "X-Total-Count": "3", "X-Page-Limit": "1"},
            )
        if request.method == "POST" and request.url.path.endswith("/collections"):
            assert json.loads(request.content) == {
                "name": "inventory",
                "description": "Inventory",
                "group_id": 2,
            }
            return httpx.Response(201, json=collection_json)
        raise AssertionError(f"unexpected {request.method} {request.url}")

    with _client(handler, token="token") as client:
        page = client.classes.page(
            Query().where("name", "serv", FilterOperator.ICONTAINS).limit(1).include_total()
        )
        collection = client.collections.create(
            CollectionCreate(
                name="inventory",
                description="Inventory",
                group_id=GroupId(2),
            )
        )

    assert page[0].id == ClassId(12)
    assert page.next_cursor == "next"
    assert page.total_count == 3
    assert page.page_limit == 1
    assert collection.id == CollectionId(11)
    assert dict(requests[0].url.params.multi_items()) == {
        "name__icontains": "serv",
        "limit": "1",
        "include_total": "true",
    }
    assert requests[0].headers["authorization"] == "Bearer token"


def test_exact_name_path_is_segment_encoded(class_json: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.raw_path == b"/api/v1/classes/by-name/a%2Fb%20c"
        return httpx.Response(200, json=class_json)

    with _client(handler, token="token") as client:
        assert client.classes.get_by_name("a/b c").name == "server"


def test_objects_use_class_scoped_routes(object_json: dict[str, Any]) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        body: object = [object_json] if request.url.path.endswith("/12/") else object_json
        return httpx.Response(200, json=body)

    with _client(handler, token="token") as client:
        objects = client.classes.by_id(12).objects
        by_id = objects.get(13)
        by_name = objects.get_by_name("web-01")

    assert by_id.id == by_name.id
    assert paths == [
        "/api/v1/classes/12/13",
        "/api/v1/classes/12/",
    ]


def test_classes_by_id_selects_class_and_nested_objects(
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

    with _client(handler, token="token") as client:
        assert not hasattr(client, "objects")
        assert not hasattr(client, "objects_by_class_name")
        selected = client.classes.by_id(ClassId(12))
        assert selected.class_id == ClassId(12)
        assert selected.objects.class_id == ClassId(12)
        assert selected.get().id == ClassId(12)
        assert selected.update(ClassUpdate(description="updated")).id == ClassId(12)
        page = selected.objects.page(Query().where("name", "web-01").include_total())
        selected.delete()

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


def test_automatic_pagination_follows_cursor(class_json: dict[str, Any]) -> None:
    cursors: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        cursors.append(cursor)
        headers = {"X-Next-Cursor": "second"} if cursor is None else {}
        body = [class_json | {"id": 12 if cursor is None else 13}]
        return httpx.Response(200, json=body, headers=headers)

    with _client(handler, token="token") as client:
        classes = client.classes.all(Query().limit(1))

    assert [item.id for item in classes] == [12, 13]
    assert cursors == [None, "second"]


def test_repeated_pagination_cursor_is_rejected(class_json: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[class_json], headers={"X-Next-Cursor": "same"})

    with (
        _client(handler, token="token") as client,
        pytest.raises(RuntimeError, match="repeated"),
    ):
        client.classes.all()


def test_one_enforces_cardinality() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    with (
        _client(handler, token="token") as client,
        pytest.raises(ResultCardinalityError, match="received 0"),
    ):
        client.classes.one(Query().where("name", "missing"))


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (400, APIError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ConflictError),
        (429, RateLimitError),
    ],
)
def test_http_errors_are_structured_and_secret_safe(
    status: int, error_type: type[APIError]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            json={"error": "Nope", "message": "request rejected"},
            headers={"X-Request-Id": "request-1", "Retry-After": "2"},
        )

    with _client(handler, token="bearer-secret") as client, pytest.raises(error_type) as raised:
        client.request("GET", "/api/v1/classes", options=RequestOptions(params={"q": "visible"}))

    error = raised.value
    assert error.status_code == status
    assert error.message == "request rejected"
    assert error.request_id == "request-1"
    assert "bearer-secret" not in str(error)
    assert "?" not in error.url
    if isinstance(error, RateLimitError):
        assert error.retry_after == 2


def test_error_responses_and_transport_failures_redact_request_secrets() -> None:
    password = "login-password-secret"

    def rejected(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["password"] == password
        return httpx.Response(
            400,
            json={
                "error": "InvalidCredentials",
                "message": f"rejected password {password}",
                "password": password,
                "access_token": "server-token-secret",
            },
            headers={"X-Request-Id": f"request-{password}"},
        )

    with _client(rejected) as client, pytest.raises(APIError) as raised:
        client.login(Credentials("admin", password))

    error = raised.value
    assert password not in str(error)
    assert password not in repr(error)
    assert "server-token-secret" not in repr(error)
    assert error.response_body["password"] == "<redacted>"
    assert error.response_body["access_token"] == "<redacted>"

    def offline(request: httpx.Request) -> httpx.Response:
        authorization = request.headers["authorization"]
        raise httpx.ConnectError(f"failed while sending {authorization}", request=request)

    with (
        _client(offline, token="bearer-secret") as client,
        pytest.raises(TransportError) as raised_transport,
    ):
        client.request("GET", "/api/v1/classes")

    assert "bearer-secret" not in str(raised_transport.value)
    assert "bearer-secret" not in repr(raised_transport.value)


def test_configured_auth_replaces_header_case_insensitively_and_host_is_locked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get_list("authorization") == ["Bearer configured-token"]
        assert request.headers["host"] == "hubuum.test"
        return httpx.Response(200, json={})

    with _client(handler, token="configured-token") as client:
        client.request(
            "GET",
            "/api/v1/custom",
            options=RequestOptions(headers={"authorization": "Bearer caller-token"}),
        )
        with pytest.raises(ConfigurationError, match="Host header"):
            client.request(
                "GET",
                "/api/v1/custom",
                options=RequestOptions(headers={"hOsT": "evil.test"}),
            )

    with Client(
        "https://hubuum.test",
        options=ClientOptions(user_agent="hubuum-test-suite"),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200 if request.headers["user-agent"] == "hubuum-test-suite" else 400,
                json={},
            )
        ),
    ) as client:
        assert client.request("GET", "/healthz", options=RequestOptions(authenticated=False)) == {}


@pytest.mark.parametrize(
    "path",
    [
        "api/v1/classes",
        "https://evil.example/api/v1/classes",
        "//evil.example/api/v1/classes",
        "/api/../secret",
        "/api/%2e%2e/secret",
        "/api/%252e%252e/secret",
        "/api/%252525252525252525",
        "/api/..\\secret",
        "/api/\tsecret",
        "/api/%00/secret",
        "/api/v1/classes?q=embedded",
    ],
)
def test_raw_request_rejects_unsafe_paths(path: str) -> None:
    with (
        _client(lambda request: httpx.Response(200, json={})) as client,
        pytest.raises(ConfigurationError),
    ):
        client.request("GET", path)


@pytest.mark.parametrize(
    "base_url",
    [
        "hubuum.test",
        "ftp://hubuum.test",
        "https://alice:secret@hubuum.test",
        "https://x.test?q=1",
        "https://hubuum.test:invalid",
        "https://hubuum.test:0",
        "https://hubuum.test:65536",
        "https://hubuum.test/%252e%252e/secret",
        "https://hubuum.test/\nsecret",
        "https://hubuum.test/%00",
    ],
)
def test_client_rejects_unsafe_base_urls(base_url: str) -> None:
    with pytest.raises(ConfigurationError):
        Client(base_url)


def test_decode_and_transport_errors_are_wrapped() -> None:
    with (
        _client(lambda request: httpx.Response(200, text="not-json")) as client,
        pytest.raises(DecodeError),
    ):
        client.classes.get(1)

    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with _client(failing_handler) as client, pytest.raises(TransportError, match="offline"):
        client.request("GET", "/healthz", options=RequestOptions(authenticated=False))


def test_raw_request_returns_json_for_unmodeled_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/search"
        return httpx.Response(200, json={"results": {"objects": []}})

    with _client(handler, token="token") as client:
        result = client.request(
            "GET", "/api/v1/search", options=RequestOptions(params={"q": "server"})
        )

    assert result == {"results": {"objects": []}}


def test_class_create_serializes_typed_request(class_json: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["collection_id"] == 11
        return httpx.Response(201, json=class_json)

    with _client(handler, token="token") as client:
        created = client.classes.create(
            ClassCreate(name="server", collection_id=CollectionId(11), description="Server")
        )

    assert created.id == ClassId(12)


def test_plain_basemodel_config_fallback_and_client_metadata() -> None:
    class PlainPayload(BaseModel):
        enabled: bool
        omitted: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/config":
            return httpx.Response(200, json=[])
        assert json.loads(request.content) == {"enabled": True}
        return httpx.Response(204)

    with _client(handler, token="token") as client:
        assert client.base_url == "https://hubuum.test/"
        assert client.config() == {}
        assert client.request("POST", "/api/v1/custom", json=PlainPayload(enabled=True)) is None


def test_decode_validation_and_nested_error_redaction_edges() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/custom-invalid-json":
            return httpx.Response(
                200,
                content=b"{",
                headers={"Content-Type": "application/json"},
            )
        if request.url.path == "/api/v1/classes/1":
            return httpx.Response(200, json={"name": "missing-required-fields"})
        return httpx.Response(
            400,
            json=[
                {"password": "response-secret"},
                {"details": ["visible", 7]},
            ],
        )

    with _client(handler, token="token") as client:
        with pytest.raises(DecodeError):
            client.request("GET", "/api/v1/custom-invalid-json")
        with pytest.raises(DecodeError) as model_error:
            client.classes.get(1)
        with pytest.raises(APIError) as api_error:
            client.request("GET", "/api/v1/custom-error-list")

    assert "input" not in model_error.value.reason
    assert api_error.value.response_body == [
        {"password": "<redacted>"},
        {"details": ["visible", 7]},
    ]


def test_nested_request_secrets_are_redacted_from_transport_errors() -> None:
    first_secret = "nested-secret-one"
    second_secret = "nested-secret-two"

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            f"failed with {first_secret} and {second_secret}",
            request=request,
        )

    with _client(offline) as client, pytest.raises(TransportError) as raised:
        client.request(
            "POST",
            "/api/v1/custom",
            json={"password": [first_secret, (second_secret,)]},
        )

    assert first_secret not in str(raised.value)
    assert second_secret not in str(raised.value)


@pytest.mark.parametrize("headers", [{}, {"Retry-After": "not-a-number"}])
def test_invalid_or_missing_retry_after_is_ignored(headers: dict[str, str]) -> None:
    with (
        _client(lambda request: httpx.Response(429, text="limited", headers=headers)) as client,
        pytest.raises(RateLimitError) as raised,
    ):
        client.request("GET", "/api/v1/custom")

    assert raised.value.retry_after is None
