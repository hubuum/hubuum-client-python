from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar
from urllib.parse import unquote

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    APIError,
    AsyncClient,
    ClassFieldInventory,
    Client,
    FieldDiscoveryOptions,
    FieldPropertySegment,
    ProfileSuggestionStatus,
    ResultCardinalityError,
    SchemaProfilePreset,
    SchemaProfileReport,
    SchemaProfileRequest,
    TaskKind,
    TaskOutputDiscoveryState,
    TaskQuery,
    TaskUnsuccessfulError,
)

T = TypeVar("T")
NOW = "2026-10-26T08:00:00Z"


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


def _client(
    asynchronous: bool, handler: Callable[[httpx.Request], httpx.Response]
) -> Client | AsyncClient:
    cls = AsyncClient if asynchronous else Client
    return cls("https://hubuum.test", token="private_token", transport=httpx.MockTransport(handler))


def _inventory() -> dict[str, Any]:
    return {
        "sampled": True,
        "sampled_objects": 2,
        "effective_sample_limit": 2,
        "max_depth": 3,
        "include_containers": True,
        "truncation": ["sample_limit"],
        "fields": [
            {
                "field": "data.private_a.b",
                "source": "data",
                "path": path,
                "observation_count": 2,
                "object_count": 1,
                "types": {"number": 1, "null": 1},
                "example": "private_preview",
                "example_truncated": True,
                "error_count": 0,
            }
            for path in (
                [{"kind": "property", "name": "private_a.b"}],
                [{"kind": "property", "name": "private_a"}, {"kind": "property", "name": "b"}],
            )
        ],
    }


def _task(status: str) -> dict[str, Any]:
    return {
        "id": 71,
        "kind": "schema_profiling",
        "status": status,
        "created_at": NOW,
        "progress": {"total_items": 1, "processed_items": 0, "success_items": 0, "failed_items": 0},
        "links": {"task": "/api/v1/tasks/71", "events": "/api/v1/tasks/71/events"},
        "details": {
            "schema_profiling": {
                "class_id": 12,
                "output_url": "/api/v1/classes/12/schema/profiles/71",
            }
        },
    }


def _report(preset: str = "balanced") -> dict[str, Any]:
    return {
        "class_id": 12,
        "sampled": True,
        "sampled_objects": 2,
        "effective_sample_limit": 2,
        "truncation": "sample_limit",
        "options": {"preset": preset, "sample_limit": 2},
        "status": "candidate",
        "schema": {"type": "object", "properties": {"private_key": {"type": "string"}}},
        "profile": {"private_statistics": 1},
        "findings": [{"private_reason": True}],
        "replay": {"private_evidence": True},
        "sample_valid": True,
    }


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("address", [12, "Hosts", "123", ".", "..", "a/b ?#"])
async def test_discover_fields_by_id_or_exact_name(
    asynchronous: bool, address: int | str, class_json: dict[str, Any]
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/classes":
            assert request.url.params["name__equals"] == address
            assert request.url.params["limit"] == "2"
            return httpx.Response(200, json=[class_json | {"name": address}])
        return httpx.Response(200, json=_inventory())

    client = _client(asynchronous, handler)
    try:
        service = (
            client.classes.by_id(address)
            if isinstance(address, int)
            else client.classes.by_name(address)
        )
        fields = await _resolve(
            service.fields(FieldDiscoveryOptions(limit=2, depth=3, containers=True))
        )
        assert fields.fields[0].path != fields.fields[1].path
        assert isinstance(fields.fields[0].path[0], FieldPropertySegment)
        assert fields.fields[0].object_count == 1
        assert fields.fields[0].observation_count == 2
        assert "private_" not in repr(fields)
        request = requests[-1]
        assert request.method == "GET"
        expected = (
            "/api/v1/classes/12/fields"
            if address in (12, ".", "..")
            else f"/api/v1/classes/by-name/{address}/fields"
        )
        assert unquote(request.url.path) == expected
        assert dict(request.url.params) == {"limit": "2", "depth": "3", "containers": "true"}
        assert len(requests) == (2 if address in (".", "..") else 1)
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("preset", list(SchemaProfilePreset))
async def test_suggest_waits_for_report_without_changing_schema(
    asynchronous: bool, preset: SchemaProfilePreset
) -> None:
    requests: list[httpx.Request] = []
    results = [_task("queued"), _task("running"), _task("succeeded"), _report(preset.value)]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(202 if request.method == "POST" else 200, json=results.pop(0))

    client = _client(asynchronous, handler)
    try:
        report = await _resolve(
            client.classes.by_id(12).schema.suggest(
                SchemaProfileRequest(preset=preset, sample_limit=2),
                idempotency_key="profile-replay",
                poll_interval=0.001,
                timeout_seconds=1,
            )
        )
        assert report.status is ProfileSuggestionStatus.CANDIDATE
        assert "private_" not in repr(report)
        stage = report.stage_request(validate_schema=True)
        assert stage.json_schema == report.schema_
        assert stage.validate_schema
        assert len(requests) == 4
        assert [r.method for r in requests] == ["POST", "GET", "GET", "GET"]
        assert requests[0].url.path == "/api/v1/classes/12/schema/profiles"
        assert requests[0].headers["idempotency-key"] == "profile-replay"
        assert json.loads(requests[0].content) == {"preset": preset, "sample_limit": 2}
        assert requests[-1].url.path == "/api/v1/classes/12/schema/profiles/71"
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", ["failed", "cancelled", "partially_succeeded"])
async def test_unsuccessful_suggestion_never_downloads_a_report(
    asynchronous: bool, status: str
) -> None:
    results = [_task("queued"), _task(status)]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert json.loads(request.content) == {}
            assert "idempotency-key" not in request.headers
        return httpx.Response(200, json=results.pop(0))

    client = _client(asynchronous, handler)
    try:
        with pytest.raises(TaskUnsuccessfulError) as error:
            await _resolve(client.classes.by_id(12).schema.suggest())
        assert error.value.task_id == 71
        assert error.value.status == status
        assert not results
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [403, 404, 410])
async def test_report_preserves_access_missing_and_expiry_errors(
    asynchronous: bool, status: int
) -> None:
    client = _client(
        asynchronous,
        lambda _: httpx.Response(
            status, json={"error": "Unavailable", "message": "report unavailable"}
        ),
    )
    try:
        with pytest.raises(APIError) as error:
            await _resolve(client.classes.by_id(12).schema.profile_report(71))
        assert error.value.status_code == status
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_dot_name_requires_one_exact_match(asynchronous: bool) -> None:
    client = _client(asynchronous, lambda _: httpx.Response(200, json=[]))
    try:
        with pytest.raises(ResultCardinalityError):
            await _resolve(client.classes.by_name(".").fields())
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_profiling_tasks_support_discovery_and_typed_details(asynchronous: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["kind"] == "schema_profiling"
        assert request.url.params["class_id"] == "12"
        assert request.url.params["output_state"] == "available"
        return httpx.Response(200, json=[_task("succeeded")])

    client = _client(asynchronous, handler)
    try:
        tasks = await _resolve(
            client.tasks.list(
                TaskQuery(
                    kind=(TaskKind.SCHEMA_PROFILING,),
                    class_id=12,
                    output_state=TaskOutputDiscoveryState.AVAILABLE,
                )
            )
        )
        assert tasks[0].details is not None
        assert tasks[0].details.schema_profiling is not None
        assert tasks[0].details.schema_profiling.class_id == 12
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("value", [0, 251, True, "1", 1.1])
def test_profile_sample_limit_rejects_invalid_values(value: Any) -> None:
    with pytest.raises(ValidationError):
        SchemaProfileRequest(sample_limit=value)


@pytest.mark.parametrize(
    "options",
    [
        {"limit": 0},
        {"limit": 251},
        {"limit": True},
        {"limit": "1"},
        {"depth": -1},
        {"depth": 33},
        {"depth": True},
        {"depth": "1"},
        {"containers": "true"},
    ],
)
def test_discovery_options_reject_invalid_values(options: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="must be"):
        FieldDiscoveryOptions(**options)


def test_discovery_options_defaults_and_bounds() -> None:
    assert dict(FieldDiscoveryOptions().as_params()) == {
        "limit": "100",
        "depth": "6",
        "containers": "false",
    }
    assert FieldDiscoveryOptions(limit=1, depth=0).limit == 1
    assert FieldDiscoveryOptions(limit=250, depth=32).depth == 32


@pytest.mark.parametrize(
    "override",
    [{"status": "blocked"}, {"status": "insufficient"}, {"sample_valid": False}, {"schema": None}],
)
def test_unusable_report_cannot_produce_a_stage_request(override: dict[str, Any]) -> None:
    report = SchemaProfileReport.model_validate(_report() | override)
    with pytest.raises(ValueError, match="candidate"):
        report.stage_request(validate_schema=True)


def test_inventory_validation_errors_redact_preview_data() -> None:
    payload = _inventory()
    payload["fields"][0]["observation_count"] = -1
    with pytest.raises(ValidationError) as error:
        ClassFieldInventory.model_validate(payload)
    assert "private_" not in str(error.value)
    assert "private_" not in str(error.value.errors())
