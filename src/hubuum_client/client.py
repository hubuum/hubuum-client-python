"""Synchronous Hubuum client."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from functools import cached_property
from typing import Any, Self, TypeVar, overload

import httpx
from pydantic import BaseModel

from ._constants import __version__
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
from .models import ClientConfig, LoginResponse, MeResponse, ProbeResponse
from .options import ClientOptions, RequestOptions
from .streaming import ResponseStream
from .types import AccessToken, Credentials

T = TypeVar("T", bound=BaseModel)
_PUBLIC_REQUEST = RequestOptions(authenticated=False)


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
        """Authenticate this client in place and retain the returned token."""
        response = self.request(
            "POST",
            "/api/v0/auth/login",
            json=credentials.as_payload(),
            response_model=LoginResponse,
            options=_PUBLIC_REQUEST,
        )
        self._token = AccessToken(response.token, expires_at=response.expires_at)
        return self

    def logout(self) -> None:
        """Revoke the current session and clear the local token in all cases."""
        try:
            self.request("POST", "/api/v0/auth/logout")
        finally:
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
        """Return the complete operation-ID interface for all 196 v0.0.8 operations."""
        return OpenAPIOperations(self)

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
            raise TransportError(
                request.method,
                str(request.url.copy_with(query=None, fragment=None)),
                redact_text(str(error), secrets),
            ) from error

    def _request_response(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        options: RequestOptions | None = None,
    ) -> httpx.Response:
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
from .services import (  # noqa: E402  (imported after Client is defined)
    ClassesService,
    ClassRelationsService,
    CollectionsService,
    ExportsService,
    GroupsService,
    ImportsService,
    ObjectRelationsService,
    TasksService,
    TokensService,
    UsersService,
)
