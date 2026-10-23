"""Generated from docs/openapi.json; run scripts/generate-typed-api.py."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field

from hubuum_client.models import APIModel

from . import models


class ClassesListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesDeleteByNameHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesPatchByNameHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesGetByNameObjectAggregatesQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    group_by: list[str] | None = None
    aggregate: list[str] | None = None
    sort: str | None = None


class ClassesGetByNameObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include: str | None = None
    sort: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetByNameObjectsByNameQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include: str | None = None


class ClassesDeleteByNameObjectsByNameHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesPatchByNameObjectsByNameHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesPatchByNameObjectsByNameDataHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesGetByNameObjectsByNameRelatedObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    ignore_classes: str | None = None
    ignore_self_class: bool | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetByNameObjectsByNameRelatedRelationsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetByNamePermissionsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetByNameRelatedQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetByNameRelatedRelationsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesGetObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include: str | None = None
    sort: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class ClassesGetHistoryTimelineQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    from_: Annotated[datetime | None, Field(alias="from")] = None
    until: datetime | None = None
    at: datetime | None = None
    anchor: Annotated[int | None, Field(ge=1)] = None
    direction: models.HistoryDirection | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetObjectAggregatesQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    group_by: list[str] | None = None
    aggregate: list[str] | None = None
    sort: str | None = None


class ClassesGetObjectsHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    name: str
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None
    revision: int | None = None


class ClassesGetObjectsHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None
    revision: int | None = None


class ClassesGetObjectsObjectRelatedObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    ignore_classes: str | None = None
    ignore_self_class: bool | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetObjectsObjectRelatedRelationsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetPermissionsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetRelatedQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetRelatedRelationsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetRelationsHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None


class ClassesGetRelationsHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None


class ClassesDeleteRelationsByRelationIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesDeleteByFromObjectIdRelationsByToClassIdByToObjectIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesGetObjectQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include: str | None = None


class ClassesDeleteObjectHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesPatchObjectHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesPatchObjectDataHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ClassesGetObjectHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetObjectHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class ClassesGetObjectHistoryComputedAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class ClassesGetObjectHistoryTimelineQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    from_: Annotated[datetime | None, Field(alias="from")] = None
    until: datetime | None = None
    at: datetime | None = None
    anchor: Annotated[int | None, Field(ge=1)] = None
    direction: models.HistoryDirection | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None


class ClassesGetObjectRelationsHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None


class ClassesGetObjectRelationsHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor: str | None = None
    include_total: bool | None = None
    sort: str | None = None


class CollectionsListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class CollectionsDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsGetHasPermissionsByPermissionQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class CollectionsGetHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class CollectionsGetHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class CollectionsPutParentHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsGetPermissionsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class CollectionsPutPermissionsGroupByGroupIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsPostPermissionsGroupByGroupIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsDeletePermissionsGroupByGroupIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsPostPermissionsGroupByGroupIdByPermissionHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsDeletePermissionsGroupByGroupIdByPermissionHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class CollectionsGetPermissionsPrincipalByPrincipalIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ComputedFieldsDeleteClassesByClassIdByFieldIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ComputedFieldsPatchClassesByClassIdByFieldIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ComputedFieldsGetIamMeQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    class_id: int | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ComputedFieldsDeleteIamMeByFieldIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ComputedFieldsPatchIamMeByFieldIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventDeliveriesListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str
    cursor: str
    include_total: bool | None = None


class EventSinksDeleteCollectionsByCollectionIdBySinkIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSinksPatchCollectionsByCollectionIdBySinkIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSinksGetQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventSinksDeleteBySinkIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSinksPatchBySinkIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSubscriptionsGetCollectionsByCollectionIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventSubscriptionsDeleteCollectionsByCollectionIdBySubscriptionIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSubscriptionsPatchCollectionsByCollectionIdBySubscriptionIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSubscriptionsDeleteSystemBySubscriptionIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventSubscriptionsPatchSystemBySubscriptionIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class EventsGetClassesByClassIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include_relations: bool | None = None
    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetClassesByClassIdObjectQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include_relations: bool | None = None
    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetCollectionsByCollectionIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    entity_type: str | None = None
    entity_id: int | None = None
    include_relations: bool | None = None
    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetExportTemplatesByTemplateIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetIamGroupsByGroupIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetIamUsersByUserIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class EventsGetRemoteTargetsByTargetIdQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    action: str | None = None
    actor_kind: str | None = None
    actor_user_id: int | None = None
    initiator_user_id: int | None = None
    collection_id: int | None = None
    occurred_after: str | None = None
    occurred_before: str | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ExportTemplatesListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ExportTemplatesDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ExportTemplatesUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ExportTemplatesGetHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ExportTemplatesGetHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class GroupsListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class GroupsDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class GroupsUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class GroupsGetMembersQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class GroupsPostMembersByPrincipalIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class GroupsDeleteMembersByPrincipalIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ImportsCreateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[
        str | None, Field(alias="X-Hubuum-Credential-Approval")
    ] = None


class ImportsGetResultsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class MetaGetLoginRateLimitQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    include: str | None = None
    scope: str | None = None
    q: str | None = None


class PrincipalsGetMeGroupsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class PrincipalsPutMeSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsDeleteMeSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsPatchMeSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsGetMeTokensQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    state: models.TokenListState | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class PrincipalsGetByPrincipalIdGroupsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class PrincipalsPutByPrincipalIdSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsDeleteByPrincipalIdSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsPatchByPrincipalIdSettingsHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class PrincipalsGetByPrincipalIdTokensQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    state: models.TokenListState | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class PrincipalsPostByPrincipalIdTokensHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[str, Field(alias="X-Hubuum-Credential-Approval")]


class PrincipalsGetByPrincipalIdTokensByTokenIdActivityQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    offset: Annotated[int | None, Field(ge=0)] = None
    limit: Annotated[int | None, Field(ge=0)] = None


class PrincipalsPostByPrincipalIdTokensByTokenIdRenewHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[str, Field(alias="X-Hubuum-Credential-Approval")]


class PrincipalsPostByPrincipalIdTokensByTokenIdRevokeHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class QueryUsageDeleteQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    expected_revision: models.ResourceRevision


class RelationsGetClassesQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class RelationsDeleteClassesByRelationIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class RelationsPatchClassesByRelationIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class RelationsGetObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class RelationsDeleteObjectsByRelationIdHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class RemoteTargetsListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class RemoteTargetsGetHistoryQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class RemoteTargetsGetHistoryAsOfQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    at: str


class RemoteTargetsDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class RemoteTargetsUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class RestoresPostConfirmHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[str, Field(alias="X-Hubuum-Credential-Approval")]


class SchemaEvolutionGetObjectsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    after: int | None = None
    limit: Annotated[int | None, Field(ge=0)] = None
    status: models.ComplianceStatus | None = None


class SchemaEvolutionGetRevisionsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    after: int | None = None
    limit: Annotated[int | None, Field(ge=0)] = None


class SchemaEvolutionGetTasksByTaskIdReportQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    download: bool | None = None


class SearchListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    q: str
    kinds: str | None = None
    limit_per_kind: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor_collections: str | None = None
    cursor_classes: str | None = None
    cursor_objects: str | None = None
    search_class_schema: bool | None = None
    search_object_data: bool | None = None


class SearchGetStreamQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    q: str
    kinds: str | None = None
    limit_per_kind: Annotated[int | None, Field(ge=1, le=250)] = None
    cursor_collections: str | None = None
    cursor_classes: str | None = None
    cursor_objects: str | None = None
    search_class_schema: bool | None = None
    search_object_data: bool | None = None


class ServiceAccountsListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class ServiceAccountsDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ServiceAccountsUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class ServiceAccountsPostDisableHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class TasksListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    class_id: int | None = None
    object_id: int | None = None
    collection_id: int | None = None
    relation_type: str | None = None
    relation_id: int | None = None
    schema_revision: int | None = None
    schema_work_kind: str | None = None
    schema_work_status: str | None = None
    computation_revision: int | None = None
    remote_target_id: int | None = None
    remote_side_effect_state: str | None = None
    export_scope_kind: str | None = None
    export_template_id: int | None = None
    export_has_warnings: bool | None = None
    export_truncated: bool | None = None
    import_dry_run: bool | None = None
    import_atomicity: str | None = None
    import_collision_policy: str | None = None
    import_permission_policy: str | None = None
    import_has_failed_items: bool | None = None
    backup_include_history: bool | None = None
    output_state: str | None = None
    kind: str | None = None
    status: str | None = None
    terminal: bool | None = None
    cancel_requested: bool | None = None
    terminal_reason: str | None = None
    trace_id: str | None = None
    created_after: str | None = None
    created_before: str | None = None
    started_after: str | None = None
    started_before: str | None = None
    finished_after: str | None = None
    finished_before: str | None = None
    submitted_by: int | None = None
    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class TasksGetEventsQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class UsersListQuery(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    limit: Annotated[int | None, Field(ge=1, le=250)] = None
    sort: str | None = None
    cursor: str | None = None
    include_total: bool | None = None


class UsersCreateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[str, Field(alias="X-Hubuum-Credential-Approval")]


class UsersDeleteHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class UsersUpdateHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    x_hubuum_credential_approval: Annotated[
        str | None, Field(alias="X-Hubuum-Credential-Approval")
    ] = None
    if_match: Annotated[str | None, Field(alias="If-Match")] = None


class UsersPostAnonymizeHeader(APIModel):
    """Immutable operation parameters; omitted fields are not sent."""

    if_match: Annotated[str | None, Field(alias="If-Match")] = None
