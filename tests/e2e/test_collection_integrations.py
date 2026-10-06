from __future__ import annotations

import inspect
import os
from collections.abc import Awaitable
from typing import TypeVar

import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    CollectionCreate,
    CreateUserOperation,
    CredentialApprovalRequest,
    Credentials,
    EventSinkCreate,
    EventSinkUpdate,
    EventSubscriptionCreate,
    GroupCreate,
    PermissionDeniedError,
    PrincipalId,
    UserCreate,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("HUBUUM_E2E_COLLECTION_INTEGRATIONS") != "1",
        reason="Collection integrations require the updated server after v0.0.17",
    ),
]
T = TypeVar("T")


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_delegated_webhook_lifecycle(
    client: Client, admin_password: str, unique_name: str, asynchronous: bool
) -> None:
    password = f"{unique_name}-Passw0rd!"
    request = UserCreate(name=unique_name, password=password)
    approval = client.credential_approvals.create(
        CredentialApprovalRequest(
            password=admin_password, operation=CreateUserOperation(user=request)
        )
    )
    user = client.users.create(request, approval=approval)
    group = None
    collection = None
    delegated = (AsyncClient if asynchronous else Client)(client.base_url)
    try:
        group = client.groups.create(GroupCreate(groupname=unique_name))
        client.groups.add_member(group.id, PrincipalId(user.id))
        collection = client.collections.create(
            CollectionCreate(name=unique_name, description="Delegated webhooks", group_id=group.id)
        )
        await resolve(delegated.login(Credentials(unique_name, password)))
        with pytest.raises(PermissionDeniedError):
            await resolve(delegated.event_sinks.list())
        sinks = delegated.collections.event_sinks(collection.id)
        sink = await resolve(
            sinks.create(
                EventSinkCreate(
                    name=unique_name,
                    kind="webhook",
                    config={"destination_url": "https://example.test/private-token"},
                    enabled=False,
                )
            )
        )
        assert sink.collection_id == collection.id
        assert sink.routing == "fixed"
        assert "private-token" not in repr(sink)
        assert len(await resolve(sinks.list())) == 1
        assert (await resolve(sinks.get(sink.id))).id == sink.id
        await resolve(sinks.update(sink.id, EventSinkUpdate(name=f"{unique_name}-updated")))
        subscriptions = delegated.collections.event_subscriptions(collection.id)
        subscription = await resolve(
            subscriptions.create(
                EventSubscriptionCreate(
                    name=unique_name,
                    sink_id=sink.id,
                    entity_types=("object",),
                    actions=("updated",),
                    enabled=False,
                )
            )
        )
        await resolve(subscriptions.delete(subscription.id))
        await resolve(sinks.delete(sink.id))
    finally:
        await resolve(delegated.close())
        if collection is not None:
            client.collections.delete(collection.id)
        if group is not None:
            client.groups.delete(group.id)
        client.users.delete(user.id)
