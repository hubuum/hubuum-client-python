from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASH = shutil.which("bash")


def test_e2e_wrapper_wires_tcp_postgres_health_wait() -> None:
    repository_root = Path(__file__).parents[2]
    wrapper = (repository_root / "scripts" / "run-e2e-tests.sh").read_text()

    assert 'postgres_health_command="$(postgres_tcp_health_command' in wrapper
    assert '--health-cmd "${postgres_health_command}"' in wrapper
    assert 'if ! wait_for_healthy_container "${db_container}" "${deadline}"; then' in wrapper
    assert 'container exec "${db_container}" pg_isready' not in wrapper


def _run_helper(script: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    repository_root = Path(__file__).parents[2]
    environment = os.environ.copy()
    environment.update(
        {
            "HELPER_PATH": str(repository_root / "scripts" / "_e2e_helpers.sh"),
            "STATE_FILE": str(tmp_path / "container-health-state"),
        }
    )
    return subprocess.run(
        [BASH, "-c", script],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


@pytest.mark.skipif(BASH is None, reason="Bash is required to test the e2e wrapper")
def test_postgres_health_uses_tcp_to_skip_the_temporary_socket_server(tmp_path: Path) -> None:
    result = _run_helper(
        r"""
set -euo pipefail
source "${HELPER_PATH}"
actual="$(postgres_tcp_health_command hubuum hubuum)"
expected='pg_isready -h 127.0.0.1 -U hubuum -d hubuum'
[[ "${actual}" == "${expected}" ]]
""",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(BASH is None, reason="Bash is required to test the e2e wrapper")
def test_health_wait_ignores_temporary_socket_server_and_shutdown(tmp_path: Path) -> None:
    result = _run_helper(
        r"""
set -euo pipefail
source "${HELPER_PATH}"
printf '0\n' > "${STATE_FILE}"

container() {
    local call_count
    local status
    [[ "$1" == "inspect" && "$2" == "--format" && "$4" == "postgres" ]]
    call_count="$(<"${STATE_FILE}")"
    case "${call_count}" in
        0) status="starting" ;; # Temporary server accepts socket connections.
        1) status="starting" ;; # Temporary server shuts down.
        *) status="healthy" ;;  # Final TCP server is ready.
    esac
    printf '%s\n' "$((call_count + 1))" > "${STATE_FILE}"
    printf '%s\n' "${status}"
}

sleep() {
    SECONDS=$((SECONDS + 1))
}

wait_for_healthy_container postgres "$((SECONDS + 5))"
[[ "$(<"${STATE_FILE}")" == "3" ]]
""",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(BASH is None, reason="Bash is required to test the e2e wrapper")
def test_health_wait_honors_startup_deadline(tmp_path: Path) -> None:
    result = _run_helper(
        r"""
set -euo pipefail
source "${HELPER_PATH}"
printf '0\n' > "${STATE_FILE}"

container() {
    local call_count
    call_count="$(<"${STATE_FILE}")"
    printf '%s\n' "$((call_count + 1))" > "${STATE_FILE}"
    printf 'starting\n'
}

sleep() {
    SECONDS=$((SECONDS + 1))
}

if wait_for_healthy_container postgres "$((SECONDS + 3))"; then
    exit 1
fi
[[ "$(<"${STATE_FILE}")" == "3" ]]
""",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(BASH is None, reason="Bash is required to test the e2e wrapper")
@pytest.mark.parametrize("runtime", ["docker", "podman"])
@pytest.mark.parametrize("migration_status", [0, 1])
def test_wrapper_migrates_before_server_start_and_cleans_up(
    tmp_path: Path, runtime: str, migration_status: int
) -> None:
    assert BASH is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls"
    stub = bin_dir / "stub"
    stub.write_text(
        f"#!{sys.executable}\n"
        + r"""
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(os.environ["CALL_LOG"]).open("a") as log:
    if name in {"docker", "podman"}:
        if args[0] == "run":
            role = "migration" if "--migrate" in args else "server" if "-p" in args else "database"
            log.write(f"run:{role}\n")
        elif args[0] == "rm":
            log.write("cleanup:" + " ".join(args[2:]) + "\n")
if name == "uv":
    if args[0] == "build":
        directory = Path(args[args.index("--out-dir") + 1])
        (directory / "hubuum_client-test.whl").touch()
    elif args[0] == "venv":
        python = Path(args[-1]) / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("#!/bin/sh\nexit 0\n")
        python.chmod(0o755)
elif name == "curl":
    print("200")
elif args[0] == "inspect":
    print("healthy")
elif args[0] == "port":
    print("127.0.0.1:8080")
elif args[0] == "exec":
    print("Password for user admin reset to: disposable-test-password")
elif args[0] == "run" and "--migrate" in args:
    sys.exit(int(os.environ["MIGRATION_STATUS"]))
"""
    )
    stub.chmod(0o755)
    for name in (runtime, "uv", "curl"):
        (bin_dir / name).symlink_to(stub)
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("HUBUUM_E2E_")
    }
    environment.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "HUBUUM_E2E_CONTAINER_RUNTIME": runtime,
            "CALL_LOG": str(log),
            "MIGRATION_STATUS": str(migration_status),
        }
    )
    result = subprocess.run(
        [BASH, str(Path(__file__).parents[2] / "scripts" / "run-e2e-tests.sh")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    calls = log.read_text().splitlines()
    assert result.returncode == migration_status, result.stderr
    assert calls[:2] == ["run:database", "run:migration"]
    if migration_status == 0:
        assert calls[2] == "run:server"
    else:
        assert "run:server" not in calls
        assert "migrations failed" in result.stderr
    cleanup = next(call for call in calls if call.startswith("cleanup:"))
    assert "hubuum-python-e2e-migrate-" in cleanup
    assert "hubuum-python-e2e-db-" in cleanup
    assert "hubuum-python-e2e-server-" in cleanup
