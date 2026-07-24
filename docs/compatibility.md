# Server compatibility

## Compatibility matrix

| Python client | Hubuum server tag | Status | End-to-end evidence |
| --- | --- | --- | --- |
| 0.0.1 | [`v0.0.3`](https://github.com/hubuum/hubuum/releases/tag/v0.0.3) | Verified | [Pinned e2e passed on 2026-07-24](https://github.com/hubuum/hubuum-client-python/actions/runs/30126233605) |

`Verified` means the complete Docker-backed suite passed for the exact
client/server pair. The server release is selected by tag and locked to the
immutable image used by that run:

```text
ghcr.io/hubuum/hubuum-server:v0.0.3@sha256:f1f57a991f69005ee81f24e77533e61f75b5586949d98cccf1c40fc4329eb186
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

The linked run passed the complete unit and OpenAPI contract suites and the
pinned live-server suite, including core CRUD/natural keys, nested object-data
queries and JSON Patch, IAM/relations, forced cursor traversal,
non-administrator authorization and live error mapping, and a complete async
resource lifecycle. The live suite imports the wheel built from the tested
source in a clean environment.

## Meaning of compatibility

For this project, targeting server v0.0.3 means:

- authentication, public probes, and client configuration work against the
  pinned server;
- the typed collection, class, object, IAM, relation, query, forced multi-page
  pagination, and sync/async mutation workflows pass live-server tests;
- the live server confirms non-administrator read grants and denied writes,
  plus client mappings for `400`, `401`, `403`, `404`, and `409` responses;
- every one of the 196 v0.0.3 OpenAPI operations is present in the checked
  operation manifest, including JSON Patch, rendered export media, and SSE;
- arbitrary extension routes remain accessible through the safe request
  extension point;
- request models follow the v0.0.3 wire schema, while response models tolerate
  additive fields.

It does not promise that every operation has a domain-specific Pydantic model
or convenience method in 0.0.1. Administrative features such as backups,
restores, computed fields, event sinks, remote targets, and imports/exports use
the complete `openapi.call()` interface while their higher-level resource
models mature.

Contract completeness and live behavioral coverage are separate claims. The
OpenAPI check validates every method, path, request media type, and success
response media type; the live suite concentrates on representative core
workflows and does not invoke all 196 operations.

## Known v0.0.3 contract gap

The committed OpenAPI `Group` schema declares `identity_scope_id`, but the
pinned server response serializes the scope name as `identity_scope`. The Python
response model accepts both forms. Requests continue to use the documented
scope name, matching the live server and Rust client.

Class write responses also embed a complete `collection` object and can return
`validate_schema: null`, whereas OpenAPI declares `collection_id` and a required
boolean. `HubuumClass` retains the embedded collection, derives its stable
`collection_id`, and accepts the nullable validation flag.

## Forward compatibility

Running against Hubuum `main` can identify drift early, but such a run is a
forward-compatibility signal only. It does not replace the immutable v0.0.3 e2e
run and does not change a released client's declared target.

Breaking server changes require a new compatibility row, changelog entry, and
successful e2e evidence for the new tag-and-digest image.
