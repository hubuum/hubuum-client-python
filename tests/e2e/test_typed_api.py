from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

import pytest

from hubuum_client import APIError, AsyncClient, Client, Credentials, ObjectRelationCreate
from hubuum_client.api import models, query

pytestmark = pytest.mark.e2e


async def resolve(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


@pytest.fixture(params=[False, True], ids=["sync", "async"])
async def typed_client(request: Any, base_url: str, admin_password: str) -> AsyncIterator[Any]:
    client = (AsyncClient if request.param else Client)(base_url)
    try:
        await resolve(client.login_session(Credentials("admin", admin_password)))
        yield client
    finally:
        await resolve(client.close())


@pytest.fixture
async def graph(typed_client: Any, unique_name: str) -> AsyncIterator[tuple[Any, ...]]:
    api = typed_client.api
    group = await resolve(typed_client.groups.get_by_name("admin"))
    collection = (
        await resolve(
            api.collections.create(
                body=models.NewCollectionWithAssignee(
                    name=unique_name, description="Typed parity", group_id=group.id
                )
            )
        )
    ).body
    try:
        classes = [
            (
                await resolve(
                    api.classes.create(
                        body=models.NewHubuumClass(
                            name=f"{unique_name}-{suffix}",
                            collection_id=collection.id,
                            description="Typed parity",
                            json_schema={
                                "type": "object",
                                "properties": {"count": {"type": "number"}},
                            },
                            validate_schema=False,
                        )
                    )
                )
            ).body
            for suffix in ("source", "target")
        ]
        objects = [
            (
                await resolve(
                    api.classes.post_objects(
                        cls.id,
                        body=models.NewHubuumObjectRequest(
                            name=cls.name,
                            collection_id=collection.id,
                            hubuum_class_id=cls.id,
                            description="Typed parity",
                            data={"count": 2},
                        ),
                    )
                )
            ).body
            for cls in classes
        ]
        relation = (
            await resolve(
                api.relations.post_classes(
                    body=models.NewHubuumClassRelation(
                        from_hubuum_class_id=classes[0].id,
                        to_hubuum_class_id=classes[1].id,
                        forward_label="contains",
                        reverse_label="contained by",
                    )
                )
            )
        ).body
        edge = await resolve(
            typed_client.object_relations.create(
                ObjectRelationCreate(
                    from_hubuum_object_id=objects[0].id,
                    to_hubuum_object_id=objects[1].id,
                    class_relation_id=relation.id,
                )
            )
        )
        yield collection, classes, objects, relation, edge
    finally:
        with suppress(APIError):
            await resolve(api.collections.delete(collection.id))


async def test_typed_history_and_relations(typed_client: Any, graph: tuple[Any, ...]) -> None:
    _, classes, objects, relation, _ = graph
    api, cls, obj = typed_client.api, classes[0], objects[0]
    at = datetime.now(UTC).isoformat()
    updated = (
        await resolve(
            api.relations.patch_classes_by_relation_id(
                relation.id,
                body=models.UpdateClassRelationLabels(
                    forward_label=None, reverse_label="belongs to"
                ),
            )
        )
    ).body
    assert updated.forward_label is None
    assert updated.reverse_label == "belongs to"
    class_history = (await resolve(api.classes.get_history(cls.id))).body
    object_history = (await resolve(api.classes.get_object_history(cls.id, obj.id))).body
    class_entry = (
        await resolve(
            api.classes.get_history_entries_by_history_id(cls.id, class_history[0].history_id)
        )
    ).body
    object_entry = (
        await resolve(
            api.classes.get_object_history_entries_by_history_id(
                cls.id, obj.id, object_history[0].history_id
            )
        )
    ).body
    assert class_entry.id == cls.id
    assert object_entry.data == {"count": 2}
    for method, args, controls in (
        (api.classes.get_history_timeline, (cls.id,), None),
        (api.classes.get_object_history_timeline, (cls.id, obj.id), None),
        (
            api.classes.get_objects_history,
            (cls.id,),
            query.ClassesGetObjectsHistoryQuery(name=obj.name),
        ),
        (
            api.classes.get_objects_history_as_of,
            (cls.id,),
            query.ClassesGetObjectsHistoryAsOfQuery(at=at),
        ),
        (api.classes.get_relations_history, (cls.id,), None),
        (
            api.classes.get_relations_history_as_of,
            (cls.id,),
            query.ClassesGetRelationsHistoryAsOfQuery(at=at),
        ),
        (api.classes.get_object_relations_history, (cls.id, obj.id), None),
        (
            api.classes.get_object_relations_history_as_of,
            (cls.id, obj.id),
            query.ClassesGetObjectRelationsHistoryAsOfQuery(at=at),
        ),
    ):
        result = await resolve(method(*args, **({"query": controls} if controls else {})))
        assert result.body
    historical = (
        await resolve(
            api.classes.get_object_history_computed_as_of(
                cls.id, obj.id, query=query.ClassesGetObjectHistoryComputedAsOfQuery(at=at)
            )
        )
    ).body
    assert isinstance(historical, models.HistoricalComputedValues)
    assert (
        await resolve(
            api.classes.get_history_as_of(cls.id, query=query.ClassesGetHistoryAsOfQuery(at=at))
        )
    ).body.id == cls.id
    assert (
        await resolve(
            api.classes.get_object_history_as_of(
                cls.id, obj.id, query=query.ClassesGetObjectHistoryAsOfQuery(at=at)
            )
        )
    ).body.id == obj.id


async def test_typed_query_usage(typed_client: Any, graph: tuple[Any, ...]) -> None:
    cls = graph[1][0]
    api = typed_client.api
    pattern = models.QueryUsagePatternSchema(
        path="count", value_type="numeric", operations=["equals"]
    )
    declaration = (
        await resolve(
            api.query_usage.create(cls.id, body=models.QueryUsageCreateRequest(pattern=pattern))
        )
    ).body
    assert declaration.pattern == pattern
    assert any(
        item.id == declaration.id for item in (await resolve(api.query_usage.list(cls.id))).body
    )
    analysis = (
        await resolve(
            api.query_usage.post_analysis(
                cls.id, body=models.QueryUsageAnalysisRequest(proposed=[pattern])
            )
        )
    ).body
    assert isinstance(analysis.observations, models.QueryObservationSnapshot)
    replaced = (
        await resolve(
            api.query_usage.replace(
                cls.id,
                declaration.id,
                body=models.QueryUsageReplaceRequest(
                    pattern=pattern.model_copy(update={"operations": ["equals", "gt"]}),
                    expected_revision=declaration.revision,
                ),
            )
        )
    ).body
    assert replaced.revision > declaration.revision
    await resolve(
        api.query_usage.delete(
            cls.id,
            declaration.id,
            query=query.QueryUsageDeleteQuery(expected_revision=replaced.revision),
        )
    )
    assert (await resolve(api.query_usage.list(cls.id))).body == []
    observation = (await resolve(api.admin.get_query_observations())).body
    assert isinstance(observation.enabled, bool)


async def test_typed_search_hydration_and_events(typed_client: Any, graph: tuple[Any, ...]) -> None:
    _, classes, objects, _, edge = graph
    api = typed_client.api
    hydrated = (
        await resolve(
            api.search.post_hydrate(
                body=models.SearchHydrationRequest(
                    version=1,
                    root_class_id=classes[0].id,
                    root_object_id=objects[0].id,
                    class_=models.StructuredClassSelectorId(id=classes[1].id),
                    depth=1,
                    limit=10,
                )
            )
        )
    ).body
    assert hydrated.target_class_id == classes[1].id
    assert any(edge.id in path.relation_ids for path in hydrated.paths)
    body = models.StructuredSearchRequest(
        version=1,
        target=models.StructuredSearchTargetObject(
            kind="object", class_=models.StructuredClassSelectorId(id=classes[0].id)
        ),
    )
    assert isinstance(
        (await resolve(api.search.create(body=body))).body, models.StructuredSearchResponse
    )
    contexts = [
        api.search.post_stream(body=body),
        api.search.get_stream(query=query.SearchGetStreamQuery(q=classes[0].name)),
    ]
    for context in contexts:
        if isinstance(typed_client, AsyncClient):
            async with context as stream:
                events = [event async for event in stream.events()]
        else:
            with context as stream:
                events = list(stream.events())
        assert events[0].event == "started"
        assert events[-1].event == "done"
        assert any(event.event in {"batch", "result"} for event in events)


async def test_typed_credential_activity(typed_client: Any) -> None:
    api = typed_client.api
    me = (await resolve(api.principals.get_me())).body
    activity = (
        await resolve(
            api.principals.get_principals_by_principal_id_tokens_by_token_id_activity(
                me.principal.principal_id, me.token.id
            )
        )
    ).body
    assert isinstance(activity, models.CredentialActivityResponse)
    assert activity.best_effort
