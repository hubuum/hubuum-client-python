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

## Schema services

::: hubuum_client.services.ClassSchemaService
    options:
      members: true

::: hubuum_client.async_services.AsyncClassSchemaService
    options:
      members: true

::: hubuum_client.SchemaPageOptions

::: hubuum_client.SchemaStageRequest

::: hubuum_client.SchemaActivationRequest

::: hubuum_client.SchemaActivationPolicy

::: hubuum_client.SchemaRepairReportRequest

::: hubuum_client.SchemaRevisionResponse

::: hubuum_client.SchemaActivationResponse

::: hubuum_client.ClassSchemaResponse

::: hubuum_client.SchemaCompliancePage

::: hubuum_client.ObjectComplianceResponse

::: hubuum_client.ObjectSchemaEvidence

::: hubuum_client.SchemaWorkResponse

::: hubuum_client.SchemaImpactResponse

::: hubuum_client.SchemaDiagnostics

::: hubuum_client.SchemaIssue

::: hubuum_client.ImportSchemaActivation

::: hubuum_client.TaskCancelRequest

::: hubuum_client.TaskRemoteSideEffectState

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

::: hubuum_client.TokenListState
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

::: hubuum_client.UserPoint

::: hubuum_client.Group

::: hubuum_client.GroupPoint

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

## Credential approvals

::: hubuum_client.services.CredentialApprovalsService
    options:
      members: true

::: hubuum_client.async_services.AsyncCredentialApprovalsService
    options:
      members: true

::: hubuum_client.CredentialApprovalRequest

::: hubuum_client.CredentialApprovalResponse
    options:
      members: true

::: hubuum_client.CredentialApprovalRecord

::: hubuum_client.CredentialApprovalSecret

::: hubuum_client.CreateTokenOperation

::: hubuum_client.RenewTokenOperation

::: hubuum_client.CreateUserOperation

::: hubuum_client.UpdateUserOperation

::: hubuum_client.ImportCredentialsOperation

::: hubuum_client.ConfirmRestoreOperation

::: hubuum_client.RestoreConfirmRequest

::: hubuum_client.ReauthenticationRequiredError

## Task discovery

::: hubuum_client.TaskQuery

::: hubuum_client.RetainedImportDetails

::: hubuum_client.RetainedExportDetails

::: hubuum_client.RetainedBackupDetails

::: hubuum_client.TaskOutputDiscoveryState

::: hubuum_client.SchemaTaskDetails

::: hubuum_client.RebuildTaskDetails

::: hubuum_client.RemoteCallTaskDetails
