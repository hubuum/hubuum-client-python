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
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def token(self) -> AccessToken | None:
        return self._token

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def login(self, credentials: Credentials) -> Self:
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
        try:
            self.request("POST", "/api/v0/auth/logout")
        finally:
            self._token = None

    def healthz(self) -> ProbeResponse:
        return self.request(
            "GET", "/healthz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    def readyz(self) -> ProbeResponse:
        return self.request("GET", "/readyz", response_model=ProbeResponse, options=_PUBLIC_REQUEST)

    def config(self) -> ClientConfig:
        return self.request(
            "GET",
            "/api/v1/config",
            response_model=ClientConfig,
            options=_PUBLIC_REQUEST,
        )

    def me(self) -> MeResponse:
        return self.request("GET", "/api/v1/iam/me", response_model=MeResponse)

    @cached_property
    def collections(self) -> CollectionsService:
        return CollectionsService(self)

    @cached_property
    def classes(self) -> ClassesService:
        return ClassesService(self)

    @cached_property
    def users(self) -> UsersService:
        return UsersService(self)

    @cached_property
    def groups(self) -> GroupsService:
        return GroupsService(self)

    @cached_property
    def tokens(self) -> TokensService:
        return TokensService(self)

    @cached_property
    def class_relations(self) -> ClassRelationsService:
        return ClassRelationsService(self)

    @cached_property
    def object_relations(self) -> ObjectRelationsService:
        return ObjectRelationsService(self)

    @cached_property
    def tasks(self) -> TasksService:
        return TasksService(self)

    @property
    def openapi(self) -> OpenAPIOperations:
        """Complete operation-ID interface for all 196 v0.0.5 operations."""
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
    GroupsService,
    ObjectRelationsService,
    TasksService,
    TokensService,
    UsersService,
)
