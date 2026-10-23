# Hubuum client for Python

`hubuum-client` is a small, modern interface to the Hubuum REST API. Version
0.0.12 targets Hubuum server v0.0.20 and gives synchronous and
asynchronous applications the same typed resource model.

## Installation

```bash
python -m pip install "hubuum-client==0.0.12"
```

Python 3.11 and later are supported.

## First request

Load the [Atlas inventory](example-dataset.md) and use an account with read access:

```python
from hubuum_client import Client, Credentials, Query

with Client("https://hubuum.example.com") as client:
    client.login_session(Credentials("alice", "secret"))
    page = client.classes.by_name("Server").objects.page(
        Query().where("name", "web-01").limit(25).include_total()
    )
    for item in page:
        print(item.id, item.name)
```

## Design goals

- **Predictable typing.** Request and response bodies are Pydantic v2 models;
  resource identities use distinct `NewType` declarations.
- **Runtime parity.** `Client` and `AsyncClient` expose matching resources,
  errors, authentication behavior, pagination semantics, and all 257 pinned
  OpenAPI operations.
- **Secure defaults.** TLS validation is enabled, tokens and credentials are
  redacted, and raw requests cannot switch origin or traverse URL paths.
- **Forward compatibility.** Response models accept new server fields while
  request models reject misspelled or unsupported fields.
- **Bounded automation.** Automatic pagination has cursor-cycle, page-count,
  and item-count guards; task polling has an explicit timeout.

## What is typed

The strongly modeled service surface includes collections, hierarchy
operations, classes, class-scoped objects, natural-key class/object routes,
atomic object-data JSON Patch, users, [service accounts](service-accounts.md),
groups, group membership, class and
object relations, nested token scopes and renewal, typed object aggregate
measures, task events, import v2, and exports. Health, readiness, and public
configuration are available before authentication.

The unreleased [`client.api` interface](typed-api.md) provides matching sync and
async types for all 257 operations and 391 named schemas in the immutable
v0.0.20 specification, including administrative domains. Existing convenience
services remain available. The `openapi` service also exposes every operation
by `operationId` for callers that need generic JSON, text, or byte values.
CI checks both interfaces against the authoritative server contract.

Continue with [client setup](client.md), then see
[queries and pagination](querying.md).

Use [credential approvals](credentials.md) for the v0.0.20 protected mutations,
and [task discovery](querying.md#task-discovery) for lifecycle and resource filters.

## Explore a shared example

[Load and explore Atlas](example-dataset.md) to work with the same classes,
objects, and relations used in the server, CLI, frontend, and client guides.
