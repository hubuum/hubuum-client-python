from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

import pytest
from test_typed_api import graph, resolve, typed_client

from hubuum_client import (
    APIError,
    AsyncClient,
    AuthenticationError,
    Client,
    CollectionCreate,
    CollectionUpdate,
    ComputedFieldCreate,
    ComputedFieldPreviewRequest,
    ComputedFieldUpdate,
    CreateUserOperation,
    CredentialApprovalRequest,
    Credentials,
    EventQuery,
    ExportTemplateCreate,
    ExportTemplateUpdate,
    GroupCreate,
    Permission,
    PermissionDeniedError,
    PersonalComputedFieldCreate,
    PreconditionFailedError,
    PrincipalId,
    Query,
    RemoteTargetCreate,
    RemoteTargetInvokeRequest,
    RemoteTargetUpdate,
    SettingsPatchOperation,
    SettingsRequest,
    UserCreate,
)
from hubuum_client.api import models

__all__ = ["graph", "typed_client"]

pytestmark = pytest.mark.e2e


async def test_computed_field_lifecycles(typed_client: Any, graph: tuple[Any, ...]) -> None:
    cls = graph[1][0]
    shared = typed_client.classes.by_id(cls.id).computed_fields
    definition = ComputedFieldCreate(
        key="total",
        label="Total",
        result_type="integer",
        operation={"type": "sum", "paths": ["/count"]},
    )
    preview = await resolve(
        shared.preview(ComputedFieldPreviewRequest(definition=definition, data={"count": 7}))
    )
    assert preview.value == 7
    assert preview.error is None
    created = await resolve(shared.create(definition))
    personal = None
    try:
        assert created.definition.key == "total"
        assert (await resolve(shared.get(created.definition.id))).visibility == "shared"
        assert any(
            d.id == created.definition.id for d in (await resolve(shared.list())).definitions
        )
        updated = await resolve(
            shared.update(created.definition.id, ComputedFieldUpdate(label="Sum"))
        )
        assert updated.definition.label == "Sum"
        rebuilt = await resolve(shared.rebuild())
        assert rebuilt.class_id == cls.id
        if rebuilt.active_task_id is not None:
            task = await resolve(
                typed_client.tasks.wait(
                    rebuilt.active_task_id, timeout_seconds=90, poll_interval=0.2
                )
            )
            assert task.status.successful
        personal = await resolve(
            typed_client.computed_fields.create(
                PersonalComputedFieldCreate(
                    class_id=cls.id,
                    **definition.wire_payload(),
                )
            )
        )
        assert personal.owner_user_id is not None
        fields = await resolve(typed_client.computed_fields.for_class(cls.id).all(Query().limit(1)))
        assert [field.id for field in fields] == [personal.id]
        assert (await resolve(typed_client.computed_fields.get(personal.id))).id == personal.id
        value = await resolve(
            typed_client.computed_fields.preview(
                ComputedFieldPreviewRequest(
                    class_id=cls.id,
                    definition=definition,
                    object_id=graph[2][0].id,
                )
            )
        )
        assert value.value == 2
        changed = await resolve(
            typed_client.computed_fields.update(personal.id, ComputedFieldUpdate(enabled=False))
        )
        assert not changed.enabled
    finally:
        if personal is not None:
            await resolve(typed_client.computed_fields.delete(personal.id))
        deleted = await resolve(shared.delete(created.definition.id))
        assert deleted.state.class_id == cls.id


async def test_export_template_lifecycle(
    typed_client: Any, graph: tuple[Any, ...], unique_name: str
) -> None:
    collection, classes, _, _, _ = graph
    created = await resolve(
        typed_client.export_templates.create(
            ExportTemplateCreate(
                name=unique_name,
                description="Reusable output",
                collection_id=collection.id,
                class_id=classes[0].id,
                scope_kind="objects_in_class",
                kind="export",
                content_type="text/plain",
                template="workflow-output",
            )
        )
    )
    try:
        assert (await resolve(typed_client.export_templates.get(created.id))).name == unique_name
        assert [
            item.id
            for item in await resolve(
                typed_client.export_templates.all(Query().where("name", unique_name).limit(1))
            )
        ] == [created.id]
        point = await resolve(typed_client.api.export_templates.get(created.id))
        at = datetime.now(UTC)
        updated = await resolve(
            typed_client.export_templates.update(
                created.id, ExportTemplateUpdate(description="Updated"), if_match=point.etag
            )
        )
        assert updated.revision > created.revision
        with pytest.raises(PreconditionFailedError):
            await resolve(
                typed_client.export_templates.update(
                    created.id, ExportTemplateUpdate(description="Stale"), if_match=point.etag
                )
            )
        result = await resolve(
            typed_client.export_templates.run(created.id, timeout_seconds=90, poll_interval=0.2)
        )
        assert result.body == "workflow-output"
        history = typed_client.export_templates.audit(created.id).history
        assert len(await resolve(history.all(Query().limit(1)))) >= 2
        assert (await resolve(history.as_of(at))).description == "Reusable output"
        assert await resolve(
            typed_client.export_templates.audit(created.id).events.all(Query().limit(1))
        )
    finally:
        await resolve(typed_client.export_templates.delete(created.id))


async def test_remote_target_lifecycle_and_safe_invocation(
    typed_client: Any, graph: tuple[Any, ...], unique_name: str
) -> None:
    collection = graph[0]
    target = await resolve(
        typed_client.remote_targets.create(
            RemoteTargetCreate(
                name=unique_name,
                description="Safe blocked invocation",
                collection_id=collection.id,
                method="get",
                url_template="https://127.0.0.1:9/never-send",
                allowed_subject_types=["collection"],
                # The nonexistent secret prevents dispatch even on caller-managed servers
                # configured to permit private targets. No external service is contacted.
                auth_config=models.RemoteAuthConfigBearerSecret(
                    type="bearer_secret", secret=unique_name.replace("-", "_")
                ),
                enabled=True,
            )
        )
    )
    try:
        at = datetime.now(UTC)
        assert (await resolve(typed_client.remote_targets.get(target.id))).id == target.id
        assert any(
            item.id == target.id
            for item in await resolve(
                typed_client.remote_targets.all(Query().where("name", unique_name).limit(1))
            )
        )
        updated = await resolve(
            typed_client.remote_targets.update(
                target.id, RemoteTargetUpdate(description="Reviewed")
            )
        )
        assert updated.revision > target.revision
        task = await resolve(
            typed_client.remote_targets.invoke(
                target.id,
                RemoteTargetInvokeRequest(
                    subject=models.RemoteInvocationSubjectCollection(
                        type="collection", collection_id=collection.id
                    ),
                ),
            )
        )
        completed = await resolve(
            typed_client.tasks.wait(task.id, timeout_seconds=90, poll_interval=0.2)
        )
        assert completed.status.value == "failed"
        assert completed.details.remote_call.remote_target_id == target.id
        assert await resolve(typed_client.tasks.all_events(task.id))
        audit = typed_client.remote_targets.audit(target.id)
        assert len(await resolve(audit.history.all(Query().limit(1)))) >= 2
        assert (await resolve(audit.history.as_of(at))).description == target.description
        assert await resolve(audit.events.all(Query().limit(1)))
    finally:
        await resolve(typed_client.remote_targets.delete(target.id))


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_delegated_permissions_audit_and_principal_settings(
    client: Client,
    admin_password: str,
    unique_name: str,
    asynchronous: bool,
) -> None:
    password = unique_name + "-Passw0rd!"
    payload = UserCreate(name=unique_name, password=password)
    approval = client.credential_approvals.create(
        CredentialApprovalRequest(
            password=admin_password, operation=CreateUserOperation(user=payload)
        )
    )
    user = client.users.create(payload, approval=approval)
    group = parent = child = None
    delegated = (AsyncClient if asynchronous else Client)(client.base_url)
    admin = (AsyncClient if asynchronous else Client)(client.base_url, token=client.token)
    try:
        group = client.groups.create(GroupCreate(groupname=unique_name))
        client.groups.add_member(group.id, PrincipalId(user.id))
        admin_group = client.groups.get_by_name("admin")
        parent = client.collections.create(
            CollectionCreate(name=unique_name, description="Parent", group_id=admin_group.id)
        )
        child = client.collections.create(
            CollectionCreate(
                name=unique_name + "-child",
                description="Child",
                group_id=admin_group.id,
                parent_collection_id=parent.id,
            )
        )
        grants = admin.collections.permissions(parent.id)
        await resolve(grants.grant(group.id, [Permission.READ_COLLECTION]))
        await resolve(delegated.login_session(Credentials(unique_name, password)))
        inherited = await resolve(
            admin.collections.permissions(child.id).effective_principal(user.id)
        )
        assert any(item.inherited and item.source_collection.id == parent.id for item in inherited)
        with pytest.raises(PermissionDeniedError):
            await resolve(
                delegated.collections.permissions(parent.id).grant_permission(
                    group.id, Permission.UPDATE_COLLECTION
                )
            )
        # Audit access is separate from ordinary resource reads.
        assert await resolve(delegated.audit.collection(parent.id).events.list()) == []
        await resolve(grants.grant_permission(group.id, Permission.READ_AUDIT))
        assert await resolve(grants.check(group.id, Permission.READ_AUDIT))
        at = datetime.now(UTC)
        client.collections.update(parent.id, CollectionUpdate(description="Changed"))
        events = await resolve(
            delegated.audit.collection(parent.id).events.all(EventQuery().limit(1))
        )
        assert len(events) >= 2
        assert all(event.collection_id == parent.id for event in events)
        assert any(event.before is not None and event.after is not None for event in events)
        assert (
            await resolve(delegated.audit.collection(parent.id).history.as_of(at))
        ).description == "Parent"
        assert (
            len(await resolve(delegated.audit.collection(parent.id).history.all(Query().limit(1))))
            >= 2
        )
        assert await resolve(delegated.principals.permissions())
        assert any(
            item.id == group.id
            for item in await resolve(delegated.principals.groups().all(Query().limit(1)))
        )
        await _exercise_settings(delegated)
        await resolve(grants.replace(group.id, [Permission.READ_COLLECTION]))
        await resolve(grants.revoke_permission(group.id, Permission.READ_COLLECTION))
        await resolve(grants.revoke(group.id))
        assert not await resolve(grants.check(group.id, Permission.READ_AUDIT))
        # Revoke only this test principal's sessions, leaving the administrator
        # and unrelated clients intact.
        await _exercise_revocation(admin, delegated, user.id)
    finally:
        await resolve(delegated.close())
        await resolve(admin.close())
        for collection in (child, parent):
            if collection is not None:
                with suppress(APIError):
                    client.collections.delete(collection.id)
        if group is not None:
            client.groups.delete(group.id)
        client.users.delete(user.id)


async def test_admin_inspection(typed_client: Any, unique_name: str) -> None:
    assert (await resolve(typed_client.admin.counts())).total_collections >= 0
    assert await resolve(typed_client.admin.database())
    assert await resolve(typed_client.admin.tasks())
    assert await resolve(typed_client.admin.config())
    state = await resolve(typed_client.admin.rate_limits(q=unique_name))
    assert state.entries == []
    # Only release an identifier created by this test, never clear global state.
    probe = Client(typed_client.base_url)
    try:
        with pytest.raises(AuthenticationError):
            probe.login_session(Credentials(unique_name, "not-a-password"))
        state = await resolve(typed_client.admin.rate_limits(include="all", q=unique_name))
        for entry in state.entries:
            assert unique_name in entry.identifier
            assert (await resolve(typed_client.admin.release_rate_limit(entry.id))).released
    finally:
        probe.close()


async def _exercise_settings(delegated: Any) -> None:
    settings = delegated.principals.settings()
    original = await resolve(settings.get())
    changed = await resolve(settings.replace(SettingsRequest(settings={"theme": "light"})))
    assert changed.revision >= original.revision
    point = await resolve(delegated.api.principals.get_me_settings())
    merged = await resolve(
        settings.merge_patch(
            SettingsRequest(settings={"theme": None, "locale": "en"}), if_match=point.etag
        )
    )
    assert "theme" not in merged.settings
    patched = await resolve(
        settings.json_patch([SettingsPatchOperation(op="add", path="/theme", value="dark")])
    )
    assert patched.settings["theme"] == "dark"
    await resolve(settings.delete())
    assert (await resolve(settings.get())).settings == {}


async def _exercise_revocation(admin: Any, delegated: Any, user_id: int) -> None:
    assert await resolve(delegated.auth.providers())
    assert await resolve(delegated.auth.validate())
    await resolve(admin.auth.revoke_user(user_id))
    with pytest.raises(AuthenticationError):
        await resolve(delegated.auth.validate())
