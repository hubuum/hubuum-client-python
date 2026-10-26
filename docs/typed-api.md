# Complete typed API

Client 0.0.14 provides `client.api` and `async_client.api` for all **261
operations** in the pinned Hubuum v0.0.21 contract. Every operation has an explicit
Python signature, request type, and response type. All **401 named schemas** are
available in `hubuum_client.api.models`, including discriminated variants, enums,
scalar aliases, arbitrary JSON where the contract permits it, and nested results.
The [operation table](typed-operations.md) maps every route to its typed method.

Existing resource services such as `client.classes` remain available with their
established convenience models. The complete contract interface uses its own
models and returns `APIResponse[T]`, whose `.body` is the decoded result.

## Requests and responses

```python
from hubuum_client import Client, Credentials
from hubuum_client.api import models, query

with Client("https://hubuum.example.org") as client:
    client.login_session(Credentials("alice", "password"))
    response = client.api.classes.list(query=query.ClassesListQuery(limit=20, include_total=True))
    for hubuum_class in response.body:
        print(hubuum_class.id, hubuum_class.name)
    print(response.next_cursor, response.total_count)

    declaration = client.api.query_usage.create(
        response.body[0].id,
        body=models.QueryUsageCreateRequest(
            pattern=models.QueryUsagePatternSchema(
                path="hostname", value_type="string", operations=["equals"]
            )
        ),
    ).body
    print(declaration.id, declaration.revision)
```

`APIResponse` also exposes `status_code`, immutable `headers`, and `etag`. A
successful bodyless operation returns `APIResponse[None]`. Methods validate
responses before returning them and raise `DecodeError` for incompatible data.
Server timestamps become `datetime` values, preserving whether the wire value
includes a timezone offset. Text responses stay strings; methods with multiple documented media types accept
`accept` or `content_type` keyword arguments and validate the selected format.

Use `await async_client.api.classes.list(...)` for the same asynchronous API.
Authentication, session refresh, URL validation, transport configuration, and
error mapping are shared with the existing client. Use `login_session()` to
install a managed session: low-level `api.auth` operations return protocol models
and do not install or rotate client session state themselves.

## Wire names, omission, and clearing

Models preserve the OpenAPI wire fields. Python keywords use an alias:
`SearchHydrationRequest(class_=...)` sends `class`. Omitted properties stay
omitted. Explicit `None` is sent as JSON null, including relation-label clearing:

```python
result = client.api.relations.patch_classes_by_relation_id(
    relation_id,
    body=models.UpdateClassRelationLabels(forward_label=None),
)
assert result.body.forward_label is None
```

The existing `client.class_relations.update()` service also supports label
updates through `ClassRelationUpdate`, with optional `if_match` concurrency
control. Creation and import models expose both direction labels.

Models are immutable at the field level. Representations omit field values,
credential fields use secret values, and validation errors redact their inputs,
including failed field assignment and deletion.
`wire_payload()` deliberately reveals request secrets for transmission; do not
log its output. JSON dictionaries and lists inside models remain mutable.

## Query and header controls

Operation-specific controls live in `hubuum_client.api.query`, including
required timestamps, expected revisions, pagination, and conditional headers.
Pass `OpenAPIOptions(params=Query(...).as_params())` for dynamic filter names
that cannot be enumerated in OpenAPI. Typed query/header controls override the
same keys in options. Supply path arguments directly to the method.

For historical reads, use the timestamp of interest:

```python
from datetime import UTC, datetime

history = client.api.classes.get_object_history_computed_as_of(
    class_id,
    object_id,
    query=query.ClassesGetObjectHistoryComputedAsOfQuery(at=datetime.now(UTC).isoformat()),
).body
print(history.mode, history.shared.status)
```

## Typed search events

Streaming methods retain raw byte, text, and line iteration and add `events()`.
Each event has an `event` name and typed `data`. Both unified and structured
search validate their named event payloads; malformed events raise `DecodeError`
without including response content.

```python
with client.api.search.get_stream(query=query.SearchGetStreamQuery(q="server")) as stream:
    for event in stream.events():
        print(event.event, type(event.data).__name__)
```

For asynchronous use, enter with `async with` and iterate with
`async for event in stream.events()`.

## Maintaining parity

The implementation and route table are generated offline from the committed
`docs/openapi.json`. The development-only model generator is pinned; it is not a
runtime dependency. CI verifies regeneration and exercises every operation in
both runtimes against independently constructed contract fixtures. The live
suite also covers history, query usage, labels, credential activity, hydration,
and typed search events against the immutable server image.

```bash
uv run python scripts/generate-typed-api.py
uv run python scripts/generate-typed-api.py --check
```

::: hubuum_client.APIResponse

::: hubuum_client.ServerEvent
