# Ultra lifecycle contract

Every ultra run uses three model-owned phases. Do not edit target source until
the planning artifact validates. Do not report successful completion until the
review artifact validates and its verdict is `approved`.

## 1. Frontier planning

Assign discovery, architecture analysis, profile coverage, and work-package
design to a frontier-class model at `high` effort or greater. The planning
phase is read-only outside `.ultra-out/`.

Write `.ultra-out/plan.json` with:

- `schema_version = 3` and `artifact = "ultra-plan"`;
- the registry and `survey.initial.json` hashes, initial source revision and
  fingerprint, run mode, mode override, and survey resource budget;
- `planner = { provider, model_class, model, effort, invocation_id,
  context_id }`, where the class is `frontier` and IDs come from the runtime;
- every registry profile ID, in registry order;
- ordered work packages that assign every profile exactly once and declare
  dependencies, scope, objectives, expected breaking changes, migration work,
  validation, and risks.

Validate the frozen plan before building:

```sh
ultra-system-reference/scripts/ultra-system plan validate \
  --registry <ultra-skill>/references/concerns.toml \
  --plan .ultra-out/plan.json \
  --root <target>
```

The validator binds the plan to the pre-build source fingerprint. A normal
ultra request proceeds automatically after validation. A plan/audit-only
request stops here. External side effects or authority not granted by the user
still require approval.

Do not invent runtime provenance. If the host cannot expose model, invocation,
or context identity, report the planning/build/review attestation as blocked.
The validator has an explicit OpenAI role allowlist: `gpt-5.6-sol` and
`gpt-5.5` are frontier; `gpt-5.6-luna` and `gpt-5.3-codex-spark` are efficient.
Update the validator when OpenAI model roles change; do not relabel an unknown
model in an artifact. Other providers are blocked until their
harness-authoritative model classifications are added to the validator.
The validator can prove artifact order and source/hash continuity after the
plan exists; without harness-signed request events it cannot prove that a user
did not mutate source before starting the ultra run.

## 2. Efficient-model build

Assign implementation to an efficient coding model. For OpenAI model roles,
prefer `gpt-5.6-luna` for the builder. If no allowlisted efficient model is
available, report the build role blocked. Give builders only the frozen plan
hash, their work packages, profile procedures, bounded scope, and resource
budget.

Builders may make the breaking changes authorized by the ultra domain and
must migrate in-repository consumers. They may not silently expand or weaken
the plan. A material discovery outside the plan becomes `replan-required` and
returns to the frontier planner. Work within the frozen scope may be repaired
without replanning.

Write `.ultra-out/build.json` with:

- `artifact = "ultra-build"` and the exact `plan_sha256`;
- builder provider, model, effort, runtime invocation, and context, with
  `model_class = "efficient"`; its model and context must differ from planning;
- the final source revision and fingerprint;
- every planned work package exactly once, with status, unchanged profile
  assignment, changes, evidence, validation, and residuals.

Validate the build receipt against the current source:

```sh
ultra-system-reference/scripts/ultra-system build validate \
  --registry <ultra-skill>/references/concerns.toml \
  --plan .ultra-out/plan.json \
  --build .ultra-out/build.json \
  --root <target>
```

Before review, produce source-bound evidence with these schema-v3 shapes:

- `score-history.json`: `artifact = "ultra-score-history"`, registry and plan
  hashes, and non-empty `entries`. Each entry has `stage`, source revision,
  source fingerprint, and a survey hash or `null`. The first entry binds to
  `survey.initial.json`; the last binds to the build source; intermediate
  stages correspond exactly to stage receipts. Completion evidence revalidates
  every post-initial stage against the final integrated build source; keep any
  historical transition telemetry separately.
- `receipts/<stage>.json`: `artifact = "ultra-stage-receipt"`, stage, plan hash,
  source fingerprint, profile IDs, findings, changes, validation, and
  residuals. Validation is non-empty, the source state appears in score
  history, and all receipts together cover every registry profile exactly once.
- `final-validation.json`: `artifact = "ultra-final-validation"`, plan hash,
  final source revision/fingerprint, and a non-empty `gates` array. Every gate
  has unique `name`, `status = "passed"`, and non-empty evidence.
- `evidence-manifest.json`: `artifact = "ultra-evidence-manifest"` and `files`
  entries containing relative `path` and `sha256` for every required artifact.

## 3. Frontier review

Finalize the profile ledger, then return the completed build, diff, ledger,
receipts, migrations, and fresh gates to the exact frontier model identity
recorded in `plan.json`.
Use an independent review context. Review effort may equal planning effort or
be lower, but may not exceed it. For OpenAI model roles, prefer
`gpt-5.6-sol` for both planning and review when available.

The reviewer checks implementation against the frozen plan, all profile and
obligation coverage, architectural quality, migration completeness, resource
discipline, and final gates. Write `.ultra-out/review.json` with:

- exact plan, build, and ledger hashes plus the final source revision and
  fingerprint;
- `evidence_manifest_sha256` for `.ultra-out/evidence-manifest.json`; the
  manifest must hash `survey.initial.json`, `profile-ledger.json`,
  `score-history.json`, every `receipts/*.json`, and `final-validation.json`;
- the same frontier provider/model as the planner, the review effort, and
  distinct runtime invocation/context IDs;
- every registry profile ID in order;
- verdict `approved`, `changes-requested`, or `blocked`, with findings,
  validation, and residuals. `findings` contains only open review findings;
  preserve resolved review work in build receipts or validation evidence.

Validate the review:

```sh
ultra-system-reference/scripts/ultra-system review validate \
  --registry <ultra-skill>/references/concerns.toml \
  --plan .ultra-out/plan.json \
  --build .ultra-out/build.json \
  --review .ultra-out/review.json \
  --ledger .ultra-out/profile-ledger.json \
  --root <target>
```

`changes-requested` returns to the efficient builder when the correction fits
the frozen plan. Update `build.json`, then replace `review.json` after another
frontier review. Material scope or architecture changes require a new frontier
plan and invalidate downstream artifact hashes.

An approved review requires all build packages completed, fresh validation,
and no open findings or residuals. Final ledger validation requires a review
whenever a build exists; successful ledger validation additionally requires
all three lifecycle artifacts. Artifact hashes prevent a stale plan, build, or
review from being reused after changes.

The validator also checks artifact content: the initial survey must match the
registry and plan; score history must connect the initial survey to the final
build source; stage receipts must collectively cover every profile exactly
once and bind to the plan; final validation must bind fresh gates to the final
source. Empty JSON placeholders are invalid.
