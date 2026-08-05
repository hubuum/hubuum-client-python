#!/usr/bin/env python3
"""Validate the immutable Hubuum v0.0.8 OpenAPI source."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

TARGET_REVISION = "9de161ff05f563302cfe6f74b04b80c1f617f5d6"
TARGET_URL = f"https://raw.githubusercontent.com/hubuum/hubuum/{TARGET_REVISION}/docs/openapi.json"
TARGET_SHA256 = "15329801b66af891b18f231d8faa81daf0c6ca12e0e581632e10e9ba3b88295a"
TARGET_VERSION = "0.0.8"
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
CLIENT_MANIFEST = Path(__file__).parents[1] / "src" / "hubuum_client" / "_operations.py"


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


def _operation_manifest(
    document: dict[str, Any],
) -> dict[str, tuple[str, str, str | None, tuple[str, ...]]]:
    result: dict[str, tuple[str, str, str | None, tuple[str, ...]]] = {}
    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError(f"{method.upper()} {path} has no operationId")
            content = operation.get("requestBody", {}).get("content", {})
            media_types = sorted(content) if isinstance(content, dict) else []
            if len(media_types) > 1:
                raise ValueError(f"{operation_id} has multiple request media types")
            response_media_types: set[str] = set()
            for status, response in operation.get("responses", {}).items():
                if not str(status).startswith("2") or not isinstance(response, dict):
                    continue
                response_content = response.get("content", {})
                if isinstance(response_content, dict):
                    response_media_types.update(response_content)
            result[operation_id] = (
                method.upper(),
                path,
                media_types[0] if media_types else None,
                tuple(sorted(response_media_types)),
            )
    return result


def _client_manifest() -> dict[str, tuple[str, str, str | None, tuple[str, ...]]]:
    spec = importlib.util.spec_from_file_location("_hubuum_client_operations", CLIENT_MANIFEST)
    if spec is None or spec.loader is None:
        raise ValueError("could not load the client operation manifest")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return {
        operation_id: (
            item.method,
            item.path,
            item.request_media_type,
            item.response_media_types,
        )
        for operation_id, item in module.OPERATIONS.items()
    }


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

    server_manifest = _operation_manifest(document)
    client_manifest = _client_manifest()
    if client_manifest != server_manifest:
        missing_ids = sorted(server_manifest.keys() - client_manifest.keys())
        extra_ids = sorted(client_manifest.keys() - server_manifest.keys())
        changed_ids = sorted(
            operation_id
            for operation_id in server_manifest.keys() & client_manifest.keys()
            if server_manifest[operation_id] != client_manifest[operation_id]
        )
        raise ValueError(
            "client operation manifest mismatch: "
            f"missing={missing_ids}, extra={extra_ids}, changed={changed_ids}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        nargs="?",
        default=TARGET_URL,
        help="OpenAPI file or URL; defaults to the immutable v0.0.8 release commit",
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
