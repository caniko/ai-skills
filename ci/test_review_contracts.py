"""Small source-contract regression check; hosted composition runs this too."""

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / "ci/skillnet-composition.yaml").read_text()
check_pr = (ROOT / "global_skills/check-pr/SKILL.md").read_text()
loop = (ROOT / "global_skills/greploop/SKILL.md").read_text()
cli = (ROOT / "global_skills/cli-review/SKILL.md").read_text()
manifest = (ROOT / "global_skills/Skillnet.pkl").read_text()
gitlab_refs = [
    (ROOT / f"global_skills/{skill}/references/gitlab-api.md").read_text()
    for skill in ("check-pr", "greploop")
]

assert "CANDIDATE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
assert "ref: ${{ env.CANDIDATE_HEAD }}" in workflow
assert '--arg head "$(git rev-parse HEAD)"' in workflow
assert "name: greptile-consumer-skills-${{ env.CANDIDATE_HEAD }}" in workflow
for source in (check_pr, loop):
    for endpoint in ("comments", "reviews"):
        assert f'gh api --paginate "repos/{{owner}}/{{repo}}/pulls/<PR_NUMBER>/{endpoint}?per_page=100"' in source
assert "p4 describe -S <CL_NUMBER>" in check_pr
assert "p4 diff2" not in check_pr
assert "p4 review" not in check_pr
for source in (check_pr, loop):
    assert 'p4 changes -s shelved' in source
assert "at most 20 attempts" in check_pr and "sha == HEAD_SHA" in check_pr
assert "isResolved == false" in loop and "not** thread-resolution state" in loop
assert '["repo-pages"] = new {\n    role = "reference"' in manifest
for skill in ("gitlab-pages", "forgejo-pages"):
    assert f'["{skill}"] = new {{\n    dependencies = List("repo-pages")' in manifest
    assert f'/{skill}/.skillnet/deps/repo-pages/SKILL.md' in workflow
assert 'repos/{owner}/{repo}/check-runs/$CHECK_RUN_ID' in loop
assert 'projects/:fullpath/jobs/$JOB_ID' in loop
assert "jq -r '.head_sha'" in loop and "jq -r '.commit.id'" in loop
assert "Do not guess the run by" in loop and "Retried jobs have distinct IDs" in loop
assert "npm i -g greptile" not in cli and "| sh" not in cli
assert "trusted checksum or signature" in cli
assert "branches: [main, trunk, maintenance/greptile-skills]" in workflow
for source in (check_pr, loop):
    assert source.index("git rev-parse --is-inside-work-tree") < source.index("p4 where")
    assert "p4 info" not in source
    assert "comments(first: 100)" in source and "comments(first: 1)" not in source
    assert "commentCursor" in source and "pageInfo { hasNextPage endCursor }" in source
    assert 'glab api --paginate "projects/:fullpath/merge_requests/<MR_IID>/notes?per_page=100"' in source
for reference in gitlab_refs:
    assert "select(.resolved == false" not in reference
    assert "any(.notes[];" in reference and ".resolvable == true" in reference
    assert "jq -s 'add |" in reference
assert loop.index("#### E. Commit and push") < loop.index("#### F. Validate") < loop.index("#### G. Resolve")
assert check_pr.index("### 8. Validate") < check_pr.index("### 9. Resolve")
assert 'echo "Greptile check completed with: $CONCLUSION" >&2\n      exit 1' in loop
assert 'echo "Greptile job completed with: $JOB_STATUS" >&2\n    exit 1' in loop
assert "at most 60 attempts" in loop and "shelf identity" in loop
assert "**Perforce** — after successful shelf-bound validation" in loop
assert "If there are no scoped edits" in loop and "skip commit/push/re-shelve" in loop
assert "Then go back to steps **B/C**" in loop
assert "Then go back to step **A**" not in loop
assert "Reuse existing successful review/CI receipts" in loop
for skill in ("check-pr", "greploop"):
    reference = (ROOT / f"global_skills/{skill}/references/graphql-queries.md").read_text()
    assert "comments(first: 3)" not in reference
    assert "comments(first: 100, after: $commentCursor)" in reference
    assert "pageInfo { hasNextPage endCursor }" in reference
    assert "threadId=THREAD_ID" in reference

# Execute each documented trigger with ready/draft/unknown state; the mock only
# supplies platform metadata and records the requested message (no network).
for cli_name in ("gh", "glab"):
    marker = "DRAFT=$(" + cli_name
    snippet = marker + loop.split("```bash\n" + marker, 1)[1].split("```", 1)[0]
    snippet = snippet.replace("<PR_NUMBER>", "1").replace("<MR_IID>", "1")
    for state in (True, False, None):
        payload = json.dumps({"isDraft": state}) if cli_name == "gh" else json.dumps({"draft": state})
        mock = f'''{cli_name}() {{
  case "$*" in
    'pr view '*|'mr view '*) printf '%s\\n' '{payload}' ;;
    'pr comment '*|'mr note '*) printf '%s\\n' "$*" ;;
    *) return 99 ;;
  esac
}}
'''
        result = subprocess.run(["bash", "-c", "set -o pipefail\n" + mock + snippet], capture_output=True, text=True, timeout=5)
        if state is None:
            assert result.returncode != 0 and "@greptileai" not in result.stdout
        else:
            expected = "@greptileai review this draft" if state else "@greptileai review"
            assert result.returncode == 0 and result.stdout.rstrip().endswith(expected), result
trigger_reference = (ROOT / "global_skills/greploop/references/gitlab-api.md").read_text()
assert "step A's draft-aware trigger" in trigger_reference
assert 'glab mr note <MR_IID> --message "@greptileai review"' not in trigger_reference

# Run the actual documented polling snippets with terminal API responses only;
# no network, credentials, sleeping, or repository mutations are involved.
for marker, cli_name, head_command, response, statuses in (
    ("CHECK_RUN_ID", "gh", "pr view", {"head_sha": "candidate", "status": "completed"},
     {"conclusion": ("success", "failure", "cancelled", "timed_out", "skipped")}),
    ("JOB_ID", "glab", "mr view", {"commit": {"id": "candidate"}},
     {"status": ("success", "failed", "canceled", "skipped")}),
):
    snippet = loop.split(f"```bash\n{marker}=", 1)[1].split("```", 1)[0]
    snippet = f"{marker}=" + snippet
    snippet = snippet.replace("<CURRENT_REVIEW_CHECK_RUN_ID>", "1").replace("<CURRENT_REVIEW_JOB_ID>", "1")
    snippet = snippet.replace("<PR_NUMBER>", "1").replace("<MR_IID>", "1")
    for field, values in statuses.items():
        for value in values:
            payload = json.dumps({**response, field: value})
            head_payload = "candidate" if cli_name == "gh" else json.dumps({"sha": "candidate"})
            mock = f'''{cli_name}() {{
  case "$*" in
    '{head_command}'*) printf '%s\\n' '{head_payload}' ;;
    'api '*) printf '%s\\n' '{payload}' ;;
    *) return 99 ;;
  esac
}}
HEAD_SHA=candidate
'''
            result = subprocess.run(["bash", "-c", mock + snippet], capture_output=True, text=True, timeout=5)
            assert (result.returncode == 0) == (value == "success"), (value, result.stdout, result.stderr)
print("review source contracts passed")
