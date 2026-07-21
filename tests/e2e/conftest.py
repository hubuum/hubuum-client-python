from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

from hubuum_client import Client, Credentials, GroupId


@pytest.fixture(scope="session")
def base_url() -> str:
    value = os.environ.get("HUBUUM_E2E_BASE_URL")
    if not value:
        pytest.fail("HUBUUM_E2E_BASE_URL must be set; use ./scripts/run-e2e-tests.sh")
    return value


@pytest.fixture(scope="session")
def admin_password() -> str:
    value = os.environ.get("HUBUUM_E2E_ADMIN_PASSWORD")
    if not value:
        pytest.fail("HUBUUM_E2E_ADMIN_PASSWORD must be set; use ./scripts/run-e2e-tests.sh")
    return value


@pytest.fixture
def client(base_url: str, admin_password: str) -> Iterator[Client]:
    with Client(base_url) as value:
        value.login(Credentials("admin", admin_password))
        yield value


@pytest.fixture
def admin_group_id(client: Client) -> GroupId:
    return client.groups.get_by_name("admin").id


@pytest.fixture
def unique_name() -> str:
    return f"python-e2e-{uuid.uuid4().hex[:16]}"
