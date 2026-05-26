---
name: multi-phase-plan
description: Break a non-trivial refactor, migration, or cleanup into a set of standalone markdown phase documents, each self-contained enough that a fresh Codex/Claude session can pick it up cold. Each phase declares its recommended GPT-5.x model and reasoning effort by consulting the `gpt-plan-routing` skill. Triggers on "break this into phases", "create a multi-phase plan", "split into markdown files", "one phase per session", "phase doc set", or whenever the user asks for plan decomposition with per-step model recommendations.
---

# Multi-phase plan document set

Use this skill when the user wants a non-trivial body of work decomposed into a set of standalone phase markdown files, each independently consumable by a fresh agent session. The skill enforces a uniform shape so phases are diffable, parallelisable where possible, and don't entangle context.

Pair this with the **`gpt-plan-routing`** skill to assign each phase its appropriate GPT-5.x model + `reasoning_effort` level. Don't guess at "max" vs "medium" — run the routing matrix for each phase.

## Modes

- **`plan`** — decompose work into standalone phase files, route each phase, and record calibration data when sampling rules fire. It accepts two input shapes: free-text task descriptions, or dossier-aware planning from a Planner Handoff dossier supplied explicitly or auto-detected in `docs/planning/`.
- **`verify`** — audit an executed phase set against its acceptance criteria and record the verification outcome.
- **`calibrate`** — walk calibration data through skillnet and prepare a changelog block for this file's footer.

## When to use

- The user describes a body of work that exceeds one session-worth of focus (typically 2+ days of effort, 3+ logical sub-goals, or interactions across multiple repos / crates / subsystems).
- The user says "break this into phases", "split into multiple files", "one markdown per phase", or names something as "a refactor" / "a migration" / "a cleanup".
- The plan has natural sequencing constraints (some steps must precede others) AND opportunities for parallel execution.
- The work will likely be handed off to multiple Codex/Claude sessions, possibly running concurrently, possibly across different model tiers.

Don't use this for:
- Single-session tasks. One file, no skill needed.
- Plans that aren't going to be handed off (just sketch in chat).
- Strategy / discussion / brainstorming — those want prose, not phase files.

## Output shape

A directory under `docs/src/planning/<plan-name>/` containing:

- A required top-level `README.md` that acts as the plan-set orchestrator index.
- One file per phase: `NN-<slug>.md` where `NN` is two-digit ordinal (`01`, `02`, …) and `<slug>` is `kebab-case`.
- Each file is fully standalone — no "see the overview doc first" preamble, no shared context that lives only in chat.
- An index entry in `docs/src/SUMMARY.md` if the project uses mdBook, so the README and phase files are surfaced.

The `docs/src/planning/<plan-name>/` location is the convention; adjust per project layout. If the project doesn't use mdBook, drop the SUMMARY hookup.

### Required top-level `README.md`

The top-level `README.md` is the coordination surface for the plan set. It must not hide content needed to execute an individual phase — every phase file remains standalone — but it must let the user understand and dispatch the plan without opening every phase first.

The README must include:

- The flavour-specific recommended model callout for plan-set orchestration.
- Scope and current state summary.
- A phase table with links to every phase file, direct dependencies, blocking status, and safe parallelism.
- A **Parallelism Layer** section with execution waves from start to plan exhaustion. Each wave must list which phases can run at the same time, why they can overlap, what unlocks next, and which phases must serialize because of shared files or validation gates.
- Whole-set acceptance criteria.
- Any global constraints that apply to every phase.
- Links to coverage, source evidence, or retirement reports when the plan consolidates prior work.

Do not make README optional just because phase files are standalone. The README is how the user coordinates the plan; the phase files are how agents execute the work.

## Required structure per phase file

Every phase file must contain, in this order:

```markdown
# Phase <letter or number> — <Imperative title>

> **Recommended Codex model: GPT 5.5 <tier>**
>
> <One paragraph rationale: complexity, role in plan, what would
> happen if a smaller model ran this. Reference the gpt-plan-routing
> matrix's axes (task complexity × role-in-plan) implicitly — don't
> name the matrix in the file, just produce a recommendation that
> matches what the matrix would yield.>

## Working tree

<Explicit cwd for the agent running this phase. If it's the same
repo as the parent project, say so. If it's an external repo
(steampipe, fragpipe, etc.), give the absolute path.>

## Goal

<One paragraph stating exactly what success looks like. Outcome-
focused, not action-focused.>

## Why this matters now

<Why-this-phase-exists context: the originating symptom (paste the
relevant log line / warning / failure mode), the cost of deferring,
and how it fits into the broader plan.>

## Out of scope

<Bullet list. Be explicit about what NOT to do — phase docs that
miss this section invite scope creep.>

## Plan

<Numbered steps. Each step is concrete enough to execute without
asking clarifying questions. Include commands where applicable.>

## Acceptance criteria

<Checkbox list of objectively verifiable conditions. "Tests pass" is
not enough; name the specific test target. "Build is clean" is not
enough; name the warning count expected.>

## Files likely touched

<Per-file list with paths. If multiple repos are involved, group by
repo with explicit working tree.>

## Pitfalls

<Failure modes the agent is likely to hit. For each: symptom, cause,
recovery. Pre-mortem the work so the agent isn't reactively
patching.>

## Reference

<Links: to the originating diagnosis (chat transcript, issue,
investigation doc), to related phases in this set, to upstream docs.>
```

For **high-risk** phases (anything routed to `GPT 5.5 max`), add:

```markdown
## Risk profile

<Enumerated list of what can go wrong. Sets the mental model the
agent enters with.>

## Strategy

<For multi-step changes that span multiple commits: lay out the
commit ladder explicitly with revert costs.>

## Rollback drill

<Concrete commands to practice rollback before the destructive
commit. Include a time SLA.>

## Failure modes and recoveries

<F1, F2, …  Each with symptom / cause / recovery, written so the
agent has a runbook.>
```

## Mode: `plan`

Triggered when the user asks to break work into phases, create a multi-phase plan, split work into standalone markdown files, or otherwise requests plan decomposition with per-phase model routing.

### Dossier-aware planning

Dossier-aware planning is an input variant of `plan`, not a fourth top-level mode. The output is still the same phase doc set, the same README shape, the same routing pass, and the same calibration sidecar. This keeps callers simple: an orchestrator can invoke the normal flavour skill in `plan` mode with `--from-dossier <path>` when a dossier exists, or with only a free-text task description when it does not.

This base skill consumes the dossier's `Recommended planner flavour`; it does
not define the downstream-flavour default. For orchestrated prep/plan
dispatch, see [`plan-and-verify`](../plan-and-verify/SKILL.md) "Default
flavour for prep/plan dispatch".

Use dossier-aware planning when the invocation includes `--from-dossier <path>`, when the first positional argument after `plan` is a path to a Planner Handoff dossier, or when a dossier is auto-detectable for the target plan name. Detection order:

1. Explicit dossier path from `--from-dossier <path>` or the plan invocation argument.
2. `docs/planning/<plan-name>-research.md` adjacent to the target plan-set directory.
3. `docs/planning/<plan-name>-findings.md`. This is a downshift case and should not normally happen; if found, stop and warn that planning directly from a findings note is suspicious unless the user explicitly confirms that file is the intended handoff dossier.

Parse only the dossier's `## Planner Handoff` section, using the `plan-handoff` contract. The required fields are required inputs. If any required H3 field is absent, empty, structurally wrong for its field type, or still contains placeholder text, stop and report:

- the missing or invalid field name;
- why that field is required for planning;
- the upstream producer to rerun, usually `long-horizon-research`, `consolidate-plan-sets`, or `plan-progress-review`;
- the exact producer workflow or command the user should rerun when known, otherwise the producer skill invocation that created the dossier;
- a validation command such as `rg -n "^## Planner Handoff|^### (Dossier path|Current-state summary|Recommended planner flavour|Work that should become phases|Known blockers|Acceptance evidence to preserve)" <dossier-path>` plus a manual check that each required heading has non-placeholder content.

Do not fabricate, infer, or silently substitute missing required dossier fields from the user's free-text prompt.

Field reads and mapping:

| Planner Handoff field | Plan-mode use |
|---|---|
| `Dossier path` | Provenance for the plan README and phase references. If it conflicts with the actual file consumed, preserve the actual consumed path in the chat reply and treat the mismatch as a dossier defect to report before writing phase files. |
| `Current-state summary` | Seeds workflow step 1, "Take inventory". Do not rediscover from scratch; verify only enough local context to avoid writing stale or impossible phase steps. |
| `Recommended planner flavour` | Must match the currently invoked flavour (`multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed`). If it names a different flavour, stop and ask the user whether to switch flavour or intentionally override the dossier recommendation. |
| `Work that should become phases` | Starting candidate phase list. Respect the proposed slice boundaries, but merge or split when the standard phase rules require it, and state the reason in the README or chat reply. |
| `Known blockers` | Hard constraints that remain blockers in the plan set. Do not plan around them, downgrade them to `not-started`, or turn them into implementation phases unless the user supplies the missing upstream artifact or decision. |
| `Acceptance evidence to preserve` | Seeds the whole-set acceptance criteria in the plan README and any phase-level evidence checks that protect those claims. |
| `Candidate phase boundaries` *(optional)* | Starting dependency table and execution-wave sketch. Refine it through the normal dependency and parallelism workflow. |
| `Risks and constraints` *(optional)* | Feed into README global constraints and per-phase Pitfalls sections. |
| `Open decisions for the user` *(optional)* | Surface before writing phase files. Do not silently choose among material open decisions. |

Precedence rules:

- Dossier fields override user free-text on factual claims: current state, blockers, acceptance evidence, provenance, and producer-observed constraints.
- User free-text overrides the dossier on intent reframing: the user may add scope, drop scope, or explicitly mark the dossier stale or superseded. If the prompt and dossier describe different goals rather than additive scope, stop and ask before writing files.
- Optional fields guide planning when present and are ignored when absent. Do not invent optional fields to make the dossier look complete.

Calibration and heuristic interaction:

- The heuristics catalog still evaluates the output plan directory, not the dossier.
- The sidecar still lives at `<plan-dir>/.calibration.json`; do not create a sidecar next to the dossier and do not extend the sidecar schema.
- After `skillnet calibration init <plan-dir>` creates the sidecar, tag dossier-aware plans as `input:from-dossier` using `skillnet calibration tag <plan-id> input=from-dossier` so `calibrate` mode can compare dossier-aware plans to free-text plans. If the tagging command is unavailable, report that tagging was skipped; the plan deliverable is still valid.

### Workflow

1. **Take inventory.** List every concrete action the work entails. Group related actions into candidate phases. Each phase must satisfy the per-phase shape rules:
   - **One outcome.** The Goal section names a single user-observable outcome; you can write "this phase succeeds when ..." in one sentence.
   - **One rollback boundary.** The phase's changes can be reverted as a unit without leaving the repo in a half-state. If a phase crosses two natural revert boundaries, it's two phases.
   - **One session window.** A fresh session can plausibly complete the phase in one sitting at the recommended tier. A phase that needs to be bumped from `medium` to `high` to fit is a routing signal, not a "make the phase bigger" signal.

   Phase count is whatever falls out. There is no upper cap. Large efforts trigger additional README sections via the heuristics catalog below.

2. **Identify dependencies.** Draw an explicit dependency table:

   ```
   Phase | Depends on  | Touches files       | Can parallel with
   A     | —           | crate/foo/          | B, C
   B     | —           | crate/bar/          | A, C
   C     | —           | vendor/baz/         | A, B
   D     | —           | repo/X/flake.nix    | A, B, C
   E     | D           | repo/X/flake.nix    | —
   ```

   Phases that touch disjoint files can run in parallel. Phases that touch the same file must serialise — flag this explicitly in each affected phase's "Working tree" or "Plan" section so the agent doesn't have to discover the conflict mid-execution.

3. **Build the README parallelism layer.** Convert the dependency table into execution waves:
   - Wave 0 contains phases that can start from the current tree.
   - Each later wave contains phases unlocked by prior wave acceptance.
   - If a phase can partly run early but must stop before overlapping files, say so explicitly.
   - Continue until the final wave says the plan is exhausted.

4. **Route each phase through `gpt-plan-routing`.** For each phase, evaluate:
   - **Task complexity**: trivial / moderate / complex / frontier.
   - **Role in plan**: leaf / sub-agent / orchestrator / top-level planner.

   Look up the routing matrix in the `gpt-plan-routing` skill. Note the recommended `model/effort` combination. Include the rationale in the phase file's `Recommended Codex model` callout block.

   See the model tiers there: `5.5 max` is for frontier complexity at top-level / orchestrator roles; `5.5 high` for complex orchestration or non-trivial design decisions; `5.5 medium` is the routine default for moderate complexity; `5.5 low` is for trivial mechanical work. Match the recommendation to the phase's complexity × role coordinates — don't inflate.

5. **Write the top-level `README.md`** with the required orchestration shape above. Its phase table and parallelism layer must match the phase files.

6. **Write each phase file** following the required structure above. Self-contained. Include the originating evidence (a log paste, a transcript excerpt, an issue reference) so the agent isn't guessing at why the phase exists.

7. **Wire into SUMMARY** if the project uses mdBook (`docs/src/SUMMARY.md`). Include the README and one line per phase under a "Plan: <plan-name>" section.

8. **Provide a routing summary** in the chat reply alongside the file creation:

   | Phase | File | Model | Tier rationale | Blocking? |
   |---|---|---|---|---|

   Plus a parallelism matrix showing which phases can run concurrently and which serialise.

9. **Record for calibration.** After the plan files are written:

   1. Run `skillnet calibration init <plan-dir>`. This bootstraps `<plan-dir>/.calibration.json` by parsing the README and phase files, evaluating the heuristics catalog, and evaluating the meta-heuristics.
   2. If `init`'s output indicates at least one meta-heuristic fired, printed as `meta_heuristics_fired: [...]`, run `skillnet calibration record <plan-dir>` to persist the plan to the calibration database.
   3. Surface the recording in the chat reply: `Recorded for calibration: <reason1, reason2>`. If no meta-heuristic fired, do not surface anything; the plan deliverable is unchanged.

   If `skillnet` is missing because there is no HM module and no `cargo install`, skip the recording silently and print a one-line install hint at the end of the chat reply: `(skillnet not installed — calibration recording skipped; see ai-skills' HM module to enable.)`. Calibration recording is a best-effort augment, not a blocker.

## Sequencing and parallelism guidance

Default each phase to "independent unless flagged". Explicit constraints belong in the phase doc, not in tribal knowledge.

| Constraint | How to communicate |
|---|---|
| File-level conflict (same file touched) | Note in both phases' "Plan" section: "<Phase X> must land first; pull/rebase before starting". |
| Logical dependency (later phase consumes earlier phase's output) | First sentence of the later phase's "Working tree" section names the prerequisite phase. |
| Repo-level conflict (both phases push to same repo's main branch) | Recommend sequential execution AND have the later phase note "pull steampipe/main before starting — see Phase D". |
| Verification gating (later phase needs earlier phase's smoke run to be green) | In the later phase's "Acceptance criteria" preamble, list the prerequisite phase's green run as a precondition. |

## Heuristics catalog

The plan's README and individual phase files gain extra sections when specific *triggers* fire. Trigger names, categories, current thresholds, and section metadata live canonically in skillnet: run `skillnet calibration heuristics list --format json`. This section documents what each category means and what kind of section each trigger contributes; it does not duplicate threshold values.

Run `skillnet calibration eval <plan-dir>` after writing a plan to see which triggers fire and what they add. `skillnet calibration init <plan-dir>` uses the same catalog when bootstrapping a sidecar.

### Coordination

Triggers in this category surface coordination cost between phases that share resources or cross repos.

- `shared-file-contention` — multiple phases touch the same file. Adds a "Shared-file lockstep" section to the README and cross-links each affected phase's Plan.
- `external-repo-phases` — any phase has a non-primary `Working tree`. Adds an "External repo coordination" section.
- `convergence-point` — a phase has many direct predecessors. The convergent phase gets a "Merge-readiness checklist".
- `ownership-boundary-spread` — phases span multiple maintainer domains. Adds a "PR sequencing & cross-owner coordination" section.

### Risk

Triggers in this category call out phases whose failure would invalidate downstream work or widen compatibility risk.

- `risk-concentration` — many `max` phases. README gets a "Risk-tier callout".
- `risk-late-in-plan` — a `max` phase in the final waves. README gets a "Late-risk warning".
- `infrastructure-spof` — a phase touches CI, build orchestration, flake files, lockfiles, or similar infrastructure and downstream phases depend on it. The phase is flagged "infra-SPOF"; downstream Pitfalls inherit a smoke-invalid note.
- `revendor-phase` — phase title or files indicate vendoring, dependency, or lockfile churn. Routing tier suggestion bumps up; the phase gets a "Compat surface" section.

### Plan Shape

Triggers in this category keep large or oddly shaped plans dispatchable.

- `long-serial-chain` — deep dependency chain. README gets a "Serial-chain recovery" section.
- `mid-plan-rerouting` — many phases. README mandates an "after wave N, re-run routing" checkpoint.
- `trivial-phase-swamp` — many low-tier phases relative to high. README gains a "Cleanup batch" appendix.
- `no-integrated-verification` — no closing verification phase. Warn; prompt adding one.

### Quality Lint

Quality lint triggers warn or block instead of adding a README section.

- `routing-tier-inversion` — leaf phase routes at least as high as its orchestrator. Require an inline justification.
- `mechanical-streak` — many `low` phases in a row. Suggest bundling.
- `hidden-prerequisite` — phase assumes state nothing earlier produces. Block; require an explicit dependency edge.

Current thresholds, including any per-tag-band overrides, are available via `skillnet calibration heuristics list --format json`. They evolve through the calibration loop; do not hardcode them in this skill body.

## When a plan gets recorded

A plan is written to the calibration dataset only when at least one *meta-heuristic* fires. The goal is to minimize selection bias: the dataset concentrates on plans where learning is possible, such as boundary cases, novel shapes, and verifier surprises.

Categories of meta-heuristic are implemented in skillnet; see `skillnet calibration meta-heuristics --help` for command usage and `skillnet/src/calibration/catalog/meta.rs` for the live list:

- **Threshold proximity.** A trigger's input value sits near its threshold; the boundary is where tuning matters most.
- **Trigger absence with risk shape.** No triggers fired, but the plan looks risky by other measures. Catches false negatives.
- **Novel shape signature.** The plan's overall shape has not appeared before; sparse-region sampling.
- **Routing tier outlier.** A phase routes unusually high or low for its complexity class.
- **Verify surprise** *(verify-time only).* The verifier reported a failure, emergency change, added phase, or structured surprise no trigger pre-empted.
- **Re-routing event** *(verify-time only).* A phase executed at a different tier than recommended.
- **High-stakes combo.** A `max` phase combined with external-repo work.
- **Uniform random.** A small per-plan probability, currently described by skillnet as the 7% anti-bias random sample; use skillnet as the live source if this value changes.

Each meta-heuristic that fires is recorded in the sidecar's `meta_heuristics_fired` array so calibration can later check whether each meta-heuristic itself produces signal.

## Sidecar `.calibration.json`

Every recorded plan carries a sidecar at `<plan-dir>/.calibration.json`. skillnet's `init`, `record`, and `verify` commands read and write it; the skill body never composes the JSON by hand.

Source-of-truth: `skillnet/src/calibration/sidecar.rs` (`schema_version = 1`). This sidecar `schema_version` is separate from the `schema_version` used by `skillnet calibration analyze --format json`.

Top-level shape; `worktype` is `null` or one of `refactor`, `migration`, `cleanup`, `feature`, `infra`, `docs`, `other`:

```json
{
  "schema_version": 1,
  "plan": {
    "id": "<uuid>",
    "name": "<slug>",
    "flavor": "codex|claude|mixed",
    "worktype": null,
    "created_at": 0,
    "phase_count": 0,
    "wave_count": 0,
    "max_chain_depth": 0,
    "repo_spread": 0,
    "routing_dist": { "low": 0, "medium": 0, "high": 0, "max": 0 },
    "shape_hash": "<blake3-hex>"
  },
  "triggers": [
    {
      "name": "...",
      "input_value": 0.0,
      "threshold": 0.0,
      "fired": false,
      "section_added": null
    }
  ],
  "phases": [
    {
      "ordinal": 1,
      "slug": "...",
      "routing_tier": "low|medium|high|max",
      "files": ["..."]
    }
  ],
  "meta_heuristics_fired": ["..."],
  "tags": { "key": "value" },
  "verify": null
}
```

When verification data exists, `verify` has this shape:

```json
{
  "verified_at": 0,
  "elapsed_seconds": null,
  "outcome": "shipped|partial|abandoned",
  "phase_outcomes": { "1": "passed|failed|skipped|abandoned" },
  "emergency_changes": null,
  "surprises": null
}
```

Run `skillnet calibration init <plan-dir>` to bootstrap; `skillnet calibration show <plan-id>` to inspect a recorded one.

## Tag conventions

skillnet applies **auto-tags** at `record` time from the sidecar's plan metadata:

- `flavor:<codex|claude|mixed>`
- `worktype:<refactor|migration|cleanup|feature|infra|docs|other>` when set
- `scope:<single-repo|multi-repo|cross-org>` from `repo_spread`
- `risk:<low|mixed|high>` from `routing_dist`
- `signal:<meta-heuristic-name>` once per firing meta-heuristic
- `outcome:<shipped|partial|abandoned>` updated by `verify`

**User tags** are free-form; key must match `^[a-z][a-z0-9_-]*$`. Add them with `skillnet calibration tag <plan-id> <key>=<value>`.

**Per-band analysis**: `skillnet calibration analyze --filter-tag <key>=<value>` slices the dataset; calibrate mode uses this to surface flavor- or worktype-specific skew.

## Verifier `surprises` field

The verifier's free-text `surprises` field accepts structured prefixes that feed calibration. Lines without a recognized prefix are preserved verbatim but ignored by the analyzer.

Recognized prefixes:

- `dead-weight: <trigger-name>: <note>` — the section added by `<trigger-name>` was useless on this plan; the analyzer treats it as a false positive.
- `missed-signal: <trigger-name>: <note>` — `<trigger-name>` would have added a useful section if its threshold were lower; the analyzer treats it as a false negative.

Full convention: `skillnet` mdBook page `docs/src/calibration/surprises.md`, surfaced as "Verifier surprises convention".

## What goes in the chat reply

After writing the files, the chat reply should include:

1. The directory location (`docs/src/planning/<plan-name>/`) with a count of files written, including the README.
2. The routing summary table (phase × model × blocking-status).
3. The README parallelism layer summary: execution waves and serialization points.
4. Any setup the user needs to run (e.g., `mdbook build`, `git add docs/src/SUMMARY.md`).
5. For dossier-aware invocations, the dossier path consumed, the Planner Handoff fields read, any dossier/free-text precedence decisions made, and any open decisions the user must resolve before phase execution.
6. A concrete next-step suggestion: "ready to start with phase A" or "phase A is the only blocker — others can fan out".

Don't recap the contents of each phase file in chat. The files are the artifact; the chat reply is the dispatch.

## Mode: `verify`

Triggered when the user asks to verify, audit, or close out a previously executed multi-phase plan set.

### Workflow

1. Read the plan README and every phase file in `<plan-dir>`.
2. Inspect the repository state and execution evidence that proves each phase acceptance criterion passed, failed, was skipped, or was abandoned.
3. Report the verify outcome in chat: `shipped`, `partial`, or `abandoned`, plus a per-phase pass/fail/skipped/abandoned map and any unresolved gaps.
4. Record any useful `surprises` notes. Use the structured prefixes documented in "Verifier `surprises` field" when applicable.
5. **Record verify outcome.**

   1. Read `<plan-dir>/.calibration.json` if it exists.
   2. Append a `verify` section to the sidecar with the outcome, per-phase pass/fail map, and `surprises` text. The `surprises` field should use the structured prefixes documented in "Verifier `surprises` field" when applicable:
      - For each section that turned out to be dead weight on this plan: `dead-weight: <trigger-name>: <one-line note>`.
      - For each failure mode no trigger pre-empted: write `missed-signal: <closest-trigger-name>: <one-line note>` if a known trigger would have caught it with a lower threshold; otherwise leave informational prose and consider proposing a new heuristic in the next calibrate-mode session.
   3. Run `skillnet calibration verify <plan-dir>`.
   4. If the sidecar does not exist because the plan was not recorded at plan time, but a verify-time meta-heuristic would fire (`skillnet calibration meta-heuristics <plan-dir> --sidecar /dev/null` returns either `verify-surprise` or `rerouting-event`), run `skillnet calibration init <plan-dir> --force` first, then proceed.

   CLI errors are reported and do not block the verify deliverable.

6. **Auto-retire on a clean verify.** A clean verify is one where outcome is `shipped`, every phase is `passed` (zero `failed`, zero `partial`, zero `abandoned`, zero unresolved gaps), and there are no `missed-signal:` surprises. On a clean verify, invoke [retire-docs-planning](../retire-docs-planning/SKILL.md) in `clean-shipped` mode scoped to `<plan-dir>`. The retirement is unconditional — **do not prompt, do not ask for confirmation, do not list "durable bits worth preserving" for user approval**. Migration criteria, removal steps, and validation steps live in `retire-docs-planning`; this skill delegates.

   On a non-clean verify (any phase not passed, any unresolved gap, any `missed-signal:` surprise), do **not** retire. Report what's missing and stop.

## Mode: `calibrate`

Triggered when the user says "calibrate", "tune the heuristics", "review calibration data", or invokes the skill with `calibrate` as the first word.

Calibrate mode does not write phase files. It walks the user through the calibration dataset and produces a changelog block to paste into this file's footer.

### Workflow

1. From the ai-skills repository root, shell out to:

   ```sh
   skillnet calibration walkthrough \
       --skill-md global/multi-phase-plan/SKILL.md \
       --interactive
   ```

   The orchestrator runs `analyze` -> interactive prompts per candidate proposal -> records `propose`/`decide` -> emits an `export-changelog` block scoped to changes since the most recent entry in this file's footer.

2. The user interacts with `walkthrough` directly; it handles the prompts. The skill agent's job is to surface what the user pasted next.

3. After `walkthrough` finishes, copy the markdown block between `──── Changelog block ────` and the closing `══` markers into the "Calibration changelog" footer at the bottom of this file. For each accepted proposal, also update the corresponding heuristic's threshold in the catalog section above. Phase 06's catalog is descriptive; the live threshold is the one in skillnet, and this footer is for human audit.

4. Calibrate mode does not auto-edit `SKILL.md`. The user pastes; the user is the editor; the user can reject a bad block before it ratchets.

### Non-interactive use

Scripted callers can run:

```sh
skillnet calibration walkthrough \
    --non-interactive --decisions decisions.json \
    --skill-md global/multi-phase-plan/SKILL.md
```

Decisions file format: see `skillnet calibration walkthrough --help` and the schema at <https://codeberg.org/caniko/skillnet/src/branch/main/docs/src/calibration/walkthrough.md>.

### Cadence

User-initiated; not scheduled. The min-N guard in `analyze` ensures running too early is a no-op. Suggested rhythm: after every ~10 verified plans, or when a recurring `dead-weight:` annotation suggests a trigger is over-firing.

## Anti-patterns to avoid

- **README content that phase files depend on.** The README is required for coordination, but each phase file must still be readable cold.
- **Cross-references between phase files for actual content.** Cross-references for *context* are fine ("Phase D must land first — see [04-…](./04-…)"). Cross-references that hide a step ("see Phase A for the build command") force the agent to read both files. Inline the step.
- **Conditional phases ("only do this if X").** If a phase's existence is conditional, write the decision criterion as its own initial step inside the phase, not as a wrapping "do we need this?" guard.
- **Generic acceptance criteria.** "Tests pass" / "builds cleanly" / "no regressions" are not acceptance criteria. Name specific test targets, warning counts, log-line presence/absence.
- **Routing every phase to `max`.** The `gpt-plan-routing` skill explicitly warns against this: it triples cost with diminishing returns. Use `low` and `medium` aggressively for mechanical phases; reserve `max` for genuinely frontier-complex work.
- **Pre-mortem section missing on high-risk phases.** If you've routed a phase to `max`, you owe the agent a failure-modes-and-recoveries section. Without it, the agent has to discover the failure modes the hard way.
- **Treating heuristic thresholds as immutable.** Use `dead-weight:` and `missed-signal:` prefixes when verifier surprises occur; the calibration loop is how thresholds get tuned.
- **Skipping the verifier `surprises` field.** Without annotations, the loop runs on shape data alone and converges slower.
- **Re-implementing what skillnet provides.** The skill body no longer evaluates heuristics in prose; call `skillnet calibration eval` or rely on `skillnet calibration init`, which uses the same catalog.
- **Fabricating dossier fields.** If a required Planner Handoff field is missing or invalid, stop and report the broken producer artifact. Do not infer it from the user's prompt; that defeats the contract.
- **Hand-editing the calibration changelog.** It is the audit trail; paste blocks from `skillnet calibration walkthrough` or `skillnet calibration export-changelog` only.
- **Editing thresholds in skillnet without going through `walkthrough`.** The accepted-proposal trail in `calibration_proposals` is provenance; bypassing it leaves no record of why a threshold moved.

## Example: the 5-phase pre-landing-cleanup set that this skill abstracts

A chessbender post-refactor cleanup with five phases routed across the GPT-5.5 tier:

| Phase | Slug | Model | Why |
|---|---|---|---|
| A | dice-partition-forget | `5.5 medium` | Diagnosis in hand, fix is 4 lines, but needs smoke-log interpretation to verify. |
| B | warning-cleanup | `5.5 low` | Three mechanical edits, no design content, no log reading. |
| C | webpki-deprecations | `5.5 high` | Mechanical edits *plus* a non-trivial path choice (patch vendor / re-vendor / bump). The design call needs context, not raw output volume. |
| D | crosvm-version-override | `5.5 medium` | External-repo edit + commit + push without supervision; needs judgement on intentional-vs-bug. |
| E | nixos-scripted-initrd | `5.5 max` | Boot-order, GPU readiness, parallel-VM race exposure. Mediocre work ships a subtle regression. Worth `max`. |

The pattern: route to the cheapest tier that holds the quality bar for *this specific phase's* complexity × role. Resist the urge to uniformly route to `max` "to be safe".

## Reference

- Model + effort selection: the **`gpt-plan-routing`** skill (consult its routing table and key heuristics).
- Planner Handoff dossier contract: **`plan-handoff`** (`global/plan-handoff/SKILL.md`).
- Clean verify plan retirement: **`retire-docs-planning`** (`global/retire-docs-planning/SKILL.md`).
- mdBook conventions for project docs: `docs/src/SUMMARY.md`.

## Calibration changelog

Threshold changes to the heuristics catalog above are recorded here. Each entry is produced by `skillnet calibration walkthrough` or `export-changelog` and pasted by the user during a `calibrate` mode session. The live thresholds are authoritative in skillnet (`heuristic_thresholds` table); this footer is the human-readable audit trail.

<!-- Newest first. Format produced by `skillnet calibration export-changelog`. -->

### 2026-05-24 — Calibration loop activated

- skillnet 0.4.0 consumed via HM module re-export.
- Initial heuristic thresholds: see `skillnet calibration heuristics list --format json` for live values.
- Database backend: Postgres (`postgres:///can?host=/run/postgresql` per this user's HM config; SQLite fallback documented).
- No threshold changes in this entry — genesis row only.
