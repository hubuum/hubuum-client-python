from __future__ import annotations

import inspect
import sys
from collections.abc import Awaitable
from datetime import UTC, timedelta
from typing import TypeVar

import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    CreateUserOperation,
    CredentialApprovalRequest,
    ImportCredentialsOperation,
    ImportGraph,
    ImportRequest,
    ReauthenticationRequiredError,
    RequestOptions,
    Task,
    TaskKind,
    TaskQuery,
    TaskStatus,
    UpdateUserOperation,
    UserCreate,
    UserUpdate,
)

pytestmark = pytest.mark.e2e
T = TypeVar("T")


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


async def _user_etag(api: Client | AsyncClient, user_id: int) -> str:
    path = f"/api/v1/iam/users/{user_id}"
    if isinstance(api, AsyncClient):
        async with api.stream("GET", path) as response:
            return response.headers["etag"]
    with api.stream("GET", path) as response:
        return response.headers["etag"]


def _discovery_query(task: Task) -> TaskQuery:
    # Use the server's timestamp, avoiding clock skew and unrelated task history.
    created_at = task.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return TaskQuery(
        kind=(TaskKind.IMPORT,),
        status=(TaskStatus.SUCCEEDED,),
        terminal=True,
        import_dry_run=True,
        submitted_by=task.submitted_by,
        created_after=created_at,
        created_before=created_at + timedelta(microseconds=1),
    )


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_approved_user_creation_and_password_update(
    client: Client,
    admin_password: str,
    unique_name: str,
    asynchronous: bool,
) -> None:
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    user_id = None
    try:
        payload = UserCreate(name=unique_name, password=f"{unique_name}-Passw0rd!")
        with pytest.raises(ReauthenticationRequiredError):
            await _resolve(api.users.create(payload))
        approval = await _resolve(
            api.credential_approvals.create(
                CredentialApprovalRequest(
                    password=admin_password, operation=CreateUserOperation(user=payload)
                )
            )
        )
        user = await _resolve(api.users.create(payload, approval=approval))
        user_id = user.id
        assert (await _resolve(api.credential_approvals.get(approval.record.id))).consumed_at
        profile = await _resolve(
            api.users.update(user.id, UserUpdate(proper_name="Updated profile"))
        )
        changed = UserUpdate(password=f"{unique_name}-New-Passw0rd!")
        with pytest.raises(ReauthenticationRequiredError):
            await _resolve(api.users.update(user.id, changed))
        approval = await _resolve(
            api.credential_approvals.create(
                CredentialApprovalRequest(
                    password=admin_password,
                    operation=UpdateUserOperation(user_id=user.id, user=changed),
                )
            )
        )
        updated = await _resolve(
            api.users.update(
                user.id,
                changed,
                approval=approval,
                options=RequestOptions(headers={"If-Match": await _user_etag(api, user.id)}),
            )
        )
        assert updated.revision > profile.revision
    finally:
        failing = sys.exc_info()[0] is not None
        try:
            if user_id is not None:
                await _resolve(api.users.delete(user_id))
        except Exception:
            if not failing:
                raise
        finally:
            if isinstance(api, AsyncClient):
                await api.close()


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_credential_import_dry_run_and_task_discovery(
    client: Client,
    admin_password: str,
    unique_name: str,
    asynchronous: bool,
) -> None:
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    try:
        payload = ImportRequest(
            dry_run=True,
            graph=ImportGraph(
                principals=(
                    {
                        "kind": "human",
                        "name": unique_name,
                        "provider_managed": False,
                        "identity_scope_key": {"name": "local"},
                        "password": f"{unique_name}-Passw0rd!",
                    },
                )
            ),
        )
        with pytest.raises(ReauthenticationRequiredError):
            await _resolve(api.imports.submit(payload))
        approval = await _resolve(
            api.credential_approvals.create(
                CredentialApprovalRequest(
                    password=admin_password, operation=ImportCredentialsOperation(import_=payload)
                )
            )
        )
        result = await _resolve(
            api.imports.run(
                payload,
                approval=approval,
                idempotency_key=unique_name,
                timeout_seconds=60,
                poll_interval=0.1,
            )
        )
        assert result.task.status is TaskStatus.SUCCEEDED
        repeated = await _resolve(
            api.imports.submit(payload, approval=approval, idempotency_key=unique_name)
        )
        assert repeated.id == result.task.id
        assert (await _resolve(api.credential_approvals.get(approval.record.id))).consumed_at
        query = _discovery_query(result.task)
        tasks = await _resolve(api.tasks.all(query.limit(1).include_total().sort("id.asc")))
        selected = next(task for task in tasks if task.id == result.task.id)
        assert selected.details is not None
        assert selected.details.import_ is not None
        assert selected.details.import_.retained is not None
        assert selected.details.import_.retained.dry_run is True
        assert selected.details.import_.retained.has_failed_items is False
    finally:
        if isinstance(api, AsyncClient):
            await api.close()
