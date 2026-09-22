from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable
from datetime import UTC, datetime
from pathlib import Path
from runpy import run_path
from typing import Any, TypeVar

import httpx
import pytest
from pydantic import ValidationError

from hubuum_client import (
    APIError,
    AsyncClient,
    Client,
    ConfirmRestoreOperation,
    CreateTokenOperation,
    CreateUserOperation,
    CredentialApprovalRequest,
    CredentialApprovalResponse,
    CredentialApprovalSecret,
    DecodeError,
    ImportCredentialsOperation,
    ImportGraph,
    ImportRequest,
    NewTokenRequest,
    OpenAPIOptions,
    PermissionDeniedError,
    PrincipalId,
    ReauthenticationRequiredError,
    RenewTokenOperation,
    RenewTokenRequest,
    RequestOptions,
    RestoreConfirmRequest,
    RestoreJobId,
    Task,
    TaskDetails,
    TaskKind,
    TaskOutputDiscoveryState,
    TaskQuery,
    TaskStatus,
    TokenId,
    TransportError,
    UpdateUserOperation,
    UserCreate,
    UserId,
    UserUpdate,
)

T = TypeVar("T")
NOW = "2026-09-22T12:00:00Z"
EXPIRY = "2026-09-23T12:00:00.123456"
SECRET = "hca1." + "a" * 64
RECORD = {
    "id": 11,
    "actor_id": 7,
    "token_id": 9,
    "operation": "create_token",
    "authenticated_at": NOW,
    "expires_at": "2026-09-22T12:02:00Z",
}
APPROVAL = {"approval": SECRET, "record": RECORD, "token_expires_at": EXPIRY}
USER = {
    "id": 7,
    "name": "human",
    "created_at": NOW,
    "updated_at": NOW,
    "revision": 1,
    "identity_scope_id": 1,
    "provider_managed": False,
}
TASK = {
    "id": 23,
    "kind": "import",
    "status": "succeeded",
    "created_at": NOW,
    "progress": {"total_items": 0, "processed_items": 0, "success_items": 0, "failed_items": 0},
    "links": {"task": "/api/v1/tasks/23", "events": "/api/v1/tasks/23/events"},
}


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("renew", [False, True])
async def test_approved_tokens_copy_normalized_expiry_and_read_evidence(
    asynchronous: bool,
    renew: bool,
) -> None:
    token = NewTokenRequest(name="reader")
    operation = (
        RenewTokenOperation(
            principal_id=PrincipalId(7), token_id=TokenId(9), token=RenewTokenRequest()
        )
        if renew
        else CreateTokenOperation(principal_id=PrincipalId(7), token=token)
    )
    payload = CredentialApprovalRequest(password="fresh-password", operation=operation)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["authorization"] == "Bearer session"
        if request.url.path == "/api/v1/iam/credential-approvals":
            assert "X-Hubuum-Credential-Approval" not in request.headers
            assert json.loads(request.content) == payload.payload()
            assert json.loads(request.content)["operation"]["kind"] == operation.kind
            return httpx.Response(201, json=APPROVAL)
        if request.url.path.endswith("credential-approvals/11"):
            assert "X-Hubuum-Credential-Approval" not in request.headers
            return httpx.Response(200, json={**RECORD, "consumed_at": NOW})
        assert request.headers["X-Hubuum-Credential-Approval"] == SECRET
        assert request.url.path == "/api/v1/iam/principals/7/tokens" + ("/9/renew" if renew else "")
        assert json.loads(request.content) == (
            {"expires_at": EXPIRY}
            if renew
            else {
                "name": "reader",
                "expires_at": EXPIRY,
            }
        )
        return httpx.Response(201, json={"token": "new-bearer", "expires_at": EXPIRY})

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        assert client.credential_approvals is client.credential_approvals
        approval = await _resolve(client.credential_approvals.create(payload))
        service = client.tokens.for_principal(7)
        issued = await _resolve(
            service.renew(9, approval=approval)
            if renew
            else service.create(token, approval=approval)
        )
        assert issued.value == "new-bearer"
        assert issued.expires_at == datetime.fromisoformat(EXPIRY)
        assert token.expires_at is None
        assert (await _resolve(client.credential_approvals.get(approval.record.id))).consumed_at
        assert len(requests) == 3
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "kind", ["create_user", "update_user", "import_credentials", "confirm_restore"]
)
async def test_approved_mutations_preserve_exact_nested_body_and_headers(
    asynchronous: bool,
    kind: str,
) -> None:
    create = UserCreate(name="human", password="new-password")
    update = UserUpdate(password="replacement-password")
    imported = ImportRequest(
        graph=ImportGraph(principals=({"password_hash": "hash-secret"},)), dry_run=True
    )
    confirmation = RestoreConfirmRequest(
        restore_capability="restore-secret", sha256="digest", confirmation="phrase"
    )
    operation = {
        "create_user": CreateUserOperation(user=create),
        "update_user": UpdateUserOperation(user_id=UserId(7), user=update),
        "import_credentials": ImportCredentialsOperation(import_=imported),
        "confirm_restore": ConfirmRestoreOperation(
            restore_id=RestoreJobId(12), confirmation=confirmation
        ),
    }[kind]
    approved_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/iam/credential-approvals":
            body = json.loads(request.content)
            assert body["operation"]["kind"] == kind
            key = {
                "create_user": "user",
                "update_user": "user",
                "import_credentials": "import",
                "confirm_restore": "confirmation",
            }[kind]
            approved_body.update(body["operation"][key])
            return httpx.Response(201, json=APPROVAL)
        assert request.headers["X-Hubuum-Credential-Approval"] == SECRET
        assert json.loads(request.content) == approved_body
        if kind == "update_user":
            assert request.headers["If-Match"] == '"1"'
            assert request.headers["X-Request-ID"] == "req"
        if kind == "import_credentials":
            assert approved_body["version"] == 2
            assert request.headers["Idempotency-Key"] == "import-key"
            return httpx.Response(202, json=TASK)
        return httpx.Response(
            200, json=USER if kind != "confirm_restore" else {"status": "confirmed"}
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        approval = await _resolve(
            client.credential_approvals.create(
                CredentialApprovalRequest(password="actor-password", operation=operation)
            )
        )
        if kind == "create_user":
            assert (await _resolve(client.users.create(create, approval=approval))).id == 7
        elif kind == "update_user":
            assert (
                await _resolve(
                    client.users.update(
                        7,
                        update,
                        approval=approval,
                        options=RequestOptions(headers={"If-Match": '"1"', "X-Request-ID": "req"}),
                    )
                )
            ).id == 7
        elif kind == "import_credentials":
            assert (
                await _resolve(
                    client.imports.submit(imported, approval=approval, idempotency_key="import-key")
                )
            ).id == 23
        else:
            await _resolve(
                client.openapi.call(
                    "postApiV1RestoresByRestoreIdConfirm",
                    json=confirmation,
                    options=OpenAPIOptions(
                        path_params={"restore_id": 12}, headers=approval.headers()
                    ),
                )
            )
    finally:
        await _resolve(client.close())


def test_approval_secrets_and_requests_are_redacted_and_strict() -> None:
    approval = CredentialApprovalResponse.model_validate(APPROVAL)
    secret = CredentialApprovalSecret(SECRET)
    for value in (
        repr(secret),
        str(secret),
        repr(approval),
        str(approval),
        approval.model_dump_json(),
    ):
        assert SECRET not in value
    assert approval.headers() == {"X-Hubuum-Credential-Approval": SECRET}
    request = CredentialApprovalRequest(
        password="password-secret",
        operation=CreateUserOperation(
            user=UserCreate(name="human", password="new-password-secret")
        ),
    )
    assert "password-secret" not in repr(request)
    assert "new-password-secret" not in repr(request.operation)
    with pytest.raises(ValidationError):
        CredentialApprovalRequest.model_validate({**request.payload(), "unexpected": True})
    with pytest.raises(ValidationError):
        CredentialApprovalRequest.model_validate(
            {"password": "secret", "operation": {"kind": "unknown"}}
        )
    with pytest.raises(ValueError, match="token_expires_at"):
        CredentialApprovalResponse.model_validate(
            {**APPROVAL, "token_expires_at": None}
        ).token_request(NewTokenRequest())
    explicit = NewTokenRequest(expires_at=datetime(2026, 9, 23, 12, 0, 0, 123457))
    assert approval.token_request(explicit).expires_at == datetime.fromisoformat(EXPIRY)
    assert explicit.expires_at != approval.token_expires_at


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("reason", ["reauthentication_required", "permission_denied", None, 17])
async def test_reauthentication_reason_and_secret_redaction(
    asynchronous: bool, reason: object
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            403,
            json={
                "error": "Forbidden",
                "reason": reason,
                "message": f"rejected {SECRET} actor-password",
                "approval": SECRET,
            },
            headers={"X-Request-ID": SECRET},
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(PermissionDeniedError) as caught:
            await _resolve(
                client.request(
                    "POST",
                    "/api/v1/imports",
                    json={"password": "actor-password"},
                    options=RequestOptions(headers={"X-Hubuum-Credential-Approval": SECRET}),
                )
            )
        error = caught.value
        assert isinstance(error, ReauthenticationRequiredError) is (
            reason == "reauthentication_required"
        )
        assert error.reason == (reason if isinstance(reason, str) else None)
        for value in (str(error), repr(error), repr(error.__dict__)):
            assert SECRET not in value
            assert "actor-password" not in value
        assert calls == 1
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_transport_failure_redacts_approval(asynchronous: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with {SECRET}", request=request)

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TransportError) as caught:
            await _resolve(
                client.request(
                    "POST",
                    "/api/v1/imports",
                    options=RequestOptions(headers={"X-Hubuum-Credential-Approval": SECRET}),
                )
            )
        assert SECRET not in str(caught.value)
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_task_discovery_filters_survive_cursor_pagination(asynchronous: bool) -> None:
    query = TaskQuery(
        kind=(TaskKind.IMPORT,),
        status=(TaskStatus.SUCCEEDED, TaskStatus.FAILED),
        terminal=True,
        import_dry_run=False,
        created_after=datetime(2026, 9, 22, tzinfo=UTC),
    )
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        params = dict(request.url.params)
        assert params == {
            "kind": "import",
            "status": "succeeded,failed",
            "terminal": "true",
            "import_dry_run": "false",
            "created_after": "2026-09-22T00:00:00+00:00",
            "limit": "1",
            "sort": "id.asc",
            "include_total": "true",
            **({"cursor": "next"} if calls == 2 else {}),
        }
        return httpx.Response(
            200,
            json=[
                {
                    **TASK,
                    "id": calls,
                    "details": {
                        "import": {"results_url": "/results", "retained": {"dry_run": False}}
                    },
                }
            ],
            headers={"X-Total-Count": "2", **({"X-Next-Cursor": "next"} if calls == 1 else {})},
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        paginated: TaskQuery = query.limit(1).sort("id.asc").include_total()
        tasks = await _resolve(client.tasks.all(paginated))
        assert [task.id for task in tasks] == [1, 2]
        assert query.limit_value is None
        assert tasks[0].details
        assert tasks[0].details.import_
        assert tasks[0].details.import_.retained
        assert tasks[0].details.import_.retained.dry_run is False
        assert tasks[0].details.import_.retained.has_failed_items is None
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize(
    ("kind", "detail"),
    [
        (
            "schema_validation",
            {
                "class_id": 12,
                "schema_revision": 2,
                "work_kind": "impact",
                "work_status": "complete",
                "results_url": "/results",
            },
        ),
        ("reindex", {"class_id": 12, "computation_revision": 3}),
        (
            "remote_call",
            {"remote_target_id": 4, "target": {"type": "object", "object_id": 13, "class_id": 12}},
        ),
        (
            "backup",
            {
                "output_url": "/output",
                "output_available": False,
                "output_expired": True,
                "retained": {"include_history": False, "output_state": "expired"},
            },
        ),
        (
            "export",
            {
                "output_url": "/output",
                "output_available": False,
                "output_expired": False,
                "retained": {
                    "output_state": "unknown",
                    "target": {"type": "class", "class_id": 12},
                },
            },
        ),
    ],
)
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_all_task_detail_variants_decode(
    asynchronous: bool, kind: str, detail: dict[str, Any]
) -> None:
    cls = AsyncClient if asynchronous else Client
    client = cls(
        "https://hubuum.test",
        token="session",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={**TASK, "kind": kind, "details": {kind: detail}}
            )
        ),
    )
    try:
        task = await _resolve(client.tasks.get(23))
        assert task.details is not None
        assert getattr(task.details, kind).model_dump(mode="json", exclude_none=True) == detail
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize(
    "target",
    [
        {"type": "collection", "collection_id": 1},
        {"type": "class_relation", "relation_id": 2},
        {"type": "object_relation", "relation_id": 3},
        {"type": "object", "object_id": 4},
    ],
)
def test_discovery_target_variants(target: dict[str, Any]) -> None:
    details = TaskDetails.model_validate({"remote_call": {"target": target}})
    assert details.remote_call
    assert details.remote_call.target
    assert details.remote_call.target.model_dump(exclude_none=True) == target
    assert Task.model_validate({**TASK, "details": None}).details is None
    assert dict(TaskQuery(output_state=TaskOutputDiscoveryState.UNKNOWN).as_params()) == {
        "output_state": "unknown"
    }


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_malformed_approval_does_not_retain_secret_in_exception_chain(
    asynchronous: bool,
) -> None:
    cls = AsyncClient if asynchronous else Client
    client = cls(
        "https://hubuum.test",
        token="session",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(201, json={"approval": SECRET})
        ),
    )
    try:
        with pytest.raises(DecodeError) as caught:
            await _resolve(
                client.credential_approvals.create(
                    CredentialApprovalRequest(
                        password="actor-password",
                        operation=CreateTokenOperation(
                            principal_id=PrincipalId(7), token=NewTokenRequest()
                        ),
                    )
                )
            )
        assert SECRET not in str(caught.value)
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("validation", ["constructor", "python", "json", "strings"])
@pytest.mark.parametrize(
    "payload",
    [
        {"password": "actor-secret"},
        {"password": {"raw": "actor-secret"}, "operation": {"kind": "create_user"}},
        {"password": "actor-secret", "operation": {"kind": "discriminator-secret"}},
        {
            "password": "actor-secret",
            "operation": {"kind": "create_user", "user": {"password": "new-password-secret"}},
        },
        {
            "password": "actor-secret",
            "operation": {
                "kind": "import_credentials",
                "import": {
                    "graph": {"principals": [{"password_hash": "hash-secret"}]},
                    "version": "invalid",
                },
            },
        },
        {
            "password": "actor-secret",
            "operation": {
                "kind": "confirm_restore",
                "restore_id": "12",
                "confirmation": {"restore_capability": "restore-secret"},
            },
        },
        {
            "password": "actor-secret",
            "extra-secret": "extra-value-secret",
            "operation": {
                "kind": "create_user",
                "user": {"name": "human", "password": "new-password-secret"},
            },
        },
    ],
    ids=[
        "missing-operation",
        "invalid-password",
        "invalid-discriminator",
        "nested-user",
        "nested-import",
        "nested-restore",
        "unknown-field",
    ],
)
def test_approval_validation_errors_discard_secret_inputs(
    validation: str,
    payload: dict[str, Any],
) -> None:
    validators = {
        "constructor": lambda: CredentialApprovalRequest(**payload),
        "python": lambda: CredentialApprovalRequest.model_validate(payload),
        "json": lambda: CredentialApprovalRequest.model_validate_json(json.dumps(payload)),
        "strings": lambda: CredentialApprovalRequest.model_validate_strings(payload),
    }
    with pytest.raises(ValidationError) as caught:
        validators[validation]()
    error = caught.value
    for diagnostic in (str(error), repr(error), repr(error.errors()), error.json()):
        assert "-secret" not in diagnostic
    assert error.__cause__ is None
    assert error.__context__ is None
    assert all(item["input"] == "<redacted>" for item in error.errors())
    assert all("ctx" not in item for item in error.errors())
    assert all(item["loc"] in {(), ("operation",), ("password",)} for item in error.errors())


def test_approval_validation_errors_strip_nested_exception_context() -> None:
    # RestoreTimestamps raises ValueError through a model validator, producing
    # a ctx.error object as well as the rejected credential-bearing import.
    with pytest.raises(ValidationError) as caught:
        CredentialApprovalRequest.model_validate(
            {
                "password": "actor-secret",
                "operation": {
                    "kind": "import_credentials",
                    "import": {
                        "graph": {
                            "collections": [
                                {
                                    "name": "collection",
                                    "description": "",
                                    "timestamps": {
                                        "created_at": "2026-09-23T12:00:00",
                                        "updated_at": "2026-09-22T12:00:00",
                                    },
                                }
                            ],
                            "principals": [{"password_hash": "hash-secret"}],
                        },
                    },
                },
            }
        )
    assert "value_error" in {item["type"] for item in caught.value.errors()}
    assert all("ctx" not in item for item in caught.value.errors())
    assert "-secret" not in caught.value.json()
    assert caught.value.__context__ is None


def test_approval_json_parser_errors_discard_original_document() -> None:
    with pytest.raises(ValidationError) as caught:
        CredentialApprovalRequest.model_validate_json('{"password":"actor-secret",')
    assert caught.value.errors()[0]["type"] == "json_invalid"
    assert caught.value.errors()[0]["input"] == "<redacted>"
    assert "actor-secret" not in caught.value.json()
    assert caught.value.__context__ is None


def test_valid_approval_validation_preserves_wire_payload() -> None:
    payload = {
        "password": "actor-secret",
        "operation": {
            "kind": "create_user",
            "user": {"name": "human", "password": "new-password-secret"},
        },
    }
    assert CredentialApprovalRequest.model_validate_json(json.dumps(payload)).payload() == payload
    assert CredentialApprovalRequest.model_validate(payload).payload() == payload


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("password", ["authentication", "reauthentication_required"])
@pytest.mark.parametrize("status", [403, 401])
async def test_reauthentication_classification_precedes_secret_redaction(
    asynchronous: bool,
    password: str,
    status: int,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {"password": password}
        return httpx.Response(
            status,
            json={
                "error": "Forbidden",
                "reason": "reauthentication_required",
                "message": f"rejected {password}",
            },
        )

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(APIError) as caught:
            await _resolve(client.users.update(7, UserUpdate(password=password)))
        error = caught.value
        assert isinstance(error, ReauthenticationRequiredError) is (status == 403)
        expected_reason = "reauthentication_required".replace(password, "<redacted>")
        assert error.reason == expected_reason
        assert error.response_body["reason"] == expected_reason
        assert password not in str(error)
        assert password not in repr(error.__dict__)
    finally:
        await _resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "created_at", ["2026-09-22T12:00:00.123456", "2026-09-22T14:00:00.123456+02:00"]
)
async def test_live_discovery_excludes_large_existing_task_history(
    asynchronous: bool,
    created_at: str,
) -> None:
    live_tests = run_path(
        str(Path(__file__).parents[1] / "e2e" / "test_credentials_and_discovery.py")
    )
    query = live_tests["_discovery_query"](Task.model_validate({**TASK, "created_at": created_at}))
    # More old matching tasks than all()'s 100-page guard, plus newer matches.
    history = [{**TASK, "id": i, "created_at": "2026-09-22T11:00:00Z"} for i in range(150)]
    target = {**TASK, "id": 150, "created_at": "2026-09-22T12:00:00.123456Z"}
    later = {**TASK, "id": 151, "created_at": "2026-09-22T12:00:00.123457Z"}
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        params = request.url.params
        matches = [*history, target, later]
        for bound, lower in (("created_after", True), ("created_before", False)):
            if bound in params:
                timestamp = datetime.fromisoformat(params[bound])
                assert timestamp.utcoffset() is not None
                matches = [
                    item
                    for item in matches
                    if (
                        datetime.fromisoformat(str(item["created_at"])) >= timestamp
                        if lower
                        else datetime.fromisoformat(str(item["created_at"])) < timestamp
                    )
                ]
        offset = int(params.get("cursor", "0"))
        page = matches[offset : offset + 1]
        headers = {"X-Total-Count": str(len(matches))}
        if offset + 1 < len(matches):
            headers["X-Next-Cursor"] = str(offset + 1)
        return httpx.Response(200, json=page, headers=headers)

    cls = AsyncClient if asynchronous else Client
    client = cls("https://hubuum.test", token="session", transport=httpx.MockTransport(handler))
    try:
        tasks = await _resolve(client.tasks.all(query.limit(1).include_total().sort("id.asc")))
        assert [task.id for task in tasks] == [150]
        assert calls == 1
    finally:
        await _resolve(client.close())
