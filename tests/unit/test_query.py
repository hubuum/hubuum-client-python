from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from hubuum_client import FilterOperator, Page, Query, QueryFilter


def test_query_is_immutable_and_encodes_supported_values() -> None:
    base = Query().where("name", "Web & DB", FilterOperator.ICONTAINS)
    query = (
        base.where("enabled", True)
        .where("created_at", datetime(2026, 7, 21, tzinfo=UTC), FilterOperator.GTE)
        .where("day", date(2026, 7, 21))
        .limit(25)
        .cursor("opaque+/=")
        .sort("name.asc")
        .include_total(False)
    )

    assert base.as_params() == [("name__icontains", "Web & DB")]
    assert query.as_params() == [
        ("name__icontains", "Web & DB"),
        ("enabled__equals", "true"),
        ("created_at__gte", "2026-07-21T00:00:00+00:00"),
        ("day__equals", "2026-07-21"),
        ("limit", "25"),
        ("cursor", "opaque+/="),
        ("sort", "name.asc"),
        ("include_total", "false"),
    ]


@pytest.mark.parametrize("field", ["", "name__equals"])
def test_filter_rejects_invalid_field(field: str) -> None:
    with pytest.raises(ValueError, match="bare field"):
        QueryFilter(field, FilterOperator.EQUALS, "x").as_pair()


def test_query_rejects_invalid_controls() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        Query().limit(0)
    with pytest.raises(ValueError, match="must not be empty"):
        Query().sort("  ")


def test_page_is_a_sequence_with_metadata() -> None:
    page = Page(items=("one", "two"), next_cursor="next", total_count=7, page_limit=2)

    assert list(page) == ["one", "two"]
    assert page[0] == "one"
    assert page[:] == ("one", "two")
    assert len(page) == 2
    assert page.has_next
    assert not Page(items=()).has_next
