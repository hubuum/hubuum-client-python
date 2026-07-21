# Hubuum client for Python

`hubuum-client` is a small, modern interface to the Hubuum REST API. The first
release targets Hubuum server v0.0.3 and gives synchronous and asynchronous
applications the same typed resource model.

```python
from hubuum_client import Client, Credentials, Query

with Client("https://hubuum.example.com") as client:
    client.login(Credentials("alice", "secret"))
    page = client.classes.page(
        Query().where("name", "server").limit(25).include_total()
    )
    for item in page:
        print(item.id, item.name)
```

## Design goals

- **Predictable typing.** Request and response bodies are Pydantic v2 models;
  resource identities use distinct `NewType` declarations.
- **Runtime parity.** `Client` and `AsyncClient` expose matching resources,
  errors, authentication behavior, and pagination semantics.
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

The dedicated service surface includes collections, hierarchy operations,
classes, class-scoped objects, users, groups, group membership, class and object
relations, and tasks. Health, readiness, and public configuration are available
before authentication.

Hubuum v0.0.3 has a wider administrative and task-backed API. Those routes can
be used immediately through the origin-locked `request()` method. Dedicated
models and helpers will be added without removing the safe extension point.

Continue with [client setup](client.md), then see
[queries and pagination](querying.md).
