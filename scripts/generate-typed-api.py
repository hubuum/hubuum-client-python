#!/usr/bin/env python3
"""Generate the complete typed API from the pinned, local OpenAPI document.

datamodel-code-generator handles JSON Schema; this script supplies the existing
Hubuum transports, safe model base, and explicit synchronous/asynchronous methods.
No remote schema references or runtime code generation are used.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import keyword
import re
import subprocess  # nosec B404 # Offline generation invokes fixed local Python modules.
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "src/hubuum_client/api"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
MAX_ARGUMENTS = 5
SEARCH_EVENTS = {
    "get": {
        "started": "UnifiedSearchStartedEvent",
        "batch": "UnifiedSearchBatchResponse",
        "done": "UnifiedSearchDoneEvent",
        "error": "UnifiedSearchErrorEvent",
    },
    "post": {
        "started": "StructuredSearchStartedEvent",
        "result": "StructuredSearchResult",
        "done": "StructuredSearchDoneEvent",
        "error": "StructuredSearchErrorEvent",
    },
}
HEADER = '"""Generated from docs/openapi.json; run scripts/generate-typed-api.py."""\n'


def identifier(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    value = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    value = re.sub(r"_+", "_", value)
    return value + "_" if keyword.iskeyword(value) or value in {"self", "id"} else value


def class_name(name: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[^a-zA-Z0-9]+", name))


def prepare_schema(document: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(document)

    def visit(value: Any, field: str = "") -> None:
        if isinstance(value, list):
            for item in value:
                visit(item, field)
        elif isinstance(value, dict):
            for key in ("description", "example", "examples"):
                value.pop(key, None)
            if value.get("type") == "object" and "properties" not in value:
                value.setdefault("additionalProperties", {})
            kind = value.get("type", [])
            if (kind == "string" or "string" in kind) and (
                field
                in {
                    "password",
                    "password_hash",
                    "token",
                    "access_token",
                    "refresh_token",
                    "confirmation_token",
                    "status_token",
                    "approval",
                    "secret",
                }
            ):
                value["format"] = "password"
            for key, item in value.items():
                if key == "properties":
                    for name, definition in item.items():
                        visit(definition, name)
                else:
                    visit(item, field)

    visit(result)
    schemas = result["components"]["schemas"]
    for name in ("CredentialApprovalSecret", "RefreshToken"):
        schemas[name] = {"type": "string", "format": "password"}
    # The index asks the generator to resolve every named schema as a field,
    # including collapsed unions, enums and scalar aliases. It is not shipped.
    schemas["ContractSchemaIndex"] = {
        "type": "object",
        "properties": {
            f"s{i}": {"$ref": f"#/components/schemas/{name}"} for i, name in enumerate(schemas)
        },
        "required": [f"s{i}" for i in range(len(schemas))],
    }
    return result


def generate_models(document: dict[str, Any], temporary: Path) -> str:
    source = temporary / "openapi.json"
    source.write_text(json.dumps(prepare_schema(document)))
    output = temporary / "models.py"
    subprocess.run(  # nosec B603 # Fixed module, local paths, no shell.
        [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(source),
            "--input-file-type",
            "openapi",
            "--output",
            str(output),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.11",
            "--base-class",
            "hubuum_client.models.APIModel",
            "--use-annotated",
            "--use-union-operator",
            "--enum-field-as-literal",
            "all",
            "--disable-timestamp",
            "--collapse-root-models",
            "--use-tag-as-union-variant-name",
            "--snake-case-field",
            "--formatters",
            "builtin",
            "--no-allow-remote-refs",
            "--strict-refs",
        ],
        check=True,
    )
    tree = ast.parse(output.read_text())
    index = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ContractSchemaIndex"
    )
    fields = {
        node.target.id: node.annotation
        for node in index.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    aliases = {name: fields[f"s{i}"] for i, name in enumerate(document["components"]["schemas"])}
    kept = []
    rebuilds = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and (
            node.name == "ContractSchemaIndex"
            or any(
                isinstance(base, ast.Subscript) and ast.unparse(base.value) == "RootModel"
                for base in node.bases
            )
        ):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            rebuilds.append(ast.unparse(node))
        else:
            kept.append(ast.unparse(node))
    declarations = [
        f"{name}: TypeAlias = {ast.unparse(annotation)}"
        for name, annotation in aliases.items()
        if not (isinstance(annotation, ast.Name) and annotation.id == name)
    ]
    text = "\n\n".join(kept)
    text = re.sub(r"\bAny\b", "JsonValue", text)
    text = re.sub(
        r"from typing import ([^\n]+)",
        lambda m: "from typing import " + m.group(1).replace("JsonValue, ", "") + ", TypeAlias",
        text,
    )
    text = text.replace("from pydantic import ", "from pydantic import JsonValue, ")
    # All explicit schema names are public, including aliases eliminated by
    # root-model collapsing. Forward references are rebuilt after the aliases.
    result = re.sub(
        r"\bAny\b",
        "JsonValue",
        HEADER + text + "\n\n" + "\n".join(declarations) + "\n\n" + "\n".join(rebuilds) + "\n",
    )
    # Use a semantic name for the inherited error variant instead of a collision suffix.
    result = re.sub(
        r"\bHistoricalComputedField3\b", "HistoricalComputedFieldEvaluationError", result
    )
    for method, variants in SEARCH_EVENTS.items():
        name = "UnifiedSearchEvent" if method == "get" else "StructuredSearchEvent"
        result += f"\n{name}: TypeAlias = " + " | ".join(variants.values()) + "\n"
    return result


def annotation(  # noqa: PLR0911 -- Separate terminal cases for schema types.
    schema: dict[str, Any], prefix: str = "models."
) -> str:
    if "$ref" in schema:
        return prefix + schema["$ref"].rsplit("/", 1)[1]
    if "enum" in schema:
        return "Literal[" + ", ".join(repr(x) for x in schema["enum"]) + "]"
    for key in ("oneOf", "anyOf"):
        if key in schema:
            return " | ".join(dict.fromkeys(annotation(x, prefix) for x in schema[key]))
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(annotation({**schema, "type": x}, prefix) for x in kind)
    if kind == "array":
        return f"list[{annotation(schema.get('items', {}), prefix)}]"
    if kind == "object":
        return "dict[str, JsonValue]"
    if kind == "string" and schema.get("format") == "date-time":
        return "datetime"
    return {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "null": "None",
    }.get(kind, "JsonValue")


def parameters_model(name: str, parameters: list[dict[str, Any]]) -> str:
    lines = [
        f"class {name}(APIModel):",
        '    """Immutable operation parameters; omitted fields are not sent."""',
    ]
    for param in parameters:
        wire = param["name"]
        field = identifier(wire)
        schema = param["schema"]
        kind = annotation(schema)
        required = param.get("required", False)
        if not required and "None" not in kind:
            kind += " | None"
        arguments = [f"alias={wire!r}"] if wire != field else []
        for key, option in {
            "minimum": "ge",
            "maximum": "le",
            "minLength": "min_length",
            "maxLength": "max_length",
            "pattern": "pattern",
        }.items():
            if key in schema:
                arguments.append(f"{option}={schema[key]!r}")
        if arguments:
            kind = f"Annotated[{kind}, Field({', '.join(arguments)})]"
        lines.append(f"    {field}: {kind}" + ("" if required else " = None"))
    return "\n".join(lines) + "\n"


def operation_name(method: str, path: str, prefix: str) -> str:
    suffix = path.removeprefix(prefix).strip("/")
    if not suffix:
        return {"get": "list", "post": "create", "put": "replace", "patch": "update"}.get(
            method, method
        )
    if re.fullmatch(r"\{[^}]+\}", suffix):
        return {"patch": "update", "put": "replace"}.get(method, method)
    parts = []
    for i, part in enumerate(suffix.split("/")):
        if part.startswith("{"):
            if i == 0 or (parts and parts[-1] == "by_name"):
                continue
            parts.append("object" if part == "{object_id}" else "by_" + part[1:-1])
        else:
            parts.append(part.replace("-", "_"))
    return method + "_" + "_".join(parts)


def generate_services(  # noqa: PLR0912, PLR0915 -- One pass keeps both runtime declarations identical.
    document: dict[str, Any],
) -> dict[str, str]:
    grouped: dict[str, list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    for path, item in document["paths"].items():
        for method, operation in item.items():
            if method in METHODS:
                grouped[operation["tags"][0]].append((method, path, operation))
    imports = """from __future__ import annotations
import builtins
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Literal
from functools import cached_property
from pydantic import JsonValue, TypeAdapter
from hubuum_client.models import APIResponse
from hubuum_client.options import OpenAPIOptions
from hubuum_client.streaming import AsyncTypedResponseStream, TypedResponseStream
from hubuum_client._transport import api_options, api_body, decode_api_response
from . import models, query as controls
if TYPE_CHECKING:
    from hubuum_client.client import Client
    from hubuum_client.async_client import AsyncClient
"""
    outputs = {False: [HEADER, imports], True: [HEADER, imports]}
    queries = [
        HEADER,
        """from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, JsonValue
from hubuum_client.models import APIModel
from . import models
""",
    ]
    coverage: dict[str, dict[str, str]] = {}
    reference = [
        "# Typed operation coverage\n",
        "Generated from the pinned OpenAPI document. Every row is available through\n"
        "both `Client.api` and `AsyncClient.api`; see [typed API usage](typed-api.md).\n",
        "| HTTP method | Route | Typed method |",
        "| --- | --- | --- |",
    ]
    for tag, operations in sorted(grouped.items()):
        split = [path.rstrip("/").split("/") for _, path, _ in operations]
        common = []
        for parts in zip(*split, strict=False):
            if len(set(parts)) != 1:
                break
            common.append(parts[0])
        prefix = "/".join(common)
        # A lone operation still deserves a verb expressing a point read.
        group_name = class_name(tag) + "API"
        used: set[str] = set()
        for asynchronous in (False, True):
            client_type = "AsyncClient" if asynchronous else "Client"
            name = ("Async" if asynchronous else "") + group_name
            outputs[asynchronous].append(
                f"class {name}:\n"
                f"    def __init__(self, client: {client_type}) -> None:\n"
                "        self._client = client\n"
            )
        for method, path, op in operations:
            operation_id = op["operationId"]
            name = operation_name(method, path, prefix)
            if path.endswith("/"):
                name += "_objects"
            if name in used:
                raise ValueError(f"Duplicate method {tag}.{name}")
            used.add(name)
            coverage[operation_id] = {"service": identifier(tag), "method": name}
            reference.append(f"| {method.upper()} | `{path}` | `api.{identifier(tag)}.{name}()` |")
            params = op.get("parameters", [])
            path_args = [p for p in params if p["in"] == "path"]
            args = [f"{identifier(p['name'])}: {annotation(p['schema'])}" for p in path_args]
            path_dict = (
                "{" + ", ".join(f"{p['name']!r}: {identifier(p['name'])}" for p in path_args) + "}"
            )
            keywords = []
            for location in ("query", "header"):
                selected = [p for p in params if p["in"] == location]
                # OpenAPI spells dynamic filter examples with angle brackets;
                # those are supplied using Query.as_params() through options.
                selected = [p for p in selected if "<" not in p["name"]]
                if selected:
                    model_name = (
                        group_name.removesuffix("API")
                        + class_name(name.replace(identifier(tag), ""))
                        + location.capitalize()
                    )
                    queries.append(parameters_model(model_name, selected))
                    required = any(p.get("required") for p in selected)
                    keywords.append(
                        f"{location}: controls.{model_name}"
                        + ("" if required else " | None = None")
                    )
            request_content = op.get("requestBody", {}).get("content", {})
            body_types = {
                media: annotation(value.get("schema", {}))
                for media, value in request_content.items()
            }
            body_union = " | ".join(dict.fromkeys(body_types.values()))
            if body_types:
                optional = not op["requestBody"].get("required", False)
                keywords.insert(0, f"body: {body_union}" + (" | None = None" if optional else ""))
            responses: dict[str, str] = {}
            empty = False
            for status, response in op["responses"].items():
                if status.startswith("2"):
                    if not response.get("content"):
                        empty = True
                    for media, value in response.get("content", {}).items():
                        responses[media] = annotation(value.get("schema", {}))
            streaming = "text/event-stream" in responses
            result_type = " | ".join(dict.fromkeys(responses.values())) or "None"
            if empty and responses:
                result_type += " | None"
            content_type = next(iter(body_types), None)
            accept = next(iter(responses), "application/json")
            if len(body_types) > 1:
                keywords.append(
                    f"content_type: Literal[{', '.join(repr(m) for m in body_types)}]"
                    f" = {content_type!r}"
                )
            if len(responses) > 1:
                keywords.append(
                    f"accept: Literal[{', '.join(repr(m) for m in responses)}] = {accept!r}"
                )
            keywords.append("options: OpenAPIOptions | None = None")
            query_arg = (
                "query"
                if any(p["in"] == "query" and "<" not in p["name"] for p in params)
                else "None"
            )
            header_arg = "header" if any(p["in"] == "header" for p in params) else "None"
            ct_arg = "content_type" if len(body_types) > 1 else repr(content_type)
            accept_arg = "accept" if len(responses) > 1 else repr(accept)
            body_arg = (
                "api_body(body, {"
                + ", ".join(
                    f"{media!r}: TypeAdapter[{body_union}]({kind})"
                    for media, kind in body_types.items()
                )
                + "}, content_type=prepared.content_type, "
                + f"optional={not op.get('requestBody', {}).get('required', False)!r})"
                if body_types
                else "None"
            )
            for asynchronous in (False, True):
                async_prefix = "async " if asynchronous else ""
                await_prefix = "await " if asynchronous else ""
                stream_class = "AsyncTypedResponseStream" if asynchronous else "TypedResponseStream"
                event_type = "UnifiedSearchEvent" if method == "get" else "StructuredSearchEvent"
                stream_type = f"{stream_class}[models.{event_type}]"
                return_type = (
                    (
                        f"AsyncIterator[{stream_type}]"
                        if asynchronous
                        else f"Iterator[{stream_type}]"
                    )
                    if streaming
                    else f"APIResponse[{result_type}]"
                )
                signature = ", ".join(["self", *args, "*", *keywords])
                lines = []
                if streaming:
                    lines.append(
                        "    @asynccontextmanager" if asynchronous else "    @contextmanager"
                    )
                opening = f"    {async_prefix}def {name}("
                if len(args) + len(keywords) > MAX_ARGUMENTS:
                    opening += "  # noqa: PLR0913 -- One argument per wire location.\n"
                lines += [
                    f"{opening}{signature}) -> {return_type}:",
                    f'        """{method.upper()} operation.\n\n        {path}\n        """',
                    f"        prepared = api_options({operation_id!r}, {path_dict}, "
                    f"{query_arg}, {header_arg}, options, "
                    f"content_type={ct_arg}, accept={accept_arg})",
                ]
                if streaming:
                    adapters = (
                        "{"
                        + ", ".join(
                            f"{event!r}: TypeAdapter[models.{event_type}](models.{schema})"
                            for event, schema in SEARCH_EVENTS[method].items()
                        )
                        + "}"
                    )
                    lines += [
                        f"        {async_prefix}with self._client.openapi.stream("
                        f"{operation_id!r}, json={body_arg}, options=prepared) as stream:",
                        f"            yield {stream_class}(stream, {adapters})",
                    ]
                else:
                    # Reuse the same route/auth/media policy as the raw registry,
                    # but decode the original response through a precise adapter.
                    response_adapters = {
                        **responses,
                        **({"": "None"} if empty or not responses else {}),
                    }
                    adapters = (
                        "{"
                        + ", ".join(
                            f"{media!r}: TypeAdapter[{result_type}]({kind})"
                            for media, kind in response_adapters.items()
                        )
                        + "}"
                    )
                    lines += [
                        f"        response = {await_prefix}self._client.openapi._response("
                        f"{operation_id!r}, json={body_arg}, options=prepared)",
                        f"        return decode_api_response(response, {adapters})",
                    ]
                outputs[asynchronous].append("\n".join(lines) + "\n")
    for asynchronous in (False, True):
        cname = "AsyncAPI" if asynchronous else "API"
        client_type = "AsyncClient" if asynchronous else "Client"
        lines = [
            f"class {cname}:",
            '    """Complete typed resource interface for the pinned server contract."""',
            f"    def __init__(self, client: {client_type}) -> None:",
            "        self._client = client",
        ]
        for tag in sorted(grouped):
            service = ("Async" if asynchronous else "") + class_name(tag) + "API"
            lines += [
                "",
                "    @cached_property",
                f"    def {identifier(tag)}(self) -> {service}:",
                f"        return {service}(self._client)",
            ]
        outputs[asynchronous].append("\n".join(lines) + "\n")
    return {
        "services.py": "\n\n".join(outputs[False]).replace("list[", "builtins.list["),
        "async_services.py": "\n\n".join(outputs[True]).replace("list[", "builtins.list["),
        "query.py": "\n\n".join(queries),
        "operations.json": json.dumps(coverage, indent=2, sort_keys=True) + "\n",
        "typed-operations.md": "\n".join(reference) + "\n",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document = json.loads((ROOT / "docs/openapi.json").read_text())
    with tempfile.TemporaryDirectory(prefix="hubuum-api-") as folder:
        temporary = Path(folder)
        outputs = generate_services(document)
        outputs["models.py"] = generate_models(document, temporary)
        for name, source in outputs.items():
            target = temporary / name
            target.write_text(source)
            if name.endswith(".py"):
                subprocess.run(  # nosec B603 # Fixed formatter and local output path.
                    [sys.executable, "-m", "ruff", "format", str(target)], check=True
                )
                subprocess.run(  # nosec B603 # Fixed module, local paths, no shell.
                    [
                        sys.executable,
                        "-m",
                        "ruff",
                        "check",
                        "--fix",
                        "--select",
                        "I,F",
                        str(target),
                    ],
                    check=True,
                )
                subprocess.run(  # nosec B603 # Fixed formatter and local output path.
                    [sys.executable, "-m", "ruff", "format", str(target)], check=True
                )
            destination = (ROOT / "docs" if name.endswith(".md") else DESTINATION) / name
            if args.check:
                if not destination.exists() or target.read_bytes() != destination.read_bytes():
                    raise SystemExit(f"Stale generated API: {name}; run {Path(__file__).name}")
            else:
                DESTINATION.mkdir(exist_ok=True)
                destination.write_bytes(target.read_bytes())


if __name__ == "__main__":
    main()
