from __future__ import annotations

import pytest

from hubuum_client import (
    Client,
    NotFoundError,
    PreconditionFailedError,
    RuntimeSettingsPatch,
    RuntimeSettingsRelease,
)


def test_discovered_runtime_setting_round_trip(client: Client) -> None:
    try:
        catalogue = client.admin.runtime_settings_schema()
    except NotFoundError:
        pytest.skip("Runtime settings discovery is optional on the pinned server")
    assert catalogue.schema_version == 1
    original = client.admin.runtime_settings_group("pagination")
    assert original.revision is not None
    next_limit = 76 if original.effective["default_page_limit"] == 75 else 75
    patch = RuntimeSettingsPatch(
        expected_revision=original.revision, changes={"default_page_limit": next_limit}
    )
    updated = client.admin.patch_runtime_settings("pagination", patch)
    try:
        assert (
            client.admin.runtime_settings_group("pagination").effective["default_page_limit"]
            == next_limit
        )
        with pytest.raises(PreconditionFailedError):
            client.admin.patch_runtime_settings("pagination", patch)
    finally:
        if original.source == "deployment":
            client.admin.release_runtime_settings(
                "pagination", RuntimeSettingsRelease(expected_revision=updated.committed_revision)
            )
        else:
            assert original.runtime is not None
            client.admin.patch_runtime_settings(
                "pagination",
                RuntimeSettingsPatch(
                    expected_revision=updated.committed_revision, changes=original.runtime
                ),
            )
