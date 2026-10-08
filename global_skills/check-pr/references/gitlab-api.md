# GitLab API Reference

Useful GitLab REST API calls for working with merge request discussions, using `glab api`.

`glab api` automatically resolves `:fullpath` to the URL-encoded project path from the local git remote.

## Fetch MR details

```bash
glab mr view <MR_IID> --output json
```

Key fields (compared to GitHub equivalents):
- `iid` — internal MR number (use this, not `id`)
- `source_branch` — equivalent to GitHub's `headRefName`
- `sha` — HEAD commit SHA, equivalent to GitHub's `headRefOid`
- `description` — equivalent to GitHub's `body`

## Fetch all discussions (inline + general comments)

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100"
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
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/discussions?per_page=100" | \
  jq -s 'add | [.[] | select(any(.notes[]; .resolvable == true and .resolved == false and .type == "DiffNote"))]'
```

## Resolve a single discussion

```bash
glab api --method PUT \
  "projects/:fullpath/merge_requests/<MR_IID>/discussions/<DISCUSSION_ID>" \
  --field resolved=true
```

There is no batch resolution in GitLab — issue one PUT per discussion. First read
all its notes, reply with the published fix and successful exact-head validation,
and ensure no follow-up remains outstanding.

## Fetch pipeline status for an MR

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/pipelines?per_page=100"
```

Pipeline statuses: `running`, `pending`, `success`, `failed`, `canceled`, `skipped`.
Select the applicable pipeline at the captured MR `sha`; missing/pending pipelines
do not qualify and older successful pipelines are not a fallback.

## Fetch jobs for a specific pipeline

```bash
glab api --paginate "projects/:fullpath/pipelines/<PIPELINE_ID>/jobs?per_page=100"
```

Each job has `name`, `status`, `stage`, and `web_url`.

## Fetch MR notes (general comments and bot reviews)

```bash
glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/notes?per_page=100"
```

Filter by `author.username` to find Greptile bot comments. The exact bot username depends on the Greptile installation — check the first Greptile comment to identify it.
Compare `updated_at` across every page, including older notes edited in place.

## Post a comment on an MR

```bash
glab mr note <MR_IID> --message "your message here"
```

Or via API:

```bash
glab api --method POST \
  "projects/:fullpath/merge_requests/<MR_IID>/notes" \
  --field body="your message here"
```
