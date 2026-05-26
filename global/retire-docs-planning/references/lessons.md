# Lessons

- 2026-05-22: Verify install guidance against both `Cargo.toml` and `git tag --list | sort` before replacing version or tag snippets; planning docs often describe the target state, not the publishable state.
- 2026-05-22: Move durable rules into stable topic pages close to where readers need them, and delete phase sequencing, branch naming, and model-routing instructions instead of paraphrasing them.
- 2026-05-22: For mdBook repos that commit generated output, rebuild `docs/book` after removing source planning pages and search both `docs/src` and `docs/book` for stale phase/planning text.
- 2026-05-22: If `mdbook` is missing on PATH, check the repo's Nix dev environment before stopping; many docs repos provide the required builder there even when the host shell does not.
- 2026-05-22: If stable docs already claim a planning tree was retired, treat any reintroduced `docs/planning` content as suspect and re-verify the live install or release surface from workflows, manifests, and tags before preserving anything.
- 2026-05-22: Before retiring a plan that may still contain active work, run a dedicated progress review and keep unfinished or blocked items in planning until they are either completed or consolidated into a replacement plan.
- 2026-05-22: When a user explicitly defers deleting old plan files, still fold durable guidance into stable docs and limit stale-reference cleanup to navigation/text that the user put in scope.
- 2026-05-22: If a future roadmap appears under `docs/src/planning` during a final retirement check, move or classify it outside active planning instead of deleting it, then re-run the exact directory assertion.
- 2026-05-24: When retiring one completed plan from a mixed planning tree, keep incomplete sibling plans published and verify stale-reference searches are scoped so retained plans do not mask deleted-plan leftovers.
- 2026-05-24: If the named obsolete plan directory is already absent, verify it is neither tracked nor referenced from published navigation, then update the replacement plan's README to state the retirement instead of running a no-op deletion.
- 2026-05-24: When stable docs exist in both README and mdBook, preserve retired plan guidance in the mdBook too; README-only preservation is not enough if the plan was published from `docs/src/SUMMARY.md`.
- 2026-05-25: When a published plan is only partially complete because external workflow evidence failed, remove it from reader navigation and fold verified durable guidance into stable docs, but keep the plan files for the unresolved follow-up.
- 2026-05-25: When planning files live outside the published docs tree, still run progress review before deletion; completed-but-superseded plans can be removed, while partial cross-repo plans should stay unlinked with stale sibling references cleaned up.
- 2026-05-25: If the user explicitly objects to retained unlinked planning files, delete the execution scaffolding after verifying stable docs and source artifacts already cover the durable behavior; report any stale plan claims instead of preserving them.
- 2026-05-25: When a mixed planning tree includes partial fleet work, removing `SUMMARY.md` exposure can be the correct retirement boundary; keep the source plans for unresolved evidence while stable docs carry shipped behavior.
- 2026-05-25: Before deleting a whole published planning tree, search stable docs for stale snippets copied from the plans; fix those snippets first so generated docs do not preserve old execution paths.
