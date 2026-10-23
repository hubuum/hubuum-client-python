from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable
from pathlib import Path
from typing import Any, TypeVar, cast

import httpx
import pytest
from pydantic import ValidationError

import hubuum_client as public
from hubuum_client import (
    AsyncClient,
    Client,
    ImportComputedFieldInput,
    ImportEventSinkInput,
    ImportEventSubscriptionInput,
    ImportExportTemplateInput,
    ImportGraph,
    ImportGroupInput,
    ImportGroupMembershipInput,
    ImportIdentityScopeInput,
    ImportPrincipalInputHuman,
    ImportPrincipalInputServiceAccount,
    ImportRemoteTargetInput,
    ImportRequest,
    TaskStatus,
)
from hubuum_client.models import RequestModel

T = TypeVar("T")
FIXTURE = Path(__file__).parents[1] / "fixtures" / "import-graph.json"
SECTIONS: dict[str, type[RequestModel]] = {
    "identity_scopes": ImportIdentityScopeInput,
    "groups": ImportGroupInput,
    "principals": ImportPrincipalInputServiceAccount,
    "group_memberships": ImportGroupMembershipInput,
    "export_templates": ImportExportTemplateInput,
    "remote_targets": ImportRemoteTargetInput,
    "event_sinks": ImportEventSinkInput,
    "event_subscriptions": ImportEventSubscriptionInput,
    "computed_fields": ImportComputedFieldInput,
}


def graph_data() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE.read_text()))


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


def assert_redacted(error: ValidationError, secret: str) -> None:
    assert secret not in str(error)
    assert secret not in repr(error)
    assert secret not in repr(error.errors())
    assert secret not in error.json()
    assert error.__context__ is None
    assert error.__cause__ is None


def test_mixed_graph_preserves_wire_fields_and_counts_typed_sections() -> None:
    data = graph_data()
    graph = ImportGraph.model_validate(data)
    assert graph.total_items == 12
    assert graph.payload() == data
    assert ImportRequest(graph=graph, dry_run=True).payload() == {
        "version": 2,
        "dry_run": True,
        "graph": data,
    }
    for section, model in SECTIONS.items():
        assert isinstance(getattr(graph, section)[0], model)
        assert getattr(public, model.__name__) is model
    assert graph.identity_scopes[0].ref_ == "scope"
    assert graph.principals[0].kind == "service_account"
    assert graph.group_memberships[0].sources[0].timestamps is not None
    assert graph.remote_targets[0].auth_config.type == "none"


@pytest.mark.parametrize("section", SECTIONS)
def test_extended_sections_reject_unknown_fields_without_leaking_inputs(section: str) -> None:
    item = graph_data()[section][0]
    secret = "unknown-field-containing-a-secret"
    item[secret] = "secret-value"
    cases: list[tuple[type[RequestModel], dict[str, Any]]] = [
        (SECTIONS[section], item),
        (ImportGraph, {section: [item]}),
        (ImportRequest, {"graph": {section: [item]}}),
    ]
    for model, value in cases:
        with pytest.raises(ValidationError) as caught:
            model.model_validate(value)
        assert_redacted(caught.value, secret)
        assert_redacted(caught.value, "secret-value")


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("identity_scopes", "provider_kind", {}),
        ("groups", "managed_by", []),
        ("principals", "kind", "invalid-secret-kind"),
        ("principals", "password", "service-account-password"),
        ("group_memberships", "sources", [{"source": "local"}]),
        ("export_templates", "content_type", "image/png"),
        ("remote_targets", "method", "put"),
        ("remote_targets", "auth_config", {"type": "basic_secret", "secret": "sensitive"}),
        ("event_sinks", "kind", "unknown"),
        ("event_sinks", "delivery_policy", {"min_interval_ms": 0}),
        ("event_sinks", "delivery_policy", {"min_interval_ms": 86_400_001}),
        ("event_subscriptions", "actions", "updated"),
        ("computed_fields", "result_type", "float"),
        ("computed_fields", "operation", []),
    ],
)
def test_invalid_section_fields_are_rejected(section: str, field: str, value: Any) -> None:
    data = graph_data()
    data[section][0][field] = value
    with pytest.raises(ValidationError) as caught:
        ImportGraph.model_validate(data)
    assert_redacted(caught.value, "sensitive")
    assert_redacted(caught.value, "invalid-secret-kind")


@pytest.mark.parametrize(
    ("section", "selector", "key"),
    [
        ("groups", "identity_scope", {"name": "local"}),
        ("principals", "identity_scope", {"name": "local"}),
        ("principals", "owner_group", {"groupname": "ops"}),
        ("group_memberships", "principal", {"name": "worker"}),
        ("group_memberships", "group", {"groupname": "ops"}),
        ("export_templates", "collection", {"name": "inventory"}),
        ("remote_targets", "collection", {"name": "inventory"}),
        ("event_subscriptions", "collection", {"name": "inventory"}),
        ("event_subscriptions", "sink", {"name": "sink"}),
        ("computed_fields", "class", {"name": "server", "collection_ref": "inventory"}),
    ],
)
def test_required_selectors_accept_keys_and_reject_missing_or_ambiguous_pairs(
    section: str, selector: str, key: dict[str, Any]
) -> None:
    item = graph_data()[section][0]
    model = SECTIONS[section]
    item[f"{selector}_key"] = key
    with pytest.raises(ValidationError):
        model.model_validate(item)
    item.pop(f"{selector}_ref")
    assert model.model_validate(item).payload()[f"{selector}_key"] == key
    item.pop(f"{selector}_key")
    with pytest.raises(ValidationError):
        model.model_validate(item)


@pytest.mark.parametrize("section", ["export_templates", "remote_targets", "computed_fields"])
def test_class_keys_require_an_unambiguous_collection(section: str) -> None:
    item = graph_data()[section][0]
    item.pop("class_ref", None)
    item["class_key"] = {"name": "server"}
    with pytest.raises(ValidationError):
        SECTIONS[section].model_validate(item)
    item["class_key"]["collection_ref"] = "inventory"
    assert SECTIONS[section].model_validate(item).payload()["class_key"] == item["class_key"]
    item["class_ref"] = "server"
    with pytest.raises(ValidationError):
        SECTIONS[section].model_validate(item)


def test_membership_source_and_service_account_creator_selectors() -> None:
    item = graph_data()["group_memberships"][0]
    source = item["sources"][0]
    source.pop("source_scope_ref")
    with pytest.raises(ValidationError):
        ImportGroupMembershipInput.model_validate(item)
    source["source_scope_key"] = {"name": "local"}
    assert ImportGroupMembershipInput.model_validate(item).sources[0].source_scope_key
    source["source_scope_ref"] = "local"
    with pytest.raises(ValidationError):
        ImportGroupMembershipInput.model_validate(item)
    account = graph_data()["principals"][0]
    account["created_by_key"] = {"name": "admin"}
    assert ImportPrincipalInputServiceAccount.model_validate(account).created_by_key
    account["created_by_ref"] = "admin"
    with pytest.raises(ValidationError):
        ImportPrincipalInputServiceAccount.model_validate(account)


def test_personal_computed_fields_require_an_owner_and_shared_fields_reject_one() -> None:
    item = graph_data()["computed_fields"][0]
    item["owner_ref"] = "worker"
    with pytest.raises(ValidationError):
        ImportComputedFieldInput.model_validate(item)
    item["visibility"] = "personal"
    assert ImportComputedFieldInput.model_validate(item).owner_ref == "worker"
    item.pop("owner_ref")
    with pytest.raises(ValidationError):
        ImportComputedFieldInput.model_validate(item)
    item["owner_key"] = {"name": "worker"}
    assert ImportComputedFieldInput.model_validate(item).owner_key


@pytest.mark.parametrize("credential", ["password", "password_hash"])
def test_human_principals_preserve_credentials_and_hide_validation_inputs(credential: str) -> None:
    secret = "human-credential-secret"
    item: dict[str, Any] = {
        "kind": "human",
        "name": "alice",
        "provider_managed": False,
        "identity_scope_key": {"name": "local"},
        credential: secret,
        "settings": None,
    }
    human = ImportPrincipalInputHuman.model_validate(item)
    graph = ImportGraph(principals=(human,))
    assert human.payload() == item
    assert graph.payload()["principals"] == [item]
    assert secret not in repr(human)
    assert secret not in str(human)
    assert secret not in repr(graph)
    item["password" if credential == "password_hash" else "password_hash"] = "other-secret"
    with pytest.raises(ValidationError) as caught:
        ImportPrincipalInputHuman.model_validate(item)
    assert_redacted(caught.value, secret)
    assert_redacted(caught.value, "other-secret")
    item.pop("identity_scope_key")
    with pytest.raises(ValidationError) as caught:
        ImportPrincipalInputHuman.model_validate(item)
    assert_redacted(caught.value, secret)


@pytest.mark.parametrize(
    "auth",
    [
        {"type": "none"},
        {"type": "bearer_secret", "secret": "auth-secret"},
        {"type": "basic_secret", "username": "private-user", "secret": "auth-secret"},
        {"type": "api_key_secret", "header": "X-Private", "secret": "auth-secret"},
    ],
)
def test_remote_authentication_variants_preserve_wire_values(auth: dict[str, str]) -> None:
    item = graph_data()["remote_targets"][0]
    item["auth_config"] = auth
    target = ImportRemoteTargetInput.model_validate(item)
    assert target.payload()["auth_config"] == auth
    assert "auth-secret" not in repr(target.auth_config)
    assert "private-user" not in repr(target.auth_config)


def test_integration_configuration_and_explicit_nulls_survive_serialization() -> None:
    data = graph_data()
    secret = "integration-secret"
    data["remote_targets"][0].update(
        {
            "url_template": f"https://user:{secret}@example.invalid/",
            "headers_template": {"Authorization": secret},
            "body_template": secret,
        }
    )
    data["event_sinks"][0].update(
        {"config": {"headers": {"Authorization": secret}}, "secret_ref": secret}
    )
    data["event_subscriptions"][0].update({"filter": None, "routing": {"secret": secret}})
    data["computed_fields"][0]["operation"] = {"secret": secret}
    data["export_templates"][0]["template"] = secret
    graph = ImportGraph.model_validate(data)
    assert graph.payload() == data
    assert secret not in repr(graph)
    for section in SECTIONS:
        assert secret not in repr(getattr(graph, section)[0])
    omitted = graph_data()["remote_targets"][0]
    omitted.pop("auth_config")
    assert ImportRemoteTargetInput.model_validate(omitted).payload() == omitted


@pytest.mark.parametrize("model", [ImportGraph, ImportRequest, ImportPrincipalInputHuman])
def test_malformed_json_never_retains_import_secrets(model: type[RequestModel]) -> None:
    with pytest.raises(ValidationError) as caught:
        model.model_validate_json('{"password": "json-secret", bad-json')
    assert_redacted(caught.value, "json-secret")


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_typed_import_submission_preserves_the_complete_wire_body(asynchronous: bool) -> None:
    data = graph_data()
    payload = ImportRequest(graph=ImportGraph.model_validate(data), dry_run=True)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "POST"
        assert request.url.path == "/api/v1/imports"
        assert request.headers["Idempotency-Key"] == "mixed-import"
        assert json.loads(request.content) == {"version": 2, "dry_run": True, "graph": data}
        return httpx.Response(
            202,
            json={
                "id": 42,
                "kind": "import",
                "status": "queued",
                "submitted_by": 7,
                "created_at": "2026-10-23T12:00:00",
                "updated_at": "2026-10-23T12:00:00",
                "progress": {
                    "total_items": 12,
                    "processed_items": 0,
                    "success_items": 0,
                    "failed_items": 0,
                },
                "links": {"task": "/api/v1/tasks/42", "events": "/api/v1/tasks/42/events"},
            },
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        task = await resolve(client.imports.submit(payload, idempotency_key="mixed-import"))
        assert task.id == 42
        assert task.status is TaskStatus.QUEUED
        assert len(requests) == 1
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("failed", [0, 1])
async def test_dry_run_counts_planned_results_as_successes(asynchronous: bool, failed: int) -> None:
    task = {
        "id": 42,
        "kind": "import",
        "status": "partially_succeeded" if failed else "succeeded",
        "created_at": "2026-10-23T12:00:00",
        "progress": {
            "total_items": 2,
            "processed_items": 2,
            "success_items": 2 - failed,
            "failed_items": failed,
        },
        "links": {"task": "/api/v1/tasks/42", "events": "/api/v1/tasks/42/events"},
    }
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/results"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": index + 1,
                        "task_id": 42,
                        "entity_kind": "collection",
                        "action": "create",
                        "outcome": "failed" if index < failed else "planned",
                        "created_at": "2026-10-23T12:00:00",
                    }
                    for index in range(2)
                ],
            )
        if request.method == "POST":
            assert json.loads(request.content)["dry_run"] is True
        return httpx.Response(200, json=task)

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        result = await resolve(client.imports.run(ImportRequest(graph=ImportGraph(), dry_run=True)))
        assert result.succeeded == 2 - failed
        assert result.failed == failed
        assert len(requests) == 3
    finally:
        await resolve(client.close())
