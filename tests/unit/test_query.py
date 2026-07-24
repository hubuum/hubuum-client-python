from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from ipaddress import ip_address, ip_network

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


def test_filter_rejects_empty_field_but_allows_computed_keys_with_separator() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        QueryFilter("", FilterOperator.EQUALS, "x").as_pair()

    assert Query().where("computed.shared.owner__label", "ops").as_params() == [
        ("computed.shared.owner__label__equals", "ops")
    ]


def test_data_field_fluent_interface_encodes_the_server_json_grammar() -> None:
    query = Query()
    query = query.data("flags", "enabled").equals(True)
    query = query.data("owner").iequals("OPS", negate=True)
    query = query.data("hostname").contains("srv")
    query = query.data("hostname").icontains("SRV", negate=True)
    query = query.data("hostname").starts_with("web")
    query = query.data("hostname").istarts_with("WEB", negate=True)
    query = query.data("hostname").ends_with(".test")
    query = query.data("hostname").iends_with(".TEST", negate=True)
    query = query.data("hostname").like("edge%")
    query = query.data("hostname").regex("^edge-", negate=True)
    query = query.data("metrics", "cpu_count").gt(2)
    query = query.data("metrics", "cpu_count").gte(4, negate=True)
    query = query.data("metrics", "cpu_count").lt(32)
    query = query.data("metrics", "cpu_count").lte(16, negate=True)
    query = query.data("maintenance", "date").between(date(2026, 7, 1), date(2026, 7, 31))
    query = query.data("status").one_of("active", "standby", negate=True)
    query = query.data("tags").contains_all("web", "api")
    query = query.data("tags").array_length(2, negate=True)
    query = query.data("config").has_key("hostname")
    query = query.data("retired_at").is_null(negate=True)
    query = query.data("network", "address").within_network(ip_network("10.0.0.0/24"))
    query = query.data("network", "address").contains_network("10.0.0.0/25", negate=True)
    query = query.data("network", "address").contains_ip(ip_address("10.0.0.10"))
    query = query.data("network", "address").overlaps_network("10.0.0.64/26", negate=True)
    query = query.data("network", "address").inet_equals("10.0.0.10/32")

    assert query.as_params() == [
        ("json_data__equals", "flags,enabled=true"),
        ("json_data__not_iequals", "owner=OPS"),
        ("json_data__contains", "hostname=srv"),
        ("json_data__not_icontains", "hostname=SRV"),
        ("json_data__startswith", "hostname=web"),
        ("json_data__not_istartswith", "hostname=WEB"),
        ("json_data__endswith", "hostname=.test"),
        ("json_data__not_iendswith", "hostname=.TEST"),
        ("json_data__like", "hostname=edge%"),
        ("json_data__not_regex", "hostname=^edge-"),
        ("json_data__gt", "metrics,cpu_count=2"),
        ("json_data__not_gte", "metrics,cpu_count=4"),
        ("json_data__lt", "metrics,cpu_count=32"),
        ("json_data__not_lte", "metrics,cpu_count=16"),
        ("json_data__between", "maintenance,date=2026-07-01,2026-07-31"),
        ("json_data__not_in", "status=active,standby"),
        ("json_data__all", "tags=web,api"),
        ("json_data__not_array_length", "tags=2"),
        ("json_data__has_key", "config=hostname"),
        ("json_data__not_is_null", "retired_at"),
        ("json_data__within_network", "network,address=10.0.0.0/24"),
        ("json_data__not_contains_network", "network,address=10.0.0.0/25"),
        ("json_data__contains_ip", "network,address=10.0.0.10"),
        ("json_data__not_overlaps_network", "network,address=10.0.0.64/26"),
        ("json_data__inet_equals", "network,address=10.0.0.10/32"),
    ]


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (lambda: Query().data(), "at least one"),
        (lambda: Query().data(""), "must not be empty"),
        (lambda: Query().data("network,address"), "must not contain"),
        (lambda: Query().data("network=address"), "must not contain"),
        (lambda: Query().data("status").one_of(), "at least one"),
        (lambda: Query().data("status").one_of("active,standby"), "must not contain"),
        (lambda: Query().data("tags").array_length(-1), "must not be negative"),
        (lambda: Query().data("config").has_key(""), "must not be empty"),
    ],
)
def test_data_field_rejects_values_the_server_grammar_cannot_encode(
    operation: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        operation()


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
