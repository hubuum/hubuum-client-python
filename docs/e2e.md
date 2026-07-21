# Docker-backed end-to-end tests

The e2e suite exercises the installed Python package against a real Hubuum
v0.0.3 server and PostgreSQL database. It covers public probes, login, public
configuration, typed CRUD, natural-key addressing, filtering, cursor metadata,
IAM membership, class and object relations, cleanup, and async reads.

## Canonical command

```bash
./scripts/run-e2e-tests.sh
```

The wrapper:

1. detects Docker or Podman;
2. pulls the immutable target server and PostgreSQL images;
3. creates an isolated network and uniquely named containers;
4. waits for PostgreSQL and `/readyz`;
5. resets the generated local administrator password inside the server;
6. exports the connection details and runs `tests/e2e`;
7. removes the stack even when a test fails.

Set `HUBUUM_E2E_KEEP=1` to retain the stack for diagnosis. The script prints the
exact resource names before returning.

## Caller-managed server

To run the same suite against an already running server:

```bash
HUBUUM_E2E_BASE_URL=http://127.0.0.1:8080 \
HUBUUM_E2E_ADMIN_PASSWORD=secret \
./scripts/run-e2e-tests.sh
```

Both variables are required together. This mode does not create or remove
containers.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `HUBUUM_E2E_SERVER_IMAGE` | Override the server image | Immutable v0.0.3 digest |
| `HUBUUM_E2E_POSTGRES_IMAGE` | Override PostgreSQL | `postgres:18` |
| `HUBUUM_E2E_CONTAINER_RUNTIME` | Select `docker` or `podman` | Auto-detected |
| `HUBUUM_E2E_TIMEOUT` | Stack startup deadline in seconds | `300` |
| `HUBUUM_E2E_KEEP` | Keep the provisioned stack | `0` |

An overridden or caller-managed server run is useful during development, but a
release compatibility claim requires the default immutable server image.

## Passing pytest options

Arguments are forwarded after the e2e selection:

```bash
./scripts/run-e2e-tests.sh -vv -k relations
```

Every test uses a random resource prefix. Cleanup happens in reverse dependency
order so one run does not pollute another.
