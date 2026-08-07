"""Complete operation-ID interface for the pinned Hubuum OpenAPI contract."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Any, TypeAlias, cast
from urllib.parse import quote

import httpx
from pydantic import BaseModel, JsonValue

from ._operations import (
    OPERATIONS,
    PUBLIC_OPERATION_IDS,
    STREAMING_OPERATION_IDS,
    OperationSpec,
)
from .errors import DecodeError
from .options import OpenAPIOptions, RequestOptions
from .streaming import AsyncResponseStream, ResponseStream

if TYPE_CHECKING:
    from .async_client import AsyncClient
    from .client import Client

JsonBody: TypeAlias = BaseModel | Mapping[str, Any] | list[Any] | None
OpenAPIResult: TypeAlias = JsonValue | str | bytes | None
_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _operation(operation_id: str) -> OperationSpec:
    try:
        return OPERATIONS[operation_id]
    except KeyError:
        raise ValueError(f"unknown Hubuum v0.0.9 operationId: {operation_id!r}") from None


def _operation_path(
    operation: OperationSpec,
    path_params: Mapping[str, str | int] | None,
) -> str:
    supplied = dict(path_params or {})
    expected = set(_PATH_PARAMETER.findall(operation.path))
    missing = expected - supplied.keys()
    extra = supplied.keys() - expected
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {sorted(missing)}")
        if extra:
            details.append(f"unexpected {sorted(extra)}")
        raise ValueError(f"invalid path_params for {operation.operation_id}: {', '.join(details)}")
    return _PATH_PARAMETER.sub(
        lambda match: quote(str(supplied[match.group(1)]), safe=""),
        operation.path,
    )


def _request_options(
    operation: OperationSpec,
    *,
    options: OpenAPIOptions,
    default_accept: str,
) -> RequestOptions:
    prepared = {
        key: value
        for key, value in (options.headers or {}).items()
        if key.casefold() not in {"accept", "content-type"}
    }
    content_type = options.content_type or operation.request_media_type
    if content_type is not None:
        if content_type not in operation.request_media_types:
            raise ValueError(
                f"unsupported content type for {operation.operation_id}: {content_type!r}"
            )
        prepared["Content-Type"] = content_type
    prepared["Accept"] = options.accept or default_accept
    return RequestOptions(
        params=options.params,
        headers=prepared or None,
        authenticated=operation.operation_id not in PUBLIC_OPERATION_IDS,
    )


def _validate_body(operation: OperationSpec, body: JsonBody) -> None:
    if not operation.request_media_types and body is not None:
        raise ValueError(f"{operation.operation_id} does not define a request body")
    if operation.request_media_types and body is None:
        raise ValueError(f"{operation.operation_id} requires a request body")


def _decode_response(response: httpx.Response, *, accept: str | None) -> OpenAPIResult:
    if response.status_code in {204, 205} or not response.content:
        return None
    content_type = response.headers.get("content-type", "").partition(";")[0].strip().casefold()
    if content_type == "application/json" or content_type.endswith("+json"):
        try:
            return cast(JsonValue, response.json())
        except ValueError as error:
            raise DecodeError(
                response.request.method,
                str(response.request.url.copy_with(query=None, fragment=None)),
                response.status_code,
                str(error),
            ) from error
    if content_type.startswith("text/") or (accept is not None and accept.startswith("text/")):
        return response.text
    return response.content


class OpenAPIOperations:
    """Invoke every operation in Hubuum v0.0.9 by its stable OpenAPI operationId."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def operation_ids(self) -> tuple[str, ...]:
        return tuple(OPERATIONS)

    def operation(self, operation_id: str) -> OperationSpec:
        return _operation(operation_id)

    def call(
        self,
        operation_id: str,
        *,
        json: JsonBody = None,
        options: OpenAPIOptions | None = None,
    ) -> OpenAPIResult:
        operation_options = options or OpenAPIOptions()
        operation = _operation(operation_id)
        if operation_id in STREAMING_OPERATION_IDS:
            raise ValueError(f"{operation_id} is streaming; use openapi.stream()")
        _validate_body(operation, json)
        response = self._client._request_response(
            operation.method,
            _operation_path(operation, operation_options.path_params),
            json=json,
            options=_request_options(
                operation,
                options=operation_options,
                default_accept="application/json",
            ),
        )
        return _decode_response(response, accept=operation_options.accept)

    @contextmanager
    def stream(
        self,
        operation_id: str,
        *,
        options: OpenAPIOptions | None = None,
    ) -> Iterator[ResponseStream]:
        operation_options = options or OpenAPIOptions()
        operation = _operation(operation_id)
        if operation_id not in STREAMING_OPERATION_IDS:
            raise ValueError(f"{operation_id} is not a streaming operation")
        with self._client.stream(
            operation.method,
            _operation_path(operation, operation_options.path_params),
            options=_request_options(
                operation,
                options=operation_options,
                default_accept="text/event-stream",
            ),
        ) as response:
            yield response


class AsyncOpenAPIOperations:
    """Asynchronous operation-ID interface for the complete v0.0.9 contract."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @property
    def operation_ids(self) -> tuple[str, ...]:
        return tuple(OPERATIONS)

    def operation(self, operation_id: str) -> OperationSpec:
        return _operation(operation_id)

    async def call(
        self,
        operation_id: str,
        *,
        json: JsonBody = None,
        options: OpenAPIOptions | None = None,
    ) -> OpenAPIResult:
        operation_options = options or OpenAPIOptions()
        operation = _operation(operation_id)
        if operation_id in STREAMING_OPERATION_IDS:
            raise ValueError(f"{operation_id} is streaming; use openapi.stream()")
        _validate_body(operation, json)
        response = await self._client._request_response(
            operation.method,
            _operation_path(operation, operation_options.path_params),
            json=json,
            options=_request_options(
                operation,
                options=operation_options,
                default_accept="application/json",
            ),
        )
        return _decode_response(response, accept=operation_options.accept)

    @asynccontextmanager
    async def stream(
        self,
        operation_id: str,
        *,
        options: OpenAPIOptions | None = None,
    ) -> AsyncIterator[AsyncResponseStream]:
        operation_options = options or OpenAPIOptions()
        operation = _operation(operation_id)
        if operation_id not in STREAMING_OPERATION_IDS:
            raise ValueError(f"{operation_id} is not a streaming operation")
        async with self._client.stream(
            operation.method,
            _operation_path(operation, operation_options.path_params),
            options=_request_options(
                operation,
                options=operation_options,
                default_accept="text/event-stream",
            ),
        ) as response:
            yield response
