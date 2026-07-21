"""Shared HTTP safety, decoding, and error helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from urllib.parse import unquote, urlsplit

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

T = TypeVar("T", bound=BaseModel)


def normalize_base_url(value: str) -> str:
    """Validate and normalize the caller-supplied server base URL."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("base_url must be an absolute http or https URL")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("base_url must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ConfigurationError("base_url must not contain a query string or fragment")
    return value.rstrip("/") + "/"


def validate_relative_path(path: str) -> str:
    """Reject origins and traversal before a relative API route reaches httpx."""
    parsed = urlsplit(path)
    if not path.startswith("/") or path.startswith("//") or parsed.scheme or parsed.netloc:
        raise ConfigurationError("API path must be an absolute-path reference on the server")
    decoded_segments = unquote(parsed.path).split("/")
    if any(segment in {".", ".."} for segment in decoded_segments):
        raise ConfigurationError("API path must not contain traversal segments")
    if parsed.query or parsed.fragment:
        raise ConfigurationError("pass query parameters through params, not in the API path")
    return path.removeprefix("/")


def json_body(value: BaseModel | Mapping[str, Any] | list[Any] | None) -> Any:
    if isinstance(value, BaseModel):
        payload_method = getattr(value, "payload", None)
        if callable(payload_method):
            return payload_method()
        return value.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return value


def safe_response_url(response: httpx.Response) -> str:
    return str(response.request.url.copy_with(query=None, fragment=None))


def raise_api_error(response: httpx.Response) -> None:
    """Map a failed HTTP response onto the public exception hierarchy."""
    if response.is_success:
        return

    body: Any
    error: str | None = None
    message: str | None = None
    try:
        body = response.json()
        if isinstance(body, dict):
            raw_error = body.get("error")
            raw_message = body.get("message")
            error = raw_error if isinstance(raw_error, str) else None
            message = raw_message if isinstance(raw_message, str) else None
    except ValueError:
        body = response.text

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
        request_id=response.headers.get("x-request-id"),
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
            reason=str(error),
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
