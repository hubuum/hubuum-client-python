# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| 0.0.5 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.4 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | Pinned e2e passed locally on 2026-08-05 |
| 0.0.3 | [`v0.0.5`](https://github.com/hubuum/hubuum/tree/v0.0.5) | Verified | Pinned e2e passed locally on 2026-07-26 |
| 0.0.2 | [`v0.0.4`](https://github.com/hubuum/hubuum/tree/v0.0.4) | Verified | Pinned e2e passed locally on 2026-07-25 |
| 0.0.1 | [`v0.0.3`](https://github.com/hubuum/hubuum/releases/tag/v0.0.3) | Verified | [Pinned e2e passed on 2026-07-24](https://github.com/hubuum/hubuum-client-python/actions/runs/30128172912) |

`Verified` means the complete Docker-backed suite passed for the exact
client/server pair. The server release is selected by tag and locked to the
immutable image used by that run:

```text
ghcr.io/hubuum/hubuum-server:v0.0.8@sha256:850bfd95a2802485f93c1700fbff5a33465cbc7855cbc94962982c1074fd96f6
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

The v0.0.8 run passed the complete pinned live-server suite, including public
probes/configuration/metrics, core CRUD/natural keys, nested object-data queries and JSON Patch, IAM/relations,
forced cursor traversal, non-administrator authorization and live error
mapping, a complete async resource lifecycle, and synchronous and asynchronous
scoped-token lifecycles. Each token lifecycle mints a nested permission and
resource scope, verifies exact metadata and allowed/denied operations, revokes
the token, and confirms that it can no longer authenticate. The v0.0.8 suite
also checks the public default token lifetime and the authoritative expiry
returned by login and token minting. It additionally exercises v0.0.8's
per-object relation cardinality limits, timestamp restoration through the
typed import service, export phase durations, and typed task events. The suite
imports the wheel built from the tested source in a clean environment.

## v0.0.8 target

The client pins the released OpenAPI document at commit
`9de161ff05f563302cfe6f74b04b80c1f617f5d6`, with SHA-256
`15329801b66af891b18f231d8faa81daf0c6ca12e0e581632e10e9ba3b88295a`.
It still contains 196 operations, so the complete operation-ID manifest remains
stable. The additive schema changes are typed: class relations accept and
return `from_max_relations` and `to_max_relations`; core import records accept
`RestoreTimestamps`; and export task details expose total, query, hydration,
and render durations. Typed import/export services and task-event pagination
cover the surrounding task workflows.

## Meaning of compatibility

For this project, targeting server v0.0.8 means:

- authentication, public probes, and client configuration work against the
  pinned server;
- the typed collection, class, object, IAM, relation, query, forced multi-page
  pagination, and sync/async mutation workflows pass live-server tests;
- the live server confirms non-administrator read grants and denied writes,
  plus client mappings for `400`, `401`, `403`, `404`, and `409` responses;
- every one of the 196 v0.0.8 OpenAPI operations is present in the checked
  operation manifest, including JSON Patch, rendered export media, and SSE;
- arbitrary extension routes remain accessible through the safe request
  extension point;
- request models follow the v0.0.8 wire schema, while response models tolerate
  additive fields.

It does not promise that every operation has a domain-specific Pydantic model
or convenience method. Administrative features such as backups, restores,
computed fields, event sinks, and remote targets use the complete
`openapi.call()` interface while their higher-level resource models mature.

Contract completeness and live behavioral coverage are separate claims. The
OpenAPI check validates every method, path, request media type, and success
response media type; the live suite concentrates on representative core
workflows and does not invoke all 196 operations.

## Known contract accommodations

The committed v0.0.8 OpenAPI `Group` schema declares `identity_scope_id`. The
Python response model also accepts the scope name as `identity_scope` for
compatibility with server responses that use that representation. Requests
continue to use the documented scope name.

Class write responses also embed a complete `collection` object and can return
`validate_schema: null`, whereas OpenAPI declares `collection_id` and a required
boolean. `HubuumClass` retains the embedded collection, derives its stable
`collection_id`, and accepts the nullable validation flag.

## Forward compatibility

Running against Hubuum `main` or a future release-candidate revision can
identify drift early, but such a run is a forward-compatibility signal only. It
does not replace the immutable v0.0.8 e2e run and does not change a released
client's declared target.

Breaking server changes require a new compatibility row, changelog entry, and
successful e2e evidence for the new tag-and-digest image.
