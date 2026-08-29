from __future__ import annotations

import os
import shutil
import subprocess
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
