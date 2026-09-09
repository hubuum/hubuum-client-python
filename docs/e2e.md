# Docker-backed end-to-end tests

The e2e suite builds the project wheel, installs that artifact into an isolated
virtual environment, and exercises the installed distribution against a real
Hubuum v0.0.13 server and PostgreSQL database. It covers public probes, login,
public configuration, typed CRUD, natural-key addressing, forced multi-page
cursor traversal and metadata, typed nested object-data filters (including
scalar, numeric, array, structure, null, combined, and network cases),
natural-key object listing and atomic object-data JSON Patch, IAM membership,
class and object relations, non-administrator permission boundaries, live
`400`, `401`, `403`, `404`, `409`, and `412` errors, successful and stale
`If-Match` updates and deletes in both runtimes, principal-settings JSON Patch,
scoped-token mint/list/inspect/renew/use/revoke lifecycles in both runtimes,
v0.0.13 relation cardinality enforcement, import-v2 timestamp restoration,
export phase timings and task events, cleanup, and a complete async
create/query/update/patch/delete lifecycle. Structured JSON and SSE searches
are also checked in both runtimes.

After the core suite passes, the wrapper starts the matching restore executor
and runs `tests/recovery` against the same disposable database. Two tests run
four consecutive backup/restore cycles in both sync/async orders without
restarting either process. They verify version 5 backups with history, restored
object data and revisions (including JSON `null`), removal of later objects,
capability-only status polling, old-token rejection, and password-reset/login
recovery. These are regression checks for the restore fixes in v0.0.13.

## Canonical command

```bash
./scripts/run-e2e-tests.sh
```

The wrapper:

1. builds the wheel and installs its `test` extra into a temporary virtual
   environment;
2. detects Docker or Podman;
3. pulls the immutable target server and PostgreSQL images;
4. creates an isolated network and uniquely named containers;
5. waits for PostgreSQL, runs `hubuum-admin --migrate` in a separate
   container, then starts Hubuum and waits for `/readyz`;
6. resets the generated local administrator password inside the server;
7. exports the connection details and runs `tests/e2e` with the isolated
   interpreter;
8. starts `hubuum-admin --restore-executor` from the same pinned image and runs
   the repeated full-restore suite in `tests/recovery`;
9. removes the executor, server, migration and database containers, network, and
   temporary test environment even when a test fails.

PostgreSQL readiness uses `pg_isready` over TCP at `127.0.0.1` and polls that
container health state through the configured startup deadline. The temporary
server used by the official image during database initialization accepts only
Unix-socket connections, so it cannot be mistaken for the final TCP server.

Set `HUBUUM_E2E_KEEP=1` to retain the stack for diagnosis. The script prints the
exact resource names before returning. The temporary wheel environment is
always removed. The migration container is included in diagnostics and cleanup;
a failed migration stops the wrapper before the server starts.

## Caller-managed server

To run the same suite against an already running server:

```bash
HUBUUM_E2E_BASE_URL=http://127.0.0.1:8080 \
HUBUUM_E2E_ADMIN_PASSWORD=secret \
./scripts/run-e2e-tests.sh
```

Both variables are required together. This mode still builds and installs the
wheel, but it does not create or remove containers or run full restores. The
recovery suite is restricted to the wrapper-owned disposable stack; its fixture
also checks the generated container name and matching local mapped URL.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `HUBUUM_E2E_SERVER_IMAGE` | Override the server image | Immutable v0.0.13 tag and digest |
| `HUBUUM_E2E_POSTGRES_IMAGE` | Override PostgreSQL | `postgres:18` |
| `HUBUUM_E2E_CONTAINER_RUNTIME` | Select `docker` or `podman` | Auto-detected |
| `HUBUUM_E2E_PYTHON` | Interpreter used for the isolated wheel environment | `python3` |
| `HUBUUM_E2E_TIMEOUT` | Stack startup deadline in seconds | `300` |
| `HUBUUM_E2E_KEEP` | Keep the provisioned stack | `0` |

An overridden or caller-managed server run is useful during development, but a
release compatibility claim requires the default server tag and immutable
digest recorded in the compatibility matrix.

## Passing pytest options

Arguments are forwarded to the core `tests/e2e` selection:

```bash
./scripts/run-e2e-tests.sh -vv -k relations
```

For a provisioned disposable stack, the complete recovery suite still runs
after the selected core tests pass. Every test uses a random resource prefix.
The core suite cleans up resources in reverse dependency order; recovery
resources are removed with the disposable database when the wrapper exits.
