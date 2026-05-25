# Planning-Skill Coupling Paradigm — Research Dossier

## Goal And Trigger

The user wants the three upstream planning skills — [long-horizon-research](../../global/long-horizon-research/SKILL.md), [consolidate-plan-sets](../../global/consolidate-plan-sets/SKILL.md), and the [multi-phase-plan](../../global/multi-phase-plan/SKILL.md) family (`-codex`, `-claude`, `-mixed`) — coupled into one explicit paradigm. They observe (correctly) that long-horizon-research and consolidate-plan-sets are both "tightly related" to multi-phase-plan: each produces input that a multi-phase-plan flavour later consumes, but there is no canonical entrypoint, no shared handoff contract, and no documented decision tree for which upstream to invoke when.

Trigger phrasing: *"skills including long horizon research and consolidate plan sets are tightly related to multi-plan skills. Let's create a skill paradigm that couples them together."*

## Current Reality

The planning-skill family in [`global/`](../../global/) today contains nine skills with overlapping responsibilities and informal coupling:

| Skill | Role | Direct dependencies (declared) |
|---|---|---|
| [long-horizon-research](../../global/long-horizon-research/SKILL.md) | Pre-plan research dossier producer | calls "plan-progress-review behavior" inline; names downstream `multi-phase-plan-*` skill in handoff |
| [consolidate-plan-sets](../../global/consolidate-plan-sets/SKILL.md) | Collapse N stale plan sets into one | depends on `plan-progress-review` + one `multi-phase-plan-*` flavour; refuses to write without flavour explicitly named |
| [plan-progress-review](../../global/plan-progress-review/SKILL.md) | Edit-free audit of existing plan claims | feeds `retire-docs-planning`, `consolidate-plan-sets`, `multi-phase-plan` verify |
| [retire-docs-planning](../../global/retire-docs-planning/SKILL.md) | Remove planning surface, preserve durable knowledge | uses `plan-progress-review` |
| [multi-phase-plan](../../global/multi-phase-plan/SKILL.md) | Base shape spec; `plan` / `verify` / `calibrate` modes; calibration sidecar | consults `gpt-plan-routing`; loaded by all flavours |
| [multi-phase-plan-codex](../../global/multi-phase-plan-codex/SKILL.md) | Codex/GPT-5.x flavour | loads base + `multi-phase-dispatch`; routes via `gpt-plan-routing` |
| [multi-phase-plan-claude](../../global/multi-phase-plan-claude/SKILL.md) | Claude flavour | loads base + `multi-phase-dispatch`; routes via `claude-plan-routing` |
| [multi-phase-plan-mixed](../../global/multi-phase-plan-mixed/SKILL.md) | Cross-provider flavour | loads base + `multi-phase-dispatch` + both routing skills |
| [multi-phase-dispatch](../../global/multi-phase-dispatch/SKILL.md) | Sub-layer model reference | loaded by every flavour |
| [plan-and-verify](../../global/plan-and-verify/SKILL.md) | Two-mode orchestrator (`plan` → flavour, `verify` → flavour-agnostic audit) | dispatches to flavour skills |

The graph is real and works, but the coupling is implicit. Seven concrete gaps:

1. **No shared upstream entrypoint.** `long-horizon-research` and `consolidate-plan-sets` are both pre-plan producers, but the user picks one based on memory, not based on a documented router. There is no single trigger that says "for this kind of ask, prep this way first."
2. **Handoff is prose, not contract.** [long-horizon-research/SKILL.md:149-166](../../global/long-horizon-research/SKILL.md) defines a `## Planner Handoff` section, but it is narrative — not a schema the downstream flavour can parse. [consolidate-plan-sets/SKILL.md:99-105](../../global/consolidate-plan-sets/SKILL.md) emits a "coverage or retirement report" with no fixed field set. The flavour skills have no `from-dossier` input mode; they re-elicit context from the user's prompt every time.
3. **Provider selection is decided three times.** `long-horizon-research` defaults to `multi-phase-plan-codex` ([SKILL.md:27](../../global/long-horizon-research/SKILL.md)). `consolidate-plan-sets` refuses to run without an explicit flavour ([SKILL.md:15](../../global/consolidate-plan-sets/SKILL.md)). `plan-and-verify` picks by user wording, defaulting to codex ([SKILL.md:20-22](../../global/plan-and-verify/SKILL.md)). Three rules, three defaults, three failure modes.
4. **`plan-and-verify` is upstream-blind.** It is the canonical orchestrator for `plan` → `verify` but knows nothing about a possible `prep` phase. Users who want research-first or consolidation-first must invoke those skills manually then hand the result to a flavour, bypassing `plan-and-verify`.
5. **Audit logic is duplicated.** `long-horizon-research` step 3 calls "plan-progress-review behavior" inline. `consolidate-plan-sets` step 1 explicitly runs `plan-progress-review`. `retire-docs-planning` step 1 also runs `plan-progress-review`. Three call sites, no shared input/output schema. Each consumer reads the audit differently.
6. **Calibration scope is silent on prep.** [multi-phase-plan/SKILL.md:278-339](../../global/multi-phase-plan/SKILL.md) defines the `.calibration.json` sidecar on the *plan directory*. There is no sidecar for prep artifacts, and no documented rule about whether prep effort feeds calibration. (Likely correct — prep is not what calibration tunes — but the silence is itself a coupling gap.)
7. **`long-horizon-research` conflates two jobs.** It is a *generic* "produce an evidence-backed research dossier" skill that is also useful standalone (audits, investigations, pre-design work that never becomes a multi-phase plan), AND it carries multi-phase-specific obligations (steps 1, 7, the Planner Handoff section). The two responsibilities tug against each other — the standalone use case is weighed down by planner-handoff prose, and the planner-handoff use case can't be hardened without making the standalone use case awkward. The family pattern that solves this already exists: [multi-phase-plan](../../global/multi-phase-plan/SKILL.md) (base) + [multi-phase-plan-{codex,claude,mixed}](../../global/multi-phase-plan-codex/SKILL.md) (flavours that load the base). The research skill should split the same way: a generic reference skill plus a multi-phase-tuned wrapper.

## Evidence Inventory

| Artifact | What it proves |
|---|---|
| [global/long-horizon-research/SKILL.md:155-166](../../global/long-horizon-research/SKILL.md) | Planner Handoff is prose, names downstream skill, but emits no machine-parseable contract |
| [global/consolidate-plan-sets/SKILL.md:10-16](../../global/consolidate-plan-sets/SKILL.md) | Consolidate explicitly depends on `plan-progress-review` + a flavour; refuses without flavour |
| [global/plan-and-verify/SKILL.md:10-34](../../global/plan-and-verify/SKILL.md) | Plan-and-verify is two-mode; the "plan" mode delegates straight to a flavour skill — no prep awareness |
| [global/multi-phase-plan/SKILL.md:13-17](../../global/multi-phase-plan/SKILL.md) | Three formal modes: `plan` / `verify` / `calibrate`. No `from-dossier` input mode |
| [global/multi-phase-plan-codex/SKILL.md:56-65](../../global/multi-phase-plan-codex/SKILL.md) | Flavour `plan` workflow re-elicits inventory; no contract that says "if a dossier exists, consume it" |
| [global/plan-progress-review/SKILL.md:68-72](../../global/plan-progress-review/SKILL.md) | Explicit Handoff Rules section names three consumers; no shared schema across them |
| [global/multi-phase-dispatch/SKILL.md:1-21](../../global/multi-phase-dispatch/SKILL.md) | Successful precedent for a shared-reference skill that the flavours load — the same pattern can host the handoff contract |
| [global/retire-docs-planning/SKILL.md:12-13](../../global/retire-docs-planning/SKILL.md) | Fourth caller of `plan-progress-review`; reinforces that the audit→producer pattern is repeated |
| `ls ~/canix/Projects/ai-skills/docs/planning/` shows sibling research dossiers (`mirror-canonical-store-research.md`, `reconciliation-anomalies-research.md`) | This repo already uses `docs/planning/<slug>-research.md` as the dossier location |

## Existing Plan Status

No prior plan set exists for this coupling work — no `docs/planning/skill-paradigm-*` directory, no related phase docs found via `ls ~/canix/Projects/ai-skills/docs/planning/`. The sibling research dossiers (`mirror-canonical-store-research.md`, `reconciliation-anomalies-research.md`) are unrelated; they target the canonical-store/reconciliation mirror, not the planning-skill family.

This dossier is the first artifact in this coupling effort; no audit-carryover is required.

## Work That Should Survive Into The Long-Term Plan

The future plan must deliver, in order of dependency:

1. **A shared "Planner Handoff" contract.** A single markdown schema with required fields (current-state summary, work-to-phase list, blockers, acceptance evidence, recommended flavour) that every upstream producer emits literally and every downstream consumer (`multi-phase-plan` base + each flavour) reads literally.
2. **Split `long-horizon-research` into base + planning wrapper.** The base stays close to the current skill body but is stripped of multi-phase-specific obligations (downstream-planner naming, `Planner Handoff` section, "Do not run the multi-phase planning skill from this skill" anti-pattern). It becomes a general-purpose "produce an evidence-backed research dossier" reference skill, useful standalone. A new sibling skill — proposed name **`plan-research`** — loads the base, adds the planning-tuned obligations (Planner Handoff schema emission, downstream flavour selection, candidate phase boundaries, planner brief), and becomes the canonical pre-plan research skill that the coupling paradigm wires up.
3. **A canonical decision tree** for "do we research first? consolidate first? skip prep?" — written into the orchestrator (`plan-and-verify` promoted to three-mode — see Open Decisions). The `prep` dispatch targets `plan-research` (not the base `long-horizon-research`) and `consolidate-plan-sets`.
4. **A `from-dossier` input mode on `multi-phase-plan` (base)** so flavours inherit it. Defines: what fields the flavour reads, what overrides the user's free-text prompt, what to do when the dossier is incomplete.
5. **Targeted patches to each upstream producer** to emit the shared schema: `plan-research` (new — emits by design), `consolidate-plan-sets`, `plan-progress-review` in producer role.
6. **Targeted patches to each flavour** (`-codex`, `-claude`, `-mixed`) to recognize and consume the `from-dossier` mode — likely a delegation note pointing at the base skill, not a full rewrite.
7. **A single-source provider-defaulting rule** that all upstream skills + the orchestrator point at, so codex-as-default is asserted once.
8. **Doctrine doc** in `docs/planning/` or `docs/src/` explaining the coupled workflow end-to-end with a worked example.
9. **A verify pass** that the new prep mode + the existing `verify` mode + calibration sidecar still compose cleanly (no regression in `plan-and-verify verify`).

Durable constraints to preserve:

- The user runs phases themselves — no flavour skill emits run scripts ([multi-phase-plan-codex/SKILL.md:62](../../global/multi-phase-plan-codex/SKILL.md), [multi-phase-plan-claude/SKILL.md:86](../../global/multi-phase-plan-claude/SKILL.md), [multi-phase-dispatch/SKILL.md:20](../../global/multi-phase-dispatch/SKILL.md)). The coupling paradigm must not introduce dispatch scripts.
- Calibration sidecar lives on the plan directory, not on prep artifacts ([multi-phase-plan/SKILL.md:278-339](../../global/multi-phase-plan/SKILL.md)).
- Each upstream skill keeps its own narrative output (research dossier, consolidated plan set, progress report). The shared handoff contract is an *additional* section, not a replacement of each skill's deliverable.
- `plan-and-verify verify` must remain flavour-agnostic — verify reads `Acceptance criteria` checklists from phase docs and runs them against repo state ([plan-and-verify/SKILL.md:90-199](../../global/plan-and-verify/SKILL.md)). Coupling work must not change the verify contract.
- Auto-retirement on clean verify is unconditional ([multi-phase-plan/SKILL.md:399-407](../../global/multi-phase-plan/SKILL.md)) — do not introduce prompts.

## Blockers And Missing Artifacts

None block dossier writing. Two items are **open decisions** rather than missing artifacts (see Open Decisions section), and one is a known unknown:

- **Skillnet calibration coupling.** Whether prep-mode emits a calibration sidecar is unknown without checking what skillnet's CLI accepts for non-plan-dir inputs. Producer: `skillnet calibration init --help`. Validation: confirm whether `init` accepts arbitrary directories or only plan dirs. This is not a foundational blocker — the future plan can scope calibration to plan-dirs only and revisit if needed.

## Risks And Constraints

| Risk | Severity | Why |
|---|---|---|
| Promoting `plan-and-verify` to three-mode breaks invocation compatibility for users with muscle memory on `plan-and-verify plan <task>` | medium | `plan` as the unprefixed default must keep working. A `prep` mode token added in front cannot change the `plan` default route |
| Over-constraining upstream skills with a strict schema | medium | Research, consolidation, and progress-review each emphasize different evidence shapes. The shared contract must be the **subset** they all already implicitly produce, not a maximalist schema that forces every skill to fabricate unused fields |
| Three provider-default rules diverging further | medium | The single-source rule must be defined in one skill (likely the base `multi-phase-plan`) and *referenced* (not copied) by the upstream and orchestrator skills. Copies will drift |
| Adding a `from-dossier` mode to flavours doubles the test surface | low-medium | Each flavour has `plan` / `verify` / `calibrate`. Adding `from-dossier` as a fourth mode (or as a `plan` variant) needs explicit anti-pattern coverage so users don't conflate "prep written" with "phases dispatched" |
| Doctrine doc bit-rot | low | A standalone end-to-end doctrine doc in `docs/planning/` will rot fast. Better: embed the decision tree in the orchestrator skill's SKILL.md so it lives with the code |
| Sub-skill name confusion | low | If we add a `plan-prep` skill, the catalog gains a name that overlaps with `plan-and-verify prep`. Picking one design (Option B vs Option A in Open Decisions) closes this |

Cross-cutting: the planning-skill family is shipped via the skillnet HM module; edits land in [`global/`](../../global/) and are mirrored to `~/.claude/skills/` on rebuild. No special migration sequencing — single-repo, single-runtime.

## Candidate Phase Boundaries

Below is a candidate decomposition. Final phase count and routing belong to the downstream multi-phase planner; these are dependency-aware slices, not commitments.

| Phase | Slug | Depends on | Touches | Can parallel with | Notes |
|---|---|---|---|---|---|
| P1 | define-handoff-contract | — | new reference skill `plan-handoff` under [`global/`](../../global/) (mirrors the `multi-phase-dispatch` shared-reference pattern) | — | Wave 0 blocker. Defines required fields, optional fields, naming, location, and the consumer-side parse rules |
| P2 | generalize-long-horizon-research | — | [`global/long-horizon-research/SKILL.md`](../../global/long-horizon-research/SKILL.md) | P1 | Strip multi-phase-specific obligations (downstream-planner naming in step 1, Planner Handoff section in step 6, handoff step 7, the anti-pattern about not running the multi-phase skill). Rewrite as a general-purpose reference skill: "produce an evidence-backed research dossier"; the right-size gate stays; the dossier shape stays but loses the Planner Handoff section. Description updates to drop multi-phase references |
| P3 | create-plan-research-wrapper | P1, P2 | new skill `global/plan-research/SKILL.md` plus a `global/multi-plan-research` symlink → `plan-research` as a discovery alias | P4, P5, P6 | Loads `long-horizon-research` (base) per its new generic shape and `plan-handoff`. Adds the planning obligations: downstream flavour selection rule (with codex default), required Planner Handoff schema emission, candidate phase boundaries section, planner brief at the end. Acts as the canonical pre-plan research skill. The `multi-plan-research` alias lets users find the skill by searching for "multi" without memorizing the canonical short name; both names resolve to the same SKILL.md. The skill description must mention the alias inline so skill-search matches it |
| P4 | patch-consolidate-plan-sets | P1 | [`global/consolidate-plan-sets/SKILL.md`](../../global/consolidate-plan-sets/SKILL.md) | P3, P5, P6 | Add Planner Handoff section to the consolidated `README.md` requirement (step 3) |
| P5 | patch-plan-progress-review-producer-mode | P1 | [`global/plan-progress-review/SKILL.md`](../../global/plan-progress-review/SKILL.md) | P3, P4, P6 | Add a "Handoff emission" step for when called as a producer (not just an evidence supplier) |
| P6 | add-from-dossier-mode-to-base | P1 | [`global/multi-phase-plan/SKILL.md`](../../global/multi-phase-plan/SKILL.md) | P3, P4, P5 | Add fourth invocation mode (or `plan --from-dossier <path>` variant). Defines field reads, overrides, fallback when incomplete |
| P7 | flavour-delegation-notes | P6 | [`global/multi-phase-plan-codex/SKILL.md`](../../global/multi-phase-plan-codex/SKILL.md), [`global/multi-phase-plan-claude/SKILL.md`](../../global/multi-phase-plan-claude/SKILL.md), [`global/multi-phase-plan-mixed/SKILL.md`](../../global/multi-phase-plan-mixed/SKILL.md) | — | Likely just "see base skill's from-dossier mode; this flavour inherits it" — three small edits, can be sub-layered |
| P8 | promote-orchestrator | P3, P4, P5, P6, P7 | [`global/plan-and-verify/SKILL.md`](../../global/plan-and-verify/SKILL.md) | — | Promote to three-mode (`prep | plan | verify`). `prep` dispatches to `plan-research` or `consolidate-plan-sets`, not the now-generic `long-horizon-research`. Embed decision tree. Preserve `plan`-as-default |
| P9 | single-source-provider-defaulting | P3, P6, P8 | `plan-research`, `consolidate-plan-sets`, `multi-phase-plan` base, `plan-and-verify` (references only, not duplications) | — | Pick the canonical home for the "default to codex" rule; replace duplicates with cross-references. Note: the now-generic `long-horizon-research` is *not* in this list — it no longer names a downstream |
| P10 | doctrine-and-worked-example | P8 | this dossier directory: a `docs/planning/skill-paradigm-coupling/` plan set's README, or a doctrine page next to it | — | End-to-end worked example showing prep → plan → verify with all three providers' decision points. Calls out the base/wrapper split and when to invoke each |
| P11 | verify-calibration-still-composes | P6, P8 | targeted re-run of `plan-and-verify verify` on a representative plan + read of `multi-phase-plan/SKILL.md` modes | — | Acceptance gate that the new prep mode hasn't broken verify or calibration sidecar |

Parallelism hint (final waves are the downstream planner's call):

- Wave 0: P1, P2 in parallel (independent; P2 only removes multi-phase coupling, doesn't depend on the new contract).
- Wave 1: P3 (depends on P1 + P2), P4, P5, P6 in parallel (all read P1's contract; touch disjoint files).
- Wave 2: P7 (depends on P6; can sub-layer per flavour file).
- Wave 3: P8.
- Wave 4: P9 (references; touches small surface across many files but only after the orchestrator settles).
- Wave 5: P10, P11 in parallel (doctrine doc + verify regression check).

## Open Decisions For The User

Four decisions materially affect the future plan. The downstream multi-phase planner will need answers (or the user can defer to the planner's recommendation):

0. **Names of the two new skills.** Short, paired, discoverable. Candidates:
   - **Wrapper** (loads the generic research base, adds planning obligations): `plan-research` *(recommended)* / `prep-research` / `plan-prep`.
   - **Handoff contract** (shared reference skill the wrapper + other producers + consumers all load): `plan-handoff` *(recommended)* / `handoff-spec` / `planner-handoff`.
   - **Recommendation**: `plan-research` + `plan-handoff`. Both 2-word kebab; sit alphabetically next to `plan-and-verify`, `plan-progress-review`; the `plan-` prefix telegraphs the family without adopting the `multi-phase-` prefix (which is reserved for the planner skills themselves).
   - **Discovery alias**: ship a `multi-plan-research` symlink pointing at `plan-research` so a user grepping for "multi" in the skill catalog still lands on the right skill. The canonical name stays short; the alias absorbs the "which one pairs with multi-phase?" lookup cost. Implemented as a directory symlink in `global/`; the alias's SKILL.md is the same file.

1. **Option A vs Option B for the entrypoint.**
   - **Option A** — add a new `plan-prep` skill that triages and dispatches to `long-horizon-research` or `consolidate-plan-sets`; `plan-and-verify` stays two-mode.
   - **Option B** — promote `plan-and-verify` to three-mode (`prep | plan | verify`); `prep` internally dispatches; no new skill name.
   - **Recommendation**: Option B. `plan-and-verify` is already the canonical orchestrator and users know its name. Adding `prep` to it is a strict superset and avoids a new catalog entry. Fewer names; tighter coupling.

2. **Strict shared schema vs minimal shared schema.**
   - **Strict** — fixed field set every upstream skill must emit; consumers can rely on every field being present.
   - **Minimal** — small set of always-required fields plus optional sections each upstream skill emits when applicable.
   - **Recommendation**: Minimal. Research, consolidation, and progress-review legitimately emphasize different evidence shapes; forcing a maximalist schema fabricates fields. The contract should be the subset every upstream already produces in some form: `current-state-summary`, `work-to-phase`, `blockers`, `recommended-flavour`. Everything else stays optional.

3. **Doctrine doc location.**
   - **Standalone `docs/planning/skill-paradigm-coupling.md`** (separate from this dossier; sibling to other planning content).
   - **Embedded in `plan-and-verify/SKILL.md`** (lives with the orchestrator code).
   - **Recommendation**: Embed the decision tree in `plan-and-verify/SKILL.md`; keep a brief pointer in `docs/planning/` or `docs/src/` that links to it. Doctrine that lives with the code stays current; standalone doctrine docs rot.

The downstream planner may proceed with the recommendations above unless the user objects.

## Planner Handoff

- **Selected downstream skill**: `multi-phase-plan-codex` (default per [long-horizon-research/SKILL.md:27](../../global/long-horizon-research/SKILL.md)). The user is welcome to switch to `multi-phase-plan-claude` if they want this Claude session's flavour propagated, or `multi-phase-plan-mixed` for cost-efficient routing across phases of mixed mechanical/design weight.
- **Dossier path**: [`docs/planning/skill-paradigm-coupling-research.md`](skill-paradigm-coupling-research.md).
- **Current-state summary**: Nine planning-related skills exist in [`global/`](../../global/) with implicit coupling via prose handoffs. No shared contract, no canonical entrypoint, three competing provider-default rules, duplicated audit invocations, and `long-horizon-research` conflates "general dossier producer" with "planning-tuned dossier producer". Single repo, no migration sequencing, no schema/API break with downstream consumers.
- **Work that should become phases**: Eleven phases listed in *Candidate Phase Boundaries*, organized in 6 dependency waves. P1 (shared handoff contract) and P2 (generalize `long-horizon-research` into a standalone reference skill) fan out in Wave 0; P3 (new `multi-phase-research` wrapper) plus P4/P5/P6 (producer patches + base from-dossier mode) fan out in Wave 1; P7 sub-layers naturally across three flavour files; P8-P11 serialize.
- **Known blockers that must remain blockers**: None foundational. One known unknown (skillnet calibration accepting non-plan-dir inputs) is not load-bearing — scope calibration to plan-dirs only and revisit if needed.
- **Acceptance evidence the future phase set should preserve**:
  - A new `plan-handoff` reference skill exists at `global/plan-handoff/SKILL.md`, defining the shared schema (mirrors `multi-phase-dispatch` precedent).
  - `long-horizon-research` is now a general-purpose reference skill: no downstream-planner naming, no Planner Handoff section in its dossier shape, no anti-pattern about running multi-phase skills. Verifiable by `rg -i "multi-phase" global/long-horizon-research/` returning nothing meaningful (or only a single `See also:` pointer).
  - A new `plan-research` skill exists at `global/plan-research/SKILL.md`, loads the generic `long-horizon-research` plus `plan-handoff`, and emits the schema literally. A `global/multi-plan-research` symlink → `plan-research` exists as a discovery alias; the SKILL.md description mentions the alias so skill-search matches both names.
  - `consolidate-plan-sets` and `plan-progress-review` (in producer role) also emit the schema literally — verifiable by `rg "## Planner Handoff" global/` showing the contract being referenced, not just the section title appearing in narrative form.
  - `multi-phase-plan` (base) has a documented `from-dossier` input mode with explicit field reads and override rules.
  - `plan-and-verify` is three-mode (`prep | plan | verify`); invoking it without a mode token still defaults to `plan` for backward compatibility. The `prep` mode dispatches to `plan-research` or `consolidate-plan-sets`, not directly to `long-horizon-research`.
  - Provider-default rule is defined in one place; all other references point at it. `long-horizon-research` is not in the chain (no longer names a downstream).
  - Existing `plan-and-verify verify` still runs cleanly against a representative plan set after all edits.
  - A worked example (in the orchestrator skill or doctrine doc) shows the prep → plan → verify arc end-to-end, and calls out when to use the base `long-horizon-research` standalone vs the `plan-research` wrapper.
- **Recommended decisions** (the user can override at plan time): `plan-research` + `plan-handoff` as the two new skill names, Option B for entrypoint, Minimal schema, doctrine embedded in `plan-and-verify/SKILL.md` with a pointer from `docs/`.

To proceed: hand this dossier to `multi-phase-plan-codex` with the brief *"Decompose the planning-skill coupling work described in `docs/planning/skill-paradigm-coupling-research.md` into a multi-phase plan set under `docs/planning/skill-paradigm-coupling/`. Honor the candidate phase boundaries, dependency waves, and open-decision recommendations; deviate only with stated reason."*
