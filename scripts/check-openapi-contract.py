#!/usr/bin/env python3
"""Validate the immutable Hubuum v0.0.3 OpenAPI source used by this client."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

TARGET_URL = "https://raw.githubusercontent.com/hubuum/hubuum/v0.0.3/docs/openapi.json"
TARGET_SHA256 = "3f072aa40ed8a2cb94987a5e35c91b64236fdbbd770100baeaa6057990ef6a10"
TARGET_VERSION = "0.0.3"
TARGET_OPERATION_COUNT = 196
MAX_SOURCE_BYTES = 10 * 1024 * 1024
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}
REQUIRED_OPERATIONS = {
    ("post", "/api/v0/auth/login"),
    ("get", "/api/v1/config"),
    ("get", "/api/v1/collections"),
    ("post", "/api/v1/collections"),
    ("get", "/api/v1/classes"),
    ("post", "/api/v1/classes/{class_id}/"),
    ("get", "/api/v1/classes/by-name/{class_name}"),
    ("get", "/api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}"),
    ("get", "/api/v1/iam/users"),
    ("get", "/api/v1/iam/groups"),
    ("get", "/api/v1/relations/classes"),
    ("get", "/api/v1/relations/objects"),
    ("get", "/api/v1/tasks/{task_id}"),
    ("get", "/healthz"),
    ("get", "/readyz"),
}


def _read_source(source: str) -> bytes:
    path = Path(source)
    if path.is_file():
        return path.read_bytes()

    parsed = urlsplit(source)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("source must be an existing local file or an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("source URL must not contain credentials")

    request = urllib.request.Request(source, headers={"User-Agent": "hubuum-client-python"})
    # The requested and final schemes are constrained immediately around this call.
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        final_url = urlsplit(response.geturl())
        if final_url.scheme != "https" or not final_url.netloc:
            raise ValueError("source URL redirected outside HTTPS")
        payload = response.read(MAX_SOURCE_BYTES + 1)
    if len(payload) > MAX_SOURCE_BYTES:
        raise ValueError(f"OpenAPI source exceeds {MAX_SOURCE_BYTES} bytes")
    return payload


def _operations(document: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        result.update((method, path) for method in path_item if method in HTTP_METHODS)
    return result


def validate(source: str) -> None:
    payload = _read_source(source)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != TARGET_SHA256:
        raise ValueError(f"OpenAPI SHA-256 mismatch: expected {TARGET_SHA256}, received {digest}")

    document = json.loads(payload)
    version = document.get("info", {}).get("version")
    if version != TARGET_VERSION:
        raise ValueError(f"OpenAPI version mismatch: expected {TARGET_VERSION}, received {version}")

    operations = _operations(document)
    if len(operations) != TARGET_OPERATION_COUNT:
        raise ValueError(
            f"OpenAPI operation count mismatch: expected {TARGET_OPERATION_COUNT}, "
            f"received {len(operations)}"
        )
    missing = REQUIRED_OPERATIONS - operations
    if missing:
        formatted = ", ".join(f"{method.upper()} {path}" for method, path in sorted(missing))
        raise ValueError(f"OpenAPI is missing required client operations: {formatted}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        nargs="?",
        default=TARGET_URL,
        help="OpenAPI file or URL; defaults to the authoritative v0.0.3 tag",
    )
    args = parser.parse_args()
    try:
        validate(args.source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"OpenAPI contract validation failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Validated Hubuum {TARGET_VERSION} OpenAPI contract "
        f"({TARGET_OPERATION_COUNT} operations, sha256={TARGET_SHA256})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
