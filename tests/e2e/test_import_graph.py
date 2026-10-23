from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable
from pathlib import Path
from typing import TypeVar

import pytest

from hubuum_client import AsyncClient, Client, ImportGraph, ImportRequest, Query, TaskStatus

pytestmark = pytest.mark.e2e
T = TypeVar("T")


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_mixed_identity_and_integration_import_dry_run(
    client: Client, unique_name: str, asynchronous: bool
) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "import-graph.json"
    graph = ImportGraph.model_validate(
        json.loads(fixture.read_text().replace("typed-import", unique_name))
    )
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    try:
        result = await resolve(
            api.imports.run(
                ImportRequest(graph=graph, dry_run=True),
                idempotency_key=unique_name,
                timeout_seconds=60,
                poll_interval=0.1,
            )
        )
        assert result.task.status is TaskStatus.SUCCEEDED
        assert result.task.progress.total_items == graph.total_items
        assert result.failed == 0
        assert result.succeeded == graph.total_items
        assert {item.outcome for item in result.results} == {"planned"}
        assert len(result.results) == graph.total_items
        assert {item.item_ref for item in result.results} == {
            "collection",
            "class",
            "object",
            "scope",
            "group",
            "principal",
            "membership",
            "template",
            "target",
            "sink",
            "subscription",
            "computed",
        }
        # Planning must leave domain resources absent; the task and results are retained.
        assert not await resolve(
            api.collections.list(Query().where("name", f"{unique_name}-collection"))
        )
        assert not await resolve(
            api.groups.list(Query().where("groupname", f"{unique_name}-group"))
        )
        assert not await resolve(api.event_sinks.list(Query().where("name", f"{unique_name}-sink")))
    finally:
        if isinstance(api, AsyncClient):
            await api.close()
