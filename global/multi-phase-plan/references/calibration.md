# Calibration subsystem (skillnet)

The skillnet calibration loop for `multi-phase-plan`. The `plan` and `verify`
modes record sampled plans here; `calibrate` mode tunes thresholds from the
accumulated dataset. The SKILL body's "Record for calibration" and verify steps
point here for the catalog/sidecar/meta-heuristic detail.

## Contents

- [Heuristics catalog](#heuristics-catalog) — trigger categories and what each adds.
- [When a plan gets recorded](#when-a-plan-gets-recorded) — meta-heuristics.
- [Sidecar `.calibration.json`](#sidecar-calibrationjson) — schema.
- [Tag conventions](#tag-conventions) — auto-tags and user tags.
- [Verifier `surprises` field](#verifier-surprises-field) — structured prefixes.
- [Mode: `calibrate`](#mode-calibrate) — workflow, non-interactive use, cadence.
- [Calibration changelog](#calibration-changelog) — audit trail footer.

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

3. After `walkthrough` finishes, copy the markdown block between `──── Changelog block ────` and the closing `══` markers into the "Calibration changelog" footer below. For each accepted proposal, also update the corresponding heuristic's threshold in the catalog section above. The catalog is descriptive; the live threshold is the one in skillnet, and this footer is for human audit.

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

### Calibrate-mode anti-patterns

- **Hand-editing the calibration changelog.** It is the audit trail; paste blocks from `skillnet calibration walkthrough` or `skillnet calibration export-changelog` only.
- **Editing thresholds in skillnet without going through `walkthrough`.** The accepted-proposal trail in `calibration_proposals` is provenance; bypassing it leaves no record of why a threshold moved.

## Calibration changelog

Threshold changes to the heuristics catalog above are recorded here. Each entry is produced by `skillnet calibration walkthrough` or `export-changelog` and pasted by the user during a `calibrate` mode session. The live thresholds are authoritative in skillnet (`heuristic_thresholds` table); this footer is the human-readable audit trail.

<!-- Newest first. Format produced by `skillnet calibration export-changelog`. -->

### 2026-05-24 — Calibration loop activated

- skillnet 0.4.0 consumed via HM module re-export.
- Initial heuristic thresholds: see `skillnet calibration heuristics list --format json` for live values.
- Database backend: Postgres (`postgres:///can?host=/run/postgresql` per this user's HM config; SQLite fallback documented).
- No threshold changes in this entry — genesis row only.
