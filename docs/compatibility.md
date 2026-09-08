# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| Unreleased | [`v0.0.12`](https://github.com/hubuum/hubuum/tree/v0.0.12) | Verified | All 14 pinned e2e tests passed locally on 2026-09-08 (Python 3.14, Docker, Linux ARM64 server) |
| 0.0.6 | [`v0.0.9`](https://github.com/hubuum/hubuum/tree/v0.0.9) | Verified | [Pinned e2e passed on 2026-08-07](https://github.com/hubuum/hubuum-client-python/actions/runs/31214164409) |
| 0.0.5 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.4 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.3 | [`v0.0.5`](https://github.com/hubuum/hubuum/tree/v0.0.5) | Verified | Pinned e2e passed locally on 2026-07-26 |
| 0.0.2 | [`v0.0.4`](https://github.com/hubuum/hubuum/tree/v0.0.4) | Verified | Pinned e2e passed locally on 2026-07-25 |
| 0.0.1 | [`v0.0.3`](https://github.com/hubuum/hubuum/releases/tag/v0.0.3) | Verified | [Pinned e2e passed on 2026-07-24](https://github.com/hubuum/hubuum-client-python/actions/runs/30128172912) |

`Verified` means the complete Docker-backed suite passed for the exact
client/server pair. The current server target is selected by tag and locked to
an immutable multi-platform image:

```text
ghcr.io/hubuum/hubuum-server:v0.0.12@sha256:6441ccbe2906d80d0e6ef5e8a9b8e4a7e1afc9c39c8d43d93ac62a5cd0e6e865
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

## v0.0.12 target

The client pins the released OpenAPI document at commit
`a3928a03451e2a2365b7405f7229dc4857b4fa05`, with SHA-256
`4a394bd86326c3abe80a784151133b2e9553485303221cd8f91be980d86aaebb`.
The exact document is [committed with the client](openapi.json), so the default
contract check runs without network access and detects document or client
manifest drift. An explicit upstream check/update workflow is documented in
[CONTRIBUTING.md](https://github.com/hubuum/hubuum-client-python/blob/main/CONTRIBUTING.md#openapi-contract-updates).

All 204 operations are registered, up from 202 in v0.0.9. No operations were
removed. The two additions are structured JSON search (`postApiV1Search`) and
structured SSE search (`postApiV1SearchStream`), introduced in v0.0.10. Both
synchronous and asynchronous `openapi.stream()` now accept `json=` so the POST
stream can send the same version 1 request envelope as ordinary structured
search. The manifest also records the corrected `text/event-stream` response
media type for the existing GET search stream.

## Changes since v0.0.9

- Structured search supports collections, classes, objects, audit events, users,
  groups, and service accounts, boolean predicates, exact totals, and cursor
  pagination. Object searches support exact class selectors and related-object
  predicates. Existing object-list routes also accept named `related.<alias>`
  filter groups. See the [v0.0.10 release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.10)
  and [search API](https://github.com/hubuum/hubuum/blob/v0.0.12/docs/search_api.md).
- Graph responses describe a complete bounded neighborhood, not a cursor page.
  `limit` is a safety bound, and `include_total` has no effect. v0.0.12 bounds
  traversal depth and generated work, external-policy export scans, and template
  batches. Narrow queries that exceed server limits.
- Restore confirmation now returns `202 Accepted` when queued. Poll
  `getApiV1RestoresByRestoreIdStatus` with `X-Hubuum-Restore-Capability` until `succeeded`
  or `failed`. This status route does not need a bearer token, including after
  a restore replaces token state. Capability values are redacted from client
  diagnostics. The server requires a separate `hubuum-admin --restore-executor`
  process for web restores.
- Full backups use version 5 logical sections, introduced in v0.0.10. Operators
  upgrading from v0.0.9 or older must first upgrade to v0.0.10 or v0.0.11 and
  create a version 5 backup. Older backup formats are not converted in place.
  Portable client imports continue to use import version 2.
- Containers no longer apply migrations during startup. Run
  `hubuum-admin --migrate` before API or worker processes. The e2e wrapper now
  does this in a separate container using the same pinned image, with failure
  diagnostics and cleanup. Default `single` database role mode remains
  supported; split roles are optional.
- Newly issued bearer values use opaque `hbt1.<key-id>.<secret>` strings. The
  existing client token type already accepts them; callers must not parse or
  reconstruct tokens. Legacy tokens remain supported by the server.
- The contract adds positive ID bounds and a closed membership principal-kind
  enum. Core typed CRUD response shapes and the public client configuration
  remain compatible. Administrative configuration adds storage, database-role,
  secret-source, token-key and tracing settings; database diagnostics can return
  `404` for backends that do not provide them.

The [v0.0.11 release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.11)
primarily cover storage internals and adapter changes. The
[v0.0.12 upgrade notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.12)
also cover migrations, coordinated server/admin/template-worker deployment,
external authorization policy changes, token-key rotation, and rollback.
Updating this Python package does not migrate a server installation.

## Meaning of compatibility

For this project, targeting server v0.0.12 means:

- authentication, public probes, client configuration, typed CRUD, natural keys,
  nested object-data filtering, JSON Patch, IAM, relations, forced multi-page
  pagination, and sync/async mutation workflows are exercised by the live suite;
- live tests check non-administrator read grants and denied writes, mappings for
  `400`, `401`, `403`, `404`, `409`, and `412`, token lifecycle operations,
  principal-settings JSON Patch, relation cardinality, import-v2 timestamps,
  export durations, and task events;
- structured JSON and SSE search are exercised in both runtimes;
- every method, path, request media type, and successful response media type
  matches the 204-operation manifest;
- request models follow the wire contract, while response models tolerate
  additive fields.

The live suite imports the built wheel in an isolated environment. Contract
completeness and live behavioral coverage are separate claims: representative
workflows are tested, not all 204 operations. Destructive full restores are
covered by client request/response regressions rather than the shared live
suite. Administrative features such as backups, restores, computed fields,
event sinks, and remote targets use `openapi.call()` while their higher-level
resource models mature.

## Contract-specific response shapes

User and group list models retain their list-only metadata; `UserPoint` and
`GroupPoint` model canonical revision-owned reads and mutations. Class point
routes return the canonical class by default and use `include=collection` for
an expanded representation. `HubuumClass` accepts both forms and derives its
stable `collection_id` from the expansion when needed.

## Forward compatibility

Runs against Hubuum `main`, a release candidate, or an overridden image can
identify drift early. They do not replace the immutable v0.0.12 e2e run or
change a released client's declared target. Breaking server changes require a
new compatibility row, changelog entry, and successful evidence for the new
tag-and-digest image.
