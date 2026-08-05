#!/usr/bin/env bash

set -euo pipefail

repository="${1:-hubuum/hubuum-client-python}"
branch="${2:-main}"
api_version="2026-03-10"
release_reviewer="${3:-}"
release_environment="pypi"
release_ruleset_name="Protect release tags"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 1
fi

gh auth status --hostname github.com >/dev/null

if [[ -z "${release_reviewer}" ]]; then
  release_reviewer="$(gh api user --jq .login)"
fi

permission="$({
  login="$(gh api user --jq .login)"
  gh api \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/collaborators/${login}/permission" \
    --jq .permission
})"

if [[ "${permission}" != "admin" ]]; then
  echo "Administrator permission on ${repository} is required (found: ${permission})." >&2
  exit 1
fi

release_reviewer_id="$(
  gh api \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "users/${release_reviewer}" \
    --jq .id
)"

echo "Configuring repository metadata and merge behavior..."
gh repo edit "${repository}" \
  --description "Modern typed synchronous and asynchronous Python client for Hubuum" \
  --enable-issues \
  --enable-projects=false \
  --enable-wiki=false \
  --enable-auto-merge \
  --allow-update-branch \
  --delete-branch-on-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge \
  --enable-squash-merge \
  --squash-merge-commit-message pr-title-description \
  --add-topic api-client \
  --add-topic async \
  --add-topic httpx \
  --add-topic hubuum \
  --add-topic pydantic \
  --add-topic python \
  --add-topic typed

echo "Enabling dependency security updates and least-privilege Actions defaults..."
gh api --silent --method PUT \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/vulnerability-alerts"
gh api --silent --method PUT \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/automated-security-fixes"
gh api --silent --method PUT \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/actions/permissions/workflow" \
  --field default_workflow_permissions=read \
  --field can_approve_pull_request_reviews=false

echo "Configuring protected PyPI trusted publishing..."
gh api --silent --method PUT \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/environments/${release_environment}" \
  --input - <<JSON
{
  "wait_timer": 0,
  "prevent_self_review": false,
  "reviewers": [
    {
      "type": "User",
      "id": ${release_reviewer_id}
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
JSON

release_tag_policy_id="$(
  gh api \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/environments/${release_environment}/deployment-branch-policies" \
    --jq '.branch_policies[]
      | select(.name == "v*" and .type == "tag")
      | .id'
)"
if [[ -z "${release_tag_policy_id}" ]]; then
  gh api --silent --method POST \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/environments/${release_environment}/deployment-branch-policies" \
    --input - <<'JSON'
{
  "name": "v*",
  "type": "tag"
}
JSON
fi

if gh api \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/actions/variables/PYPI_PUBLISH_ENABLED" \
  >/dev/null 2>&1; then
  gh api --silent --method PATCH \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/actions/variables/PYPI_PUBLISH_ENABLED" \
    --raw-field name=PYPI_PUBLISH_ENABLED \
    --raw-field value=true
else
  gh api --silent --method POST \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/actions/variables" \
    --raw-field name=PYPI_PUBLISH_ENABLED \
    --raw-field value=true
fi

release_ruleset_id="$(
  gh api \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/rulesets?includes_parents=false" \
    --jq ".[] | select(.name == \"${release_ruleset_name}\") | .id"
)"
release_ruleset_method="POST"
release_ruleset_endpoint="repos/${repository}/rulesets"
if [[ -n "${release_ruleset_id}" ]]; then
  release_ruleset_method="PUT"
  release_ruleset_endpoint="${release_ruleset_endpoint}/${release_ruleset_id}"
fi
gh api --silent --method "${release_ruleset_method}" \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "${release_ruleset_endpoint}" \
  --input - <<JSON
{
  "name": "${release_ruleset_name}",
  "target": "tag",
  "enforcement": "active",
  "bypass_actors": [
    {
      "actor_id": ${release_reviewer_id},
      "actor_type": "User",
      "bypass_mode": "always"
    }
  ],
  "conditions": {
    "ref_name": {
      "include": ["refs/tags/v*"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "creation"},
    {"type": "update"},
    {"type": "deletion"}
  ]
}
JSON

head_sha="$(
  gh api \
    --header "X-GitHub-Api-Version: ${api_version}" \
    "repos/${repository}/commits/${branch}" \
    --jq .sha
)"
run_id="$(
  gh run list \
    --repo "${repository}" \
    --workflow ci.yml \
    --commit "${head_sha}" \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId // empty'
)"

if [[ -z "${run_id}" ]]; then
  echo "No CI run found for ${branch} at ${head_sha}; branch protection was not changed." >&2
  exit 1
fi

echo "Waiting for CI run ${run_id} before protecting ${branch}..."
gh run watch "${run_id}" --repo "${repository}" --exit-status

echo "Protecting ${branch} with the successful end-to-end check..."
gh api --silent --method PUT \
  --header "X-GitHub-Api-Version: ${api_version}" \
  "repos/${repository}/branches/${branch}/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "Pinned Hubuum v0.0.8 e2e"}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON

echo "GitHub repository configuration is complete: https://github.com/${repository}"
