"""Full restores against the disposable stack owned by run-e2e-tests.sh."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from hubuum_client import (
    AsyncClient,
    AuthenticationError,
    BackupRequest,
    ClassCreate,
    Client,
    CollectionCreate,
    ConfirmRestoreOperation,
    CredentialApprovalRequest,
    Credentials,
    NotFoundError,
    ObjectCreate,
    ObjectUpdate,
    RestoreConfirmRequest,
    RestoreJobId,
)

pytestmark = pytest.mark.e2e


@dataclass(frozen=True)
class RecoveryStack:
    runtime: str
    server_container: str
    base_url: str

    def reset_password(self) -> str:
        result = subprocess.run(
            [
                self.runtime,
                "exec",
                self.server_container,
                "hubuum-admin",
                "--reset-password",
                "admin",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Password for user admin reset to: "):
                    return line.removeprefix("Password for user admin reset to: ")
        pytest.fail("could not reset the disposable recovery administrator password")


@pytest.fixture(scope="module")
def recovery_stack() -> RecoveryStack:
    server = os.environ.get("HUBUUM_E2E_RECOVERY_SERVER_CONTAINER", "")
    if not server.startswith("hubuum-python-e2e-server-"):
        pytest.fail("full restores require the disposable stack from scripts/run-e2e-tests.sh")
    runtime_name = os.environ.get("HUBUUM_E2E_CONTAINER_RUNTIME", "")
    if runtime_name not in {"docker", "podman"}:
        pytest.fail("the e2e wrapper must select Docker or Podman for recovery tests")
    runtime = shutil.which(runtime_name)
    if runtime is None:
        pytest.fail("the selected container runtime is unavailable")
    result = subprocess.run(
        [runtime, "port", server, "8080/tcp"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        pytest.fail("could not identify the disposable recovery server port")
    port = result.stdout.strip().rsplit(":", 1)[-1]
    base_url = f"http://127.0.0.1:{port}"
    if not port.isdecimal() or base_url != os.environ.get("HUBUUM_E2E_BASE_URL"):
        pytest.fail("recovery URL does not match the disposable server container")
    return RecoveryStack(runtime, server, base_url)


def _confirmation(stage: dict[str, Any]) -> dict[str, str]:
    return {
        "restore_capability": stage["restore_capability"],
        "sha256": stage["sha256"],
        "confirmation": "REPLACE ALL HUBUUM DATA",
    }


def _validated_stage(value: Any) -> dict[str, Any]:
    assert isinstance(value, dict)
    assert value["status"] == "validated"
    return value


def _sync_roundtrip(stack: RecoveryStack, *, include_history: bool | None = None) -> None:
    prefix = f"recovery-sync-{uuid.uuid4().hex}"
    with Client(stack.base_url) as client:
        password = stack.reset_password()
        client.login_session(Credentials("admin", password))
        collection = client.collections.create(
            CollectionCreate(
                name=prefix,
                description="Recovery regression",
                group_id=client.groups.get_by_name("admin").id,
            )
        )
        cls = client.classes.create(
            ClassCreate(
                name=prefix,
                collection_id=collection.id,
                description="Recovery regression",
                json_schema={"type": ["object", "null"]},
                validate_schema=True,
            )
        )
        objects = client.classes.by_id(cls.id).objects
        original = objects.create(
            ObjectCreate(name=prefix, description="Before backup", data={"phase": "before"})
        )
        original = objects.update(original.id, ObjectUpdate(description="Revised before backup"))
        nullable = objects.create(
            ObjectCreate(name=f"{prefix}-null", description="JSON null", data={})
        )
        nullable = objects.patch_data(nullable.id, [{"op": "replace", "path": "", "value": None}])
        assert nullable.data is None
        backup = client.backups.run(
            BackupRequest()
            if include_history is None
            else BackupRequest(include_history=include_history),
            timeout_seconds=90,
            poll_interval=0.2,
        )
        assert backup.backup_version == 10
        assert (backup.history is not None) is (include_history is not False)
        objects.update(original.id, ObjectUpdate(data={"phase": "after"}))
        objects.update(nullable.id, ObjectUpdate(data={"phase": "after"}))
        extra = objects.create(
            ObjectCreate(name=f"{prefix}-later", description="After backup", data={})
        )
        stage = _validated_stage((client.restores.stage(backup)).wire_payload())
        approval = client.credential_approvals.create(
            CredentialApprovalRequest(
                password=password,
                operation=ConfirmRestoreOperation(
                    restore_id=RestoreJobId(stage["id"]),
                    confirmation=RestoreConfirmRequest.model_validate(_confirmation(stage)),
                ),
            )
        )
        confirmed = client.restores.confirm(
            RestoreJobId(stage["id"]),
            RestoreConfirmRequest.model_validate(_confirmation(stage)),
            credential_approval=approval.approval,
        )
        assert confirmed.status == "confirmed"
        # Keep the now-invalid bearer session installed: capability polling must
        # neither refresh it nor send it to the restore-status route.
        completed = client.restores.wait(
            RestoreJobId(stage["id"]),
            capability=stage["restore_capability"],
            timeout_seconds=90,
            poll_interval=0.2,
        )
        assert completed.status == "succeeded"
        with pytest.raises(AuthenticationError):
            client.me()
        client.login_session(Credentials("admin", stack.reset_password()))
        assert client.classes.by_id(cls.id).schema.get().active.json_schema == cls.json_schema
        restored = objects.get(original.id)
        assert restored.data == original.data
        assert restored.revision == original.revision
        restored_null = objects.get(nullable.id)
        assert restored_null.data is None
        assert restored_null.revision == nullable.revision
        with pytest.raises(NotFoundError):
            objects.get(extra.id)
        mutated = objects.update(restored.id, ObjectUpdate(data={"phase": "after restore"}))
        assert mutated.revision == original.revision + 1


async def _async_roundtrip(stack: RecoveryStack, *, include_history: bool | None = None) -> None:
    prefix = f"recovery-async-{uuid.uuid4().hex}"
    async with AsyncClient(stack.base_url) as client:
        password = await asyncio.to_thread(stack.reset_password)
        await client.login_session(Credentials("admin", password))
        group = await client.groups.get_by_name("admin")
        collection = await client.collections.create(
            CollectionCreate(name=prefix, description="Recovery regression", group_id=group.id)
        )
        cls = await client.classes.create(
            ClassCreate(
                name=prefix,
                collection_id=collection.id,
                description="Recovery regression",
                json_schema={"type": ["object", "null"]},
                validate_schema=True,
            )
        )
        objects = client.classes.by_id(cls.id).objects
        original = await objects.create(
            ObjectCreate(name=prefix, description="Before backup", data={"phase": "before"})
        )
        original = await objects.update(
            original.id, ObjectUpdate(description="Revised before backup")
        )
        nullable = await objects.create(
            ObjectCreate(name=f"{prefix}-null", description="JSON null", data={})
        )
        nullable = await objects.patch_data(
            nullable.id, [{"op": "replace", "path": "", "value": None}]
        )
        assert nullable.data is None
        backup = await client.backups.run(
            BackupRequest()
            if include_history is None
            else BackupRequest(include_history=include_history),
            timeout_seconds=90,
            poll_interval=0.2,
        )
        assert backup.backup_version == 10
        assert (backup.history is not None) is (include_history is not False)
        await objects.update(original.id, ObjectUpdate(data={"phase": "after"}))
        await objects.update(nullable.id, ObjectUpdate(data={"phase": "after"}))
        extra = await objects.create(
            ObjectCreate(name=f"{prefix}-later", description="After backup", data={})
        )
        stage = _validated_stage((await client.restores.stage(backup)).wire_payload())
        approval = await client.credential_approvals.create(
            CredentialApprovalRequest(
                password=password,
                operation=ConfirmRestoreOperation(
                    restore_id=RestoreJobId(stage["id"]),
                    confirmation=RestoreConfirmRequest.model_validate(_confirmation(stage)),
                ),
            )
        )
        confirmed = await client.restores.confirm(
            RestoreJobId(stage["id"]),
            RestoreConfirmRequest.model_validate(_confirmation(stage)),
            credential_approval=approval.approval,
        )
        assert confirmed.status == "confirmed"
        # Keep the now-invalid bearer session installed: capability polling must
        # neither refresh it nor send it to the restore-status route.
        completed = await client.restores.wait(
            RestoreJobId(stage["id"]),
            capability=stage["restore_capability"],
            timeout_seconds=90,
            poll_interval=0.2,
        )
        assert completed.status == "succeeded"
        with pytest.raises(AuthenticationError):
            await client.me()
        await client.login_session(
            Credentials("admin", await asyncio.to_thread(stack.reset_password))
        )
        assert (
            await client.classes.by_id(cls.id).schema.get()
        ).active.json_schema == cls.json_schema
        restored = await objects.get(original.id)
        assert restored.data == original.data
        assert restored.revision == original.revision
        restored_null = await objects.get(nullable.id)
        assert restored_null.data is None
        assert restored_null.revision == nullable.revision
        with pytest.raises(NotFoundError):
            await objects.get(extra.id)
        mutated = await objects.update(restored.id, ObjectUpdate(data={"phase": "after restore"}))
        assert mutated.revision == original.revision + 1


@pytest.mark.parametrize("async_first", [False, True], ids=["sync-then-async", "async-then-sync"])
@pytest.mark.parametrize("include_history", [True, False], ids=["history", "history-free"])
def test_repeated_full_restores(
    recovery_stack: RecoveryStack, async_first: bool, include_history: bool
) -> None:
    if async_first:
        asyncio.run(_async_roundtrip(recovery_stack, include_history=include_history))
        _sync_roundtrip(recovery_stack)
    else:
        _sync_roundtrip(recovery_stack, include_history=include_history)
        asyncio.run(_async_roundtrip(recovery_stack))
