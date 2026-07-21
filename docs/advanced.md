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
and request ID where available. They never retain the bearer token or outgoing
request body.

## Safe access to unmodeled routes

The Hubuum v0.0.3 OpenAPI contract contains 196 operations. Dedicated services
cover the normal resource lifecycle; `request()` covers the remainder without
giving up the configured origin:

```python
result = client.request(
    "GET",
    "/api/v1/search",
    params={"q": "server", "limit_per_kind": 10},
)
```

The path must begin with one slash and may not contain an origin, traversal
segment, query string, or fragment. Pass query values through `params`, request
bodies through `json`, and additional headers through `headers`.

Use `response_model=MyPydanticModel` to decode an extension route into an
application model:

```python
result = client.request(
    "GET",
    "/api/v1/admin/config",
    response_model=AdminConfig,
)
```

## Task polling

Imports, exports, backups, restores, and computed-field rebuilds return tasks.
Once a task ID is known, wait for a terminal state with a bounded poller:

```python
task = client.tasks.wait(task_id, timeout=300, poll_interval=0.5)
if task.status.value != "succeeded":
    raise RuntimeError(task.summary or "Hubuum task failed")
```

The async equivalent uses `timeout_seconds` and awaits without blocking the
event loop.
