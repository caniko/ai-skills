# GitLab API Reference

Useful GitLab REST API calls for the greploop workflow, using `glab api`.

`glab api` automatically resolves `:fullpath` to the URL-encoded project path from the local git remote.

## Fetch MR details

```bash
glab mr view <MR_IID> --output json
```

Key fields:
- `iid` — internal MR number (use this, not `id`)
- `source_branch` — equivalent to GitHub's `headRefName`
- `sha` — HEAD commit SHA
- `description` — MR body (Greptile may update this with the confidence score)

## Trigger Greptile review

```bash
glab mr note <MR_IID> --message "@greptileai review"
```

## Fetch pipelines for an MR

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/pipelines?per_page=100"
```

Check `status` field: `running`, `pending`, `success`, `failed`, `canceled`, `skipped`.

## Fetch jobs for a pipeline (to find the Greptile job)

```bash
glab api --paginate "projects/:fullpath/pipelines/<PIPELINE_ID>/jobs?per_page=100"
```

Verify provider identity and bind one immutable job ID to the current request and
MR head, not just a matching name. Retried jobs have distinct IDs. Only `success`
allows result processing; failed/canceled/skipped jobs remain blockers.

## Inspect pending pipelines at the current head

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/pipelines?per_page=100" | \
  jq -s --arg sha "HEAD_SHA" 'add | [.[] | select(.sha == $sha and (.status == "running" or .status == "pending"))] | length'
```

An unrelated pending pipeline is not evidence of a pending Greptile request.

## Find pipeline for a specific commit SHA

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/pipelines?per_page=100" | \
  jq -s --arg sha "COMMIT_SHA" 'add | [.[] | select(.sha == $sha)]'
```

## Fetch MR notes (to find Greptile's confidence score)

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/notes?per_page=100"
```

Filter by the verified `author.username`, compare `updated_at` across all pages,
and require binding to the completed current request/head before accepting a score.

The Greptile bot username on GitLab may differ from GitHub's `greptile-apps[bot]` — check the first Greptile comment on the MR to identify the exact username.

## Fetch unresolved discussions (inline comments)

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
```

Read all pages. Resolution fields belong to `notes[]`, not the discussion object.

Filter for unresolved inline diff comments from Greptile:
```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100" | \
  jq -s 'add | [.[] | select(any(.notes[]; .resolvable == true and .resolved == false and .type == "DiffNote" and .author.username == "GREPTILE_BOT_USERNAME"))]'
```

Each discussion has:
- `id` — use this for resolution
- `notes[]` — inspect all note bodies, resolution flags and follow-up replies
- `notes[].position.new_path` — file path for inline notes

## Resolve a discussion

```bash
glab api --method PUT \
  "projects/:fullpath/merge_requests/<MR_IID>/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

GitLab has no batch resolution — issue one PUT per discussion.
First reply with the published fix and successful exact-head validation, and
ensure no follow-up question or new finding remains outstanding.
