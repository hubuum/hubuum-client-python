# Releasing

The release workflow builds and publishes distributions when a matching
`vX.Y.Z` tag is pushed. A manual workflow run builds and validates the
distributions without publishing them.

## One-time PyPI setup

1. Create or claim the `hubuum-client` project on PyPI.
2. Add a GitHub Actions trusted publisher for:
   - owner: `hubuum`
   - repository: `hubuum-client-python`
   - workflow: `release.yml`
   - environment: `pypi`
3. Run `scripts/configure-github-repository.sh` with an authenticated GitHub
   CLI session. The script:
   - creates a `pypi` environment with the authenticated user as its required
     reviewer;
   - allows that reviewer to approve their own deployment, so a
     single-maintainer project is not deadlocked;
   - restricts the environment to `v*` tags;
   - protects `v*` tags so only that reviewer can create, update, or delete
     them; and
   - sets the repository variable `PYPI_PUBLISH_ENABLED` to `true`.

The workflow requests `id-token: write` only for the publishing job and does
not require a stored PyPI password or API token.

## Repository baseline

Repository metadata, merge behavior, dependency security updates, Actions token
permissions, and `main` branch protection are codified in
`scripts/configure-github-repository.sh`. Maintainers can rerun the idempotent
script with an authenticated GitHub CLI session after changing the baseline.

## Release process

1. Choose the version and update it in `pyproject.toml` and
   `src/hubuum_client/_constants.py`.
2. Move relevant changelog entries from `[Unreleased]` into a dated version
   section and update its comparison links.
3. Run every check in
   [CONTRIBUTING.md](https://github.com/hubuum/hubuum-client-python/blob/main/CONTRIBUTING.md),
   including the pinned-server e2e suite.
4. Commit the release changes, merge them to `main`, and wait for `main` CI to
   pass.
5. Create an annotated `vX.Y.Z` tag on that commit and push the tag.
6. Approve the waiting `pypi` environment deployment. The release workflow
   publishes the distributions through PyPI trusted publishing.
7. Optionally publish a GitHub release from the tag after the PyPI job
   succeeds.

The workflow verifies that the pushed tag equals `v` followed by the package
version before it builds or publishes distributions. PyPI releases cannot be
replaced, so never move or reuse a release tag after its workflow begins.
