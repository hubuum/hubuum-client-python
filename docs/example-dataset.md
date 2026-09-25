# Explore the Atlas example inventory

Use the same small inventory as the server documentation and the other Hubuum
interfaces. Atlas demonstrates **classes, objects, relations, and access** with
four classes and ten connected objects.

## Load the shared dataset

Follow the server's [Atlas dataset guide](https://hubuum.github.io/hubuum/main/getting-started/example-dataset/)
to download and import the inventory into an evaluation server. Atlas is initially
available in the explicitly selected development edition. When a server release
includes it, use that release's documentation and downloads. Pin a release or
exact server commit for repeatable tests; do not copy a second fixture into this
repository.

The import aborts atomically on name collisions and contains no passwords,
tokens, users, or group memberships. Its separate backup replaces all application
data and is intended for resetting a disposable demo installation. The server
guide owns the loading, restore, compatibility, and checksum instructions.

| Class | Objects to explore | Schema and authority |
| --- | --- | --- |
| Service | Atlas, Beacon | Enforced schema; maintained in Hubuum |
| Server | web-01, web-02, worker-01 | Enforced schema; reference inventory data |
| Location | Oslo, Bergen | Schema-free; reference facilities data |
| Context | Research notes, Migration checklist, Capacity observation | Schema-free; locally maintained notes and an upstream observation |

A class defines a resource type and its schema policy. Its objects hold the
individual JSON records. Source ownership is independent of schema policy:
`data.source` is example metadata, not automatic synchronization or write
protection.

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

Atlas runs on web-01 and web-02; their locations are Oslo and Bergen. Atlas
also links to Research notes and Migration checklist. Class relations define
which resource types connect; object relations connect these specific instances.

The example creates empty atlas-readers and atlas-operators groups. A principal
assigned only to atlas-readers can read all ten objects without changing them.
A principal assigned only to atlas-operators can read and maintain the five
Server/Location objects in atlas-demo-operations, but cannot read the service
catalogue in its parent collection. Test these differences with non-admin
accounts and an unscoped token; other memberships and token scopes affect access.

For exact data, expected relationships, and checksums, return to the server's
[canonical dataset guide](https://hubuum.github.io/hubuum/main/getting-started/example-dataset/).
The server corpus tests verify import and restore, schemas, permissions,
computed values, filters, and pagination. Each client retains its own compatibility
and integration tests; the example does not change its supported server target.
