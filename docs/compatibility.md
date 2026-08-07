# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| Unreleased | [`v0.0.9`](https://github.com/hubuum/hubuum/tree/v0.0.9) | Verified | Pinned e2e passed locally on 2026-08-07 |
| 0.0.5 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.4 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.3 | [`v0.0.5`](https://github.com/hubuum/hubuum/tree/v0.0.5) | Verified | Pinned e2e passed locally on 2026-07-26 |
| 0.0.2 | [`v0.0.4`](https://github.com/hubuum/hubuum/tree/v0.0.4) | Verified | Pinned e2e passed locally on 2026-07-25 |
| 0.0.1 | [`v0.0.3`](https://github.com/hubuum/hubuum/releases/tag/v0.0.3) | Verified | [Pinned e2e passed on 2026-07-24](https://github.com/hubuum/hubuum-client-python/actions/runs/30128172912) |

`Verified` means the complete Docker-backed suite passed for the exact
client/server pair. The server release is selected by tag and locked to the
immutable image used by that run:

```text
ghcr.io/hubuum/hubuum-server:v0.0.9@sha256:1f12baf882b6d3df5b4b2dbdf26aad0793274e57f86a2c186b8e1e68632db5db
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

The v0.0.9 run passed the complete pinned live-server suite, including public
probes/configuration/metrics, core CRUD/natural keys, nested object-data queries and JSON Patch, IAM/relations,
forced cursor traversal, non-administrator authorization and live error
mapping (including successful and stale `If-Match` updates and deletes in both
runtimes), a complete async resource lifecycle, and synchronous and
asynchronous scoped-token lifecycles.
Each token lifecycle mints a nested permission and
resource scope, verifies revisioned metadata, point lookup, renewal,
allowed/denied operations, revoked-token selection, and rejection after
revocation. The suite also checks principal-settings JSON Patch, the public
default and maximum token lifetimes, import v2 timestamp restoration,
per-object relation cardinality limits, export phase durations, and typed task
events. It imports the wheel built from the tested source in a clean
environment.

## v0.0.9 target

The client pins the released OpenAPI document at commit
`04367a8d6eb38e4356b4e4673269b356f46bbcc3`, with SHA-256
`f4fcadd502ec3329973de7eb879f483ced9de232139057c9c951b89f8088e0dd`.
It contains 202 operations. The operation manifest includes the six new point
lookup and token-renewal operations plus every changed request and successful
response media type. Typed models cover positive resource revisions, canonical
user and group-membership shapes, retained-token lifecycle state, token point
lookup and renewal, import-v2 conditions, and the public maximum token
lifetime. Principal settings PATCH can select JSON Patch or either supported
JSON Merge Patch media type.

## Meaning of compatibility

For this project, targeting server v0.0.9 means:

- authentication, public probes, and client configuration work against the
  pinned server;
- the typed collection, class, object, IAM, relation, query, forced multi-page
  pagination, and sync/async mutation workflows pass live-server tests;
- the live server confirms non-administrator read grants and denied writes,
  plus client mappings for `400`, `401`, `403`, `404`, `409`, and `412`
  responses;
- every one of the 202 v0.0.9 OpenAPI operations is present in the checked
  operation manifest, including JSON Patch, rendered export media, and SSE;
- arbitrary extension routes remain accessible through the safe request
  extension point;
- request models follow the v0.0.9 wire schema, while response models tolerate
  additive fields.

It does not promise that every operation has a domain-specific Pydantic model
or convenience method. Administrative features such as backups, restores,
computed fields, event sinks, and remote targets use the complete
`openapi.call()` interface while their higher-level resource models mature.

Contract completeness and live behavioral coverage are separate claims. The
OpenAPI check validates every method, path, request media type, and success
response media type; the live suite concentrates on representative core
workflows and does not invoke all 202 operations.

## Contract-specific response shapes

Hubuum v0.0.9 user lists include scope and provider names, while canonical user
point responses use the stable `identity_scope_id` and omit provider metadata.
`User` represents list entries and `UserPoint` represents canonical reads and
mutations, so neither type invents absent fields. Groups follow the same split:
`Group` includes list-only directory synchronization state, while `GroupPoint`
models revision-owned point responses without that operational state.

Class point routes now return the canonical class by default and use
`include=collection` for the expanded representation. `HubuumClass` accepts
both forms, retains an embedded collection when present, and derives its stable
`collection_id` from that expansion.

## Forward compatibility

Running against Hubuum `main` or a future release-candidate revision can
identify drift early, but such a run is a forward-compatibility signal only. It
does not replace the immutable v0.0.9 e2e run and does not change a released
client's declared target.

Breaking server changes require a new compatibility row, changelog entry, and
successful e2e evidence for the new tag-and-digest image.
