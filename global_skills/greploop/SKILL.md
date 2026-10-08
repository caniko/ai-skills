---
name: greploop
description: >
  Run a bounded Greptile review-and-fix loop for a PR/MR/CL, targeting 5/5
  confidence and no unresolved findings while retaining CI and merge gates.
license: MIT
compatibility: Requires jq and git with authenticated gh (GitHub CLI) or glab (GitLab CLI), and Greptile installed on the repo. For Perforce, requires authenticated p4 with JSON output support.
metadata:
  author: greptileai
  version: "1.3"
allowed-tools: Bash(gh:*) Bash(glab:*) Bash(git:*) Bash(p4:*) Bash(jq:*) Bash(canix repo review:*) Bash(canix repo merge:*) Bash(canix-toolbelt repo review:*) Bash(canix-toolbelt repo merge:*)
---

# Greploop

Read [the repository contract](references/repository-contract.md) first. The
confidence target below is a review-loop stopping signal, not merge permission.

Iteratively fix a PR/MR/CL until Greptile gives a perfect review: 5/5 confidence, zero unresolved comments.

## Inputs

- **PR/MR/CL number** (optional): If not provided, detect the PR/MR for the current branch, or the default pending changelist for p4.
- **GitHub target**: Set `PR_TARGET_REPO` to `OWNER/REPO` and `GH_HOST` from the
  verified upstream PR URL. Ask for the URL if unknown; never infer upstream from
  a fork remote. All GitHub CLI/API requests use this captured target.
- **GitLab target repository**: Set `MR_TARGET_REPO` to the verified upstream
  target project. If unknown, ask for the MR URL; never guess from a fork remote.

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

For self-hosted GitLab instances whose hostname doesn't contain "gitlab", the user can override by passing `--vcs gitlab` as an input. For Perforce, pass `--vcs perforce`.

Map an explicit Git platform input to `VCS` before detection. Set `PLATFORM_REMOTE`
for another verified remote; a failed lookup never silently defaults to GitHub.

For Git, refuse a dirty baseline before branch switching, any loop edits or
publication. Preserve existing staged, unstaged and untracked work untouched;
require a clean task-owned checkout, never auto-stash/reset or publish foreign work.

```bash
BASELINE_STATUS=$(git status --porcelain=v1 --untracked-files=all) || exit 1
if [ -n "$BASELINE_STATUS" ]; then
  echo "Dirty baseline; preserve existing work and stop before edits/publication." >&2
  exit 1
fi
```

Keep the fix checkout task-owned. If concurrent foreign edits arrive, stop and
preserve them; the initial clean guard does not authorize those later edits.

### 1. Identify the PR/MR/CL

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
: "${MR_TARGET_REPO:?Set the verified GitLab target repository first}"
MR=$(glab mr view --repo "$MR_TARGET_REPO" --output json) || exit 1
MR_PROJECT_ID=$(echo "$MR" | jq -er '.target_project_id') || exit 1
MR_IID=$(echo "$MR" | jq -er '.iid') || exit 1
HEAD_SHA=$(echo "$MR" | jq -er '.sha') || exit 1
HEAD_BRANCH=$(echo "$MR" | jq -er '.source_branch') || exit 1
```

When supplied, pass the IID to that same command with `--repo "$MR_TARGET_REPO"`.
Use the captured target project ID and IID for all later MR API operations.

For Git, require the local source to equal the hosted candidate **before** any
review trigger, source analysis or publication:

```bash
LOCAL_HEAD=$(git rev-parse HEAD) || exit 1
if [ "$LOCAL_HEAD" != "$HEAD_SHA" ]; then
  echo "Local HEAD differs from hosted candidate; preserve unpublished commits and stop." >&2
  exit 1
fi
```

Provide a clean task-owned checkout of that exact revision if needed, preserving
the original local branch. A clean porcelain status does not authorize unpublished
commits. Extra commits require explicit authorization and a separate source-bound
publication step; never silently push them to start a review.

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

# Describe a specific CL
p4 describe -s <CL_NUMBER>
```

Ensure the correct workspace (`p4 client`) is set before proceeding. Analyze the
selected shelf, not unrelated local files. Before step D edits, use check-pr's
declared dependency preparation: refuse foreign/opened/unopened work, verify the
pending CL's owner/client, unshelve into that CL when needed and verify the file's
association with `p4 opened -c <CL_NUMBER>`. Open edits explicitly with
`p4 edit -c <CL_NUMBER> <file>`; never default to the default changelist.

Key field differences:
- GitHub: `number`, `headRefName`, `headRefOid`
- GitLab: `iid`, `source_branch`, `sha`
- Perforce: changelist number, effective client, shelved files

### 2. Loop

Repeat the following cycle. **Max 5 iterations** to avoid runaway loops.

#### A. Trigger Greptile review

No initial push or re-shelve: start from the already hosted candidate/shelf.
Only task-owned confirmed repairs are published in step E. Revalidate local and
hosted source identities before each analysis/edit phase; never refresh `HEAD_SHA`
to a moved candidate without also preparing and verifying that local source.

**GitHub** — check if Greptile is already running before posting a new trigger comment:

```bash
PR_REVISION=$(gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json headRefOid,baseRefOid) || exit 1
HEAD_SHA=$(echo "$PR_REVISION" | jq -er '.headRefOid') || exit 1
BASE_SHA=$(echo "$PR_REVISION" | jq -er '.baseRefOid') || exit 1
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/commits/$HEAD_SHA/check-runs?per_page=100"
```

Re-run step 1's local-head equality guard here before requesting a review. Any
newly captured head requires matching local source, not just clean worktree status.

Verify the installed review provider's app identity, not just a matching check
name. Retain the configured app's exact bot login and numeric actor ID as
`GREPTILE_BOT_LOGIN` / `GREPTILE_BOT_ID`, verified from trusted installation/provider
configuration, not inferred from an arbitrary PR comment. Unknown identity blocks
result acceptance; do not use substring/regex or staging-account fallbacks.
Reconcile every matching pending request/check at this head before posting
another trigger. If a current request is already queued or running, reuse it.
Require its receipt to cover the captured head/base pair; a check's `head_sha`
alone does not prove base coverage. A request for an older base cannot be reused.
Otherwise retain the current check IDs and request timestamp, then request a
fresh review:

```bash
DRAFT=$(gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json isDraft | jq -r '.isDraft') || exit 1
case "$DRAFT" in
  true) REVIEW_TRIGGER="@greptileai review this draft" ;;
  false) REVIEW_TRIGGER="@greptileai review" ;;
  *) echo "Missing PR draft state; stop before requesting review." >&2; exit 1 ;;
esac
gh pr comment --repo "$PR_TARGET_REPO" "$PR_NUMBER" --body "$REVIEW_TRIGGER"
```

Bind `CHECK_RUN_ID` to the single check belonging to that current request and
head. For a new request, do not reuse a completed check that predates the
request; retain its provider/request evidence. If no attributable run appears
within ten minutes, stop and report the missing receipt. Do not guess the run by
its name, choose an arbitrary latest run, or concatenate multiple JSON objects.
Then poll that immutable check ID:

```bash
CHECK_RUN_ID=<CURRENT_REVIEW_CHECK_RUN_ID>
ATTEMPTS=0
MAX_ATTEMPTS=60
POLL_INTERVAL_SECONDS=10

while true; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -gt "$MAX_ATTEMPTS" ]; then
    echo "Timed out waiting for the Greptile check run after approximately 10 minutes." >&2
    exit 1
  fi

  CURRENT_REVISION=$(gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json headRefOid,baseRefOid) || exit 1
  if [ "$(echo "$CURRENT_REVISION" | jq -r '.headRefOid')" != "$HEAD_SHA" ] \
    || [ "$(echo "$CURRENT_REVISION" | jq -r '.baseRefOid')" != "$BASE_SHA" ]; then
    echo "PR head/base moved; stop and reconcile the review request." >&2
    exit 1
  fi
  GREPTILE_CHECK=$(gh api --hostname "$GH_HOST" "repos/$PR_TARGET_REPO/check-runs/$CHECK_RUN_ID") || exit 1
  if [ "$(echo "$GREPTILE_CHECK" | jq -r '.head_sha')" != "$HEAD_SHA" ]; then
    echo "Review check is not bound to the candidate head." >&2
    exit 1
  fi

  STATUS=$(echo "$GREPTILE_CHECK" | jq -r '.status')
  CONCLUSION=$(echo "$GREPTILE_CHECK" | jq -r '.conclusion // "pending"')
  
  if [ "$STATUS" = "completed" ]; then
    if [ "$CONCLUSION" = "success" ]; then
      echo "Greptile check passed!"
    else
      echo "Greptile check completed with: $CONCLUSION" >&2
      exit 1
    fi
    break
  fi
  
  echo "Waiting for Greptile... (status: $STATUS)"
  sleep "$POLL_INTERVAL_SECONDS"
done
```

If polling times out, stop the greploop workflow and report the timeout. Do not continue with stale or missing review results.

**GitLab** — check if Greptile is already running before posting a trigger comment:

```bash
MR=$(glab api "projects/$MR_PROJECT_ID/merge_requests/$MR_IID") || exit 1
# Load the MR identity helpers from the declared check-pr dependency first.
MR_REVISION=$(mr_revision) || exit 1
HEAD_SHA=$(echo "$MR_REVISION" | jq -er '.source_sha') || exit 1
TARGET_SHA=$(echo "$MR_REVISION" | jq -er '.target_sha') || exit 1
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100"
```

Load the comparison/pipeline binding from
[check-pr's declared dependency](.skillnet/deps/check-pr/references/gitlab-api.md).
Re-run step 1's local-head equality guard for this captured source before reviewing.
Inspect MR-associated pipelines and their paginated jobs for the verified
provider. Reconcile an existing review request before posting another trigger;
an unrelated running pipeline does not establish a pending Greptile review.
If no current request exists, retain its timestamp and request a review:

```bash
DRAFT=$(glab api "projects/$MR_PROJECT_ID/merge_requests/$MR_IID" | jq -r '.draft') || exit 1
case "$DRAFT" in
  true) REVIEW_TRIGGER="@greptileai review this draft" ;;
  false) REVIEW_TRIGGER="@greptileai review" ;;
  *) echo "Missing MR draft state; stop before requesting review." >&2; exit 1 ;;
esac
glab api --method POST "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes" -f body="$REVIEW_TRIGGER"
```

Retain `PIPELINE_ID`, owning `PIPELINE_PROJECT_ID` and `PIPELINE_SHA` after executing
the referenced pipeline binding. A merged-results temporary SHA need not equal
`HEAD_SHA`; its current source/target parents must be proven. Bind `JOB_ID` to
this pipeline and provider/request comparison evidence (see [GitLab API reference](references/gitlab-api.md)).
Retried jobs have distinct IDs: do not reuse the earlier attempt or select all
jobs whose names match. Stop if no attributable job appears within ten minutes.
Then poll that immutable job ID:

```bash
JOB_ID=<CURRENT_REVIEW_JOB_ID>
ATTEMPTS=0
MAX_ATTEMPTS=60
POLL_INTERVAL_SECONDS=10

while true; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -gt "$MAX_ATTEMPTS" ]; then
    echo "Timed out waiting for the Greptile pipeline job after approximately 10 minutes." >&2
    exit 1
  fi

  assert_mr_revision || exit 1
  GREPTILE_JOB=$(glab api "projects/$PIPELINE_PROJECT_ID/jobs/$JOB_ID") || exit 1
  if ! echo "$GREPTILE_JOB" | jq -e --arg sha "$PIPELINE_SHA" --argjson pipeline "$PIPELINE_ID" --argjson project "$PIPELINE_PROJECT_ID" \
    '.commit.id == $sha and .pipeline.id == $pipeline and .pipeline.project_id == $project' >/dev/null; then
    echo "Review job is not bound to the verified MR pipeline/owner." >&2
    exit 1
  fi

  JOB_STATUS=$(echo "$GREPTILE_JOB" | jq -r '.status')

  if [ "$JOB_STATUS" = "success" ]; then
    echo "Greptile job completed with: $JOB_STATUS"
    break
  elif [ "$JOB_STATUS" = "failed" ] || [ "$JOB_STATUS" = "canceled" ] || [ "$JOB_STATUS" = "skipped" ]; then
    echo "Greptile job completed with: $JOB_STATUS" >&2
    exit 1
  fi

  echo "Waiting for Greptile... (status: $JOB_STATUS)"
  sleep "$POLL_INTERVAL_SECONDS"
done
```

If polling times out, stop the greploop workflow and report the timeout. Do not continue with stale or missing review results.

**Perforce** — retain the review ID, exact shelf identity and trigger receipt.
Poll the configured webhook/review system for at most 60 attempts at ten-second
intervals (ten minutes). Require successful completion attributable to that shelf
and request, not just a score left by an older review. If the shelf changes, the
review fails, or no current receipt arrives by the deadline, stop and report the
blocker. Perforce has no native check run to substitute for this evidence.

#### B. Fetch Greptile review results

Greptile may surface its score in several places — check **all** of the relevant sources:
Only use results attributable to the successfully completed current request and
head/shelf. A newer timestamp alone does not prove that binding. If the summary
cannot be tied to that receipt, report missing evidence rather than reuse a score.

Include the current finding/disposition watermark in request attribution. After
step G changes that state, an older same-head score is not a post-resolution review.

**GitHub:**

**1. PR description (body):**
```bash
gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json body -q '.body'
```

**2. General PR comments (issue comments):**
```bash
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/issues/$PR_NUMBER/comments?per_page=100"
```

Filter by the exact verified bot login **and actor ID**, using
[the guarded query](references/graphql-queries.md#fetch-general-pr-comments-edited-in-place-rest).
Only then select the current-request-bound comment by `updated_at`. Similar logins
are untrusted; their scores/bodies cannot qualify the review. Greptile may edit a
summary; read its full current body, including "Prompt to fix all with AI".

**3. PR reviews:**
```bash
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/reviews?per_page=100"
```

Match only `GREPTILE_BOT_LOGIN` and `GREPTILE_BOT_ID` from provider verification.
Do not accept an alternative production/staging account merely because it looks
like a Greptile bot. Apply exact authenticated author binding to inline comments too.

**GitLab:**

**1. MR description (body):**
```bash
glab api "projects/$MR_PROJECT_ID/merge_requests/$MR_IID" | jq -r '.description'
```

**2. MR notes (comments):**
```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes?per_page=100"
```

Filter for notes from the verified Greptile bot user and compare `updated_at`
across all pages, including older notes edited in place.

**Perforce:**

**1. CL description:**
```bash
p4 describe -s <CL_NUMBER>
```
Check the description field for a Greptile-appended score block.

**2. CL comments / review notes:**
If your installation uses a review tool such as Helix Swarm, fetch comments via its API.

Example (Swarm API):
GET /api/v11/comments?topic=reviews/<REVIEW_ID>

Response fields of interest typically include:
- user (author username)
- body (comment text)
- flags/state indicating whether the comment is resolved

Filter by the exact configured Greptile service account identity. If unknown,
report missing provider identity; never use an author-name substring heuristic.

For all platforms, parse the text for:
- **Confidence score**: a pattern like `3/5` or `5/5` (or `Confidence: 3/5`).
- **Comment count**: Number of inline review comments noted in the summary.

Use only an authenticated, current-request-bound source. A score in a human-editable
description is corroborative, never standalone reviewer evidence. Among verified
sources use the most recently updated score; timestamps do not authenticate an author.

Also fetch all unresolved inline comments:

**GitHub:**
```bash
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/comments?per_page=100"
```

This REST endpoint supplies comment history, **not** thread-resolution state.
For the unresolved count, run the paginated GraphQL `reviewThreads` query in
step G now and select verified reviewer threads with `isResolved == false`.
Follow every `pageInfo.endCursor`; do not count REST comments as unresolved.
Keep historical/outdated findings in the ledger until their disposition is
source-backed; neither age nor resolution alone proves a fix.

Also carry forward actionable items from the latest Greptile general PR comment,
especially the "Prompt to fix all with AI" section, even if the GraphQL thread
query reports zero unresolved threads.

**GitLab:**
```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
```

Paginate discussions and inspect all their notes for the verified Greptile
reviewer and `DiffNote` notes with `resolvable == true` and `resolved == false`.
Resolution state belongs to each note, not the enclosing discussion. Retain that
discussion's ID and inspect all replies before disposition. Keep older findings until
a source-backed disposition exists; do not drop them merely because the head
changed.

**Perforce:**
If using Swarm:

# Fetch inline diff comments for the review associated with the CL
GET /api/v11/comments?topic=reviews/<REVIEW_ID>

Filter to comments from the Greptile bot user that have not been marked as resolved/addressed.

#### C. Check exit conditions

Before a successful exit, perform step F for this unchanged revision, even when
the initial review has no findings. Reuse its completed review receipt rather
than requesting another review. Discover required/expected CI gates as described
in check-pr step 3; a verified empty gate set is recorded as N/A, not CI success.

Stop the loop if **any** of these are true:

- Confidence score is **5/5** AND there are **zero unresolved comments** AND
  independent current-revision CI requirements are satisfied (or verified N/A).
- Max iterations reached (report incomplete qualification, not success).

Pending, failed, skipped, canceled, missing or unknown expected gates prevent a
successful exit. Never present a clean review score as independent CI acceptance.

#### D. Fix actionable comments

For each unresolved Greptile comment:

1. Read the file and understand the comment in context.
2. Determine if it's actionable (code change needed) or informational.
3. If actionable, make the fix.
4. Record informational or false-positive dispositions for the reply in step G.
   Keep any unresolved product decision open. Do not resolve threads yet.

#### E. Commit and push / re-shelve

Only publish when step D made scoped edits. If there are no scoped edits (for
example, every finding is informational or a false positive), reuse the existing
published head or shelf, skip commit/push/re-shelve, and continue to step F. Do
not manufacture an empty commit or treat "nothing to commit" as a failed fix.

**GitHub/GitLab:**
```bash
git diff --cached --quiet || { echo "Unexpected staged work; stop without changing it." >&2; exit 1; }
git add -- <scoped-files>
git diff --cached --check || exit 1
# Inspect the entire staged diff and verify every hunk belongs to this task.
git commit -m "fix: describe the confirmed review issue"
# Recheck the hosted comparison and verify the whole commit range is task-owned.
# PUBLISH_REMOTE and HEAD_BRANCH must be the verified candidate source repository/ref.
git push "${PUBLISH_REMOTE:?Verify candidate source remote}" "HEAD:refs/heads/${HEAD_BRANCH:?Verify candidate branch}"
```

**Perforce:**
```bash
# Publish the updated shelf for the next review round
# First verify the complete CL file inventory and each edited file's association.
p4 opened -c <CL_NUMBER>
p4 shelve -f -c <CL_NUMBER>
```

If publication fails or the remote head moved, stop and reconcile. Leave the
threads open; a local edit or commit is not a published fix.

#### F. Validate the published revision

Capture the new head/base or shelf identity and obtain successful required CI
and a completed review for it, using step A's bounded, current-request checks
and the configured CI system. Retain exact-revision receipts; a completed
Greptile review alone is not required CI. Failed, skipped, canceled, missing or
pending gates keep threads open. Stop with the specific blocker at the deadline.
Inspect new feedback and verify the live candidate still matches before resolution.
Reuse existing successful review/CI receipts when the published head or shelf
has not changed; do not trigger another review merely to validate a no-edit pass.
For GitHub, reuse requires the same base too. Re-run step A's head/base guard
immediately before accepting validation receipts.
For GitLab, call `assert_mr_revision` immediately before acceptance; source-only
and merged-results receipts must retain the proven current comparison inputs.

#### G. Resolve threads

Re-run step A's head/base guard immediately before each GitHub reply/resolution.
If either revision moved, leave the thread open and obtain fresh comparison-bound
review and CI evidence; a successful old-head check is not enough.
For GitLab, call `assert_mr_revision` immediately before each reply/resolution;
leave threads open if source/target/diff identity moved.

Reply with the published fix revision and successful validation receipts before
resolving actionable findings. Explain false positives with source-backed evidence.
Do not close an outstanding question or a new finding from the latest review.

**Perforce** — after successful shelf-bound validation, post a reply to each
addressed finding through the configured Swarm or other review-system API, then
call that system's supported comment/task resolution operation. Retain the reply
ID, resolution receipt, review ID and shelf identity. Read back the review state
to verify the finding is addressed. If the API or permission is unavailable,
leave the finding open and report that blocker; do not claim zero unresolved
comments or substitute a depot review-daemon command.

**GitHub** — fetch unresolved review threads and resolve all that have been addressed (see [GraphQL reference](references/graphql-queries.md)):

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
            nodes { body path author { login } }
          }
        }
      }
    }
  }
}'
```

Resolve addressed threads:

Substitute only the captured target owner/repository and PR number into GraphQL
placeholders. A fork checkout never changes that target.

If `hasNextPage` is true, repeat with `-f cursor=ENDCURSOR` until every thread has
been read. Inspect each thread's complete comment history before disposition;
paginate the comments connection separately when needed.

```bash
gh api --hostname "$GH_HOST" graphql -f threadId=THREAD_ID -f commentCursor=ENDCURSOR -f query='
query($threadId: ID!, $commentCursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $commentCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { body path author { login } }
      }
    }
  }
}'
```

Repeat until all comments are read; a follow-up may invalidate the opening finding's disposition.

```bash
gh api --hostname "$GH_HOST" graphql -f query='
mutation {
  t1: resolveReviewThread(input: {threadId: "ID1"}) { thread { isResolved } }
  t2: resolveReviewThread(input: {threadId: "ID2"}) { thread { isResolved } }
}'
```

**GitLab** — fetch unresolved discussions and resolve each one (see [GitLab API reference](references/gitlab-api.md)):

```bash
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions?per_page=100"
```

Select discussions containing a relevant note with `resolvable == true` and
`resolved == false`. Inspect every note before resolving the enclosing discussion
by its `id`:

```bash
glab api --method PUT \
  "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

Repeat for each unresolved discussion ID. (GitLab has no batch resolution — loop through each one.)

If actual replies/resolutions changed the finding disposition and the retained
score is below 5/5, return to A before reevaluating the score for one deduplicated
post-resolution review at the same source, bound to the new disposition watermark.
Reuse only a request/receipt covering that watermark; the prior completed score
does not cover the changed disposition. Preserve the five-iteration limit and
reuse successful unchanged-source CI. A source change or missing current completed
receipt also requires A. Otherwise, do not retrigger a completed review merely for
validation. Then go back to steps **B/C** with the applicable completed review,
counting its result as the next bounded iteration.

### 3. Report

After exiting the loop, summarize:

| Field              | Value      |
| ------------------ | ---------- |
| Platform           | GitHub / GitLab / Perforce |
| Iterations         | N          |
| Final confidence   | X/5        |
| Comments resolved  | N          |
| Remaining comments | N (if any) |

If the loop exited due to max iterations, list any remaining unresolved comments and suggest next steps.

## Output format

```
Greploop complete.
  Platform:      GitHub
  Iterations:    2
  Confidence:    5/5
  Resolved:      7 comments
  Remaining:     0
```

If not fully resolved:

```
Greploop stopped after 5 iterations.
  Platform:      GitLab
  Confidence:    4/5
  Resolved:      12 comments
  Remaining:     2

Remaining issues:
  - src/auth.ts:45 — "Consider rate limiting this endpoint"
  - src/db.ts:112 — "Missing index on user_id column"
```

**Perforce example:**

```
Greploop complete.
  Platform:      Perforce
  Changelist:    12345
  Iterations:    3
  Confidence:    5/5
  Resolved:      9 comments
  Remaining:     0
```
