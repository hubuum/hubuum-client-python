"""Asynchronous Hubuum client."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
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
from .models import LoginResponse, ProbeResponse
from .options import ClientOptions, RequestOptions
from .streaming import AsyncResponseStream
from .types import AccessToken, Credentials

T = TypeVar("T", bound=BaseModel)
_PUBLIC_REQUEST = RequestOptions(authenticated=False)


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
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def token(self) -> AccessToken | None:
        return self._token

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    async def login(self, credentials: Credentials) -> Self:
        response = await self.request(
            "POST",
            "/api/v0/auth/login",
            json=credentials.as_payload(),
            response_model=LoginResponse,
            options=_PUBLIC_REQUEST,
        )
        self._token = AccessToken(response.token)
        return self

    async def logout(self) -> None:
        try:
            await self.request("POST", "/api/v0/auth/logout")
        finally:
            self._token = None

    async def healthz(self) -> ProbeResponse:
        return await self.request(
            "GET", "/healthz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    async def readyz(self) -> ProbeResponse:
        return await self.request(
            "GET", "/readyz", response_model=ProbeResponse, options=_PUBLIC_REQUEST
        )

    async def config(self) -> dict[str, Any]:
        value = await self.request("GET", "/api/v1/config", options=_PUBLIC_REQUEST)
        return value if isinstance(value, dict) else {}

    @property
    def collections(self) -> AsyncCollectionsService:
        return AsyncCollectionsService(self)

    @property
    def classes(self) -> AsyncClassesService:
        return AsyncClassesService(self)

    @property
    def users(self) -> AsyncUsersService:
        return AsyncUsersService(self)

    @property
    def groups(self) -> AsyncGroupsService:
        return AsyncGroupsService(self)

    @property
    def class_relations(self) -> AsyncClassRelationsService:
        return AsyncClassRelationsService(self)

    @property
    def object_relations(self) -> AsyncObjectRelationsService:
        return AsyncObjectRelationsService(self)

    @property
    def tasks(self) -> AsyncTasksService:
        return AsyncTasksService(self)

    @property
    def openapi(self) -> AsyncOpenAPIOperations:
        """Complete operation-ID interface for all 196 v0.0.3 operations."""
        return AsyncOpenAPIOperations(self)

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
            secrets = sensitive_request_values(request.headers, request_body)
            raise TransportError(
                request.method,
                str(request.url.copy_with(query=None, fragment=None)),
                redact_text(str(error), secrets),
            ) from error

    async def _request_response(
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


from .async_services import (  # noqa: E402
    AsyncClassesService,
    AsyncClassRelationsService,
    AsyncCollectionsService,
    AsyncGroupsService,
    AsyncObjectRelationsService,
    AsyncTasksService,
    AsyncUsersService,
)
from .openapi import AsyncOpenAPIOperations  # noqa: E402
