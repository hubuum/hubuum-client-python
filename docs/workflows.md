# Resource workflows

The convenience services below are available on both `Client` and `AsyncClient`.
Await asynchronous network calls; service selection itself does not perform IO.
They use the committed Hubuum v0.0.21 contract. Response types are the exact
models in `hubuum_client.api.models`, except task and export results, which use
`Task` and `ExportOutput` from the existing convenience API.

Request models are exported from `hubuum_client`. They reject unknown top-level
fields and hide inputs in validation errors. Explicit nulls in these requests
are preserved. `wire_payload()` exposes values for transmission; do not log it.

## Discovery and concurrency

Cursor-backed services expose `list()` (one page), `page()` (items and metadata),
`pages()`, and `all()`. Traversal detects repeated cursors and defaults to at most
100 pages and 10,000 collected items. Supply `max_pages` and `max_items` when a
larger result is intentional. Filters use the existing immutable `Query`.

Conditional mutations accept `if_match`. Obtain the opaque ETag from the
corresponding `client.api` point response; do not manufacture it from a numeric
revision. A stale validator raises `PreconditionFailedError`.

## Permissions and delegation

```python
from hubuum_client import Permission, Query

permissions = client.collections.permissions(collection_id)
assignments = permissions.assignments()  # CollectionPermissionSet, including revision
for assignment in permissions.all(Query().limit(20)):
    print(assignment.group_id, assignment.has_read_object)

permissions.grant(group_id, [Permission.READ_COLLECTION, Permission.READ_OBJECT])
permissions.grant_permission(group_id, Permission.READ_AUDIT)
assert permissions.check(group_id, Permission.READ_AUDIT)
effective = permissions.effective_principal(principal_id)
for grant in effective:
    print(grant.inherited, grant.depth, grant.source_collection.id)
```

`group()` reads one group's direct assignment set. `principal()` returns a
cursor-backed service of group assignments for one principal. `effective_group()`
and `effective_principal()` retain inheritance depth, source/target collections,
and group identity. `with_permission(Permission.READ_OBJECT)` returns a paginated
group service. `check()` returns false for an absent grant; authorization errors
still propagate. `grant()` adds permissions, `replace()` replaces the group set,
`revoke()` removes it, and `revoke_permission()` removes a single permission.

Class permissions are inherited from collections and have no class-specific
write route: use `client.classes.by_id(class_id).permissions` for guarded reads.
Use `client.principals.permissions()` for the current principal or pass an ID to
inspect another principal. These responses retain the contributing group grants.
All writes remain subject to the server's management and delegation rules;
ordinary read access does not authorize granting oneself more permissions.

**Migration:** `client.classes.by_name(name).permissions()` now returns
`list[GroupPermission]`. Replace dictionary indexing with attributes, for example
`entry.permission.has_read_class` and `entry.group.id`. Use
`entry.model_dump(mode="json")` when a dictionary is required. Invalid permission
records raise `DecodeError`, just like other typed responses.

## Audit and historical reads

```python
from datetime import UTC, datetime
from hubuum_client import EventQuery, Query

feed = client.audit.collection(collection_id)
events = feed.events.all(EventQuery(action="updated").limit(20))
versions = feed.history.all(Query().limit(20))
then = feed.history.as_of(datetime(2026, 10, 29, tzinfo=UTC))
```

`client.audit.events` is the global feed. Resource selectors are `collection(id)`,
`class_(id)`, `object(class_id, object_id)`, `export_template(id)`, and
`remote_target(id)`, each exposing `.events` and `.history`. `user(id)` and
`group(id)` return event services only: the contract has no temporal routes for
those identities. Templates and remote targets also expose `.audit(id)`.

`EventQuery` supplies plain action, actor, initiator, entity, collection, relation,
and time filters. `occurred_after`, `occurred_before`, and `history.as_of(at)`
require timezone-aware datetimes, avoiding implicit local-time conversion.
Events retain provenance and before/after snapshots; history retains the exact
resource-specific version model and validity interval.

Audit reads require separate `ReadAudit` authorization. Related-collection
visibility may omit snapshots. Historical reads use current authorization and
the server's historical visibility rules; a timestamp is not permission to read
otherwise inaccessible data. Retention gaps are not filled from current state.
Advanced timeline, relationship, and historical-computation operations remain
available through `client.api`.

## Computed fields

```python
from hubuum_client import ComputedFieldCreate, ComputedFieldPreviewRequest

fields = client.classes.by_id(class_id).computed_fields
definition = ComputedFieldCreate(
    key="total",
    label="Total",
    result_type="number",
    operation={"type": "sum", "paths": ["/compute_cost", "/storage_cost"]},
)
preview = fields.preview(
    ComputedFieldPreviewRequest(
        definition=definition,
        data={"compute_cost": 45, "storage_cost": 5},
    )
)
created = fields.create(definition)  # definition plus class computation state
state = fields.rebuild()
if state.active_task_id is not None:
    task = client.tasks.wait(state.active_task_id)
```

Shared fields support `list`, `get`, `create`, `update`, `delete`, `preview`, and
`rebuild`. List, mutation, deletion, preview, and rebuild return distinct contract
models. Shared mutation requires collection update authority. Value-affecting
changes can queue a rebuild; rebuild returns computation state rather than a task
object. Follow `active_task_id` when present.

Personal definitions use `client.computed_fields`, `PersonalComputedFieldCreate`
(which includes `class_id`), and `ComputedFieldUpdate`. Select one class with
`.for_class(class_id)`. Personal list results support guarded pagination;
mutations return the definition directly and deletion returns `None`. Personal
preview also requires `class_id`. Personal fields belong to a human principal,
require class read access, and are evaluated on read; they have no rebuild route.

Preview selects either sample `data` or an existing `object_id`. Expressions use
the server's bounded operation catalog and JSON Pointer paths into raw object
data. They cannot depend on other computed fields, relations, external services,
or time. Computed values do not modify canonical object data. The server
validates operation semantics; Python preserves the operation JSON without
inventing another expression language.

## Export templates

`client.export_templates` provides CRUD, guarded pagination, `.audit(id)`,
`submit(id, ExportTemplateRunRequest(...))`, and `run(id, ...)`.
Create/update requests are `ExportTemplateCreate` and `ExportTemplateUpdate`.

```python
from hubuum_client import ExportTemplateCreate, ExportTemplateRunRequest

template = client.export_templates.create(
    ExportTemplateCreate(
        name="inventory",
        description="Inventory report",
        collection_id=collection_id,
        class_id=class_id,
        scope_kind="objects_in_class",
        kind="export",
        content_type="text/plain",
        template="Inventory report",
    )
)
result = client.export_templates.run(template.id, ExportTemplateRunRequest())
```

Templates render on the server with its template context and execution limits.
The `strict`, `null`, and `omit` missing-data policies control missing values;
choose the policy when creating a template or running it. `submit()` returns a
`Task`, whose status can be resumed with `client.tasks.wait()`. Retrieve output
with `client.exports.output(task.id)` or stream it with `.output_stream(task.id)`.
JSON output remains typed; rendered text retains its content type and body.
For explicit media negotiation use `client.api.exports.get_output(..., accept=...)`.
`run()` waits for `succeeded` before fetching output and raises
`TaskUnsuccessfulError` for other terminal states. The same success requirement
applies to the new backup and remote-target `run()` helpers.

## Remote targets

`client.remote_targets` provides CRUD, guarded pagination, `.audit(id)`,
`invoke(id, RemoteTargetInvokeRequest(...))`, and `run(id, ...)`.
`RemoteTargetCreate` and `RemoteTargetUpdate` preserve the exact authentication,
subject, header, URL, and body-template fields. Omitting `body_template` leaves it
unchanged; explicitly setting it to `None` clears it.

An invocation returns a queued `Task`; acceptance does not establish successful
delivery. `run()` returns the completed task, including typed remote-call details.
Task events remain available through `client.tasks.all_events(task.id)`. The
pinned contract has no public remote-call response-output endpoint: this client
does not invent one or expose an untyped internal result row.

The server requires HTTPS, screens destination addresses, rejects embedded URL
credentials, and does not follow redirects. Credential-bearing targets require
administrator approval of a fixed destination binding. Permission and target
revision are rechecked before dispatch. Response previews have a server-configured
size cap, and task cancellation cannot undo an outbound action already sent.
Keep reusable secrets in server secret references. Configuration and response
models redact representations and validation diagnostics, but their explicit
field access and wire serialization still expose values to the caller.

## Event delivery controls

```python
from hubuum_client import Query

health = client.event_deliveries.health()
delivery = client.event_deliveries.get(delivery_id)
client.event_deliveries.mark_dead(delivery.id)
client.event_deliveries.retry(delivery.id)  # Explicitly requeue this delivery
```

Delivery list/page traversal uses the usual bounds. `retry()` and `mark_dead()`
return `EventDeliveryUpdateResponse`, whose `.delivery` contains the updated
record. Health preserves system subscription entries with `collection_id=None`.
Administrative authority is required for delivery control.

Delivery is at least once: deduplicate with `event_id`. Failed deliveries back
off according to server policy and can reach the dead-letter state. Retrying
reuses the original event snapshot. It can cause another external delivery;
marking a record dead cannot retract a notification already sent.

Existing convenience APIs remain `client.event_sinks` for administrator sink
management/grants and `client.collections.event_sinks(id)` /
`.event_subscriptions(id)` for collection integrations. Sink kinds are webhook,
email, AMQP, and Valkey streams. System subscriptions and preview/test admission
remain in `client.api`. Subscription scope and sink grants determine which events
may reach a destination; resource read access alone does not authorize delivery.

## Principal settings and administration

```python
from hubuum_client import SettingsRequest, SettingsPatchOperation

settings = client.principals.settings()  # Or settings(principal_id)
point = client.api.principals.get_me_settings()
settings.merge_patch(SettingsRequest(settings={"theme": None}), if_match=point.etag)
settings.json_patch([SettingsPatchOperation(op="add", path="/theme", value="dark")])
```

`get`, `replace`, `delete`, `merge_patch`, and `json_patch` preserve revision
responses and conditional writes. Settings keys are application-defined JSON;
requests enforce a JSON object or a strict RFC 6902 operation list. Merge Patch
null deletes a key; a JSON Patch `value=None` explicitly stores JSON null.
Each helper sends its corresponding media type. `client.principals.groups(id)`
supports cursor pagination; omit the ID for current-principal groups.

`client.auth.providers()` is public and omits bearer credentials. `validate()`
is authenticated. `revoke_token`, `revoke_user`, and `revoke_all` perform explicit
server revocation subject to its authorization rules. Revocation can invalidate
other clients. These calls do not install or rotate this client's managed
credentials: continue using `login_session()` and `logout()` for local session
lifecycle, as with low-level `client.api.auth` calls.

`client.admin` exposes `config`, `counts`, `database`, `tasks`, and `rate_limits`.
Running configuration is authenticated administrator data, unlike the public
`client.config()`. `release_rate_limit(entry_id)` releases one entry;
`clear_rate_limits()` clears the global table. These actions remove login
throttling state and require administrative authorization. Prefer a targeted
release when investigating one caller.

## Full backup and restore

```python
from hubuum_client import BackupRequest

backup = client.backups.run(BackupRequest(include_history=True))
staged = client.restores.stage(backup)
```

`backups.submit()` returns a `Task`; `.get(task_id)` and `.output(task_id)` allow
resuming work. Output is the strict `BackupDocument`, not a portable import.
Restore job IDs (`RestoreJobId`) are distinct from task IDs (`TaskId`).

Staging validates the document. Confirmation replaces **all Hubuum data** and
requires a fresh operation-bound credential approval:

```python
from hubuum_client import (
    ConfirmRestoreOperation,
    CredentialApprovalRequest,
    RestoreConfirmRequest,
    RestoreJobId,
)

confirmation = RestoreConfirmRequest(
    restore_capability=staged.restore_capability,
    sha256=staged.sha256,
    confirmation="REPLACE ALL HUBUUM DATA",
)
approval = client.credential_approvals.create(
    CredentialApprovalRequest(
        password=password,
        operation=ConfirmRestoreOperation(
            restore_id=RestoreJobId(staged.id),
            confirmation=confirmation,
        ),
    )
)
client.restores.confirm(staged.id, confirmation, credential_approval=approval.approval)
result = client.restores.wait(staged.id, capability=staged.restore_capability)
assert result.status == "succeeded"
```

Keep the staged capability and digest private. `status()` and `wait()` authorize
with the capability and omit bearer credentials, even when an invalidated managed
session is still installed. `wait()` returns `succeeded`, `failed`, or `expired`;
callers must inspect the status. Its timeout bounds polling and does not cancel
the restore. The stage has its own expiry, and execution requires a matching
v0.0.21 restore executor. Reauthenticate after recovery.

Full restore tests run only on the wrapper-owned disposable stack. Caller-managed
servers never run destructive recovery tests. See [end-to-end tests](e2e.md).
