from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, TypeVar

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    AsyncClient,
    AuthenticationError,
    Client,
    DecodeError,
    GroupId,
    NewTokenRequest,
    NotFoundError,
    PermissionDeniedError,
    PreconditionFailedError,
    PrincipalId,
    Query,
    ResultCardinalityError,
    ServiceAccount,
    ServiceAccountCreate,
    ServiceAccountId,
    ServiceAccountPoint,
    ServiceAccountUpdate,
)

T = TypeVar("T")
BASE = "/api/v1/iam/service-accounts"


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


async def _collect(value: Iterable[T] | AsyncIterable[T]) -> list[T]:
    if isinstance(value, AsyncIterable):
        return [item async for item in value]
    return list(value)


@asynccontextmanager
async def _client(
    asynchronous: bool, handler: Callable[[httpx.Request], httpx.Response]
) -> AsyncIterator[Client | AsyncClient]:
    api = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="bearer-secret", transport=httpx.MockTransport(handler)
    )
    try:
        yield api
    finally:
        await _resolve(api.close())


def _record(*, point: bool = False) -> dict[str, Any]:
    return {
        "id": 41,
        "name": "importer",
        "description": "Inventory import",
        "owner_group_id": 23,
        "created_by": 17,
        "disabled_at": None,
        "created_at": "2026-10-24T10:00:00Z",
        "updated_at": "2026-10-24T10:00:00Z",
        "revision": 1,
        **({"identity_scope_id": 3} if point else {"identity_scope": "local"}),
    }


def test_service_account_request_and_response_models() -> None:
    create = ServiceAccountCreate(name="importer", owner_group_id=GroupId(23))
    assert create.payload() == {"name": "importer", "owner_group_id": 23}
    assert ServiceAccountUpdate(description="").payload() == {"description": ""}
    assert ServiceAccountUpdate(description=None).payload() == {}
    with pytest.raises(ValidationError):
        ServiceAccountCreate(name="importer", owner_group_id=GroupId(0))
    for model in (ServiceAccountCreate, ServiceAccountUpdate):
        with pytest.raises(ValidationError):
            model.model_validate({"name": "importer", "owner_group_id": 23, "unknown": True})
    record = ServiceAccount.model_validate(_record() | {"future_field": "retained"})
    point = ServiceAccountPoint.model_validate(_record(point=True))
    assert record.model_extra == {"future_field": "retained"}
    assert record.principal_id == point.principal_id == PrincipalId(41)
    assert isinstance(record.created_at, datetime)
    for response_model, value in (
        (ServiceAccount, _record(point=True)),
        (ServiceAccountPoint, _record()),
    ):
        with pytest.raises(ValidationError):
            response_model.model_validate(value)


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_service_account_lifecycle_and_token_identity(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["authorization"] == "Bearer bearer-secret"
        path = request.url.path
        if path == "/api/v1/iam/principals/41/tokens":
            assert json.loads(request.content) == {"name": "automation"}
            return httpx.Response(
                201, json={"token": "issued-secret", "expires_at": "2026-10-25T10:00:00Z"}
            )
        if request.method == "DELETE":
            assert request.headers["if-match"] == '"rev-3"'
            return httpx.Response(204)
        body = _record(point=True)
        if request.method == "PATCH":
            assert request.headers["if-match"] == '"rev-1"'
            assert json.loads(request.content) == {"description": "", "owner_group_id": 24}
            body.update(description="", owner_group_id=24, revision=2)
        elif path.endswith("/disable"):
            assert request.headers["if-match"] == '"rev-2"'
            assert not request.content
            body.update(disabled_at="2026-10-24T11:00:00Z", revision=3)
        elif request.method == "POST":
            assert json.loads(request.content) == {
                "name": "importer",
                "owner_group_id": 23,
                "identity_scope": "local",
            }
        return httpx.Response(201 if request.method == "POST" else 200, json=body)

    async with _client(asynchronous, handler) as api:
        service = api.service_accounts
        assert service is api.service_accounts
        created = await _resolve(
            service.create(
                ServiceAccountCreate(
                    name="importer", owner_group_id=GroupId(23), identity_scope="local"
                )
            )
        )
        assert isinstance(created, ServiceAccountPoint)
        assert created.id == ServiceAccountId(41)
        assert created.identity_scope_id == 3
        assert await _resolve(service.get(created.id)) == created
        token = await _resolve(
            api.tokens.for_principal(created.principal_id).create(
                NewTokenRequest(name="automation")
            )
        )
        assert token.value == "issued-secret"
        assert "issued-secret" not in repr(token)
        updated = await _resolve(
            service.update(
                created.id,
                ServiceAccountUpdate(description="", owner_group_id=GroupId(24)),
                if_match='"rev-1"',
            )
        )
        assert updated.description == ""
        assert updated.owner_group_id == 24
        disabled = await _resolve(service.disable(created.id, if_match='"rev-2"'))
        assert disabled.disabled_at is not None
        await _resolve(service.delete(created.id, if_match='"rev-3"'))
    assert [(r.method, r.url.path) for r in requests] == [
        ("POST", BASE),
        ("GET", f"{BASE}/41"),
        ("POST", "/api/v1/iam/principals/41/tokens"),
        ("PATCH", f"{BASE}/41"),
        ("POST", f"{BASE}/41/disable"),
        ("DELETE", f"{BASE}/41"),
    ]


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_service_account_pagination_and_name_lookup(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == BASE
        assert request.url.params["identity_scope__equals"] == "local"
        second = "cursor" in request.url.params
        return httpx.Response(
            200,
            json=[_record() | {"id": 42 if second else 41}],
            headers={
                "X-Total-Count": "2",
                "X-Page-Limit": "1",
                **({} if second else {"X-Next-Cursor": "opaque-next"}),
            },
        )

    async with _client(asynchronous, handler) as api:
        service = api.service_accounts
        query = Query().where("identity_scope", "local").sort("id.asc").limit(1).include_total()
        page = await _resolve(service.page(query))
        assert page.total_count == 2
        assert page.page_limit == 1
        assert page.next_cursor == "opaque-next"
        assert isinstance(page[0], ServiceAccount)
        assert len(await _resolve(service.list(query))) == 1
        assert len(await _collect(service.pages(query))) == 2
        assert [item.id for item in await _resolve(service.all(query))] == [41, 42]
        assert requests[-1].url.params == httpx.QueryParams(query.cursor("opaque-next").as_params())
        assert query.cursor_value is None
        found = await _resolve(service.get_by_name("importer", identity_scope="local"))
        assert found.principal_id == 41
        assert requests[-1].url.params["name__equals"] == "importer"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("count", [0, 2])
async def test_service_account_name_lookup_requires_one_match(
    asynchronous: bool, count: int
) -> None:
    async with _client(
        asynchronous, lambda _: httpx.Response(200, json=[_record()] * count)
    ) as api:
        with pytest.raises(ResultCardinalityError):
            await _resolve(api.service_accounts.get_by_name("importer"))


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("guard", ["cycle", "max_pages", "max_items"])
async def test_service_account_pagination_guards(asynchronous: bool, guard: str) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[_record()], headers={"X-Next-Cursor": "repeated"})

    async with _client(asynchronous, handler) as api:
        with pytest.raises(RuntimeError, match=r"repeated|exceeded"):
            await _resolve(
                api.service_accounts.all(
                    Query().cursor("repeated") if guard == "cycle" else Query(),
                    max_pages=1 if guard == "max_pages" else 100,
                    max_items=1 if guard == "max_items" else 10_000,
                )
            )


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("point", [False, True])
async def test_service_account_malformed_responses_are_redacted(
    asynchronous: bool, point: bool
) -> None:
    body = _record(point=point) | {"revision": "response-secret"}
    async with _client(
        asynchronous, lambda _: httpx.Response(200, json=body if point else [body])
    ) as api:
        with pytest.raises(DecodeError) as error:
            await _resolve(api.service_accounts.get(41) if point else api.service_accounts.list())
    assert "response-secret" not in str(error.value)
    assert "bearer-secret" not in repr(error.value)
    assert error.value.__context__ is None


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (412, PreconditionFailedError),
    ],
)
async def test_service_account_errors(
    asynchronous: bool, status: int, error_type: type[Exception]
) -> None:
    async with _client(
        asynchronous, lambda _: httpx.Response(status, json={"message": "denied"})
    ) as api:
        with pytest.raises(error_type):
            await _resolve(api.service_accounts.disable(ServiceAccountId(41)))
