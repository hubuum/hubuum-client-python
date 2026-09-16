from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TypeVar

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    APIError,
    AsyncClient,
    Client,
    ComplianceStatus,
    ConflictError,
    DecodeError,
    ImportClassInput,
    ImportGraph,
    ImportRequest,
    ImportSchemaActivation,
    SchemaActivationPolicy,
    SchemaActivationRequest,
    SchemaImpactReadiness,
    SchemaPageOptions,
    SchemaRepairReportRequest,
    SchemaRevisionStatus,
    SchemaStageRequest,
    SchemaWorkResponse,
    TaskCancelRequest,
    TaskKind,
    TaskRemoteSideEffectState,
    TaskStatus,
)

T = TypeVar("T")
NOW = "2026-09-15T20:00:00Z"
SCHEMA = {"type": "object", "required": ["hostname"]}
REVISION = {
    "class_id": 12,
    "revision": 2,
    "validate_schema": True,
    "json_schema": SCHEMA,
    "status": "staged",
    "created_at": NOW,
}
WORK = {
    "task_id": 27,
    "target": {"class_id": 12, "revision": 2},
    "kind": "impact",
    "status": "complete",
    "start_epoch": 1,
    "upper_bound": 13,
    "cursor": 13,
    "examined": 1,
    "valid": 0,
    "invalid": 1,
    "not_required": 0,
    "uninspectable": 0,
    "stale": 0,
    "invalid_samples": [13],
    "elapsed_millis": 1,
    "batches": 1,
    "created_at": NOW,
    "readiness": "incompatible",
}
HTML = "<!doctype html><html><body>Retained diagnostics: æ</body></html>"


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


def _client(
    asynchronous: bool, handler: Callable[[httpx.Request], httpx.Response]
) -> Client | AsyncClient:
    cls = AsyncClient if asynchronous else Client
    return cls("https://hubuum.test", token="token", transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_schema_lifecycle_requests_and_typed_responses(asynchronous: bool) -> None:
    expected: list[tuple[str, str, object, object]] = [
        (
            "GET",
            "",
            None,
            {
                "active": REVISION,
                "object_epoch": 1,
                "counts": {
                    "valid": 0,
                    "invalid": 0,
                    "pending": 1,
                    "not_required": 0,
                },
            },
        ),
        ("GET", "/revisions?after=1&limit=2", None, [REVISION]),
        ("GET", "/revisions/2", None, REVISION),
        ("POST", "/revisions", {"json_schema": SCHEMA, "validate_schema": True}, REVISION),
        ("POST", "/revisions/2/impact", None, WORK),
        ("GET", "/tasks/27", None, WORK),
        (
            "POST",
            "/revisions/2/activate",
            {
                "expected_active_revision": 1,
                "policy": "reject_incompatible",
                "impact_task_id": 27,
            },
            {"active": REVISION | {"status": "active"}, "task_id": 28},
        ),
        ("POST", "/revisions/2/revalidate", None, WORK | {"kind": "revalidation"}),
        ("DELETE", "/tasks/27", None, WORK | {"status": "cancelled"}),
        ("DELETE", "/revisions/2", None, REVISION | {"status": "abandoned"}),
        (
            "POST",
            "/tasks/27/report",
            {
                "object_url_template": "https://inventory.test/objects/{object_id}",
                "template_id": 7,
            },
            HTML,
        ),
        ("GET", "/tasks/27/report?download=true", None, HTML),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        method, suffix, body, result = expected.pop(0)
        assert request.method == method
        assert request.url == f"https://hubuum.test/api/v1/classes/12/schema{suffix}"
        assert request.headers["authorization"] == "Bearer token"
        assert (json.loads(request.content) if request.content else None) == body
        if body is not None:
            assert request.headers["content-type"] == "application/json"
        if isinstance(result, str):
            assert request.headers["accept"] == "text/html"
            return httpx.Response(
                200, text=result, headers={"content-type": "text/html; charset=utf-8"}
            )
        return httpx.Response(200, json=result)

    client = _client(asynchronous, handler)
    try:
        schema = client.classes.by_id(12).schema
        assert (await _resolve(schema.get())).counts.pending == 1
        assert (await _resolve(schema.revisions(SchemaPageOptions(after=1, limit=2))))[
            0
        ].revision == 2
        assert (await _resolve(schema.revision(2))).created_at == datetime(
            2026, 9, 15, 20, tzinfo=UTC
        )
        assert (
            await _resolve(
                schema.stage(SchemaStageRequest(json_schema=SCHEMA, validate_schema=True))
            )
        ).json_schema == SCHEMA
        assert (await _resolve(schema.impact(2))).readiness is SchemaImpactReadiness.INCOMPATIBLE
        assert (await _resolve(schema.work(27))).invalid_samples == (13,)
        active = await _resolve(
            schema.activate(
                2,
                SchemaActivationRequest(
                    expected_active_revision=1,
                    policy=SchemaActivationPolicy.REJECT_INCOMPATIBLE,
                    impact_task_id=27,
                ),
            )
        )
        assert active.active.status is SchemaRevisionStatus.ACTIVE
        assert active.task_id == 28
        assert (await _resolve(schema.revalidate(2))).kind == "revalidation"
        assert (await _resolve(schema.cancel(27))).status == "cancelled"
        assert (await _resolve(schema.abandon(2))).status is SchemaRevisionStatus.ABANDONED
        assert (
            await _resolve(
                schema.generate_report(
                    27,
                    SchemaRepairReportRequest(
                        object_url_template="https://inventory.test/objects/{object_id}",
                        template_id=7,
                    ),
                )
            )
            == HTML
        )
        assert await _resolve(schema.report(27, download=True)) == HTML
        assert not expected
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_compliance_pages_resume_after_hidden_candidates(asynchronous: bool) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/api/v1/classes/12/schema/objects"
        assert request.url.params["limit"] == "50"
        if calls == 1:
            assert request.url.params["after"] == "0"
            assert "status" not in request.url.params
            return httpx.Response(200, json={"items": [], "next_after": 42})
        assert request.url.params["after"] == "42"
        assert request.url.params["status"] == "valid"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "object_id": 51,
                        "object_revision": 9,
                        "active_schema": {"class_id": 12, "revision": 2},
                        "status": "valid",
                        "evidence": {
                            "schema": {"class_id": 12, "revision": 2},
                            "object_revision": 9,
                            "valid": True,
                            "validated_at": NOW,
                        },
                    }
                ],
                "next_after": None,
            },
        )

    client = _client(asynchronous, handler)
    try:
        schema = client.classes.by_id(12).schema
        first = await _resolve(schema.objects())
        assert first.items == ()
        assert first.next_after == 42
        second = await _resolve(
            schema.objects(SchemaPageOptions(after=first.next_after), status=ComplianceStatus.VALID)
        )
        assert second.next_after is None
        evidence = second.items[0].evidence
        assert evidence is not None
        assert evidence.schema_.revision == 2
        assert evidence.model_dump(by_alias=True)["schema"] == {"class_id": 12, "revision": 2}
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [200, 202])
async def test_task_cancellation_can_be_pending_or_terminal(
    asynchronous: bool, status: int
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/tasks/27/cancel"
        assert json.loads(request.content) == (
            {}
            if status == 200
            else {
                "expected_status": "running",
                "reason": "private cancellation reason",
            }
        )
        return httpx.Response(
            status,
            json={
                "id": 27,
                "kind": "schema_validation",
                "created_at": NOW,
                "status": "cancelled" if status == 200 else "running",
                "unattempted_items": 3,
                "cancel_reason": "private cancellation reason",
                "cancel_requested_at": NOW,
                "cancel_requested_by": 5,
                "execution_deadline_at": NOW,
                "remote_side_effect_state": "possibly_sent",
                "terminal_reason": "requested",
                "progress": {
                    "total_items": 5,
                    "processed_items": 2,
                    "success_items": 2,
                    "failed_items": 0,
                },
                "links": {"task": "/api/v1/tasks/27", "events": "/api/v1/tasks/27/events"},
            },
        )

    client = _client(asynchronous, handler)
    try:
        payload = (
            None
            if status == 200
            else TaskCancelRequest(
                expected_status=TaskStatus.RUNNING, reason="private cancellation reason"
            )
        )
        task = await _resolve(client.tasks.cancel(27, payload))
        assert task.kind is TaskKind.SCHEMA_VALIDATION
        assert task.status.terminal is (status == 200)
        assert task.unattempted_items == 3
        assert task.cancel_requested_by == 5
        assert task.cancel_requested_at == datetime(2026, 9, 15, 20, tzinfo=UTC)
        assert task.execution_deadline_at == task.cancel_requested_at
        assert task.remote_side_effect_state is TaskRemoteSideEffectState.POSSIBLY_SENT
        assert "private cancellation reason" not in repr(task)
        assert "private cancellation reason" not in repr(payload)
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_schema_and_cancellation_errors_keep_status_and_redact_bodies(
    asynchronous: bool,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/activate") or request.url.path.endswith("/cancel"):
            return httpx.Response(409, json={"error": "Conflict", "message": "Bearer token"})
        return httpx.Response(413, json={"error": "TooLarge", "message": "Bearer token"})

    client = _client(asynchronous, handler)
    try:
        schema = client.classes.by_id(12).schema
        with pytest.raises(ConflictError):
            await _resolve(
                schema.activate(
                    2,
                    SchemaActivationRequest(
                        expected_active_revision=1,
                        policy=SchemaActivationPolicy.REJECT_INCOMPATIBLE,
                    ),
                )
            )
        with pytest.raises(ConflictError):
            await _resolve(
                client.tasks.cancel(27, TaskCancelRequest(expected_status=TaskStatus.QUEUED))
            )
        with pytest.raises(APIError) as error:
            await _resolve(
                schema.generate_report(
                    27,
                    SchemaRepairReportRequest(
                        object_url_template="https://inventory.test/{object_id}"
                    ),
                )
            )
        assert error.value.status_code == 413
        assert "Bearer token" not in str(error.value)
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_html_reports_reject_unexpected_content_type(asynchronous: bool) -> None:
    client = _client(asynchronous, lambda request: httpx.Response(200, json={"private": "data"}))
    try:
        with pytest.raises(DecodeError, match="expected a text/html response"):
            await _resolve(client.classes.by_id(12).schema.report(27))
    finally:
        await _resolve(client.close())


def test_import_schema_activation_uses_exact_nested_wire_fields() -> None:
    request = ImportRequest(
        graph=ImportGraph(
            classes=[
                ImportClassInput(
                    name="Hosts",
                    description="Hosts",
                    json_schema=SCHEMA,
                    validate_schema=True,
                    schema_activation=ImportSchemaActivation(
                        revision=2,
                        expected_active_revision=1,
                        policy=SchemaActivationPolicy.ALLOW_PENDING,
                    ),
                )
            ]
        )
    )
    row = request.payload()["graph"]["classes"][0]
    assert row["schema_activation"] == {
        "revision": 2,
        "expected_active_revision": 1,
        "policy": "allow_pending",
    }
    assert row["json_schema"] == SCHEMA
    assert "schema_activation" not in ImportClassInput(name="Hosts", description="Hosts").payload()
    assert SchemaStageRequest(validate_schema=False).payload() == {"validate_schema": False}
    assert (
        SchemaStageRequest(validate_schema=True, json_schema=False).payload()["json_schema"]
        is False
    )
    with pytest.raises(ValidationError):
        SchemaActivationRequest.model_validate(
            {"expected_active_revision": 0, "policy": "allow_pending"}
        )
    with pytest.raises(ValidationError):
        TaskCancelRequest(reason="x" * 513)
    with pytest.raises(ValidationError):
        SchemaStageRequest.model_validate({"validate_schema": False, "unknown": True})


@pytest.mark.parametrize("options", [{"after": -1}, {"limit": 0}, {"limit": 101}])
def test_schema_page_bounds(options: dict[str, int]) -> None:
    with pytest.raises(ValueError, match=r"after must|limit must"):
        SchemaPageOptions(**options)


def test_retained_diagnostics_preserve_snapshot_and_expected_null() -> None:
    reason = {"keyword": "const", "schema_path": "/properties/hostname/const"}
    finding = {
        "object_id": 13,
        "reason": reason,
        "snapshot": {
            "object_revision": 9,
            "inspected_at": NOW,
            "diagnostics": {
                "truncated": True,
                "issues": [
                    {
                        "reason": reason,
                        "instance_path": "/hostname",
                        "message": "Must be null",
                        "expected": {"status": "available", "value": None},
                        "actual": {"string": {"characters": 12}},
                        "alternative": False,
                        "omissions": ["actual_value_redacted"],
                    },
                    {
                        "reason": reason,
                        "message": "Constraint unavailable",
                        "expected": {"status": "omitted"},
                        "actual": "number",
                        "alternative": True,
                        "omissions": [],
                    },
                ],
            },
        },
    }
    work = SchemaWorkResponse.model_validate(
        WORK
        | {
            "impact": {
                "baseline": {"class_id": 12, "revision": 1},
                "counts": {
                    "newly_invalid": 1,
                    "newly_valid": 0,
                    "still_invalid": 0,
                    "still_valid": 0,
                    "newly_required_valid": 0,
                    "no_longer_required": 0,
                    "unchanged_not_required": 0,
                    "uninspectable": 0,
                },
                "failures": [{"reason": reason, "objects": 1, "samples": [13]}],
                "findings": [finding, {"object_id": 14, "reason": reason, "snapshot": None}],
                "ungrouped_failures": 0,
            }
        }
    )
    assert work.impact is not None
    snapshot = work.impact.findings[0].snapshot
    assert snapshot is not None
    assert snapshot.object_revision == 9
    assert snapshot.diagnostics.truncated
    available, omitted = snapshot.diagnostics.issues
    assert available.expected.status == "available"
    assert available.expected.value is None
    assert omitted.expected.status == "omitted"
    assert work.impact.findings[1].snapshot is None
