"""Independent public Python API consumer; private inputs, sanitized pipe events."""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import SecretStr

from hubuum_client import (
    AccessToken,
    APIError,
    AsyncClient,
    AuthenticationBrowserNext,
    AuthenticationInteractionRequest,
    AuthenticationProviderInput,
    Client,
    ClientOptions,
    CreateTokenOperation,
    Credentials,
    NewTokenRequest,
    ProviderCredentialInput,
    SecurityCandidateActivated,
    SecurityCandidateRequest,
)


def emit(event, *, acknowledge=False):
    print(json.dumps(event), flush=True)
    if acknowledge and sys.stdin.readline().strip() != "continue":
        raise RuntimeError("Missing fixture acknowledgement")


def passed(check):
    emit({"event": "passed", "check": check})


def browser(flow):
    step = flow.next
    if not isinstance(step, AuthenticationBrowserNext):
        raise RuntimeError("Expected browser step")
    emit(
        {
            "event": "browser",
            "id": str(flow.id),
            "next": {
                "kind": "browser",
                "verification_uri": step.verification_uri,
                "user_code": step.user_code,
            },
        },
        acknowledge=True,
    )


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


async def setup(local, config):
    password = config["local_password"]
    await resolve(local.login_session(Credentials("admin", password), client_id="python-qa"))
    passed("local administrator session is available before external setup")
    state = await resolve(local.admin.effective_authentication_settings())
    existing = next((p.provider_id for p in state.providers if p.name == "python-consumer"), None)
    provider = AuthenticationProviderInput(
        provider_id=existing,
        name="python-consumer",
        kind=config["kind"],
        configuration=config["definition"],
        credential=ProviderCredentialInput(
            action="replace", value=SecretStr(config["client_secret"])
        ),
    )
    report = await resolve(
        local.admin.create_security_candidate(
            SecurityCandidateRequest(
                group="authentication",
                expected_revision=state.expected_revision,
                providers=[provider],
            )
        )
    )
    provider_id = report.providers[0].provider_id
    emit({"event": "provider", "id": str(provider_id)}, acknowledge=True)
    request = AuthenticationInteractionRequest(client_id="python-qa", provider_id=provider_id)
    verification = await resolve(local.auth.begin_provider_verification(request, report.id))
    browser(verification)
    verified = await resolve(verification.complete())
    if verified.verification.issued_session or verified.verification.provisioned:
        raise RuntimeError("Preview had live effects")
    emit({"event": "preview_completed"}, acknowledge=True)
    approved = await resolve(
        local.credential_approvals.approve(password, verified.candidate.activation_operation())
    )
    activated = await resolve(approved.send())
    if not isinstance(activated, SecurityCandidateActivated) or not activated.changed:
        raise RuntimeError("Candidate did not activate")
    passed("runtime encrypted configuration, non-login preview and exact fresh-approved activation")
    return request


async def renew(client, principal):
    token = client.token
    if token is None or token.expires_at is None:
        raise RuntimeError("Missing ordinary session metadata")
    delay = max(0, (token.expires_at - datetime.now(UTC)).total_seconds()) + 0.1
    if delay > 35:
        raise RuntimeError("Fixture access lifetime must be 30 seconds")
    emit({"event": "renew_before"}, acknowledge=True)
    await asyncio.sleep(delay)
    renewed = await resolve(client.me())
    if renewed.principal.principal_id != principal or client.token == token:
        raise RuntimeError("Session renewal failed or changed identity")
    emit({"event": "renew_after"}, acknowledge=True)
    passed("browser login adopts an ordinary rotating session and retains principal")


async def fresh_approval(client, request, method, config, principal):
    constructor = type(client)
    emit({"event": "stage", "stage": "fresh approval begin"})
    operation = CreateTokenOperation(
        principal_id=principal, token=NewTokenRequest(name="python-consumer")
    )
    try:
        fresh = await resolve(client.auth.begin_approval(request, operation))
    except APIError as error:
        if (
            method.kind != "oauth"
            or error.status_code != 422
            or error.reason != "capability_unsupported"
        ):
            raise
        passed("OAuth fresh approval is explicitly unsupported")
    else:
        if method.kind == "oauth":
            raise RuntimeError("OAuth unexpectedly supports fresh approval")
        browser(fresh)
        approved = await resolve(fresh.complete())
        token = await resolve(approved.send())
        if not isinstance(token, AccessToken):
            raise RuntimeError("Fresh token issuance did not return a token")
        pat = constructor(
            config["origin"], token=token, options=ClientOptions(verify=config["ca_file"])
        )
        try:
            if (await resolve(pat.me())).principal.principal_id != principal:
                raise RuntimeError("PAT changed principal")
            await resolve(pat.logout())
        finally:
            await resolve(pat.close())
        passed("OIDC exact-operation fresh approval retains originating credential")


async def login_attempt(client, request, method, config, attempt):
    constructor = type(client)
    flow = await resolve(client.auth.begin_login(request))
    browser(flow)
    await asyncio.sleep(flow.poll_after)
    status = await resolve(flow.poll())
    if status.state != "ready":
        raise RuntimeError("Fixture interaction not ready")
    await resolve(flow.complete())
    identity = await resolve(client.me())
    principal = identity.principal.principal_id
    if attempt == 0:
        await renew(client, principal)
    await fresh_approval(client, request, method, config, principal)
    old_token = client.token
    await resolve(client.logout())
    stale = constructor(
        config["origin"], token=old_token, options=ClientOptions(verify=config["ca_file"])
    )
    try:
        try:
            await resolve(stale.me())
        except APIError as error:
            if error.status_code != 401:
                raise
        else:
            raise RuntimeError("Logout left the session authorized")
    finally:
        await resolve(stale.close())
    passed("local logout revokes external session")
    return principal


async def qualify(config, mode):
    constructor = AsyncClient if mode == "async" else Client
    local = constructor(config["origin"], options=ClientOptions(verify=config["ca_file"]))
    client = constructor(config["origin"], options=ClientOptions(verify=config["ca_file"]))
    try:
        request = await setup(local, config)
        methods = await resolve(client.auth.methods())
        method = next(m for m in methods.methods if m.provider_id == request.provider_id)
        stable_principal = None
        for attempt in range(2):
            principal = await login_attempt(client, request, method, config, attempt)
            if stable_principal is not None and stable_principal != principal:
                raise RuntimeError("Provider identity changed")
            stable_principal = principal
        passed("repeat browser login resolves the same immutable principal")
        recovery = await resolve(
            client.auth.begin_login(
                AuthenticationInteractionRequest(
                    client_id="python-qa",
                    provider_id="local",
                )
            )
        )
        await resolve(recovery.submit_credentials(Credentials("admin", config["local_password"])))
        await resolve(recovery.complete())
        if (await resolve(client.me())).principal.name != "admin":
            raise RuntimeError("Local recovery identity changed")
        await resolve(client.logout())
        passed("local recovery remains available after runtime activation")
        await resolve(local.logout())
        emit({"event": "complete"})
    finally:
        await resolve(client.close())
        await resolve(local.close())


def main():
    mode, path = sys.argv[1:]
    if mode not in {"sync", "async"}:
        raise RuntimeError("Unknown SDK mode")
    config = json.loads(Path(path).read_text())
    try:
        asyncio.run(qualify(config, mode))
    except APIError as error:
        emit({"event": "failure", "category": "api", "status": error.status_code})
        return 1
    except Exception:
        emit({"event": "failure", "category": "consumer"})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
