from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from hubuum_client import (
    AsyncClient,
    Client,
    DecodeError,
    ObjectDataPatchOperation,
    OpenAPIOptions,
)
from hubuum_client._operations import OPERATIONS, SUPPORTED_OPERATIONS


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> Client:
    return Client("https://hubuum.test", token="token", transport=httpx.MockTransport(handler))


def _async_client(handler: Callable[[httpx.Request], httpx.Response]) -> AsyncClient:
    return AsyncClient(
        "https://hubuum.test",
        token="token",
        transport=httpx.MockTransport(handler),
    )


def test_manifest_deliberately_covers_all_v003_operations() -> None:
    assert len(OPERATIONS) == 196
    assert len(SUPPORTED_OPERATIONS) == 196
    assert OPERATIONS["getApiV1SearchStream"].path == "/api/v1/search/stream"
    assert (
        OPERATIONS[
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectNameData"
        ].request_media_type
        == "application/json-patch+json"
    )
    assert OPERATIONS["deleteApiV1ClassesByClassId"].response_media_types == ()
    assert OPERATIONS["getApiV1Config"].response_media_types == ("application/json",)
    assert OPERATIONS["getApiV1ExportsByTaskIdOutput"].response_media_types == (
        "application/json",
        "text/csv",
        "text/html",
        "text/plain",
    )


def test_openapi_call_formats_paths_media_types_and_response_modes() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/config":
            return httpx.Response(200, json={"pagination": {"max_page_limit": 250}})
        if request.url.path.endswith("/data"):
            return httpx.Response(200, json={"patched": True})
        if request.url.path.endswith("/output"):
            return httpx.Response(
                200, text="name,id\nhost,1\n", headers={"Content-Type": "text/csv"}
            )
        raise AssertionError(request.url)

    with _client(handler) as client:
        config = client.openapi.call("getApiV1Config")
        patched = client.openapi.call(
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectNameData",
            json=[{"op": "add", "path": "/facts", "value": {"serial": "A"}}],
            options=OpenAPIOptions(
                path_params={"class_name": "Hosts 2", "object_name": "123/name"},
                headers={
                    "Idempotency-Key": "patch-1",
                    "content-type": "text/plain",
                    "accept": "text/plain",
                },
            ),
        )
        exported = client.openapi.call(
            "getApiV1ExportsByTaskIdOutput",
            options=OpenAPIOptions(path_params={"task_id": 7}, accept="text/csv"),
        )

    assert config == {"pagination": {"max_page_limit": 250}}
    assert patched == {"patched": True}
    assert exported == "name,id\nhost,1\n"
    assert "authorization" not in requests[0].headers
    assert requests[1].url.raw_path == (
        b"/api/v1/classes/by-name/Hosts%202/objects/by-name/123%2Fname/data"
    )
    assert requests[1].headers["authorization"] == "Bearer token"
    assert requests[1].headers["content-type"] == "application/json-patch+json"
    assert requests[1].headers["accept"] == "application/json"
    assert requests[1].headers["idempotency-key"] == "patch-1"
    assert json.loads(requests[1].content) == [
        {"op": "add", "path": "/facts", "value": {"serial": "A"}}
    ]
    assert requests[2].headers["accept"] == "text/csv"


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda client: client.openapi.call("missingOperation"),
            "unknown",
        ),
        (
            lambda client: client.openapi.call(
                "getApiV1TasksByTaskId",
                options=OpenAPIOptions(),
            ),
            "missing",
        ),
        (
            lambda client: client.openapi.call(
                "getApiV1Config",
                options=OpenAPIOptions(path_params={"extra": 1}),
            ),
            "unexpected",
        ),
        (
            lambda client: client.openapi.call("getApiV1Config", json={}),
            "does not define",
        ),
        (
            lambda client: client.openapi.call("postApiV1Imports"),
            "requires",
        ),
        (
            lambda client: client.openapi.call(
                "getApiV1SearchStream",
                options=OpenAPIOptions(params={"q": "server"}),
            ),
            "streaming",
        ),
    ],
)
def test_openapi_call_rejects_contract_mismatches(
    call: Callable[[Client], object],
    message: str,
) -> None:
    with (
        _client(lambda request: pytest.fail(f"unexpected request: {request.url}")) as client,
        pytest.raises(ValueError, match=message),
    ):
        call(client)


def test_openapi_stream_is_incremental_and_restricted_to_stream_operations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "text/event-stream"
        assert request.url.params["q"] == "server"
        return httpx.Response(
            200,
            text='event: result\ndata: {"kind":"object"}\n\n',
            headers={"Content-Type": "text/event-stream"},
        )

    with _client(handler) as client:
        with client.openapi.stream(
            "getApiV1SearchStream",
            options=OpenAPIOptions(params={"q": "server"}),
        ) as response:
            assert response.status_code == 200
            assert list(response.iter_lines()) == [
                "event: result",
                'data: {"kind":"object"}',
                "",
            ]
        with (
            pytest.raises(ValueError, match="not a streaming"),
            client.openapi.stream("getApiV1Config"),
        ):
            pass


async def test_async_openapi_call_and_stream_match_sync_behavior() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/search/stream":
            return httpx.Response(200, text="data: done\n\n")
        return httpx.Response(200, json={"id": 9})

    async with _async_client(handler) as client:
        result = await client.openapi.call(
            "getApiV1TasksByTaskId",
            options=OpenAPIOptions(path_params={"task_id": 9}),
        )
        async with client.openapi.stream(
            "getApiV1SearchStream",
            options=OpenAPIOptions(params={"q": "done"}),
        ) as response:
            lines = [line async for line in response.iter_lines()]

    assert result == {"id": 9}
    assert lines == ["data: done", ""]
    assert requests[0].url.path == "/api/v1/tasks/9"


def test_openapi_invalid_json_does_not_fall_back_to_text() -> None:
    with (
        _client(
            lambda request: httpx.Response(
                200,
                text="not-json",
                headers={"Content-Type": "application/json"},
            )
        ) as client,
        pytest.raises(DecodeError),
    ):
        client.openapi.call("getApiV1Config")


def test_object_data_patch_operation_enforces_rfc_member_shapes_without_losing_null() -> None:
    add_null = ObjectDataPatchOperation(op="add", path="/optional", value=None)
    move = ObjectDataPatchOperation(op="move", path="/new", from_path="/old")

    assert add_null.payload() == {"op": "add", "path": "/optional", "value": None}
    assert move.payload() == {"op": "move", "path": "/new", "from": "/old"}
    with pytest.raises(ValueError, match="require value"):
        ObjectDataPatchOperation(op="add", path="/missing")
    with pytest.raises(ValueError, match="only valid"):
        ObjectDataPatchOperation(op="remove", path="/old", value="secret")
