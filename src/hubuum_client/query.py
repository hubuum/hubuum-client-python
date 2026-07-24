"""Immutable filtering and cursor-pagination helpers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Generic, TypeVar, overload

from .types import FilterOperator, QueryValue

T = TypeVar("T")
FilterValue = QueryValue | date | datetime
NetworkFilterValue = str | IPv4Address | IPv6Address | IPv4Network | IPv6Network
WireValue = FilterValue | NetworkFilterValue


def _wire_value(value: WireValue) -> str:
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
        if not self.field:
            raise ValueError("filter field must not be empty")
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

    def data(self, *path: str) -> DataField:
        """Select a nested object ``data`` field for a fluent JSON filter."""
        return DataField(self, path)

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
class DataField:
    """A nested object ``data`` path selected from an immutable query.

    Each terminal method returns a new :class:`Query`, so another ``data()``
    selection or any normal query control can be chained immediately.
    """

    query: Query
    path: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("data path must contain at least one key")
        if any(not key for key in self.path):
            raise ValueError("data path keys must not be empty")
        if any("," in key or "=" in key for key in self.path):
            raise ValueError("data path keys must not contain ',' or '='")

    @property
    def _path_value(self) -> str:
        return ",".join(self.path)

    @staticmethod
    def _operator(operator: FilterOperator, negate: bool) -> FilterOperator:
        if not negate:
            return operator
        return FilterOperator(f"not_{operator.value}")

    @staticmethod
    def _list_value(values: tuple[FilterValue, ...]) -> str:
        if not values:
            raise ValueError("data filter requires at least one value")
        encoded = tuple(_wire_value(value) for value in values)
        if any("," in value for value in encoded):
            raise ValueError("data list values must not contain ','")
        return ",".join(encoded)

    def _value_filter(
        self,
        operator: FilterOperator,
        value: FilterValue | NetworkFilterValue,
        *,
        negate: bool,
    ) -> Query:
        wire_value = _wire_value(value)
        return self.query.where(
            "json_data",
            f"{self._path_value}={wire_value}",
            self._operator(operator, negate),
        )

    def equals(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a string, number, boolean, date, or datetime value."""
        return self._value_filter(FilterOperator.EQUALS, value, negate=negate)

    def iequals(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value case-insensitively."""
        return self._value_filter(FilterOperator.IEQUALS, value, negate=negate)

    def contains(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value containing ``value``."""
        return self._value_filter(FilterOperator.CONTAINS, value, negate=negate)

    def icontains(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value containing ``value`` case-insensitively."""
        return self._value_filter(FilterOperator.ICONTAINS, value, negate=negate)

    def starts_with(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value starting with ``value``."""
        return self._value_filter(FilterOperator.STARTSWITH, value, negate=negate)

    def istarts_with(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value starting with ``value`` case-insensitively."""
        return self._value_filter(FilterOperator.ISTARTSWITH, value, negate=negate)

    def ends_with(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value ending with ``value``."""
        return self._value_filter(FilterOperator.ENDSWITH, value, negate=negate)

    def iends_with(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value ending with ``value`` case-insensitively."""
        return self._value_filter(FilterOperator.IENDSWITH, value, negate=negate)

    def like(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value with the server's SQL-like semantics."""
        return self._value_filter(FilterOperator.LIKE, value, negate=negate)

    def regex(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a textual value using a PostgreSQL regular expression."""
        return self._value_filter(FilterOperator.REGEX, value, negate=negate)

    def gt(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a number or date greater than ``value``."""
        return self._value_filter(FilterOperator.GT, value, negate=negate)

    def gte(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a number or date greater than or equal to ``value``."""
        return self._value_filter(FilterOperator.GTE, value, negate=negate)

    def lt(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a number or date less than ``value``."""
        return self._value_filter(FilterOperator.LT, value, negate=negate)

    def lte(self, value: FilterValue, *, negate: bool = False) -> Query:
        """Match a number or date less than or equal to ``value``."""
        return self._value_filter(FilterOperator.LTE, value, negate=negate)

    def between(
        self,
        lower: FilterValue,
        upper: FilterValue,
        *,
        negate: bool = False,
    ) -> Query:
        """Match a number or date inside an inclusive range."""
        bounds = self._list_value((lower, upper))
        return self._value_filter(FilterOperator.BETWEEN, bounds, negate=negate)

    def one_of(self, *values: FilterValue, negate: bool = False) -> Query:
        """Match a scalar in ``values`` or an array containing any of them."""
        return self._value_filter(
            FilterOperator.IN,
            self._list_value(values),
            negate=negate,
        )

    def contains_all(self, *values: FilterValue, negate: bool = False) -> Query:
        """Match an array containing every supplied value."""
        return self._value_filter(
            FilterOperator.ALL,
            self._list_value(values),
            negate=negate,
        )

    def array_length(self, value: int, *, negate: bool = False) -> Query:
        """Match an array with exactly ``value`` elements."""
        if value < 0:
            raise ValueError("data array length must not be negative")
        return self._value_filter(FilterOperator.ARRAY_LENGTH, value, negate=negate)

    def has_key(self, key: str, *, negate: bool = False) -> Query:
        """Match an object containing ``key``, including a JSON-null value."""
        if not key:
            raise ValueError("data object key must not be empty")
        return self._value_filter(FilterOperator.HAS_KEY, key, negate=negate)

    def is_null(self, *, negate: bool = False) -> Query:
        """Match a missing or JSON-null path."""
        return self.query.where(
            "json_data",
            self._path_value,
            self._operator(FilterOperator.IS_NULL, negate),
        )

    def within_network(self, value: NetworkFilterValue, *, negate: bool = False) -> Query:
        """Match an IP/network stored inside ``value``."""
        return self._value_filter(FilterOperator.WITHIN_NETWORK, value, negate=negate)

    def contains_network(self, value: NetworkFilterValue, *, negate: bool = False) -> Query:
        """Match a stored network containing ``value``."""
        return self._value_filter(FilterOperator.CONTAINS_NETWORK, value, negate=negate)

    def contains_ip(
        self,
        value: str | IPv4Address | IPv6Address,
        *,
        negate: bool = False,
    ) -> Query:
        """Match a stored network strictly containing the host IP ``value``."""
        return self._value_filter(FilterOperator.CONTAINS_IP, value, negate=negate)

    def overlaps_network(self, value: NetworkFilterValue, *, negate: bool = False) -> Query:
        """Match a stored IP/network overlapping ``value``."""
        return self._value_filter(FilterOperator.OVERLAPS_NETWORK, value, negate=negate)

    def inet_equals(self, value: NetworkFilterValue, *, negate: bool = False) -> Query:
        """Match normalized PostgreSQL ``inet`` equality."""
        return self._value_filter(FilterOperator.INET_EQUALS, value, negate=negate)


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
