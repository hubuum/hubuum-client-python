# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3] - 2026-07-26

### Added

- Added typed public client configuration models exposing Hubuum v0.0.5's
  `authentication.default_token_lifetime_hours` alongside the effective
  pagination settings, with matching synchronous and asynchronous access.
- Access tokens returned by login and token-mint services now retain the
  server's authoritative `expires_at` value without weakening secret
  redaction.

### Changed

- Updated the declared server target, immutable OpenAPI contract, complete
  operation manifest, CI, and Docker-backed suite to Hubuum v0.0.5 at release
  commit `31fa25feaf366fb3077d5c4fd0c154275ee4bf16` and the pinned multi-platform
  image digest.

## [0.0.2] - 2026-07-26

### Added

- Added matching synchronous and asynchronous token services for listing
  visible token metadata and minting or revoking principal tokens with Hubuum
  v0.0.4's nested `scope.permissions` and `scope.resources` request shape.
- Added typed token scope, token metadata, and multi-measure object aggregate
  models, including resource scope kinds and aggregate value states.

### Changed

- Prepared the complete 196-operation interface against the immutable OpenAPI
  document from the Hubuum v0.0.4 release commit
  `81ca7b575ce888415c97dd19c83bfddaca272b6e`.
- Switched the declared server target and complete live suite to the immutable
  v0.0.4 image index digest, with synchronous and asynchronous nested-scope
  token lifecycle coverage for minting, metadata, authorization, and
  revocation.
- Object aggregate services now decode v0.0.4 dimension and measure results
  into typed response models.

### Security

- Reject empty or oversized `Idempotency-Key` request headers before I/O,
  matching Hubuum v0.0.4's 1-to-255-byte bound for task submissions.
- Replaced the yanked zizmor 1.27.0 development lock with 1.28.0 before
  release verification.

## [0.0.1] - 2026-07-25

### Added

- Initial typed Python client targeting Hubuum server v0.0.3.
- Synchronous and asynchronous clients with equivalent resource services.
- Typed Pydantic models and distinct ID types for core Hubuum resources.
- Collection, class, object, user, group, relation, and task workflows.
- Immutable filtering, cursor pages, bounded automatic pagination, and task polling.
- Structured transport, decoding, authentication, permission, not-found,
  conflict, and rate-limit exceptions.
- Redacted credentials and access tokens plus origin-locked raw requests.
- Unit, typing, documentation, and Docker-backed e2e test infrastructure.
- GitHub CI, dependency update automation, contribution guidance, and an
  explicitly gated PyPI trusted-publishing workflow.
- Added an immutable fluent interface for nested object `data` filtering,
  covering scalar, range, array, object-key, null, and IP/network operators,
  with pinned-server end-to-end coverage.
- Added a contract-checked operation interface covering all 196 Hubuum v0.0.3
  OpenAPI endpoints, including authenticated/public policy, JSON/text/binary
  response decoding, and incremental SSE consumption.
- Added the complete class/object `by-name` surface and validated atomic RFC
  6902 object-data patch operations, covering the API workflows used by
  `hubuum-import-miami`.
- Added `classes.by_id(id)` as the numeric counterpart to `classes.by_name(name)`,
  with synchronous and asynchronous class operations and nested `.objects`
  access.

### Changed

- Raised the branch-aware unit coverage gate from 90% to 95% after adding
  request-construction coverage for every pinned OpenAPI operation and focused
  transport, streaming, decoding, pagination, and sync/async failure tests.
- Strengthened pinned-server compatibility evidence with forced multi-page
  cursor traversal, a complete async resource lifecycle, non-administrator
  permission boundaries, and live `400`, `401`, `403`, `404`, and `409` error
  mapping; the e2e wrapper now tests the built wheel in an isolated environment.
- Changed PyPI trusted publishing to run from protected `v*` tag pushes, with a
  manually approved GitHub environment and an exact package-version check.
- Added an evidence-linked client/server compatibility matrix and identified
  the pinned e2e server image by both its `v0.0.3` tag and immutable digest.
- Updated every GitHub Action to its latest immutable release commit and
  corrected invalid checkout and Python setup action versions; release artifact
  validation now uses an explicit Twine version.
- Disabled persisted checkout credentials and release-job caching, added a
  dependency update cooldown, bounded contract downloads to HTTPS sources, and
  added Bandit and zizmor security gates to CI.
- Aligned synchronous and asynchronous task polling on the same
  `timeout_seconds` keyword, validated polling and pagination bounds before
  doing work, and prevented poll sleeps from exceeding the remaining timeout.
- Fixed the end-to-end wrapper on Bash 3.2 when invoked without additional
  pytest arguments.
- Replaced long client and raw-request parameter lists with shared typed
  `ClientOptions` and `RequestOptions` values and re-enabled Ruff's argument
  count rule.
- Updated examples to prefer explicit nested class selectors and documented
  application-lifetime client reuse, HTTP connection pooling, and shutdown.
- Returned group memberships as contract-validated `PrincipalMember` values
  and added cursor-aware membership page and collection helpers.
- Parsed both standard `Retry-After` forms into safe, non-negative rate-limit
  delays and ignored malformed or non-finite values.
- Cached lazily created resource-service accessors per client while keeping
  class-scoped object services on demand.

### Security

- Hardened origin-locked requests against nested URL traversal, ambiguous path
  characters, and caller-supplied `Host` headers.
- Made bearer-header replacement case-insensitive and redact request secrets
  from transport, API, and decoding exception details.
- Redacted values under sensitive query parameter names from API and transport
  error diagnostics.
- Redacted login tokens from model representations.

[Unreleased]: https://github.com/hubuum/hubuum-client-python/compare/v0.0.3...HEAD
[0.0.3]: https://github.com/hubuum/hubuum-client-python/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/hubuum/hubuum-client-python/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/hubuum/hubuum-client-python/releases/tag/v0.0.1
