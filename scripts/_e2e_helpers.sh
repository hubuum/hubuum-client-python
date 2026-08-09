#!/usr/bin/env bash
# Shared Bash helpers for the Docker-backed end-to-end wrapper.

postgres_tcp_health_command() {
    local database_user="$1"
    local database_name="$2"

    printf 'pg_isready -h 127.0.0.1 -U %q -d %q' \
        "${database_user}" "${database_name}"
}

wait_for_healthy_container() {
    local container_name="$1"
    local deadline="$2"
    local health_status=""

    while ((SECONDS < deadline)); do
        health_status="$(
            container inspect --format '{{.State.Health.Status}}' "${container_name}" \
                2>/dev/null || true
        )"
        if [[ "${health_status}" == "healthy" ]]; then
            return 0
        fi
        sleep 1
    done
    return 1
}
