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
