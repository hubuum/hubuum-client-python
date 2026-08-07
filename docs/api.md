# API reference

## Clients

::: hubuum_client.Client
    options:
      members: true

::: hubuum_client.AsyncClient
    options:
      members: true

::: hubuum_client.ClientOptions
    options:
      members: true

::: hubuum_client.RequestOptions
    options:
      members: true

::: hubuum_client.OpenAPIOptions
    options:
      members: true

::: hubuum_client.OperationSpec
    options:
      members: true

::: hubuum_client.OpenAPIOperations
    options:
      members: true

::: hubuum_client.AsyncOpenAPIOperations
    options:
      members: true

::: hubuum_client.ResponseStream
    options:
      members: true

::: hubuum_client.AsyncResponseStream
    options:
      members: true

## Task-backed services

::: hubuum_client.services.TasksService
    options:
      members: true

::: hubuum_client.async_services.AsyncTasksService
    options:
      members: true

::: hubuum_client.services.ImportsService
    options:
      members: true

::: hubuum_client.async_services.AsyncImportsService
    options:
      members: true

::: hubuum_client.services.ExportsService
    options:
      members: true

::: hubuum_client.async_services.AsyncExportsService
    options:
      members: true

## Queries

::: hubuum_client.Query
    options:
      members: true

::: hubuum_client.QueryFilter
    options:
      members: true

::: hubuum_client.DataField
    options:
      members: true

::: hubuum_client.FilterOperator
    options:
      members: true

::: hubuum_client.Page
    options:
      members: true

## Core models

::: hubuum_client.Collection

::: hubuum_client.HubuumClass

::: hubuum_client.HubuumObject

::: hubuum_client.ObjectDataPatchOperation

::: hubuum_client.ObjectAggregateRow

::: hubuum_client.ObjectAggregateDimensionValue

::: hubuum_client.ObjectAggregateMeasureValue

::: hubuum_client.User

::: hubuum_client.Group

::: hubuum_client.ClassRelation

::: hubuum_client.ObjectRelation

::: hubuum_client.Task

::: hubuum_client.TaskEvent

::: hubuum_client.TaskProgress

::: hubuum_client.TaskDetails

::: hubuum_client.ClassRelationCreate

::: hubuum_client.ImportRequest

::: hubuum_client.ImportGraph

::: hubuum_client.ImportWriteCondition

::: hubuum_client.ImportWriteMode

::: hubuum_client.RestoreTimestamps

::: hubuum_client.ImportTaskResult

::: hubuum_client.ImportRunResult

::: hubuum_client.ExportRequest

::: hubuum_client.ExportScope

::: hubuum_client.ExportJsonResponse

::: hubuum_client.RenderedExport

::: hubuum_client.NewTokenRequest

::: hubuum_client.RenewTokenRequest

::: hubuum_client.TokenListState

::: hubuum_client.TokenScope

::: hubuum_client.TokenResourceScope

::: hubuum_client.PrincipalTokenMetadata

::: hubuum_client.PrincipalTokenPoint

::: hubuum_client.PrincipalMember

::: hubuum_client.MembershipPrincipal

::: hubuum_client.CurrentTokenMetadata

::: hubuum_client.MeResponse

::: hubuum_client.ClientConfig

::: hubuum_client.ClientAuthenticationConfig

::: hubuum_client.ClientPaginationConfig

::: hubuum_client.AccessToken

## Errors

::: hubuum_client.APIError

::: hubuum_client.TransportError

::: hubuum_client.DecodeError

::: hubuum_client.TaskUnsuccessfulError

::: hubuum_client.PreconditionFailedError
