"""Small typed values shared by the public API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

CollectionId = NewType("CollectionId", int)
ClassId = NewType("ClassId", int)
ObjectId = NewType("ObjectId", int)
ClassRelationId = NewType("ClassRelationId", int)
ObjectRelationId = NewType("ObjectRelationId", int)
UserId = NewType("UserId", int)
GroupId = NewType("GroupId", int)
PrincipalId = NewType("PrincipalId", int)
TaskId = NewType("TaskId", int)
TokenId = NewType("TokenId", int)


@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    """Login credentials with a redacted representation."""

    name: str
    password: str
    identity_scope: str | None = None

    def __repr__(self) -> str:
        return (
            f"Credentials(name={self.name!r}, password=<redacted>, "
            f"identity_scope={self.identity_scope!r})"
        )

    def as_payload(self) -> dict[str, str]:
        payload = {"name": self.name, "password": self.password}
        if self.identity_scope is not None:
            payload["identity_scope"] = self.identity_scope
        return payload


@dataclass(frozen=True, slots=True, repr=False)
class AccessToken:
    """Bearer token and optional authoritative expiry with a redacted representation."""

    value: str
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("access token must not be empty")
        object.__setattr__(self, "value", normalized)

    def __repr__(self) -> str:
        return "AccessToken(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"


class FilterOperator(StrEnum):
    """Operators understood by Hubuum's ``field__operator=value`` syntax."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IEQUALS = "iequals"
    NOT_IEQUALS = "not_iequals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    ICONTAINS = "icontains"
    NOT_ICONTAINS = "not_icontains"
    STARTSWITH = "startswith"
    NOT_STARTSWITH = "not_startswith"
    ISTARTSWITH = "istartswith"
    NOT_ISTARTSWITH = "not_istartswith"
    ENDSWITH = "endswith"
    NOT_ENDSWITH = "not_endswith"
    IENDSWITH = "iendswith"
    NOT_IENDSWITH = "not_iendswith"
    LIKE = "like"
    NOT_LIKE = "not_like"
    REGEX = "regex"
    NOT_REGEX = "not_regex"
    GT = "gt"
    NOT_GT = "not_gt"
    GTE = "gte"
    NOT_GTE = "not_gte"
    LT = "lt"
    NOT_LT = "not_lt"
    LTE = "lte"
    NOT_LTE = "not_lte"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    IN = "in"
    NOT_IN = "not_in"
    ALL = "all"
    NOT_ALL = "not_all"
    ARRAY_LENGTH = "array_length"
    NOT_ARRAY_LENGTH = "not_array_length"
    HAS_KEY = "has_key"
    NOT_HAS_KEY = "not_has_key"
    IS_NULL = "is_null"
    NOT_IS_NULL = "not_is_null"
    WITHIN_NETWORK = "within_network"
    NOT_WITHIN_NETWORK = "not_within_network"
    CONTAINS_NETWORK = "contains_network"
    NOT_CONTAINS_NETWORK = "not_contains_network"
    CONTAINS_IP = "contains_ip"
    NOT_CONTAINS_IP = "not_contains_ip"
    OVERLAPS_NETWORK = "overlaps_network"
    NOT_OVERLAPS_NETWORK = "not_overlaps_network"
    INET_EQUALS = "inet_equals"
    NOT_INET_EQUALS = "not_inet_equals"


QueryValue = str | int | float | bool
