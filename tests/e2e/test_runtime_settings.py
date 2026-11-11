from __future__ import annotations

import inspect
from typing import Any

import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    Credentials,
    PreconditionFailedError,
    RuntimeSettingsPatch,
    RuntimeSettingsRelease,
)

pytestmark = pytest.mark.e2e


async def resolve(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
async def test_discovered_runtime_setting_round_trip(
    base_url: str, admin_password: str, asynchronous: bool
) -> None:
    client = (AsyncClient if asynchronous else Client)(base_url)
    try:
        await resolve(client.login_session(Credentials("admin", admin_password)))
        catalogue = await resolve(client.admin.runtime_settings_schema())
        assert catalogue.schema_version == 1
        group = next(group for group in catalogue.groups if group.key == "pagination")
        assert group.patch_supported
        assert group.value_schema["properties"]["default_page_limit"]["description"]
        original = await resolve(client.admin.runtime_settings_group("pagination"))
        assert original.revision is not None
        next_limit = 76 if original.effective["default_page_limit"] == 75 else 75
        patch = RuntimeSettingsPatch(
            expected_revision=original.revision, changes={"default_page_limit": next_limit}
        )
        updated = await resolve(client.admin.patch_runtime_settings("pagination", patch))
        try:
            state = await resolve(client.admin.runtime_settings_group("pagination"))
            assert state.effective["default_page_limit"] == next_limit
            assert state.revision == updated.committed_revision
            with pytest.raises(PreconditionFailedError):
                await resolve(client.admin.patch_runtime_settings("pagination", patch))
        finally:
            if original.source == "deployment":
                await resolve(
                    client.admin.release_runtime_settings(
                        "pagination",
                        RuntimeSettingsRelease(expected_revision=updated.committed_revision),
                    )
                )
            else:
                assert original.runtime is not None
                await resolve(
                    client.admin.patch_runtime_settings(
                        "pagination",
                        RuntimeSettingsPatch(
                            expected_revision=updated.committed_revision, changes=original.runtime
                        ),
                    )
                )
        restored = await resolve(client.admin.runtime_settings_group("pagination"))
        assert restored.source == original.source
        assert restored.effective == original.effective
    finally:
        await resolve(client.close())
