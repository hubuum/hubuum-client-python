# Credential approvals

Hubuum v0.0.16 requires fresh password approval for credential management.
A bearer token alone cannot create or renew a token, create a local user,
change a password, import human passwords or password hashes (even in a dry
run), or confirm a restore. Profile-only user updates, credential-free
imports, token reads, and revocation keep their existing flow.

Use `client.credential_approvals.create()` with the acting human's current
password and a typed operation. Pass the returned response as `approval=` to
the corresponding typed mutation. Both clients expose the same interface;
await service calls when using `AsyncClient`.

## Create or renew a token

```python
from getpass import getpass

from hubuum_client import (
    CreateTokenOperation,
    CredentialApprovalRequest,
    NewTokenRequest,
    RenewTokenOperation,
    RenewTokenRequest,
)

principal_id = client.me().principal.principal_id
request = NewTokenRequest(name="inventory-reader")
approval = client.credential_approvals.create(
    CredentialApprovalRequest(
        password=getpass("Current password: "),
        operation=CreateTokenOperation(principal_id=principal_id, token=request),
    )
)
token = client.tokens.for_principal(principal_id).create(request, approval=approval)

renewal = RenewTokenRequest()
approval = client.credential_approvals.create(
    CredentialApprovalRequest(
        password=getpass("Current password: "),
        operation=RenewTokenOperation(principal_id=principal_id, token_id=token_id, token=renewal),
    )
)
replacement = client.tokens.for_principal(principal_id).renew(token_id, renewal, approval=approval)
```

Typed token methods copy the returned `token_expires_at` into the final request,
even when you originally supplied an expiry. This preserves the server's UTC
microsecond normalization without mutating your request. When using
`openapi.call()` instead, send `json=approval.token_request(request)` with
`OpenAPIOptions(headers=approval.headers(), path_params=...)`.

Approvals are bound to the exact operation, body, and originating bearer token.
They last at most 120 seconds and are single use. Changing a target, scope,
name, description, or other approved field requires fresh approval. Use the
same client session for both calls. Service accounts cannot password-login;
the acting human must have authority to manage the account. Approval never
adds permissions the human lacks. Unattended bearer-only token rotation is
not supported by this server release.

## Users, imports, and restores

| Operation model | Protected mutation |
| --- | --- |
| `CreateUserOperation(user=request)` | `client.users.create(request, approval=approval)` |
| `UpdateUserOperation(user_id=id, user=request)` | `client.users.update(id, request, approval=approval)` |
| `ImportCredentialsOperation(import_=request)` | `client.imports.submit(request, approval=approval, idempotency_key=key)` or `run(...)` |
| `ConfirmRestoreOperation(restore_id=id, confirmation=request)` | `postApiV1RestoresByRestoreIdConfirm` with `approval.headers()` |

Each operation is wrapped in `CredentialApprovalRequest(password=..., operation=...)`.
For user changes the top-level password authenticates the acting human; the
nested user password is the new account password. A password update can pass
`options=RequestOptions(headers={"If-Match": revision_etag})` to retain its
normal concurrency precondition.

Credential-bearing imports require an unscoped human administrator. Preserve
the complete approved import, including array order, and use a client-generated
idempotency key. A retry of an accepted request with the same key and body
returns the existing task; its approval header is still required. Use task
status to resolve an ambiguous admission response. A changed payload requires
a new approval and key. Imported password changes revoke the affected user's
tokens and invalidate their outstanding approvals.

For a validated restore stage:

```python
from hubuum_client import ConfirmRestoreOperation, OpenAPIOptions, RestoreConfirmRequest

confirmation = RestoreConfirmRequest(
    restore_capability=stage["restore_capability"],
    sha256=stage["sha256"],
    confirmation="REPLACE ALL HUBUUM DATA",
)
approval = client.credential_approvals.create(
    CredentialApprovalRequest(
        password=getpass("Current password: "),
        operation=ConfirmRestoreOperation(restore_id=stage["id"], confirmation=confirmation),
    )
)
client.openapi.call(
    "postApiV1RestoresByRestoreIdConfirm",
    json=confirmation,
    options=OpenAPIOptions(path_params={"restore_id": stage["id"]}, headers=approval.headers()),
)
```

The restore capability remains required. Approval is consumed when confirmation
is admitted; executor failure does not make it reusable. Continue the existing
[capability-authenticated status polling](advanced.md#queued-full-restores).

## Errors and evidence

`ReauthenticationRequiredError` is a subclass of `PermissionDeniedError` and
means HTTP 403 with the server reason `reauthentication_required`. Classification
uses the original reason before redaction. Other permission failures remain
`PermissionDeniedError`; `APIError.reason` exposes a redacted server reason, which
may be altered when a submitted secret overlaps the code. Use the exception type
for recovery. The client does not retry or prompt for a password automatically.
An approval-creation 401 means authentication failed; a 429 follows the normal
rate-limit handling. Do not parse human-readable error messages.

If the final mutation response is lost, inspect
`client.credential_approvals.get(approval.record.id).consumed_at`. Consumption
cannot recover a newly issued token secret. Inspect token metadata and revoke
unwanted credentials before requesting a replacement. Approval records also
include invalidation, actor, originating token, and optional restore-stage IDs.

Keep passwords and approvals transient. `CredentialApprovalSecret` redacts
string, representation, and JSON output. `approval.headers()` deliberately
reveals the secret for HTTP use; do not log or persist that dictionary. Approval
headers, password fields, and echoed secrets are redacted from client errors;
transport and model-decoding errors do not chain exceptions containing raw
requests or responses. A completed restore invalidates unused approvals while
preserving local evidence; backups do not transfer approval authority.

Invalid `CredentialApprovalRequest` inputs produce sanitized Pydantic validation
errors. Their `errors()` and `json()` diagnostics retain error codes and known
top-level fields, with generic messages and redacted inputs; nested context and
the original validation exception are discarded. Successful validation preserves
the exact wire payload, including passwords needed for the approved operation.

See the [server client and rollout guide](https://github.com/hubuum/hubuum/blob/v0.0.16/docs/credential_approvals.md)
for the complete authorization, audit, retry, and deployment contract.
