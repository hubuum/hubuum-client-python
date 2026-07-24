# Client setup

## Synchronous client

Use a context manager to close pooled connections deterministically:

```python
from hubuum_client import Client, Credentials

with Client("https://hubuum.example.com") as client:
    client.login(Credentials("alice", "secret"))
    me = client.request("GET", "/api/v1/iam/me")
```

`login()` authenticates the current client and returns it for optional chaining.
An existing bearer token can be supplied at construction:

```python
client = Client("https://hubuum.example.com", token=token)
```

`logout()` invalidates the current token on the server and always clears the
local token, including when the server reports an error.

## Application lifetime and connection reuse

Each `Client` owns an HTTPX connection pool. A context-managed client is already
persistent for the entire `with` block; it is not recreated for each request.
Keep that block around the application's work when the application's lifetime
fits naturally into one scope:

```python
from hubuum_client import Client, Credentials

with Client("https://hubuum.example.com") as client:
    client.login(Credentials("alice", "secret"))
    run_application(client)
```

Frameworks, workers, and dependency-injection containers can instead create the
client during application startup and close it during shutdown:

```python
from hubuum_client import Client, Credentials

client = Client("https://hubuum.example.com")
try:
    client.login(Credentials("alice", "secret"))
    servers = client.classes.by_name("Servers").objects
    for server in servers.all():
        print(server.name)
finally:
    client.close()
```

The asynchronous client follows the same ownership pattern:

```python
from hubuum_client import AsyncClient, Credentials

client = AsyncClient("https://hubuum.example.com")
try:
    await client.login(Credentials("alice", "secret"))
    servers = client.classes.by_name("Servers").objects
    for server in await servers.all():
        print(server.name)
finally:
    await client.close()
```

Reuse a client for a meaningful application lifetime rather than constructing
one for every API call. HTTPX reuses eligible TCP/TLS connections from the
client's pool and transparently opens replacements when a connection is no
longer usable. `close()` releases local network resources; `logout()` also
invalidates the current bearer token on the server.

## Asynchronous client

The async client mirrors the resource surface and uses HTTPX's async connection
pool:

```python
from hubuum_client import AsyncClient, Credentials

async with AsyncClient("https://hubuum.example.com") as client:
    await client.login(Credentials("alice", "secret"))
    collections = await client.collections.list()
```

Only I/O methods are awaited. Query construction and Pydantic models are the
same in both modes.

Create and close an `AsyncClient` within the same application and event-loop
lifetime.

## Identity scopes

Provider-scoped authentication uses the optional `identity_scope` value:

```python
credentials = Credentials(
    name="alice",
    password="secret",
    identity_scope="company-directory",
)
client.login(credentials)
```

## HTTP configuration

Both clients accept a shared `ClientOptions` value:

```python
from hubuum_client import Client, ClientOptions

client = Client(
    "https://hubuum.example.com",
    options=ClientOptions(timeout=15.0, user_agent="inventory-service/1.0"),
)
```

`ClientOptions` contains:

- `timeout`: a float or HTTPX timeout object;
- `verify`: certificate validation settings, enabled by default;
- `user_agent`: an application-specific user agent.

The optional `transport` constructor argument accepts an HTTPX transport. It is
primarily useful for explicit proxy policies and deterministic tests.

The base URL must be an absolute HTTP or HTTPS URL without credentials, a query
string, or a fragment. A deployment prefix such as
`https://example.test/hubuum/` is preserved.

!!! warning

    Setting `verify=False` disables server certificate authentication. Use it
    only for a disposable local system whose network you control.

## Public probes and configuration

Authentication is not required for:

```python
health = client.healthz()
readiness = client.readyz()
config = client.config()
```

The client configuration contains the server's effective pagination defaults
and limit, which are useful when sizing queries.
