from __future__ import annotations

from contextlib import suppress
from datetime import datetime

import pytest

from hubuum_client import (
    APIError,
    AsyncClient,
    AuthenticationError,
    ClassCreate,
    ClassRelationCreate,
    ClassUpdate,
    Client,
    CollectionCreate,
    CollectionUpdate,
    ConflictError,
    Credentials,
    ExportJsonResponse,
    ExportRequest,
    ExportScope,
    ExportScopeKind,
    GroupCreate,
    GroupId,
    HubuumObject,
    ImportCollectionInput,
    ImportGraph,
    ImportRequest,
    NewTokenRequest,
    NotFoundError,
    ObjectCreate,
    ObjectRelationCreate,
    ObjectUpdate,
    OpenAPIOptions,
    Permission,
    PermissionDeniedError,
    PrincipalId,
    Query,
    RestoreTimestamps,
    TaskStatus,
    TokenListState,
    TokenResourceKind,
    TokenResourceScope,
    TokenScope,
    UserCreate,
)

pytestmark = pytest.mark.e2e


def test_public_config_authentication_and_core_crud(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    public = Client(client.base_url)
    try:
        assert public.healthz().status
        assert "# HELP" in public.metrics()
        config = public.config()
        assert config.authentication.default_token_lifetime_hours > 0
        assert (
            config.authentication.max_token_lifetime_hours
            >= config.authentication.default_token_lifetime_hours
        )
        assert config.pagination.default_page_limit > 0
        assert client.token is not None
        assert client.token.expires_at is not None
    finally:
        public.close()

    collection = client.collections.create(
        CollectionCreate(
            name=f"{unique_name}-collection",
            description="Python e2e collection",
            group_id=admin_group_id,
        )
    )
    hubuum_class = None
    hubuum_object = None
    try:
        assert collection.revision > 0
        numeric_name = str(int(unique_name.rsplit("-", 1)[-1], 16))
        hubuum_class = client.classes.create(
            ClassCreate(
                name=numeric_name,
                collection_id=collection.id,
                description="Python e2e class",
            )
        )
        assert hubuum_class.revision > 0
        assert client.classes.get_by_name(numeric_name).id == hubuum_class.id

        hubuum_object = client.classes.by_id(hubuum_class.id).objects.create(
            ObjectCreate(
                name=f"{unique_name}-object",
                collection_id=collection.id,
                hubuum_class_id=hubuum_class.id,
                description="Python e2e object",
                data={"source": "hubuum-client-python"},
            )
        )
        assert hubuum_object.revision > 0
        updated = client.classes.by_id(hubuum_class.id).objects.update(
            hubuum_object.id,
            ObjectUpdate(description="Updated from Python", data={"updated": True}),
        )
        assert updated.data == {"updated": True}
        assert (
            client.classes.by_id(hubuum_class.id).objects.get_by_name(hubuum_object.name).id
            == hubuum_object.id
        )

        page = client.classes.by_id(hubuum_class.id).objects.page(
            Query().where("name", hubuum_object.name).limit(5).include_total()
        )
        assert any(item.id == hubuum_object.id for item in page)

        renamed = client.classes.update(
            hubuum_class.id, ClassUpdate(description="Updated Python e2e class")
        )
        assert renamed.description == "Updated Python e2e class"
    finally:
        if hubuum_object is not None and hubuum_class is not None:
            client.classes.by_id(hubuum_class.id).objects.delete(hubuum_object.id)
        if hubuum_class is not None:
            client.classes.delete(hubuum_class.id)
        client.collections.delete(collection.id)


def test_v009_principal_settings_json_patch(client: Client, unique_name: str) -> None:
    key = f"python_e2e_{unique_name.rsplit('-', 1)[-1]}"
    path = f"/{key}"
    try:
        merged = client.openapi.call("patchApiV1IamMeSettings", json={key: "light"})
        assert isinstance(merged, dict)
        assert merged["settings"][key] == "light"
        patched = client.openapi.call(
            "patchApiV1IamMeSettings",
            json=[
                {"op": "test", "path": path, "value": "light"},
                {"op": "replace", "path": path, "value": "dark"},
            ],
            options=OpenAPIOptions(content_type="application/json-patch+json"),
        )
        assert isinstance(patched, dict)
        assert patched["settings"][key] == "dark"
    finally:
        with suppress(APIError):
            client.openapi.call(
                "patchApiV1IamMeSettings",
                json=[{"op": "remove", "path": path}],
                options=OpenAPIOptions(content_type="application/json-patch+json"),
            )


def test_object_data_query_interface(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    collection = client.collections.create(
        CollectionCreate(
            name=f"{unique_name}-data-query-collection",
            description="Object data query e2e collection",
            group_id=admin_group_id,
        )
    )
    hubuum_class = None
    objects: list[HubuumObject] = []
    try:
        hubuum_class = client.classes.create(
            ClassCreate(
                name=f"{unique_name}-data-query-class",
                collection_id=collection.id,
                description="Object data query e2e class",
            )
        )
        fixtures = (
            (
                "active",
                {
                    "status": "active",
                    "metrics": {"cpu_count": 8},
                    "tags": ["web", "api"],
                    "config": {"hostname": "web-01"},
                    "network": {"address": "10.0.0.10"},
                },
            ),
            (
                "standby",
                {
                    "status": "standby",
                    "metrics": {"cpu_count": 4},
                    "tags": ["web"],
                    "config": {},
                    "network": {"address": "10.0.1.10"},
                },
            ),
            (
                "retired",
                {
                    "status": "retired",
                    "metrics": {"cpu_count": 2},
                    "tags": ["db"],
                    "config": {"hostname": "db-01"},
                    "network": {"address": "192.0.2.10"},
                    "retired_at": "2026-07-01",
                },
            ),
        )
        for suffix, data in fixtures:
            objects.append(
                client.classes.by_id(hubuum_class.id).objects.create(
                    ObjectCreate(
                        name=f"{unique_name}-data-{suffix}",
                        collection_id=collection.id,
                        hubuum_class_id=hubuum_class.id,
                        description=f"Object data query fixture {suffix}",
                        data=data,
                    )
                )
            )

        named_objects = client.classes.by_name(hubuum_class.name).objects
        assert named_objects.get(objects[0].name).id == objects[0].id
        patched = named_objects.patch_data(
            objects[0].name,
            [{"op": "add", "path": "/verified_by_name", "value": True}],
        )
        assert isinstance(patched.data, dict)
        assert patched.data["verified_by_name"] is True

        def selected_names(query: Query) -> set[str]:
            return {item.name for item in client.classes.by_id(hubuum_class.id).objects.all(query)}

        names = {suffix: f"{unique_name}-data-{suffix}" for suffix, _ in fixtures}
        assert selected_names(Query().data("status").equals("active")) == {names["active"]}
        assert selected_names(Query().data("metrics", "cpu_count").gte(4)) == {
            names["active"],
            names["standby"],
        }
        assert selected_names(Query().data("status").one_of("active", "standby")) == {
            names["active"],
            names["standby"],
        }
        assert selected_names(Query().data("tags").contains_all("web", "api")) == {names["active"]}
        assert selected_names(Query().data("config").has_key("hostname")) == {
            names["active"],
            names["retired"],
        }
        assert selected_names(Query().data("retired_at").is_null(negate=True)) == {names["retired"]}
        assert {
            item.name for item in named_objects.all(Query().data("verified_by_name").equals(True))
        } == {names["active"]}
        assert selected_names(Query().data("network", "address").within_network("10.0.0.0/24")) == {
            names["active"]
        }
        assert selected_names(
            Query().data("status").equals("active").data("tags").array_length(2)
        ) == {names["active"]}
    finally:
        if hubuum_class is not None:
            for hubuum_object in reversed(objects):
                client.classes.by_id(hubuum_class.id).objects.delete(hubuum_object.id)
            client.classes.delete(hubuum_class.id)
        client.collections.delete(collection.id)


def test_cursor_pagination_traverses_all_pages(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    collection = client.collections.create(
        CollectionCreate(
            name=f"{unique_name}-pagination-collection",
            description="Cursor pagination e2e collection",
            group_id=admin_group_id,
        )
    )
    hubuum_class = None
    objects: list[HubuumObject] = []
    try:
        hubuum_class = client.classes.create(
            ClassCreate(
                name=f"{unique_name}-pagination-class",
                collection_id=collection.id,
                description="Cursor pagination e2e class",
            )
        )
        object_service = client.classes.by_id(hubuum_class.id).objects
        objects.extend(
            object_service.create(
                ObjectCreate(
                    name=f"{unique_name}-pagination-{index}",
                    collection_id=collection.id,
                    hubuum_class_id=hubuum_class.id,
                    description=f"Cursor pagination fixture {index}",
                    data={"index": index},
                )
            )
            for index in range(3)
        )

        query = Query().limit(1).sort("id.asc").include_total()
        pages = list(object_service.pages(query))

        assert [len(page) for page in pages] == [1, 1, 1]
        assert [page.total_count for page in pages] == [3, 3, 3]
        assert [page.page_limit for page in pages] == [1, 1, 1]
        assert [page.has_next for page in pages] == [True, True, False]
        assert len({page.next_cursor for page in pages[:-1]}) == 2
        assert [item.id for page in pages for item in page] == [item.id for item in objects]
        assert [item.id for item in object_service.all(query)] == [item.id for item in objects]
    finally:
        if hubuum_class is not None:
            for hubuum_object in reversed(objects):
                client.classes.by_id(hubuum_class.id).objects.delete(hubuum_object.id)
            client.classes.delete(hubuum_class.id)
        client.collections.delete(collection.id)


def test_iam_and_relations(client: Client, admin_group_id: GroupId, unique_name: str) -> None:
    user = client.users.create(
        UserCreate(
            name=f"{unique_name}-user",
            password=f"{unique_name}-Passw0rd!",
            email=f"{unique_name}@example.test",
        )
    )
    group = client.groups.create(
        GroupCreate(groupname=f"{unique_name}-group", description="Python e2e group")
    )
    collections = []
    classes = []
    objects: list[HubuumObject] = []
    class_relation = None
    object_relation = None
    extra_to_object = None
    try:
        added = client.groups.add_member(group.id, PrincipalId(user.id))
        assert added.revision > 0
        member = next(
            member
            for member in client.groups.members(group.id)
            if member.principal_id == PrincipalId(user.id)
        )
        assert member.group_id == group.id
        assert member.principal is not None
        assert member.principal.name == user.name
        client.groups.remove_member(group.id, PrincipalId(user.id))

        for suffix in ("from", "to"):
            collection = client.collections.create(
                CollectionCreate(
                    name=f"{unique_name}-{suffix}-collection",
                    description="Relation e2e collection",
                    group_id=admin_group_id,
                )
            )
            collections.append(collection)
            hubuum_class = client.classes.create(
                ClassCreate(
                    name=f"{unique_name}-{suffix}-class",
                    collection_id=collection.id,
                    description="Relation e2e class",
                )
            )
            classes.append(hubuum_class)
            objects.append(
                client.classes.by_id(hubuum_class.id).objects.create(
                    ObjectCreate(
                        name=f"{unique_name}-{suffix}-object",
                        collection_id=collection.id,
                        hubuum_class_id=hubuum_class.id,
                        description="Relation e2e object",
                        data={},
                    )
                )
            )

        class_relation = client.class_relations.create(
            ClassRelationCreate(
                from_hubuum_class_id=classes[0].id,
                to_hubuum_class_id=classes[1].id,
                from_max_relations=1,
                to_max_relations=2,
            )
        )
        assert class_relation.from_max_relations == 1
        assert class_relation.to_max_relations == 2
        object_relation = client.object_relations.create(
            ObjectRelationCreate(
                from_hubuum_object_id=objects[0].id,
                to_hubuum_object_id=objects[1].id,
                class_relation_id=class_relation.id,
            )
        )
        assert client.object_relations.get(object_relation.id).id == object_relation.id
        extra_to_object = client.classes.by_id(classes[1].id).objects.create(
            ObjectCreate(
                name=f"{unique_name}-to-extra-object",
                collection_id=collections[1].id,
                hubuum_class_id=classes[1].id,
                description="Relation cardinality e2e object",
                data={},
            )
        )
        with pytest.raises(ConflictError):
            client.object_relations.create(
                ObjectRelationCreate(
                    from_hubuum_object_id=objects[0].id,
                    to_hubuum_object_id=extra_to_object.id,
                    class_relation_id=class_relation.id,
                )
            )
    finally:
        if object_relation is not None:
            client.object_relations.delete(object_relation.id)
        if class_relation is not None:
            client.class_relations.delete(class_relation.id)
        if extra_to_object is not None and len(classes) == 2:
            client.classes.by_id(classes[1].id).objects.delete(extra_to_object.id)
        for hubuum_class, hubuum_object in zip(classes, objects, strict=True):
            client.classes.by_id(hubuum_class.id).objects.delete(hubuum_object.id)
        for hubuum_class in classes:
            client.classes.delete(hubuum_class.id)
        for collection in collections:
            client.collections.delete(collection.id)
        client.groups.delete(group.id)
        client.users.delete(user.id)


def test_v009_import_timestamps_export_timings_and_task_events(
    client: Client,
    unique_name: str,
) -> None:
    restored_created_at = datetime(2024, 2, 3, 4, 5, 6)
    restored_updated_at = datetime(2024, 2, 3, 4, 5, 7)
    collection_name = f"{unique_name}-imported-collection"
    imported_collection = None
    try:
        imported = client.imports.run(
            ImportRequest(
                graph=ImportGraph(
                    collections=(
                        ImportCollectionInput(
                            ref_="imported-collection",
                            name=collection_name,
                            description="v0.0.9 restored timestamp e2e collection",
                            timestamps=RestoreTimestamps(
                                created_at=restored_created_at,
                                updated_at=restored_updated_at,
                            ),
                        ),
                    )
                )
            ),
            idempotency_key=f"{unique_name}-import",
        )
        assert imported.task.status in {
            TaskStatus.SUCCEEDED,
            TaskStatus.PARTIALLY_SUCCEEDED,
        }
        assert imported.succeeded == 1
        assert imported.failed == 0
        imported_collection = client.collections.one(Query().where("name", collection_name))
        assert imported_collection.created_at.replace(tzinfo=None) == restored_created_at
        assert imported_collection.updated_at.replace(tzinfo=None) == restored_updated_at

        submitted = client.exports.submit(
            ExportRequest(scope=ExportScope(kind=ExportScopeKind.COLLECTIONS)),
            idempotency_key=f"{unique_name}-export",
        )
        export_task = client.tasks.wait(submitted.id)
        assert export_task.status is TaskStatus.SUCCEEDED
        assert export_task.details is not None
        assert export_task.details.export is not None
        timings = export_task.details.export
        durations = (
            timings.total_duration_ms,
            timings.query_duration_ms,
            timings.hydration_duration_ms,
            timings.render_duration_ms,
        )
        assert all(duration is not None for duration in durations)
        assert all(duration >= 0 for duration in durations if duration is not None)
        output = client.exports.output(export_task.id)
        assert isinstance(output, ExportJsonResponse)
        assert output.meta.count >= 1
        assert client.tasks.all_events(export_task.id)
    finally:
        if imported_collection is not None:
            client.collections.delete(imported_collection.id)


def test_sync_scoped_token_full_lifecycle(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    collection = client.collections.create(
        CollectionCreate(
            name=f"{unique_name}-token-collection",
            description="Scoped token lifecycle e2e collection",
            group_id=admin_group_id,
        )
    )
    token_name = f"{unique_name}-sync-token"
    principal_tokens = client.tokens.for_principal(client.me().principal.principal_id)
    try:
        token = principal_tokens.create(
            NewTokenRequest(
                name=token_name,
                scope=TokenScope(
                    permissions=(Permission.READ_COLLECTION,),
                    resources=(
                        TokenResourceScope(
                            kind=TokenResourceKind.COLLECTION,
                            id=collection.id,
                        ),
                    ),
                ),
            )
        )
        assert token.expires_at is not None
        metadata = next(item for item in principal_tokens.list() if item.name == token_name)
        assert metadata.active
        assert not metadata.expired
        assert metadata.revision > 0
        assert metadata.scope is not None
        assert metadata.scope.permissions == (Permission.READ_COLLECTION,)
        assert metadata.scope.resources is not None
        assert [(item.kind, item.id) for item in metadata.scope.resources] == [
            (TokenResourceKind.COLLECTION, collection.id)
        ]
        point = principal_tokens.get(metadata.id)
        assert point.id == metadata.id
        assert point.revision == metadata.revision
        renewed = principal_tokens.renew(metadata.id)
        renewed_metadata = next(
            item
            for item in principal_tokens.list()
            if item.name == token_name and item.id != metadata.id
        )
        assert renewed_metadata.active

        with Client(client.base_url, token=token) as scoped:
            current_scope = scoped.me().token.scope
            assert current_scope is not None
            assert current_scope.permissions == (Permission.READ_COLLECTION,)
            assert {item.id for item in scoped.collections.list()} == {collection.id}
            assert scoped.collections.get(collection.id).id == collection.id
            with pytest.raises(PermissionDeniedError):
                scoped.collections.update(
                    collection.id,
                    CollectionUpdate(description="A read-scoped token must not update"),
                )

        principal_tokens.revoke(metadata.id)
        revoked_metadata = next(
            item
            for item in principal_tokens.list(state=TokenListState.REVOKED)
            if item.id == metadata.id
        )
        assert not revoked_metadata.active
        with (
            Client(client.base_url, token=token) as revoked_client,
            pytest.raises(AuthenticationError),
        ):
            revoked_client.collections.get(collection.id)
        with Client(client.base_url, token=renewed) as renewed_client:
            assert renewed_client.collections.get(collection.id).id == collection.id
        principal_tokens.revoke(renewed_metadata.id)
    finally:
        for metadata in principal_tokens.list(state=TokenListState.ALL):
            if metadata.name == token_name and metadata.active:
                with suppress(APIError):
                    principal_tokens.revoke(metadata.id)
        client.collections.delete(collection.id)


def test_non_admin_permissions_and_live_error_mapping(
    base_url: str,
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    password = f"{unique_name}-Limited-Passw0rd!"
    user = client.users.create(
        UserCreate(
            name=f"{unique_name}-limited-user",
            password=password,
            email=f"{unique_name}-limited@example.test",
        )
    )
    group = None
    collection = None
    member_added = False
    try:
        group = client.groups.create(
            GroupCreate(
                groupname=f"{unique_name}-limited-group",
                description="Read-only e2e group",
            )
        )
        client.groups.add_member(group.id, PrincipalId(user.id))
        member_added = True
        collection = client.collections.create(
            CollectionCreate(
                name=f"{unique_name}-limited-collection",
                description="Permission boundary e2e collection",
                group_id=admin_group_id,
            )
        )
        client.openapi.call(
            "postApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            options=OpenAPIOptions(
                path_params={
                    "collection_id": collection.id,
                    "group_id": group.id,
                    "permission": "ReadCollection",
                }
            ),
        )

        with Client(base_url) as public:
            with pytest.raises(AuthenticationError) as unauthenticated:
                public.collections.list()
            assert unauthenticated.value.status_code == 401

        with Client(base_url) as limited:
            limited.login(Credentials(user.name, password))
            assert limited.collections.get(collection.id).id == collection.id
            with pytest.raises(PermissionDeniedError) as forbidden:
                limited.collections.update(
                    collection.id,
                    CollectionUpdate(description="This update must be denied"),
                )
            assert forbidden.value.status_code == 403

        with pytest.raises(NotFoundError) as missing:
            client.collections.get(2_147_483_647)
        assert missing.value.status_code == 404

        with pytest.raises(APIError) as invalid:
            client.request("GET", "/api/v1/collections/0")
        assert type(invalid.value) is APIError
        assert invalid.value.status_code == 400

        with pytest.raises(ConflictError) as duplicate:
            client.collections.create(
                CollectionCreate(
                    name=collection.name,
                    description="Duplicate collection name",
                    group_id=admin_group_id,
                )
            )
        assert duplicate.value.status_code == 409
    finally:
        if collection is not None:
            client.collections.delete(collection.id)
        if group is not None and member_added:
            client.groups.remove_member(group.id, PrincipalId(user.id))
        if group is not None:
            client.groups.delete(group.id)
        client.users.delete(user.id)


async def test_async_scoped_token_full_lifecycle(
    base_url: str,
    admin_password: str,
    unique_name: str,
) -> None:
    async with AsyncClient(base_url) as admin:
        await admin.login(Credentials("admin", admin_password))
        admin_group_id = (await admin.groups.get_by_name("admin")).id
        collection = await admin.collections.create(
            CollectionCreate(
                name=f"{unique_name}-async-token-collection",
                description="Async scoped token lifecycle e2e collection",
                group_id=admin_group_id,
            )
        )
        token_name = f"{unique_name}-async-token"
        principal_tokens = admin.tokens.for_principal((await admin.me()).principal.principal_id)
        try:
            token = await principal_tokens.create(
                NewTokenRequest(
                    name=token_name,
                    scope=TokenScope(
                        permissions=(Permission.READ_COLLECTION,),
                        resources=(
                            TokenResourceScope(
                                kind=TokenResourceKind.COLLECTION,
                                id=collection.id,
                            ),
                        ),
                    ),
                )
            )
            assert token.expires_at is not None
            metadata = next(
                item for item in await principal_tokens.list() if item.name == token_name
            )
            assert metadata.active
            assert not metadata.expired
            assert metadata.scope is not None
            assert metadata.scope.permissions == (Permission.READ_COLLECTION,)
            assert metadata.scope.resources is not None
            assert [(item.kind, item.id) for item in metadata.scope.resources] == [
                (TokenResourceKind.COLLECTION, collection.id)
            ]
            assert (await principal_tokens.get(metadata.id)).revision == metadata.revision
            renewed = await principal_tokens.renew(metadata.id)
            renewed_metadata = next(
                item
                for item in await principal_tokens.list()
                if item.name == token_name and item.id != metadata.id
            )

            async with AsyncClient(base_url, token=token) as scoped:
                current_scope = (await scoped.me()).token.scope
                assert current_scope is not None
                assert current_scope.permissions == (Permission.READ_COLLECTION,)
                assert {item.id for item in await scoped.collections.list()} == {collection.id}
                assert (await scoped.collections.get(collection.id)).id == collection.id
                with pytest.raises(PermissionDeniedError):
                    await scoped.collections.update(
                        collection.id,
                        CollectionUpdate(description="A read-scoped token must not update"),
                    )

            await principal_tokens.revoke(metadata.id)
            assert any(
                item.id == metadata.id and not item.active
                for item in await principal_tokens.list(state=TokenListState.REVOKED)
            )
            async with AsyncClient(base_url, token=token) as revoked_client:
                with pytest.raises(AuthenticationError):
                    await revoked_client.collections.get(collection.id)
            async with AsyncClient(base_url, token=renewed) as renewed_client:
                assert (await renewed_client.collections.get(collection.id)).id == collection.id
            await principal_tokens.revoke(renewed_metadata.id)
        finally:
            for metadata in await principal_tokens.list(state=TokenListState.ALL):
                if metadata.name == token_name and metadata.active:
                    with suppress(APIError):
                        await principal_tokens.revoke(metadata.id)
            await admin.collections.delete(collection.id)


async def test_async_client_full_resource_lifecycle(
    base_url: str,
    admin_password: str,
    unique_name: str,
) -> None:
    async with AsyncClient(base_url) as async_client:
        await async_client.login(Credentials("admin", admin_password))
        admin_group_id = (await async_client.groups.get_by_name("admin")).id
        collection = await async_client.collections.create(
            CollectionCreate(
                name=f"{unique_name}-async-collection",
                description="Async Python e2e collection",
                group_id=admin_group_id,
            )
        )
        hubuum_class = None
        hubuum_object = None
        try:
            hubuum_class = await async_client.classes.create(
                ClassCreate(
                    name=f"{unique_name}-async-class",
                    collection_id=collection.id,
                    description="Async Python e2e class",
                )
            )
            object_service = async_client.classes.by_id(hubuum_class.id).objects
            hubuum_object = await object_service.create(
                ObjectCreate(
                    name=f"{unique_name}-async-object",
                    collection_id=collection.id,
                    hubuum_class_id=hubuum_class.id,
                    description="Async Python e2e object",
                    data={"phase": "created"},
                )
            )
            selected = await object_service.get(hubuum_object.id)
            assert selected.id == hubuum_object.id
            assert {
                item.id
                for item in await object_service.all(Query().data("phase").equals("created"))
            } == {hubuum_object.id}

            updated = await object_service.update(
                hubuum_object.id,
                ObjectUpdate(description="Updated asynchronously", data={"phase": "updated"}),
            )
            assert updated.data == {"phase": "updated"}

            named_objects = async_client.classes.by_name(hubuum_class.name).objects
            patched = await named_objects.patch_data(
                hubuum_object.name,
                [{"op": "replace", "path": "/phase", "value": "patched"}],
            )
            assert patched.data == {"phase": "patched"}

            object_id = hubuum_object.id
            await named_objects.delete(hubuum_object.name)
            hubuum_object = None
            with pytest.raises(NotFoundError):
                await object_service.get(object_id)
        finally:
            if hubuum_object is not None and hubuum_class is not None:
                await async_client.classes.by_id(hubuum_class.id).objects.delete(hubuum_object.id)
            if hubuum_class is not None:
                await async_client.classes.delete_by_name(hubuum_class.name)
            await async_client.collections.delete(collection.id)
