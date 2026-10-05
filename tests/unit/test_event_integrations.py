from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable
from typing import TypeVar

import httpx
import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    EventSinkCreate,
    EventSinkId,
    EventSinkUpdate,
    EventSubscriptionCreate,
    EventSubscriptionUpdate,
    PermissionDeniedError,
)

T = TypeVar("T")


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


SINK = {
    "id": 5,
    "name": "notifications",
    "kind": "webhook",
    "enabled": True,
    "collection_id": 7,
    "revision": 1,
    "routing": "fixed",
}
SUBSCRIPTION = {
    "id": 8,
    "name": "changes",
    "sink_id": 5,
    "collection_id": 7,
    "revision": 1,
    "entity_types": ["object"],
    "actions": ["updated"],
    "enabled": True,
    "created_at": "2026-10-05T00:00:00Z",
    "updated_at": "2026-10-05T00:00:00Z",
}


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_collection_webhook_and_subscription_workflow(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method in {"DELETE", "PUT"}:
            return httpx.Response(204)
        if request.url.path.endswith("/collections"):
            return httpx.Response(200, json=[7])
        body = SUBSCRIPTION if "event-subscriptions" in request.url.path else SINK
        if request.method == "GET" and request.url.path.endswith(
            ("/event-sinks", "/event-subscriptions")
        ):
            return httpx.Response(200, json=[body], headers={"X-Total-Count": "1"})
        return httpx.Response(201 if request.method == "POST" else 200, json=body)

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    )
    try:
        sinks = client.collections.event_sinks(7)
        payload = EventSinkCreate(
            name="notifications",
            kind="webhook",
            config={"destination_url": "https://example.test/private-token"},
        )
        assert "private-token" not in repr(payload)
        created = await resolve(sinks.create(payload))
        assert created.id == 5
        assert (await resolve(sinks.page())).total_count == 1
        assert (await resolve(sinks.get(5))).collection_id == 7
        await resolve(sinks.update(5, EventSinkUpdate(enabled=False)))
        subscriptions = client.collections.event_subscriptions(7)
        await resolve(
            subscriptions.create(
                EventSubscriptionCreate(
                    sink_id=EventSinkId(5),
                    name="changes",
                    entity_types=("object",),
                    actions=("updated",),
                )
            )
        )
        assert (await resolve(subscriptions.page()))[0].id == 8
        await resolve(subscriptions.get(8))
        await resolve(subscriptions.update(8, EventSubscriptionUpdate(enabled=False)))
        await resolve(subscriptions.delete(8))
        await resolve(sinks.delete(5))
        await resolve(client.event_sinks.grant(12, 7))
        assert await resolve(client.event_sinks.collections(12)) == [7]
        await resolve(client.event_sinks.revoke(12, 7))
    finally:
        if isinstance(client, AsyncClient):
            await client.close()
        else:
            client.close()
    assert all(request.url.path != "/api/v1/event-sinks" for request in requests)
    assert (
        json.loads(requests[0].content)["config"]["destination_url"]
        == "https://example.test/private-token"
    )
    assert [(request.method, request.url.path) for request in requests[-3:]] == [
        ("PUT", "/api/v1/event-sinks/12/collections/7"),
        ("GET", "/api/v1/event-sinks/12/collections"),
        ("DELETE", "/api/v1/event-sinks/12/collections/7"),
    ]


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_collection_discovery_does_not_fall_back_to_admin_endpoint(
    asynchronous: bool,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(403, json={"message": "Permission denied"})

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handler)
    )
    try:
        with pytest.raises(PermissionDeniedError):
            await resolve(client.collections.event_sinks(7).page())
    finally:
        if isinstance(client, AsyncClient):
            await client.close()
        else:
            client.close()
    assert [request.url.path for request in requests] == ["/api/v1/collections/7/event-sinks"]
