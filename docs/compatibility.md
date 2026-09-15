# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| Unreleased | [`v0.0.15`](https://github.com/hubuum/hubuum/tree/v0.0.15) | Verified | 16 core and 4 recovery tests passed locally on 2026-09-15 (Python 3.11.12, Podman, Linux AMD64 server) |
| 0.0.8 | [`v0.0.14`](https://github.com/hubuum/hubuum/tree/v0.0.14) | Verified | [14 core and 4 recovery tests passed on 2026-09-10](https://github.com/hubuum/hubuum-client-python/actions/runs/34446685036) (Python 3.11, Docker, Linux AMD64 server) |
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
ghcr.io/hubuum/hubuum-server:v0.0.15@sha256:36af667dbc9e221a40448496d4a87e168c999d0834df4b69177345ff3d36e821
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

## v0.0.15 target

The client pins the released OpenAPI document at commit
`4bb889c66a5e2a1dfc86d1b6beac7495912fd02e`, with SHA-256
`d654d5e18aee32e998cb47ce1da5dadbc5fe83ff22a260192ba125b201c3649b`.
The exact document is [committed with the client](openapi.json), so the default
contract check runs without network access and detects document or client
manifest drift. An explicit upstream check/update workflow is documented in
[CONTRIBUTING.md](https://github.com/hubuum/hubuum-client-python/blob/main/CONTRIBUTING.md#openapi-contract-updates).

All 218 operations are registered, up from 204 in v0.0.14, with no removals.
The 14 additions cover schema revision staging, activation and abandonment,
impact and revalidation tasks, compliance pages, retained HTML repair reports,
and generic task cancellation. Typed services support these operations in both
runtimes; see [schema evolution](schema.md). Imports accept the exact nested
`schema_activation` policy, and typed tasks include the new `schema_validation`
kind, cancellation/deadline metadata, unattempted item counts, and conservative
remote-dispatch state.

### Server upgrade considerations

- Schema-policy PATCH and legacy import overwrites on nonempty classes now
  return `409 Conflict`. Stage a revision, request impact, and explicitly
  activate it. Strict activation rechecks the active revision and population;
  administrator-only `allow_pending` activation can proceed without proof.
- Backup format **6** replaces format 5 and retains schema revisions, state,
  evidence, and history. Restore older artifacts with their matching server
  release, migrate the database, and create a format 6 backup. No automatic
  artifact converter is provided. Portable imports remain version 2.
- Drain old workers, apply the release migrations, and start matching API,
  administrator, restore-executor, and worker binaries. Existing enforced
  objects begin pending; request revalidation after migration.
- JSON Schema admission and validation have shared document, expansion,
  object-size, and work budgets. Stored schemas are rechecked when used.
  Simplify unsupported references, patterns, or excessive expansion before
  resuming writes; see the [server validation limits](https://github.com/hubuum/hubuum/blob/v0.0.15/docs/json_schema_validation.md).
- JSON impact reports can return `413` above the 16 MiB assembly budget.
  HTML reports have separate assembly and output limits. Failed generation
  retains the previous HTML and saved findings.
- Restart in-progress string-sorted pagination after upgrading locale-collated
  databases: v0.0.15 consistently uses byte ordering. External authorization
  traversal now bounds candidate loading and policy checks at 10,000 candidates.
- Cancellation may return `202` while cleanup continues. Poll the task until
  terminal; cancellation does not reverse committed imports or remote effects.

See the [v0.0.15 release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.15)
for the complete server migration and authorization changes. Updating this
Python package does not migrate a server installation.

## Changes since v0.0.9

- Structured search supports collections, classes, objects, audit events, users,
  groups, and service accounts, boolean predicates, exact totals, and cursor
  pagination. Object searches support exact class selectors and related-object
  predicates. Existing object-list routes also accept named `related.<alias>`
  filter groups. See the [v0.0.10 release notes](https://github.com/hubuum/hubuum/releases/tag/v0.0.10)
  and [search API](https://github.com/hubuum/hubuum/blob/v0.0.15/docs/search_api.md).
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
- Full backups used version 5 logical sections starting in v0.0.10; v0.0.15
  moves to format 6 as described above. Portable imports remain version 2.
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

For this project, targeting server v0.0.15 means:

- authentication, public probes, client configuration, typed CRUD, natural keys,
  nested object-data filtering, JSON Patch, IAM, relations, forced multi-page
  pagination, and sync/async mutation workflows are exercised by the live suite;
- live tests check non-administrator read grants and denied writes, mappings for
  `400`, `401`, `403`, `404`, `409`, and `412`, token lifecycle operations,
  principal-settings JSON Patch, relation cardinality, import-v2 timestamps,
  export durations, and task events;
- structured JSON and SSE search, schema impact/repair/activation, import
  activation, and terminal task cancellation are exercised in both runtimes;
- the disposable stack runs eight consecutive full backup/restore cycles,
  covering sync-then-async and async-then-sync order without restarting the
  server or executor. Version 6 backups include and omit history; restored
  objects retain data, JSON `null`, and revisions, post-backup objects disappear, old tokens
  are rejected, and login works after an administrator password reset. Default
  backups after history-free restores and further mutations remain restorable;
  enforced class schemas also survive full restores;
- every method, path, request media type, and successful response media type
  matches the 218-operation manifest;
- request models follow the wire contract, while response models tolerate
  additive fields.

The live suite imports the built wheel in an isolated environment. Contract
completeness and live behavioral coverage are separate claims: representative
workflows are tested, not all 218 operations. Full restore tests run after the
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
identify drift early. They do not replace the immutable v0.0.15 e2e run or
change a released client's declared target. Breaking server changes require a
new compatibility row, changelog entry, and successful evidence for the new
tag-and-digest image.
