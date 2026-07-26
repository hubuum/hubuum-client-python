# Hubuum client library (Python)

[![CI](https://github.com/hubuum/hubuum-client-python/actions/workflows/ci.yml/badge.svg)](https://github.com/hubuum/hubuum-client-python/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://peps.python.org/pep-0561/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

`hubuum-client` is a modern, fully typed Python client for the
[Hubuum](https://github.com/hubuum/hubuum) asset-management API. It provides
matching synchronous and asynchronous clients, Pydantic v2 models, typed
resource IDs, immutable queries, cursor pagination, structured errors, and a
contract-checked interface for all 196 operations in the server's OpenAPI
surface.

Version 0.0.3 targets Hubuum server **v0.0.5**. Compatibility is tested against
the tag-and-digest server image recorded in the
[compatibility matrix](docs/compatibility.md). Client version 0.0.2 remains the
v0.0.4-compatible baseline.

## Installation

```bash
python -m pip install hubuum-client
```

Python 3.11 or newer is required. The runtime dependencies are only
[HTTPX](https://www.python-httpx.org/) and
[Pydantic](https://docs.pydantic.dev/).

## Quick start

```python
from hubuum_client import ClassCreate, Client, Credentials, Query

with Client("https://hubuum.example.com") as client:
    client.login(Credentials("alice", "correct-horse-battery-staple"))

    classes = client.classes.list(
        Query().where("name", "server").limit(25).include_total()
    )

    created = client.classes.create(
        ClassCreate(
            name="server",
            collection_id=1,
            description="Server inventory",
        )
    )
    print(created.id, len(classes))
```

The asynchronous API has the same shape:

```python
import asyncio

from hubuum_client import AsyncClient, Credentials, Query


async def main() -> None:
    async with AsyncClient("https://hubuum.example.com") as client:
        await client.login(Credentials("alice", "secret"))
        page = await client.classes.by_name("Servers").objects.page(
            Query().where("name", "web-01").include_total()
        )
        print(page.total_count, page.items)


asyncio.run(main())
```

Context-managed clients remain open for the entire block and reuse their HTTP
connection pools. Applications that manage startup and shutdown explicitly can
keep the same client for their full lifetime:

```python
client = Client("https://hubuum.example.com")
try:
    client.login(Credentials("alice", "secret"))
    run_application(client)
finally:
    client.close()
```

The async equivalent uses `await client.close()`. Reuse a client instead of
constructing one per request so eligible TCP/TLS connections can be reused; see
[Client setup](docs/client.md) for synchronous and asynchronous lifetime
examples.

Credentials and bearer tokens have redacted representations. TLS certificate
validation is enabled by default; disabling it is an explicit client option and
should be limited to disposable development systems.

Hubuum v0.0.5 reports the authoritative expiry for newly issued tokens. After
login or token minting, it is available as `client.token.expires_at` or
`created_token.expires_at`. The unauthenticated public configuration reports
the default used when no explicit expiry is requested:

```python
config = client.config()
default_hours = config.authentication.default_token_lifetime_hours
```

## Resource services

The typed surface currently covers the most common Hubuum workflows:

- collections, hierarchy traversal, and parent moves;
- classes and class-scoped objects, including exact-name addressing and nested
  `data` filtering and atomic JSON Patch;
- users, groups, memberships, and user anonymization;
- scoped token listing, minting, and revocation;
- class relations and object relations;
- typed grouped and multi-measure object aggregates;
- cursor pagination and task polling;
- health, readiness, and public server configuration.

Every v0.0.5 OpenAPI operation is registered by its stable `operationId`:

```python
from hubuum_client import OpenAPIOptions

result = client.openapi.call(
    "getApiV1Search",
    options=OpenAPIOptions(params={"q": "server", "limit_per_kind": 10}),
)
```

The checked-in manifest covers all 196 methods, paths, path variables, body
media types, public/authenticated policies, JSON responses, rendered text
exports, and the search event stream. `request()` remains available for
server extensions outside the pinned specification. Both interfaces are
constrained to the configured origin.

## Querying and pagination

Queries are immutable and reusable:

```python
from hubuum_client import FilterOperator, Query

base = Query().where("name", "server", FilterOperator.ICONTAINS)
first_page = client.classes.page(base.limit(25).include_total())
all_matches = client.classes.all(base, max_items=5_000)

active_web_servers = client.classes.by_name("Servers").objects.all(
    Query()
    .data("status")
    .equals("active")
    .data("tags")
    .contains_all("web", "api")
)
```

`Page` exposes `items`, `next_cursor`, `total_count`, and the effective
`page_limit`. Automatic pagination detects repeated cursors and enforces page
and item limits. The fluent `data()` selector supports nested paths, typed
comparisons, arrays, nulls, object keys, and IP/network operators; see
[Queries and pagination](docs/querying.md).

Group membership uses the same typed, cursor-aware interface:

```python
member_page = client.groups.members_page(group_id, Query().limit(25).include_total())
all_members = client.groups.all_members(group_id, max_items=5_000)
```

## Documentation

- [Client setup](docs/client.md)
- [Queries and pagination](docs/querying.md)
- [API reference](docs/api.md)
- [Compatibility policy](docs/compatibility.md)
- [Docker-backed end-to-end tests](docs/e2e.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run bandit -q -r src scripts
uv run zizmor .
uv run pytest --cov
uv run mkdocs build --strict
```

The full pinned-server workflow is:

```bash
./scripts/run-e2e-tests.sh
```

See [AGENTS.md](AGENTS.md) for repository conventions and the exact e2e stack.
Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for the
development and pull-request workflow. Maintainers can find the release process
in [the release guide](docs/releasing.md).

Please report security issues according to [SECURITY.md](SECURITY.md), rather
than in a public issue.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
