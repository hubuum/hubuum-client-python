from __future__ import annotations

import inspect
import sys
from collections.abc import Awaitable
from typing import TypeVar

import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    CollectionCreate,
    EventSinkId,
    GroupId,
    NotFoundError,
    OpenAPIOptions,
)

pytestmark = pytest.mark.e2e
T = TypeVar("T")


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_notification_preview_test_and_system_subscriptions(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
    asynchronous: bool,
) -> None:
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    cleanup: list[tuple[str, OpenAPIOptions]] = []
    try:
        sink = await _resolve(
            api.openapi.call(
                "postApiV1EventSinks",
                json={
                    "name": unique_name,
                    "kind": "webhook",
                    "config": {
                        # No worker can send a message without this nonexistent secret.
                        "url_secret_ref": unique_name,
                        "body_template": '{"text": {{ (test_marker ~ summary) | tojson }}}',
                        "response": {"success_statuses": [200], "rate_limit": True},
                    },
                    "delivery_policy": {"min_interval_ms": 1000},
                    "enabled": False,
                },
            )
        )
        assert isinstance(sink, dict)
        sink_options = OpenAPIOptions(path_params={"sink_id": sink["id"]})
        cleanup.append(("deleteApiV1EventSinksBySinkId", sink_options))
        assert sink["delivery_policy"] == {"min_interval_ms": 1000}

        system = await _resolve(
            api.openapi.call(
                "postApiV1SystemEventSubscriptions",
                json={
                    "sink_id": sink["id"],
                    "name": unique_name,
                    "entity_types": ["task"],
                    "actions": ["failed"],
                    "filter": {"task_kinds": ["backup"]},
                    "enabled": False,
                },
            )
        )
        assert isinstance(system, dict)
        system_options = OpenAPIOptions(path_params={"subscription_id": system["id"]})
        cleanup.append(("deleteApiV1SystemEventSubscriptionsBySubscriptionId", system_options))
        await _check_system_subscription(api, system["id"])

        collection = await _resolve(
            api.collections.create(
                CollectionCreate(
                    name=unique_name,
                    description="Notification source",
                    group_id=admin_group_id,
                )
            )
        )
        collection_options = OpenAPIOptions(path_params={"collection_id": collection.id})
        cleanup.append(("deleteApiV1CollectionsByCollectionId", collection_options))
        await _resolve(api.event_sinks.grant(EventSinkId(sink["id"]), collection.id))
        subscription = await _resolve(
            api.openapi.call(
                "postApiV1CollectionsByCollectionIdEventSubscriptions",
                json={
                    "sink_id": sink["id"],
                    "name": unique_name,
                    "entity_types": ["collection"],
                    "actions": ["created"],
                    "enabled": False,
                },
                options=collection_options,
            )
        )
        assert isinstance(subscription, dict)
        cleanup.append(
            (
                "deleteApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
                OpenAPIOptions(
                    path_params={
                        "collection_id": collection.id,
                        "subscription_id": subscription["id"],
                    }
                ),
            )
        )
        events = await _resolve(
            api.openapi.call("getApiV1CollectionsByCollectionIdEvents", options=collection_options)
        )
        assert isinstance(events, list)
        event = next(item for item in events if item["action"] == "created")
        source = {"subscription_id": subscription["id"], "event_id": event["event_id"]}
        preview = await _resolve(
            api.openapi.call(
                "postApiV1EventSinksBySinkIdPreview", json=source, options=sink_options
            )
        )
        assert isinstance(preview, dict)
        assert preview["sink_kind"] == "webhook"
        assert preview["payload"]["text"] == "[TEST] " + event["summary"]
        delivery = await _resolve(
            api.openapi.call("postApiV1EventSinksBySinkIdTest", json=source, options=sink_options)
        )
        assert isinstance(delivery, dict)
        assert delivery["purpose"] == "test"
        assert delivery["subscription_id"] == subscription["id"]

        await _resolve(
            api.openapi.call(
                "deleteApiV1SystemEventSubscriptionsBySubscriptionId", options=system_options
            )
        )
        cleanup.remove(("deleteApiV1SystemEventSubscriptionsBySubscriptionId", system_options))
        with pytest.raises(NotFoundError):
            await _resolve(
                api.openapi.call(
                    "getApiV1SystemEventSubscriptionsBySubscriptionId", options=system_options
                )
            )
    finally:
        primary_failure = sys.exc_info()[0] is not None
        cleanup_error: Exception | None = None
        for operation_id, options in reversed(cleanup):
            try:
                await _resolve(api.openapi.call(operation_id, options=options))
            except Exception as error:
                cleanup_error = error
        if asynchronous:
            await _resolve(api.close())
        if cleanup_error is not None and not primary_failure:
            raise cleanup_error


async def _check_system_subscription(api: Client | AsyncClient, system_id: int) -> None:
    system_options = OpenAPIOptions(path_params={"subscription_id": system_id})
    fetched = await _resolve(
        api.openapi.call("getApiV1SystemEventSubscriptionsBySubscriptionId", options=system_options)
    )
    assert isinstance(fetched, dict)
    assert fetched["id"] == system_id
    listed = await _resolve(api.openapi.call("getApiV1SystemEventSubscriptions"))
    assert isinstance(listed, list)
    assert fetched in listed
    updated = await _resolve(
        api.openapi.call(
            "patchApiV1SystemEventSubscriptionsBySubscriptionId",
            json={"description": "Failed backup notifications"},
            options=system_options,
        )
    )
    assert isinstance(updated, dict)
    assert updated["description"] == "Failed backup notifications"
    assert updated["filter"]["task_kinds"] == ["backup"]
    health = await _resolve(api.openapi.call("getApiV1EventDeliveriesHealth"))
    assert isinstance(health, dict)
    entry = next(item for item in health["subscriptions"] if item["subscription_id"] == system_id)
    assert entry["collection_id"] is None
