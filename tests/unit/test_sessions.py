"""Interactive sessions have identical safety behavior in both transports."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    APIError,
    AsyncClient,
    Client,
    ConfigurationError,
    Credentials,
    DecodeError,
    SessionExpiredError,
    SessionResponse,
    TransportError,
)


class SessionServer:
    def __init__(self) -> None:
        self.identifier = str(uuid4())
        self.absolute = datetime.now(UTC) + timedelta(days=30)
        self.rotations = 0
        self.requests: list[httpx.Request] = []
        self.failure: str | None = None

    def pair(self) -> dict[str, str]:
        return {
            "session_id": self.identifier,
            "token_type": "Bearer",
            "access_token": f"hbt1.test.access-secret-{self.rotations}",
            "refresh_token": f"hbr1.test.refresh-secret-{self.rotations}",
            "access_expires_at": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
            "refresh_expires_at": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "absolute_expires_at": self.absolute.isoformat(),
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == "/api/v1/auth/login":
            assert "authorization" not in request.headers
            assert json.loads(request.content)["client_id"] == "sdk-tests"
            return httpx.Response(200, json=self.pair())
        if path == "/api/v1/auth/refresh":
            assert "authorization" not in request.headers
            payload = json.loads(request.content)
            assert payload == {
                "client_id": "sdk-tests",
                "refresh_token": self.pair()["refresh_token"],
            }
            self.rotations += 1
            if self.failure == "transport":
                raise httpx.ReadTimeout(payload["refresh_token"], request=request)
            if self.failure == "rejected":
                return httpx.Response(401, json={"message": payload["refresh_token"]})
            if self.failure == "decode":
                return httpx.Response(200, json={"refresh_token": payload["refresh_token"]})
            pair = self.pair()
            if self.failure == "family":
                pair["session_id"] = str(uuid4())
            if self.failure == "absolute":
                pair["absolute_expires_at"] = (self.absolute + timedelta(days=1)).isoformat()
            if self.failure == "reuse":
                pair["refresh_token"] = payload["refresh_token"]
            return httpx.Response(200, json=pair)
        if path == "/api/v1/auth/logout":
            return httpx.Response(200, json={"message": "Logged out"})
        assert request.headers["authorization"] == "Bearer " + self.pair()["access_token"]
        return httpx.Response(200, json={"ok": True})


async def invoke(client: Client | AsyncClient, name: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(client, name)
    if isinstance(client, AsyncClient):
        return await method(*args, **kwargs)
    return await asyncio.to_thread(method, *args, **kwargs)


@pytest.fixture(params=[Client, AsyncClient], ids=["sync", "async"])
async def session(request: pytest.FixtureRequest) -> Any:
    server = SessionServer()
    client = request.param("https://hubuum.test", transport=httpx.MockTransport(server))
    await invoke(
        client, "login_session", Credentials("alice", "private-password"), client_id="sdk-tests"
    )
    try:
        yield client, server
    finally:
        await invoke(client, "close")


def expire(client: Client | AsyncClient) -> None:
    assert client._session is not None
    client._session = replace(client._session, refresh_at=-1)


async def test_concurrent_calls_rotate_exactly_once(session: Any) -> None:
    client, server = session
    expire(client)
    results = await asyncio.gather(
        *(invoke(client, "request", "GET", "/api/v1/iam/me") for _ in range(20))
    )
    assert results == [{"ok": True}] * 20
    assert server.rotations == 1
    assert client.token.value.endswith("-1")
    assert "private-password" not in repr(client._session)
    assert "refresh-secret" not in repr(client._session)


async def test_fresh_access_does_not_rotate(session: Any) -> None:
    client, server = session
    assert await invoke(client, "request", "GET", "/api/v1/iam/me") == {"ok": True}
    assert server.rotations == 0


@pytest.mark.parametrize(
    ("failure", "error"),
    [
        ("transport", TransportError),
        ("rejected", APIError),
        ("decode", DecodeError),
        ("family", SessionExpiredError),
        ("absolute", SessionExpiredError),
        ("reuse", SessionExpiredError),
    ],
)
async def test_uncertain_or_invalid_refresh_discards_credentials(
    session: Any, failure: str, error: type[Exception]
) -> None:
    client, server = session
    server.failure = failure
    expire(client)
    with pytest.raises(error) as caught:
        await invoke(client, "request", "GET", "/api/v1/iam/me")
    assert "refresh-secret" not in str(caught.value)
    assert "refresh-secret" not in repr(caught.value)
    assert client.token is None
    assert client._session is None
    assert not client.is_authenticated
    assert server.rotations == 1


async def test_expired_refresh_is_discarded_without_network_call(session: Any) -> None:
    client, server = session
    old = client._session
    assert old is not None
    past = datetime.now(UTC) - timedelta(seconds=1)
    response = old.credentials.model_copy(update={"refresh_expires_at": past})
    client._session = replace(old, credentials=response, refresh_at=-1)
    with pytest.raises(SessionExpiredError):
        await invoke(client, "request", "GET", "/api/v1/iam/me")
    assert client.token is None
    assert server.rotations == 0


async def test_logout_refreshes_if_needed_then_revokes_family(session: Any) -> None:
    client, server = session
    expire(client)
    await invoke(client, "logout")
    assert [r.url.path for r in server.requests[-2:]] == [
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
    ]
    assert client.token is None
    assert client._session is None


async def test_stream_refreshes_before_sending_bearer(session: Any) -> None:
    client, server = session
    expire(client)
    if isinstance(client, AsyncClient):
        async with client.stream("GET", "/api/v1/exports") as stream:
            assert b"ok" in b"".join([chunk async for chunk in stream.iter_bytes()])
    else:
        with client.stream("GET", "/api/v1/exports") as stream:
            assert b"ok" in b"".join(stream.iter_bytes())
    assert server.rotations == 1


@pytest.mark.parametrize("client_id", ["", "spaces forbidden", "x" * 129, "nonascii-ø"])
async def test_invalid_client_id_makes_no_request(session: Any, client_id: str) -> None:
    client, server = session
    before = len(server.requests)
    with pytest.raises(ConfigurationError):
        await invoke(client, "login_session", Credentials("alice", "private"), client_id=client_id)
    assert len(server.requests) == before


def test_session_model_serialization_redacts_both_credentials() -> None:
    response = SessionResponse.model_validate(SessionServer().pair())
    for value in [repr(response), str(response), response.model_dump_json()]:
        assert "access-secret" not in value
        assert "refresh-secret" not in value


@pytest.mark.parametrize("invalid", ["deadline", "secret_type", "same_secret", "ordering"])
def test_session_validation_errors_do_not_retain_credentials(invalid: str) -> None:
    payload = SessionServer().pair()
    if invalid == "deadline":
        payload["access_expires_at"] = "secret-in-invalid-date"
    elif invalid == "ordering":
        payload["refresh_expires_at"] = datetime.now(UTC).isoformat()
    elif invalid == "secret_type":
        payload["token_type"] = payload["refresh_token"]
    else:
        payload["access_token"] = payload["refresh_token"]
    with pytest.raises(ValidationError) as caught:
        SessionResponse.model_validate(payload)
    diagnostic = f"{caught.value!s} {caught.value!r} {caught.value.errors()}"
    assert "refresh-secret" not in diagnostic
    assert "access-secret" not in diagnostic
    assert "secret-in-invalid-date" not in diagnostic
    assert caught.value.__context__ is None


def test_session_does_not_retain_unknown_secret_fields() -> None:
    payload = {**SessionServer().pair(), "unexpected_secret": "do-not-retain"}
    response = SessionResponse.model_validate(payload)
    assert "do-not-retain" not in repr(response)
    assert "unexpected_secret" not in response.model_dump()


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_injected_token_logout_uses_versioned_route_when_legacy_is_absent(
    asynchronous: bool,
) -> None:
    paths: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.headers["authorization"] == "Bearer pat-secret"
        return httpx.Response(404 if len(paths) == 1 else 200, json={})

    if asynchronous:
        async with AsyncClient(
            "https://hubuum.test", token="pat-secret", transport=httpx.MockTransport(handle)
        ) as client:
            await client.logout()
            assert not client.is_authenticated
    else:
        with Client(
            "https://hubuum.test", token="pat-secret", transport=httpx.MockTransport(handle)
        ) as sync_client:
            sync_client.logout()
            assert not sync_client.is_authenticated
    assert paths == ["/api/v0/auth/logout", "/api/v1/auth/logout"]
