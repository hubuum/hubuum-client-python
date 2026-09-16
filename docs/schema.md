# Schema evolution and task cancellation

Hubuum v0.0.15 gives every class an immutable schema revision. A schema revision
is independent of the class or object's resource revision. Select the typed
service with `client.classes.by_id(class_id).schema`; `AsyncClient` exposes the
same methods with `await`.

## Stage, inspect, and activate

Changing the schema policy of a nonempty class through ordinary class PATCH now
returns `409 Conflict`. Stage the proposed policy, request an impact analysis,
and explicitly activate it after inspecting the results:

```python
from hubuum_client import (
    SchemaActivationPolicy,
    SchemaActivationRequest,
    SchemaImpactReadiness,
    SchemaStageRequest,
)

schema = client.classes.by_id(class_id).schema
active = schema.get().active
staged = schema.stage(
    SchemaStageRequest(
        json_schema={
            "type": "object",
            "required": ["hostname"],
            "properties": {"hostname": {"type": "string"}},
        },
        validate_schema=True,
    )
)
analysis = schema.impact(staged.revision)
client.tasks.wait(analysis.task_id, timeout_seconds=60)
report = schema.work(analysis.task_id)
if report.readiness != SchemaImpactReadiness.COMPATIBLE:
    raise RuntimeError("Inspect the impact findings and repair objects before activation")
activated = schema.activate(
    staged.revision,
    SchemaActivationRequest(
        expected_active_revision=active.revision,
        policy=SchemaActivationPolicy.REJECT_INCOMPATIBLE,
        impact_task_id=analysis.task_id,
    ),
)
if activated.task_id is not None:
    client.tasks.wait(activated.task_id, timeout_seconds=60)
```

Strict activation rechecks the active revision and object population inside the
server transaction. Concurrent writes can invalidate a completed analysis and
cause `ConflictError`; obtain a fresh impact analysis before retrying.
`SchemaActivationPolicy.ALLOW_PENDING` requires an unscoped administrator and
can activate without compatibility proof. Existing enforced objects then become
pending until revalidated. `schema.revalidate(revision)` queues another scan;
`schema.abandon(revision)` abandons a staged revision.

Class read permission allows revision reads. Class update permission allows
staging, abandonment, and strict activation. Aggregate counts, impact and
revalidation requests, work reports, and schema cancellation additionally require
an unscoped administrator. See the
[server schema reference](https://github.com/hubuum/hubuum/blob/v0.0.15/docs/schema_evolution.md)
for the complete authorization and migration rules.

## Saved findings and HTML reports

`schema.work(task_id)` returns typed counters, readiness, and `impact` details.
`impact.failures[*].samples` contains all retained object IDs in each failure
group for new analyses. `impact.findings` contains inspected object revisions,
timestamps, and diagnostics. Legacy findings may have no snapshot. Diagnostics
contain JSON Pointer locations, expected constraints, redacted actual type/size
context, and omission/truncation indicators. `expected.status` distinguishes an
available JSON `null` constraint from an omitted constraint.

These findings describe saved snapshots. Repairing an object does not update
old diagnostics or HTML. Re-run impact after repairs to obtain current evidence.

```python
from pathlib import Path
from hubuum_client import SchemaRepairReportRequest

html = schema.generate_report(
    analysis.task_id,
    SchemaRepairReportRequest(
        object_url_template="https://inventory.example/objects/{object_id}",
    ),
)
Path("schema-repair.html").write_text(html, encoding="utf-8")
retained_html = schema.report(analysis.task_id, download=True)
```

The object URL template must be an absolute HTTP(S) frontend URL with exactly
one `{object_id}` placeholder and no credentials. Optional `template_id` selects
a stored HTML layout. The report methods return HTML text. `download=True`
requests attachment disposition; the caller chooses where to save the text.

Reports can exceed server assembly/output budgets and return `APIError` with
`status_code == 413`. Failed generation preserves the previous HTML and saved
findings. `schema.cancel(task_id)` cancels schema work while retaining committed
findings; its report response can also exceed the assembly budget even when
cancellation succeeded.

## Compliance pages

Schema lists use numeric `after` continuations, distinct from ordinary opaque
cursor queries. `SchemaPageOptions` is immutable and limits pages to 1–100
candidates. `schema.revisions(options)` returns one page; resume after its last
revision. Compliance pages expose `items` and `next_after`, with no totals:

```python
from hubuum_client import ComplianceStatus, SchemaPageOptions

options = SchemaPageOptions(limit=50)
while True:
    page = schema.objects(options, status=ComplianceStatus.PENDING)
    for item in page.items:
        print(item.object_id, item.status)
    if page.next_after is None:
        break
    options = SchemaPageOptions(after=page.next_after, limit=50)
```

An empty page can still have `next_after`: the continuation advances past
inspected candidates that the caller cannot see. Evidence uses the wire field
`schema`, exposed in Python as `evidence.schema_`.

## Import activation

`ImportClassInput.schema_activation` accepts `ImportSchemaActivation` with
`revision`, `expected_active_revision`, `policy`, and optional `impact_task_id`.
The class input must contain the exact policy of an already staged revision.
Import activation requires administrator authority and commits with that import
item. Portable import envelopes remain version 2; full backups now use format 6.
See [server compatibility](compatibility.md) before upgrading or restoring older
artifacts.

## Cancel a task

```python
from hubuum_client import TaskCancelRequest, TaskStatus

task = client.tasks.cancel(
    task_id,
    TaskCancelRequest(expected_status=TaskStatus.QUEUED, reason="Superseded import"),
)
if not task.status.terminal:
    task = client.tasks.wait(task_id, timeout_seconds=60)
```

Omit the payload to send an unconditional cancellation request. `expected_status`
protects a queued-only withdrawal; a changed status returns `ConflictError`.
Cancellation may return a running task while cleanup continues. It does not undo
committed work. Inspect `unattempted_items`, `terminal_reason`, and
`remote_side_effect_state`; `possibly_sent` means the remote system may already
have been affected. Reasons are limited to 512 characters and omitted from model
representations.

Task owners and unscoped administrators can cancel authorized tasks. Scoped
tokens are restricted to tasks submitted with the same token, and internal
reindex/schema work requires an unscoped administrator. Repeated requests for a
terminal task return its existing terminal state.
