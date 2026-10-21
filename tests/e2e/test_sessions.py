"""Opt-in checks for a caller-managed server implementing hubuum/hubuum#178."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from hubuum_client import AsyncClient, AuthenticationError, Client, Credentials, RequestOptions

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("HUBUUM_E2E_SESSION_API") != "1",
        reason="rotating sessions require the versioned session API",
    ),
]


def test_live_session_rotation_and_replay(base_url: str, admin_password: str) -> None:
    with Client(base_url) as client:
        client.login_session(Credentials("admin", admin_password), client_id="python-live-session")
        session = client._session
        assert session is not None
        client._session = replace(session, refresh_at=0)
        assert client.me().principal.name == "admin"
        assert client._session is not None
        assert client._session.credentials.session_id == session.credentials.session_id
        assert client._session.credentials.refresh_token != session.credentials.refresh_token
        with pytest.raises(AuthenticationError):
            client.request(
                "POST",
                "/api/v1/auth/refresh",
                json={
                    "client_id": session.client_id,
                    "refresh_token": session.credentials.refresh_token.get_secret_value(),
                },
                options=RequestOptions(authenticated=False),
            )
        with pytest.raises(AuthenticationError):
            client.me()


async def test_live_async_session_logout(base_url: str, admin_password: str) -> None:
    async with AsyncClient(base_url) as client:
        await client.login_session(Credentials("admin", admin_password))
        session = client._session
        assert session is not None
        client._session = replace(session, refresh_at=0)
        assert (await client.me()).principal.name == "admin"
        await client.logout()
        assert not client.is_authenticated
