# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| Unreleased | [`v0.0.13`](https://github.com/hubuum/hubuum/tree/v0.0.13) | Verified | 14 core and 2 recovery tests passed locally on 2026-09-09 (Python 3.14, Docker, Linux ARM64 server) |
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
ghcr.io/hubuum/hubuum-server:v0.0.13@sha256:512562e789d6430875c5075faf832a9669a4f266f7fe9fbf8c1524b49a6476c5
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

## v0.0.13 target

The client pins the released OpenAPI document at commit
`8ecefbf3e3147714014221598d9873ba92e0fdce`, with SHA-256
`7ee39d51c9750732223e147ad555c6e84e0a2511a0a977de4fad40c0d95c5ae7`.
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

The v0.0.13 OpenAPI document differs from v0.0.12 only in its version field;
there are no operation or schema changes. The server fixes the repeated-restore
maintenance-generation failure reported in
[hubuum/hubuum#378](https://github.com/hubuum/hubuum/issues/378), and preserves
JSON `null` in required JSON columns during PostgreSQL restores. Existing
version 5 backups remain readable. Install matching v0.0.13 server,
administrator, and template worker binaries, including the separate restore
executor; see the [release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.13).

## Changes since v0.0.9

- Structured search supports collections, classes, objects, audit events, users,
  groups, and service accounts, boolean predicates, exact totals, and cursor
  pagination. Object searches support exact class selectors and related-object
  predicates. Existing object-list routes also accept named `related.<alias>`
  filter groups. See the [v0.0.10 release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.10)
  and [search API](https://github.com/hubuum/hubuum/blob/v0.0.13/docs/search_api.md).
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

For this project, targeting server v0.0.13 means:

- authentication, public probes, client configuration, typed CRUD, natural keys,
  nested object-data filtering, JSON Patch, IAM, relations, forced multi-page
  pagination, and sync/async mutation workflows are exercised by the live suite;
- live tests check non-administrator read grants and denied writes, mappings for
  `400`, `401`, `403`, `404`, `409`, and `412`, token lifecycle operations,
  principal-settings JSON Patch, relation cardinality, import-v2 timestamps,
  export durations, and task events;
- structured JSON and SSE search are exercised in both runtimes;
- the disposable stack runs four consecutive full backup/restore cycles,
  covering sync-then-async and async-then-sync order without restarting the
  server or executor. Version 5 backups include history; restored objects retain
  data, JSON `null`, and revisions, post-backup objects disappear, old tokens
  are rejected, and login works after an administrator password reset;
- every method, path, request media type, and successful response media type
  matches the 204-operation manifest;
- request models follow the wire contract, while response models tolerate
  additive fields.

The live suite imports the built wheel in an isolated environment. Contract
completeness and live behavioral coverage are separate claims: representative
workflows are tested, not all 204 operations. Full restore tests run after the
core suite and only against the wrapper-owned disposable stack in the default
`single` database role mode. Caller-managed servers never run this recovery
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
identify drift early. They do not replace the immutable v0.0.13 e2e run or
change a released client's declared target. Breaking server changes require a
new compatibility row, changelog entry, and successful evidence for the new
tag-and-digest image.
