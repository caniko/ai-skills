---
name: problem-group-lifecycle-reference
description: Structure investigations into evidence-based problem groups with plan, fork/select, and build phases. Use for grouping, exclusions, and downstream handoffs.
---

# Problem Group Lifecycle Reference

Keep the active harness in charge of planning and build modes. This reference
defines the records passed between those modes; it does not route models or
create a second planning system.

## Phase 1: Plan

Collect evidence without changing the investigated system. Normalize each
finding into:

- symptom and affected items;
- earliest evidence-supported cause and confidence;
- responsible source, service, operator, or upstream owner;
- prerequisites, blockers, and recovery producer;
- exact acceptance gate.

Group findings only when cause, owner, and acceptance gate are the same. Do not
group by similar error text alone, and do not split one cause merely because it
affects several services.

Honor exclusions by affected-item membership. An instruction such as “exclude
Group 4” is valid only when Group 4's record or affected-item list is available.
If it is missing, stop and request that foundational input rather than guessing.
Keep excluded items out of new groups while retaining any effect they have on a
parent health gate.

Preserve supplied group numbers. Give each group a stable
`<owner>/<root-cause-slug>` key and allocate new numbers after the highest
supplied number. Order new groups by dependency, then severity, then key.

Use this record:

```markdown
## Group N — Title

- Key:
- Status: planned
- Cause and confidence:
- Affected items:
- Evidence:
- Owner and authority:
- Dependencies:
- Blocker and recovery:
- Acceptance gate:
- Fork prompt:
```

Allowed statuses are `planned`, `selected`, `building`, `verified`, `blocked`,
and `deferred`.

## Phase 2: Fork and select

Emit one self-contained Markdown record per group. The fork prompt must name
the selected group, carry its evidence and boundaries, invoke the relevant
domain skill, and state the exact acceptance gate. Do not write planning files
unless the caller explicitly asks for persistence.

Select one group per downstream conversation. Keep cross-group dependencies in
the record; do not silently expand a fork to sibling groups.

## Phase 3: Build

Load `$fix-loop` and operate only on the selected group. Establish its repair
contract before changing state, then:

1. capture the group gate baseline;
2. repair the earliest cause at its highest-authority owner;
3. run the narrow validation and exact group gate;
4. rerun the parent investigation or health gate;
5. mark only that group `verified`.

Regroup only when new evidence changes the cause, owner, or gate. Preserve the
old key and explain the replacement. Never mark excluded or unselected groups
complete as a side effect.

For a missing or invalid foundational input, report its exact identity, why it
is required, its upstream producer, the recovery workflow, and the validation
that proves recovery.
