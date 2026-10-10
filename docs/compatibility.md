# Server compatibility

## Compatibility matrix

| Python client | Hubuum server contract | Status | End-to-end evidence |
| --- | --- | --- | --- |
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
ghcr.io/hubuum/hubuum-server:v0.0.18@sha256:5b54248f19171200dfa497174d385a48f90666a415cb31732797043d5e182fc4
```

The tag identifies the supported server release; the digest prevents that tag
from resolving to different content later. The same reference is stored in
`src/hubuum_client/_constants.py`, the e2e wrapper, and CI.

## Before upgrading

Client 0.0.11 targets server v0.0.18 with matching sync and async behavior.
Use [credential approvals](credentials.md) before protected mutations and
[schema evolution](schema.md) when changing validation policy on populated
classes. The registered OpenAPI surface covers all 235 operations; dedicated
typed services and generic operation calls are distinguished in the API guides.

Server v0.0.18 requires an offline upgrade from v0.0.17 and emits backup format 8;
older servers cannot restore that format. Follow the canonical
[server upgrade and recovery instructions](https://hubuum.github.io/hubuum/v0.0.18/events/#upgrade-and-rollback)
and [backup compatibility](https://hubuum.github.io/hubuum/v0.0.18/backup-restore/).
Use the server guide for the actual version transition rather than copying
migration commands from an older client release.

## Verification evidence

[Detailed evidence and historical migrations](compatibility-evidence.md) retain tested
image identities, dates, suite results, and earlier compatibility limits.

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
