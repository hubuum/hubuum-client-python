# External authentication (project candidate)

These additions belong to `project/auth-support` and require the accepted auth
project server candidate. The released v0.0.22 API and compatibility image remain
pinned. The server performs OIDC/OAuth exchange and maps upstream identity; the
Python client never accepts upstream tokens or identity claims as login input.

## Discover and continue explicitly

```python
import time

from hubuum_client import (
    AuthenticationBrowserNext,
    AuthenticationInteractionRequest,
    Client,
)

with Client("https://hubuum.example") as client:
    methods = client.auth.methods()
    provider = next(method for method in methods.methods if method.kind == "oidc")
    flow = client.auth.begin_login(
        AuthenticationInteractionRequest(
            client_id="my-application",
            provider_id=provider.provider_id,
        )
    )
    if isinstance(flow.next, AuthenticationBrowserNext):
        # Display these public instructions or invoke an explicit application hook.
        print(flow.next.verification_uri, flow.next.user_code)
    while True:
        time.sleep(flow.poll_after)
        status = flow.poll()
        if status.state == "ready":
            flow.complete()
            break
        if status.terminal:
            raise RuntimeError("Authentication stopped; begin a new interaction")
    identity = client.me()
    client.logout()
```

`AsyncClient` has the same service methods and typed handles. Await each operation
and use `await asyncio.sleep(flow.poll_after)` between polls. Browser launching
always belongs to the application. Discovery failure, unknown protocol versions
and unsupported capabilities never trigger automatic password fallback.

A credentials step accepts `flow.submit_credentials(Credentials(name, password))`;
a browser step rejects it. `flow.cancel()` ends an interaction. Polling is caller
driven, honors integer/HTTP-date Retry-After, applies backoff/jitter, and stops at
expiry or a terminal state. Early polls fail locally. No background polling or
unbounded retry is started. Authentication responses are bounded to 1 MiB and
HTTP timeouts are capped at 30 seconds, honoring shorter client settings.

Interaction handles retain their origin-bound capability privately, redact
representations and never attach the client's bearer to poll/complete requests.
Completion is attempted once, installs the normal in-memory rotating session,
and uses the existing serialized refresh policy. An uncertain completion attempts
cancel-first exact-family cleanup. Applications may retain
`cleanup = flow.issued_session_cleanup()` before completion and explicitly retry
`cleanup.revoke()` if connectivity prevented cleanup. An uncertain rotation is
never retried. Reusing a completed handle fails locally without revoking the
accepted session. Clients do not persist passwords or upstream credentials.

## Fresh approval

```python
from hubuum_client import CreateTokenOperation, NewTokenRequest

operation = CreateTokenOperation(
    principal_id=identity.principal.principal_id,
    token=NewTokenRequest(name="automation"),
)
fresh = client.auth.begin_approval(request, operation)
# Display fresh.next, finish the explicit server-owned browser approval.
approved = fresh.complete()
issued_token = approved.send()
```

This fragment assumes an authenticated client, a provider-bound `request`, and
an identity read from that client. Approved handles deep-copy the exact operation,
retain the original authenticated credential, and allow one protected attempt.
Changing the caller's operation or credentials cannot rebind an approval. Password
approval uses `client.credential_approvals.approve(password, operation)`.
Activation receipts go only to the protected activation request, never into its
approval description. OAuth's `422 capability_unsupported` is a typed `APIError`
with that stable reason; applications must handle it explicitly. OIDC fresh
approval remains provider-policy dependent. No password/PAT fallback occurs.

## Configure every external provider at runtime

A locally authenticated administrator uses:

1. `client.admin.runtime_settings_schema()` to discover security capabilities,
   deployment locks, trust profiles and supported provider kinds.
2. `client.admin.effective_authentication_settings()` to obtain the responding
   replica's status, credential-configured flags and `expected_revision`.
3. `client.admin.create_security_candidate(SecurityCandidateRequest(...))` with
   the complete desired provider set and the observed revision.
4. `client.auth.begin_provider_verification(request, candidate.id)` for an actual
   OIDC/OAuth test sign-in, or `client.admin.verify_ldap_candidate(...)` for LDAP.
5. `verified.candidate.activation_operation()`, then exact local fresh approval
   and `approved.send()` to activate the verified candidate.

`AuthenticationProviderInput` supports LDAP, OIDC and OAuth, immutable provider
IDs, runtime definitions, enabled state and explicit deployment adoption where
supported. Keep the immutable ID when editing; names are display metadata.
Browser definitions accept `ProviderCredentialInput` actions `keep`, `clear`,
`reference` or `replace` with a `SecretStr` value. LDAP distinguishes omitted
`bind_password` (keep encrypted value) from explicit `None` (clear), and supports
an existing deployment reference. Credentials are write-only; effective state
never returns their values. Explicit wire serialization is the only method that
reveals secret inputs for transmission. Invalid secret-bearing model inputs
produce redacted validation details, including `errors()`.

Local accounts remain available through IAM and cannot be disabled by a provider
candidate. The server still owns encryption root keys, verified TLS, private-target
policy, public browser origin, registered return targets, deployment locks,
revision/receipt freshness and replica reconciliation. A stale/conflicting
candidate fails without changing live login. Refetch effective state and prepare
a new candidate; never blindly retry activation. Read replica/application status
before reporting a committed change as applied everywhere. Authorization candidate
models also represent runtime or deployment ownership and bounded HTTPS remote
policy connections. A candidate is not permission to bypass deployment locks.

## Reproduce project qualification

The independent consumer and controller under `tests/integration/` use only the
public Python SDK for Hubuum operations and accepted hash-pinned server fixtures
for provider/browser duties. They require Docker, the accepted server source
checkout and one immutable qualified image recorded in
[authentication-project-source.json](authentication-project-source.json).

```bash
uv run python tests/integration/authentication.py \
  --server-source /path/to/accepted/server \
  --image sha256:QUALIFIED_IMAGE_ID \
  --consumer tests/integration/authentication_consumer.py \
  --profile id_token \
  --evidence /path/to/disposable/evidence
```

Repeat with `userinfo` and `oauth`. Both sync and async modes run for each
profile. Private configuration and CA keys stay inside the disposable fixture
root and are removed afterward; reports retain only source/image pins and check
names. Browser events contain public verification instructions only. Previews
must leave six identity/session tables unchanged; renewal must retain the exact
session family and principal while rotating access credentials. The driver also
checks fresh approval or explicit OAuth rejection, logout, repeat identity and
local recovery. These project tests supplement the full canonical
`./scripts/run-e2e-tests.sh` v0.0.22 core/recovery suite.
