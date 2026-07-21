# Releasing

The release workflow builds distributions for every published GitHub release.
PyPI upload is deliberately disabled until trusted publishing is configured.

## One-time PyPI setup

1. Create or claim the `hubuum-client` project on PyPI.
2. Add a GitHub Actions trusted publisher for:
   - owner: `hubuum`
   - repository: `hubuum-client-python`
   - workflow: `release.yml`
   - environment: `pypi`
3. Create a GitHub environment named `pypi` and protect it with required
   reviewers.
4. Add the repository variable `PYPI_PUBLISH_ENABLED` with the value `true`.

The workflow requests `id-token: write` only for the publishing job and does
not require a stored PyPI password or API token.

## Release process

1. Choose the version and update it in `pyproject.toml` and
   `src/hubuum_client/_constants.py`.
2. Move relevant changelog entries from `[Unreleased]` into a dated version
   section and update its comparison links.
3. Run every check in
   [CONTRIBUTING.md](https://github.com/hubuum/hubuum-client-python/blob/main/CONTRIBUTING.md),
   including the pinned-server e2e suite.
4. Commit the release changes and create an annotated `vX.Y.Z` tag.
5. Push the commit and tag, then publish a GitHub release from that tag.

The workflow verifies that the GitHub release tag equals `v` followed by the
package version before it builds or publishes distributions.
