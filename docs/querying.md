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
prefix, suffix, SQL-like, regular-expression, comparison, and range operators,
along with each operator's negated form. The server validates whether an
operator is legal for a particular field.

## Result shapes

Resource services expose four common terminals:

- `list(query)` returns the current page's items as a list;
- `page(query)` returns `Page[T]` with items and cursor metadata;
- `all(query)` follows cursors and collects bounded results;
- `one(query)` requires exactly one item and raises
  `ResultCardinalityError` otherwise.

```python
page = client.objects(class_id).page(Query().limit(50).include_total())

print(page.total_count)
print(page.page_limit)
if page.has_next:
    next_page = client.objects(class_id).page(Query().cursor(page.next_cursor))
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

Hubuum v0.0.3 supports natural-key lookup for classes and exact equality lookup
within an ID-scoped class. Use these helpers instead of treating a
numeric-looking name as an ID:

```python
hubuum_class = client.classes.get_by_name("12345")
hubuum_object = client.objects(hubuum_class.id).get_by_name("67890")
```

Class names are encoded as opaque path segments. Object names are encoded as
query values on the valid ID-scoped object collection route, so spaces, slashes,
and numeric-looking values remain unambiguous.
