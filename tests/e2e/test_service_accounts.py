from __future__ import annotations

import inspect
import sys
from collections.abc import Awaitable
from typing import TypeVar

import pytest

from hubuum_client import (
    AsyncClient,
    AuthenticationError,
    Client,
    CreateTokenOperation,
    CredentialApprovalRequest,
    FilterOperator,
    GroupCreate,
    GroupId,
    NewTokenRequest,
    NotFoundError,
    PreconditionFailedError,
    Query,
    ServiceAccountCreate,
    ServiceAccountId,
    ServiceAccountPoint,
    ServiceAccountUpdate,
)

pytestmark = pytest.mark.e2e
T = TypeVar("T")


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


async def _assert_disable_revokes_token(
    api: Client | AsyncClient, account: ServiceAccountPoint, password: str, token_name: str
) -> None:
    tokens = api.tokens.for_principal(account.principal_id)
    request = NewTokenRequest(name=token_name)
    approval = await _resolve(
        api.credential_approvals.create(
            CredentialApprovalRequest(
                password=password,
                operation=CreateTokenOperation(principal_id=account.principal_id, token=request),
            )
        )
    )
    token = await _resolve(tokens.create(request, approval=approval))
    bearer = (AsyncClient if isinstance(api, AsyncClient) else Client)(api.base_url, token=token)
    try:
        assert (await _resolve(bearer.me())).principal.principal_id == account.principal_id
        disabled = await _resolve(api.service_accounts.disable(account.id))
        assert disabled.disabled_at is not None
        assert disabled.revision > account.revision
        assert (await _resolve(api.service_accounts.get(account.id))).disabled_at is not None
        with pytest.raises(AuthenticationError):
            await _resolve(bearer.me())
    finally:
        await _resolve(bearer.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_service_account_lifecycle(
    client: Client, admin_password: str, unique_name: str, asynchronous: bool
) -> None:
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    account_ids: list[ServiceAccountId] = []
    group_ids: list[GroupId] = []
    try:
        for suffix in ("owner", "new-owner"):
            group = await _resolve(
                api.groups.create(GroupCreate(groupname=f"{unique_name}-{suffix}"))
            )
            group_ids.append(group.id)
        for suffix in ("a", "b"):
            account = await _resolve(
                api.service_accounts.create(
                    ServiceAccountCreate(
                        name=f"{unique_name}-{suffix}",
                        owner_group_id=group_ids[0],
                        identity_scope="local",
                    )
                )
            )
            account_ids.append(account.id)
        listed = await _resolve(
            api.service_accounts.all(
                Query()
                .where("name", unique_name, FilterOperator.STARTSWITH)
                .sort("id.asc")
                .limit(1)
            )
        )
        assert [item.id for item in listed] == account_ids
        assert all(item.identity_scope == "local" for item in listed)
        account = await _resolve(api.service_accounts.get(account_ids[0]))
        found = await _resolve(
            api.service_accounts.get_by_name(account.name, identity_scope="local")
        )
        assert found.principal_id == account.principal_id == account.id
        assert account.identity_scope_id > 0
        tagged = await _resolve(api.api.service_accounts.get(account.id))
        assert tagged.etag
        updated = await _resolve(
            api.service_accounts.update(
                account.id,
                ServiceAccountUpdate(description="Updated", owner_group_id=group_ids[1]),
                if_match=tagged.etag,
            )
        )
        assert updated.owner_group_id == group_ids[1]
        assert updated.description == "Updated"
        assert updated.revision > account.revision
        with pytest.raises(PreconditionFailedError):
            await _resolve(api.service_accounts.disable(account.id, if_match=tagged.etag))

        await _assert_disable_revokes_token(api, updated, admin_password, f"{unique_name}-token")
        await _resolve(api.service_accounts.delete(account.id))
        account_ids.remove(account.id)
        with pytest.raises(NotFoundError):
            await _resolve(api.service_accounts.get(account.id))
    finally:
        failing = sys.exc_info()[0] is not None
        try:
            for account_id in account_ids:
                try:
                    await _resolve(api.service_accounts.delete(account_id))
                except Exception:
                    if not failing:
                        raise
            for group_id in reversed(group_ids):
                try:
                    await _resolve(api.groups.delete(group_id))
                except Exception:
                    if not failing:
                        raise
        finally:
            if isinstance(api, AsyncClient):
                await api.close()
