#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

SERVER_IMAGE="${HUBUUM_E2E_SERVER_IMAGE:-ghcr.io/hubuum/hubuum-server:v0.0.4@sha256:60142d605f423b1dc58d9dfe709164b0d5ec93befd2d702f9bdca7ee0654a583}"
POSTGRES_IMAGE="${HUBUUM_E2E_POSTGRES_IMAGE:-postgres:18}"
CONTAINER_RUNTIME="${HUBUUM_E2E_CONTAINER_RUNTIME:-}"
STARTUP_TIMEOUT="${HUBUUM_E2E_TIMEOUT:-300}"
KEEP="${HUBUUM_E2E_KEEP:-0}"
DB_USER="hubuum"
DB_PASSWORD="hubuum_password"
DB_NAME="hubuum"
PYTEST_ARGS=("$@")
E2E_TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/hubuum-python-e2e.XXXXXX")"
E2E_WHEEL_DIR="${E2E_TEMP_DIR}/dist"
E2E_VENV_DIR="${E2E_TEMP_DIR}/venv"
E2E_PYTHON=""
network_name=""
db_container=""
server_container=""

container() {
    "${CONTAINER_RUNTIME}" "$@"
}

cleanup() {
    if [[ -n "${network_name}" ]]; then
        if [[ "${KEEP}" == "1" || "${KEEP}" == "true" ]]; then
            echo "Keeping e2e resources:"
            echo "  network=${network_name}"
            echo "  database=${db_container}"
            echo "  server=${server_container}"
        else
            container rm -f "${server_container}" "${db_container}" >/dev/null 2>&1 || true
            container network rm "${network_name}" >/dev/null 2>&1 || true
        fi
    fi
    rm -rf -- "${E2E_TEMP_DIR}"
}
trap cleanup EXIT INT TERM

prepare_test_environment() {
    mkdir -p "${E2E_WHEEL_DIR}"
    echo "Building the wheel used by the e2e suite..."
    uv build --wheel --out-dir "${E2E_WHEEL_DIR}"

    wheel_paths=("${E2E_WHEEL_DIR}"/*.whl)
    if ((${#wheel_paths[@]} != 1)) || [[ ! -f "${wheel_paths[0]}" ]]; then
        echo "Expected exactly one built wheel in ${E2E_WHEEL_DIR}." >&2
        exit 1
    fi

    uv venv --python "${HUBUUM_E2E_PYTHON:-python3}" "${E2E_VENV_DIR}"
    uv pip install --python "${E2E_VENV_DIR}/bin/python" "${wheel_paths[0]}[test]"
    E2E_PYTHON="${E2E_VENV_DIR}/bin/python"
    echo "Testing installed wheel: ${wheel_paths[0]}"
}

run_e2e_tests() {
    if ((${#PYTEST_ARGS[@]})); then
        "${E2E_PYTHON}" -m pytest -m e2e tests/e2e "${PYTEST_ARGS[@]}"
    else
        "${E2E_PYTHON}" -m pytest -m e2e tests/e2e
    fi
}

prepare_test_environment

if [[ -n "${HUBUUM_E2E_BASE_URL:-}" || -n "${HUBUUM_E2E_ADMIN_PASSWORD:-}" ]]; then
    if [[ -z "${HUBUUM_E2E_BASE_URL:-}" || -z "${HUBUUM_E2E_ADMIN_PASSWORD:-}" ]]; then
        echo "HUBUUM_E2E_BASE_URL and HUBUUM_E2E_ADMIN_PASSWORD must be set together." >&2
        exit 2
    fi
    run_e2e_tests
    exit
fi

if [[ -z "${CONTAINER_RUNTIME}" ]]; then
    if command -v docker >/dev/null 2>&1; then
        CONTAINER_RUNTIME="docker"
    elif command -v podman >/dev/null 2>&1; then
        CONTAINER_RUNTIME="podman"
    else
        echo "Docker or Podman is required for end-to-end tests." >&2
        exit 2
    fi
fi

suffix="$(date +%s)-$$-${RANDOM}"
network_name="hubuum-python-e2e-net-${suffix}"
db_container="hubuum-python-e2e-db-${suffix}"
server_container="hubuum-python-e2e-server-${suffix}"

diagnostics() {
    echo "Hubuum server diagnostics:" >&2
    container logs --tail 150 "${server_container}" >&2 || true
    echo "PostgreSQL diagnostics:" >&2
    container logs --tail 80 "${db_container}" >&2 || true
}

deadline=$((SECONDS + STARTUP_TIMEOUT))

echo "Pulling pinned Hubuum server image: ${SERVER_IMAGE}"
container pull "${SERVER_IMAGE}"
container pull "${POSTGRES_IMAGE}"

container network create "${network_name}" >/dev/null
container run -d \
    --name "${db_container}" \
    --network "${network_name}" \
    --health-cmd "pg_isready -U ${DB_USER} -d ${DB_NAME}" \
    --health-interval 1s \
    --health-timeout 5s \
    --health-retries 60 \
    -e "POSTGRES_USER=${DB_USER}" \
    -e "POSTGRES_PASSWORD=${DB_PASSWORD}" \
    -e "POSTGRES_DB=${DB_NAME}" \
    "${POSTGRES_IMAGE}" >/dev/null

while ((SECONDS < deadline)); do
    if container exec "${db_container}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
if ! container exec "${db_container}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
    diagnostics
    echo "PostgreSQL did not become ready within ${STARTUP_TIMEOUT} seconds." >&2
    exit 1
fi

database_url="postgres://${DB_USER}:${DB_PASSWORD}@${db_container}/${DB_NAME}"
container run -d \
    --name "${server_container}" \
    --network "${network_name}" \
    -p "127.0.0.1::8080" \
    -e "HUBUUM_BIND_IP=0.0.0.0" \
    -e "HUBUUM_BIND_PORT=8080" \
    -e "HUBUUM_CLIENT_ALLOWLIST=*" \
    -e "HUBUUM_DATABASE_URL=${database_url}" \
    -e "HUBUUM_LOG_LEVEL=info" \
    "${SERVER_IMAGE}" >/dev/null

mapped_port="$(container port "${server_container}" 8080/tcp | awk -F: 'END {print $NF}')"
if [[ -z "${mapped_port}" ]]; then
    diagnostics
    echo "Could not resolve the mapped Hubuum port." >&2
    exit 1
fi
base_url="http://127.0.0.1:${mapped_port}"

while ((SECONDS < deadline)); do
    status="$(curl -sS -o /dev/null -w '%{http_code}' "${base_url}/readyz" || true)"
    if [[ "${status}" == "200" ]]; then
        break
    fi
    sleep 1
done
if [[ "${status:-000}" != "200" ]]; then
    diagnostics
    echo "Hubuum did not become ready within ${STARTUP_TIMEOUT} seconds." >&2
    exit 1
fi

reset_output="$(container exec "${server_container}" hubuum-admin --reset-password admin)"
admin_password="$(printf '%s\n' "${reset_output}" | sed -n 's/^Password for user admin reset to: //p' | tail -n 1)"
if [[ -z "${admin_password}" ]]; then
    diagnostics
    echo "Could not obtain the temporary administrator password." >&2
    exit 1
fi

export HUBUUM_E2E_BASE_URL="${base_url}"
export HUBUUM_E2E_ADMIN_PASSWORD="${admin_password}"

echo "Running Python e2e tests against Hubuum v0.0.4 at ${base_url}"
run_e2e_tests
