---
name: check-pr
description: >
  Inspect PR/MR/CL review feedback, CI and descriptions; fix confirmed issues and
  resolve addressed threads with revision-bound evidence. Supports GitHub, GitLab and Perforce.
license: MIT
compatibility: Requires jq and git with authenticated gh (GitHub CLI) or glab (GitLab CLI), or authenticated p4 (Perforce CLI) with JSON output support.
metadata:
  author: greptileai
  version: "1.3"
allowed-tools: Bash(gh:*) Bash(glab:*) Bash(git:*) Bash(p4:*) Bash(jq:*) Bash(canix repo review:*) Bash(canix repo merge:*) Bash(canix-toolbelt repo review:*) Bash(canix-toolbelt repo merge:*)
---

# Check PR

Read [the repository contract](references/repository-contract.md) first. It
governs authority, revision binding, hosted-only validation and thread resolution
when applying the upstream workflow below.

Analyze a pull request (GitHub), merge request (GitLab), or shelved changelist (Perforce) for review comments, status checks, and description completeness, then help address any issues found.

## Inputs

- **PR/MR/CL number** (optional): If not provided, detect the PR/MR for the current branch, or the default pending changelist for p4.
- **GitHub target**: Set `PR_TARGET_REPO` to `OWNER/REPO` and `GH_HOST` to the
  host from the verified upstream PR URL (`github.com` for public GitHub).
  Numbers are repository-local: ask for the URL when the target is unknown, never
  infer upstream from a fork remote. Use these values for all CLI/API operations.
- **GitLab target repository**: Set `MR_TARGET_REPO` to the verified upstream
  target project, not a source fork. An IID is project-local; if the target is
  unknown, ask for the MR URL instead of guessing from the checkout's remote.

## Instructions

### 0. Detect platform

Prefer an actual Git worktree; global Perforce configuration does not establish
that the current directory belongs to a depot. Otherwise require a current-path
Perforce mapping:

```bash
if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" = "true" ]; then
  if [ "${VCS:-}" != "github" ] && [ "${VCS:-}" != "gitlab" ]; then
    REMOTE_URL=$(git remote get-url "${PLATFORM_REMOTE:-origin}") || {
      echo "Cannot identify platform: select a verified remote or explicit VCS." >&2
      exit 1
    }
    case "$REMOTE_URL" in
      *gitlab*) VCS="gitlab" ;;
      *github*) VCS="github" ;;
      *) echo "Unknown forge: set VCS from the verified candidate URL." >&2; exit 1 ;;
    esac
  fi
elif p4 where "$PWD/..." >/dev/null 2>&1; then
  VCS="perforce"
else
  echo "Current path is not a Git worktree or mapped Perforce workspace." >&2
  exit 1
fi
```

For self-hosted GitLab instances whose hostname doesn't contain "gitlab", the user can override by passing `--vcs gitlab` as an input. For Perforce, the user can override by passing `--vcs perforce`.

Map an explicit Git platform input to `VCS` before detection. Set `PLATFORM_REMOTE`
when origin is not the intended remote; a failed lookup never defaults to GitHub.

For Git, refuse a dirty baseline before switching branches or making fixes.
Preserve staged, unstaged and untracked work untouched; ask the user to provide a
clean task-owned checkout. Do not stash/reset or commit someone else's work.

```bash
BASELINE_STATUS=$(git status --porcelain=v1 --untracked-files=all) || exit 1
if [ -n "$BASELINE_STATUS" ]; then
  echo "Dirty baseline; preserve existing work and stop before edits/publication." >&2
  exit 1
fi
```

Keep the checkout task-owned for the fix phase. If concurrent foreign edits arrive,
stop and preserve them; the clean entry check does not authorize later foreign work.

### 1. Identify the PR/MR/CL

If a number was provided, use it. Otherwise, detect it:

**GitHub:**
```bash
: "${PR_TARGET_REPO:?Set the verified GitHub target repository first}"
: "${GH_HOST:?Set the verified GitHub host first}"
export GH_HOST
PR_REVISION=$(gh pr view --repo "$PR_TARGET_REPO" --json number,headRefOid,baseRefOid,headRefName) || exit 1
PR_NUMBER=$(echo "$PR_REVISION" | jq -er '.number') || exit 1
HEAD_SHA=$(echo "$PR_REVISION" | jq -er '.headRefOid') || exit 1
BASE_SHA=$(echo "$PR_REVISION" | jq -er '.baseRefOid') || exit 1
HEAD_BRANCH=$(echo "$PR_REVISION" | jq -er '.headRefName') || exit 1
```

When supplied, pass the PR number to that same explicitly targeted command.

**GitLab:**
```bash
: "${MR_TARGET_REPO:?Set the verified https://HOST/OWNER/REPO target URL first}"
case "$MR_TARGET_REPO" in https://*/*) ;; *) echo "A fully qualified GitLab target URL is required." >&2; exit 1 ;; esac
GITLAB_HOST=${MR_TARGET_REPO#https://}
GITLAB_HOST=${GITLAB_HOST%%/*}
: "${GITLAB_HOST:?Missing GitLab instance}"
export GITLAB_HOST
MR=$(glab mr view --repo "$MR_TARGET_REPO" --output json) || exit 1
MR_PROJECT_ID=$(echo "$MR" | jq -er '.target_project_id') || exit 1
MR_IID=$(echo "$MR" | jq -er '.iid') || exit 1
HEAD_SHA=$(echo "$MR" | jq -er '.sha') || exit 1
HEAD_BRANCH=$(echo "$MR" | jq -er '.source_branch') || exit 1
```

When a number is supplied, pass it to that same `glab mr view` with the explicit
`--repo "$MR_TARGET_REPO"`. Retain the returned target project ID and MR IID for
every later API operation. Retain the URL's hostname and explicitly pass it to
every API call; never re-infer the instance or project from the local fork.

**Perforce:**
```bash
# Resolve effective settings, including P4CONFIG; exported variables may be unset.
P4_IDENTITY=$(p4 -ztag -Mj info) || exit 1
REVIEW_USER=$(echo "$P4_IDENTITY" | jq -esr 'map(select(.userName != null)) | if length == 1 then .[0].userName else error("Unknown Perforce user") end') || exit 1
REVIEW_CLIENT=$(echo "$P4_IDENTITY" | jq -esr 'map(select(.clientName != null)) | if length == 1 then .[0].clientName else error("Unknown Perforce client") end') || exit 1
if [ -z "$REVIEW_USER" ] || [ -z "$REVIEW_CLIENT" ] || [ "$REVIEW_CLIENT" = "*unknown*" ]; then
  echo "Unknown effective Perforce identity; stop." >&2
  exit 1
fi
p4 changes -s shelved -u "$REVIEW_USER" -c "$REVIEW_CLIENT"
p4 changes -s pending -u "$REVIEW_USER" -c "$REVIEW_CLIENT"
```

Key field differences between platforms:
- GitHub: `number`, `headRefName`, `headRefOid`
- GitLab: `iid`, `source_branch`, `sha`
- Perforce: changelist number (CL), `shelved` files for in-review CLs

For Git, prepare the **exact hosted candidate before source analysis**, not at
the later fix step. Preserve any committed local branch, including unpublished
commits, by using a detached task-owned checkout. Verify `CANDIDATE_REMOTE` is
the candidate's source repository (the fork for fork PRs/MRs), not merely origin.
Fetching must not publish anything. A missing remote/revision is a blocker.

```bash
: "${CANDIDATE_REMOTE:?Verify the candidate source remote first}"
git fetch --no-tags "$CANDIDATE_REMOTE" "$HEAD_SHA" || exit 1
git switch --detach "$HEAD_SHA" || exit 1
if [ "$(git rev-parse HEAD)" != "$HEAD_SHA" ]; then
  echo "Local source does not match the hosted candidate; stop." >&2
  exit 1
fi
```

Repeat the live comparison check after preparation/waiting and before analysis.
For Perforce, analyze the selected shelf's described diff/file revisions, not an
unrelated workspace's local files; restoring a shelf belongs to the authorized fix
phase below. Keep the exact shelf identity in source-verification receipts.

### 2. Fetch PR/MR/CL details

**GitHub:**
```bash
gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json title,body,state,reviews,comments,headRefName,statusCheckRollup
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/comments?per_page=100"
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/reviews?per_page=100"
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/issues/$PR_NUMBER/comments?per_page=100"
```

GitHub PRs are also issues, so general PR comments live on the issue comments endpoint. Greptile may edit a single general PR comment on each review cycle. First retain the configured app's exact bot login and numeric actor ID from trusted installation/provider configuration; use the guarded filter in [the GraphQL reference](references/graphql-queries.md#fetch-general-pr-comments-edited-in-place-rest). Similar logins and human-editable description text do not authenticate provider evidence. Inspect only authenticated, current-request-bound summaries by `updated_at`, including "Prompt to fix all with AI".

During this initial collection, also fetch thread state **before** analysis or
categorization. REST comment history has no thread-level resolution state:

```bash
gh api --hostname "$GH_HOST" graphql -f query='
query($cursor: String) {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes { databaseId body path author { login } }
          }
        }
      }
    }
  }
}'
```

Follow every thread cursor. Separately paginate each thread's remaining comments:

```bash
gh api --hostname "$GH_HOST" graphql -f threadId=THREAD_ID -f commentCursor=ENDCURSOR -f query='
query($threadId: ID!, $commentCursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $commentCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { databaseId body path author { login } }
      }
    }
  }
}'
```

Read every page before proceeding ([reference](references/graphql-queries.md)). Bind
the GraphQL query's `OWNER`, `REPO` and `PR_NUMBER` placeholders to the captured
target repository and number, never the fork's identity. Join
REST comment IDs to GraphQL `databaseId`; missing thread state is unknown, not
unresolved. Resolved threads are historical, not automatically current actionable
feedback. Read all replies and retain their source-backed disposition in the
ledger; if a defect demonstrably persists, report it separately with current-source
evidence rather than blindly replaying a resolved request. Refresh state after
waiting and before reporting/fixing findings, and again before resolution.

**GitLab:**
```bash
glab api --hostname "$GITLAB_HOST" "projects/$MR_PROJECT_ID/merge_requests/$MR_IID"
# Fetch discussions (inline diff comments are type "DiffNote"; general comments have null type)
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes?per_page=100"
```

Inspect every page and compare note `updated_at` values to detect edited summaries.

**Perforce:**
```bash
# Get changelist description, files, and status
p4 describe -s <CL_NUMBER>

# Get shelved files and their diff (for in-review CLs)
p4 describe -S <CL_NUMBER>

```

Fetch review comments through the configured Helix Swarm or other review-system
API, bound to the selected changelist's review ID. The Perforce CLI's automated
review-daemon command does not expose comments or resolution state. If no review
system is configured, report that comment evidence is unavailable rather than
claiming there are no findings.

Key Perforce CL fields:
- `Change`: changelist number
- `Status`: `pending`, `submitted`, `shelved`
- `Description`: the CL description / commit message
- `Files`: list of files in the CL

### 3. Wait for pending checks

First discover the required/expected gate set from the repository contract,
native target-branch protection/rules and CI configuration (including external
integrations). Retain that evidence. For GitHub inspect applicable rules and
required checks for the PR's target; for GitLab inspect project/merge policies
and the effective CI configuration, including referenced includes. An unavailable
policy/configuration is an unknown gate set, not an empty one.

If the configured gate set is confirmed empty, record CI as **N/A** and skip the
wait for a pipeline/check that is not expected to exist; proceed to analysis.
An empty status response alone never establishes N/A. Expected checks that have
not appeared remain missing-gate blockers.

Capture the candidate head/base before checking status. Check only that revision's
checks, with at most 20 attempts at 30-second intervals (ten minutes). If checks
remain pending or no current-head pipeline appears by that deadline, report the
pending/missing gates as blockers and stop waiting. Never interpret an API error,
missing check, skipped or canceled gate as a pass. A head change requires fresh
revision binding.

**GitHub:** capture `headRefOid` and `baseRefOid`, then inspect `statusCheckRollup`
with the explicitly targeted command and verify both revisions on each attempt:

```bash
CURRENT_REVISION=$(gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json headRefOid,baseRefOid,statusCheckRollup) || exit 1
if [ "$(echo "$CURRENT_REVISION" | jq -r '.headRefOid')" != "$HEAD_SHA" ] \
  || [ "$(echo "$CURRENT_REVISION" | jq -r '.baseRefOid')" != "$BASE_SHA" ]; then
  echo "PR head/base moved; stop and requalify the comparison." >&2
  exit 1
fi
```

Retain head/base-bound receipts; a target advance requires fresh comparison qualification.

**GitLab:**
```bash
MR=$(glab api --hostname "$GITLAB_HOST" "projects/$MR_PROJECT_ID/merge_requests/$MR_IID") || exit 1
# Load the MR identity helpers from references/gitlab-api.md first.
MR_REVISION=$(mr_revision) || exit 1
HEAD_SHA=$(echo "$MR_REVISION" | jq -er '.source_sha') || exit 1
TARGET_SHA=$(echo "$MR_REVISION" | jq -er '.target_sha') || exit 1
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100"
```
Use [the pipeline input/ownership binding](references/gitlab-api.md#fetch-pipeline-status-for-an-mr)
to select a configured applicable pipeline, including a merged-results pipeline
whose temporary SHA differs from the source head. Retain its ID, owner and SHA.
On each attempt call `assert_mr_revision` and inspect jobs through that owner.
Pipeline statuses: `running`, `pending`, `success`, `failed`, `canceled`, `skipped`.
Only actual successful current-head gates qualify; old terminal pipelines do not.
Immediately before accepting receipts and before each GitLab reply/resolution,
call `assert_mr_revision`; a source, live target or diff-ref change invalidates reuse.

**Perforce:** Perforce doesn't have built-in CI checks natively. If the team uses a review tool (Swarm, etc.) or an external CI triggered by shelve events, check the relevant system. Otherwise, proceed to analysis immediately.

### 4. Analyze the PR/MR

Once all checks are complete, evaluate these areas:

#### A. Status Checks

- Are all CI checks passing?
- If any are failing, identify which ones and the failure reason.

#### B. PR/MR Description

- Is the description complete and follows team conventions?
- Are all required sections filled in?
- Are there TODOs or placeholders that need updating?

#### C. Review Comments

- Inline code review comments that need addressing
- Use initial GraphQL `isResolved` state, not every historical REST comment, to
  identify current GitHub inline feedback. Keep resolved findings in the audit.
- Look for bot review comments (e.g. from `greptile-apps[bot]` on GitHub, or the Greptile bot user on GitLab, linters, etc.)
- Human reviewer comments
- **Perforce:** comments from the configured Swarm or other review-system API

#### D. General Comments

- Discussion comments on the PR/MR
- For GitHub, check the issue comments endpoint and use `updated_at` to catch bot comments edited in place. Greptile's latest edited summary can contain actionable items even when there are no new inline comments.
- Bot comments (deploy previews, etc.) — usually informational
- **Perforce:** CL description should include a clear summary, affected files rationale, and testing notes

### 5. Categorize issues

For each issue found, categorize as:

| Category | Meaning |
|---|---|
| **Actionable** | Code changes, test improvements, or fixes needed |
| **Informational** | Verification notes, questions, or FYIs that don't require changes |
| **Already addressed** | Issues that appear to be resolved by subsequent commits |

### 6. Report findings

Present a summary table:

| Area | Issue | Status | Action Needed |
|------|-------|--------|---------------|
| Status Checks | CI build failing | Failing | Fix type error in `src/api.ts` |
| Review | "Add null check" — @reviewer | Actionable | Add guard clause |
| Description | TODO placeholder in test plan | Actionable | Fill in test plan |
| Review | "Looks good" — @teammate | Informational | None |

### 7. Fix issues (if requested)

If there are actionable items:

1. Revalidate the live comparison/shelf identity. For Git, require local `HEAD`
   still equals the prepared hosted head before editing; do not switch to an
   unverified local branch. For Perforce, prepare the selected CL as below.
2. Use the user's existing authorization to fix issues. Ask only when the task
   did not authorize changes or a material product decision is required.
3. Make confirmed fixes, then:

Re-run step 3's live comparison guard and this local guard **before** editing:

```bash
LOCAL_HEAD=$(git rev-parse HEAD) || exit 1
if [ "$LOCAL_HEAD" != "$HEAD_SHA" ]; then
  echo "Local source moved; stop before applying review fixes." >&2
  exit 1
fi
```

**GitHub/GitLab:** commit and push:
```bash
git diff --cached --quiet || { echo "Unexpected staged work; stop without changing it." >&2; exit 1; }
git add -- <files>
git diff --cached --check || exit 1
# Inspect the entire staged diff and verify every hunk belongs to this task.
git commit -m "fix: describe the confirmed review issue"
# Recheck the hosted comparison, and verify the complete commit range is task-owned.
# PUBLISH_REMOTE and HEAD_BRANCH must be the verified candidate source repository/ref.
git push "${PUBLISH_REMOTE:?Verify candidate source remote}" "HEAD:refs/heads/${HEAD_BRANCH:?Verify candidate branch}"
```

**Perforce:** before restoring a shelf, inspect `p4 opened` and a nonmutating
`p4 reconcile -n` preview. Refuse foreign/opened/unopened modifications; never use
force unshelve or move someone else's work. Verify the selected pending CL's
`User` and `Client` match the effective identity. If a handoff needs another CL,
obtain explicit authorization and record the new review/shelf identity instead.
When the shelf is not already open, restore it into the selected pending CL:

```bash
p4 unshelve -s <CL_NUMBER> -c <CL_NUMBER> || exit 1
p4 opened -c <CL_NUMBER>
# Inspect all restored files; resolve any integration requirements before editing.
# For a shelved edit (other actions retain their restored action):
p4 edit -c <CL_NUMBER> <file> || exit 1
# Verify the file is opened in this CL, not default or another numbered CL.
p4 opened -c <CL_NUMBER> <file>
OPENED_FILE=$(p4 -ztag -Mj opened <file>) || exit 1
echo "$OPENED_FILE" | jq -es --arg cl "<CL_NUMBER>" 'length == 1 and (.[0].change | tostring) == $cl' >/dev/null || exit 1
# make changes
p4 shelve -f -c <CL_NUMBER> || exit 1
```

If already open in this task-owned CL, verify its files/actions/content against the
selected shelf before editing instead of unshelving over work. Recheck association
and the full CL file inventory immediately before reshelving; preserve adds,
deletes and moves rather than converting every shelved action to `edit`.

### 8. Validate the published revision

After publication, repeat step 3 against the new head (or exact updated shelf
identity), retaining successful required checks and a current completed review.
Verify the live head/base or shelf still matches that evidence. Failed, skipped,
canceled, missing or pending gates keep actionable threads open; report the
blocker instead of resolving. Reconcile any new feedback before proceeding.

### 9. Resolve review threads

For GitHub, re-read `headRefOid` and `baseRefOid` immediately before each reply or
resolution. If either changed, leave threads open and repeat revision-bound
qualification instead of accepting old comparison evidence.

Reply with the published fix revision and successful validation receipts before
resolving each actionable thread. For an informational or false-positive finding,
reply with source-backed evidence. Inspect the complete thread, including all
follow-up replies, and keep outstanding questions or product decisions open.

**Perforce** — respond to addressed findings through the configured Swarm or
other review-system API and use that system's supported resolution operation.
Do not substitute an automated depot review-daemon command for a comment API.
Retain the reply and resolution receipts bound to the selected review/changelist.

**GitHub** — repeat step 2's paginated thread-state collection, including all
secondary comment pages, to obtain fresh unresolved IDs and follow-up replies.

Then resolve threads that have been addressed or are informational:

```bash
gh api --hostname "$GH_HOST" graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_ID"}) {
    thread { isResolved }
  }
}'
```

Batch multiple resolutions into a single mutation using aliases (`t1`, `t2`, etc.).

**GitLab** — fetch unresolved discussions (see [the GitLab API reference](references/gitlab-api.md)):

```bash
glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
```

Select discussions containing a relevant note with `resolvable == true` and
`resolved == false`; these fields belong to `notes[]`, not the discussion.
Inspect all notes before resolving and retain the enclosing discussion's `id`.

Resolve each discussion individually (GitLab has no batch resolution):

```bash
glab api --hostname "$GITLAB_HOST" --method PUT \
  "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

Repeat for each unresolved discussion ID.

### 10. Multiple PRs/MRs/CLs

If checking a chain of PRs/MRs/CLs, process them sequentially.

**Perforce** — to check multiple changelists at once:
```bash
p4 changes -s pending -u "$REVIEW_USER" -c "$REVIEW_CLIENT" -l
p4 changes -s shelved -u "$REVIEW_USER" -c "$REVIEW_CLIENT" -l
```

## Output format

Summarize:
- PR/MR/CL title or description and current state
- Platform detected (GitHub / GitLab / Perforce)
- Status checks summary (passing/failing/pending) — or N/A for Perforce
- Total issues found
- Actionable items with descriptions
- Items that can be ignored with reasons
- Recommended next steps
