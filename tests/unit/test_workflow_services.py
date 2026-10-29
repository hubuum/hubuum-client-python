from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterable, Callable, Iterable
from datetime import UTC, datetime
from functools import partial
from typing import Any

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from test_typed_api import DOCUMENT, example

from hubuum_client import (
    APIError,
    AsyncClient,
    BackupRequest,
    Client,
    ComputedFieldCreate,
    ComputedFieldPreviewRequest,
    ComputedFieldUpdate,
    CredentialApprovalSecret,
    DecodeError,
    EventQuery,
    EventSinkCreate,
    EventSinkUpdate,
    ExportTemplateCreate,
    ExportTemplateRunRequest,
    ExportTemplateUpdate,
    Permission,
    PersonalComputedFieldCreate,
    RemoteTargetCreate,
    RemoteTargetInvokeRequest,
    RemoteTargetUpdate,
    RestoreConfirmRequest,
    SettingsPatchOperation,
    SettingsRequest,
    TaskUnsuccessfulError,
    TransportError,
)
from hubuum_client.api import models as wire


async def resolve(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


async def collect(value: Iterable[Any] | AsyncIterable[Any]) -> list[Any]:
    return [item async for item in value] if isinstance(value, AsyncIterable) else list(value)


def record(name: str) -> Any:
    return example(DOCUMENT["components"]["schemas"][name])


def response_fixture(path: str, method: str) -> Any:
    operation = DOCUMENT["paths"][path][method.lower()]
    response = next(v for k, v in operation["responses"].items() if k.startswith("2"))
    if "content" not in response:
        return None
    return example(response["content"]["application/json"]["schema"])


Case = tuple[str, str, Callable[[Any], Any]]
CASES: list[Case] = [
    ("GET", "/api/v1/events", lambda c: c.audit.events.list()),
    (
        "GET",
        "/api/v1/collections/{collection_id}/events",
        lambda c: c.audit.collection(11).events.list(),
    ),
    ("GET", "/api/v1/classes/{class_id}/events", lambda c: c.audit.class_(11).events.list()),
    (
        "GET",
        "/api/v1/classes/{class_id}/{object_id}/events",
        lambda c: c.audit.object(11, 11).events.list(),
    ),
    ("GET", "/api/v1/iam/users/{user_id}/events", lambda c: c.audit.user(11).list()),
    ("GET", "/api/v1/iam/groups/{group_id}/events", lambda c: c.audit.group(11).list()),
    (
        "GET",
        "/api/v1/export-templates/{template_id}/events",
        lambda c: c.export_templates.audit(11).events.list(),
    ),
    (
        "GET",
        "/api/v1/remote-targets/{target_id}/events",
        lambda c: c.remote_targets.audit(11).events.list(),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions",
        lambda c: c.collections.permissions(11).assignments(),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions",
        lambda c: c.collections.permissions(11).list(),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}",
        lambda c: c.collections.permissions(11).group(11),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions/principal/{principal_id}",
        lambda c: c.collections.permissions(11).principal(11).list(),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions/effective/group/{group_id}",
        lambda c: c.collections.permissions(11).effective_group(11),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions/effective/principal/{principal_id}",
        lambda c: c.collections.permissions(11).effective_principal(11),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/has_permissions/{permission}",
        lambda c: c.collections.permissions(11).with_permission(Permission.READ_CLASS).list(),
    ),
    (
        "GET",
        "/api/v1/classes/{class_id}/permissions",
        lambda c: c.classes.by_id(11).permissions.list(),
    ),
    (
        "POST",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}",
        lambda c: c.collections.permissions(11).grant(11, [Permission.READ_CLASS], if_match='"r1"'),
    ),
    (
        "PUT",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}",
        lambda c: c.collections.permissions(11).replace(
            11, [Permission.READ_CLASS], if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}",
        lambda c: c.collections.permissions(11).revoke(11, if_match='"r1"'),
    ),
    (
        "POST",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}",
        lambda c: c.collections.permissions(11).grant_permission(
            11, Permission.READ_CLASS, if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}",
        lambda c: c.collections.permissions(11).revoke_permission(
            11, Permission.READ_CLASS, if_match='"r1"'
        ),
    ),
    (
        "GET",
        "/api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}",
        lambda c: c.collections.permissions(11).check(11, Permission.READ_CLASS),
    ),
    ("GET", "/api/v1/event-deliveries", lambda c: c.event_deliveries.list()),
    ("GET", "/api/v1/event-deliveries/{delivery_id}", lambda c: c.event_deliveries.get(11)),
    ("GET", "/api/v1/event-deliveries/health", lambda c: c.event_deliveries.health()),
    (
        "POST",
        "/api/v1/event-deliveries/{delivery_id}/retry",
        lambda c: c.event_deliveries.retry(11),
    ),
    (
        "POST",
        "/api/v1/event-deliveries/{delivery_id}/dead",
        lambda c: c.event_deliveries.mark_dead(11),
    ),
    ("GET", "/api/v1/export-templates", lambda c: c.export_templates.list()),
    ("GET", "/api/v1/export-templates/{template_id}", lambda c: c.export_templates.get(11)),
    (
        "POST",
        "/api/v1/export-templates",
        lambda c: c.export_templates.create(
            ExportTemplateCreate.model_validate(record("NewExportTemplate"))
        ),
    ),
    (
        "PATCH",
        "/api/v1/export-templates/{template_id}",
        lambda c: c.export_templates.update(
            11, ExportTemplateUpdate(description="changed"), if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/export-templates/{template_id}",
        lambda c: c.export_templates.delete(11, if_match='"r1"'),
    ),
    (
        "POST",
        "/api/v1/export-templates/{template_id}/exports",
        lambda c: c.export_templates.submit(11),
    ),
    ("GET", "/api/v1/remote-targets", lambda c: c.remote_targets.list()),
    ("GET", "/api/v1/remote-targets/{target_id}", lambda c: c.remote_targets.get(11)),
    (
        "POST",
        "/api/v1/remote-targets",
        lambda c: c.remote_targets.create(
            RemoteTargetCreate.model_validate(record("NewRemoteTarget"))
        ),
    ),
    (
        "PATCH",
        "/api/v1/remote-targets/{target_id}",
        lambda c: c.remote_targets.update(
            11, RemoteTargetUpdate(description="changed"), if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/remote-targets/{target_id}",
        lambda c: c.remote_targets.delete(11, if_match='"r1"'),
    ),
    (
        "POST",
        "/api/v1/remote-targets/{target_id}/invoke",
        lambda c: c.remote_targets.invoke(
            11, RemoteTargetInvokeRequest.model_validate(record("RemoteTargetInvokeRequest"))
        ),
    ),
    (
        "GET",
        "/api/v1/classes/{class_id}/computed-fields",
        lambda c: c.classes.by_id(11).computed_fields.list(),
    ),
    (
        "GET",
        "/api/v1/classes/{class_id}/computed-fields/{field_id}",
        lambda c: c.classes.by_id(11).computed_fields.get(11),
    ),
    (
        "POST",
        "/api/v1/classes/{class_id}/computed-fields",
        lambda c: c.classes.by_id(11).computed_fields.create(
            ComputedFieldCreate.model_validate(record("ComputedFieldDefinitionRequest"))
        ),
    ),
    (
        "PATCH",
        "/api/v1/classes/{class_id}/computed-fields/{field_id}",
        lambda c: c.classes.by_id(11).computed_fields.update(
            11, ComputedFieldUpdate(enabled=False), if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/classes/{class_id}/computed-fields/{field_id}",
        lambda c: c.classes.by_id(11).computed_fields.delete(11, if_match='"r1"'),
    ),
    (
        "POST",
        "/api/v1/classes/{class_id}/computed-fields/preview",
        lambda c: c.classes.by_id(11).computed_fields.preview(
            ComputedFieldPreviewRequest.model_validate(record("ComputedFieldPreviewRequest"))
        ),
    ),
    (
        "POST",
        "/api/v1/classes/{class_id}/computed-fields/rebuild",
        lambda c: c.classes.by_id(11).computed_fields.rebuild(),
    ),
    ("GET", "/api/v1/iam/me/computed-fields", lambda c: c.computed_fields.for_class(11).list()),
    ("GET", "/api/v1/iam/me/computed-fields/{field_id}", lambda c: c.computed_fields.get(11)),
    (
        "POST",
        "/api/v1/iam/me/computed-fields",
        lambda c: c.computed_fields.create(
            PersonalComputedFieldCreate.model_validate(
                record("PersonalComputedFieldDefinitionRequest")
            )
        ),
    ),
    (
        "PATCH",
        "/api/v1/iam/me/computed-fields/{field_id}",
        lambda c: c.computed_fields.update(11, ComputedFieldUpdate(enabled=False), if_match='"r1"'),
    ),
    (
        "DELETE",
        "/api/v1/iam/me/computed-fields/{field_id}",
        lambda c: c.computed_fields.delete(11, if_match='"r1"'),
    ),
    (
        "POST",
        "/api/v1/iam/me/computed-fields/preview",
        lambda c: c.computed_fields.preview(
            ComputedFieldPreviewRequest.model_validate(record("ComputedFieldPreviewRequest"))
        ),
    ),
    ("POST", "/api/v1/backups", lambda c: c.backups.submit()),
    ("GET", "/api/v1/backups/{task_id}", lambda c: c.backups.get(11)),
    ("GET", "/api/v1/backups/{task_id}/output", lambda c: c.backups.output(11)),
    (
        "POST",
        "/api/v1/restores",
        lambda c: c.restores.stage(wire.BackupDocument.model_validate(record("BackupDocument"))),
    ),
    (
        "POST",
        "/api/v1/restores/{restore_id}/confirm",
        lambda c: c.restores.confirm(
            11,
            RestoreConfirmRequest(
                restore_capability="cap-secret",
                sha256="digest-secret",
                confirmation="REPLACE ALL HUBUUM DATA",
            ),
            credential_approval=CredentialApprovalSecret("approval-secret"),
        ),
    ),
    (
        "GET",
        "/api/v1/restores/{restore_id}/status",
        lambda c: c.restores.status(11, capability=SecretStr("cap-secret")),
    ),
    ("GET", "/api/v1/iam/me/permissions", lambda c: c.principals.permissions()),
    (
        "GET",
        "/api/v1/iam/principals/{principal_id}/permissions",
        lambda c: c.principals.permissions(11),
    ),
    ("GET", "/api/v1/iam/me/groups", lambda c: c.principals.groups().list()),
    (
        "GET",
        "/api/v1/iam/principals/{principal_id}/groups",
        lambda c: c.principals.groups(11).list(),
    ),
    ("GET", "/api/v1/iam/me/settings", lambda c: c.principals.settings().get()),
    (
        "GET",
        "/api/v1/iam/principals/{principal_id}/settings",
        lambda c: c.principals.settings(11).get(),
    ),
    (
        "PUT",
        "/api/v1/iam/me/settings",
        lambda c: c.principals.settings().replace(
            SettingsRequest(settings={"theme": None}), if_match='"r1"'
        ),
    ),
    (
        "PATCH",
        "/api/v1/iam/me/settings",
        lambda c: c.principals.settings().merge_patch(
            SettingsRequest(settings={"theme": None}), if_match='"r1"'
        ),
    ),
    (
        "DELETE",
        "/api/v1/iam/me/settings",
        lambda c: c.principals.settings().delete(if_match='"r1"'),
    ),
    ("GET", "/api/v1/auth/providers", lambda c: c.auth.providers()),
    ("GET", "/api/v1/auth/validate", lambda c: c.auth.validate()),
    ("POST", "/api/v1/auth/logout/token", lambda c: c.auth.revoke_token("token-secret")),
    ("POST", "/api/v1/auth/logout/uid/{user_id}", lambda c: c.auth.revoke_user(11)),
    ("POST", "/api/v1/auth/logout_all", lambda c: c.auth.revoke_all()),
    ("GET", "/api/v1/admin/config", lambda c: c.admin.config()),
    ("GET", "/api/v0/meta/counts", lambda c: c.admin.counts()),
    ("GET", "/api/v0/meta/db", lambda c: c.admin.database()),
    ("GET", "/api/v0/meta/tasks", lambda c: c.admin.tasks()),
    (
        "GET",
        "/api/v0/meta/login-rate-limit",
        lambda c: c.admin.rate_limits(include="active", scope="ip", q="test"),
    ),
    ("DELETE", "/api/v0/meta/login-rate-limit/{id}", lambda c: c.admin.release_rate_limit("11")),
    ("DELETE", "/api/v0/meta/login-rate-limit", lambda c: c.admin.clear_rate_limits()),
]


def history_call(client: Any, factory: Callable[[Any], Any], *, as_of: bool = False) -> Any:
    history = factory(client).history
    return history.as_of(datetime(2026, 10, 29, tzinfo=UTC)) if as_of else history.list()


for resource, factory in (
    ("collections/{collection_id}", lambda c: c.audit.collection(11)),
    ("classes/{class_id}", lambda c: c.audit.class_(11)),
    ("classes/{class_id}/{object_id}", lambda c: c.audit.object(11, 11)),
    ("export-templates/{template_id}", lambda c: c.audit.export_template(11)),
    ("remote-targets/{remote_target_id}", lambda c: c.audit.remote_target(11)),
):
    CASES.extend(
        [
            (
                "GET",
                f"/api/v1/{resource}/history",
                partial(history_call, factory=factory),
            ),
            (
                "GET",
                f"/api/v1/{resource}/history/as-of",
                partial(history_call, factory=factory, as_of=True),
            ),
        ]
    )


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("malformed", [False, True])
@pytest.mark.parametrize(("method", "path", "call"), CASES, ids=[f"{m} {p}" for m, p, _ in CASES])
async def test_convenience_routes_and_safe_decoding(
    asynchronous: bool, malformed: bool, method: str, path: str, call: Callable[[Any], Any]
) -> None:
    body = response_fixture(path, method)
    if malformed and body is None:
        pytest.skip("bodyless response")

    def handler(request: httpx.Request) -> httpx.Response:
        concrete = path
        for part in path.split("/"):
            if part.startswith("{"):
                concrete = concrete.replace(part, "ReadClass" if part == "{permission}" else "11")
        assert request.method == method
        assert request.url.path == concrete
        if path.endswith(("/status", "/providers")):
            assert "authorization" not in request.headers
        else:
            assert request.headers["authorization"] == "Bearer bearer-secret"
        if path.endswith("/status"):
            assert request.headers["x-hubuum-restore-capability"] == "cap-secret"
        if path.endswith("/confirm"):
            assert request.headers["x-hubuum-credential-approval"] == "approval-secret"
        if method in {"PATCH", "DELETE", "PUT"} and not path.startswith("/api/v0"):
            assert request.headers["if-match"] == '"r1"'
        if method in {"POST", "PUT"} and path.endswith("/permissions/group/{group_id}"):
            assert json.loads(request.content) == ["ReadClass"]
        if path.endswith("/settings") and method in {"PATCH", "PUT"}:
            assert json.loads(request.content) == {"theme": None}
            assert request.headers["content-type"] == (
                "application/merge-patch+json" if method == "PATCH" else "application/json"
            )
        if path.endswith("/as-of"):
            assert request.url.params["at"] == "2026-10-29T00:00:00+00:00"
        if path == "/api/v1/iam/me/computed-fields" and method == "GET":
            assert request.url.params["class_id"] == "11"
        return (
            httpx.Response(204)
            if body is None
            else httpx.Response(200, json="response-secret" if malformed else body)
        )

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="bearer-secret", transport=httpx.MockTransport(handler)
    )
    try:
        if malformed:
            with pytest.raises(DecodeError) as error:
                await resolve(call(client))
            assert "secret" not in str(error.value)
            assert error.value.__context__ is None
        else:
            result = await resolve(call(client))
            assert "secret" not in repr(result)
    finally:
        await resolve(client.close())


@pytest.mark.parametrize(
    ("model", "schema"),
    [
        (BackupRequest, "BackupRequest"),
        (ExportTemplateCreate, "NewExportTemplate"),
        (ExportTemplateUpdate, "UpdateExportTemplate"),
        (ExportTemplateRunRequest, "ExportTemplateRunRequest"),
        (RemoteTargetCreate, "NewRemoteTarget"),
        (RemoteTargetUpdate, "UpdateRemoteTarget"),
        (RemoteTargetInvokeRequest, "RemoteTargetInvokeRequest"),
        (ComputedFieldCreate, "ComputedFieldDefinitionRequest"),
        (ComputedFieldUpdate, "ComputedFieldDefinitionPatch"),
        (PersonalComputedFieldCreate, "PersonalComputedFieldDefinitionRequest"),
        (ComputedFieldPreviewRequest, "ComputedFieldPreviewRequest"),
        (RestoreConfirmRequest, "RestoreConfirmRequest"),
    ],
)
def test_strict_requests_redact_validation(model: Any, schema: str) -> None:
    data = record(schema)
    value = model.model_validate(data)
    assert value.wire_payload() == data
    with pytest.raises(ValidationError) as error:
        model.model_validate(data | {"secret-field": "input-secret"})
    assert "input-secret" not in str(error.value)
    assert "secret-field" not in str(error.value)
    assert error.value.__context__ is None


@pytest.mark.parametrize("kind", ["webhook", "email", "amqp", "valkey_stream"])
def test_sink_config_and_patch_redaction(kind: str) -> None:
    for model in (EventSinkCreate, EventSinkUpdate):
        value = model(
            name="sink",
            kind=kind,
            config={"url": "https://user:secret@host/", "headers": {"Authorization": "secret"}},
            secret_ref="alias-secret",
        )
        assert "secret" not in repr(value)
        assert value.payload()["secret_ref"] == "alias-secret"
        with pytest.raises(ValidationError) as error:
            model.model_validate(
                {
                    "name": "sink",
                    "kind": kind,
                    "config": {"password": object()},
                    "secret_ref": "alias-secret",
                }
            )
        assert "alias-secret" not in str(error.value)
        assert error.value.__context__ is None
    assert EventSinkUpdate(secret_ref=None).payload() == {"secret_ref": None}


def test_remote_target_sensitive_fields_and_null_clearing() -> None:
    fields = {
        "url_template": "https://user:password-secret@host/?token=url-secret",
        "auth_config": {"type": "bearer_secret", "secret": "alias-secret"},
        "headers_template": {"Authorization": "header-secret"},
        "body_template": "body-secret",
    }
    target = RemoteTargetCreate.model_validate(record("NewRemoteTarget") | fields)
    assert "secret" not in repr(target)
    assert target.wire_payload()["headers_template"] == fields["headers_template"]
    assert RemoteTargetUpdate(body_template=None).wire_payload() == {"body_template": None}
    with pytest.raises(ValidationError) as error:
        RemoteTargetCreate.model_validate(
            record("NewRemoteTarget") | fields | {"timeout_ms": "invalid-secret"}
        )
    assert "secret" not in str(error.value)
    assert error.value.__context__ is None


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_audit_filters_pages_and_guards(asynchronous: bool) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.url.params["occurred_after"] == "2026-10-29T00:00:00+00:00"
        assert request.url.params["action"] == "object.updated"
        return httpx.Response(
            200,
            json=[record("EventResponse")],
            headers={"X-Next-Cursor": "next", "X-Total-Count": "9", "X-Page-Limit": "1"},
        )

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", transport=httpx.MockTransport(handler)
    )
    controls = EventQuery(
        action="object.updated", occurred_after=datetime(2026, 10, 29, tzinfo=UTC)
    ).limit(1)
    try:
        page = await resolve(client.audit.events.page(controls))
        assert page.total_count == 9
        assert page.page_limit == 1
        assert page.items[0].provenance.actor is not None
        with pytest.raises(RuntimeError, match="repeated"):
            await resolve(client.audit.events.all(controls))
        assert seen[-1].url.params["cursor"] == "next"
        with pytest.raises(RuntimeError, match="max_pages"):
            await collect(client.audit.events.pages(controls, max_pages=1))
        with pytest.raises(RuntimeError, match="max_items"):
            await resolve(client.audit.events.all(controls, max_items=1))
        with pytest.raises(ValueError, match="timezone"):
            await resolve(client.audit.collection(11).history.as_of(datetime(2026, 10, 29)))
        with pytest.raises(ValueError, match="timezone"):
            await resolve(
                client.audit.events.list(EventQuery(occurred_before=datetime(2026, 10, 29)))
            )
        assert controls.cursor_value is None
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("workflow", ["backup", "template", "remote"])
@pytest.mark.parametrize("status", ["succeeded", "failed", "partially_succeeded"])
async def test_task_workflows_wait_and_keep_exact_outputs(
    asynchronous: bool, workflow: str, status: str
) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/output"):
            if workflow == "backup":
                return httpx.Response(200, json=record("BackupDocument"))
            return httpx.Response(200, text="template-output", headers={"Content-Type": "text/csv"})
        data = record("TaskResponse") | {
            "id": 17,
            "kind": "remote_call"
            if workflow == "remote"
            else "backup"
            if workflow == "backup"
            else "export",
            "status": "queued" if request.method == "POST" else status,
        }
        return httpx.Response(202 if request.method == "POST" else 200, json=data)

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", transport=httpx.MockTransport(handler)
    )

    def run(**kwargs: Any) -> Any:
        if workflow == "backup":
            return client.backups.run(**kwargs)
        if workflow == "template":
            return client.export_templates.run(11, **kwargs)
        return client.remote_targets.run(
            11,
            RemoteTargetInvokeRequest.model_validate(record("RemoteTargetInvokeRequest")),
            **kwargs,
        )

    try:
        for invalid in ({"poll_interval": 0}, {"timeout_seconds": float("nan")}):
            with pytest.raises(ValueError, match="must be"):
                await resolve(run(**invalid))
        assert not paths
        if status != "succeeded":
            with pytest.raises(TaskUnsuccessfulError):
                await resolve(run())
            assert not any(p.endswith("/output") for p in paths)
        else:
            result = await resolve(run())
            if workflow == "template":
                assert result.body == "template-output"
            elif workflow == "backup":
                assert isinstance(result, wire.BackupDocument)
            else:
                assert result.id == 17
        assert "/api/v1/tasks/17" in paths
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("terminal", ["succeeded", "failed", "expired", "confirmed"])
async def test_restore_capability_polling(asynchronous: bool, terminal: str) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert "authorization" not in request.headers
        assert request.headers["x-hubuum-restore-capability"] == "cap-secret"
        return httpx.Response(
            200,
            json=record("RestoreStageResponse")
            | {
                "id": 93,
                "status": "confirmed" if calls == 1 else terminal,
                "sha256": "digest-secret",
            },
        )

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="invalidated-token", transport=httpx.MockTransport(handler)
    )
    try:
        if terminal == "confirmed":
            with pytest.raises(TimeoutError):
                await resolve(client.restores.wait(93, capability="cap-secret", timeout_seconds=0))
        else:
            result = await resolve(
                client.restores.wait(93, capability="cap-secret", poll_interval=0.001)
            )
            assert result.status == terminal
            assert "secret" not in repr(result)
        with pytest.raises(ValueError, match="poll_interval"):
            await resolve(client.restores.wait(93, capability="cap-secret", poll_interval=0))
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_settings_json_patch_and_permission_absence(asynchronous: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/ReadClass"):
            return httpx.Response(404, json={"message": "missing"})
        assert request.headers["content-type"] == "application/json-patch+json"
        assert request.headers["if-match"] == '"revision-1"'
        assert json.loads(request.content) == [{"op": "add", "path": "/nullable", "value": None}]
        return httpx.Response(200, json={"revision": 2, "settings": {"nullable": None}})

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", transport=httpx.MockTransport(handler)
    )
    try:
        result = await resolve(
            client.principals.settings(11).json_patch(
                [SettingsPatchOperation(op="add", path="/nullable", value=None)],
                if_match='"revision-1"',
            )
        )
        assert result.settings == {"nullable": None}
        assert not await resolve(
            client.collections.permissions(11).check(12, Permission.READ_CLASS)
        )
    finally:
        await resolve(client.close())
    with pytest.raises(ValidationError) as error:
        SettingsPatchOperation.model_validate({"op": "move", "path": "/secret"})
    assert "/secret" not in str(error.value)
    assert error.value.__context__ is None


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("transport_failure", [False, True])
async def test_remote_request_diagnostics_redact_nested_and_url_secrets(
    asynchronous: bool, transport_failure: bool
) -> None:

    secrets = ["url-password", "query-secret", "header-secret", "body-secret", "alias-secret"]

    def handler(request: httpx.Request) -> httpx.Response:
        message = " ".join(secrets)
        if transport_failure:
            raise httpx.ConnectError(message, request=request)
        return httpx.Response(400, json={"message": message, "details": message})

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", transport=httpx.MockTransport(handler)
    )
    payload = RemoteTargetCreate.model_validate(
        record("NewRemoteTarget")
        | {
            "url_template": "https://user:url-password@example.test/?token=query-secret",
            "headers_template": {"X-Custom": "header-secret"},
            "body_template": "body-secret",
            "auth_config": {"type": "bearer_secret", "secret": "alias-secret"},
        }
    )
    try:
        with pytest.raises((APIError, TransportError)) as error:
            await resolve(client.remote_targets.create(payload))
        for secret in secrets:
            assert secret not in str(error.value)
            assert secret not in repr(vars(error.value))
        assert error.value.__context__ is None
    finally:
        await resolve(client.close())
