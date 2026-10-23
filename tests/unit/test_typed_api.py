from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, get_type_hints

import httpx
import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from hubuum_client import (
    AsyncClient,
    ClassRelationCreate,
    ClassRelationUpdate,
    Client,
    DecodeError,
    ImportClassRelationInput,
    OpenAPIOptions,
)
from hubuum_client._operations import CAPABILITY_OPERATION_IDS, OPERATIONS, PUBLIC_OPERATION_IDS
from hubuum_client._transport import api_body
from hubuum_client.api import models, query
from hubuum_client.models import APIResponse

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = json.loads((ROOT / "docs/openapi.json").read_text())
COVERAGE = json.loads((ROOT / "src/hubuum_client/api/operations.json").read_text())
SPEC = {
    operation["operationId"]: operation
    for item in DOCUMENT["paths"].values()
    for operation in item.values()
    if isinstance(operation, dict) and "operationId" in operation
}


def example(schema: dict[str, Any], seen: tuple[str, ...] = ()) -> Any:
    """Build independent, minimally populated wire fixtures from the contract."""
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[1]
        return example(DOCUMENT["components"]["schemas"][name], (*seen, name))
    if "enum" in schema:
        return schema["enum"][0]
    if "allOf" in schema:
        return {
            key: value for item in schema["allOf"] for key, value in example(item, seen).items()
        }
    for union in ("oneOf", "anyOf"):
        if union in schema:
            choices = schema[union]
            if "StructuredSearchExpression" in seen:
                choices = sorted(choices, key=lambda x: "predicate" not in x.get("properties", {}))
            return example(choices[0], seen)
    kind = schema.get("type")
    if isinstance(kind, list):
        return example({**schema, "type": kind[0]}, seen)
    if kind == "object":
        return {
            name: example(schema["properties"][name], seen) for name in schema.get("required", [])
        }
    if kind == "array":
        return [example(schema.get("items", {}), seen) for _ in range(schema.get("minItems", 0))]
    if kind in {"integer", "number"}:
        return max(1, schema.get("minimum", 1))
    if kind == "boolean":
        return True
    if kind == "string":
        if schema.get("format") == "date-time":
            return "2026-10-22T12:00:00+00:00"
        if schema.get("format") == "uuid":
            return "00000000-0000-4000-8000-000000000001"
        if schema.get("pattern", "").startswith("^hca1"):
            return "hca1." + "a" * 64
        return "sample"[: schema.get("maxLength", 6)]
    return None


async def resolve(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


def test_every_operation_and_schema_has_a_typed_public_surface() -> None:
    assert COVERAGE.keys() == OPERATIONS.keys()
    for name in DOCUMENT["components"]["schemas"]:
        assert hasattr(models, name), name
        TypeAdapter(getattr(models, name))
    with Client("https://hubuum.test") as client:
        for entry in COVERAGE.values():
            method = getattr(getattr(client.api, entry["service"]), entry["method"])
            hints = get_type_hints(method)
            assert hints["return"] is not Any
            assert all(value is not Any for value in hints.values())


def operation_fixture(operation: dict[str, Any]) -> tuple[str, str | None, Any, str | None, Any]:
    responses = {
        status: response
        for status, response in operation["responses"].items()
        if status.startswith("2")
    }
    status, response = next(iter(responses.items()))
    response_media = next(iter(response.get("content", {})), None)
    response_data = (
        example(response["content"][response_media].get("schema", {})) if response_media else None
    )
    if response_media and response_media.startswith("text/"):
        response_data = "data: {}\n\n" if response_media == "text/event-stream" else "report"
    body_content = operation.get("requestBody", {}).get("content", {})
    body_media = next(iter(body_content), None)
    request_body = example(body_content[body_media]["schema"]) if body_media else None
    return status, response_media, response_data, body_media, request_body


def operation_arguments(
    method: Any, operation: dict[str, Any], body_media: str | None, request_body: Any
) -> dict[str, Any]:
    hints = get_type_hints(method)
    arguments: dict[str, Any] = {}
    for parameter in operation.get("parameters", []):
        if parameter["in"] == "path":
            name = parameter["name"]
            arguments["id_" if name == "id" else name] = example(parameter["schema"])
    for location in ("query", "header"):
        if location in hints:
            values = {
                p["name"]: example(p["schema"])
                for p in operation.get("parameters", [])
                if p["in"] == location and p.get("required", False)
            }
            arguments[location] = TypeAdapter(hints[location]).validate_python(values)
    if body_media:
        arguments["body"] = TypeAdapter(hints["body"]).validate_python(request_body)
    return arguments


@pytest.mark.parametrize("operation_id", tuple(COVERAGE))
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_all_typed_operations_validate_wire_bodies_and_decode_responses(
    operation_id: str, asynchronous: bool
) -> None:
    operation = SPEC[operation_id]
    manifest = OPERATIONS[operation_id]
    status, response_media, response_data, body_media, request_body = operation_fixture(operation)
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == manifest.method
        if operation_id in PUBLIC_OPERATION_IDS | CAPABILITY_OPERATION_IDS:
            assert "authorization" not in request.headers
        else:
            assert request.headers["authorization"] == "Bearer test-token"
        if body_media:
            assert request.headers["content-type"] == body_media
            assert json.loads(request.content) == request_body
        headers = {"X-Next-Cursor": "next", "X-Total-Count": "17", "ETag": '"revision"'}
        if response_media:
            headers["content-type"] = response_media
            content = json.dumps(response_data) if "json" in response_media else response_data
            return httpx.Response(int(status), content=content, headers=headers)
        return httpx.Response(int(status), headers=headers)

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="test-token", transport=httpx.MockTransport(handle)
    )
    try:
        entry = COVERAGE[operation_id]
        method = getattr(getattr(client.api, entry["service"]), entry["method"])
        arguments = operation_arguments(method, operation, body_media, request_body)
        result = method(**arguments)
        if response_media == "text/event-stream":
            if asynchronous:
                async with result as stream:
                    assert "data: {}" in [line async for line in stream.iter_lines()]
            else:
                with result as stream:
                    assert "data: {}" in list(stream.iter_lines())
        else:
            result = await resolve(result)
            assert isinstance(result, APIResponse)
            assert result.status_code == int(status)
            assert result.next_cursor == "next"
            assert result.total_count == 17
            assert result.etag == '"revision"'
            if isinstance(response_data, dict) and response_data:
                assert isinstance(result.body, BaseModel)
            if response_data is None:
                assert result.body is None
        assert len(calls) == 1
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_relation_label_mutations_preserve_explicit_null_and_revision(
    asynchronous: bool,
) -> None:
    wire = example(DOCUMENT["components"]["schemas"]["HubuumClassRelation"])
    sent: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        sent.append(payload)
        if request.method == "PATCH":
            assert request.headers["if-match"] == '"revision"'
        return httpx.Response(200, json={**wire, **payload})

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handle)
    )
    try:
        created = await resolve(
            client.class_relations.create(
                ClassRelationCreate(
                    from_hubuum_class_id=1,
                    to_hubuum_class_id=2,
                    forward_label="owns",
                    reverse_label="owned by",
                )
            )
        )
        assert created.forward_label == "owns"
        updated = await resolve(
            client.class_relations.update(
                1, ClassRelationUpdate(forward_label=None), if_match='"revision"'
            )
        )
        assert updated.forward_label is None
        assert sent[-1] == {"forward_label": None}
        assert ImportClassRelationInput(forward_label="owns").payload()["forward_label"] == "owns"
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_invalid_response_and_request_diagnostics_are_secret_safe(asynchronous: bool) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "response-secret", "session_id": "bad"})

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", transport=httpx.MockTransport(handle)
    )
    entry = COVERAGE["postApiV1AuthLogin"]
    method = getattr(client.api.auth, entry["method"])
    try:
        with pytest.raises(DecodeError) as error:
            await resolve(
                method(
                    body=models.SessionLoginRequest(
                        client_id="typed-tests", name="alice", password="request-secret"
                    )
                )
            )
        assert "secret" not in str(error.value)
        assert error.value.__context__ is None
        with pytest.raises(ValueError, match="Invalid typed API request"):
            await resolve(method(body={"password": "request-secret"}))
    finally:
        await resolve(client.close())


def test_secret_models_and_arbitrary_json_preserve_wire_shapes() -> None:
    value = models.SessionLoginRequest(client_id="sdk", name="alice", password="private-password")
    assert "private-password" not in repr(value)
    assert "private-password" not in value.model_dump_json()
    assert value.wire_payload()["password"] == "private-password"
    with pytest.raises(ValidationError) as error:
        models.SessionLoginRequest.model_validate({"password": "private-password"})
    assert "private-password" not in f"{error.value} {error.value.errors()} {error.value.json()}"
    assert error.value.__context__ is None
    data = {"arbitrary": {"nested": [None, 2, True]}}
    assert TypeAdapter(models.PrincipalSettings).validate_python(data) == data
    assert models.UpdateClassRelationLabels(forward_label=None).wire_payload() == {
        "forward_label": None
    }


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_query_controls_and_extension_filters_merge(asynchronous: bool) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.params == httpx.QueryParams(
            "name__contains=Hosts&limit=2&include_total=true"
        )
        assert request.headers["x-trace"] == "request"
        return httpx.Response(200, json=[])

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handle)
    )
    try:
        result = await resolve(
            client.api.classes.list(
                query=query.ClassesListQuery(limit=2, include_total=True),
                options=OpenAPIOptions(
                    params={"name__contains": "Hosts"}, headers={"X-Trace": "request"}
                ),
            )
        )
        assert result.body == []
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("malformed", [False, True])
async def test_typed_search_events(asynchronous: bool, structured: bool, malformed: bool) -> None:
    schema = "StructuredSearchDoneEvent" if structured else "UnifiedSearchDoneEvent"
    data = example(DOCUMENT["components"]["schemas"][schema])
    payload = "response-secret" if malformed else json.dumps(data, indent=2)
    # Comments and unrelated framing fields must not disrupt multiline data.
    content = ": keepalive\n\nevent: done\nid: 7\nretry: 1000\n"
    content += "\n".join("data: " + line for line in payload.splitlines()) + "\n\n"
    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test",
        token="token",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, text=content, headers={"Content-Type": "text/event-stream"}
            )
        ),
    )
    try:
        context: Any = (
            client.api.search.post_stream(
                body=models.StructuredSearchRequest(
                    version=1, target=models.StructuredSearchTargetObject(kind="object")
                )
            )
            if structured
            else client.api.search.get_stream(query=query.SearchGetStreamQuery(q="server"))
        )

        async def collect() -> list[Any]:
            if asynchronous:
                async with context as stream:
                    return [event async for event in stream.events()]
            with context as stream:
                return list(stream.events())

        if malformed:
            with pytest.raises(DecodeError) as error:
                await collect()
            assert "response-secret" not in str(error.value)
            assert error.value.__context__ is None
        else:
            events = await collect()
            assert len(events) == 1
            assert events[0].event == "done"
            assert isinstance(events[0].data, getattr(models, schema))
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "media", ["application/json", "application/merge-patch+json", "application/json-patch+json"]
)
async def test_typed_alternate_request_media(asynchronous: bool, media: str) -> None:
    operation_id = "patchApiV1IamPrincipalsByPrincipalIdSettings"
    entry = COVERAGE[operation_id]
    operation = SPEC[operation_id]
    body = (
        [{"op": "add", "path": "/theme", "value": "dark"}]
        if "json-patch" in media
        else {"theme": "dark"}
    )

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == media
        assert json.loads(request.content) == body
        return httpx.Response(
            200,
            json={
                **example(DOCUMENT["components"]["schemas"]["PrincipalSettingsResponse"]),
                "settings": {"theme": "dark"},
            },
        )

    client = (AsyncClient if asynchronous else Client)(
        "https://hubuum.test", token="token", transport=httpx.MockTransport(handle)
    )
    try:
        method = getattr(getattr(client.api, entry["service"]), entry["method"])
        arguments = operation_arguments(method, operation, media, body)
        result = await resolve(method(**arguments, content_type=media))
        assert result.body.settings == {"theme": "dark"}
        with pytest.raises(ValueError, match="Invalid typed API request"):
            await resolve(method(principal_id=1, body=["secret"], content_type="application/json"))
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_typed_controls_reject_route_and_media_overrides(asynchronous: bool) -> None:
    client = (AsyncClient if asynchronous else Client)("https://hubuum.test", token="token")
    try:
        for options in (OpenAPIOptions(path_params={"id": 1}), OpenAPIOptions(accept="text/html")):
            with pytest.raises(ValueError, match="typed"):
                await resolve(client.api.classes.list(options=options))
    finally:
        await resolve(client.close())


@pytest.mark.parametrize("name", tuple(DOCUMENT["components"]["schemas"]))
def test_every_schema_round_trips_required_wire_fields(name: str) -> None:
    expected = example(DOCUMENT["components"]["schemas"][name])
    adapter = TypeAdapter(getattr(models, name))
    assert (
        api_body(
            expected, {"application/json": adapter}, content_type="application/json", optional=False
        )
        == expected
    )
