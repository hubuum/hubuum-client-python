# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] - 2026-07-21

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

[Unreleased]: https://github.com/hubuum/hubuum-client-python/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/hubuum/hubuum-client-python/releases/tag/v0.0.1
