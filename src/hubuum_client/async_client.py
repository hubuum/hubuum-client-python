"""Asynchronous Hubuum client."""

from __future__ import annotations

from asyncio import Lock
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any, Self, TypeVar, overload

import httpx
from pydantic import BaseModel

from ._constants import __version__
from ._sessions import SessionState, validate_client_id
from ._transport import (
    decode_json,
    decode_model,
    json_body,
    normalize_base_url,
    prepare_request_headers,
    raise_api_error,
    redact_text,
    sensitive_request_values,
    validate_relative_path,
)
from .errors import TransportError
from .models import ClientConfig, LoginResponse, MeResponse, ProbeResponse, SessionResponse
from .options import ClientOptions, RequestOptions
from .streaming import AsyncResponseStream
from .types import AccessToken, Credentials

T = TypeVar("T", bound=BaseModel)
_PUBLIC_REQUEST = RequestOptions(authenticated=False)

if TYPE_CHECKING:
    from .api.async_services import AsyncAPI


class AsyncClient:
    """Async client with the same resource surface as :class:`Client`."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | AccessToken | None = None,
        options: ClientOptions | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        client_options = options or ClientOptions()
        self._base_url = normalize_base_url(base_url)
        self._token = AccessToken(token) if isinstance(token, str) else token
        self._session: SessionState | None = None
        self._session_lock = Lock()
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=client_options.timeout,
            verify=client_options.verify,
            transport=transport,
            headers={
                "User-Agent": client_options.user_agent or f"hubuum-client-python/{__version__}"
            },
        )

    @property
    def base_url(self) -> str:
        """Return the validated server base URL, including its trailing slash."""
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        """Return whether the client currently holds an access token."""
        return self._token is not None

    @property
    def token(self) -> AccessToken | None:
        """Return the current redacted token value, if authenticated."""
        return self._token

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP connection pool owned by this client."""
        await self._http.aclose()

    async def login(self, credentials: Credentials) -> Self:
        """Use legacy single-token login on servers providing /api/v0/auth."""
        async with self._session_lock:
            response = await self.request(
                "POST",
                "/api/v0/auth/login",
                json=credentials.as_payload(),
                response_model=LoginResponse,
                options=_PUBLIC_REQUEST,
            )
            self._session = None
            self._token = AccessToken(response.token, expires_at=response.expires_at)
        return self

    async def login_session(
        self, credentials: Credentials, *, client_id: str = "hubuum-python"
    ) -> Self:
        """Opt into rotating interactive credentials, retained only in memory.

        Requires the versioned session API. Refresh is serialized per client;
        failed or uncertain refresh destroys local credentials and is never retried.
        """
        client_id = validate_client_id(client_id)
        async with self._session_lock:
            response = await self.request(
                "POST",
                "/api/v1/auth/login",
                json={**credentials.as_payload(), "client_id": client_id},
                response_model=SessionResponse,
                options=_PUBLIC_REQUEST,
            )
            self._install_session(SessionState.receive(response, client_id))
        return self

    def _install_session(self, session: SessionState) -> None:
        self._session = session
        self._token = AccessToken(
            session.credentials.access_token.get_secret_value(),
            expires_at=session.credentials.access_expires_at,
        )

    async def _ensure_session(self) -> None:
        if self._session is None or not self._session.needs_refresh():
            return
        async with self._session_lock:
            await self._refresh_session()

    async def _refresh_session(self) -> None:
        session = self._session
        if session is None or not session.needs_refresh():
            return
        try:
            session.require_refreshable()
            response = await self.request(
                "POST",
                "/api/v1/auth/refresh",
                json={
                    "client_id": session.client_id,
                    "refresh_token": session.credentials.refresh_token.get_secret_value(),
                },
                response_model=SessionResponse,
                options=_PUBLIC_REQUEST,
            )
            self._install_session(SessionState.receive(response, session.client_id, session))
        except BaseException:
            # Cancellation/interrupt can also leave the server's rotation committed.
            self._session = None
            self._token = None
            raise

    async def logout(self) -> None:
        """Revoke the current session and clear local credentials in all cases."""
        async with self._session_lock:
            try:
                endpoint = (
                    "/api/v1/auth/logout" if self._session is not None else "/api/v0/auth/logout"
                )
                await self._refresh_session()
                # The lock is held; bypass another refresh check for this request.
                request, body = self._build_request("POST", endpoint, json=None, options=None)
                response = await self._send_request(request, body, stream=False)
                if (
                    endpoint == "/api/v0/auth/logout"
                    and response.status_code == httpx.codes.NOT_FOUND
                ):
                    request, body = self._build_request(
                        "POST", "/api/v1/auth/logout", json=None, options=None
                    )
                    response = await self._send_request(request, body, stream=False)
                raise_api_error(response)
            finally:
                self._session = None
                self._token = None

    async def healthz(self) -> ProbeResponse:
        """Return the unauthenticated process-health probe."""
        return await self.request(
            "GET", "/healthz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    async def readyz(self) -> ProbeResponse:
        """Return the unauthenticated dependency-readiness probe."""
        return await self.request(
            "GET", "/readyz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    async def config(self) -> ClientConfig:
        """Return client-safe public server configuration."""
        return await self.request(
            "GET",
            "/api/v1/config",
            response_model=ClientConfig,
            options=_PUBLIC_REQUEST,
        )

    async def metrics(self) -> str:
        """Return Prometheus exposition text from the default ``/metrics`` path."""
        return await self.metrics_at("/metrics")

    async def metrics_at(self, path: str) -> str:
        """Return unauthenticated metrics text from an origin-locked custom path."""
        response = await self._request_response("GET", path, options=_PUBLIC_REQUEST)
        return response.text

    async def me(self) -> MeResponse:
        """Return the authenticated principal and current token metadata."""
        return await self.request("GET", "/api/v1/iam/me", response_model=MeResponse)

    @cached_property
    def audit(self) -> AsyncAuditService:
        return AsyncAuditService(self)

    @cached_property
    def event_deliveries(self) -> AsyncEventDeliveriesService:
        return AsyncEventDeliveriesService(self)

    @cached_property
    def export_templates(self) -> AsyncExportTemplatesService:
        return AsyncExportTemplatesService(self)

    @cached_property
    def remote_targets(self) -> AsyncRemoteTargetsService:
        return AsyncRemoteTargetsService(self)

    @cached_property
    def computed_fields(self) -> AsyncPersonalComputedFieldsService:
        return AsyncPersonalComputedFieldsService(self)

    @cached_property
    def backups(self) -> AsyncBackupsService:
        return AsyncBackupsService(self)

    @cached_property
    def restores(self) -> AsyncRestoresService:
        return AsyncRestoresService(self)

    @cached_property
    def principals(self) -> AsyncPrincipalsService:
        return AsyncPrincipalsService(self)

    @cached_property
    def auth(self) -> AsyncAuthService:
        return AsyncAuthService(self)

    @cached_property
    def admin(self) -> AsyncAdminService:
        return AsyncAdminService(self)

    @cached_property
    def event_sinks(self) -> AsyncEventSinksService:
        """Administrator sink management and explicit collection grants."""
        return AsyncEventSinksService(self)

    @cached_property
    def collections(self) -> AsyncCollectionsService:
        """Return typed collection CRUD and hierarchy operations."""
        return AsyncCollectionsService(self)

    @cached_property
    def classes(self) -> AsyncClassesService:
        """Return typed class and nested-object operations."""
        return AsyncClassesService(self)

    @cached_property
    def users(self) -> AsyncUsersService:
        """Return typed user lifecycle operations."""
        return AsyncUsersService(self)

    @cached_property
    def service_accounts(self) -> AsyncServiceAccountsService:
        """Return typed service-account lifecycle and pagination operations."""
        return AsyncServiceAccountsService(self)

    @cached_property
    def groups(self) -> AsyncGroupsService:
        """Return typed group and membership operations."""
        return AsyncGroupsService(self)

    @cached_property
    def credential_approvals(self) -> AsyncCredentialApprovalsService:
        """Return operation-bound password approval and evidence operations."""
        return AsyncCredentialApprovalsService(self)

    @cached_property
    def tokens(self) -> AsyncTokensService:
        """Return typed principal-token operations."""
        return AsyncTokensService(self)

    @cached_property
    def class_relations(self) -> AsyncClassRelationsService:
        """Return typed class-relation operations."""
        return AsyncClassRelationsService(self)

    @cached_property
    def object_relations(self) -> AsyncObjectRelationsService:
        """Return typed object-relation operations."""
        return AsyncObjectRelationsService(self)

    @cached_property
    def tasks(self) -> AsyncTasksService:
        """Return task inspection, event, pagination, and polling operations."""
        return AsyncTasksService(self)

    @cached_property
    def imports(self) -> AsyncImportsService:
        """Return typed asynchronous-import operations."""
        return AsyncImportsService(self)

    @cached_property
    def exports(self) -> AsyncExportsService:
        """Return typed asynchronous-export and output operations."""
        return AsyncExportsService(self)

    @property
    def openapi(self) -> AsyncOpenAPIOperations:
        """Return the complete operation-ID interface for all 261 v0.0.21 operations."""
        return AsyncOpenAPIOperations(self)

    @cached_property
    def api(self) -> AsyncAPI:
        """Fully typed resource operations for the complete server contract."""
        from .api.async_services import AsyncAPI  # noqa: PLC0415 -- Load full schema on demand.

        return AsyncAPI(self)

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        response_model: type[T],
        options: RequestOptions | None = None,
    ) -> T: ...

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        response_model: None = None,
        options: RequestOptions | None = None,
    ) -> Any: ...

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        response_model: type[T] | None = None,
        options: RequestOptions | None = None,
    ) -> T | Any:
        """Send an authenticated, origin-locked request to a relative API path.

        Supply ``response_model`` to validate a JSON response. Prefer a typed
        resource service when one exists; this method is the constrained
        extension point for server routes outside that surface.
        """
        response = await self._request_response(
            method,
            path,
            json=json,
            options=options,
        )
        return (
            decode_model(response, response_model)
            if response_model is not None
            else decode_json(response)
        )

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncIterator[AsyncResponseStream]:
        """Stream one origin-locked response without exposing request secrets."""
        response = await self._request_stream_response(method, path, json=json, options=options)
        try:
            yield AsyncResponseStream(response)
        finally:
            await response.aclose()

    def _build_request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None,
        options: RequestOptions | None,
    ) -> tuple[httpx.Request, Any]:
        request_options = options or RequestOptions()
        relative_path = validate_relative_path(path)
        bearer_token = (
            self._token.value if request_options.authenticated and self._token is not None else None
        )
        request_headers = prepare_request_headers(request_options.headers, bearer_token)
        request_body = json_body(json)
        request = self._http.build_request(
            method.upper(),
            relative_path,
            params=request_options.params,
            json=request_body,
            headers=request_headers,
        )
        return request, request_body

    async def _send_request(
        self,
        request: httpx.Request,
        request_body: Any,
        *,
        stream: bool,
    ) -> httpx.Response:
        try:
            return await self._http.send(request, stream=stream)
        except httpx.HTTPError as error:
            secrets = sensitive_request_values(
                request.headers,
                request_body,
                request.url.params,
            )
            transport_error = TransportError(
                request.method,
                str(request.url.copy_with(query=None, fragment=None)),
                redact_text(str(error), secrets),
            )
        # Do not chain an HTTPX exception retaining secret-bearing requests.
        raise transport_error

    async def _request_response(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> httpx.Response:
        if options is None or options.authenticated:
            await self._ensure_session()
        request, request_body = self._build_request(
            method,
            path,
            json=json,
            options=options,
        )
        response = await self._send_request(request, request_body, stream=False)
        raise_api_error(response)
        return response

    async def _request_stream_response(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> httpx.Response:
        if options is None or options.authenticated:
            await self._ensure_session()
        request, request_body = self._build_request(
            method,
            path,
            json=json,
            options=options,
        )
        response = await self._send_request(request, request_body, stream=True)
        if not response.is_success:
            await response.aread()
            try:
                raise_api_error(response)
            finally:
                await response.aclose()
        return response


from .async_services import (  # noqa: E402 -- Services reference the client type.
    AsyncAdminService,
    AsyncAuditService,
    AsyncAuthService,
    AsyncBackupsService,
    AsyncClassesService,
    AsyncClassRelationsService,
    AsyncCollectionsService,
    AsyncCredentialApprovalsService,
    AsyncEventDeliveriesService,
    AsyncEventSinksService,
    AsyncExportsService,
    AsyncExportTemplatesService,
    AsyncGroupsService,
    AsyncImportsService,
    AsyncObjectRelationsService,
    AsyncPersonalComputedFieldsService,
    AsyncPrincipalsService,
    AsyncRemoteTargetsService,
    AsyncRestoresService,
    AsyncServiceAccountsService,
    AsyncTasksService,
    AsyncTokensService,
    AsyncUsersService,
)
from .openapi import AsyncOpenAPIOperations  # noqa: E402
