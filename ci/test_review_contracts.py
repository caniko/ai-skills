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
assert "name: greptile-qualification-skills-${{ env.CANDIDATE_HEAD }}" in workflow
assert 'trust: "qualification-only", consumable: false' in workflow
for field in ('event: $event', 'ref: $ref', 'refProtected:', 'sourceRepository: $sourceRepository', 'base: $base'):
    assert field in workflow
assert '**not installation**' in (ROOT / 'README.md').read_text()
for source in (check_pr, loop):
    for endpoint in ("comments", "reviews"):
        assert f'gh api --hostname "$GH_HOST" --paginate "repos/$PR_TARGET_REPO/pulls/$PR_NUMBER/{endpoint}?per_page=100"' in source
assert "p4 describe -S <CL_NUMBER>" in check_pr
assert "p4 diff2" not in check_pr
assert "p4 review" not in check_pr
for source in (check_pr, loop):
    assert 'p4 changes -s shelved' in source
assert "at most 20 attempts" in check_pr and "assert_mr_revision" in check_pr
assert "isResolved == false" in loop and "not** thread-resolution state" in loop
assert '["repo-pages"] = new {\n    role = "reference"' in manifest
for skill in ("gitlab-pages", "forgejo-pages"):
    assert f'["{skill}"] = new {{\n    dependencies = List("repo-pages")' in manifest
    assert f'/{skill}/.skillnet/deps/repo-pages/SKILL.md' in workflow
assert 'repos/$PR_TARGET_REPO/check-runs/$CHECK_RUN_ID' in loop
assert 'projects/$PIPELINE_PROJECT_ID/jobs/$JOB_ID' in loop
assert "jq -r '.head_sha'" in loop and ".commit.id == $sha" in loop
assert "Do not guess the run by" in loop and "Retried jobs have distinct IDs" in loop
assert "npm i -g greptile" not in cli and "| sh" not in cli
assert "trusted checksum or signature" in cli
assert 'greptile review --branch "$REVIEW_BASE" --json' in cli
assert 'greptile review --branch "$REVIEW_BASE" --agent' in cli
assert "withheld/excluded" in cli and "coverage as unknown/incomplete" in cli
assert "explicitly authorizes transmitting each named path" in cli
assert "branches: [main, trunk, maintenance/greptile-skills]" in workflow
for source in (check_pr, loop):
    assert source.index("git rev-parse --is-inside-work-tree") < source.index("p4 where")
    assert 'p4 -ztag -Mj info' in source
    assert '$P4USER' not in source and '$P4CLIENT' not in source
    assert 'Bash(jq:*)' in source and 'Requires jq' in source
    for tool in ('canix repo review', 'canix repo merge', 'canix-toolbelt repo review', 'canix-toolbelt repo merge'):
        assert f'Bash({tool}:*)' in source
    assert 'git push\n' not in source
    for line in source.splitlines():
        if 'gh pr ' in line and not line.lstrip().startswith('from `'):
            assert '--repo "$PR_TARGET_REPO"' in line, line
        if line.lstrip().startswith('gh api ') or '$(gh api ' in line:
            assert '--hostname "$GH_HOST"' in line, line
        if 'glab api ' in line:
            assert '--hostname "$GITLAB_HOST"' in line, line
    assert "comments(first: 100)" in source and "comments(first: 1)" not in source
    assert "commentCursor" in source and "pageInfo { hasNextPage endCursor }" in source
    assert 'glab api --hostname "$GITLAB_HOST" --paginate "projects/$MR_PROJECT_ID/merge_requests/$MR_IID/notes?per_page=100"' in source
    assert ':fullpath' not in source
    assert 'glab mr view --repo "$MR_TARGET_REPO"' in source
    assert "refuse a dirty baseline" in source
assert check_pr.index("reviewThreads(first: 100") < check_pr.index("### 4. Analyze")
assert "Resolved threads are historical" in check_pr
assert check_pr.index('git switch --detach "$HEAD_SHA"') < check_pr.index('### 4. Analyze')
assert loop.index('LOCAL_HEAD=$(git rev-parse HEAD)') < loop.index('#### A. Trigger')
assert 'No initial push or re-shelve' in loop
for reference in gitlab_refs:
    assert ':fullpath' not in reference
    assert 'glab mr view <MR_IID> --repo "$MR_TARGET_REPO"' in reference
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
assert 'post-resolution review' in loop and 'disposition watermark' in loop
assert '["canix-cli"] = new {\n    dependencies = List("canix-structure-reference")' in manifest
assert '["canix-structure-reference"] = new {\n    role = "reference"' in manifest
for skill in ('canix-cli', 'canix-structure-reference', 'multi-host-agent-orchestration'):
    assert (ROOT / f'global_skills/{skill}/SKILL.md').is_file()
registry_reference = (ROOT / 'global_skills/canix-cli/references/secrets-and-registry.md').read_text()
assert '`.skillnet/deps/canix-structure-reference/SKILL.md`' in registry_reference
assert '**canix-cli package root**' in registry_reference
assert '../.skillnet/' not in registry_reference
for skill in ("check-pr", "greploop"):
    reference = (ROOT / f"global_skills/{skill}/references/graphql-queries.md").read_text()
    assert "comments(first: 3)" not in reference
    assert "comments(first: 100, after: $commentCursor)" in reference
    assert "pageInfo { hasNextPage endCursor }" in reference
    assert "threadId=THREAD_ID" in reference
    assert 'test("greptile"' not in reference

# Execute each documented trigger with ready/draft/unknown state; the mock only
# supplies platform metadata and records the requested message (no network).
for cli_name in ("gh", "glab"):
    marker = "DRAFT=$(gh" if cli_name == "gh" else "DRAFT=$(glab api"
    snippet = marker + loop.split("```bash\n" + marker, 1)[1].split("```", 1)[0]
    snippet = snippet.replace("<PR_NUMBER>", "1").replace("<MR_IID>", "1")
    for state in (True, False, None):
        payload = json.dumps({"isDraft": state}) if cli_name == "gh" else json.dumps({"draft": state})
        mock = f'''{cli_name}() {{
  case "$*" in
    'pr view '*|'api --hostname gitlab.example projects/101/merge_requests/1') printf '%s\\n' '{payload}' ;;
    'pr comment '*|'api --hostname gitlab.example --method POST projects/101/merge_requests/1/notes -f body='*) printf '%s\\n' "$*" ;;
    *) return 99 ;;
  esac
}}
'''
        result = subprocess.run(["bash", "-c", "set -o pipefail\nGH_HOST=github.com\nGITLAB_HOST=gitlab.example\nPR_TARGET_REPO=upstream/repo\nPR_NUMBER=1\nMR_PROJECT_ID=101\nMR_IID=1\n" + mock + snippet], capture_output=True, text=True, timeout=5)
        if state is None:
            assert result.returncode != 0 and "@greptileai" not in result.stdout
        else:
            expected = "@greptileai review this draft" if state else "@greptileai review"
            assert result.returncode == 0 and result.stdout.rstrip().endswith(expected), result
            if cli_name == "gh":
                assert 'pr comment --repo upstream/repo 1 --body ' in result.stdout, result
trigger_reference = (ROOT / "global_skills/greploop/references/gitlab-api.md").read_text()
assert "step A's draft-aware trigger" in trigger_reference
assert 'glab mr note <MR_IID> --message "@greptileai review"' not in trigger_reference
exit_conditions = loop.split("#### C. Check exit conditions", 1)[1].split("#### D.", 1)[0]
assert "Before a successful exit, perform step F" in exit_conditions
assert "independent current-revision CI requirements are satisfied" in exit_conditions
assert "headRefOid,baseRefOid" in loop and '"$BASE_SHA"' in loop
assert "immediately before each GitHub reply/resolution" in loop
assert "configured gate set is confirmed empty" in check_pr
assert "An empty status response alone never establishes N/A" in check_pr
reply_style = (ROOT / "global_skills/pr-review-reply-style/SKILL.md").read_text()
assert ".skillnet/deps/write-human-style/SKILL.md" in reply_style
assert "/check-pr/.skillnet/deps/pr-review-reply-style/.skillnet/deps/write-human-style/SKILL.md" in workflow

# Exercise the actual CLI coverage guard without running a reviewer or mutating git.
guard = "WORKTREE_STATUS=" + cli.split("```bash\nWORKTREE_STATUS=", 1)[1].split("```", 1)[0]
assert cli.index("WORKTREE_STATUS=") < cli.index('greptile review --branch "$REVIEW_BASE" --json')
for status in ("", " M tracked.md", "M  staged.md", "?? new.md"):
    mock = f"git() {{ printf '%s\\n' '{status}'; }}\n"
    result = subprocess.run(["bash", "-c", mock + guard], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == (not status), (status, result.stderr)

# Run the actual documented polling snippets with terminal API responses only;
# no network, credentials, sleeping, or repository mutations are involved.
for marker, cli_name, head_command, response, statuses in (
    ("CHECK_RUN_ID", "gh", "pr view", {"head_sha": "candidate", "status": "completed"},
     {"conclusion": ("success", "failure", "cancelled", "timed_out", "skipped")}),
):
    snippet = loop.split(f"```bash\n{marker}=", 1)[1].split("```", 1)[0]
    snippet = f"{marker}=" + snippet
    snippet = snippet.replace("<CURRENT_REVIEW_CHECK_RUN_ID>", "1").replace("<CURRENT_REVIEW_JOB_ID>", "1")
    snippet = snippet.replace("<PR_NUMBER>", "1").replace("<MR_IID>", "1")
    for field, values in statuses.items():
        for value in values:
            payload = json.dumps({**response, field: value})
            head_payload = json.dumps({"headRefOid": "candidate", "baseRefOid": "base"}) if cli_name == "gh" else json.dumps({"sha": "candidate"})
            mock = f'''{cli_name}() {{
  case "$*" in
    '{head_command}'*) printf '%s\\n' '{head_payload}' ;;
    'api '*) printf '%s\\n' '{payload}' ;;
    *) return 99 ;;
  esac
}}
HEAD_SHA=candidate
BASE_SHA=base
'''
            result = subprocess.run(["bash", "-c", mock + snippet], capture_output=True, text=True, timeout=5)
            assert (result.returncode == 0) == (value == "success"), (value, result.stdout, result.stderr)

# A successful head-only check cannot validate a changed PR comparison.
snippet = "CHECK_RUN_ID=" + loop.split("```bash\nCHECK_RUN_ID=", 1)[1].split("```", 1)[0]
snippet = snippet.replace("<CURRENT_REVIEW_CHECK_RUN_ID>", "1").replace("<PR_NUMBER>", "1")
for live_head, live_base in (("moved-head", "base"), ("candidate", "moved-base")):
    current = json.dumps({"headRefOid": live_head, "baseRefOid": live_base})
    check = json.dumps({"head_sha": "candidate", "status": "completed", "conclusion": "success"})
    mock = f'''gh() {{
  case "$*" in
    'pr view '*) printf '%s\\n' '{current}' ;;
    'api '*) printf '%s\\n' '{check}' ;;
    *) return 99 ;;
  esac
}}
HEAD_SHA=candidate
BASE_SHA=base
'''
    result = subprocess.run(["bash", "-c", mock + snippet], capture_output=True, text=True, timeout=5)
    assert result.returncode != 0 and "head/base moved" in result.stderr, result

# Exercise the shared GitLab identity/input proof and real polling snippet. Fork
# pipelines belong to project 202; MR/target APIs belong to project 101.
reference = gitlab_refs[0]
helpers = "# MR identity helpers" + reference.split("```bash\n# MR identity helpers", 1)[1].split("```", 1)[0]
binding = "# Bind selected pipeline" + reference.split("```bash\n# Bind selected pipeline", 1)[1].split("```", 1)[0]
poll = "JOB_ID=" + loop.split("```bash\nJOB_ID=", 1)[1].split("```", 1)[0]
poll = poll.replace("<CURRENT_REVIEW_JOB_ID>", "1")
for source in (check_pr, loop, *gitlab_refs):
    assert "sha == HEAD_SHA" not in source
    assert "projects/$PIPELINE_PROJECT_ID" in source or "through that owner" in source


def gitlab_fixture(status="success", sha="merged", parents=("target", "candidate")):
    mr = {"iid": 1, "source_project_id": 202, "target_project_id": 101,
          "source_branch": "feature", "target_branch": "trunk", "sha": "candidate",
          "diff_refs": {"base_sha": "base", "start_sha": "target", "head_sha": "candidate"}}
    payloads = {
        "MR_DATA": mr, "TARGET_DATA": {"commit": {"id": "target"}},
        "LIST_DATA": [{"id": 7, "project_id": 202, "sha": sha}],
        "PIPELINE_DATA": {"id": 7, "project_id": 202, "sha": sha, "source": "merge_request_event"},
        "COMMIT_DATA": {"id": sha, "parent_ids": list(parents)},
        "JOB_DATA": {"commit": {"id": sha}, "pipeline": {"id": 7, "project_id": 202}, "status": status},
    }
    setup = "\n".join(f"{key}='{json.dumps(value)}'" for key, value in payloads.items())
    return setup + f'''
glab() {{
  case "$*" in
    'api --hostname gitlab.example --paginate projects/101/merge_requests/1/pipelines?per_page=100') printf '%s\\n' "$LIST_DATA" ;;
    'api --hostname gitlab.example projects/101/merge_requests/1') printf '%s\\n' "$MR_DATA" ;;
    'api --hostname gitlab.example projects/101/repository/branches/trunk') printf '%s\\n' "$TARGET_DATA" ;;
    'api --hostname gitlab.example projects/202/pipelines/7') printf '%s\\n' "$PIPELINE_DATA" ;;
    'api --hostname gitlab.example projects/202/repository/commits/'*) printf '%s\\n' "$COMMIT_DATA" ;;
    'api --hostname gitlab.example projects/202/jobs/1') printf '%s\\n' "$JOB_DATA" ;;
    *) return 99 ;;
  esac
}}
MR_PROJECT_ID=101
MR_IID=1
GITLAB_HOST=gitlab.example
PIPELINE_ID=7
PIPELINE_PROJECT_ID=202
PIPELINE_SHA={sha}
HEAD_SHA=candidate
TARGET_SHA=target
{helpers}
MR_REVISION=$(mr_revision) || exit 90
'''


for status in ("success", "failed", "canceled", "skipped"):
    result = subprocess.run(["bash", "-c", gitlab_fixture(status) + binding + poll], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == (status == "success"), (status, result.stderr)
for sha, parents, success in (
    ("candidate", (), True), ("merged", ("target", "candidate"), True),
    ("merged", ("old-target", "candidate"), False),
    ("merged", ("target", "old-source"), False),
):
    result = subprocess.run(["bash", "-c", gitlab_fixture(sha=sha, parents=parents) + binding], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == success, (sha, parents, result.stderr)
for mutation in (
    'TARGET_DATA=\'{"commit":{"id":"advanced-target"}}\'',
    'MR_DATA=$(echo "$MR_DATA" | jq \'.sha = "new-source" | .diff_refs.head_sha = "new-source"\')',
    'MR_DATA=$(echo "$MR_DATA" | jq \'.diff_refs.start_sha = "new-diff"\')',
    'LIST_DATA=\'[]\'',
    'PIPELINE_DATA=$(echo "$PIPELINE_DATA" | jq \'.project_id = 999\')',
    'JOB_DATA=$(echo "$JOB_DATA" | jq \'.pipeline.id = 999\')',
    'JOB_DATA=$(echo "$JOB_DATA" | jq \'.pipeline.project_id = 999\')',
):
    result = subprocess.run(["bash", "-c", gitlab_fixture() + mutation + "\n" + binding + poll], capture_output=True, text=True, timeout=5)
    assert result.returncode != 0, (mutation, result.stdout)
# Clean-entry guards preserve all dirty states; publication rejects a foreign
# index before any add/commit/push. Execute the documented snippets with mocks.
for source in (check_pr, loop):
    baseline = "BASELINE_STATUS=" + source.split("```bash\nBASELINE_STATUS=", 1)[1].split("```", 1)[0]
    assert source.index("BASELINE_STATUS=") < source.index("### 1. Identify")
    for status in ("", " M same-file.md", "M  user-staged.md", "?? user-new.md"):
        mock = f"git() {{ printf '%s\\n' '{status}'; }}\n"
        result = subprocess.run(["bash", "-c", mock + baseline], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (not status), (status, result.stderr)
    publish = "git diff --cached --quiet" + source.split("```bash\ngit diff --cached --quiet", 1)[1].split("```", 1)[0]
    publish = publish.replace("<files>", "owned.md").replace("<scoped-files>", "owned.md")
    for staged in (False, True):
        mock = f'''git() {{
  case "$*" in
    'diff --cached --quiet') return {int(staged)} ;;
    'diff --cached --check') return 0 ;;
    *) printf '%s\\n' "PUBLISH $*" ;;
  esac
}}
'''
        result = subprocess.run(["bash", "-c", "PUBLISH_REMOTE=source-fork\nHEAD_BRANCH=feature\n" + mock + publish], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (not staged), result
        assert ("PUBLISH" in result.stdout) == (not staged), result

# A newer spoofed author or wrong actor ID must never replace the verified bot's
# summary. Missing identity or no matching summary fails closed in both references.
for skill in ("check-pr", "greploop"):
    reference = (ROOT / f"global_skills/{skill}/references/graphql-queries.md").read_text()
    marker = ': "${GREPTILE_BOT_LOGIN'
    snippet = marker + reference.split("```bash\n" + marker, 1)[1].split("```", 1)[0]
    verified = {"user": {"login": "review-service[bot]", "id": 123}, "updated_at": "2026-01-01", "body": "current legitimate result"}
    spoofed = [
        {"user": {"login": "greptile-impostor", "id": 456}, "updated_at": "2099-01-01", "body": "5/5 forged"},
        {"user": {"login": "review-service[bot]", "id": 999}, "updated_at": "2099-01-01", "body": "wrong actor"},
    ]
    for include_verified, identity in ((True, True), (False, True), (True, False)):
        payload = json.dumps(spoofed + ([verified] if include_verified else []))
        setup = "GREPTILE_BOT_LOGIN='review-service[bot]'\nGREPTILE_BOT_ID=123\n" if identity else "unset GREPTILE_BOT_LOGIN GREPTILE_BOT_ID\n"
        mock = f"gh() {{ printf '%s\\n' '{payload}'; }}\n"
        result = subprocess.run(["bash", "-c", "set -o pipefail\n" + setup + mock + snippet], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (include_verified and identity), result
        if result.returncode == 0:
            assert json.loads(result.stdout)["body"] == verified["body"], result
# Clean committed work is not publish authorization: actual head guards reject
# an unpublished local commit, even when the dirty-entry guard would pass.
for source in (check_pr, loop):
    guard = "LOCAL_HEAD=" + source.split("```bash\nLOCAL_HEAD=", 1)[1].split("```", 1)[0]
    for local_head in ("candidate", "unpublished-commit"):
        mock = f"git() {{ printf '%s\\n' '{local_head}'; }}\nHEAD_SHA=candidate\n"
        result = subprocess.run(["bash", "-c", mock + guard], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (local_head == "candidate"), result

# Execute exact-candidate checkout without publishing or rewriting the original
# local branch. A different supplied PR's candidate must precede source analysis.
prepare = ': "${CANDIDATE_REMOTE' + check_pr.split('```bash\n: "${CANDIDATE_REMOTE', 1)[1].split("```", 1)[0]
for checked_out in ("candidate", "wrong-head"):
    mock = f'''git() {{
  case "$*" in
    'fetch --no-tags source-fork candidate'|'switch --detach candidate') return 0 ;;
    'rev-parse HEAD') printf '%s\\n' '{checked_out}' ;;
    *) return 99 ;;
  esac
}}
CANDIDATE_REMOTE=source-fork
HEAD_SHA=candidate
'''
    result = subprocess.run(["bash", "-c", mock + prepare], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == (checked_out == "candidate"), result

# P4CONFIG-only identities are discovered through Perforce, not exported vars.
for source in (check_pr, loop):
    identity = "P4_IDENTITY=" + source.split("P4_IDENTITY=", 1)[1].split('p4 changes -s pending -u "$REVIEW_USER" -c "$REVIEW_CLIENT"', 1)[0]
    identity += 'p4 changes -s pending -u "$REVIEW_USER" -c "$REVIEW_CLIENT"\n'
    for client in ("mapped-client", "", "*unknown*"):
        payload = json.dumps({"userName": "configured-user", "clientName": client})
        mock = f'''unset P4USER P4CLIENT
p4() {{
  case "$*" in
    '-ztag -Mj info') printf '%s\\n' '{payload}' ;;
    'changes -s shelved -u configured-user -c mapped-client'|'changes -s pending -u configured-user -c mapped-client') printf '%s\\n' "$*" ;;
    *) return 99 ;;
  esac
}}
'''
        result = subprocess.run(["bash", "-c", mock + identity], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (client == "mapped-client"), result
        assert ('changes -s' in result.stdout) == (client == "mapped-client"), result

# Verify the edited file really belongs to the reviewed numbered CL; empty
# opened output, default CL and another numbered CL all block publication.
association = "OPENED_FILE=" + check_pr.split("OPENED_FILE=", 1)[1].split("# make changes", 1)[0]
association = association.replace("<CL_NUMBER>", "123").replace("<file>", "owned.txt")
assert 'p4 unshelve -s <CL_NUMBER> -c <CL_NUMBER>' in check_pr
assert 'p4 edit -c <CL_NUMBER> <file>' in check_pr and 'p4 edit -c <CL_NUMBER> <file>' in loop
for change in ("123", "default", "456", None):
    payload = json.dumps({"change": change}) if change is not None else ""
    mock = f"p4() {{ printf '%s\\n' '{payload}'; }}\n"
    result = subprocess.run(["bash", "-c", "set -o pipefail\n" + mock + association], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == (change == "123"), result
# Platform detection fails explicitly without the selected remote, and an explicit
# platform selection avoids touching origin in a valid Git worktree.
for source in (check_pr, loop):
    detection = 'if [ "$(git rev-parse' + source.split('```bash\nif [ "$(git rev-parse', 1)[1].split('```', 1)[0]
    for platform, remote, success in (("", "missing", False), ("", "gitlab", True), ("", "github", True), ("", "unknown", False), ("gitlab", "missing", True), ("github", "missing", True)):
        mock = f'''VCS='{platform}'
PLATFORM_REMOTE=selected-remote
git() {{
  case "$*" in
    'rev-parse --is-inside-work-tree') echo true ;;
    'remote get-url selected-remote')
      if [ '{remote}' = missing ]; then return 1; fi
      echo 'https://{remote}.example/owner/repo.git' ;;
    *) return 99 ;;
  esac
}}
p4() {{ return 99; }}
'''
        result = subprocess.run(["bash", "-c", mock + detection + '\nprintf "%s" "$VCS"'], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == success, result
        if success:
            assert result.stdout.strip() == (platform or remote), result

# Use the real configured GitLab service account, never its placeholder name.
reference = gitlab_refs[1]
marker = ': "${GREPTILE_BOT_USERNAME'
filter_snippet = marker + reference.split('```bash\n' + marker, 1)[1].split('```', 1)[0]
for identity in (True, False):
    payload = json.dumps([{"id": "real", "notes": [{"resolvable": True, "resolved": False, "type": "DiffNote", "author": {"username": "configured-reviewer", "id": 123}}]}, {"id": "spoof", "notes": [{"resolvable": True, "resolved": False, "type": "DiffNote", "author": {"username": "configured-reviewer", "id": 456}}]}])
    setup = 'GREPTILE_BOT_USERNAME=configured-reviewer\nGREPTILE_BOT_USER_ID=123\n' if identity else 'unset GREPTILE_BOT_USERNAME GREPTILE_BOT_USER_ID\n'
    mock = f"GITLAB_HOST=gitlab.example\nMR_PROJECT_ID=101\nMR_IID=1\nglab() {{ [ \"$*\" = 'api --hostname gitlab.example --paginate projects/101/merge_requests/1/discussions?per_page=100' ] || return 99; printf '%s\\n' '{payload}'; }}\n"
    result = subprocess.run(["bash", "-c", 'set -o pipefail\n' + setup + mock + filter_snippet], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == identity, result
    if identity:
        assert [item['id'] for item in json.loads(result.stdout)] == ['real'], result
# URL-derived host binding must override a different checkout's default instance.
for source in (check_pr, loop, gitlab_refs[0]):
    for line in source.splitlines():
        if 'glab api ' in line:
            assert '--hostname "$GITLAB_HOST"' in line, line
    marker = ': "${MR_TARGET_REPO'
    setup = marker + source.split('```bash\n' + marker, 1)[1].split('```', 1)[0]
    setup = setup.replace('<MR_IID>', '1')
    for repo, success in (('https://gitlab.example/target/repo', True), ('owner/repo', False)):
        mock = '''glab() {
  [ "$GITLAB_HOST" = gitlab.example ] || return 99
  case "$*" in 'mr view '*) printf '%s\\n' '{"target_project_id":101,"iid":1,"sha":"candidate","source_branch":"feature"}' ;; *) return 99 ;; esac
}
'''
        result = subprocess.run(['bash', '-c', f'GITLAB_HOST=wrong.example\nMR_TARGET_REPO={repo}\n' + mock + setup], capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == success, result

# Use a freshly fetched immutable base; remote target movement invalidates review.
marker = ': "${REVIEW_TARGET_REMOTE'
setup = marker + cli.split('```bash\n' + marker, 1)[1].split('```', 1)[0]
for live_base, success in (('fresh-base', True), ('advanced-base', False)):
    mock = f'''git() {{
  case "$*" in
    'fetch --no-tags target refs/heads/trunk') return 0 ;;
    'rev-parse --verify HEAD') echo candidate ;;
    'rev-parse --verify FETCH_HEAD^{{commit}}') echo fresh-base ;;
    'ls-remote --exit-code target refs/heads/trunk') printf '%s\\trefs/heads/trunk\\n' '{live_base}' ;;
    'status --porcelain --untracked-files=all') return 0 ;;
    *) return 99 ;;
  esac
}}
REVIEW_TARGET_REMOTE=target
REVIEW_TARGET_BRANCH=trunk
'''
    result = subprocess.run(['bash', '-c', mock + setup + '\n[ "$REVIEW_BASE" = fresh-base ]'], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == success, result
assert cli.count('assert_review_revision || exit 1') == 3
print("review source contracts passed")
