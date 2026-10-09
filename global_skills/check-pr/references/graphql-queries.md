# GraphQL Queries Reference

Use `GH_HOST`, `PR_TARGET_REPO` and `PR_NUMBER` captured from the verified upstream
PR URL. Export `GH_HOST` for `gh pr` and substitute only that target owner/repo and
number into GraphQL placeholders; never infer them from a fork checkout.

Useful GitHub GraphQL queries for working with PR review threads.

## Fetch unresolved review threads (with pagination)

```graphql
query($cursor: String) {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          isResolved
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              databaseId
              body
              path
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
```

Pass `-f cursor=ENDCURSOR` on subsequent requests if `hasNextPage` is `true`.

Thread pagination does not paginate comments. For every thread whose comments
connection has `hasNextPage == true`, use its ID and comment `endCursor`:

```bash
gh api --hostname "$GH_HOST" graphql -f threadId=THREAD_ID -f commentCursor=ENDCURSOR -f query='
query($threadId: ID!, $commentCursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $commentCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { databaseId body path author { login } createdAt }
      }
    }
  }
}'
```

Repeat with that connection's next `endCursor` until all replies have been read.
Inspect objections and source-bound dispositions before resolving any thread.

## Resolve a single review thread

```graphql
mutation {
  resolveReviewThread(input: {threadId: "THREAD_ID"}) {
    thread { isResolved }
  }
}
```

## Batch-resolve multiple threads

Use GraphQL aliases to resolve several threads in one request:

```graphql
mutation {
  t1: resolveReviewThread(input: {threadId: "THREAD_ID_1"}) {
    thread { isResolved }
  }
  t2: resolveReviewThread(input: {threadId: "THREAD_ID_2"}) {
    thread { isResolved }
  }
  t3: resolveReviewThread(input: {threadId: "THREAD_ID_3"}) {
    thread { isResolved }
  }
}
```

## Fetch PR details (REST)

```bash
gh pr view --repo "$PR_TARGET_REPO" "$PR_NUMBER" --json title,body,state,reviews,comments,headRefName,statusCheckRollup
```

## Fetch inline review comments (REST)

```bash
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/comments?per_page=100"
```

## Fetch general PR comments edited in place (REST)

General PR comments are issue comments. Greptile may update one summary comment repeatedly, so select by `updated_at` instead of `created_at`:

First retain `GREPTILE_BOT_LOGIN` and `GREPTILE_BOT_ID` from trusted configured
app/installation identity, not from any arbitrary commenter. Match both exactly;
missing identity blocks acceptance. Timestamp orders already-authenticated evidence
and never proves current-request binding. Use the same exact author checks for
reviews/inline comments; validate request/revision attribution separately. A
missing matching summary is not a clean review.

```bash
: "${GREPTILE_BOT_LOGIN:?Missing verified review bot login}"
: "${GREPTILE_BOT_ID:?Missing verified review bot actor ID}"
gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/issues/$PR_NUMBER/comments?per_page=100" \
  | jq -se --arg bot "$GREPTILE_BOT_LOGIN" --argjson bot_id "$GREPTILE_BOT_ID" 'add
    | map(select(.user.login == $bot and .user.id == $bot_id))
    | sort_by(.updated_at)
    | last
    | select(. != null)
    | {author: .user.login, updated_at, body}'
```
