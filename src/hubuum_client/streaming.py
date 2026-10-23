"""Secret-safe wrappers for streamed Hubuum responses."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Generic, TypeVar

import httpx
from pydantic import TypeAdapter

from ._transport import _ServerEventDecoder
from .models import ServerEvent

T = TypeVar("T")


class ResponseStream:
    """A synchronous response body consumed inside ``Client.stream()``."""

    __slots__ = ("_response",)

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Mapping[str, str]:
        return self._response.headers

    def iter_bytes(self) -> Iterator[bytes]:
        return self._response.iter_bytes()

    def iter_text(self) -> Iterator[str]:
        return self._response.iter_text()

    def iter_lines(self) -> Iterator[str]:
        return self._response.iter_lines()


class AsyncResponseStream:
    """An asynchronous response body consumed inside ``AsyncClient.stream()``."""

    __slots__ = ("_response",)

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Mapping[str, str]:
        return self._response.headers

    def iter_bytes(self) -> AsyncIterator[bytes]:
        return self._response.aiter_bytes()

    def iter_text(self) -> AsyncIterator[str]:
        return self._response.aiter_text()

    def iter_lines(self) -> AsyncIterator[str]:
        return self._response.aiter_lines()


class TypedResponseStream(ResponseStream, Generic[T]):
    """A response stream whose ``events()`` validates each named SSE payload."""

    __slots__ = ("_adapters",)

    def __init__(self, stream: ResponseStream, adapters: Mapping[str, TypeAdapter[T]]) -> None:
        super().__init__(stream._response)
        self._adapters = adapters

    def events(self) -> Iterator[ServerEvent[T]]:
        decoder = _ServerEventDecoder(self._response, self._adapters)
        for line in self.iter_lines():
            event = decoder.feed(line)
            if event is not None:
                yield event


class AsyncTypedResponseStream(AsyncResponseStream, Generic[T]):
    """Asynchronous typed SSE events, with the same framing and validation."""

    __slots__ = ("_adapters",)

    def __init__(self, stream: AsyncResponseStream, adapters: Mapping[str, TypeAdapter[T]]) -> None:
        super().__init__(stream._response)
        self._adapters = adapters

    async def events(self) -> AsyncIterator[ServerEvent[T]]:
        decoder = _ServerEventDecoder(self._response, self._adapters)
        async for line in self.iter_lines():
            event = decoder.feed(line)
            if event is not None:
                yield event
