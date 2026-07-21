# Server compatibility

## Declared target

| Python client | Hubuum server | Required integration image |
| --- | --- | --- |
| 0.0.1 | 0.0.3 | `ghcr.io/hubuum/hubuum-server@sha256:f1f57a991f69005ee81f24e77533e61f75b5586949d98cccf1c40fc4329eb186` |

The digest, not a floating tag, defines the release's compatibility evidence.
The same value is stored in `src/hubuum_client/_constants.py`, the e2e wrapper,
and CI.

The initial 0.0.1 verification on 2026-07-21 passed the complete unit suite
(including strict typing and sync/async parity) and all three Docker-backed
workflows against this digest: core CRUD/natural keys, IAM/relations, and async
consumption.

## Meaning of compatibility

For this project, targeting server v0.0.3 means:

- authentication, public probes, and client configuration work against the
  pinned server;
- the typed collection, class, object, IAM, relation, query, and pagination
  workflows pass live-server tests;
- arbitrary v0.0.3 relative routes remain accessible through the safe request
  extension point;
- request models follow the v0.0.3 wire schema, while response models tolerate
  additive fields.

It does not promise that every one of the 196 OpenAPI operations has a dedicated
Python convenience method in 0.0.1. Administrative features such as backups,
restores, computed fields, event sinks, remote targets, and imports/exports can
be called through `request()` while their high-level APIs mature.

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
successful e2e evidence for the new immutable image.
