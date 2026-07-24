# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed

- Raised the branch-aware unit coverage gate from 90% to 95% after adding
  request-construction coverage for every pinned OpenAPI operation and focused
  transport, streaming, decoding, pagination, and sync/async failure tests.
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

### Security

- Hardened origin-locked requests against nested URL traversal, ambiguous path
  characters, and caller-supplied `Host` headers.
- Made bearer-header replacement case-insensitive and redact request secrets
  from transport, API, and decoding exception details.
- Redacted login tokens from model representations.

[Unreleased]: https://github.com/hubuum/hubuum-client-python/commits/main
