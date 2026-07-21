"""Typed client and request configuration objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

import httpx

ParamValue: TypeAlias = str | int | float | bool | None
Params: TypeAlias = (
    Mapping[str, ParamValue | Sequence[ParamValue]]
    | list[tuple[str, ParamValue]]
    | tuple[tuple[str, ParamValue], ...]
    | str
    | bytes
    | None
)


@dataclass(frozen=True, slots=True)
class ClientOptions:
    """Connection behavior shared by synchronous and asynchronous clients."""

    timeout: float | httpx.Timeout = 30.0
    verify: bool | str = True
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class RequestOptions:
    """Transport controls for one origin-locked request."""

    params: Params = None
    headers: Mapping[str, str] | None = None
    authenticated: bool = True
