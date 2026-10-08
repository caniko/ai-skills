---
name: greploop
description: >
  Run a bounded Greptile review-and-fix loop for a PR/MR/CL, targeting 5/5
  confidence and no unresolved findings while retaining CI and merge gates.
license: MIT
compatibility: Requires git, gh (GitHub CLI) or glab (GitLab CLI) authenticated, and Greptile installed on the repo. For Perforce, requires p4 CLI authenticated.
metadata:
  author: greptileai
  version: "1.3"
allowed-tools: Bash(gh:*) Bash(glab:*) Bash(git:*) Bash(p4:*)
---

# Greploop

Read [the repository contract](references/repository-contract.md) first. The
confidence target below is a review-loop stopping signal, not merge permission.

Iteratively fix a PR/MR/CL until Greptile gives a perfect review: 5/5 confidence, zero unresolved comments.

## Inputs

- **PR/MR/CL number** (optional): If not provided, detect the PR/MR for the current branch, or the default pending changelist for p4.

## Instructions

### 0. Detect platform

Prefer an actual Git worktree; global Perforce configuration does not establish
that the current directory belongs to a depot. Otherwise require a current-path
Perforce mapping:

```bash
if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" = "true" ]; then
  REMOTE_URL=$(git remote get-url origin)
  if echo "$REMOTE_URL" | grep -qi "gitlab"; then
    VCS="gitlab"
  else
    VCS="github"
  fi
elif p4 where "$PWD/..." >/dev/null 2>&1; then
  VCS="perforce"
else
  echo "Current path is not a Git worktree or mapped Perforce workspace." >&2
  exit 1
fi
```

For self-hosted GitLab instances whose hostname doesn't contain "gitlab", the user can override by passing `--vcs gitlab` as an input. For Perforce, pass `--vcs perforce`.

### 1. Identify the PR/MR/CL

**GitHub:**
```bash
gh pr view --json number,headRefName -q '{number: .number, branch: .headRefName}'
```

**GitLab:**
```bash
glab mr view --output json | jq '{iid: .iid, branch: .source_branch}'
```

Switch to the PR/MR branch if not already on it.

**Perforce:**
```bash
# List shelved and pending candidates for current user/client
p4 changes -s shelved -u "$P4USER" -c "$P4CLIENT"
p4 changes -s pending -u "$P4USER" -c "$P4CLIENT"

# Describe a specific CL
p4 describe -s <CL_NUMBER>
```

Ensure the correct workspace (`p4 client`) is set before proceeding.

Key field differences:
- GitHub: `number`, `headRefName`, `headRefOid`
- GitLab: `iid`, `source_branch`, `sha`
- Perforce: changelist number, `P4CLIENT`, shelved files

### 2. Loop

Repeat the following cycle. **Max 5 iterations** to avoid runaway loops.

#### A. Trigger Greptile review

Push/shelve the latest changes (if any):

**GitHub/GitLab:**
```bash
git push
```

**Perforce:**
```bash
# Re-shelve to update the shelved files for review
p4 shelve -f -c <CL_NUMBER>
```

Wait for checks to start after push/shelve:

```bash
sleep 5
```

**GitHub** — check if Greptile is already running before posting a new trigger comment:

```bash
PR_REVISION=$(gh pr view <PR_NUMBER> --json headRefOid,baseRefOid) || exit 1
HEAD_SHA=$(echo "$PR_REVISION" | jq -er '.headRefOid') || exit 1
BASE_SHA=$(echo "$PR_REVISION" | jq -er '.baseRefOid') || exit 1
gh api --paginate "repos/{owner}/{repo}/commits/$HEAD_SHA/check-runs?per_page=100"
```

Verify the installed review provider's app identity, not just a matching check
name. Reconcile every matching pending request/check at this head before posting
another trigger. If a current request is already queued or running, reuse it.
Require its receipt to cover the captured head/base pair; a check's `head_sha`
alone does not prove base coverage. A request for an older base cannot be reused.
Otherwise retain the current check IDs and request timestamp, then request a
fresh review:

```bash
DRAFT=$(gh pr view <PR_NUMBER> --json isDraft | jq -r '.isDraft') || exit 1
case "$DRAFT" in
  true) REVIEW_TRIGGER="@greptileai review this draft" ;;
  false) REVIEW_TRIGGER="@greptileai review" ;;
  *) echo "Missing PR draft state; stop before requesting review." >&2; exit 1 ;;
esac
gh pr comment <PR_NUMBER> --body "$REVIEW_TRIGGER"
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

  CURRENT_REVISION=$(gh pr view <PR_NUMBER> --json headRefOid,baseRefOid) || exit 1
  if [ "$(echo "$CURRENT_REVISION" | jq -r '.headRefOid')" != "$HEAD_SHA" ] \
    || [ "$(echo "$CURRENT_REVISION" | jq -r '.baseRefOid')" != "$BASE_SHA" ]; then
    echo "PR head/base moved; stop and reconcile the review request." >&2
    exit 1
  fi
  GREPTILE_CHECK=$(gh api "repos/{owner}/{repo}/check-runs/$CHECK_RUN_ID") || exit 1
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
MR=$(glab mr view <MR_IID> --output json) || exit 1
MR_PROJECT_ID=$(echo "$MR" | jq -er '.target_project_id') || exit 1
MR_IID=$(echo "$MR" | jq -er '.iid') || exit 1
# Load the MR identity helpers from the declared check-pr dependency first.
MR_REVISION=$(mr_revision) || exit 1
HEAD_SHA=$(echo "$MR_REVISION" | jq -er '.source_sha') || exit 1
TARGET_SHA=$(echo "$MR_REVISION" | jq -er '.target_sha') || exit 1
glab api --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/pipelines?per_page=100"
```

Load the comparison/pipeline binding from
[check-pr's declared dependency](.skillnet/deps/check-pr/references/gitlab-api.md).
Inspect MR-associated pipelines and their paginated jobs for the verified
provider. Reconcile an existing review request before posting another trigger;
an unrelated running pipeline does not establish a pending Greptile review.
If no current request exists, retain its timestamp and request a review:

```bash
DRAFT=$(glab mr view <MR_IID> --output json | jq -r '.draft') || exit 1
case "$DRAFT" in
  true) REVIEW_TRIGGER="@greptileai review this draft" ;;
  false) REVIEW_TRIGGER="@greptileai review" ;;
  *) echo "Missing MR draft state; stop before requesting review." >&2; exit 1 ;;
esac
glab mr note <MR_IID> --message "$REVIEW_TRIGGER"
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

**GitHub:**

**1. PR description (body):**
```bash
gh pr view <PR_NUMBER> --json body -q '.body'
```

**2. General PR comments (issue comments):**
```bash
gh api --paginate "repos/{owner}/{repo}/issues/<PR_NUMBER>/comments?per_page=100"
```

Filter for Greptile-authored comments and use the body from the most recently updated comment (`updated_at`), not the most recently created comment. Greptile may edit the same general PR comment on each review cycle; parse the current body, including the "Prompt to fix all with AI" section, before deciding there are no remaining issues.

**3. PR reviews:**
```bash
gh api --paginate "repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews?per_page=100"
```

Look for the most recent entry from `greptile-apps[bot]` or `greptile-apps-staging[bot]`.

**GitLab:**

**1. MR description (body):**
```bash
glab mr view <MR_IID> --output json | jq -r '.description'
```

**2. MR notes (comments):**
```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/notes?per_page=100"
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

Filter to comments authored by the Greptile bot:
- Prefer exact username match if known
- Otherwise, use a heuristic where the author name contains "greptile" (case-insensitive)

For all platforms, parse the text for:
- **Confidence score**: a pattern like `3/5` or `5/5` (or `Confidence: 3/5`).
- **Comment count**: Number of inline review comments noted in the summary.

Use whichever source has the **most recently updated** score. For GitHub, prefer `updated_at` from issue comments when comparing an edited Greptile summary against older review entries.

Also fetch all unresolved inline comments:

**GitHub:**
```bash
gh api --paginate "repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments?per_page=100"
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
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
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
git add <scoped-files>
git commit -m "fix: describe the confirmed review issue"
git push
```

**Perforce:**
```bash
# Publish the updated shelf for the next review round
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
gh api graphql -f query='
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

If `hasNextPage` is true, repeat with `-f cursor=ENDCURSOR` until every thread has
been read. Inspect each thread's complete comment history before disposition;
paginate the comments connection separately when needed.

```bash
gh api graphql -f threadId=THREAD_ID -f commentCursor=ENDCURSOR -f query='
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
gh api graphql -f query='
mutation {
  t1: resolveReviewThread(input: {threadId: "ID1"}) { thread { isResolved } }
  t2: resolveReviewThread(input: {threadId: "ID2"}) { thread { isResolved } }
}'
```

**GitLab** — fetch unresolved discussions and resolve each one (see [GitLab API reference](references/gitlab-api.md)):

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
```

Select discussions containing a relevant note with `resolvable == true` and
`resolved == false`. Inspect every note before resolving the enclosing discussion
by its `id`:

```bash
glab api --method PUT \
  "projects/:fullpath/merge_requests/<MR_IID>/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

Repeat for each unresolved discussion ID. (GitLab has no batch resolution — loop through each one.)

Then go back to steps **B/C**, using the review already completed in step F.
Count that result as the next bounded iteration and evaluate its exit conditions
before requesting anything else. Return to A only if the candidate changed or a
current completed review receipt is missing; do not retrigger a review already
obtained during validation.

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
