---
name: check-pr
description: >
  Inspect PR/MR/CL review feedback, CI and descriptions; fix confirmed issues and
  resolve addressed threads with revision-bound evidence. Supports GitHub, GitLab and Perforce.
license: MIT
compatibility: Requires git and gh (GitHub CLI), glab (GitLab CLI), or p4 (Perforce CLI) installed and authenticated.
metadata:
  author: greptileai
  version: "1.3"
allowed-tools: Bash(gh:*) Bash(glab:*) Bash(git:*) Bash(p4:*)
---

# Check PR

Read [the repository contract](references/repository-contract.md) first. It
governs authority, revision binding, hosted-only validation and thread resolution
when applying the upstream workflow below.

Analyze a pull request (GitHub), merge request (GitLab), or shelved changelist (Perforce) for review comments, status checks, and description completeness, then help address any issues found.

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

For self-hosted GitLab instances whose hostname doesn't contain "gitlab", the user can override by passing `--vcs gitlab` as an input. For Perforce, the user can override by passing `--vcs perforce`.

### 1. Identify the PR/MR/CL

If a number was provided, use it. Otherwise, detect it:

**GitHub:**
```bash
gh pr view --json number -q .number
```

**GitLab:**
```bash
glab mr view --output json | jq '.iid'
```

**Perforce:**
```bash
# List shelved and pending candidates for the current user/client
p4 changes -s shelved -u "$P4USER" -c "$P4CLIENT"
p4 changes -s pending -u "$P4USER" -c "$P4CLIENT"
```

Key field differences between platforms:
- GitHub: `number`, `headRefName`, `headRefOid`
- GitLab: `iid`, `source_branch`, `sha`
- Perforce: changelist number (CL), `shelved` files for in-review CLs

### 2. Fetch PR/MR/CL details

**GitHub:**
```bash
gh pr view <PR_NUMBER> --json title,body,state,reviews,comments,headRefName,statusCheckRollup
gh api --paginate "repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments?per_page=100"
gh api --paginate "repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews?per_page=100"
gh api --paginate "repos/{owner}/{repo}/issues/<PR_NUMBER>/comments?per_page=100"
```

GitHub PRs are also issues, so general PR comments live on the issue comments endpoint. Greptile may edit a single general PR comment on each review cycle instead of creating a new review or comment. Always inspect the latest Greptile-authored general comment by `updated_at`, including any "Prompt to fix all with AI" section, before concluding that the PR is clear.

**GitLab:**
```bash
glab mr view <MR_IID> --output json
# Fetch discussions (inline diff comments are type "DiffNote"; general comments have null type)
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/notes?per_page=100"
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

Capture the candidate head before checking status. Check only that revision's
checks, with at most 20 attempts at 30-second intervals (ten minutes). If checks
remain pending or no current-head pipeline appears by that deadline, report the
pending/missing gates as blockers and stop waiting. Never interpret an API error,
missing check, skipped or canceled gate as a pass. A head change requires fresh
revision binding.

**GitHub:** capture `headRefOid`, then inspect `statusCheckRollup` from `gh pr view`
and verify the head has not changed on each attempt.

**GitLab:**
```bash
HEAD_SHA=$(glab mr view <MR_IID> --output json | jq -r '.sha')
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/pipelines?per_page=100"
```
Select the applicable pipeline with `sha == HEAD_SHA` and retain its ID. Do not
fall back to an older SHA while waiting for the new pipeline to appear. On each
attempt, verify the MR still has that head and inspect that pipeline's jobs.
Pipeline statuses: `running`, `pending`, `success`, `failed`, `canceled`, `skipped`.
Only actual successful current-head gates qualify; old terminal pipelines do not.

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

1. Switch to the PR/MR's branch (git) or ensure files are open in the correct CL (Perforce) if not already.
2. Use the user's existing authorization to fix issues. Ask only when the task
   did not authorize changes or a material product decision is required.
3. Make confirmed fixes, then:

**GitHub/GitLab:** commit and push:
```bash
git add <files>
git commit -m "fix: describe the confirmed review issue"
git push
```

**Perforce:** open files for edit, make changes, and re-shelve:
```bash
p4 edit <file>
# make changes
p4 shelve -f -c <CL_NUMBER>
```

### 8. Validate the published revision

After publication, repeat step 3 against the new head (or exact updated shelf
identity), retaining successful required checks and a current completed review.
Verify the live head/base or shelf still matches that evidence. Failed, skipped,
canceled, missing or pending gates keep actionable threads open; report the
blocker instead of resolving. Reconcile any new feedback before proceeding.

### 9. Resolve review threads

Reply with the published fix revision and successful validation receipts before
resolving each actionable thread. For an informational or false-positive finding,
reply with source-backed evidence. Inspect the complete thread, including all
follow-up replies, and keep outstanding questions or product decisions open.

**Perforce** — respond to addressed findings through the configured Swarm or
other review-system API and use that system's supported resolution operation.
Do not substitute an automated depot review-daemon command for a comment API.
Retain the reply and resolution receipts bound to the selected review/changelist.

**GitHub** — fetch unresolved thread IDs (paginate if needed — see [the GraphQL reference](references/graphql-queries.md)):

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

If `hasNextPage` is true, repeat with `-f cursor=ENDCURSOR` to get remaining threads.
For each thread with more comments, paginate the comments connection separately:

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

Repeat until that thread's comments have all been read.

Then resolve threads that have been addressed or are informational:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_ID"}) {
    thread { isResolved }
  }
}'
```

Batch multiple resolutions into a single mutation using aliases (`t1`, `t2`, etc.).

**GitLab** — fetch unresolved discussions (see [the GitLab API reference](references/gitlab-api.md)):

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
```

Select discussions containing a relevant note with `resolvable == true` and
`resolved == false`; these fields belong to `notes[]`, not the discussion.
Inspect all notes before resolving and retain the enclosing discussion's `id`.

Resolve each discussion individually (GitLab has no batch resolution):

```bash
glab api --method PUT \
  "projects/:fullpath/merge_requests/<MR_IID>/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

Repeat for each unresolved discussion ID.

### 10. Multiple PRs/MRs/CLs

If checking a chain of PRs/MRs/CLs, process them sequentially.

**Perforce** — to check multiple changelists at once:
```bash
p4 changes -s pending -u $P4USER -c $P4CLIENT -l
p4 changes -s shelved -u "$P4USER" -c "$P4CLIENT" -l
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
