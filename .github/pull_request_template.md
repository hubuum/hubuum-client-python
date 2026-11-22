<!-- markdownlint-disable MD041 -->

## Summary

<!-- What changed, and why? -->

## User impact

<!-- Describe public API, compatibility, security, or operational impact. -->

## Validation

- [ ] Ruff formatting and linting
- [ ] mypy
- [ ] Unit tests with coverage
- [ ] Strict documentation build
- [ ] Package build
- [ ] Pinned-server e2e tests, when server behavior is affected

## Checklist

- [ ] Tests cover the change, including sync/async parity where relevant
- [ ] Documentation is updated
- [ ] `[Unreleased]` in `CHANGELOG.md` is updated for user-visible changes
- [ ] No credentials, tokens, production data, or generated artifacts are included

## Authentication project prerequisite gate

For Project #6 work, follow [CONTRIBUTING.md](../CONTRIBUTING.md).

- [ ] Implementing issue: <!-- full issue URL; identify setup/preparation-only work -->
- [ ] Target is `project/auth-support`; current `main` has been merged as needed
- [ ] Native strict blockers were inspected across repositories and are completed
- [ ] Accepted contract commits and candidate artifact IDs/digests are recorded
- [ ] No not-planned closure is counted as delivered work
- [ ] Selected correctness, integration and affected production container checks pass

The blocker/acceptance checks require reviewer verification; native dependencies
are not automatic merge enforcement. Mark inapplicable items explicitly for
independent setup, planning or fixture work.
