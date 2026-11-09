from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable
from typing import TypeVar

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    AsyncClient,
    Client,
    PreconditionFailedError,
    RuntimeSettingsPatch,
    RuntimeSettingsRelease,
)

T = TypeVar("T")


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


CATALOGUE = {
    "schema_version": 1,
    "groups": [
        {
            "key": "future_policy",
            "title": "Future policy",
            "description": "Added later",
            "schema": {
                "type": "object",
                "properties": {
                    "new_option": {
                        "type": "integer",
                        "title": "New option",
                        "description": "Controls a future limit.",
                        "x-unit": "items",
                        "x-future": True,
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["fast"],
                        "x-enum-descriptions": {"fast": "Prefer speed with more resource use."},
                    },
                },
            },
            "patch_supported": True,
            "requires_local_admin": False,
            "takes_effect": "next_request",
            "read_only_reason": None,
        }
    ],
}
STATE = {
    "group": "future_policy",
    "source": "runtime",
    "revision": 4,
    "mutable": True,
    "restart_required": False,
    "takes_effect": "next_request",
    "replica": {"status": "current"},
    "effective": {"new_option": 5, "unknown": 7},
    "runtime": {"new_option": 5, "unknown": 7},
    "deployment": None,
    "constrained_by_ceiling": False,
}
UPDATE = {
    "group": "future_policy",
    "committed_revision": 5,
    "changed": True,
    "applied_by_responding_replica": False,
    "settings": {},
}


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_discovered_future_fields_can_be_edited_without_replacing_unknowns(
    asynchronous: bool,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer test-token"
        if request.url.path.endswith("/schema"):
            return httpx.Response(200, json=CATALOGUE)
        if request.method == "GET":
            return httpx.Response(200, json=STATE)
        assert json.loads(request.content) == {
            "expected_revision": 4,
            "changes": {"new_option": 10},
        }
        return httpx.Response(200, json=UPDATE)

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="test-token", transport=httpx.MockTransport(handler))
    try:
        catalogue = await resolve(client.admin.runtime_settings_schema())
        group = catalogue.groups[0]
        assert group.value_schema["properties"] == {
            "new_option": {
                "type": "integer",
                "title": "New option",
                "description": "Controls a future limit.",
                "x-unit": "items",
                "x-future": True,
            },
            "mode": {
                "type": "string",
                "enum": ["fast"],
                "x-enum-descriptions": {"fast": "Prefer speed with more resource use."},
            },
        }
        state = await resolve(client.admin.runtime_settings_group(group.key))
        assert state.revision is not None
        result = await resolve(
            client.admin.patch_runtime_settings(
                group.key,
                RuntimeSettingsPatch(expected_revision=state.revision, changes={"new_option": 10}),
            )
        )
        assert result.committed_revision == 5
        assert not result.applied_by_responding_replica
        assert len(requests) == 3
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_revision_conflict_is_not_retried(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            412, json={"error": "stale", "message": "Refetch", "current_revision": 5}
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="test-token", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(PreconditionFailedError):
            await resolve(
                client.admin.patch_runtime_settings(
                    "future_policy",
                    RuntimeSettingsPatch(expected_revision=4, changes={"new_option": 10}),
                )
            )
        assert len(requests) == 1
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_release_sends_expected_revision(asynchronous: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.params["expected_revision"] == "4"
        return httpx.Response(200, json=UPDATE)

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="test-token", transport=httpx.MockTransport(handler))
    try:
        await resolve(
            client.admin.release_runtime_settings(
                "future_policy", RuntimeSettingsRelease(expected_revision=4)
            )
        )
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("changes", [{}, {"x": None}, {"expected_revision": 2}])
def test_invalid_partial_edits_are_rejected(changes: dict[str, int | None]) -> None:
    with pytest.raises(ValidationError):
        RuntimeSettingsPatch(expected_revision=1, changes=changes)


def test_patch_repr_hides_values() -> None:
    patch = RuntimeSettingsPatch(expected_revision=1, changes={"new_option": "private-value"})
    assert "private-value" not in repr(patch)
