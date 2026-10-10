# Explore the Atlas example inventory

Use the same small inventory as the server documentation and the other Hubuum
interfaces. Atlas demonstrates **classes, objects, relations, and access** with
four classes and ten connected objects.

## Load the shared dataset

Use the [server v0.0.18 Atlas guide](https://hubuum.github.io/hubuum/v0.0.18/getting-started/example-dataset/)
to load the inventory into an evaluation server and grant your account access.
This matches this release's server target. The server guide owns the downloads,
model, permissions, and expected data. Import adds the dataset atomically;
**restoring its backup replaces all application data**.

Use the case-sensitive names `Service`, `Server`, `Location`, and `Context`.
Resolve numeric IDs from responses; they vary between installations.

## Read classes and objects

After [authenticating a client](client.md), inspect the Service class and its
Atlas object:

```python
services = client.classes.by_name("Service")
service_class = services.get()
atlas = services.objects.get("Atlas")
server = client.classes.by_name("Server").objects.get("web-01")
notes = client.classes.by_name("Context").objects.get("Research notes")
```

`atlas.data["owner"]` is `"Platform"`; `server.data["hostname"]` is
`"web-01.example.invalid"`. The notes have a different, schema-free shape.
Names are case-sensitive and encoded by the client, including the space in
Research notes. The async equivalents use the same services and await requests:

```python
services = client.classes.by_name("Service")
service_class = await services.get()
atlas = await services.objects.get("Atlas")
```

Use [querying and pagination](querying.md) to list Server objects. The starting
inventory contains three: web-01, web-02, and worker-01. Prefer name selectors or
resolve IDs from returned resources; importing does not preserve database IDs.

## Relations and access

Use a non-admin account in `atlas-readers` to read the full inventory, or one
in `atlas-operators` to maintain Server/Location objects in the operations child.
Other memberships and token scopes affect the result. See the canonical
[relationships](https://hubuum.github.io/hubuum/v0.0.18/getting-started/example-dataset/#relations-connect-the-instances)
and [permission checks](https://hubuum.github.io/hubuum/v0.0.18/getting-started/example-dataset/#explore-collection-permissions)
for expected results and cleanup.
