# Repository Guidelines

These instructions apply to the entire repository.

## Sources of truth

- `pyproject.toml` defines the package version, supported Python versions,
  dependencies, and verification configuration.
- `src/hubuum_client/_constants.py` defines the target Hubuum server version and
  immutable test image. Keep those values synchronized with `README.md`,
  `CHANGELOG.md`, `docs/compatibility.md`, the e2e script, and CI.
- Hubuum server `v0.0.9` and its committed `docs/openapi.json` are the
  authoritative API contract. Do not infer wire fields from Python naming
  preferences when the contract says otherwise.
- Maintain sync/async capability parity unless a runtime constraint is
  documented explicitly.

## Architecture

- Put response and request types in `models.py`, small ID and secret values in
  `types.py`, and immutable list controls in `query.py`.
- Keep shared URL validation, decoding, and error mapping in `_transport.py`.
- Synchronous HTTP behavior belongs in `client.py` and `services.py`; matching
  asynchronous behavior belongs in `async_client.py` and `async_services.py`.
- Typed resource services are the preferred public API. Keep `request()` as a
  constrained extension point for authenticated relative routes.
- Never retain or expose bearer tokens, passwords, authorization headers, or
  secret-bearing request bodies in exceptions, representations, or logs.

## Verification

Run all non-container checks before considering a change complete:

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run bandit -q -r src scripts
uv run zizmor .
uv run pytest --cov
uv run mkdocs build --strict
uv build
```

Focused tests are useful while iterating but do not replace the full unit suite.
Every behavior change needs regression coverage for both sync and async paths
when they could diverge.

## Release readiness

- Never prepare or push a release tag while a Dependabot pull request is open.
- Before release version changes, inspect every open Dependabot pull request,
  merge or explicitly supersede each update, run `uv lock --upgrade`, and
  review the resulting application, development, documentation, and workflow
  dependency changes.
- Wait for dependency changes to pass `main` CI, then confirm the Dependabot
  queue is empty with
  `gh pr list --state open --author app/dependabot --json number,title,url`.
  Repeat that check immediately before creating the release tag.
- The release workflow must retain its tag-time Dependabot gate. Do not bypass
  or remove the gate to publish a release.

## Docker-backed end-to-end tests

Run the complete live-server suite with:

```bash
./scripts/run-e2e-tests.sh
```

The wrapper starts PostgreSQL and the immutable Hubuum v0.0.9 server image,
waits for readiness, obtains the generated administrator password, runs the
tests under `tests/e2e`, and removes its containers and network. Docker and
Podman are both supported.

Useful environment variables:

- `HUBUUM_E2E_SERVER_IMAGE`: server image override; compatibility evidence must
  use the pinned default.
- `HUBUUM_E2E_POSTGRES_IMAGE`: PostgreSQL image override.
- `HUBUUM_E2E_BASE_URL` and `HUBUUM_E2E_ADMIN_PASSWORD`: run against a
  caller-managed server instead of provisioning containers.
- `HUBUUM_E2E_CONTAINER_RUNTIME`: select `docker` or `podman`.
- `HUBUUM_E2E_KEEP=1`: retain resources for diagnosis.
- `HUBUUM_E2E_TIMEOUT`: stack startup timeout in seconds.

Live tests must use unique resource names, avoid assumptions about global IDs,
and clean up resources when doing so does not hide the primary failure. Do not
describe unit tests or an unpinned live run as v0.0.9 compatibility evidence.

## Change discipline

- Preserve unrelated user changes and keep the worktree scoped.
- Add user-visible changes to `[Unreleased]` in `CHANGELOG.md`.
- Update documentation when public behavior, requirements, compatibility, or
  the e2e workflow changes.
- Prefer clear, idiomatic Python and explicit types over clever abstractions.
- Do not suppress Ruff or mypy broadly; fix the type or isolate a justified,
  narrow exception.
