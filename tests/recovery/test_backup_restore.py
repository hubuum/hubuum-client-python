"""Full restores against the disposable stack owned by run-e2e-tests.sh."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from hubuum_client import (
    AsyncClient,
    AuthenticationError,
    ClassCreate,
    Client,
    CollectionCreate,
    Credentials,
    NotFoundError,
    ObjectCreate,
    ObjectUpdate,
    OpenAPIOptions,
    Task,
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


def _stage_options(stage: dict[str, Any], *, capability: bool = False) -> OpenAPIOptions:
    return OpenAPIOptions(
        path_params={"restore_id": stage["id"]},
        headers={"X-Hubuum-Restore-Capability": stage["restore_capability"]}
        if capability
        else None,
    )


def _confirmation(stage: dict[str, Any]) -> dict[str, str]:
    return {
        "restore_capability": stage["restore_capability"],
        "sha256": stage["sha256"],
        "confirmation": "REPLACE ALL HUBUUM DATA",
    }


def _check_status(status: Any) -> bool:
    if not isinstance(status, dict):
        pytest.fail("restore status must be a JSON object")
    if status["status"] == "failed":
        pytest.fail("the disposable restore executor reported failure")
    return bool(status["status"] == "succeeded")


def _sync_roundtrip(stack: RecoveryStack) -> None:
    prefix = f"recovery-sync-{uuid.uuid4().hex}"
    with Client(stack.base_url) as client:
        client.login(Credentials("admin", stack.reset_password()))
        collection = client.collections.create(
            CollectionCreate(
                name=prefix,
                description="Recovery regression",
                group_id=client.groups.get_by_name("admin").id,
            )
        )
        cls = client.classes.create(
            ClassCreate(name=prefix, collection_id=collection.id, description="Recovery regression")
        )
        objects = client.classes.by_id(cls.id).objects
        original = objects.create(
            ObjectCreate(name=prefix, description="Before backup", data={"phase": "before"})
        )
        nullable = objects.create(
            ObjectCreate(name=f"{prefix}-null", description="JSON null", data={})
        )
        nullable = objects.patch_data(nullable.id, [{"op": "replace", "path": "", "value": None}])
        assert nullable.data is None
        task = Task.model_validate(
            client.openapi.call("postApiV1Backups", json={"include_history": True})
        )
        completed = client.tasks.wait(task.id, timeout_seconds=90, poll_interval=0.2)
        assert completed.status.successful
        backup = client.openapi.call(
            "getApiV1BackupsByTaskIdOutput",
            options=OpenAPIOptions(path_params={"task_id": task.id}),
        )
        assert isinstance(backup, dict)
        assert backup["backup_version"] == 5
        assert backup["history"] is not None
        objects.update(original.id, ObjectUpdate(data={"phase": "after"}))
        objects.update(nullable.id, ObjectUpdate(data={"phase": "after"}))
        extra = objects.create(
            ObjectCreate(name=f"{prefix}-later", description="After backup", data={})
        )
        stage = client.openapi.call("postApiV1Restores", json=backup)
        assert isinstance(stage, dict)
        assert stage["status"] == "validated"
        confirmed = client.openapi.call(
            "postApiV1RestoresByRestoreIdConfirm",
            json=_confirmation(stage),
            options=_stage_options(stage),
        )
        assert isinstance(confirmed, dict)
        assert confirmed["status"] == "confirmed"
        with Client(stack.base_url) as status_client:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if _check_status(
                    status_client.openapi.call(
                        "getApiV1RestoresByRestoreIdStatus",
                        options=_stage_options(stage, capability=True),
                    )
                ):
                    break
                time.sleep(0.2)
            else:
                pytest.fail("disposable restore did not complete within 90 seconds")
        with pytest.raises(AuthenticationError):
            client.me()
        client.login(Credentials("admin", stack.reset_password()))
        restored = objects.get(original.id)
        assert restored.data == original.data
        assert restored.revision == original.revision
        restored_null = objects.get(nullable.id)
        assert restored_null.data is None
        assert restored_null.revision == nullable.revision
        with pytest.raises(NotFoundError):
            objects.get(extra.id)


async def _async_roundtrip(stack: RecoveryStack) -> None:
    prefix = f"recovery-async-{uuid.uuid4().hex}"
    async with AsyncClient(stack.base_url) as client:
        await client.login(Credentials("admin", await asyncio.to_thread(stack.reset_password)))
        group = await client.groups.get_by_name("admin")
        collection = await client.collections.create(
            CollectionCreate(name=prefix, description="Recovery regression", group_id=group.id)
        )
        cls = await client.classes.create(
            ClassCreate(name=prefix, collection_id=collection.id, description="Recovery regression")
        )
        objects = client.classes.by_id(cls.id).objects
        original = await objects.create(
            ObjectCreate(name=prefix, description="Before backup", data={"phase": "before"})
        )
        nullable = await objects.create(
            ObjectCreate(name=f"{prefix}-null", description="JSON null", data={})
        )
        nullable = await objects.patch_data(
            nullable.id, [{"op": "replace", "path": "", "value": None}]
        )
        assert nullable.data is None
        task = Task.model_validate(
            await client.openapi.call("postApiV1Backups", json={"include_history": True})
        )
        completed = await client.tasks.wait(task.id, timeout_seconds=90, poll_interval=0.2)
        assert completed.status.successful
        backup = await client.openapi.call(
            "getApiV1BackupsByTaskIdOutput",
            options=OpenAPIOptions(path_params={"task_id": task.id}),
        )
        assert isinstance(backup, dict)
        assert backup["backup_version"] == 5
        assert backup["history"] is not None
        await objects.update(original.id, ObjectUpdate(data={"phase": "after"}))
        await objects.update(nullable.id, ObjectUpdate(data={"phase": "after"}))
        extra = await objects.create(
            ObjectCreate(name=f"{prefix}-later", description="After backup", data={})
        )
        stage = await client.openapi.call("postApiV1Restores", json=backup)
        assert isinstance(stage, dict)
        assert stage["status"] == "validated"
        confirmed = await client.openapi.call(
            "postApiV1RestoresByRestoreIdConfirm",
            json=_confirmation(stage),
            options=_stage_options(stage),
        )
        assert isinstance(confirmed, dict)
        assert confirmed["status"] == "confirmed"
        async with AsyncClient(stack.base_url) as status_client:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if _check_status(
                    await status_client.openapi.call(
                        "getApiV1RestoresByRestoreIdStatus",
                        options=_stage_options(stage, capability=True),
                    )
                ):
                    break
                await asyncio.sleep(0.2)
            else:
                pytest.fail("disposable restore did not complete within 90 seconds")
        with pytest.raises(AuthenticationError):
            await client.me()
        await client.login(Credentials("admin", await asyncio.to_thread(stack.reset_password)))
        restored = await objects.get(original.id)
        assert restored.data == original.data
        assert restored.revision == original.revision
        restored_null = await objects.get(nullable.id)
        assert restored_null.data is None
        assert restored_null.revision == nullable.revision
        with pytest.raises(NotFoundError):
            await objects.get(extra.id)


@pytest.mark.parametrize("async_first", [False, True], ids=["sync-then-async", "async-then-sync"])
def test_repeated_full_restores(recovery_stack: RecoveryStack, async_first: bool) -> None:
    if async_first:
        asyncio.run(_async_roundtrip(recovery_stack))
        _sync_roundtrip(recovery_stack)
    else:
        _sync_roundtrip(recovery_stack)
        asyncio.run(_async_roundtrip(recovery_stack))
