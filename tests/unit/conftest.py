from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def collection_json() -> dict[str, Any]:
    return {
        "id": 11,
        "name": "inventory",
        "description": "Inventory collection",
        "parent_collection_id": None,
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
        "revision": 1,
    }


@pytest.fixture
def class_json() -> dict[str, Any]:
    return {
        "id": 12,
        "name": "server",
        "collection_id": 11,
        "validate_schema": False,
        "description": "Server class",
        "json_schema": None,
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
        "revision": 1,
    }


@pytest.fixture
def object_json() -> dict[str, Any]:
    return {
        "id": 13,
        "name": "web-01",
        "collection_id": 11,
        "hubuum_class_id": 12,
        "data": {"address": "192.0.2.10"},
        "description": "Web server",
        "created_at": "2026-07-21T10:00:00Z",
        "updated_at": "2026-07-21T10:00:00Z",
        "revision": 1,
    }
