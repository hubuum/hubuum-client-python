"""Secret-safe wrappers for streamed Hubuum responses."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping

import httpx


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
