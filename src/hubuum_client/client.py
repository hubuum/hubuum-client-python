"""Synchronous Hubuum client."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from functools import cached_property
from threading import Lock
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
from .streaming import ResponseStream
from .types import AccessToken, Credentials

T = TypeVar("T", bound=BaseModel)
_PUBLIC_REQUEST = RequestOptions(authenticated=False)

if TYPE_CHECKING:
    from .api.services import API


class Client:
    """Blocking client for the Hubuum server API.

    Use the client as a context manager so its connection pool is closed
    deterministically. ``request`` is the safe extension point for routes that
    do not yet have a dedicated service method.
    """

    def __init__(
        self,
        base_url: str,
        *,
        token: str | AccessToken | None = None,
        options: ClientOptions | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        client_options = options or ClientOptions()
        self._base_url = normalize_base_url(base_url)
        self._token = AccessToken(token) if isinstance(token, str) else token
        self._session: SessionState | None = None
        self._session_lock = Lock()
        self._http = httpx.Client(
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

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP connection pool owned by this client."""
        self._http.close()

    def login(self, credentials: Credentials) -> Self:
        """Use legacy single-token login on servers providing /api/v0/auth."""
        with self._session_lock:
            response = self.request(
                "POST",
                "/api/v0/auth/login",
                json=credentials.as_payload(),
                response_model=LoginResponse,
                options=_PUBLIC_REQUEST,
            )
            self._session = None
            self._token = AccessToken(response.token, expires_at=response.expires_at)
        return self

    def login_session(self, credentials: Credentials, *, client_id: str = "hubuum-python") -> Self:
        """Opt into rotating interactive credentials, retained only in memory.

        Requires the versioned session API. Refresh is serialized per client;
        failed or uncertain refresh destroys local credentials and is never retried.
        """
        client_id = validate_client_id(client_id)
        with self._session_lock:
            response = self.request(
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

    def _ensure_session(self) -> None:
        if self._session is None or not self._session.needs_refresh():
            return
        with self._session_lock:
            self._refresh_session()

    def _refresh_session(self) -> None:
        session = self._session
        if session is None or not session.needs_refresh():
            return
        try:
            session.require_refreshable()
            response = self.request(
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

    def logout(self) -> None:
        """Revoke the current session and clear local credentials in all cases."""
        with self._session_lock:
            try:
                endpoint = (
                    "/api/v1/auth/logout" if self._session is not None else "/api/v0/auth/logout"
                )
                self._refresh_session()
                # The lock is held; bypass another refresh check for this request.
                request, body = self._build_request("POST", endpoint, json=None, options=None)
                response = self._send_request(request, body, stream=False)
                if (
                    endpoint == "/api/v0/auth/logout"
                    and response.status_code == httpx.codes.NOT_FOUND
                ):
                    request, body = self._build_request(
                        "POST", "/api/v1/auth/logout", json=None, options=None
                    )
                    response = self._send_request(request, body, stream=False)
                raise_api_error(response)
            finally:
                self._session = None
                self._token = None

    def healthz(self) -> ProbeResponse:
        """Return the unauthenticated process-health probe."""
        return self.request(
            "GET", "/healthz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    def readyz(self) -> ProbeResponse:
        """Return the unauthenticated dependency-readiness probe."""
        return self.request("GET", "/readyz", response_model=ProbeResponse, options=_PUBLIC_REQUEST)

    def config(self) -> ClientConfig:
        """Return client-safe public server configuration."""
        return self.request(
            "GET",
            "/api/v1/config",
            response_model=ClientConfig,
            options=_PUBLIC_REQUEST,
        )

    def metrics(self) -> str:
        """Return Prometheus exposition text from the default ``/metrics`` path."""
        return self.metrics_at("/metrics")

    def metrics_at(self, path: str) -> str:
        """Return unauthenticated metrics text from an origin-locked custom path."""
        return self._request_response("GET", path, options=_PUBLIC_REQUEST).text

    def me(self) -> MeResponse:
        """Return the authenticated principal and current token metadata."""
        return self.request("GET", "/api/v1/iam/me", response_model=MeResponse)

    @cached_property
    def event_sinks(self) -> EventSinksService:
        """Administrator sink management and explicit collection grants."""
        return EventSinksService(self)

    @cached_property
    def collections(self) -> CollectionsService:
        """Return typed collection CRUD and hierarchy operations."""
        return CollectionsService(self)

    @cached_property
    def classes(self) -> ClassesService:
        """Return typed class and nested-object operations."""
        return ClassesService(self)

    @cached_property
    def users(self) -> UsersService:
        """Return typed user lifecycle operations."""
        return UsersService(self)

    @cached_property
    def groups(self) -> GroupsService:
        """Return typed group and membership operations."""
        return GroupsService(self)

    @cached_property
    def credential_approvals(self) -> CredentialApprovalsService:
        """Return operation-bound password approval and evidence operations."""
        return CredentialApprovalsService(self)

    @cached_property
    def tokens(self) -> TokensService:
        """Return typed principal-token operations."""
        return TokensService(self)

    @cached_property
    def class_relations(self) -> ClassRelationsService:
        """Return typed class-relation operations."""
        return ClassRelationsService(self)

    @cached_property
    def object_relations(self) -> ObjectRelationsService:
        """Return typed object-relation operations."""
        return ObjectRelationsService(self)

    @cached_property
    def tasks(self) -> TasksService:
        """Return task inspection, event, pagination, and polling operations."""
        return TasksService(self)

    @cached_property
    def imports(self) -> ImportsService:
        """Return typed asynchronous-import operations."""
        return ImportsService(self)

    @cached_property
    def exports(self) -> ExportsService:
        """Return typed asynchronous-export and output operations."""
        return ExportsService(self)

    @property
    def openapi(self) -> OpenAPIOperations:
        """Return the complete operation-ID interface for all 257 v0.0.20 operations."""
        return OpenAPIOperations(self)

    @cached_property
    def api(self) -> API:
        """Fully typed resource operations for the complete server contract."""
        from .api.services import API  # noqa: PLC0415 -- Load the full schema only on demand.

        return API(self)

    @overload
    def request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        response_model: type[T],
        options: RequestOptions | None = None,
    ) -> T: ...

    @overload
    def request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        response_model: None = None,
        options: RequestOptions | None = None,
    ) -> Any: ...

    def request(
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
        response = self._request_response(
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

    @contextmanager
    def stream(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Iterator[ResponseStream]:
        """Stream one origin-locked response without exposing request secrets."""
        response = self._request_stream_response(method, path, json=json, options=options)
        try:
            yield ResponseStream(response)
        finally:
            response.close()

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

    def _send_request(
        self,
        request: httpx.Request,
        request_body: Any,
        *,
        stream: bool,
    ) -> httpx.Response:
        try:
            return self._http.send(request, stream=stream)
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

    def _request_response(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> httpx.Response:
        if options is None or options.authenticated:
            self._ensure_session()
        request, request_body = self._build_request(
            method,
            path,
            json=json,
            options=options,
        )
        response = self._send_request(request, request_body, stream=False)
        raise_api_error(response)
        return response

    def _request_stream_response(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> httpx.Response:
        if options is None or options.authenticated:
            self._ensure_session()
        request, request_body = self._build_request(
            method,
            path,
            json=json,
            options=options,
        )
        response = self._send_request(request, request_body, stream=True)
        if not response.is_success:
            response.read()
            try:
                raise_api_error(response)
            finally:
                response.close()
        return response


from .openapi import OpenAPIOperations  # noqa: E402
from .services import (  # noqa: E402
    ClassesService,
    ClassRelationsService,
    CollectionsService,
    CredentialApprovalsService,
    EventSinksService,
    ExportsService,
    GroupsService,
    ImportsService,
    ObjectRelationsService,
    TasksService,
    TokensService,
    UsersService,
)
