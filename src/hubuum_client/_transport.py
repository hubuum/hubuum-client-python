"""Shared HTTP safety, decoding, and error helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import suppress
from typing import Any, TypeVar
from urllib.parse import quote_plus, unquote, urlsplit

import httpx
from pydantic import BaseModel, ValidationError

from .errors import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    DecodeError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from .options import Params

T = TypeVar("T", bound=BaseModel)
_REDACTED = "<redacted>"
_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "passwd",
    "secret",
    "token",
)
_MAX_PATH_DECODING_PASSES = 8
_ASCII_CONTROL_END = 32
_ASCII_DELETE = 127
_MAX_PORT = 65_535


def _reject_ambiguous_characters(value: str, *, label: str) -> None:
    if "\\" in value or any(
        ord(character) < _ASCII_CONTROL_END or ord(character) == _ASCII_DELETE
        for character in value
    ):
        raise ConfigurationError(f"{label} must not contain backslashes or control characters")


def _validate_url_path(path: str, *, label: str) -> None:
    """Reject traversal and ambiguous path syntax through repeated decoding."""
    decoded = path
    for _ in range(_MAX_PATH_DECODING_PASSES):
        _reject_ambiguous_characters(decoded, label=label)
        if any(segment in {".", ".."} for segment in decoded.split("/")):
            raise ConfigurationError(f"{label} must not contain traversal segments")
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            return
        decoded = next_decoded
    raise ConfigurationError(f"{label} contains excessive nested URL encoding")


def normalize_base_url(value: str) -> str:
    """Validate and normalize the caller-supplied server base URL."""
    _reject_ambiguous_characters(value, label="base_url")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("base_url must be an absolute http or https URL")
    try:
        port = parsed.port
    except ValueError as error:
        raise ConfigurationError("base_url contains an invalid port") from error
    if parsed.hostname is None or (port is not None and not 1 <= port <= _MAX_PORT):
        raise ConfigurationError("base_url must contain a valid host and port")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("base_url must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ConfigurationError("base_url must not contain a query string or fragment")
    _validate_url_path(parsed.path, label="base_url path")
    return value.rstrip("/") + "/"


def validate_relative_path(path: str) -> str:
    """Reject origins and traversal before a relative API route reaches httpx."""
    _reject_ambiguous_characters(path, label="API path")
    parsed = urlsplit(path)
    if not path.startswith("/") or path.startswith("//") or parsed.scheme or parsed.netloc:
        raise ConfigurationError("API path must be an absolute-path reference on the server")
    _validate_url_path(parsed.path, label="API path")
    if parsed.query or parsed.fragment:
        raise ConfigurationError(
            "pass query parameters through RequestOptions(params=...), not in the API path"
        )
    return path.removeprefix("/")


def prepare_request_headers(
    headers: Mapping[str, str] | None, bearer_token: str | None
) -> httpx.Headers:
    """Build case-insensitive headers without allowing origin authority changes."""
    prepared = httpx.Headers(headers)
    if "host" in prepared:
        raise ConfigurationError(
            "the Host header is derived from base_url and cannot be overridden"
        )
    if bearer_token is not None:
        prepared["Authorization"] = f"Bearer {bearer_token}"
    return prepared


def json_body(value: BaseModel | Mapping[str, Any] | list[Any] | None) -> Any:
    if isinstance(value, BaseModel):
        payload_method = getattr(value, "payload", None)
        if callable(payload_method):
            return payload_method()
        return value.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return value


def _sensitive_key(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.casefold().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _collect_sensitive_values(value: Any, result: set[str], *, sensitive: bool = False) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _collect_sensitive_values(item, result, sensitive=_sensitive_key(key))
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_sensitive_values(item, result, sensitive=sensitive)
    elif sensitive and isinstance(value, str) and value:
        result.add(value)


def sensitive_request_values(
    headers: httpx.Headers,
    body: Any,
    params: Params = None,
) -> set[str]:
    """Return exact secret strings that must never survive into an exception."""
    result: set[str] = set()
    for name, value in headers.multi_items():
        if _sensitive_key(name) and value:
            result.add(value)
            scheme, separator, credential = value.partition(" ")
            if separator and scheme.casefold() in {"basic", "bearer"} and credential:
                result.add(credential)
    for name, value in httpx.QueryParams(params).multi_items():
        if _sensitive_key(name) and value:
            result.add(value)
            result.add(quote_plus(value, safe=""))
    _collect_sensitive_values(body, result)
    return result


def redact_text(value: str, secrets: set[str]) -> str:
    """Redact known request secrets from diagnostic text."""
    for secret in sorted(secrets, key=len, reverse=True):
        value = value.replace(secret, _REDACTED)
    return value


def _redact_sensitive_data(value: Any, secrets: set[str]) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _REDACTED if _sensitive_key(key) else _redact_sensitive_data(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_data(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_sensitive_data(item, secrets) for item in value)
    if isinstance(value, str):
        return redact_text(value, secrets)
    return value


def _response_request_secrets(response: httpx.Response) -> set[str]:
    request = response.request
    body: Any = None
    with suppress(UnicodeDecodeError, ValueError):
        body = json.loads(request.content) if request.content else None
    return sensitive_request_values(request.headers, body, request.url.params)


def validation_error_reason(error: TypeError | ValueError, response: httpx.Response) -> str:
    """Format decoding failures without retaining rejected input values."""
    if isinstance(error, ValidationError):
        reason = json.dumps(error.errors(include_input=False, include_url=False), default=str)
    else:
        reason = str(error)
    return redact_text(reason, _response_request_secrets(response))


def safe_response_url(response: httpx.Response) -> str:
    return str(response.request.url.copy_with(query=None, fragment=None))


def raise_api_error(response: httpx.Response) -> None:
    """Map a failed HTTP response onto the public exception hierarchy."""
    if response.is_success:
        return

    body: Any
    error: str | None = None
    message: str | None = None
    secrets = _response_request_secrets(response)
    try:
        body = _redact_sensitive_data(response.json(), secrets)
        if isinstance(body, dict):
            raw_error = body.get("error")
            raw_message = body.get("message")
            error = raw_error if isinstance(raw_error, str) else None
            message = raw_message if isinstance(raw_message, str) else None
    except ValueError:
        body = redact_text(response.text, secrets)

    error_type: type[APIError]
    error_type = {
        401: AuthenticationError,
        403: PermissionDeniedError,
        404: NotFoundError,
        409: ConflictError,
        429: RateLimitError,
    }.get(response.status_code, APIError)
    api_error = error_type(
        method=response.request.method,
        url=safe_response_url(response),
        status_code=response.status_code,
        error=error,
        message=message,
        response_body=body,
        request_id=redact_text(response.headers.get("x-request-id", ""), secrets) or None,
    )
    if isinstance(api_error, RateLimitError):
        try:
            api_error.retry_after = float(response.headers["retry-after"])
        except (KeyError, ValueError):
            api_error.retry_after = None
    raise api_error


def decode_model(response: httpx.Response, model: type[T]) -> T:
    try:
        return model.model_validate(response.json())
    except (ValueError, ValidationError) as error:
        raise DecodeError(
            method=response.request.method,
            url=safe_response_url(response),
            status_code=response.status_code,
            reason=validation_error_reason(error, response),
        ) from error


def decode_json(response: httpx.Response) -> Any:
    if response.status_code in {204, 205} or not response.content:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise DecodeError(
            method=response.request.method,
            url=safe_response_url(response),
            status_code=response.status_code,
            reason=str(error),
        ) from error
