"""Generated from docs/openapi.json; run scripts/generate-typed-api.py."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Literal

from pydantic import TypeAdapter

from hubuum_client._transport import api_body, api_options, decode_api_response
from hubuum_client.models import APIResponse
from hubuum_client.options import OpenAPIOptions
from hubuum_client.streaming import TypedResponseStream

from . import models
from . import query as controls

if TYPE_CHECKING:
    from hubuum_client.client import Client


class AdminAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_config(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RunningConfig]:
        """GET operation.

        /api/v1/admin/config
        """
        prepared = api_options(
            "getApiV1AdminConfig",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1AdminConfig", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.RunningConfig](models.RunningConfig)}
        )

    def get_query_observations(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.QueryObservationConfig]:
        """GET operation.

        /api/v1/admin/query-observations
        """
        prepared = api_options(
            "getApiV1AdminQueryObservations",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1AdminQueryObservations", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.QueryObservationConfig](
                    models.QueryObservationConfig
                )
            },
        )

    def put_query_observations(
        self, *, body: models.QueryObservationUpdateRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.QueryObservationConfig]:
        """PUT operation.

        /api/v1/admin/query-observations
        """
        prepared = api_options(
            "putApiV1AdminQueryObservations",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1AdminQueryObservations",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.QueryObservationUpdateRequest](
                        models.QueryObservationUpdateRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.QueryObservationConfig](
                    models.QueryObservationConfig
                )
            },
        )


class AuthAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def post_auth_login(
        self, *, body: models.SessionLoginRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SessionResponse]:
        """POST operation.

        /api/v1/auth/login
        """
        prepared = api_options(
            "postApiV1AuthLogin",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthLogin",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SessionLoginRequest](
                        models.SessionLoginRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SessionResponse](models.SessionResponse)},
        )

    def post_auth_logout(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.MessageResponse]:
        """POST operation.

        /api/v1/auth/logout
        """
        prepared = api_options(
            "postApiV1AuthLogout",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthLogout", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.MessageResponse](models.MessageResponse)},
        )

    def post_auth_logout_token(
        self, *, body: models.LogoutTokenRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.MessageResponse]:
        """POST operation.

        /api/v1/auth/logout/token
        """
        prepared = api_options(
            "postApiV1AuthLogoutToken",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthLogoutToken",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.LogoutTokenRequest](
                        models.LogoutTokenRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.MessageResponse](models.MessageResponse)},
        )

    def post_auth_logout_uid_by_user_id(
        self, user_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.MessageResponse]:
        """POST operation.

        /api/v1/auth/logout/uid/{user_id}
        """
        prepared = api_options(
            "postApiV1AuthLogoutUidByUserId",
            {"user_id": user_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthLogoutUidByUserId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.MessageResponse](models.MessageResponse)},
        )

    def post_auth_logout_all(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.MessageResponse]:
        """POST operation.

        /api/v1/auth/logout_all
        """
        prepared = api_options(
            "postApiV1AuthLogoutAll",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthLogoutAll", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.MessageResponse](models.MessageResponse)},
        )

    def get_auth_providers(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.AuthProvidersResponse]:
        """GET operation.

        /api/v1/auth/providers
        """
        prepared = api_options(
            "getApiV1AuthProviders",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1AuthProviders", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.AuthProvidersResponse](
                    models.AuthProvidersResponse
                )
            },
        )

    def post_auth_refresh(
        self, *, body: models.SessionRefreshRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SessionResponse]:
        """POST operation.

        /api/v1/auth/refresh
        """
        prepared = api_options(
            "postApiV1AuthRefresh",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1AuthRefresh",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SessionRefreshRequest](
                        models.SessionRefreshRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SessionResponse](models.SessionResponse)},
        )

    def get_auth_validate(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.MessageResponse]:
        """GET operation.

        /api/v1/auth/validate
        """
        prepared = api_options(
            "getApiV1AuthValidate",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1AuthValidate", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.MessageResponse](models.MessageResponse)},
        )

    def post_iam_credential_approvals(
        self, *, body: models.CredentialApprovalRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.CredentialApprovalResponse]:
        """POST operation.

        /api/v1/iam/credential-approvals
        """
        prepared = api_options(
            "postApiV1IamCredentialApprovals",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamCredentialApprovals",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.CredentialApprovalRequest](
                        models.CredentialApprovalRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CredentialApprovalResponse](
                    models.CredentialApprovalResponse
                )
            },
        )

    def get_iam_credential_approvals_by_approval_id(
        self, approval_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.CredentialApprovalRecord]:
        """GET operation.

        /api/v1/iam/credential-approvals/{approval_id}
        """
        prepared = api_options(
            "getApiV1IamCredentialApprovalsByApprovalId",
            {"approval_id": approval_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamCredentialApprovalsByApprovalId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CredentialApprovalRecord](
                    models.CredentialApprovalRecord
                )
            },
        )


class BackupsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def create(
        self, *, body: models.BackupRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/backups
        """
        prepared = api_options(
            "postApiV1Backups",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Backups",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.BackupRequest](models.BackupRequest)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get(
        self, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """GET operation.

        /api/v1/backups/{task_id}
        """
        prepared = api_options(
            "getApiV1BackupsByTaskId",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1BackupsByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_output(
        self, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.BackupDocument]:
        """GET operation.

        /api/v1/backups/{task_id}/output
        """
        prepared = api_options(
            "getApiV1BackupsByTaskIdOutput",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1BackupsByTaskIdOutput", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.BackupDocument](models.BackupDocument)},
        )


class ClassesAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.ClassesListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassExpanded]]:
        """GET operation.

        /api/v1/classes
        """
        prepared = api_options(
            "getApiV1Classes",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV1Classes", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassExpanded]](
                    builtins.list[models.HubuumClassExpanded]
                )
            },
        )

    def create(
        self, *, body: models.NewHubuumClass, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClassExpanded]:
        """POST operation.

        /api/v1/classes
        """
        prepared = api_options(
            "postApiV1Classes",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Classes",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewHubuumClass](models.NewHubuumClass)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassExpanded](
                    models.HubuumClassExpanded
                )
            },
        )

    def get_by_name(
        self, class_name: str, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClass]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassName",
            {"class_name": class_name},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassName", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumClass](models.HubuumClass)}
        )

    def delete_by_name(
        self,
        class_name: str,
        *,
        header: controls.ClassesDeleteByNameHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/by-name/{class_name}
        """
        prepared = api_options(
            "deleteApiV1ClassesByNameByClassName",
            {"class_name": class_name},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByNameByClassName", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_by_name(
        self,
        class_name: str,
        *,
        body: models.UpdateHubuumClass,
        header: controls.ClassesPatchByNameHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumClassExpanded]:
        """PATCH operation.

        /api/v1/classes/by-name/{class_name}
        """
        prepared = api_options(
            "patchApiV1ClassesByNameByClassName",
            {"class_name": class_name},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByNameByClassName",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateHubuumClass](
                        models.UpdateHubuumClass
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassExpanded](
                    models.HubuumClassExpanded
                )
            },
        )

    def get_by_name_fields(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNameFieldsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ClassFieldInventory]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/fields
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameFields",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameFields", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ClassFieldInventory](
                    models.ClassFieldInventory
                )
            },
        )

    def get_by_name_object_aggregates(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNameObjectAggregatesQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ObjectAggregateRow]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/object-aggregates
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjectAggregates",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjectAggregates", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ObjectAggregateRow]](
                    builtins.list[models.ObjectAggregateRow]
                )
            },
        )

    def get_by_name_objects(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNameObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectReadResponse]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/objects
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjects",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjects", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectReadResponse]](
                    builtins.list[models.HubuumObjectReadResponse]
                )
            },
        )

    def post_by_name_objects(
        self,
        class_name: str,
        *,
        body: models.NewHubuumObjectRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """POST operation.

        /api/v1/classes/by-name/{class_name}/objects
        """
        prepared = api_options(
            "postApiV1ClassesByNameByClassNameObjects",
            {"class_name": class_name},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByNameByClassNameObjects",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewHubuumObjectRequest](
                        models.NewHubuumObjectRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def get_by_name_objects_by_name(
        self,
        class_name: str,
        object_name: str,
        *,
        query: controls.ClassesGetByNameObjectsByNameQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObjectReadResponse]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectName",
            {"class_name": class_name, "object_name": object_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectName", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectReadResponse](
                    models.HubuumObjectReadResponse
                )
            },
        )

    def delete_by_name_objects_by_name(
        self,
        class_name: str,
        object_name: str,
        *,
        header: controls.ClassesDeleteByNameObjectsByNameHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}
        """
        prepared = api_options(
            "deleteApiV1ClassesByNameByClassNameObjectsByNameByObjectName",
            {"class_name": class_name, "object_name": object_name},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByNameByClassNameObjectsByNameByObjectName",
            json=None,
            options=prepared,
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_by_name_objects_by_name(
        self,
        class_name: str,
        object_name: str,
        *,
        body: models.UpdateHubuumObjectRequest,
        header: controls.ClassesPatchByNameObjectsByNameHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """PATCH operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}
        """
        prepared = api_options(
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectName",
            {"class_name": class_name, "object_name": object_name},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectName",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateHubuumObjectRequest](
                        models.UpdateHubuumObjectRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def patch_by_name_objects_by_name_data(
        self,
        class_name: str,
        object_name: str,
        *,
        body: models.ObjectDataPatchDocument,
        header: controls.ClassesPatchByNameObjectsByNameDataHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """PATCH operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}/data
        """
        prepared = api_options(
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectNameData",
            {"class_name": class_name, "object_name": object_name},
            None,
            header,
            options,
            content_type="application/json-patch+json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByNameByClassNameObjectsByNameByObjectNameData",
            json=api_body(
                body,
                {
                    "application/json-patch+json": TypeAdapter[models.ObjectDataPatchDocument](
                        models.ObjectDataPatchDocument
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def get_by_name_objects_by_name_related_graph(
        self, class_name: str, object_name: str, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RelatedObjectGraph]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}/related/graph
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedGraph",
            {"class_name": class_name, "object_name": object_name},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedGraph",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.RelatedObjectGraph](models.RelatedObjectGraph)},
        )

    def get_by_name_objects_by_name_related_objects(
        self,
        class_name: str,
        object_name: str,
        *,
        query: controls.ClassesGetByNameObjectsByNameRelatedObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectWithPath]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}/related/objects
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedObjects",
            {"class_name": class_name, "object_name": object_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedObjects",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectWithPath]](
                    builtins.list[models.HubuumObjectWithPath]
                )
            },
        )

    def get_by_name_objects_by_name_related_relations(
        self,
        class_name: str,
        object_name: str,
        *,
        query: controls.ClassesGetByNameObjectsByNameRelatedRelationsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectRelation]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/objects/by-name/{object_name}/related/relations
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedRelations",
            {"class_name": class_name, "object_name": object_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameObjectsByNameByObjectNameRelatedRelations",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectRelation]](
                    builtins.list[models.HubuumObjectRelation]
                )
            },
        )

    def get_by_name_permissions(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNamePermissionsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupPermission]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/permissions
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNamePermissions",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNamePermissions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupPermission]](
                    builtins.list[models.GroupPermission]
                )
            },
        )

    def get_by_name_related_classes(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNameRelatedQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassWithPath]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/related/classes
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameRelatedClasses",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameRelatedClasses", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassWithPath]](
                    builtins.list[models.HubuumClassWithPath]
                )
            },
        )

    def get_by_name_related_graph(
        self, class_name: str, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RelatedClassGraph]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/related/graph
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameRelatedGraph",
            {"class_name": class_name},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameRelatedGraph", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.RelatedClassGraph](models.RelatedClassGraph)},
        )

    def get_by_name_related_relations(
        self,
        class_name: str,
        *,
        query: controls.ClassesGetByNameRelatedRelationsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassRelation]]:
        """GET operation.

        /api/v1/classes/by-name/{class_name}/related/relations
        """
        prepared = api_options(
            "getApiV1ClassesByNameByClassNameRelatedRelations",
            {"class_name": class_name},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByNameByClassNameRelatedRelations", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassRelation]](
                    builtins.list[models.HubuumClassRelation]
                )
            },
        )

    def get(
        self, class_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClass]:
        """GET operation.

        /api/v1/classes/{class_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassId",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumClass](models.HubuumClass)}
        )

    def delete(
        self,
        class_id: int,
        *,
        header: controls.ClassesDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/{class_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassId",
            {"class_id": class_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        class_id: int,
        *,
        body: models.UpdateHubuumClass,
        header: controls.ClassesUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumClassExpanded]:
        """PATCH operation.

        /api/v1/classes/{class_id}
        """
        prepared = api_options(
            "patchApiV1ClassesByClassId",
            {"class_id": class_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByClassId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateHubuumClass](
                        models.UpdateHubuumClass
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassExpanded](
                    models.HubuumClassExpanded
                )
            },
        )

    def get_objects(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectReadResponse]]:
        """GET operation.

        /api/v1/classes/{class_id}/
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdTrailing",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdTrailing", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectReadResponse]](
                    builtins.list[models.HubuumObjectReadResponse]
                )
            },
        )

    def post_objects(
        self,
        class_id: int,
        *,
        body: models.NewHubuumObjectRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """POST operation.

        /api/v1/classes/{class_id}/
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdTrailing",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdTrailing",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewHubuumObjectRequest](
                        models.NewHubuumObjectRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def get_fields(
        self,
        class_id: models.HubuumClassID,
        *,
        query: controls.ClassesGetFieldsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ClassFieldInventory]:
        """GET operation.

        /api/v1/classes/{class_id}/fields
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdFields",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdFields", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ClassFieldInventory](
                    models.ClassFieldInventory
                )
            },
        )

    def get_history(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_HubuumClassHistory]]:
        """GET operation.

        /api/v1/classes/{class_id}/history
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdHistory",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_HubuumClassHistory]
                ](builtins.list[models.HistoryResponse_HubuumClassHistory])
            },
        )

    def get_history_as_of(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_HubuumClassHistory]:
        """GET operation.

        /api/v1/classes/{class_id}/history/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdHistoryAsOf",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_HubuumClassHistory](
                    models.HistoryResponse_HubuumClassHistory
                )
            },
        )

    def get_history_entries_by_history_id(
        self, class_id: int, history_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HistoryResponse_HubuumClassHistory]:
        """GET operation.

        /api/v1/classes/{class_id}/history/entries/{history_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdHistoryEntriesByHistoryId",
            {"class_id": class_id, "history_id": history_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdHistoryEntriesByHistoryId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_HubuumClassHistory](
                    models.HistoryResponse_HubuumClassHistory
                )
            },
        )

    def get_history_timeline(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetHistoryTimelineQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_HistoryMarker]]:
        """GET operation.

        /api/v1/classes/{class_id}/history/timeline
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdHistoryTimeline",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdHistoryTimeline", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_HistoryMarker]
                ](builtins.list[models.HistoryResponse_HistoryMarker])
            },
        )

    def get_object_aggregates(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetObjectAggregatesQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ObjectAggregateRow]]:
        """GET operation.

        /api/v1/classes/{class_id}/object-aggregates
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectAggregates",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectAggregates", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ObjectAggregateRow]](
                    builtins.list[models.ObjectAggregateRow]
                )
            },
        )

    def get_objects_history(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetObjectsHistoryQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_HubuumObjectHistory]]:
        """GET operation.

        /api/v1/classes/{class_id}/objects/history
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectsHistory",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectsHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_HubuumObjectHistory]
                ](builtins.list[models.HistoryResponse_HubuumObjectHistory])
            },
        )

    def get_objects_history_as_of(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetObjectsHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalClassObjects]:
        """GET operation.

        /api/v1/classes/{class_id}/objects/history/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectsHistoryAsOf",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectsHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalClassObjects](
                    models.HistoricalClassObjects
                )
            },
        )

    def get_objects_object_related_graph(
        self, class_id: int, object_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RelatedObjectGraph]:
        """GET operation.

        /api/v1/classes/{class_id}/objects/{object_id}/related/graph
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedGraph",
            {"class_id": class_id, "object_id": object_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedGraph", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.RelatedObjectGraph](models.RelatedObjectGraph)},
        )

    def get_objects_object_related_objects(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectsObjectRelatedObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectWithPath]]:
        """GET operation.

        /api/v1/classes/{class_id}/objects/{object_id}/related/objects
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedObjects",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedObjects", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectWithPath]](
                    builtins.list[models.HubuumObjectWithPath]
                )
            },
        )

    def get_objects_object_related_relations(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectsObjectRelatedRelationsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectRelation]]:
        """GET operation.

        /api/v1/classes/{class_id}/objects/{object_id}/related/relations
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedRelations",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdObjectsByObjectIdRelatedRelations", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectRelation]](
                    builtins.list[models.HubuumObjectRelation]
                )
            },
        )

    def get_permissions(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetPermissionsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupPermission]]:
        """GET operation.

        /api/v1/classes/{class_id}/permissions
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdPermissions",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdPermissions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupPermission]](
                    builtins.list[models.GroupPermission]
                )
            },
        )

    def get_related_classes(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetRelatedQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassWithPath]]:
        """GET operation.

        /api/v1/classes/{class_id}/related/classes
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelatedClasses",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelatedClasses", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassWithPath]](
                    builtins.list[models.HubuumClassWithPath]
                )
            },
        )

    def get_related_graph(
        self, class_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RelatedClassGraph]:
        """GET operation.

        /api/v1/classes/{class_id}/related/graph
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelatedGraph",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelatedGraph", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.RelatedClassGraph](models.RelatedClassGraph)},
        )

    def get_related_relations(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetRelatedRelationsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassRelation]]:
        """GET operation.

        /api/v1/classes/{class_id}/related/relations
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelatedRelations",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelatedRelations", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassRelation]](
                    builtins.list[models.HubuumClassRelation]
                )
            },
        )

    def post_relations(
        self,
        class_id: int,
        *,
        body: models.NewHubuumClassRelationFromClass,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumClassRelation]:
        """POST operation.

        /api/v1/classes/{class_id}/relations
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdRelations",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdRelations",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewHubuumClassRelationFromClass](
                        models.NewHubuumClassRelationFromClass
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassRelation](
                    models.HubuumClassRelation
                )
            },
        )

    def get_relations_history(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetRelationsHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalRelationships]:
        """GET operation.

        /api/v1/classes/{class_id}/relations/history
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelationsHistory",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelationsHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalRelationships](
                    models.HistoricalRelationships
                )
            },
        )

    def get_relations_history_as_of(
        self,
        class_id: int,
        *,
        query: controls.ClassesGetRelationsHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalRelationships]:
        """GET operation.

        /api/v1/classes/{class_id}/relations/history/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelationsHistoryAsOf",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelationsHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalRelationships](
                    models.HistoricalRelationships
                )
            },
        )

    def get_relations_by_relation_id(
        self, class_id: int, relation_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClassRelation]:
        """GET operation.

        /api/v1/classes/{class_id}/relations/{relation_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdRelationsByRelationId",
            {"class_id": class_id, "relation_id": relation_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdRelationsByRelationId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassRelation](
                    models.HubuumClassRelation
                )
            },
        )

    def delete_relations_by_relation_id(
        self,
        class_id: int,
        relation_id: int,
        *,
        header: controls.ClassesDeleteRelationsByRelationIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/{class_id}/relations/{relation_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdRelationsByRelationId",
            {"class_id": class_id, "relation_id": relation_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdRelationsByRelationId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def post_schema_profiles(
        self,
        class_id: int,
        *,
        body: models.SchemaProfileRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/profiles
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaProfiles",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaProfiles",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SchemaProfileRequest](
                        models.SchemaProfileRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_schema_profiles_by_task_id(
        self, class_id: int, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SchemaProfileReport]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/profiles/{task_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaProfilesByTaskId",
            {"class_id": class_id, "task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaProfilesByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaProfileReport](
                    models.SchemaProfileReport
                )
            },
        )

    def get_by_from_object_id_relations_by_to_class_id_by_to_object_id(
        self,
        class_id: int,
        from_object_id: int,
        to_class_id: int,
        to_object_id: int,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObjectRelation]:
        """GET operation.

        /api/v1/classes/{class_id}/{from_object_id}/relations/{to_class_id}/{to_object_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            {
                "class_id": class_id,
                "from_object_id": from_object_id,
                "to_class_id": to_class_id,
                "to_object_id": to_object_id,
            },
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectRelation](
                    models.HubuumObjectRelation
                )
            },
        )

    def post_by_from_object_id_relations_by_to_class_id_by_to_object_id(
        self,
        class_id: int,
        from_object_id: int,
        to_class_id: int,
        to_object_id: int,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObjectRelation]:
        """POST operation.

        /api/v1/classes/{class_id}/{from_object_id}/relations/{to_class_id}/{to_object_id}
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            {
                "class_id": class_id,
                "from_object_id": from_object_id,
                "to_class_id": to_class_id,
                "to_object_id": to_object_id,
            },
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectRelation](
                    models.HubuumObjectRelation
                )
            },
        )

    def delete_by_from_object_id_relations_by_to_class_id_by_to_object_id(  # noqa: PLR0913 -- One argument per wire location.
        self,
        class_id: int,
        from_object_id: int,
        to_class_id: int,
        to_object_id: int,
        *,
        header: controls.ClassesDeleteByFromObjectIdRelationsByToClassIdByToObjectIdHeader
        | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/{class_id}/{from_object_id}/relations/{to_class_id}/{to_object_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            {
                "class_id": class_id,
                "from_object_id": from_object_id,
                "to_class_id": to_class_id,
                "to_object_id": to_object_id,
            },
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdByFromObjectIdRelationsByToClassIdByToObjectId",
            json=None,
            options=prepared,
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def get_object(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObjectReadResponse]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectId",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectReadResponse](
                    models.HubuumObjectReadResponse
                )
            },
        )

    def delete_object(
        self,
        class_id: int,
        object_id: int,
        *,
        header: controls.ClassesDeleteObjectHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/{class_id}/{object_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdByObjectId",
            {"class_id": class_id, "object_id": object_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdByObjectId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_object(
        self,
        class_id: int,
        object_id: int,
        *,
        body: models.UpdateHubuumObjectRequest,
        header: controls.ClassesPatchObjectHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """PATCH operation.

        /api/v1/classes/{class_id}/{object_id}
        """
        prepared = api_options(
            "patchApiV1ClassesByClassIdByObjectId",
            {"class_id": class_id, "object_id": object_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByClassIdByObjectId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateHubuumObjectRequest](
                        models.UpdateHubuumObjectRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def patch_object_data(
        self,
        class_id: int,
        object_id: int,
        *,
        body: models.ObjectDataPatchDocument,
        header: controls.ClassesPatchObjectDataHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumObject]:
        """PATCH operation.

        /api/v1/classes/{class_id}/{object_id}/data
        """
        prepared = api_options(
            "patchApiV1ClassesByClassIdByObjectIdData",
            {"class_id": class_id, "object_id": object_id},
            None,
            header,
            options,
            content_type="application/json-patch+json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByClassIdByObjectIdData",
            json=api_body(
                body,
                {
                    "application/json-patch+json": TypeAdapter[models.ObjectDataPatchDocument](
                        models.ObjectDataPatchDocument
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.HubuumObject](models.HubuumObject)}
        )

    def get_object_history(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_HubuumObjectHistory]]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/history
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdHistory",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_HubuumObjectHistory]
                ](builtins.list[models.HistoryResponse_HubuumObjectHistory])
            },
        )

    def get_object_history_as_of(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_HubuumObjectHistory]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/history/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdHistoryAsOf",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_HubuumObjectHistory](
                    models.HistoryResponse_HubuumObjectHistory
                )
            },
        )

    def get_object_history_computed_as_of(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectHistoryComputedAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalComputedValues]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/history/computed/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdHistoryComputedAsOf",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdHistoryComputedAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalComputedValues](
                    models.HistoricalComputedValues
                )
            },
        )

    def get_object_history_entries_by_history_id(
        self,
        class_id: int,
        object_id: int,
        history_id: int,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_HubuumObjectHistory]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/history/entries/{history_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdHistoryEntriesByHistoryId",
            {"class_id": class_id, "object_id": object_id, "history_id": history_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdHistoryEntriesByHistoryId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_HubuumObjectHistory](
                    models.HistoryResponse_HubuumObjectHistory
                )
            },
        )

    def get_object_history_timeline(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectHistoryTimelineQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_HistoryMarker]]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/history/timeline
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdHistoryTimeline",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdHistoryTimeline", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_HistoryMarker]
                ](builtins.list[models.HistoryResponse_HistoryMarker])
            },
        )

    def get_object_relations_history(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectRelationsHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalRelationships]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/relations/history
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdRelationsHistory",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdRelationsHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalRelationships](
                    models.HistoricalRelationships
                )
            },
        )

    def get_object_relations_history_as_of(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.ClassesGetObjectRelationsHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoricalRelationships]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/relations/history/as-of
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdRelationsHistoryAsOf",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdRelationsHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoricalRelationships](
                    models.HistoricalRelationships
                )
            },
        )


class CollectionsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.CollectionsListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.Collection]]:
        """GET operation.

        /api/v1/collections
        """
        prepared = api_options(
            "getApiV1Collections",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1Collections", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.Collection]](
                    builtins.list[models.Collection]
                )
            },
        )

    def create(
        self, *, body: models.NewCollectionWithAssignee, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.Collection]:
        """POST operation.

        /api/v1/collections
        """
        prepared = api_options(
            "postApiV1Collections",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Collections",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewCollectionWithAssignee](
                        models.NewCollectionWithAssignee
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.Collection](models.Collection)}
        )

    def get(
        self, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.Collection]:
        """GET operation.

        /api/v1/collections/{collection_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionId",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.Collection](models.Collection)}
        )

    def delete(
        self,
        collection_id: int,
        *,
        header: controls.CollectionsDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/collections/{collection_id}
        """
        prepared = api_options(
            "deleteApiV1CollectionsByCollectionId",
            {"collection_id": collection_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1CollectionsByCollectionId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        collection_id: int,
        *,
        body: models.UpdateCollection,
        header: controls.CollectionsUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.Collection]:
        """PATCH operation.

        /api/v1/collections/{collection_id}
        """
        prepared = api_options(
            "patchApiV1CollectionsByCollectionId",
            {"collection_id": collection_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1CollectionsByCollectionId",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.UpdateCollection](models.UpdateCollection)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.Collection](models.Collection)}
        )

    def get_ancestors(
        self, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.Collection]]:
        """GET operation.

        /api/v1/collections/{collection_id}/ancestors
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdAncestors",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdAncestors", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.Collection]](
                    builtins.list[models.Collection]
                )
            },
        )

    def get_children(
        self, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.Collection]]:
        """GET operation.

        /api/v1/collections/{collection_id}/children
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdChildren",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdChildren", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.Collection]](
                    builtins.list[models.Collection]
                )
            },
        )

    def get_has_permissions_by_permission(
        self,
        collection_id: int,
        permission: models.Permissions,
        *,
        query: controls.CollectionsGetHasPermissionsByPermissionQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupResponse]]:
        """GET operation.

        /api/v1/collections/{collection_id}/has_permissions/{permission}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdHasPermissionsByPermission",
            {"collection_id": collection_id, "permission": permission},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdHasPermissionsByPermission",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupResponse]](
                    builtins.list[models.GroupResponse]
                )
            },
        )

    def get_history(
        self,
        collection_id: int,
        *,
        query: controls.CollectionsGetHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_CollectionHistory]]:
        """GET operation.

        /api/v1/collections/{collection_id}/history
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdHistory",
            {"collection_id": collection_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_CollectionHistory]
                ](builtins.list[models.HistoryResponse_CollectionHistory])
            },
        )

    def get_history_as_of(
        self,
        collection_id: int,
        *,
        query: controls.CollectionsGetHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_CollectionHistory]:
        """GET operation.

        /api/v1/collections/{collection_id}/history/as-of
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdHistoryAsOf",
            {"collection_id": collection_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_CollectionHistory](
                    models.HistoryResponse_CollectionHistory
                )
            },
        )

    def put_parent(
        self,
        collection_id: int,
        *,
        body: models.UpdateCollectionParent,
        header: controls.CollectionsPutParentHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.Collection]:
        """PUT operation.

        /api/v1/collections/{collection_id}/parent
        """
        prepared = api_options(
            "putApiV1CollectionsByCollectionIdParent",
            {"collection_id": collection_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1CollectionsByCollectionIdParent",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateCollectionParent](
                        models.UpdateCollectionParent
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.Collection](models.Collection)}
        )

    def get_permissions(
        self,
        collection_id: int,
        *,
        query: controls.CollectionsGetPermissionsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissions",
            {"collection_id": collection_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def get_permissions_effective_group_by_group_id(
        self, collection_id: int, group_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.EffectiveGroupPermission]]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions/effective/group/{group_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissionsEffectiveGroupByGroupId",
            {"collection_id": collection_id, "group_id": group_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissionsEffectiveGroupByGroupId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EffectiveGroupPermission]](
                    builtins.list[models.EffectiveGroupPermission]
                )
            },
        )

    def get_permissions_effective_principal_by_principal_id(
        self, collection_id: int, principal_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.EffectiveGroupPermission]]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions/effective/principal/{principal_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissionsEffectivePrincipalByPrincipalId",
            {"collection_id": collection_id, "principal_id": principal_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissionsEffectivePrincipalByPrincipalId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EffectiveGroupPermission]](
                    builtins.list[models.EffectiveGroupPermission]
                )
            },
        )

    def get_permissions_group_by_group_id(
        self, collection_id: int, group_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.CollectionPermissionSet]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            {"collection_id": collection_id, "group_id": group_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def put_permissions_group_by_group_id(
        self,
        collection_id: int,
        group_id: int,
        *,
        body: builtins.list[models.Permissions],
        header: controls.CollectionsPutPermissionsGroupByGroupIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """PUT operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}
        """
        prepared = api_options(
            "putApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            {"collection_id": collection_id, "group_id": group_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[builtins.list[models.Permissions]](
                        builtins.list[models.Permissions]
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def post_permissions_group_by_group_id(
        self,
        collection_id: int,
        group_id: int,
        *,
        body: builtins.list[models.Permissions],
        header: controls.CollectionsPostPermissionsGroupByGroupIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """POST operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}
        """
        prepared = api_options(
            "postApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            {"collection_id": collection_id, "group_id": group_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[builtins.list[models.Permissions]](
                        builtins.list[models.Permissions]
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def delete_permissions_group_by_group_id(
        self,
        collection_id: int,
        group_id: int,
        *,
        header: controls.CollectionsDeletePermissionsGroupByGroupIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """DELETE operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}
        """
        prepared = api_options(
            "deleteApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            {"collection_id": collection_id, "group_id": group_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1CollectionsByCollectionIdPermissionsGroupByGroupId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def get_permissions_group_by_group_id_by_permission(
        self,
        collection_id: int,
        group_id: int,
        permission: models.Permissions,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            {"collection_id": collection_id, "group_id": group_id, "permission": permission},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            json=None,
            options=prepared,
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def post_permissions_group_by_group_id_by_permission(
        self,
        collection_id: int,
        group_id: int,
        permission: models.Permissions,
        *,
        header: controls.CollectionsPostPermissionsGroupByGroupIdByPermissionHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """POST operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}
        """
        prepared = api_options(
            "postApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            {"collection_id": collection_id, "group_id": group_id, "permission": permission},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def delete_permissions_group_by_group_id_by_permission(
        self,
        collection_id: int,
        group_id: int,
        permission: models.Permissions,
        *,
        header: controls.CollectionsDeletePermissionsGroupByGroupIdByPermissionHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionPermissionSet]:
        """DELETE operation.

        /api/v1/collections/{collection_id}/permissions/group/{group_id}/{permission}
        """
        prepared = api_options(
            "deleteApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            {"collection_id": collection_id, "group_id": group_id, "permission": permission},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1CollectionsByCollectionIdPermissionsGroupByGroupIdByPermission",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionPermissionSet](
                    models.CollectionPermissionSet
                )
            },
        )

    def get_permissions_principal_by_principal_id(
        self,
        collection_id: int,
        principal_id: int,
        *,
        query: controls.CollectionsGetPermissionsPrincipalByPrincipalIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupPermission]]:
        """GET operation.

        /api/v1/collections/{collection_id}/permissions/principal/{principal_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdPermissionsPrincipalByPrincipalId",
            {"collection_id": collection_id, "principal_id": principal_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdPermissionsPrincipalByPrincipalId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupPermission]](
                    builtins.list[models.GroupPermission]
                )
            },
        )


class ComputedFieldsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_classes_by_class_id_computed_fields(
        self, class_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ComputedFieldListResponse]:
        """GET operation.

        /api/v1/classes/{class_id}/computed-fields
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdComputedFields",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdComputedFields", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldListResponse](
                    models.ComputedFieldListResponse
                )
            },
        )

    def post_classes_by_class_id_computed_fields(
        self,
        class_id: int,
        *,
        body: models.ComputedFieldDefinitionRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldMutationResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/computed-fields
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdComputedFields",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdComputedFields",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ComputedFieldDefinitionRequest](
                        models.ComputedFieldDefinitionRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldMutationResponse](
                    models.ComputedFieldMutationResponse
                )
            },
        )

    def post_classes_by_class_id_computed_fields_preview(
        self,
        class_id: int,
        *,
        body: models.ComputedFieldPreviewRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldPreviewResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/computed-fields/preview
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdComputedFieldsPreview",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdComputedFieldsPreview",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ComputedFieldPreviewRequest](
                        models.ComputedFieldPreviewRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldPreviewResponse](
                    models.ComputedFieldPreviewResponse
                )
            },
        )

    def post_classes_by_class_id_computed_fields_rebuild(
        self, class_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ClassComputationState]:
        """POST operation.

        /api/v1/classes/{class_id}/computed-fields/rebuild
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdComputedFieldsRebuild",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdComputedFieldsRebuild", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ClassComputationState](
                    models.ClassComputationState
                )
            },
        )

    def get_classes_by_class_id_computed_fields_by_field_id(
        self, class_id: int, field_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ComputedFieldDefinition]:
        """GET operation.

        /api/v1/classes/{class_id}/computed-fields/{field_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdComputedFieldsByFieldId",
            {"class_id": class_id, "field_id": field_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdComputedFieldsByFieldId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldDefinition](
                    models.ComputedFieldDefinition
                )
            },
        )

    def delete_classes_by_class_id_computed_fields_by_field_id(
        self,
        class_id: int,
        field_id: int,
        *,
        header: controls.ComputedFieldsDeleteClassesByClassIdByFieldIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldDeleteResponse]:
        """DELETE operation.

        /api/v1/classes/{class_id}/computed-fields/{field_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdComputedFieldsByFieldId",
            {"class_id": class_id, "field_id": field_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdComputedFieldsByFieldId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldDeleteResponse](
                    models.ComputedFieldDeleteResponse
                )
            },
        )

    def patch_classes_by_class_id_computed_fields_by_field_id(
        self,
        class_id: int,
        field_id: int,
        *,
        body: models.ComputedFieldDefinitionPatch,
        header: controls.ComputedFieldsPatchClassesByClassIdByFieldIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldMutationResponse]:
        """PATCH operation.

        /api/v1/classes/{class_id}/computed-fields/{field_id}
        """
        prepared = api_options(
            "patchApiV1ClassesByClassIdComputedFieldsByFieldId",
            {"class_id": class_id, "field_id": field_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ClassesByClassIdComputedFieldsByFieldId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ComputedFieldDefinitionPatch](
                        models.ComputedFieldDefinitionPatch
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldMutationResponse](
                    models.ComputedFieldMutationResponse
                )
            },
        )

    def get_iam_me_computed_fields(
        self,
        *,
        query: controls.ComputedFieldsGetIamMeQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ComputedFieldDefinition]]:
        """GET operation.

        /api/v1/iam/me/computed-fields
        """
        prepared = api_options(
            "getApiV1IamMeComputedFields",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMeComputedFields", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ComputedFieldDefinition]](
                    builtins.list[models.ComputedFieldDefinition]
                )
            },
        )

    def post_iam_me_computed_fields(
        self,
        *,
        body: models.PersonalComputedFieldDefinitionRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldDefinition]:
        """POST operation.

        /api/v1/iam/me/computed-fields
        """
        prepared = api_options(
            "postApiV1IamMeComputedFields",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamMeComputedFields",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.PersonalComputedFieldDefinitionRequest](
                        models.PersonalComputedFieldDefinitionRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldDefinition](
                    models.ComputedFieldDefinition
                )
            },
        )

    def post_iam_me_computed_fields_preview(
        self, *, body: models.ComputedFieldPreviewRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ComputedFieldPreviewResponse]:
        """POST operation.

        /api/v1/iam/me/computed-fields/preview
        """
        prepared = api_options(
            "postApiV1IamMeComputedFieldsPreview",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamMeComputedFieldsPreview",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ComputedFieldPreviewRequest](
                        models.ComputedFieldPreviewRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldPreviewResponse](
                    models.ComputedFieldPreviewResponse
                )
            },
        )

    def get_iam_me_computed_fields_by_field_id(
        self, field_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ComputedFieldDefinition]:
        """GET operation.

        /api/v1/iam/me/computed-fields/{field_id}
        """
        prepared = api_options(
            "getApiV1IamMeComputedFieldsByFieldId",
            {"field_id": field_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMeComputedFieldsByFieldId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldDefinition](
                    models.ComputedFieldDefinition
                )
            },
        )

    def delete_iam_me_computed_fields_by_field_id(
        self,
        field_id: int,
        *,
        header: controls.ComputedFieldsDeleteIamMeByFieldIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/me/computed-fields/{field_id}
        """
        prepared = api_options(
            "deleteApiV1IamMeComputedFieldsByFieldId",
            {"field_id": field_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamMeComputedFieldsByFieldId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_iam_me_computed_fields_by_field_id(
        self,
        field_id: int,
        *,
        body: models.ComputedFieldDefinitionPatch,
        header: controls.ComputedFieldsPatchIamMeByFieldIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ComputedFieldDefinition]:
        """PATCH operation.

        /api/v1/iam/me/computed-fields/{field_id}
        """
        prepared = api_options(
            "patchApiV1IamMeComputedFieldsByFieldId",
            {"field_id": field_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamMeComputedFieldsByFieldId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ComputedFieldDefinitionPatch](
                        models.ComputedFieldDefinitionPatch
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ComputedFieldDefinition](
                    models.ComputedFieldDefinition
                )
            },
        )


class ConfigAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *, options: OpenAPIOptions | None = None) -> APIResponse[models.ClientConfig]:
        """GET operation.

        /api/v1/config
        """
        prepared = api_options(
            "getApiV1Config", {}, None, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV1Config", json=None, options=prepared)
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.ClientConfig](models.ClientConfig)}
        )


class EventDeliveriesAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, query: controls.EventDeliveriesListQuery, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.EventDeliveryResponse]]:
        """GET operation.

        /api/v1/event-deliveries
        """
        prepared = api_options(
            "getApiV1EventDeliveries",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1EventDeliveries", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventDeliveryResponse]](
                    builtins.list[models.EventDeliveryResponse]
                )
            },
        )

    def get_health(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventDeliveryHealthResponse]:
        """GET operation.

        /api/v1/event-deliveries/health
        """
        prepared = api_options(
            "getApiV1EventDeliveriesHealth",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1EventDeliveriesHealth", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventDeliveryHealthResponse](
                    models.EventDeliveryHealthResponse
                )
            },
        )

    def get(
        self, delivery_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventDeliveryResponse]:
        """GET operation.

        /api/v1/event-deliveries/{delivery_id}
        """
        prepared = api_options(
            "getApiV1EventDeliveriesByDeliveryId",
            {"delivery_id": delivery_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1EventDeliveriesByDeliveryId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventDeliveryResponse](
                    models.EventDeliveryResponse
                )
            },
        )

    def post_dead(
        self, delivery_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventDeliveryUpdateResponse]:
        """POST operation.

        /api/v1/event-deliveries/{delivery_id}/dead
        """
        prepared = api_options(
            "postApiV1EventDeliveriesByDeliveryIdDead",
            {"delivery_id": delivery_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1EventDeliveriesByDeliveryIdDead", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventDeliveryUpdateResponse](
                    models.EventDeliveryUpdateResponse
                )
            },
        )

    def post_retry(
        self, delivery_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventDeliveryUpdateResponse]:
        """POST operation.

        /api/v1/event-deliveries/{delivery_id}/retry
        """
        prepared = api_options(
            "postApiV1EventDeliveriesByDeliveryIdRetry",
            {"delivery_id": delivery_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1EventDeliveriesByDeliveryIdRetry", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventDeliveryUpdateResponse](
                    models.EventDeliveryUpdateResponse
                )
            },
        )


class EventSinksAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_collections_by_collection_id_event_sinks(
        self, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.CollectionEventSink]]:
        """GET operation.

        /api/v1/collections/{collection_id}/event-sinks
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdEventSinks",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdEventSinks", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.CollectionEventSink]](
                    builtins.list[models.CollectionEventSink]
                )
            },
        )

    def post_collections_by_collection_id_event_sinks(
        self,
        collection_id: int,
        *,
        body: models.NewEventSink,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionEventSink]:
        """POST operation.

        /api/v1/collections/{collection_id}/event-sinks
        """
        prepared = api_options(
            "postApiV1CollectionsByCollectionIdEventSinks",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1CollectionsByCollectionIdEventSinks",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewEventSink](models.NewEventSink)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionEventSink](
                    models.CollectionEventSink
                )
            },
        )

    def get_collections_by_collection_id_event_sinks_by_sink_id(
        self, collection_id: int, sink_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.CollectionEventSink]:
        """GET operation.

        /api/v1/collections/{collection_id}/event-sinks/{sink_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdEventSinksBySinkId",
            {"collection_id": collection_id, "sink_id": sink_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdEventSinksBySinkId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionEventSink](
                    models.CollectionEventSink
                )
            },
        )

    def delete_collections_by_collection_id_event_sinks_by_sink_id(
        self,
        collection_id: int,
        sink_id: int,
        *,
        header: controls.EventSinksDeleteCollectionsByCollectionIdBySinkIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/collections/{collection_id}/event-sinks/{sink_id}
        """
        prepared = api_options(
            "deleteApiV1CollectionsByCollectionIdEventSinksBySinkId",
            {"collection_id": collection_id, "sink_id": sink_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1CollectionsByCollectionIdEventSinksBySinkId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_collections_by_collection_id_event_sinks_by_sink_id(
        self,
        collection_id: int,
        sink_id: int,
        *,
        body: models.UpdateEventSink,
        header: controls.EventSinksPatchCollectionsByCollectionIdBySinkIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CollectionEventSink]:
        """PATCH operation.

        /api/v1/collections/{collection_id}/event-sinks/{sink_id}
        """
        prepared = api_options(
            "patchApiV1CollectionsByCollectionIdEventSinksBySinkId",
            {"collection_id": collection_id, "sink_id": sink_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1CollectionsByCollectionIdEventSinksBySinkId",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.UpdateEventSink](models.UpdateEventSink)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CollectionEventSink](
                    models.CollectionEventSink
                )
            },
        )

    def get_event_sinks(
        self,
        *,
        query: controls.EventSinksGetQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventSink]]:
        """GET operation.

        /api/v1/event-sinks
        """
        prepared = api_options(
            "getApiV1EventSinks",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV1EventSinks", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventSink]](
                    builtins.list[models.EventSink]
                )
            },
        )

    def post_event_sinks(
        self, *, body: models.NewEventSink, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventSink]:
        """POST operation.

        /api/v1/event-sinks
        """
        prepared = api_options(
            "postApiV1EventSinks",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1EventSinks",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewEventSink](models.NewEventSink)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.EventSink](models.EventSink)}
        )

    def get_event_sinks_by_sink_id(
        self, sink_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventSink]:
        """GET operation.

        /api/v1/event-sinks/{sink_id}
        """
        prepared = api_options(
            "getApiV1EventSinksBySinkId",
            {"sink_id": sink_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1EventSinksBySinkId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.EventSink](models.EventSink)}
        )

    def delete_event_sinks_by_sink_id(
        self,
        sink_id: int,
        *,
        header: controls.EventSinksDeleteBySinkIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/event-sinks/{sink_id}
        """
        prepared = api_options(
            "deleteApiV1EventSinksBySinkId",
            {"sink_id": sink_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1EventSinksBySinkId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_event_sinks_by_sink_id(
        self,
        sink_id: int,
        *,
        body: models.UpdateEventSink,
        header: controls.EventSinksPatchBySinkIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.EventSink]:
        """PATCH operation.

        /api/v1/event-sinks/{sink_id}
        """
        prepared = api_options(
            "patchApiV1EventSinksBySinkId",
            {"sink_id": sink_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1EventSinksBySinkId",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.UpdateEventSink](models.UpdateEventSink)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.EventSink](models.EventSink)}
        )

    def get_event_sinks_by_sink_id_collections(
        self, sink_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[int]]:
        """GET operation.

        /api/v1/event-sinks/{sink_id}/collections
        """
        prepared = api_options(
            "getApiV1EventSinksBySinkIdCollections",
            {"sink_id": sink_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1EventSinksBySinkIdCollections", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[builtins.list[int]](builtins.list[int])}
        )

    def put_event_sinks_by_sink_id_collections_by_collection_id(
        self, sink_id: int, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[None]:
        """PUT operation.

        /api/v1/event-sinks/{sink_id}/collections/{collection_id}
        """
        prepared = api_options(
            "putApiV1EventSinksBySinkIdCollectionsByCollectionId",
            {"sink_id": sink_id, "collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1EventSinksBySinkIdCollectionsByCollectionId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def delete_event_sinks_by_sink_id_collections_by_collection_id(
        self, sink_id: int, collection_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/event-sinks/{sink_id}/collections/{collection_id}
        """
        prepared = api_options(
            "deleteApiV1EventSinksBySinkIdCollectionsByCollectionId",
            {"sink_id": sink_id, "collection_id": collection_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1EventSinksBySinkIdCollectionsByCollectionId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def post_event_sinks_by_sink_id_preview(
        self,
        sink_id: int,
        *,
        body: models.EventNotificationRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.EventNotificationPreview]:
        """POST operation.

        /api/v1/event-sinks/{sink_id}/preview
        """
        prepared = api_options(
            "postApiV1EventSinksBySinkIdPreview",
            {"sink_id": sink_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1EventSinksBySinkIdPreview",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.EventNotificationRequest](
                        models.EventNotificationRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventNotificationPreview](
                    models.EventNotificationPreview
                )
            },
        )

    def post_event_sinks_by_sink_id_test(
        self,
        sink_id: int,
        *,
        body: models.EventNotificationRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.EventDeliveryResponse]:
        """POST operation.

        /api/v1/event-sinks/{sink_id}/test
        """
        prepared = api_options(
            "postApiV1EventSinksBySinkIdTest",
            {"sink_id": sink_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1EventSinksBySinkIdTest",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.EventNotificationRequest](
                        models.EventNotificationRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.EventDeliveryResponse](
                    models.EventDeliveryResponse
                )
            },
        )


class EventSubscriptionsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_collections_by_collection_id_event_subscriptions(
        self,
        collection_id: int,
        *,
        query: controls.EventSubscriptionsGetCollectionsByCollectionIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventSubscription]]:
        """GET operation.

        /api/v1/collections/{collection_id}/event-subscriptions
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdEventSubscriptions",
            {"collection_id": collection_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdEventSubscriptions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventSubscription]](
                    builtins.list[models.EventSubscription]
                )
            },
        )

    def post_collections_by_collection_id_event_subscriptions(
        self,
        collection_id: int,
        *,
        body: models.NewEventSubscription,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.EventSubscription]:
        """POST operation.

        /api/v1/collections/{collection_id}/event-subscriptions
        """
        prepared = api_options(
            "postApiV1CollectionsByCollectionIdEventSubscriptions",
            {"collection_id": collection_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1CollectionsByCollectionIdEventSubscriptions",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewEventSubscription](
                        models.NewEventSubscription
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.EventSubscription](models.EventSubscription)},
        )

    def get_collections_by_collection_id_event_subscriptions_by_subscription_id(
        self, collection_id: int, subscription_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.EventSubscription]:
        """GET operation.

        /api/v1/collections/{collection_id}/event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            {"collection_id": collection_id, "subscription_id": subscription_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.EventSubscription](models.EventSubscription)},
        )

    def delete_collections_by_collection_id_event_subscriptions_by_subscription_id(
        self,
        collection_id: int,
        subscription_id: int,
        *,
        header: controls.EventSubscriptionsDeleteCollectionsByCollectionIdBySubscriptionIdHeader
        | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/collections/{collection_id}/event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "deleteApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            {"collection_id": collection_id, "subscription_id": subscription_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            json=None,
            options=prepared,
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_collections_by_collection_id_event_subscriptions_by_subscription_id(
        self,
        collection_id: int,
        subscription_id: int,
        *,
        body: models.UpdateEventSubscription,
        header: controls.EventSubscriptionsPatchCollectionsByCollectionIdBySubscriptionIdHeader
        | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.EventSubscription]:
        """PATCH operation.

        /api/v1/collections/{collection_id}/event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "patchApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            {"collection_id": collection_id, "subscription_id": subscription_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1CollectionsByCollectionIdEventSubscriptionsBySubscriptionId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateEventSubscription](
                        models.UpdateEventSubscription
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.EventSubscription](models.EventSubscription)},
        )

    def get_system_event_subscriptions(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.SystemEventSubscription]]:
        """GET operation.

        /api/v1/system-event-subscriptions
        """
        prepared = api_options(
            "getApiV1SystemEventSubscriptions",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1SystemEventSubscriptions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.SystemEventSubscription]](
                    builtins.list[models.SystemEventSubscription]
                )
            },
        )

    def post_system_event_subscriptions(
        self, *, body: models.NewEventSubscription, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SystemEventSubscription]:
        """POST operation.

        /api/v1/system-event-subscriptions
        """
        prepared = api_options(
            "postApiV1SystemEventSubscriptions",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1SystemEventSubscriptions",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewEventSubscription](
                        models.NewEventSubscription
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SystemEventSubscription](
                    models.SystemEventSubscription
                )
            },
        )

    def get_system_event_subscriptions_by_subscription_id(
        self, subscription_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SystemEventSubscription]:
        """GET operation.

        /api/v1/system-event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "getApiV1SystemEventSubscriptionsBySubscriptionId",
            {"subscription_id": subscription_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1SystemEventSubscriptionsBySubscriptionId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SystemEventSubscription](
                    models.SystemEventSubscription
                )
            },
        )

    def delete_system_event_subscriptions_by_subscription_id(
        self,
        subscription_id: int,
        *,
        header: controls.EventSubscriptionsDeleteSystemBySubscriptionIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/system-event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "deleteApiV1SystemEventSubscriptionsBySubscriptionId",
            {"subscription_id": subscription_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1SystemEventSubscriptionsBySubscriptionId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_system_event_subscriptions_by_subscription_id(
        self,
        subscription_id: int,
        *,
        body: models.UpdateEventSubscription,
        header: controls.EventSubscriptionsPatchSystemBySubscriptionIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SystemEventSubscription]:
        """PATCH operation.

        /api/v1/system-event-subscriptions/{subscription_id}
        """
        prepared = api_options(
            "patchApiV1SystemEventSubscriptionsBySubscriptionId",
            {"subscription_id": subscription_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1SystemEventSubscriptionsBySubscriptionId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateEventSubscription](
                        models.UpdateEventSubscription
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SystemEventSubscription](
                    models.SystemEventSubscription
                )
            },
        )


class EventsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_classes_by_class_id_events(
        self,
        class_id: int,
        *,
        query: controls.EventsGetClassesByClassIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/classes/{class_id}/events
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdEvents",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_classes_by_class_id_object_events(
        self,
        class_id: int,
        object_id: int,
        *,
        query: controls.EventsGetClassesByClassIdObjectQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/classes/{class_id}/{object_id}/events
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdByObjectIdEvents",
            {"class_id": class_id, "object_id": object_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdByObjectIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_collections_by_collection_id_events(
        self,
        collection_id: int,
        *,
        query: controls.EventsGetCollectionsByCollectionIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/collections/{collection_id}/events
        """
        prepared = api_options(
            "getApiV1CollectionsByCollectionIdEvents",
            {"collection_id": collection_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1CollectionsByCollectionIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_events(
        self, *, query: controls.EventsGetQuery | None = None, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/events
        """
        prepared = api_options(
            "getApiV1Events", {}, query, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV1Events", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_export_templates_by_template_id_events(
        self,
        template_id: int,
        *,
        query: controls.EventsGetExportTemplatesByTemplateIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/export-templates/{template_id}/events
        """
        prepared = api_options(
            "getApiV1ExportTemplatesByTemplateIdEvents",
            {"template_id": template_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportTemplatesByTemplateIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_iam_groups_by_group_id_events(
        self,
        group_id: int,
        *,
        query: controls.EventsGetIamGroupsByGroupIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/iam/groups/{group_id}/events
        """
        prepared = api_options(
            "getApiV1IamGroupsByGroupIdEvents",
            {"group_id": group_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamGroupsByGroupIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_iam_users_by_user_id_events(
        self,
        user_id: int,
        *,
        query: controls.EventsGetIamUsersByUserIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/iam/users/{user_id}/events
        """
        prepared = api_options(
            "getApiV1IamUsersByUserIdEvents",
            {"user_id": user_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamUsersByUserIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )

    def get_remote_targets_by_target_id_events(
        self,
        target_id: int,
        *,
        query: controls.EventsGetRemoteTargetsByTargetIdQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.EventResponse]]:
        """GET operation.

        /api/v1/remote-targets/{target_id}/events
        """
        prepared = api_options(
            "getApiV1RemoteTargetsByTargetIdEvents",
            {"target_id": target_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RemoteTargetsByTargetIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.EventResponse]](
                    builtins.list[models.EventResponse]
                )
            },
        )


class ExportTemplatesAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.ExportTemplatesListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ExportTemplate]]:
        """GET operation.

        /api/v1/export-templates
        """
        prepared = api_options(
            "getApiV1ExportTemplates",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportTemplates", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ExportTemplate]](
                    builtins.list[models.ExportTemplate]
                )
            },
        )

    def create(
        self, *, body: models.NewExportTemplate, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ExportTemplate]:
        """POST operation.

        /api/v1/export-templates
        """
        prepared = api_options(
            "postApiV1ExportTemplates",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ExportTemplates",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewExportTemplate](
                        models.NewExportTemplate
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.ExportTemplate](models.ExportTemplate)},
        )

    def get(
        self, template_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ExportTemplate]:
        """GET operation.

        /api/v1/export-templates/{template_id}
        """
        prepared = api_options(
            "getApiV1ExportTemplatesByTemplateId",
            {"template_id": template_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportTemplatesByTemplateId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.ExportTemplate](models.ExportTemplate)},
        )

    def delete(
        self,
        template_id: int,
        *,
        header: controls.ExportTemplatesDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/export-templates/{template_id}
        """
        prepared = api_options(
            "deleteApiV1ExportTemplatesByTemplateId",
            {"template_id": template_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ExportTemplatesByTemplateId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        template_id: int,
        *,
        body: models.UpdateExportTemplate,
        header: controls.ExportTemplatesUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ExportTemplate]:
        """PATCH operation.

        /api/v1/export-templates/{template_id}
        """
        prepared = api_options(
            "patchApiV1ExportTemplatesByTemplateId",
            {"template_id": template_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1ExportTemplatesByTemplateId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateExportTemplate](
                        models.UpdateExportTemplate
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.ExportTemplate](models.ExportTemplate)},
        )

    def post_exports(
        self,
        template_id: int,
        *,
        body: models.ExportTemplateRunRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/export-templates/{template_id}/exports
        """
        prepared = api_options(
            "postApiV1ExportTemplatesByTemplateIdExports",
            {"template_id": template_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ExportTemplatesByTemplateIdExports",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.ExportTemplateRunRequest](
                        models.ExportTemplateRunRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_history(
        self,
        template_id: int,
        *,
        query: controls.ExportTemplatesGetHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_ExportTemplateHistory]]:
        """GET operation.

        /api/v1/export-templates/{template_id}/history
        """
        prepared = api_options(
            "getApiV1ExportTemplatesByTemplateIdHistory",
            {"template_id": template_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportTemplatesByTemplateIdHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_ExportTemplateHistory]
                ](builtins.list[models.HistoryResponse_ExportTemplateHistory])
            },
        )

    def get_history_as_of(
        self,
        template_id: int,
        *,
        query: controls.ExportTemplatesGetHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_ExportTemplateHistory]:
        """GET operation.

        /api/v1/export-templates/{template_id}/history/as-of
        """
        prepared = api_options(
            "getApiV1ExportTemplatesByTemplateIdHistoryAsOf",
            {"template_id": template_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportTemplatesByTemplateIdHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_ExportTemplateHistory](
                    models.HistoryResponse_ExportTemplateHistory
                )
            },
        )


class ExportsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def create(
        self, *, body: models.ExportRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/exports
        """
        prepared = api_options(
            "postApiV1Exports",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Exports",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.ExportRequest](models.ExportRequest)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get(
        self, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """GET operation.

        /api/v1/exports/{task_id}
        """
        prepared = api_options(
            "getApiV1ExportsByTaskId",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ExportsByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_output(
        self,
        task_id: int,
        *,
        accept: Literal[
            "application/json", "text/plain", "text/html", "text/csv"
        ] = "application/json",
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ExportJsonResponse | str]:
        """GET operation.

        /api/v1/exports/{task_id}/output
        """
        prepared = api_options(
            "getApiV1ExportsByTaskIdOutput",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept=accept,
        )
        response = self._client.openapi._response(
            "getApiV1ExportsByTaskIdOutput", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ExportJsonResponse | str](
                    models.ExportJsonResponse
                ),
                "text/plain": TypeAdapter[models.ExportJsonResponse | str](str),
                "text/html": TypeAdapter[models.ExportJsonResponse | str](str),
                "text/csv": TypeAdapter[models.ExportJsonResponse | str](str),
            },
        )


class GroupsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.GroupsListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupResponse]]:
        """GET operation.

        /api/v1/iam/groups
        """
        prepared = api_options(
            "getApiV1IamGroups",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV1IamGroups", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupResponse]](
                    builtins.list[models.GroupResponse]
                )
            },
        )

    def create(
        self, *, body: models.NewGroup, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.GroupPointResponse]:
        """POST operation.

        /api/v1/iam/groups
        """
        prepared = api_options(
            "postApiV1IamGroups",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamGroups",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewGroup](models.NewGroup)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.GroupPointResponse](models.GroupPointResponse)},
        )

    def get(
        self, group_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.GroupPointResponse]:
        """GET operation.

        /api/v1/iam/groups/{group_id}
        """
        prepared = api_options(
            "getApiV1IamGroupsByGroupId",
            {"group_id": group_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamGroupsByGroupId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.GroupPointResponse](models.GroupPointResponse)},
        )

    def delete(
        self,
        group_id: int,
        *,
        header: controls.GroupsDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/groups/{group_id}
        """
        prepared = api_options(
            "deleteApiV1IamGroupsByGroupId",
            {"group_id": group_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamGroupsByGroupId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        group_id: int,
        *,
        body: models.UpdateGroup,
        header: controls.GroupsUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.GroupPointResponse]:
        """PATCH operation.

        /api/v1/iam/groups/{group_id}
        """
        prepared = api_options(
            "patchApiV1IamGroupsByGroupId",
            {"group_id": group_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamGroupsByGroupId",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.UpdateGroup](models.UpdateGroup)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.GroupPointResponse](models.GroupPointResponse)},
        )

    def get_members(
        self,
        group_id: int,
        *,
        query: controls.GroupsGetMembersQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.PrincipalMemberResponse]]:
        """GET operation.

        /api/v1/iam/groups/{group_id}/members
        """
        prepared = api_options(
            "getApiV1IamGroupsByGroupIdMembers",
            {"group_id": group_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamGroupsByGroupIdMembers", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.PrincipalMemberResponse]](
                    builtins.list[models.PrincipalMemberResponse]
                )
            },
        )

    def get_members_by_principal_id(
        self, group_id: int, principal_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.PrincipalMemberResponse]:
        """GET operation.

        /api/v1/iam/groups/{group_id}/members/{principal_id}
        """
        prepared = api_options(
            "getApiV1IamGroupsByGroupIdMembersByPrincipalId",
            {"group_id": group_id, "principal_id": principal_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamGroupsByGroupIdMembersByPrincipalId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalMemberResponse](
                    models.PrincipalMemberResponse
                )
            },
        )

    def post_members_by_principal_id(
        self,
        group_id: int,
        principal_id: int,
        *,
        header: controls.GroupsPostMembersByPrincipalIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.PrincipalMemberResponse]:
        """POST operation.

        /api/v1/iam/groups/{group_id}/members/{principal_id}
        """
        prepared = api_options(
            "postApiV1IamGroupsByGroupIdMembersByPrincipalId",
            {"group_id": group_id, "principal_id": principal_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamGroupsByGroupIdMembersByPrincipalId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalMemberResponse](
                    models.PrincipalMemberResponse
                )
            },
        )

    def delete_members_by_principal_id(
        self,
        group_id: int,
        principal_id: int,
        *,
        header: controls.GroupsDeleteMembersByPrincipalIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/groups/{group_id}/members/{principal_id}
        """
        prepared = api_options(
            "deleteApiV1IamGroupsByGroupIdMembersByPrincipalId",
            {"group_id": group_id, "principal_id": principal_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamGroupsByGroupIdMembersByPrincipalId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})


class ImportsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def create(
        self,
        *,
        body: models.ImportRequest,
        header: controls.ImportsCreateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/imports
        """
        prepared = api_options(
            "postApiV1Imports",
            {},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Imports",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.ImportRequest](models.ImportRequest)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get(
        self, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """GET operation.

        /api/v1/imports/{task_id}
        """
        prepared = api_options(
            "getApiV1ImportsByTaskId",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ImportsByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_results(
        self,
        task_id: int,
        *,
        query: controls.ImportsGetResultsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ImportTaskResultResponse]]:
        """GET operation.

        /api/v1/imports/{task_id}/results
        """
        prepared = api_options(
            "getApiV1ImportsByTaskIdResults",
            {"task_id": task_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ImportsByTaskIdResults", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ImportTaskResultResponse]](
                    builtins.list[models.ImportTaskResultResponse]
                )
            },
        )


class MetaAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_counts(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.CountsResponse]:
        """GET operation.

        /api/v0/meta/counts
        """
        prepared = api_options(
            "getApiV0MetaCounts",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV0MetaCounts", json=None, options=prepared)
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.CountsResponse](models.CountsResponse)},
        )

    def get_db(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.DbStateResponse]:
        """GET operation.

        /api/v0/meta/db
        """
        prepared = api_options(
            "getApiV0MetaDb", {}, None, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV0MetaDb", json=None, options=prepared)
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.DbStateResponse](models.DbStateResponse)},
        )

    def get_login_rate_limit(
        self,
        *,
        query: controls.MetaGetLoginRateLimitQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.LoginRateLimitStateResponse]:
        """GET operation.

        /api/v0/meta/login-rate-limit
        """
        prepared = api_options(
            "getApiV0MetaLoginRateLimit",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV0MetaLoginRateLimit", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.LoginRateLimitStateResponse](
                    models.LoginRateLimitStateResponse
                )
            },
        )

    def delete_login_rate_limit(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ClearRateLimitResponse]:
        """DELETE operation.

        /api/v0/meta/login-rate-limit
        """
        prepared = api_options(
            "deleteApiV0MetaLoginRateLimit",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV0MetaLoginRateLimit", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ClearRateLimitResponse](
                    models.ClearRateLimitResponse
                )
            },
        )

    def delete_login_rate_limit_by_id(
        self, id_: str, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ReleaseRateLimitResponse]:
        """DELETE operation.

        /api/v0/meta/login-rate-limit/{id}
        """
        prepared = api_options(
            "deleteApiV0MetaLoginRateLimitById",
            {"id": id_},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV0MetaLoginRateLimitById", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ReleaseRateLimitResponse](
                    models.ReleaseRateLimitResponse
                )
            },
        )

    def get_tasks(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskQueueStateResponse]:
        """GET operation.

        /api/v0/meta/tasks
        """
        prepared = api_options(
            "getApiV0MetaTasks",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV0MetaTasks", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.TaskQueueStateResponse](
                    models.TaskQueueStateResponse
                )
            },
        )


class PrincipalsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_me(self, *, options: OpenAPIOptions | None = None) -> APIResponse[models.MeResponse]:
        """GET operation.

        /api/v1/iam/me
        """
        prepared = api_options(
            "getApiV1IamMe", {}, None, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV1IamMe", json=None, options=prepared)
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.MeResponse](models.MeResponse)}
        )

    def get_me_groups(
        self,
        *,
        query: controls.PrincipalsGetMeGroupsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupResponse]]:
        """GET operation.

        /api/v1/iam/me/groups
        """
        prepared = api_options(
            "getApiV1IamMeGroups",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMeGroups", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupResponse]](
                    builtins.list[models.GroupResponse]
                )
            },
        )

    def get_me_permissions(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.PrincipalCollectionPermissions]]:
        """GET operation.

        /api/v1/iam/me/permissions
        """
        prepared = api_options(
            "getApiV1IamMePermissions",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMePermissions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.PrincipalCollectionPermissions]
                ](builtins.list[models.PrincipalCollectionPermissions])
            },
        )

    def get_me_settings(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """GET operation.

        /api/v1/iam/me/settings
        """
        prepared = api_options(
            "getApiV1IamMeSettings",
            {},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMeSettings", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def put_me_settings(
        self,
        *,
        body: models.PrincipalSettings,
        header: controls.PrincipalsPutMeSettingsHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """PUT operation.

        /api/v1/iam/me/settings
        """
        prepared = api_options(
            "putApiV1IamMeSettings",
            {},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1IamMeSettings",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.PrincipalSettings](
                        models.PrincipalSettings
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def delete_me_settings(
        self,
        *,
        header: controls.PrincipalsDeleteMeSettingsHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/me/settings
        """
        prepared = api_options(
            "deleteApiV1IamMeSettings",
            {},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamMeSettings", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_me_settings(
        self,
        *,
        body: models.PrincipalSettings | models.PrincipalSettingsPatchDocument,
        header: controls.PrincipalsPatchMeSettingsHeader | None = None,
        content_type: Literal[
            "application/json", "application/json-patch+json", "application/merge-patch+json"
        ] = "application/json",
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """PATCH operation.

        /api/v1/iam/me/settings
        """
        prepared = api_options(
            "patchApiV1IamMeSettings",
            {},
            None,
            header,
            options,
            content_type=content_type,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamMeSettings",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettings),
                    "application/json-patch+json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettingsPatchDocument),
                    "application/merge-patch+json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettings),
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def get_me_tokens(
        self,
        *,
        query: controls.PrincipalsGetMeTokensQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.PrincipalTokenMetadata]]:
        """GET operation.

        /api/v1/iam/me/tokens
        """
        prepared = api_options(
            "getApiV1IamMeTokens",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamMeTokens", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.PrincipalTokenMetadata]](
                    builtins.list[models.PrincipalTokenMetadata]
                )
            },
        )

    def get_principals_by_principal_id_groups(
        self,
        principal_id: int,
        *,
        query: controls.PrincipalsGetByPrincipalIdGroupsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.GroupResponse]]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/groups
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdGroups",
            {"principal_id": principal_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdGroups", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.GroupResponse]](
                    builtins.list[models.GroupResponse]
                )
            },
        )

    def get_principals_by_principal_id_permissions(
        self, principal_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.PrincipalCollectionPermissions]]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/permissions
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdPermissions",
            {"principal_id": principal_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdPermissions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.PrincipalCollectionPermissions]
                ](builtins.list[models.PrincipalCollectionPermissions])
            },
        )

    def get_principals_by_principal_id_settings(
        self, principal_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/settings
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdSettings",
            {"principal_id": principal_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdSettings", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def put_principals_by_principal_id_settings(
        self,
        principal_id: int,
        *,
        body: models.PrincipalSettings,
        header: controls.PrincipalsPutByPrincipalIdSettingsHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """PUT operation.

        /api/v1/iam/principals/{principal_id}/settings
        """
        prepared = api_options(
            "putApiV1IamPrincipalsByPrincipalIdSettings",
            {"principal_id": principal_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1IamPrincipalsByPrincipalIdSettings",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.PrincipalSettings](
                        models.PrincipalSettings
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def delete_principals_by_principal_id_settings(
        self,
        principal_id: int,
        *,
        header: controls.PrincipalsDeleteByPrincipalIdSettingsHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/principals/{principal_id}/settings
        """
        prepared = api_options(
            "deleteApiV1IamPrincipalsByPrincipalIdSettings",
            {"principal_id": principal_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamPrincipalsByPrincipalIdSettings", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_principals_by_principal_id_settings(
        self,
        principal_id: int,
        *,
        body: models.PrincipalSettings | models.PrincipalSettingsPatchDocument,
        header: controls.PrincipalsPatchByPrincipalIdSettingsHeader | None = None,
        content_type: Literal[
            "application/json", "application/json-patch+json", "application/merge-patch+json"
        ] = "application/json",
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.PrincipalSettingsResponse]:
        """PATCH operation.

        /api/v1/iam/principals/{principal_id}/settings
        """
        prepared = api_options(
            "patchApiV1IamPrincipalsByPrincipalIdSettings",
            {"principal_id": principal_id},
            None,
            header,
            options,
            content_type=content_type,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamPrincipalsByPrincipalIdSettings",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettings),
                    "application/json-patch+json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettingsPatchDocument),
                    "application/merge-patch+json": TypeAdapter[
                        models.PrincipalSettings | models.PrincipalSettingsPatchDocument
                    ](models.PrincipalSettings),
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalSettingsResponse](
                    models.PrincipalSettingsResponse
                )
            },
        )

    def get_principals_by_principal_id_tokens(
        self,
        principal_id: int,
        *,
        query: controls.PrincipalsGetByPrincipalIdTokensQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.PrincipalTokenMetadata]]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/tokens
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdTokens",
            {"principal_id": principal_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdTokens", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.PrincipalTokenMetadata]](
                    builtins.list[models.PrincipalTokenMetadata]
                )
            },
        )

    def post_principals_by_principal_id_tokens(
        self,
        principal_id: int,
        *,
        body: models.NewTokenRequest,
        header: controls.PrincipalsPostByPrincipalIdTokensHeader,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.LoginResponse]:
        """POST operation.

        /api/v1/iam/principals/{principal_id}/tokens
        """
        prepared = api_options(
            "postApiV1IamPrincipalsByPrincipalIdTokens",
            {"principal_id": principal_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamPrincipalsByPrincipalIdTokens",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewTokenRequest](models.NewTokenRequest)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.LoginResponse](models.LoginResponse)}
        )

    def get_principals_by_principal_id_tokens_by_token_id(
        self, principal_id: int, token_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.PrincipalTokenPointResponse]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/tokens/{token_id}
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdTokensByTokenId",
            {"principal_id": principal_id, "token_id": token_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdTokensByTokenId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.PrincipalTokenPointResponse](
                    models.PrincipalTokenPointResponse
                )
            },
        )

    def get_principals_by_principal_id_tokens_by_token_id_activity(
        self,
        principal_id: int,
        token_id: int,
        *,
        query: controls.PrincipalsGetByPrincipalIdTokensByTokenIdActivityQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.CredentialActivityResponse]:
        """GET operation.

        /api/v1/iam/principals/{principal_id}/tokens/{token_id}/activity
        """
        prepared = api_options(
            "getApiV1IamPrincipalsByPrincipalIdTokensByTokenIdActivity",
            {"principal_id": principal_id, "token_id": token_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamPrincipalsByPrincipalIdTokensByTokenIdActivity", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.CredentialActivityResponse](
                    models.CredentialActivityResponse
                )
            },
        )

    def post_principals_by_principal_id_tokens_by_token_id_renew(
        self,
        principal_id: int,
        token_id: int,
        *,
        body: models.RenewTokenRequest,
        header: controls.PrincipalsPostByPrincipalIdTokensByTokenIdRenewHeader,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.LoginResponse]:
        """POST operation.

        /api/v1/iam/principals/{principal_id}/tokens/{token_id}/renew
        """
        prepared = api_options(
            "postApiV1IamPrincipalsByPrincipalIdTokensByTokenIdRenew",
            {"principal_id": principal_id, "token_id": token_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamPrincipalsByPrincipalIdTokensByTokenIdRenew",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.RenewTokenRequest](
                        models.RenewTokenRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.LoginResponse](models.LoginResponse)}
        )

    def post_principals_by_principal_id_tokens_by_token_id_revoke(
        self,
        principal_id: int,
        token_id: int,
        *,
        header: controls.PrincipalsPostByPrincipalIdTokensByTokenIdRevokeHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """POST operation.

        /api/v1/iam/principals/{principal_id}/tokens/{token_id}/revoke
        """
        prepared = api_options(
            "postApiV1IamPrincipalsByPrincipalIdTokensByTokenIdRevoke",
            {"principal_id": principal_id, "token_id": token_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamPrincipalsByPrincipalIdTokensByTokenIdRevoke", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})


class ProbesAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_healthz(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ProbeResponse]:
        """GET operation.

        /healthz
        """
        prepared = api_options(
            "getHealthz", {}, None, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getHealthz", json=None, options=prepared)
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.ProbeResponse](models.ProbeResponse)}
        )

    def get_readyz(
        self, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ProbeResponse]:
        """GET operation.

        /readyz
        """
        prepared = api_options(
            "getReadyz", {}, None, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getReadyz", json=None, options=prepared)
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.ProbeResponse](models.ProbeResponse)}
        )


class QueryUsageAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, class_id: models.HubuumClassID, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.QueryUsageResponse]]:
        """GET operation.

        /api/v1/classes/{class_id}/query-usage
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdQueryUsage",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdQueryUsage", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.QueryUsageResponse]](
                    builtins.list[models.QueryUsageResponse]
                )
            },
        )

    def create(
        self,
        class_id: models.HubuumClassID,
        *,
        body: models.QueryUsageCreateRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.QueryUsageResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/query-usage
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdQueryUsage",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdQueryUsage",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.QueryUsageCreateRequest](
                        models.QueryUsageCreateRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.QueryUsageResponse](models.QueryUsageResponse)},
        )

    def post_analysis(
        self,
        class_id: models.HubuumClassID,
        *,
        body: models.QueryUsageAnalysisRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.QueryUsageAnalysisResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/query-usage/analysis
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdQueryUsageAnalysis",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdQueryUsageAnalysis",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.QueryUsageAnalysisRequest](
                        models.QueryUsageAnalysisRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.QueryUsageAnalysisResponse](
                    models.QueryUsageAnalysisResponse
                )
            },
        )

    def replace(
        self,
        class_id: models.HubuumClassID,
        declaration_id: models.ResourceID,
        *,
        body: models.QueryUsageReplaceRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.QueryUsageResponse]:
        """PUT operation.

        /api/v1/classes/{class_id}/query-usage/{declaration_id}
        """
        prepared = api_options(
            "putApiV1ClassesByClassIdQueryUsageByDeclarationId",
            {"class_id": class_id, "declaration_id": declaration_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "putApiV1ClassesByClassIdQueryUsageByDeclarationId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.QueryUsageReplaceRequest](
                        models.QueryUsageReplaceRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.QueryUsageResponse](models.QueryUsageResponse)},
        )

    def delete(
        self,
        class_id: models.HubuumClassID,
        declaration_id: models.ResourceID,
        *,
        query: controls.QueryUsageDeleteQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/classes/{class_id}/query-usage/{declaration_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdQueryUsageByDeclarationId",
            {"class_id": class_id, "declaration_id": declaration_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdQueryUsageByDeclarationId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})


class RelationsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_classes(
        self,
        *,
        query: controls.RelationsGetClassesQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumClassRelation]]:
        """GET operation.

        /api/v1/relations/classes
        """
        prepared = api_options(
            "getApiV1RelationsClasses",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RelationsClasses", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumClassRelation]](
                    builtins.list[models.HubuumClassRelation]
                )
            },
        )

    def post_classes(
        self, *, body: models.NewHubuumClassRelation, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClassRelation]:
        """POST operation.

        /api/v1/relations/classes
        """
        prepared = api_options(
            "postApiV1RelationsClasses",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1RelationsClasses",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewHubuumClassRelation](
                        models.NewHubuumClassRelation
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassRelation](
                    models.HubuumClassRelation
                )
            },
        )

    def get_classes_by_relation_id(
        self, relation_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumClassRelation]:
        """GET operation.

        /api/v1/relations/classes/{relation_id}
        """
        prepared = api_options(
            "getApiV1RelationsClassesByRelationId",
            {"relation_id": relation_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RelationsClassesByRelationId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassRelation](
                    models.HubuumClassRelation
                )
            },
        )

    def delete_classes_by_relation_id(
        self,
        relation_id: int,
        *,
        header: controls.RelationsDeleteClassesByRelationIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/relations/classes/{relation_id}
        """
        prepared = api_options(
            "deleteApiV1RelationsClassesByRelationId",
            {"relation_id": relation_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1RelationsClassesByRelationId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def patch_classes_by_relation_id(
        self,
        relation_id: int,
        *,
        body: models.UpdateClassRelationLabels,
        header: controls.RelationsPatchClassesByRelationIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HubuumClassRelation]:
        """PATCH operation.

        /api/v1/relations/classes/{relation_id}
        """
        prepared = api_options(
            "patchApiV1RelationsClassesByRelationId",
            {"relation_id": relation_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1RelationsClassesByRelationId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateClassRelationLabels](
                        models.UpdateClassRelationLabels
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumClassRelation](
                    models.HubuumClassRelation
                )
            },
        )

    def get_objects(
        self,
        *,
        query: controls.RelationsGetObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HubuumObjectRelation]]:
        """GET operation.

        /api/v1/relations/objects
        """
        prepared = api_options(
            "getApiV1RelationsObjects",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RelationsObjects", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.HubuumObjectRelation]](
                    builtins.list[models.HubuumObjectRelation]
                )
            },
        )

    def post_objects(
        self, *, body: models.NewHubuumObjectRelation, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumObjectRelation]:
        """POST operation.

        /api/v1/relations/objects
        """
        prepared = api_options(
            "postApiV1RelationsObjects",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1RelationsObjects",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewHubuumObjectRelation](
                        models.NewHubuumObjectRelation
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectRelation](
                    models.HubuumObjectRelation
                )
            },
        )

    def get_objects_by_relation_id(
        self, relation_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.HubuumObjectRelation]:
        """GET operation.

        /api/v1/relations/objects/{relation_id}
        """
        prepared = api_options(
            "getApiV1RelationsObjectsByRelationId",
            {"relation_id": relation_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RelationsObjectsByRelationId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HubuumObjectRelation](
                    models.HubuumObjectRelation
                )
            },
        )

    def delete_objects_by_relation_id(
        self,
        relation_id: int,
        *,
        header: controls.RelationsDeleteObjectsByRelationIdHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/relations/objects/{relation_id}
        """
        prepared = api_options(
            "deleteApiV1RelationsObjectsByRelationId",
            {"relation_id": relation_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1RelationsObjectsByRelationId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})


class RemoteTargetsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.RemoteTargetsListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.RemoteTarget]]:
        """GET operation.

        /api/v1/remote-targets
        """
        prepared = api_options(
            "getApiV1RemoteTargets",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RemoteTargets", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.RemoteTarget]](
                    builtins.list[models.RemoteTarget]
                )
            },
        )

    def create(
        self, *, body: models.NewRemoteTarget, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RemoteTarget]:
        """POST operation.

        /api/v1/remote-targets
        """
        prepared = api_options(
            "postApiV1RemoteTargets",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1RemoteTargets",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewRemoteTarget](models.NewRemoteTarget)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.RemoteTarget](models.RemoteTarget)}
        )

    def get_history(
        self,
        remote_target_id: int,
        *,
        query: controls.RemoteTargetsGetHistoryQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.HistoryResponse_RemoteTargetHistory]]:
        """GET operation.

        /api/v1/remote-targets/{remote_target_id}/history
        """
        prepared = api_options(
            "getApiV1RemoteTargetsByRemoteTargetIdHistory",
            {"remote_target_id": remote_target_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RemoteTargetsByRemoteTargetIdHistory", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[
                    builtins.list[models.HistoryResponse_RemoteTargetHistory]
                ](builtins.list[models.HistoryResponse_RemoteTargetHistory])
            },
        )

    def get_history_as_of(
        self,
        remote_target_id: int,
        *,
        query: controls.RemoteTargetsGetHistoryAsOfQuery,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.HistoryResponse_RemoteTargetHistory]:
        """GET operation.

        /api/v1/remote-targets/{remote_target_id}/history/as-of
        """
        prepared = api_options(
            "getApiV1RemoteTargetsByRemoteTargetIdHistoryAsOf",
            {"remote_target_id": remote_target_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RemoteTargetsByRemoteTargetIdHistoryAsOf", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.HistoryResponse_RemoteTargetHistory](
                    models.HistoryResponse_RemoteTargetHistory
                )
            },
        )

    def get(
        self, target_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RemoteTarget]:
        """GET operation.

        /api/v1/remote-targets/{target_id}
        """
        prepared = api_options(
            "getApiV1RemoteTargetsByTargetId",
            {"target_id": target_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RemoteTargetsByTargetId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.RemoteTarget](models.RemoteTarget)}
        )

    def delete(
        self,
        target_id: int,
        *,
        header: controls.RemoteTargetsDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/remote-targets/{target_id}
        """
        prepared = api_options(
            "deleteApiV1RemoteTargetsByTargetId",
            {"target_id": target_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1RemoteTargetsByTargetId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        target_id: int,
        *,
        body: models.UpdateRemoteTarget,
        header: controls.RemoteTargetsUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.RemoteTarget]:
        """PATCH operation.

        /api/v1/remote-targets/{target_id}
        """
        prepared = api_options(
            "patchApiV1RemoteTargetsByTargetId",
            {"target_id": target_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1RemoteTargetsByTargetId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateRemoteTarget](
                        models.UpdateRemoteTarget
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.RemoteTarget](models.RemoteTarget)}
        )

    def post_invoke(
        self,
        target_id: int,
        *,
        body: models.RemoteTargetInvokeRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/remote-targets/{target_id}/invoke
        """
        prepared = api_options(
            "postApiV1RemoteTargetsByTargetIdInvoke",
            {"target_id": target_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1RemoteTargetsByTargetIdInvoke",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.RemoteTargetInvokeRequest](
                        models.RemoteTargetInvokeRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )


class RestoresAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def create(
        self, *, body: models.BackupDocument, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RestoreStageResponse]:
        """POST operation.

        /api/v1/restores
        """
        prepared = api_options(
            "postApiV1Restores",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Restores",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.BackupDocument](models.BackupDocument)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.RestoreStageResponse](
                    models.RestoreStageResponse
                )
            },
        )

    def post_confirm(
        self,
        restore_id: int,
        *,
        body: models.RestoreConfirmRequest,
        header: controls.RestoresPostConfirmHeader,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.RestoreStageResponse]:
        """POST operation.

        /api/v1/restores/{restore_id}/confirm
        """
        prepared = api_options(
            "postApiV1RestoresByRestoreIdConfirm",
            {"restore_id": restore_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1RestoresByRestoreIdConfirm",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.RestoreConfirmRequest](
                        models.RestoreConfirmRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.RestoreStageResponse](
                    models.RestoreStageResponse
                )
            },
        )

    def get_status(
        self, restore_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.RestoreStageResponse]:
        """GET operation.

        /api/v1/restores/{restore_id}/status
        """
        prepared = api_options(
            "getApiV1RestoresByRestoreIdStatus",
            {"restore_id": restore_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1RestoresByRestoreIdStatus", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.RestoreStageResponse](
                    models.RestoreStageResponse
                )
            },
        )


class SchemaEvolutionAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, class_id: models.HubuumClassID, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ClassSchemaResponse]:
        """GET operation.

        /api/v1/classes/{class_id}/schema
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchema",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchema", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ClassSchemaResponse](
                    models.ClassSchemaResponse
                )
            },
        )

    def get_objects(
        self,
        class_id: models.HubuumClassID,
        *,
        query: controls.SchemaEvolutionGetObjectsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaCompliancePage]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/objects
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaObjects",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaObjects", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaCompliancePage](
                    models.SchemaCompliancePage
                )
            },
        )

    def get_revisions(
        self,
        class_id: models.HubuumClassID,
        *,
        query: controls.SchemaEvolutionGetRevisionsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.SchemaRevisionResponse]]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/revisions
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaRevisions",
            {"class_id": class_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaRevisions", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.SchemaRevisionResponse]](
                    builtins.list[models.SchemaRevisionResponse]
                )
            },
        )

    def post_revisions(
        self,
        class_id: models.HubuumClassID,
        *,
        body: models.SchemaStageRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaRevisionResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/revisions
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaRevisions",
            {"class_id": class_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaRevisions",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SchemaStageRequest](
                        models.SchemaStageRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaRevisionResponse](
                    models.SchemaRevisionResponse
                )
            },
        )

    def get_revisions_by_revision(
        self,
        class_id: models.HubuumClassID,
        revision: models.SchemaRevision,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaRevisionResponse]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/revisions/{revision}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaRevisionsByRevision",
            {"class_id": class_id, "revision": revision},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaRevisionsByRevision", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaRevisionResponse](
                    models.SchemaRevisionResponse
                )
            },
        )

    def delete_revisions_by_revision(
        self,
        class_id: models.HubuumClassID,
        revision: models.SchemaRevision,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaRevisionResponse]:
        """DELETE operation.

        /api/v1/classes/{class_id}/schema/revisions/{revision}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdSchemaRevisionsByRevision",
            {"class_id": class_id, "revision": revision},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdSchemaRevisionsByRevision", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaRevisionResponse](
                    models.SchemaRevisionResponse
                )
            },
        )

    def post_revisions_by_revision_activate(
        self,
        class_id: models.HubuumClassID,
        revision: models.SchemaRevision,
        *,
        body: models.SchemaActivationRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaActivationResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/revisions/{revision}/activate
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionActivate",
            {"class_id": class_id, "revision": revision},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionActivate",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SchemaActivationRequest](
                        models.SchemaActivationRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SchemaActivationResponse](
                    models.SchemaActivationResponse
                )
            },
        )

    def post_revisions_by_revision_impact(
        self,
        class_id: models.HubuumClassID,
        revision: models.SchemaRevision,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaWorkResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/revisions/{revision}/impact
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionImpact",
            {"class_id": class_id, "revision": revision},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionImpact", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SchemaWorkResponse](models.SchemaWorkResponse)},
        )

    def post_revisions_by_revision_revalidate(
        self,
        class_id: models.HubuumClassID,
        revision: models.SchemaRevision,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaWorkResponse]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/revisions/{revision}/revalidate
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionRevalidate",
            {"class_id": class_id, "revision": revision},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaRevisionsByRevisionRevalidate",
            json=None,
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SchemaWorkResponse](models.SchemaWorkResponse)},
        )

    def get_tasks_by_task_id(
        self,
        class_id: models.HubuumClassID,
        task_id: models.TaskID,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaWorkResponse]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/tasks/{task_id}
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaTasksByTaskId",
            {"class_id": class_id, "task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaTasksByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SchemaWorkResponse](models.SchemaWorkResponse)},
        )

    def delete_tasks_by_task_id(
        self,
        class_id: models.HubuumClassID,
        task_id: models.TaskID,
        *,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.SchemaWorkResponse]:
        """DELETE operation.

        /api/v1/classes/{class_id}/schema/tasks/{task_id}
        """
        prepared = api_options(
            "deleteApiV1ClassesByClassIdSchemaTasksByTaskId",
            {"class_id": class_id, "task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1ClassesByClassIdSchemaTasksByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.SchemaWorkResponse](models.SchemaWorkResponse)},
        )

    def get_tasks_by_task_id_report(
        self,
        class_id: models.HubuumClassID,
        task_id: models.TaskID,
        *,
        query: controls.SchemaEvolutionGetTasksByTaskIdReportQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[str]:
        """GET operation.

        /api/v1/classes/{class_id}/schema/tasks/{task_id}/report
        """
        prepared = api_options(
            "getApiV1ClassesByClassIdSchemaTasksByTaskIdReport",
            {"class_id": class_id, "task_id": task_id},
            query,
            None,
            options,
            content_type=None,
            accept="text/html",
        )
        response = self._client.openapi._response(
            "getApiV1ClassesByClassIdSchemaTasksByTaskIdReport", json=None, options=prepared
        )
        return decode_api_response(response, {"text/html": TypeAdapter[str](str)})

    def post_tasks_by_task_id_report(
        self,
        class_id: models.HubuumClassID,
        task_id: models.TaskID,
        *,
        body: models.SchemaRepairReportRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[str]:
        """POST operation.

        /api/v1/classes/{class_id}/schema/tasks/{task_id}/report
        """
        prepared = api_options(
            "postApiV1ClassesByClassIdSchemaTasksByTaskIdReport",
            {"class_id": class_id, "task_id": task_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="text/html",
        )
        response = self._client.openapi._response(
            "postApiV1ClassesByClassIdSchemaTasksByTaskIdReport",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SchemaRepairReportRequest](
                        models.SchemaRepairReportRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(response, {"text/html": TypeAdapter[str](str)})


class SearchAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, query: controls.SearchListQuery, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.UnifiedSearchResponse]:
        """GET operation.

        /api/v1/search
        """
        prepared = api_options(
            "getApiV1Search", {}, query, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV1Search", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.UnifiedSearchResponse](
                    models.UnifiedSearchResponse
                )
            },
        )

    def create(
        self, *, body: models.StructuredSearchRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.StructuredSearchResponse]:
        """POST operation.

        /api/v1/search
        """
        prepared = api_options(
            "postApiV1Search",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1Search",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.StructuredSearchRequest](
                        models.StructuredSearchRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.StructuredSearchResponse](
                    models.StructuredSearchResponse
                )
            },
        )

    def post_hydrate(
        self, *, body: models.SearchHydrationRequest, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.SearchHydrationResponse]:
        """POST operation.

        /api/v1/search/hydrate
        """
        prepared = api_options(
            "postApiV1SearchHydrate",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1SearchHydrate",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.SearchHydrationRequest](
                        models.SearchHydrationRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.SearchHydrationResponse](
                    models.SearchHydrationResponse
                )
            },
        )

    @contextmanager
    def get_stream(
        self, *, query: controls.SearchGetStreamQuery, options: OpenAPIOptions | None = None
    ) -> Iterator[TypedResponseStream[models.UnifiedSearchEvent]]:
        """GET operation.

        /api/v1/search/stream
        """
        prepared = api_options(
            "getApiV1SearchStream",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="text/event-stream",
        )
        with self._client.openapi.stream(
            "getApiV1SearchStream", json=None, options=prepared
        ) as stream:
            yield TypedResponseStream(
                stream,
                {
                    "started": TypeAdapter[models.UnifiedSearchEvent](
                        models.UnifiedSearchStartedEvent
                    ),
                    "batch": TypeAdapter[models.UnifiedSearchEvent](
                        models.UnifiedSearchBatchResponse
                    ),
                    "done": TypeAdapter[models.UnifiedSearchEvent](models.UnifiedSearchDoneEvent),
                    "error": TypeAdapter[models.UnifiedSearchEvent](models.UnifiedSearchErrorEvent),
                },
            )

    @contextmanager
    def post_stream(
        self, *, body: models.StructuredSearchRequest, options: OpenAPIOptions | None = None
    ) -> Iterator[TypedResponseStream[models.StructuredSearchEvent]]:
        """POST operation.

        /api/v1/search/stream
        """
        prepared = api_options(
            "postApiV1SearchStream",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="text/event-stream",
        )
        with self._client.openapi.stream(
            "postApiV1SearchStream",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.StructuredSearchRequest](
                        models.StructuredSearchRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        ) as stream:
            yield TypedResponseStream(
                stream,
                {
                    "started": TypeAdapter[models.StructuredSearchEvent](
                        models.StructuredSearchStartedEvent
                    ),
                    "result": TypeAdapter[models.StructuredSearchEvent](
                        models.StructuredSearchResult
                    ),
                    "done": TypeAdapter[models.StructuredSearchEvent](
                        models.StructuredSearchDoneEvent
                    ),
                    "error": TypeAdapter[models.StructuredSearchEvent](
                        models.StructuredSearchErrorEvent
                    ),
                },
            )


class ServiceAccountsAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        query: controls.ServiceAccountsListQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.ServiceAccountResponse]]:
        """GET operation.

        /api/v1/iam/service-accounts
        """
        prepared = api_options(
            "getApiV1IamServiceAccounts",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamServiceAccounts", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.ServiceAccountResponse]](
                    builtins.list[models.ServiceAccountResponse]
                )
            },
        )

    def create(
        self, *, body: models.NewServiceAccount, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ServiceAccountPointResponse]:
        """POST operation.

        /api/v1/iam/service-accounts
        """
        prepared = api_options(
            "postApiV1IamServiceAccounts",
            {},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamServiceAccounts",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.NewServiceAccount](
                        models.NewServiceAccount
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ServiceAccountPointResponse](
                    models.ServiceAccountPointResponse
                )
            },
        )

    def get(
        self, service_account_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.ServiceAccountPointResponse]:
        """GET operation.

        /api/v1/iam/service-accounts/{service_account_id}
        """
        prepared = api_options(
            "getApiV1IamServiceAccountsByServiceAccountId",
            {"service_account_id": service_account_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamServiceAccountsByServiceAccountId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ServiceAccountPointResponse](
                    models.ServiceAccountPointResponse
                )
            },
        )

    def delete(
        self,
        service_account_id: int,
        *,
        header: controls.ServiceAccountsDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/service-accounts/{service_account_id}
        """
        prepared = api_options(
            "deleteApiV1IamServiceAccountsByServiceAccountId",
            {"service_account_id": service_account_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamServiceAccountsByServiceAccountId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        service_account_id: int,
        *,
        body: models.UpdateServiceAccount,
        header: controls.ServiceAccountsUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ServiceAccountPointResponse]:
        """PATCH operation.

        /api/v1/iam/service-accounts/{service_account_id}
        """
        prepared = api_options(
            "patchApiV1IamServiceAccountsByServiceAccountId",
            {"service_account_id": service_account_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamServiceAccountsByServiceAccountId",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.UpdateServiceAccount](
                        models.UpdateServiceAccount
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ServiceAccountPointResponse](
                    models.ServiceAccountPointResponse
                )
            },
        )

    def post_disable(
        self,
        service_account_id: int,
        *,
        header: controls.ServiceAccountsPostDisableHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.ServiceAccountPointResponse]:
        """POST operation.

        /api/v1/iam/service-accounts/{service_account_id}/disable
        """
        prepared = api_options(
            "postApiV1IamServiceAccountsByServiceAccountIdDisable",
            {"service_account_id": service_account_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamServiceAccountsByServiceAccountIdDisable", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[models.ServiceAccountPointResponse](
                    models.ServiceAccountPointResponse
                )
            },
        )


class TasksAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, query: controls.TasksListQuery | None = None, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.TaskResponse]]:
        """GET operation.

        /api/v1/tasks
        """
        prepared = api_options(
            "getApiV1Tasks", {}, query, None, options, content_type=None, accept="application/json"
        )
        response = self._client.openapi._response("getApiV1Tasks", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.TaskResponse]](
                    builtins.list[models.TaskResponse]
                )
            },
        )

    def get(
        self, task_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.TaskResponse]:
        """GET operation.

        /api/v1/tasks/{task_id}
        """
        prepared = api_options(
            "getApiV1TasksByTaskId",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1TasksByTaskId", json=None, options=prepared
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def post_cancel(
        self,
        task_id: models.TaskID,
        *,
        body: models.TaskCancelRequest,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.TaskResponse]:
        """POST operation.

        /api/v1/tasks/{task_id}/cancel
        """
        prepared = api_options(
            "postApiV1TasksByTaskIdCancel",
            {"task_id": task_id},
            None,
            None,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1TasksByTaskIdCancel",
            json=api_body(
                body,
                {
                    "application/json": TypeAdapter[models.TaskCancelRequest](
                        models.TaskCancelRequest
                    )
                },
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response, {"application/json": TypeAdapter[models.TaskResponse](models.TaskResponse)}
        )

    def get_events(
        self,
        task_id: int,
        *,
        query: controls.TasksGetEventsQuery | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[builtins.list[models.TaskEventResponse]]:
        """GET operation.

        /api/v1/tasks/{task_id}/events
        """
        prepared = api_options(
            "getApiV1TasksByTaskIdEvents",
            {"task_id": task_id},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1TasksByTaskIdEvents", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.TaskEventResponse]](
                    builtins.list[models.TaskEventResponse]
                )
            },
        )


class UsersAPI:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, query: controls.UsersListQuery | None = None, options: OpenAPIOptions | None = None
    ) -> APIResponse[builtins.list[models.UserResponse]]:
        """GET operation.

        /api/v1/iam/users
        """
        prepared = api_options(
            "getApiV1IamUsers",
            {},
            query,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response("getApiV1IamUsers", json=None, options=prepared)
        return decode_api_response(
            response,
            {
                "application/json": TypeAdapter[builtins.list[models.UserResponse]](
                    builtins.list[models.UserResponse]
                )
            },
        )

    def create(
        self,
        *,
        body: models.NewUser,
        header: controls.UsersCreateHeader,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.UserPointResponse]:
        """POST operation.

        /api/v1/iam/users
        """
        prepared = api_options(
            "postApiV1IamUsers",
            {},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamUsers",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.NewUser](models.NewUser)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.UserPointResponse](models.UserPointResponse)},
        )

    def get(
        self, user_id: int, *, options: OpenAPIOptions | None = None
    ) -> APIResponse[models.UserPointResponse]:
        """GET operation.

        /api/v1/iam/users/{user_id}
        """
        prepared = api_options(
            "getApiV1IamUsersByUserId",
            {"user_id": user_id},
            None,
            None,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "getApiV1IamUsersByUserId", json=None, options=prepared
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.UserPointResponse](models.UserPointResponse)},
        )

    def delete(
        self,
        user_id: int,
        *,
        header: controls.UsersDeleteHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """DELETE operation.

        /api/v1/iam/users/{user_id}
        """
        prepared = api_options(
            "deleteApiV1IamUsersByUserId",
            {"user_id": user_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "deleteApiV1IamUsersByUserId", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})

    def update(
        self,
        user_id: int,
        *,
        body: models.UpdateUser,
        header: controls.UsersUpdateHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[models.UserPointResponse]:
        """PATCH operation.

        /api/v1/iam/users/{user_id}
        """
        prepared = api_options(
            "patchApiV1IamUsersByUserId",
            {"user_id": user_id},
            None,
            header,
            options,
            content_type="application/json",
            accept="application/json",
        )
        response = self._client.openapi._response(
            "patchApiV1IamUsersByUserId",
            json=api_body(
                body,
                {"application/json": TypeAdapter[models.UpdateUser](models.UpdateUser)},
                content_type=prepared.content_type,
                optional=False,
            ),
            options=prepared,
        )
        return decode_api_response(
            response,
            {"application/json": TypeAdapter[models.UserPointResponse](models.UserPointResponse)},
        )

    def post_anonymize(
        self,
        user_id: int,
        *,
        header: controls.UsersPostAnonymizeHeader | None = None,
        options: OpenAPIOptions | None = None,
    ) -> APIResponse[None]:
        """POST operation.

        /api/v1/iam/users/{user_id}/anonymize
        """
        prepared = api_options(
            "postApiV1IamUsersByUserIdAnonymize",
            {"user_id": user_id},
            None,
            header,
            options,
            content_type=None,
            accept="application/json",
        )
        response = self._client.openapi._response(
            "postApiV1IamUsersByUserIdAnonymize", json=None, options=prepared
        )
        return decode_api_response(response, {"": TypeAdapter[None](None)})


class API:
    """Complete typed resource interface for the pinned server contract."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @cached_property
    def admin(self) -> AdminAPI:
        return AdminAPI(self._client)

    @cached_property
    def auth(self) -> AuthAPI:
        return AuthAPI(self._client)

    @cached_property
    def backups(self) -> BackupsAPI:
        return BackupsAPI(self._client)

    @cached_property
    def classes(self) -> ClassesAPI:
        return ClassesAPI(self._client)

    @cached_property
    def collections(self) -> CollectionsAPI:
        return CollectionsAPI(self._client)

    @cached_property
    def computed_fields(self) -> ComputedFieldsAPI:
        return ComputedFieldsAPI(self._client)

    @cached_property
    def config(self) -> ConfigAPI:
        return ConfigAPI(self._client)

    @cached_property
    def event_deliveries(self) -> EventDeliveriesAPI:
        return EventDeliveriesAPI(self._client)

    @cached_property
    def event_sinks(self) -> EventSinksAPI:
        return EventSinksAPI(self._client)

    @cached_property
    def event_subscriptions(self) -> EventSubscriptionsAPI:
        return EventSubscriptionsAPI(self._client)

    @cached_property
    def events(self) -> EventsAPI:
        return EventsAPI(self._client)

    @cached_property
    def export_templates(self) -> ExportTemplatesAPI:
        return ExportTemplatesAPI(self._client)

    @cached_property
    def exports(self) -> ExportsAPI:
        return ExportsAPI(self._client)

    @cached_property
    def groups(self) -> GroupsAPI:
        return GroupsAPI(self._client)

    @cached_property
    def imports(self) -> ImportsAPI:
        return ImportsAPI(self._client)

    @cached_property
    def meta(self) -> MetaAPI:
        return MetaAPI(self._client)

    @cached_property
    def principals(self) -> PrincipalsAPI:
        return PrincipalsAPI(self._client)

    @cached_property
    def probes(self) -> ProbesAPI:
        return ProbesAPI(self._client)

    @cached_property
    def query_usage(self) -> QueryUsageAPI:
        return QueryUsageAPI(self._client)

    @cached_property
    def relations(self) -> RelationsAPI:
        return RelationsAPI(self._client)

    @cached_property
    def remote_targets(self) -> RemoteTargetsAPI:
        return RemoteTargetsAPI(self._client)

    @cached_property
    def restores(self) -> RestoresAPI:
        return RestoresAPI(self._client)

    @cached_property
    def schema_evolution(self) -> SchemaEvolutionAPI:
        return SchemaEvolutionAPI(self._client)

    @cached_property
    def search(self) -> SearchAPI:
        return SearchAPI(self._client)

    @cached_property
    def service_accounts(self) -> ServiceAccountsAPI:
        return ServiceAccountsAPI(self._client)

    @cached_property
    def tasks(self) -> TasksAPI:
        return TasksAPI(self._client)

    @cached_property
    def users(self) -> UsersAPI:
        return UsersAPI(self._client)
