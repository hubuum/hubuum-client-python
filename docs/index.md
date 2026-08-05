# Hubuum client for Python

`hubuum-client` is a small, modern interface to the Hubuum REST API. Version
0.0.4 targets Hubuum server v0.0.8 and gives synchronous and asynchronous
applications the same typed resource model. Client version 0.0.2 remains the
v0.0.4-compatible baseline, and 0.0.3 remains the v0.0.5 baseline.

```python
from hubuum_client import Client, Credentials, Query

with Client("https://hubuum.example.com") as client:
    client.login(Credentials("alice", "secret"))
    page = client.classes.by_name("Servers").objects.page(
        Query().where("name", "web-01").limit(25).include_total()
    )
    for item in page:
        print(item.id, item.name)
```

## Design goals

- **Predictable typing.** Request and response bodies are Pydantic v2 models;
  resource identities use distinct `NewType` declarations.
- **Runtime parity.** `Client` and `AsyncClient` expose matching resources,
  errors, authentication behavior, pagination semantics, and all 196 pinned
  OpenAPI operations.
- **Secure defaults.** TLS validation is enabled, tokens and credentials are
  redacted, and raw requests cannot switch origin or traverse URL paths.
- **Forward compatibility.** Response models accept new server fields while
  request models reject misspelled or unsupported fields.
- **Bounded automation.** Automatic pagination has cursor-cycle, page-count,
  and item-count guards; task polling has an explicit timeout.

## Installation

```bash
python -m pip install hubuum-client
```

Python 3.11 and later are supported.

## What is typed

The strongly modeled service surface includes collections, hierarchy
operations, classes, class-scoped objects, natural-key class/object routes,
atomic object-data JSON Patch, users, groups, group membership, class and
object relations, nested token scopes, typed object aggregate measures, task
events, imports, and exports. Health, readiness, and public configuration are available before
authentication.

The `openapi` service deliberately registers every operation in the immutable
v0.0.8 specification. Administrative domains that do not yet
have dedicated Pydantic resources are invoked by `operationId` and return
standard typed JSON, text, or byte values. CI compares that manifest with the
authoritative server contract so an endpoint cannot silently fall out of
coverage.

Continue with [client setup](client.md), then see
[queries and pagination](querying.md).
