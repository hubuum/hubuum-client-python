"""Public sync/async interaction behavior with no upstream provider implementation."""

from __future__ import annotations

import gzip
import inspect
import json
from collections.abc import AsyncIterator, Awaitable, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TypeVar
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr

from hubuum_client import (
    AccessToken,
    APIError,
    ApprovalInteraction,
    ApprovedCredentialOperation,
    AsyncApprovalInteraction,
    AsyncApprovedCredentialOperation,
    AsyncClient,
    AsyncLoginInteraction,
    AsyncProviderVerificationInteraction,
    AuthenticationInteractionError,
    AuthenticationInteractionRequest,
    AuthenticationProviderInput,
    Client,
    ClientOptions,
    CreateTokenOperation,
    Credentials,
    DecodeError,
    LoginInteraction,
    NewTokenRequest,
    PrincipalId,
    ProviderCredentialInput,
    ProviderVerificationInteraction,
    SecurityCandidateActivated,
    SecurityCandidateReport,
    SecurityCandidateRequest,
    TransportError,
)
from hubuum_client import _interactions as policy
from hubuum_client import async_client as async_client_module
from hubuum_client import client as sync_client_module

T = TypeVar("T")


async def resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


Flow = LoginInteraction | AsyncLoginInteraction
REQUEST = AuthenticationInteractionRequest(client_id="sdk-fixture", provider_id="local")


async def begin(client: Client | AsyncClient) -> Flow:
    if isinstance(client, AsyncClient):
        return await client.auth.begin_login(REQUEST)
    return client.auth.begin_login(REQUEST)


async def complete(flow: Flow) -> Client | AsyncClient:
    if isinstance(flow, AsyncLoginInteraction):
        return await flow.complete()
    return flow.complete()


async def begin_approval(
    client: Client | AsyncClient, operation: CreateTokenOperation
) -> ApprovalInteraction | AsyncApprovalInteraction:
    if isinstance(client, AsyncClient):
        return await client.auth.begin_approval(REQUEST, operation)
    return client.auth.begin_approval(REQUEST, operation)


async def authenticate(
    client: Client | AsyncClient, server: Server, value: str = "access-fixture"
) -> None:
    pair = server.session()
    pair["access_token"] = value
    server.push(200, pair)
    if isinstance(client, AsyncClient):
        await client.login_session(
            Credentials("admin", "fixture-password"), client_id="sdk-fixture"
        )
    else:
        client.login_session(Credentials("admin", "fixture-password"), client_id="sdk-fixture")


def approval(operation: str = "create_token") -> dict[str, object]:
    now = datetime.now(UTC)
    return {
        "approval": "hca1." + "c" * 64,
        "token_expires_at": (now + timedelta(hours=1)).replace(tzinfo=None).isoformat(),
        "record": {
            "id": 123,
            "actor_id": 7,
            "token_id": 18,
            "operation": operation,
            "target_id": 42,
            "restore_job_id": None,
            "authenticated_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=2)).isoformat(),
            "consumed_at": None,
            "invalidated_at": None,
        },
    }


def candidate(identifier: str, *, verified: bool = False) -> dict[str, object]:
    result: dict[str, object] = {
        "id": identifier,
        "group": "authentication",
        "base_revision": 7,
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        "checks": [],
        "state": "verified" if verified else "unverified",
        "providers": [],
    }
    if verified:
        result["verification_receipt"] = "hcv1." + "b" * 64
    return result


def definition(kind: str) -> dict[str, object]:
    common: dict[str, object] = {
        "client_id": "fixture",
        "client_authentication": "client_secret_basic",
        "scopes": [],
        "membership": {
            "mode": "local_only",
            "refresh_interval_seconds": 300,
            "max_stale_seconds": 900,
        },
        "admission": {"mode": "existing_only"},
    }
    if kind == "ldap":
        return {
            "url": "ldaps://directory.example",
            "bind_dn": "cn=service,dc=example",
            "scope": "employees",
            "user_base_dn": "dc=example",
            "user_filter": "(uid={username})",
        }
    if kind == "oidc":
        return common | {
            "issuer": "https://identity.example/realm",
            "scopes": ["openid"],
            "signing_algorithms": ["RS256"],
        }
    return common | {
        "profile": "json_user",
        "authorization_endpoint": "https://identity.example/authorize",
        "token_endpoint": "https://identity.example/token",
        "profile_endpoint": "https://identity.example/account",
        "subject_pointer": "/id",
        "subject_type": "string",
        "name_pointer": "/login",
    }


class Server:
    def __init__(self) -> None:
        self.id = str(uuid4())
        self.expiry = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
        self.requests: list[httpx.Request] = []
        self.responses: list[httpx.Response | httpx.HTTPError] = []
        self.secret = "hai1." + "a" * 64

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, httpx.HTTPError):
            raise response
        return response

    def push(self, status: int, body: object = None, **headers: str) -> None:
        self.responses.append(httpx.Response(status, json=body, headers=headers))

    def begin(self, *, browser: str | None = None, **changes: object) -> None:
        self.push(
            201,
            {
                "id": self.id,
                "interaction_version": 1,
                "redemption_secret": self.secret,
                "expires_at": self.expiry,
                "interval_seconds": 5,
                "next": {"kind": "browser", "verification_uri": browser, "user_code": "public-code"}
                if browser is not None
                else {"kind": "credentials"},
                **changes,
            },
        )

    def status(self, state: str = "ready") -> dict[str, object]:
        return {"id": self.id, "expires_at": self.expiry, "state": state}

    def session(self) -> dict[str, str]:
        now = datetime.now(UTC)
        return {
            "session_id": self.id,
            "token_type": "Bearer",
            "access_token": "access-fixture",
            "refresh_token": "refresh-fixture",
            "access_expires_at": (now + timedelta(minutes=15)).isoformat(),
            "refresh_expires_at": (now + timedelta(days=7)).isoformat(),
            "absolute_expires_at": (now + timedelta(days=30)).isoformat(),
        }


@pytest.fixture(params=["sync", "async"])
async def client_server(
    request: pytest.FixtureRequest,
) -> AsyncIterator[tuple[Client | AsyncClient, Server]]:
    server = Server()
    cls = Client if request.param == "sync" else AsyncClient
    instance = cls("https://hubuum.example.invalid", transport=httpx.MockTransport(server))
    try:
        yield instance, server
    finally:
        await resolve(instance.close())


@pytest.mark.parametrize("case", ["session", "browser_password", "password_lost"])
async def test_session_and_credentials(
    client_server: tuple[Client | AsyncClient, Server], case: str
) -> None:
    client, server = client_server
    server.begin(
        browser="https://hubuum.example.invalid/verify" if case == "browser_password" else None
    )
    flow = await begin(client)
    assert server.secret not in repr(flow)
    if case == "session":
        server.push(200, server.status())
        await resolve(flow.submit_credentials(Credentials("user", "fixture-password")))
        server.push(200, server.session())
        assert await complete(flow) is client
        assert client.token is not None
        assert client.token.value == "access-fixture"
        with pytest.raises(AuthenticationInteractionError):
            await complete(flow)
        assert len(server.requests) == 3
    elif case == "browser_password":
        with pytest.raises(AuthenticationInteractionError):
            await resolve(flow.submit_credentials(Credentials("user", "not-sent")))
        assert len(server.requests) == 1
    else:
        server.responses.append(httpx.ReadTimeout("fixture-password"))
        with pytest.raises(TransportError) as failed:
            await resolve(flow.submit_credentials(Credentials("user", "fixture-password")))
        assert "fixture-password" not in str(failed.value)
        assert len(server.requests) == 2
    for rpc in server.requests[1:]:
        assert rpc.headers["authorization"] == "Hubuum-Interaction " + server.secret
        assert rpc.url.host == "hubuum.example.invalid"
        assert not rpc.url.query
        assert json.loads(rpc.content)["client_id"] == "sdk-fixture"


@pytest.mark.parametrize("case", ["early_poll", "slow_down", "terminal"])
async def test_bounded_polling(
    client_server: tuple[Client | AsyncClient, Server], monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    client, server = client_server
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(policy, "time", SimpleNamespace(monotonic=lambda: clock.now))
    server.begin()
    flow = await begin(client)
    if case == "early_poll":
        with pytest.raises(AuthenticationInteractionError):
            await resolve(flow.poll())
        assert len(server.requests) == 1
    elif case == "slow_down":
        clock.now = 5
        server.push(
            429,
            {"error": "AuthenticationFailed", "message": "Wait", "reason": "slow_down"},
            **{"Retry-After": "17"},
        )
        with pytest.raises(APIError, match="429"):
            await resolve(flow.poll())
        assert flow.poll_after >= 17
    else:
        clock.now = 5
        server.push(200, server.status("denied"))
        assert (await resolve(flow.poll())).terminal
        with pytest.raises(AuthenticationInteractionError):
            await resolve(flow.poll())
        assert len(server.requests) == 2


@pytest.mark.parametrize(
    "case", ["cancel", "cleanup_pending", "cleanup_uncertain", "completion_lost", "invalid_session"]
)
async def test_single_attempt_completion_and_cleanup(
    client_server: tuple[Client | AsyncClient, Server], case: str
) -> None:
    client, server = client_server
    server.begin()
    flow = await begin(client)
    if case == "cancel":
        server.push(204)
        await resolve(flow.cancel())
        with pytest.raises(AuthenticationInteractionError):
            await resolve(flow.cancel())
    elif case in {"cleanup_pending", "cleanup_uncertain"}:
        cleanup = flow.issued_session_cleanup()
        server.push(204 if case == "cleanup_pending" else 503)
        server.push(
            409, {"error": "Conflict", "message": "Pending", "reason": "interaction_pending"}
        )
        if case == "cleanup_pending":
            await resolve(cleanup.revoke())
        else:
            with pytest.raises(APIError, match="503"):
                await resolve(cleanup.revoke())
        assert [r.url.path.rsplit("/", 1)[-1] for r in server.requests[1:]] == ["cancel", "revoke"]
    else:
        if case == "completion_lost":
            server.responses.append(httpx.ReadTimeout(server.secret))
        else:
            server.push(200, {"access_token": "incomplete-fixture-session"})
        server.push(204)
        server.push(204)
        with pytest.raises((TransportError, DecodeError)) as failed:
            await complete(flow)
        assert server.secret not in str(failed.value)
        assert len(server.requests) == 4
        assert sum(r.url.path.endswith("/complete") for r in server.requests) == 1


@pytest.mark.parametrize(
    "case", ["foreign_browser", "secret_in_uri", "expired", "version", "proof", "interval"]
)
async def test_invalid_begin_never_authenticates(
    client_server: tuple[Client | AsyncClient, Server], case: str
) -> None:
    client, server = client_server
    changes: dict[str, object] = {}
    browser = None
    if case == "foreign_browser":
        browser = "https://foreign.invalid/verify"
    elif case == "secret_in_uri":
        browser = "https://hubuum.example.invalid/verify?secret=fixture"
    elif case == "expired":
        changes["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    elif case == "version":
        changes["interaction_version"] = 2
    elif case == "interval":
        changes["interval_seconds"] = True
    else:
        changes["redemption_secret"] = "invalid-fixture-proof"
    server.begin(browser=browser, **changes)
    with pytest.raises((AuthenticationInteractionError, DecodeError)):
        await begin(client)
    assert not client.is_authenticated
    assert len(server.requests) == 1


async def test_fresh_approval_retains_exact_operation_and_originating_bearer(
    client_server: tuple[Client | AsyncClient, Server],
) -> None:
    client, server = client_server
    await authenticate(client, server)
    operation = CreateTokenOperation(
        principal_id=PrincipalId(42), token=NewTokenRequest(name="fixture-token")
    )
    server.begin()
    flow = await begin_approval(client, operation)
    operation.token.name = "changed-after-begin"
    server.push(200, server.status())
    await resolve(flow.submit_credentials(Credentials("admin", "fixture-password")))
    server.push(200, approval())
    approved: ApprovedCredentialOperation | AsyncApprovedCredentialOperation
    if isinstance(flow, AsyncApprovalInteraction):
        approved = await flow.complete()
    else:
        approved = flow.complete()
    await authenticate(client, server, "replacement-fixture")
    server.push(
        201,
        {
            "token": "pat-fixture",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        },
    )
    result = await resolve(approved.send())
    assert isinstance(result, AccessToken)
    assert result.value == "pat-fixture"
    sent = server.requests[-1]
    assert sent.headers["authorization"] == "Bearer access-fixture"
    assert sent.headers["x-hubuum-credential-approval"] == "hca1." + "c" * 64
    assert json.loads(sent.content)["name"] == "fixture-token"
    assert "hca1." not in repr(approved)
    before = len(server.requests)
    with pytest.raises(AuthenticationInteractionError):
        await resolve(approved.send())
    assert len(server.requests) == before


async def test_unsupported_freshness_is_explicit_and_not_downgraded(
    client_server: tuple[Client | AsyncClient, Server],
) -> None:
    client, server = client_server
    await authenticate(client, server)
    server.push(
        422,
        {
            "error": "AuthenticationFailed",
            "message": "Unsupported",
            "reason": "capability_unsupported",
        },
    )
    operation = CreateTokenOperation(
        principal_id=PrincipalId(42), token=NewTokenRequest(name="fixture-token")
    )
    with pytest.raises(APIError) as failed:
        await begin_approval(client, operation)
    assert failed.value.reason == "capability_unsupported"
    assert failed.value.status_code == 422
    assert len(server.requests) == 2


@pytest.mark.parametrize("kind", ["ldap", "oidc", "oauth"])
async def test_runtime_provider_credentials_are_write_only_inputs(
    client_server: tuple[Client | AsyncClient, Server],
    kind: str,
) -> None:
    client, server = client_server
    await authenticate(client, server)
    secret = "private-fixture-provider-credential"
    provider = AuthenticationProviderInput(
        name="employees",
        kind=kind,
        configuration=definition(kind),
        **(
            {"bind_password": SecretStr(secret)}
            if kind == "ldap"
            else {"credential": ProviderCredentialInput(action="replace", value=SecretStr(secret))}
        ),
    )
    request = SecurityCandidateRequest(
        group="authentication", expected_revision=7, providers=[provider]
    )
    assert secret not in repr(request)
    assert secret not in request.model_dump_json()
    server.push(201, candidate(server.id))
    report = await resolve(client.admin.create_security_candidate(request))
    with pytest.raises(ValueError, match="unverified"):
        report.activation_operation()
    sent = json.loads(server.requests[-1].content)
    configuration = sent["providers"][0]["configuration"]
    assert (
        configuration["bind_password"] if kind == "ldap" else configuration["credential"]["value"]
    ) == secret
    assert server.requests[-1].headers["authorization"] == "Bearer access-fixture"


@pytest.mark.parametrize(
    "case",
    [
        "verified",
        "wrong_report",
        "wrong_preview",
        "wrong_provider",
        "wrong_group",
        "provisioned",
        "issued_session",
    ],
)
async def test_non_login_verification_is_bound_to_candidate_and_provider(
    client_server: tuple[Client | AsyncClient, Server],
    case: str,
) -> None:
    client, server = client_server
    await authenticate(client, server)
    identifier = UUID(server.id)
    provider_id = uuid4()
    request = AuthenticationInteractionRequest(client_id="sdk-fixture", provider_id=provider_id)
    server.begin(browser="https://hubuum.example.invalid/verify")
    flow: ProviderVerificationInteraction | AsyncProviderVerificationInteraction
    if isinstance(client, AsyncClient):
        flow = await client.auth.begin_provider_verification(request, identifier)
    else:
        flow = client.auth.begin_provider_verification(request, identifier)
    report = candidate(server.id, verified=True)
    report["providers"] = [{"provider_id": str(provider_id), "name": "employees", "kind": "oidc"}]
    preview: dict[str, object] = {
        "candidate_id": server.id,
        "provider_id": str(provider_id),
        "subject": "private-fixture-subject",
        "admitted": False,
        "membership": "complete",
        "groups": [],
        "issued_session": False,
        "provisioned": False,
    }
    if case == "wrong_report":
        report["id"] = str(uuid4())
    elif case == "wrong_preview":
        preview["candidate_id"] = str(uuid4())
    elif case == "wrong_provider":
        preview["provider_id"] = str(uuid4())
    elif case == "wrong_group":
        report["group"] = "authorization"
    elif case in {"provisioned", "issued_session"}:
        preview[case] = True
    server.push(200, {"candidate": report, "verification": preview})
    if case == "verified":
        result = await resolve(flow.complete())
        assert result.candidate.id == identifier
        assert "private-fixture-subject" not in repr(result)
        assert "verification_receipt" not in result.candidate.activation_operation().payload()
    else:
        with pytest.raises(AuthenticationInteractionError):
            await resolve(flow.complete())


async def test_verified_candidate_activates_with_exact_fresh_password_approval(
    client_server: tuple[Client | AsyncClient, Server],
) -> None:
    client, server = client_server
    await authenticate(client, server)
    report = SecurityCandidateReport.model_validate(candidate(server.id, verified=True))
    server.push(200, approval("activate_security_candidate"))
    approved: ApprovedCredentialOperation | AsyncApprovedCredentialOperation
    if isinstance(client, AsyncClient):
        approved = await client.credential_approvals.approve(
            "fixture-password", report.activation_operation()
        )
    else:
        approved = client.credential_approvals.approve(
            "fixture-password", report.activation_operation()
        )
    description = json.loads(server.requests[-1].content)["operation"]
    assert "verification_receipt" not in description
    server.push(200, {"group": "authentication", "revision": 8, "changed": True})
    result = await resolve(approved.send())
    assert isinstance(result, SecurityCandidateActivated)
    assert result.changed
    body = json.loads(server.requests[-1].content)
    assert body == {"expected_revision": 7, "verification_receipt": "hcv1." + "b" * 64}


class Stream(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(
        self, body: bytes, *, fail: bool = False, clock: SimpleNamespace | None = None
    ) -> None:
        self.body = body
        self.fail = fail
        self.clock = clock
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        if self.clock is not None:
            self.clock.now = 31.0
        yield self.body
        if self.fail:
            raise httpx.ReadError("unknown-response-secret")

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self:
            yield chunk

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.close()


@pytest.mark.parametrize("mode", [Client, AsyncClient], ids=["sync", "async"])
@pytest.mark.parametrize(
    "case",
    [
        "success",
        "gzip",
        "unsupported",
        "outage",
        "bad_version",
        "malformed",
        "redirect",
        "oversize",
        "read_failure",
        "deadline",
    ],
)
async def test_authentication_transport_is_bounded_and_never_downgrades(
    mode: type[Client] | type[AsyncClient],
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(policy, "time", SimpleNamespace(monotonic=lambda: clock.now))
    monkeypatch.setattr(sync_client_module, "monotonic", lambda: clock.now)
    monkeypatch.setattr(async_client_module, "monotonic", lambda: clock.now)
    stream = Stream(b"{}", fail=case == "read_failure", clock=clock if case == "deadline" else None)
    if case == "oversize":
        stream.body = b"x" * (1024 * 1024 + 1)

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if case in {"oversize", "read_failure", "deadline"}:
            return httpx.Response(200, stream=stream)
        if case == "redirect":
            return httpx.Response(307, headers={"Location": "https://foreign.invalid/escape"})
        status = {"unsupported": 404, "outage": 503}.get(case, 200)
        body: object = {"interaction_version": 2 if case == "bad_version" else 1, "methods": []}
        if case == "malformed":
            body = []
        if case == "gzip":
            encoded = gzip.compress(json.dumps(body).encode())
            return httpx.Response(
                status,
                headers={"Content-Encoding": "gzip", "Content-Length": str(len(encoded))},
                stream=Stream(encoded),
            )
        return httpx.Response(status, json=body)

    instance = mode(
        "https://hubuum.example.invalid",
        token="bearer-fixture",
        options=ClientOptions(timeout=httpx.Timeout(None)),
        transport=httpx.MockTransport(handle),
    )
    try:
        if case in {"success", "gzip"}:
            assert (await resolve(instance.auth.methods())).methods == []
        else:
            with pytest.raises(
                (APIError, DecodeError, TransportError, AuthenticationInteractionError)
            ) as failed:
                await resolve(instance.auth.methods())
            assert "unknown-response-secret" not in str(failed.value)
        assert len(requests) == 1
        assert "authorization" not in requests[0].headers
        assert max(requests[0].extensions["timeout"].values()) == 30
        if case in {"oversize", "read_failure", "deadline"}:
            assert stream.closed
    finally:
        await resolve(instance.close())
