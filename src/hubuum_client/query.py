"""Immutable filtering and cursor-pagination helpers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Generic, TypeVar, overload

from .types import FilterOperator, QueryValue

T = TypeVar("T")
FilterValue = QueryValue | date | datetime


def _wire_value(value: FilterValue) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


@dataclass(frozen=True, slots=True)
class QueryFilter:
    """One typed Hubuum resource filter."""

    field: str
    operator: FilterOperator
    value: FilterValue

    def as_pair(self) -> tuple[str, str]:
        if not self.field or "__" in self.field:
            raise ValueError("filter field must be a non-empty bare field name")
        return f"{self.field}__{self.operator.value}", _wire_value(self.value)


@dataclass(frozen=True, slots=True)
class Query:
    """Immutable query parameters for list endpoints.

    Reusing a base query is safe because every fluent method returns a new value.
    """

    filters: tuple[QueryFilter, ...] = ()
    limit_value: int | None = None
    cursor_value: str | None = None
    sort_value: str | None = None
    include_total_value: bool | None = None

    def where(
        self,
        field: str,
        value: FilterValue,
        operator: FilterOperator = FilterOperator.EQUALS,
    ) -> Query:
        return replace(self, filters=(*self.filters, QueryFilter(field, operator, value)))

    def limit(self, value: int) -> Query:
        if value < 1:
            raise ValueError("limit must be at least 1")
        return replace(self, limit_value=value)

    def cursor(self, value: str | None) -> Query:
        return replace(self, cursor_value=value)

    def sort(self, value: str) -> Query:
        if not value.strip():
            raise ValueError("sort must not be empty")
        return replace(self, sort_value=value)

    def include_total(self, value: bool = True) -> Query:
        return replace(self, include_total_value=value)

    def as_params(self) -> list[tuple[str, QueryValue | None]]:
        params: list[tuple[str, QueryValue | None]] = [item.as_pair() for item in self.filters]
        if self.limit_value is not None:
            params.append(("limit", str(self.limit_value)))
        if self.cursor_value is not None:
            params.append(("cursor", self.cursor_value))
        if self.sort_value is not None:
            params.append(("sort", self.sort_value))
        if self.include_total_value is not None:
            params.append(("include_total", _wire_value(self.include_total_value)))
        return params


@dataclass(frozen=True, slots=True)
class Page(Sequence[T], Generic[T]):
    """One cursor-paginated response page."""

    items: tuple[T, ...]
    next_cursor: str | None = None
    total_count: int | None = None
    page_limit: int | None = None

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[T, ...]: ...

    def __getitem__(self, index: int | slice) -> T | tuple[T, ...]:
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    @property
    def has_next(self) -> bool:
        return self.next_cursor is not None
