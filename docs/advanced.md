# Advanced usage

## Structured errors

All library exceptions derive from `HubuumError`. HTTP status codes are mapped
to useful subclasses:

| Status | Exception |
| --- | --- |
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 429 | `RateLimitError` |

Other failed HTTP responses raise `APIError`. Network and TLS failures raise
`TransportError`; successful responses that violate a typed model raise
`DecodeError`.

```python
from hubuum_client import NotFoundError

try:
    item = client.classes.get(42)
except NotFoundError as error:
    print(error.status_code, error.message, error.request_id)
```

Exceptions retain the method, query-free URL, status, API error code, message,
and request ID where available. Bearer tokens, secret-bearing request headers
and bodies, and values under sensitive query parameter names are redacted from
their diagnostics.

## Complete OpenAPI operation surface

The Hubuum v0.0.3 OpenAPI contract contains 196 operations. Every operation is
registered by its exact `operationId`, HTTP method, path template, request
media type, and authentication policy:

```python
from hubuum_client import OpenAPIOptions

result = client.openapi.call(
    "getApiV1Search",
    options=OpenAPIOptions(params={"q": "server", "limit_per_kind": 10}),
)
```

Path parameters are encoded as opaque segments, and missing or unexpected
parameters fail before a request:

```python
task = client.openapi.call(
    "postApiV1Imports",
    json=import_payload,
    options=OpenAPIOptions(headers={"Idempotency-Key": import_key}),
)

status = client.openapi.call(
    "getApiV1ImportsByTaskId",
    options=OpenAPIOptions(path_params={"task_id": task_id}),
)
```

`call()` returns a JSON value for JSON responses, `str` for a negotiated text
response, `bytes` for any other media type, and `None` for an empty success.
For example, rendered exports are not forced through a JSON decoder:

```python
csv_text = client.openapi.call(
    "getApiV1ExportsByTaskIdOutput",
    options=OpenAPIOptions(
        path_params={"task_id": task_id},
        accept="text/csv",
    ),
)
```

The unified search stream is consumed incrementally:

```python
with client.openapi.stream(
    "getApiV1SearchStream",
    options=OpenAPIOptions(params={"q": "server"}),
) as response:
    for line in response.iter_lines():
        process_sse_line(line)
```

Use `async with` and `async for` for the asynchronous client. The operation
manifest is compared with the immutable server OpenAPI document in CI,
including request and successful-response media types; all 196 operations must
match exactly.

## Natural-key objects and JSON Patch

All class/object `by-name` aliases have first-class service paths:

```python
from hubuum_client import ObjectDataPatchOperation, Query

hosts = client.classes.by_name("Hosts").objects
active = hosts.all(Query().data("status").equals("active"))
current = hosts.get("workstation.example")

updated = hosts.patch_data(
    current.name,
    [
        ObjectDataPatchOperation(
            op="add",
            path="/facts",
            value={"source": "ansible", "serial": "A"},
        )
    ],
)
```

`client.classes.by_id(id).objects` provides the corresponding numeric-ID
interface. `client.classes.by_name(name)` additionally exposes class
permissions, relations, graphs, aggregates, and its name-addressed object
service. JSON Patch paths are relative to the raw `data` root. Operations are
validated for their RFC 6902 member shape, explicit JSON null values are
preserved, and the server applies the complete patch atomically with rename
safety.

## Custom extension routes

`request()` remains the lower-level escape hatch for a server extension that is
not part of the pinned v0.0.3 OpenAPI document:

```python
from hubuum_client import RequestOptions

result = client.request(
    "GET",
    "/api/v1/custom-extension",
    options=RequestOptions(params={"scope": "example"}),
)
```

The path must begin with one slash and may not contain an origin, traversal
segment, query string, or fragment. Pass query values and additional headers
through `RequestOptions`, and request bodies through `json`. Use
`response_model=MyPydanticModel` to validate a custom JSON response.

## Task polling

Imports, exports, backups, restores, and computed-field rebuilds return tasks.
Once a task ID is known, wait for a terminal state with a bounded poller:

```python
task = client.tasks.wait(task_id, timeout_seconds=300, poll_interval=0.5)
if task.status.value != "succeeded":
    raise RuntimeError(task.summary or "Hubuum task failed")
```

The async equivalent uses the same `timeout_seconds` and `poll_interval`
keywords and awaits without blocking the event loop. Both pollers reject
invalid bounds and cap each sleep to the remaining timeout.
