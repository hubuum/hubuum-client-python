# Service accounts

`client.service_accounts` manages automation identities with the same methods on
`AsyncClient` (await requests and use `async for` with `pages()`). Service accounts
authenticate using tokens; they cannot sign in with a password.

## Create and discover

```python
from hubuum_client import GroupId, Query, ServiceAccountCreate

account = client.service_accounts.create(
    ServiceAccountCreate(
        name="inventory-importer",
        owner_group_id=GroupId(owner_group_id),
        identity_scope="local",
        description="Imports the inventory",
    )
)
account = client.service_accounts.get(account.id)
listed = client.service_accounts.get_by_name("inventory-importer", identity_scope="local")
accounts = client.service_accounts.all(Query().limit(50), max_pages=100, max_items=10_000)
```

An administrator can create accounts for any owner group. Other human callers
must belong to the owner group. Lists include only accounts the caller can
manage; point requests hide inaccessible accounts as not found. Management also
requires an appropriate management-capable credential. Owning an account does
not make it a member of its owner group: use `client.groups.add_member()` when
the account should inherit that group's resource permissions.

Names are scoped to an identity scope. Creation through v0.0.20 accepts only
`local`, which is also the default when `identity_scope` is omitted. Accounts in
other scopes are managed by their identity provider. Supply `identity_scope`
to `get_by_name()` when names are ambiguous; the helper raises
`ResultCardinalityError` unless exactly one account matches.

`list()` returns one page. `page()` exposes cursor and count metadata, while
`pages()` and `all()` enforce cursor-cycle and page/item bounds. List records are
`ServiceAccount` values with `identity_scope`; create, get, update, and disable
return `ServiceAccountPoint` with `identity_scope_id`. Both preserve unknown
response fields and expose `principal_id`, which equals `id`.

## Mint a token

Use the existing [credential approval workflow](credentials.md) as a human
authorized to manage the account:

```python
from hubuum_client import CreateTokenOperation, CredentialApprovalRequest, NewTokenRequest

request = NewTokenRequest(name="inventory-job")
approval = client.credential_approvals.create(
    CredentialApprovalRequest(
        password=password,
        operation=CreateTokenOperation(principal_id=account.principal_id, token=request),
    )
)
token = client.tokens.for_principal(account.principal_id).create(request, approval=approval)
```

Configure `NewTokenRequest.scope` for the permissions and resources needed by
the job. The approval and mint must use the same human client session. Account
creation itself does not require a password approval. The returned `AccessToken`
has a redacted representation; pass it to `Client(base_url, token=token)` or
`AsyncClient(base_url, token=token)` and keep its value out of logs.

## Update, disable, and delete

```python
from hubuum_client import ServiceAccountUpdate

tagged = client.api.service_accounts.get(account.id)
account = client.service_accounts.update(
    account.id,
    ServiceAccountUpdate(description="Updated importer"),
    if_match=tagged.etag,
)
disabled = client.service_accounts.disable(account.id)
client.service_accounts.delete(account.id)
```

Only description and owner group are mutable. Reassignment requires authority
over the new group as well as the current account. An omitted or `None` update
field is unchanged; use `description=""` to clear it. Request models reject
unknown fields.

Disable revokes the account's tokens and returns its `disabled_at` timestamp.
The v0.0.20 API has no enable operation. Delete removes the account. Update,
disable, and delete accept optional `if_match` ETags; stale tags raise
`PreconditionFailedError`. Obtain a fresh tag from `client.api.service_accounts.get()`
before each conditional mutation.
