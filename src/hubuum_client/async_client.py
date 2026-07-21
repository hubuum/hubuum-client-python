"""Asynchronous Hubuum client."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Self, TypeVar, overload

import httpx
from pydantic import BaseModel

from ._constants import __version__
from ._transport import (
    decode_json,
    decode_model,
    json_body,
    normalize_base_url,
    raise_api_error,
    validate_relative_path,
)
from .errors import TransportError
from .models import LoginResponse, ProbeResponse
from .types import AccessToken, ClassId, Credentials

T = TypeVar("T", bound=BaseModel)
ParamValue = str | int | float | bool | None
Params = (
    Mapping[str, ParamValue | Sequence[ParamValue]]
    | list[tuple[str, ParamValue]]
    | tuple[tuple[str, ParamValue], ...]
    | str
    | bytes
    | None
)


class AsyncClient:
    """Async client with the same resource surface as :class:`Client`."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | AccessToken | None = None,
        timeout: float | httpx.Timeout = 30.0,
        verify: bool | str = True,
        user_agent: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = normalize_base_url(base_url)
        self._token = AccessToken(token) if isinstance(token, str) else token
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            verify=verify,
            transport=transport,
            headers={"User-Agent": user_agent or f"hubuum-client-python/{__version__}"},
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
            authenticated=False,
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
            "GET", "/healthz", response_model=ProbeResponse, authenticated=False
        )

    async def readyz(self) -> ProbeResponse:
        return await self.request(
            "GET", "/readyz", response_model=ProbeResponse, authenticated=False
        )

    async def config(self) -> dict[str, Any]:
        value = await self.request("GET", "/api/v1/config", authenticated=False)
        return value if isinstance(value, dict) else {}

    @property
    def collections(self) -> AsyncCollectionsService:
        return AsyncCollectionsService(self)

    @property
    def classes(self) -> AsyncClassesService:
        return AsyncClassesService(self)

    def objects(self, class_id: ClassId | int) -> AsyncObjectsService:
        return AsyncObjectsService(self, ClassId(class_id))

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

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Params = None,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
        response_model: type[T],
        authenticated: bool = True,
    ) -> T: ...

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Params = None,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
        response_model: None = None,
        authenticated: bool = True,
    ) -> Any: ...

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Params = None,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
        response_model: type[T] | None = None,
        authenticated: bool = True,
    ) -> T | Any:
        response = await self._request_response(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
            authenticated=authenticated,
        )
        return (
            decode_model(response, response_model)
            if response_model is not None
            else decode_json(response)
        )

    async def _request_response(
        self,
        method: str,
        path: str,
        *,
        params: Params = None,
        json: BaseModel | Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
        authenticated: bool = True,
    ) -> httpx.Response:
        relative_path = validate_relative_path(path)
        request_headers = dict(headers or {})
        if authenticated and self._token is not None:
            request_headers["Authorization"] = f"Bearer {self._token.value}"
        try:
            response = await self._http.request(
                method.upper(),
                relative_path,
                params=params,
                json=json_body(json),
                headers=request_headers,
            )
        except httpx.HTTPError as error:
            raise TransportError(
                method.upper(), f"{self._base_url}{relative_path}", str(error)
            ) from error
        raise_api_error(response)
        return response


from .async_services import (  # noqa: E402
    AsyncClassesService,
    AsyncClassRelationsService,
    AsyncCollectionsService,
    AsyncGroupsService,
    AsyncObjectRelationsService,
    AsyncObjectsService,
    AsyncTasksService,
    AsyncUsersService,
)
