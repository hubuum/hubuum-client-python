# Contributing

Thank you for helping improve the Hubuum Python client.

## Development setup

Install [uv](https://docs.astral.sh/uv/), clone the repository, and create the
development environment:

```bash
uv sync --extra dev
```

Before opening a pull request, run the same non-container checks as CI:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run bandit -q -r src scripts
uv run zizmor .
uv run pytest --cov
uv run mkdocs build --strict
uv build
```

Changes that affect server behavior should also pass the pinned live-server
suite:

```bash
./scripts/run-e2e-tests.sh
```

## OpenAPI contract updates

The exact OpenAPI document for the supported Hubuum release is committed as
`docs/openapi.json`. The default contract check is offline and verifies the
document's SHA-256, server version, operation count, required operations, and
the complete client operation manifest:

```bash
uv run python scripts/check-openapi-contract.py
```

Use the network only when deliberately comparing with or refreshing from the
immutable upstream server revision:

```bash
uv run python scripts/check-openapi-contract.py --check-upstream
uv run python scripts/check-openapi-contract.py --update
```

Both commands validate the upstream bytes against the pinned checksum before
accepting them. `--check-upstream` leaves the worktree unchanged; `--update`
replaces `docs/openapi.json` only after the complete validation succeeds.

When targeting a future Hubuum release:

1. Select the immutable server release commit and image digest, then update the
   version, revision, checksum, operation count, and image constants in
   `src/hubuum_client/_constants.py`, the contract checker, CI, and the e2e
   wrapper.
2. Regenerate or update `src/hubuum_client/_operations.py` from that exact
   contract, including request and successful-response media types, and update
   contract-derived test cases and generated expectations.
3. Run the checker with `--update` to commit the exact upstream document, then
   run its default offline mode to detect document or manifest drift.
4. Update `README.md`, `CHANGELOG.md`, and `docs/compatibility.md` with the new
   target and compatibility evidence.
5. Run every non-container check above and the pinned live-server suite.

## Pull requests

- Keep each pull request focused and explain its user-visible effect.
- Add tests for behavior changes, including sync and async paths when they can
  diverge.
- Update documentation and the `[Unreleased]` changelog section when public
  behavior, compatibility, or requirements change.
- Do not include credentials, bearer tokens, server data, or generated build
  artifacts.

By contributing, you agree that your contribution is licensed under the
repository's MIT License.
