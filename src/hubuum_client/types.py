"""Small typed values shared by the public API."""

from __future__ import annotations

from dataclasses import dataclass
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
    """Bearer token that cannot be exposed through ``repr`` or ``str``."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("access token must not be empty")

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


QueryValue = str | int | float | bool
