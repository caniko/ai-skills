# GitLab API Reference

Useful GitLab REST API calls for working with merge request discussions, using `glab api`.

Bind every MR operation to the verified target project, not the source fork's
remote. Set `MR_TARGET_REPO` from the actual MR URL; ask if unknown. Capture the
numeric target project ID, IID and URL hostname once and retain them throughout
the workflow. Every API call explicitly targets that instance.

## Fetch MR details

```bash
: "${MR_TARGET_REPO:?Set the verified https://HOST/OWNER/REPO target URL first}"
case "$MR_TARGET_REPO" in https://*/*) ;; *) echo "A fully qualified GitLab target URL is required." >&2; exit 1 ;; esac
GITLAB_HOST=${MR_TARGET_REPO#https://}
GITLAB_HOST=${GITLAB_HOST%%/*}
: "${GITLAB_HOST:?Missing GitLab instance}"
export GITLAB_HOST
MR=$(glab mr view <MR_IID> --repo "$MR_TARGET_REPO" --output json) || exit 1
MR_PROJECT_ID=$(echo "$MR" | jq -er '.target_project_id') || exit 1
MR_IID=$(echo "$MR" | jq -er '.iid') || exit 1
```

Key fields (compared to GitHub equivalents):
- `iid` — internal MR number (use this, not `id`)
- `source_branch` — equivalent to GitHub's `headRefName`
- `sha` — HEAD commit SHA, equivalent to GitHub's `headRefOid`
- `description` — equivalent to GitHub's `body`

## Bind the MR comparison

Use the numeric **target** project ID from the MR, not the local fork's path.
Retain source/target projects and branches, all `diff_refs`, and the live target
branch SHA. `diff_refs` describe the latest diff version and populate
asynchronously; `start_sha` alone can lag a target advance. Missing fields fail
closed. Load these Bash helpers before capture/polling/acceptance/resolution:

```bash
# MR identity helpers
mr_revision() {
  local mr branch target target_sha
  mr=$(glab api --hostname "$GITLAB_HOST" "projects/$MR_PROJECT_ID/merge_requests/$MR_IID") || return 1
  branch=$(echo "$mr" | jq -er '.target_branch | select(length > 0) | @uri') || return 1
  target=$(glab api --hostname "$GITLAB_HOST" "projects/$MR_PROJECT_ID/repository/branches/$branch") || return 1
  target_sha=$(echo "$target" | jq -er '.commit.id | select(length > 0)') || return 1
  echo "$mr" | jq -ceS --arg target "$target_sha" '
    {iid, source_project_id, target_project_id, source_branch, target_branch,
     source_sha: .sha, diff_refs, target_sha: $target}
    | select(.source_project_id > 0 and .target_project_id > 0
      and (.source_branch | length) > 0 and (.target_branch | length) > 0
      and (.diff_refs.base_sha | length) > 0 and (.diff_refs.start_sha | length) > 0
      and (.diff_refs.head_sha | length) > 0 and .source_sha == .diff_refs.head_sha)'
}
assert_mr_revision() {
  local current
  current=$(mr_revision) || return 1
  if [ "$current" != "$MR_REVISION" ]; then
    echo "MR source/target moved; stop and obtain fresh comparison evidence." >&2
    return 1
  fi
}
```

Capture once, then call `assert_mr_revision` on each attempt and immediately before
accepting receipts or replying/resolving. Do not overwrite the captured identity
when rechecking. Reconcile a matching pending provider request for this entire
comparison before posting another request.

## Fetch all discussions (inline + general comments)

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
```

Read every page; `--paginate` follows GitLab's pagination links.

Each discussion object:
- `id` — discussion ID (used for resolution)
- `notes` — array of note objects

Each note object:
- `resolvable`, `resolved` — whether this note can be and has been resolved
- `type` — `"DiffNote"` for inline diff comments, `null` for general comments
- `author.username` — author's username
- `body` — comment text
- `position.new_path` — file path (for `DiffNote` type)

## Filter for unresolved inline diff comments

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100" | \
  jq -s 'add | [.[] | select(any(.notes[]; .resolvable == true and .resolved == false and .type == "DiffNote"))]'
```

## Resolve a single discussion

```bash
glab api --hostname "$GITLAB_HOST" --method PUT \
  "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

There is no batch resolution in GitLab — issue one PUT per discussion. First read
all its notes, reply with the published fix and successful exact-head validation,
and ensure no follow-up remains outstanding.

## Fetch pipeline status for an MR

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100"
```

Retain a selected policy-applicable pipeline's ID, owning `project_id` and `sha`
from its MR-associated receipt. If the list omits `project_id`, use the MR's
`head_pipeline.project_id` only when its ID matches; otherwise obtain trustworthy
ownership evidence or report it missing. Never guess the target project for a fork.

Merged-results pipelines run a temporary merge commit, **not** the source head.
Verify MR association and immutable inputs before polling. For ordinary merged
results, the temporary commit's parents are target then source. Merge trains need
separate train provenance for all included inputs; do not misclassify them as an
ordinary two-input merge or fall back to a detached pipeline required policy rejects.

```bash
# Bind selected pipeline
assert_mr_revision || exit 1
MR_PIPELINES=$(glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100") || exit 1
echo "$MR_PIPELINES" | jq -se --argjson id "$PIPELINE_ID" --arg sha "$PIPELINE_SHA" \
  'add | any(.[]; .id == $id and .sha == $sha)' >/dev/null || exit 1
PIPELINE=$(glab api --hostname "$GITLAB_HOST" "projects/$PIPELINE_PROJECT_ID/pipelines/$PIPELINE_ID") || exit 1
echo "$PIPELINE" | jq -e --argjson id "$PIPELINE_ID" --argjson project "$PIPELINE_PROJECT_ID" --arg sha "$PIPELINE_SHA" \
  '.id == $id and .project_id == $project and .sha == $sha' >/dev/null || exit 1
if [ "$PIPELINE_SHA" != "$HEAD_SHA" ]; then
  echo "$PIPELINE" | jq -e '.source == "merge_request_event"' >/dev/null || exit 1
  MERGE_COMMIT=$(glab api --hostname "$GITLAB_HOST" "projects/$PIPELINE_PROJECT_ID/repository/commits/$PIPELINE_SHA") || exit 1
  echo "$MERGE_COMMIT" | jq -e --arg sha "$PIPELINE_SHA" --arg head "$HEAD_SHA" --arg target "$TARGET_SHA" \
    '.id == $sha and .parent_ids == [$target, $head]' >/dev/null || exit 1
fi
assert_mr_revision || exit 1
```

Retain this proof with the review request and pipeline/job IDs. For a source-only
pipeline, retain its provider's captured target/comparison evidence too; source SHA
alone cannot prove target coverage. Pipeline statuses: `running`, `pending`,
`success`, `failed`, `canceled`, `skipped`. Only successful configured current gates
qualify; missing ownership/input proof and old terminal pipelines are not fallbacks.

Sources: [MR API/diff_refs](https://docs.gitlab.com/api/merge_requests/#get-single-mr),
[pipeline ownership](https://docs.gitlab.com/api/pipelines/#get-a-single-pipeline),
[temporary merged results](https://docs.gitlab.com/ci/pipelines/merged_results_pipelines/),
[commit parents API](https://docs.gitlab.com/api/commits/#get-a-single-commit), and
[GitLab's merge-to-ref parent binding](https://github.com/gitlabhq/gitlabhq/blob/master/app/services/merge_requests/merge_to_ref_service.rb).

## Fetch jobs for a specific pipeline

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$PIPELINE_PROJECT_ID/pipelines/$PIPELINE_ID/jobs?per_page=100"
```

Each job has `name`, `status`, `stage`, and `web_url`. Use the verified pipeline
owner for single-job endpoints too; a fork pipeline need not belong to the target
project. Before any resolution, call `assert_mr_revision` again and retain fresh
comparison-bound evidence if either branch or diff identity changed.

## Fetch MR notes (general comments and bot reviews)

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes?per_page=100"
```

Match the exact configured Greptile service account identity verified from trusted
installation metadata, not a substring or the first commenter claiming to be the bot.
Compare `updated_at` across every page, including older notes edited in place.

## Post a comment on an MR

```bash
glab api --hostname "$GITLAB_HOST" --method POST "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes" -f body="your message here"
```

Or via API:

```bash
glab api --hostname "$GITLAB_HOST" --method POST \
  "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes" \
  --field body="your message here"
```
