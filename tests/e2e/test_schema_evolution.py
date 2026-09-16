from __future__ import annotations

import inspect
import sys
from collections.abc import Awaitable
from html import unescape
from typing import TypeVar

import pytest

from hubuum_client import (
    AsyncClient,
    ClassCreate,
    ClassUpdate,
    Client,
    Collection,
    CollectionCreate,
    CollectionKey,
    ComplianceStatus,
    ConflictError,
    GroupId,
    HubuumClass,
    HubuumObject,
    ImportClassInput,
    ImportGraph,
    ImportRequest,
    ImportSchemaActivation,
    ImportWriteCondition,
    ImportWriteMode,
    ObjectCreate,
    ObjectUpdate,
    SchemaActivationPolicy,
    SchemaActivationRequest,
    SchemaImpactReadiness,
    SchemaPageOptions,
    SchemaRepairReportRequest,
    SchemaRevision,
    SchemaRevisionResponse,
    SchemaStageRequest,
    SchemaWorkResponse,
    TaskKind,
    TaskStatus,
)

pytestmark = pytest.mark.e2e
T = TypeVar("T")


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_schema_impact_repair_activation_and_import(
    client: Client,
    admin_group_id: GroupId,
    unique_name: str,
    asynchronous: bool,
) -> None:
    api = AsyncClient(client.base_url, token=client.token) if asynchronous else client
    collection = await _resolve(
        api.collections.create(
            CollectionCreate(
                name=unique_name,
                description="Schema evolution e2e",
                group_id=admin_group_id,
            )
        )
    )
    try:
        cls = await _resolve(
            api.classes.create(
                ClassCreate(
                    name=unique_name,
                    collection_id=collection.id,
                    description="Schema evolution e2e",
                )
            )
        )
        selected = api.classes.by_id(cls.id)
        schema = selected.schema
        baseline = (await _resolve(schema.get())).active
        obj = await _resolve(
            selected.objects.create(
                ObjectCreate(
                    name=unique_name,
                    description="Repair candidate",
                    data={"hostname": 42},
                )
            )
        )
        staged, impact, html = await _inspect_candidate(api, cls, obj)
        with pytest.raises(ConflictError):
            await _resolve(
                schema.activate(
                    staged.revision,
                    SchemaActivationRequest(
                        expected_active_revision=baseline.revision,
                        policy=SchemaActivationPolicy.REJECT_INCOMPATIBLE,
                        impact_task_id=impact.task_id,
                    ),
                )
            )
        await _resolve(selected.objects.update(obj.id, ObjectUpdate(data={"hostname": "repaired"})))
        stale = await _resolve(schema.work(impact.task_id))
        assert stale.readiness is SchemaImpactReadiness.INCONCLUSIVE
        assert await _resolve(schema.report(impact.task_id)) == html
        fresh = await _resolve(schema.impact(staged.revision))
        assert (
            await _resolve(api.tasks.wait(fresh.task_id, timeout_seconds=60, poll_interval=0.1))
        ).status.successful
        assert (
            await _resolve(schema.work(fresh.task_id))
        ).readiness is SchemaImpactReadiness.COMPATIBLE
        activated = await _resolve(
            schema.activate(
                staged.revision,
                SchemaActivationRequest(
                    expected_active_revision=baseline.revision,
                    policy=SchemaActivationPolicy.REJECT_INCOMPATIBLE,
                    impact_task_id=fresh.task_id,
                ),
            )
        )
        assert activated.active.revision == staged.revision
        assert activated.task_id is not None
        assert (
            await _resolve(api.tasks.wait(activated.task_id, timeout_seconds=60, poll_interval=0.1))
        ).status.successful
        page = await _resolve(
            schema.objects(SchemaPageOptions(limit=1), status=ComplianceStatus.VALID)
        )
        assert page.items[0].object_id == obj.id
        assert page.items[0].evidence is not None
        assert page.items[0].evidence.schema_.revision == staged.revision
        await _check_terminal_cancellation_and_import(
            api, cls, collection, fresh.task_id, staged.revision
        )

    finally:
        primary_failure = sys.exc_info()[0] is not None
        try:
            await _resolve(api.collections.delete(collection.id))
        except Exception:
            if not primary_failure:
                raise
        finally:
            if asynchronous:
                await _resolve(api.close())


async def _check_terminal_cancellation_and_import(
    api: Client | AsyncClient,
    cls: HubuumClass,
    collection: Collection,
    task_id: int,
    active_revision: SchemaRevision,
) -> None:
    schema = api.classes.by_id(cls.id).schema
    # Cancellation is idempotent for a terminal task and must preserve its result.
    cancelled = await _resolve(api.tasks.cancel(task_id))
    assert cancelled.status is TaskStatus.SUCCEEDED
    assert (await _resolve(api.tasks.cancel(task_id))).status == cancelled.status
    # Import activation uses a separately staged removal and its exact policy.
    removed = await _resolve(schema.stage(SchemaStageRequest(validate_schema=False)))
    imported = await _resolve(
        api.imports.run(
            ImportRequest(
                graph=ImportGraph(
                    classes=(
                        ImportClassInput(
                            name=cls.name,
                            description=cls.description,
                            collection_key=CollectionKey(name=collection.name),
                            validate_schema=False,
                            condition=ImportWriteCondition(mode=ImportWriteMode.OVERWRITE),
                            schema_activation=ImportSchemaActivation(
                                revision=removed.revision,
                                expected_active_revision=active_revision,
                                policy=SchemaActivationPolicy.ALLOW_PENDING,
                            ),
                        ),
                    )
                )
            ),
            timeout_seconds=60,
            poll_interval=0.1,
        )
    )
    assert imported.failed == 0
    assert (await _resolve(schema.get())).active.revision == removed.revision
    assert (await _resolve(schema.objects())).items[0].status is ComplianceStatus.NOT_REQUIRED


async def _inspect_candidate(
    api: Client | AsyncClient,
    cls: HubuumClass,
    obj: HubuumObject,
) -> tuple[SchemaRevisionResponse, SchemaWorkResponse, str]:
    selected = api.classes.by_id(cls.id)
    schema = selected.schema
    candidate = {
        "type": "object",
        "required": ["hostname"],
        "properties": {"hostname": {"type": "string"}},
    }
    with pytest.raises(ConflictError):
        await _resolve(selected.update(ClassUpdate(json_schema=candidate, validate_schema=True)))
    staged = await _resolve(
        schema.stage(SchemaStageRequest(json_schema=candidate, validate_schema=True))
    )
    assert (await _resolve(schema.revision(staged.revision))).json_schema == candidate
    assert staged.revision in [r.revision for r in await _resolve(schema.revisions())]
    impact = await _resolve(schema.impact(staged.revision))
    completed = await _resolve(
        api.tasks.wait(impact.task_id, timeout_seconds=60, poll_interval=0.1)
    )
    assert completed.kind is TaskKind.SCHEMA_VALIDATION
    assert completed.status is TaskStatus.SUCCEEDED
    impact = await _resolve(schema.work(impact.task_id))
    assert impact.readiness is SchemaImpactReadiness.INCOMPATIBLE
    assert impact.impact is not None
    assert impact.impact.counts.newly_invalid == 1
    finding = next(f for f in impact.impact.findings if f.object_id == obj.id)
    assert finding.snapshot is not None
    assert finding.snapshot.object_revision == obj.revision
    assert finding.snapshot.diagnostics.issues
    html = await _resolve(
        schema.generate_report(
            impact.task_id,
            SchemaRepairReportRequest(
                object_url_template="https://inventory.example/objects/{object_id}",
            ),
        )
    )
    assert f"https://inventory.example/objects/{obj.id}" in unescape(html)
    assert await _resolve(schema.report(impact.task_id, download=True)) == html
    return staged, impact, html
