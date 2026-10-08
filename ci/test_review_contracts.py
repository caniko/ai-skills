"""Small source-contract regression check; hosted composition runs this too."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / "ci/skillnet-composition.yaml").read_text()
check_pr = (ROOT / "global_skills/check-pr/SKILL.md").read_text()
loop = (ROOT / "global_skills/greploop/SKILL.md").read_text()
cli = (ROOT / "global_skills/cli-review/SKILL.md").read_text()
manifest = (ROOT / "global_skills/Skillnet.pkl").read_text()

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
print("review source contracts passed")
