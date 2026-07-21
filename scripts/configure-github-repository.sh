#!/usr/bin/env bash

set -euo pipefail

repository="${1:-hubuum/hubuum-client-python}"
branch="${2:-main}"
api_version="2026-03-10"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 1
fi

gh auth status --hostname github.com >/dev/null

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
      {"context": "Pinned Hubuum v0.0.3 e2e"}
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
