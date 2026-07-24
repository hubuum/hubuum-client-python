# Querying and pagination

Hubuum filters use `field__operator=value`. The Python client represents them as
immutable `Query` values:

```python
from hubuum_client import FilterOperator, Query

query = (
    Query()
    .where("name", "server", FilterOperator.ICONTAINS)
    .where("validate_schema", True)
    .sort("name.asc")
    .limit(25)
    .include_total()
)
page = client.classes.page(query)
```

Dates and datetimes are encoded as ISO 8601 values. Booleans are encoded as
lowercase JSON-style strings.

## Operators

`FilterOperator` includes equality, case-insensitive equality, containment,
prefix, suffix, SQL-like, regular-expression, comparison, range, membership,
null, JSON structure, and IP/network operators, along with each operator's
negated form. The server validates whether an operator is legal for a
particular field.

## Object data

Use `data()` to select a key path inside an object's JSON `data` document. A
terminal filter returns a new immutable `Query`, so filters compose naturally:

```python
query = (
    Query()
    .data("status")
    .equals("active")
    .data("metrics", "cpu_count")
    .gte(4)
    .data("tags")
    .contains_all("web", "api")
)

objects = client.objects(class_id).all(query)
```

The path is passed as one key per argument. For example,
`data("network", "address")` selects `data["network"]["address"]` and encodes
the server value `network,address=...`. Commas and equals signs cannot be used
in path keys because Hubuum v0.0.3 does not define escaping for those
delimiters.

Common scalar and textual filters use direct method names:

```python
from datetime import date

Query().data("hostname").icontains("web")
Query().data("enabled").equals(True)
Query().data("maintenance", "starts_at").between(
    date(2026, 7, 1),
    date(2026, 7, 31),
)
```

Available scalar methods are `equals`, `iequals`, `contains`, `icontains`,
`starts_with`, `istarts_with`, `ends_with`, `iends_with`, `like`, `regex`,
`gt`, `gte`, `lt`, `lte`, and `between`. Booleans use lowercase wire values,
and dates and datetimes use ISO 8601. Set `negate=True` on any terminal to use
the corresponding server `not_` operator.

JSON arrays, objects, and nulls have semantic helpers:

```python
Query().data("status").one_of("active", "standby")
Query().data("tags").contains_all("web", "api")
Query().data("tags").array_length(2)
Query().data("config").has_key("hostname")
Query().data("retired_at").is_null()
Query().data("retired_at").is_null(negate=True)
```

`one_of` matches either a scalar in the supplied set or an array containing at
least one supplied value. `contains_all` requires every supplied array value.
`is_null` matches both a missing path and JSON null, following server semantics.

Network-aware filters accept strings or values from Python's `ipaddress`
module:

```python
from ipaddress import ip_network

Query().data("network", "address").within_network(ip_network("10.0.0.0/24"))
Query().data("network", "address").contains_network("10.0.0.0/25")
Query().data("network", "address").contains_ip("10.0.0.10")
Query().data("network", "address").overlaps_network("10.0.0.64/26")
Query().data("network", "address").inet_equals("10.0.0.10/32")
```

These helpers generate normal `json_data__operator` parameters and work
unchanged with both synchronous and asynchronous object services.

## Result shapes

Resource services expose four common terminals:

- `list(query)` returns the current page's items as a list;
- `page(query)` returns `Page[T]` with items and cursor metadata;
- `all(query)` follows cursors and collects bounded results;
- `one(query)` requires exactly one item and raises
  `ResultCardinalityError` otherwise.

```python
page = client.classes.by_id(class_id).objects.page(
    Query().limit(50).include_total()
)

print(page.total_count)
print(page.page_limit)
if page.has_next:
    next_page = client.classes.by_id(class_id).objects.page(
        Query().cursor(page.next_cursor)
    )
```

`total_count` is `None` when `include_total=False` or the server omits the
header. `page_limit` is the effective server-applied limit.

## Automatic pagination safeguards

```python
items = client.classes.all(query, max_pages=50, max_items=5_000)
```

The client rejects repeated cursors, more than `max_pages`, and more than
`max_items`. Bounds must be positive and are validated before the client makes a
request. The async client provides the same API, and its `pages()` method is an
async iterator.

The default bounds are intentionally conservative. Increase them explicitly for
a known large result set, or consume pages individually when streaming work is
more appropriate.

## Exact-name routes

Hubuum v0.0.3 supports explicit natural-key aliases for classes and objects.
Use the complete name-addressed service when class and object names are already
known:

```python
selected_class = client.classes.by_name("12345")
hubuum_class = selected_class.get()
hubuum_object = selected_class.objects.get("67890")
all_objects = selected_class.objects.all()

id_selected_class = client.classes.by_id(class_id)
same_class = id_selected_class.get()
id_scoped_objects = id_selected_class.objects.all()
```

Both names are encoded as opaque path segments after explicit `by-name`
markers, so spaces, slashes, and numeric-looking values remain unambiguous.
The `client.objects(class_id)` and
`client.objects_by_class_name(class_name)` conveniences remain available for
compatibility. New code should prefer the nested class selectors because they
make the resource hierarchy and ID-versus-name choice explicit.
