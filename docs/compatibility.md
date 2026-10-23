# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
| 0.0.12 | [`v0.0.20`](https://github.com/hubuum/hubuum/tree/v0.0.20) | Verified | [26 core and 4 recovery tests, including rotating sessions and eight complete restore cycles](compatibility-evidence.md#v0020-target) |
| 0.0.11 | [`v0.0.18`](https://github.com/hubuum/hubuum/tree/v0.0.18) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.10 | [`v0.0.17`](https://github.com/hubuum/hubuum/tree/v0.0.17) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.9 | [`v0.0.16`](https://github.com/hubuum/hubuum/tree/v0.0.16) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| [7165240](https://github.com/hubuum/hubuum-client-python/commit/7165240) | [`v0.0.15`](https://github.com/hubuum/hubuum/tree/v0.0.15) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.8 | [`v0.0.14`](https://github.com/hubuum/hubuum/tree/v0.0.14) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.6 | [`v0.0.9`](https://github.com/hubuum/hubuum/tree/v0.0.9) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.5 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.4 | [`v0.0.8`](https://github.com/hubuum/hubuum/tree/v0.0.8) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.3 | [`v0.0.5`](https://github.com/hubuum/hubuum/tree/v0.0.5) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.2 | [`v0.0.4`](https://github.com/hubuum/hubuum/tree/v0.0.4) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |
| 0.0.1 | [`v0.0.3`](https://github.com/hubuum/hubuum/releases/tag/v0.0.3) | Verified | [Evidence](compatibility-evidence.md#compatibility-matrix) |

`Verified` means the complete Docker-backed suite passed for the exact
client/server pair. The current server target is selected by tag and locked to
an immutable multi-platform image:

```text
ghcr.io/hubuum/hubuum-server:v0.0.20@sha256:eaf59f8a4b4793030a78bc1637a8e2b9fad2f810b8621ff9a874dca534b9a23a
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

## Typed parity

The unreleased `client.api` interface provides matching sync and async types for
all 257 operations and 391 schemas in this pinned contract. See
[typed API usage](typed-api.md) and the [operation table](typed-operations.md).
Existing convenience services retain their established return types.

## Before upgrading

Client 0.0.12 targets server v0.0.20 with matching sync and async behavior.
Use [credential approvals](credentials.md) before protected mutations and
[schema evolution](schema.md) when changing validation policy on populated
classes. The registered OpenAPI surface covers all 257 operations; dedicated
typed services and generic operation calls are distinguished in the API guides.

Server v0.0.20 requires an offline migration from v0.0.19 and emits backup
format 10. Upgrade every API, worker, and restore executor together, retain a
pre-upgrade backup and matching binaries for rollback, and sign in again.
Follow the [server deployment guide](https://hubuum.github.io/hubuum/v0.0.20/deployment/)
and [backup compatibility](https://hubuum.github.io/hubuum/v0.0.20/backup-restore/).

## Verification evidence

[Detailed evidence and historical migrations](compatibility-evidence.md) retain tested
image identities, dates, suite results, and earlier compatibility limits.

## v0.0.20 target

See [v0.0.20 evidence](compatibility-evidence.md#v0020-target) for the exact
OpenAPI provenance and completed live/recovery checks.

## v0.0.18 target

See [v0.0.18 target](compatibility-evidence.md#v0018-target) in the historical evidence.

## v0.0.17 target

See [v0.0.17 target](compatibility-evidence.md#v0017-target) in the historical evidence.

## Changes introduced in v0.0.16

See [changes introduced in v0.0.16](compatibility-evidence.md#changes-introduced-in-v0016) in the historical evidence.

## Changes introduced in v0.0.15

See [changes introduced in v0.0.15](compatibility-evidence.md#changes-introduced-in-v0015) in the historical evidence.

## Changes since v0.0.9

See [changes since v0.0.9](compatibility-evidence.md#changes-since-v009) in the historical evidence.

## Meaning of compatibility

See [meaning of compatibility](compatibility-evidence.md#meaning-of-compatibility) in the historical evidence.

## Contract-specific response shapes

See [contract-specific response shapes](compatibility-evidence.md#contract-specific-response-shapes) in the historical evidence.

## Forward compatibility

See [forward compatibility](compatibility-evidence.md#forward-compatibility) in the historical evidence.

## Collection integrations

See [collection integrations](compatibility-evidence.md#collection-integrations) in the historical evidence.

## Moved reference sections

<!-- markdownlint-disable MD033 -->

| Topic | Reference |
| --- | --- |
| <span id="upgrade-from-v0016"></span>Upgrade from v0.0.16 | [Details](compatibility-evidence.md#upgrade-from-v0016) |
| <span id="upgrade-from-v0015"></span>Upgrade from v0.0.15 | [Details](compatibility-evidence.md#upgrade-from-v0015) |
| <span id="server-upgrade-considerations"></span>Server upgrade considerations | [Details](compatibility-evidence.md#server-upgrade-considerations) |

<!-- markdownlint-enable MD033 -->

## Rotating session API

`login_session()` in both runtimes uses the required `/api/v1/auth` contract.
Migrate interactive callers from `login()`, which remains available only for
older servers. There is no automatic authentication downgrade. The server no
longer supports legacy interactive clients; explicit PAT injection remains valid.
The complete live suite requires rotation, replay revocation, and logout checks.

The operation registry includes all 257 server operations. The seven generic
authentication operation IDs replace `ApiV0Auth` with `ApiV1Auth`; callers using
those identifiers must update them. Dedicated
typed services remain projections of that contract: newly added history,
search hydration, credential activity, and observation-management operations can
be called through `client.openapi.call()` or authenticated relative `request()`.
