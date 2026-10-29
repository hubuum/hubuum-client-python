from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from hubuum_client import AsyncClient, Client, DecodeError
from hubuum_client.api import models, query


class ChunkStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes], *, block: bool = False) -> None:
        self.chunks = chunks
        self.consumed = 0
        self.closed = False
        self.block = block
        self.waiting = asyncio.Event()

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self.chunks:
            self.consumed += 1
            yield chunk

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self:
            yield chunk
        if self.block:
            self.waiting.set()
            await asyncio.Event().wait()

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        await asyncio.sleep(0)
        self.close()


def _context(client: Client | AsyncClient, structured: bool) -> Any:
    if structured:
        return client.api.search.post_stream(
            body=models.StructuredSearchRequest(
                version=1, target=models.StructuredSearchTargetObject(kind="object")
            )
        )
    return client.api.search.get_stream(query=query.SearchGetStreamQuery(q="blåbær"))


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("ending", ["complete", "early", "decode_error"])
async def test_chunked_events_are_incremental_and_close(
    asynchronous: bool, structured: bool, ending: str
) -> None:
    # Both protocols have a message-bearing error event. It is data, not a
    # transport exception, and permits a UTF-8 split inside a multibyte value.
    first = (
        "event: error\r\ndata: "
        + json.dumps({"message": "blåbær", "kind": "object", "version": 1}, ensure_ascii=False)
        + "\r\n\r\n"
    ).encode()
    tail = (
        b"event: error\ndata: "
        + (
            b"response-secret"
            if ending == "decode_error"
            else b'{"message":"second","kind":"object","version":1}'
        )
        + b"\n\n"
    )
    chunks = [bytes([value]) for value in first] + [tail]
    body = ChunkStream(chunks)
    response = httpx.Response(200, stream=body, headers={"Content-Type": "text/event-stream"})
    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test",
        token="bearer-secret",
        transport=httpx.MockTransport(lambda request: response),
    )

    async def consume() -> None:
        if isinstance(client, AsyncClient):
            async with _context(client, structured) as stream:
                events = stream.events()
                event = await anext(events)
                assert event.data.message == "blåbær"
                assert body.consumed < len(chunks)
                assert not body.closed
                if ending != "early":
                    remaining = [event async for event in events]
                    assert len(remaining) == 1
        else:
            with _context(client, structured) as stream:
                events = stream.events()
                event = next(events)
                assert event.data.message == "blåbær"
                assert body.consumed < len(chunks)
                assert not body.closed
                if ending != "early":
                    assert len(list(events)) == 1

    try:
        if ending == "decode_error":
            with pytest.raises(DecodeError) as error:
                await consume()
            assert "response-secret" not in str(error.value)
            assert error.value.__context__ is None
        else:
            await consume()
        assert response.is_closed
        assert body.closed
        assert body.consumed == (len(first) if ending == "early" else len(chunks))
    finally:
        if isinstance(client, AsyncClient):
            await client.close()
        else:
            client.close()


@pytest.mark.parametrize("structured", [False, True])
async def test_cancelling_event_consumer_closes_response(structured: bool) -> None:
    body = ChunkStream([b": heartbeat\n\n"], block=True)
    response = httpx.Response(200, stream=body, headers={"Content-Type": "text/event-stream"})
    async with AsyncClient(
        "https://hubuum.test", transport=httpx.MockTransport(lambda request: response)
    ) as client:

        async def consume() -> None:
            async with _context(client, structured) as stream:
                async for _ in stream.events():
                    pytest.fail("heartbeat must not produce an event")

        task = asyncio.create_task(consume())
        try:
            await asyncio.wait_for(body.waiting.wait(), timeout=2)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert body.closed
        assert response.is_closed
