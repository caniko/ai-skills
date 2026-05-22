# Lessons

- 2026-05-22: Verify install guidance against both `Cargo.toml` and `git tag --list | sort` before replacing version or tag snippets; planning docs often describe the target state, not the publishable state.
- 2026-05-22: Move durable rules into stable topic pages close to where readers need them, and delete phase sequencing, branch naming, and model-routing instructions instead of paraphrasing them.
- 2026-05-22: For mdBook repos that commit generated output, rebuild `docs/book` after removing source planning pages and search both `docs/src` and `docs/book` for stale phase/planning text.
- 2026-05-22: If `mdbook` is missing on PATH, check the repo's Nix dev environment before stopping; many docs repos provide the required builder there even when the host shell does not.
- 2026-05-22: If stable docs already claim a planning tree was retired, treat any reintroduced `docs/planning` content as suspect and re-verify the live install or release surface from workflows, manifests, and tags before preserving anything.
- 2026-05-22: Before retiring a plan that may still contain active work, run a dedicated progress review and keep unfinished or blocked items in planning until they are either completed or consolidated into a replacement plan.
- 2026-05-22: When a user explicitly defers deleting old plan files, still fold durable guidance into stable docs and limit stale-reference cleanup to navigation/text that the user put in scope.
