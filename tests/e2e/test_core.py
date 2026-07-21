from __future__ import annotations

import pytest

from hubuum_client import (
    AsyncClient,
    ClassCreate,
    ClassRelationCreate,
    ClassUpdate,
    Client,
    CollectionCreate,
    Credentials,
    GroupCreate,
    GroupId,
    ObjectCreate,
    ObjectRelationCreate,
    ObjectUpdate,
    PrincipalId,
    Query,
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
        config = public.config()
        assert config["pagination"]["default_page_limit"] > 0
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
        numeric_name = str(int(unique_name.rsplit("-", 1)[-1], 16))
        hubuum_class = client.classes.create(
            ClassCreate(
                name=numeric_name,
                collection_id=collection.id,
                description="Python e2e class",
            )
        )
        assert client.classes.get_by_name(numeric_name).id == hubuum_class.id

        hubuum_object = client.objects(hubuum_class.id).create(
            ObjectCreate(
                name=f"{unique_name}-object",
                collection_id=collection.id,
                hubuum_class_id=hubuum_class.id,
                description="Python e2e object",
                data={"source": "hubuum-client-python"},
            )
        )
        updated = client.objects(hubuum_class.id).update(
            hubuum_object.id,
            ObjectUpdate(description="Updated from Python", data={"updated": True}),
        )
        assert updated.data == {"updated": True}
        assert (
            client.objects(hubuum_class.id).get_by_name(hubuum_object.name).id == hubuum_object.id
        )

        page = client.objects(hubuum_class.id).page(
            Query().where("name", hubuum_object.name).limit(5).include_total()
        )
        assert any(item.id == hubuum_object.id for item in page)

        renamed = client.classes.update(
            hubuum_class.id, ClassUpdate(description="Updated Python e2e class")
        )
        assert renamed.description == "Updated Python e2e class"
    finally:
        if hubuum_object is not None and hubuum_class is not None:
            client.objects(hubuum_class.id).delete(hubuum_object.id)
        if hubuum_class is not None:
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
    objects = []
    class_relation = None
    object_relation = None
    try:
        client.groups.add_member(group.id, PrincipalId(user.id))
        assert any(member["principal_id"] == user.id for member in client.groups.members(group.id))
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
                client.objects(hubuum_class.id).create(
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
            )
        )
        object_relation = client.object_relations.create(
            ObjectRelationCreate(
                from_hubuum_object_id=objects[0].id,
                to_hubuum_object_id=objects[1].id,
                class_relation_id=class_relation.id,
            )
        )
        assert client.object_relations.get(object_relation.id).id == object_relation.id
    finally:
        if object_relation is not None:
            client.object_relations.delete(object_relation.id)
        if class_relation is not None:
            client.class_relations.delete(class_relation.id)
        for hubuum_class, hubuum_object in zip(classes, objects, strict=True):
            client.objects(hubuum_class.id).delete(hubuum_object.id)
        for hubuum_class in classes:
            client.classes.delete(hubuum_class.id)
        for collection in collections:
            client.collections.delete(collection.id)
        client.groups.delete(group.id)
        client.users.delete(user.id)


async def test_async_client_reads_live_resources(
    base_url: str,
    admin_password: str,
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
) -> None:
    collection = client.collections.create(
        CollectionCreate(
            name=f"{unique_name}-async-collection",
            description="Async Python e2e collection",
            group_id=admin_group_id,
        )
    )
    try:
        async with AsyncClient(base_url) as async_client:
            await async_client.login(Credentials("admin", admin_password))
            selected = await async_client.collections.get(collection.id)
            assert selected.id == collection.id
            assert any(item.id == collection.id for item in await async_client.collections.all())
    finally:
        client.collections.delete(collection.id)
