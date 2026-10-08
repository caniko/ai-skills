# GitLab API Reference

Useful GitLab REST API calls for the greploop workflow, using `glab api`.

Use the verified target MR project and IID throughout, not the source fork's
remote. Set `MR_TARGET_REPO` from the actual upstream MR URL; ask if unknown.

## Fetch MR details

```bash
: "${MR_TARGET_REPO:?Set the verified GitLab target repository first}"
MR=$(glab mr view <MR_IID> --repo "$MR_TARGET_REPO" --output json) || exit 1
MR_PROJECT_ID=$(echo "$MR" | jq -er '.target_project_id') || exit 1
MR_IID=$(echo "$MR" | jq -er '.iid') || exit 1
```

Key fields:
- `iid` — internal MR number (use this, not `id`)
- `source_branch` — equivalent to GitHub's `headRefName`
- `sha` — HEAD commit SHA
- `draft` — whether the MR requires the draft-specific review trigger
- `description` — MR body (Greptile may update this with the confidence score)

## Trigger Greptile review

Use [step A's draft-aware trigger](../SKILL.md#a-trigger-greptile-review) after
reconciling the current request and MR head. Do not use the normal review trigger
for a draft or request another review while a matching request is pending.

## Fetch pipelines for an MR

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100"
```

Check `status` field: `running`, `pending`, `success`, `failed`, `canceled`, `skipped`.
Select only after [check-pr's comparison and pipeline binding](../.skillnet/deps/check-pr/references/gitlab-api.md).
Retain the selected pipeline's ID, SHA and owning `project_id`, not an assumed
target project. Merged-results SHA differs from source head; retain proven current
source/target inputs. Capture/recheck all `diff_refs` plus live target branch SHA.

## Fetch jobs for a pipeline (to find the Greptile job)

```bash
glab api --paginate "projects/$PIPELINE_PROJECT_ID/pipelines/$PIPELINE_ID/jobs?per_page=100"
```

Verify provider identity and bind one immutable job ID to the current request and
MR comparison, pipeline SHA and owning project, not just a matching name. Use
`projects/$PIPELINE_PROJECT_ID/jobs/$JOB_ID` for a single job, including fork-owned
pipelines. Retried jobs have distinct IDs. Only `success`
allows result processing; failed/canceled/skipped jobs remain blockers.

## Inspect pending MR-associated pipelines

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100" | \
  jq -s 'add | [.[] | select(.status == "running" or .status == "pending")]'
```

Bind these candidates to current comparison inputs and provider/request identity
before considering any a pending Greptile review; mere MR association is not enough.

## Find the selected pipeline

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100" | \
  jq -s --argjson id "$PIPELINE_ID" 'add | [.[] | select(.id == $id)]'
```

## Fetch MR notes (to find Greptile's confidence score)

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes?per_page=100"
```

Filter by the verified `author.username`, compare `updated_at` across all pages,
and require binding to the completed current request/head before accepting a score.

Verify the exact Greptile service account from trusted installation metadata;
the first comment or a similar username does not establish provider identity.

## Fetch unresolved discussions (inline comments)

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
```

Read all pages. Resolution fields belong to `notes[]`, not the discussion object.

Filter for unresolved inline diff comments from Greptile:
```bash
: "${GREPTILE_BOT_USERNAME:?Missing verified GitLab service account}"
: "${GREPTILE_BOT_USER_ID:?Missing verified GitLab service account ID}"
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100" | \
  jq -s --arg bot "$GREPTILE_BOT_USERNAME" --argjson bot_id "$GREPTILE_BOT_USER_ID" 'add | [.[] | select(any(.notes[]; .resolvable == true and .resolved == false and .type == "DiffNote" and .author.username == $bot and .author.id == $bot_id))]'
```

Retain both identity values from trusted configured installation metadata, not
from an arbitrary comment. Missing identity blocks acceptance, not a zero count.

Each discussion has:
- `id` — use this for resolution
- `notes[]` — inspect all note bodies, resolution flags and follow-up replies
- `notes[].position.new_path` — file path for inline notes

## Resolve a discussion

```bash
glab api --method PUT \
  "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

GitLab has no batch resolution — issue one PUT per discussion.
First reply with the published fix and successful exact-head validation, and
ensure no follow-up question or new finding remains outstanding.
Call `assert_mr_revision` immediately before replying/resolving; target branch
movement can invalidate evidence without a source push. Sources:
[MR API](https://docs.gitlab.com/api/merge_requests/#get-single-mr),
[merged results](https://docs.gitlab.com/ci/pipelines/merged_results_pipelines/),
[fork pipeline ownership](https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/#use-with-forked-projects).
