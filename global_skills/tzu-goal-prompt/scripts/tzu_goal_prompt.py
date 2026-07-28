#!/usr/bin/env python3
"""Build a grounded prompt from tzu harness state and external harness files."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shlex
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_SQLITE = Path(".tzu/state.sqlite")
STATE_ID = "project-state"


class Blocker(Exception):
    def __init__(
        self,
        *,
        missing: str,
        why: str,
        producer: str,
        regenerate: str,
        validate: str,
    ) -> None:
        self.missing = missing
        self.why = why
        self.producer = producer
        self.regenerate = regenerate
        self.validate = validate
        super().__init__(missing)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a grounded goal prompt from tzu harness metadata.",
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--state-json", type=Path)
    parser.add_argument("--harness-output", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    try:
        prompt = build_prompt(args)
    except Blocker as error:
        print(format_blocker(error), file=sys.stderr)
        return 2

    print(prompt)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(prompt + "\n", encoding="utf-8")
    return 0


def build_prompt(args: argparse.Namespace) -> str:
    state, state_source, context_snapshots = load_state(args.state_json, args.sqlite)
    external_outputs = load_external_outputs(args.harness_output)
    return render_prompt(state, state_source, context_snapshots, external_outputs)


def load_state(
    state_json: Path | None,
    sqlite_path: Path,
) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    if state_json is not None:
        if not state_json.exists():
            raise missing_state_blocker(
                f"state JSON `{state_json}` does not exist",
                state_json=state_json,
                sqlite_path=sqlite_path,
            )
        text = state_json.read_text(encoding="utf-8")
        if not text.strip():
            raise missing_state_blocker(
                f"state JSON `{state_json}` is empty",
                state_json=state_json,
                sqlite_path=sqlite_path,
            )
        return json.loads(text), str(state_json), []

    if not sqlite_path.exists():
        raise missing_state_blocker(
            f"SQLite state database `{sqlite_path}` does not exist",
            state_json=state_json,
            sqlite_path=sqlite_path,
        )

    try:
        connection = sqlite3.connect(sqlite_path)
    except sqlite3.Error as error:
        raise missing_state_blocker(
            f"SQLite state database `{sqlite_path}` is unreadable: {error}",
            state_json=state_json,
            sqlite_path=sqlite_path,
        ) from error

    with connection:
        state_row = connection.execute(
            "SELECT state_json FROM project_state WHERE id = ?",
            (STATE_ID,),
        ).fetchone()
        if state_row is None:
            raise missing_state_blocker(
                f"SQLite state database `{sqlite_path}` has no `{STATE_ID}` row",
                state_json=state_json,
                sqlite_path=sqlite_path,
            )
        snapshots = []
        with contextlib.suppress(sqlite3.Error):
            rows = connection.execute(
                "SELECT snapshot_json FROM context_snapshots ORDER BY updated_at, id",
            ).fetchall()
            snapshots = [json.loads(row[0]) for row in rows]
    return json.loads(state_row[0]), str(sqlite_path), snapshots


def missing_state_blocker(
    missing: str,
    *,
    state_json: Path | None,
    sqlite_path: Path,
) -> Blocker:
    validation_target = state_json if state_json is not None else sqlite_path
    return Blocker(
        missing=missing,
        why="A tzu ProjectState is required to extract grounded goal, plan, and harness claims.",
        producer="tzu planning workflow",
        regenerate='Run `tzu plan "<goal>" --domain coding --context-root <path>` or export ProjectState JSON with the current plan.',
        validate=f"test -s {shlex.quote(str(validation_target))}",
    )


def load_external_outputs(paths: list[Path]) -> list[tuple[Path, str]]:
    outputs = []
    for path in paths:
        if not path.exists():
            raise Blocker(
                missing=f"external harness output `{path}` does not exist",
                why="The prompt must preserve external harness claims from the exact supplied artifact.",
                producer="the external harness workflow named by the user",
                regenerate=f"Run the external harness and write its output to {shlex.quote(str(path))}.",
                validate=f"test -s {shlex.quote(str(path))}",
            )
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            raise Blocker(
                missing=f"external harness output `{path}` is empty",
                why="Empty harness output cannot support any factual project claims.",
                producer="the external harness workflow named by the user",
                regenerate=f"Re-run the external harness and write non-empty output to {shlex.quote(str(path))}.",
                validate=f"test -s {shlex.quote(str(path))}",
            )
        outputs.append((path, text.rstrip()))
    return outputs


def render_prompt(
    state: dict[str, Any],
    state_source: str,
    context_snapshots: list[dict[str, Any]],
    external_outputs: list[tuple[Path, str]],
) -> str:
    plan = state.get("current_plan") or {}
    harness = plan.get("harness")
    spec = (harness or {}).get("problem_spec") or {}

    lines = [
        "# Grounded Goal Prompt",
        "",
        "Use this prompt as a starting point. Treat every harness claim below as evidence to verify before making consequential changes.",
        "",
        "## Source State",
        "",
        f"- tzu state source: `{state_source}`",
        f"- project root: {inline(state.get('project_root'))}",
    ]

    lines.extend(render_goal_section(plan, spec))
    if harness:
        lines.extend(render_harness_section(harness, spec))
    else:
        lines.extend(render_missing_harness_section(plan))
    lines.extend(render_context_snapshots(context_snapshots))
    lines.extend(render_external_outputs(external_outputs))
    lines.extend(
        [
            "## Instructions For The Next Agent",
            "",
            "- Verify the cited harness claims against the current repository before editing.",
            "- Preserve blockers and validation obligations as hard constraints.",
            "- Do not fabricate missing files, outputs, schema details, or test results.",
            "- If a foundational input is missing or stale, stop and report the missing artifact, upstream producer, regeneration command, and validation command.",
        ]
    )
    return "\n".join(lines).rstrip()


def render_goal_section(plan: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    visible_goal = plan.get("goal") or "(no current plan goal found)"
    planner_goal = spec.get("goal")
    lines = [
        "",
        "## Goal",
        "",
        f"- user-visible goal: {inline(visible_goal)}",
    ]
    if planner_goal and planner_goal != visible_goal:
        lines.append(f"- planner goal: {inline(planner_goal)}")
    return lines


def render_harness_section(harness: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    lines = [
        "",
        "## Tzu Harness Claims",
        "",
        f"- domain: {inline(spec.get('domain'))}",
        f"- project root: {inline(spec.get('project_root'))}",
        f"- selected candidate: {inline(harness.get('selected_candidate_id'))}",
    ]
    lines.extend(render_list("Constraints", spec.get("constraints") or []))
    lines.extend(render_acceptance_criteria(spec.get("acceptance") or []))
    lines.extend(render_evidence(spec.get("evidence") or []))
    lines.extend(render_frontier(harness))
    lines.extend(render_candidates(harness))
    lines.extend(render_obligations(harness))
    return lines


def render_missing_harness_section(plan: dict[str, Any]) -> list[str]:
    plan_id = plan.get("id") or "(no current plan)"
    return [
        "",
        "## Tzu Harness Claims",
        "",
        "- unavailable: current project state does not contain persisted harness metadata.",
        f"- current plan id: {inline(plan_id)}",
        '- regenerate: `tzu plan "<goal>" --domain coding --context-root <path>`',
        "- validate: `tzu inspect --frontier` shows retained candidates and selected champion.",
    ]


def render_list(title: str, values: list[Any]) -> list[str]:
    lines = ["", f"### {title}", ""]
    if not values:
        return lines + ["- none recorded"]
    return lines + [f"- {inline(value)}" for value in values]


def render_acceptance_criteria(values: list[Any]) -> list[str]:
    lines = ["", "### Acceptance Criteria", ""]
    if not values:
        return lines + ["- none recorded"]
    rendered = []
    for value in values:
        if isinstance(value, dict):
            rendered.append(f"- {inline(value.get('description'))}")
        else:
            rendered.append(f"- {inline(value)}")
    return lines + rendered


def render_evidence(values: list[Any]) -> list[str]:
    lines = ["", "### Evidence", ""]
    if not values:
        return lines + ["- none recorded"]
    rendered = []
    for value in values:
        if isinstance(value, dict):
            rendered.append(
                f"- {inline(value.get('source'))}: {inline(value.get('summary'))}"
            )
        else:
            rendered.append(f"- {inline(value)}")
    return lines + rendered


def render_frontier(harness: dict[str, Any]) -> list[str]:
    frontier = harness.get("frontier") or {}
    retained = frontier.get("retained_candidate_ids") or []
    discarded = frontier.get("discarded_candidates") or []
    lines = [
        "",
        "### Frontier",
        "",
        f"- selected champion: {inline(frontier.get('selected_candidate_id'))}",
        f"- retained candidates: {', '.join(map(str, retained)) if retained else 'none recorded'}",
    ]
    if discarded:
        lines.append("- discarded candidates:")
        for item in discarded:
            if isinstance(item, dict):
                lines.append(
                    f"  - {inline(item.get('candidate_id'))}: {inline(item.get('reason'))}"
                )
            else:
                lines.append(f"  - {inline(item)}")
    return lines


def render_candidates(harness: dict[str, Any]) -> list[str]:
    lines = ["", "### Candidate Summaries", ""]
    candidates = harness.get("candidates") or []
    if not candidates:
        return lines + ["- none recorded"]
    for candidate in candidates:
        candidate_id = candidate.get("id")
        plan = candidate.get("candidate") or {}
        status = candidate.get("status")
        summary = plan.get("summary")
        lines.append(f"- {inline(candidate_id)} [{inline(status)}]: {inline(summary)}")
    return lines


def render_obligations(harness: dict[str, Any]) -> list[str]:
    lines = ["", "### Validation Obligations And Blockers", ""]
    obligations = []
    for candidate in harness.get("candidates") or []:
        validation = candidate.get("validation") or {}
        for obligation in validation.get("obligations") or []:
            obligations.append((candidate.get("id"), obligation))
    if not obligations:
        return lines + ["- none recorded"]
    for candidate_id, obligation in obligations:
        if not isinstance(obligation, dict):
            lines.append(f"- {inline(candidate_id)}: {inline(obligation)}")
            continue
        lines.append(
            f"- {inline(candidate_id)} / {inline(obligation.get('id'))}: {inline(obligation.get('description'))}"
        )
        lines.append(f"  - producer: {inline(obligation.get('producer'))}")
        lines.append(
            f"  - regenerate: {inline(obligation.get('regenerate_command'))}"
        )
        lines.append(
            f"  - validate: {inline(obligation.get('validation_command'))}"
        )
    return lines


def render_context_snapshots(snapshots: list[dict[str, Any]]) -> list[str]:
    lines = ["", "## Persisted Coding Context Claims", ""]
    if not snapshots:
        return lines + ["- no persisted context snapshots found in the selected state source"]
    for snapshot in snapshots:
        lines.append(f"- snapshot {inline(snapshot.get('id'))}: {inline(snapshot.get('summary'))}")
        for root in snapshot.get("roots") or []:
            lines.append(
                f"  - root {inline(root.get('id'))}: path={inline(root.get('root'))}, files={inline(len(root.get('files') or []))}, dirty={inline(root.get('dirty'))}"
            )
            manifests = root.get("manifests") or []
            docs = root.get("docs") or []
            if manifests:
                lines.append(
                    "    - manifests: "
                    + ", ".join(inline(doc.get("path")) for doc in manifests if isinstance(doc, dict))
                )
            if docs:
                lines.append(
                    "    - docs: "
                    + ", ".join(inline(doc.get("path")) for doc in docs if isinstance(doc, dict))
                )
    return lines


def render_external_outputs(outputs: list[tuple[Path, str]]) -> list[str]:
    lines = ["", "## External Harness Outputs", ""]
    if not outputs:
        return lines + ["- none supplied"]
    for path, text in outputs:
        lines.extend(
            [
                f"### {path}",
                "",
                "```text",
                text,
                "```",
                "",
            ]
        )
    return lines


def inline(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    text = str(value).replace("\n", " ").strip()
    return text or "unknown"


def format_blocker(error: Blocker) -> str:
    return "\n".join(
        [
            "tzu-goal-prompt blocker:",
            f"- missing artifact/source: {error.missing}",
            f"- why required: {error.why}",
            f"- upstream producer: {error.producer}",
            f"- regenerate: {error.regenerate}",
            f"- validate: {error.validate}",
        ]
    )


def run_self_test() -> int:
    tests = [
        ("state json extraction", test_state_json_extraction),
        ("sqlite project_state extraction", test_sqlite_extraction),
        ("external harness output inclusion", test_external_output),
        ("missing sqlite failure", test_missing_sqlite_failure),
        ("missing external file failure", test_missing_external_failure),
    ]
    for name, test in tests:
        test()
        print(f"ok - {name}")
    return 0


def fixture_state(with_harness: bool = True) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "id": "plan-demo",
        "goal": "visible goal @demo",
        "domain": "coding",
        "tasks": [],
    }
    if with_harness:
        plan["harness"] = {
            "problem_spec": {
                "id": "problem-demo",
                "goal": "visible goal /tmp/demo",
                "domain": "coding",
                "project_root": "/tmp/demo",
                "constraints": ["Do not overwrite unrelated user work."],
                "acceptance": [{"description": "Demo behavior is implemented."}],
                "evidence": [{"source": "user-goal", "summary": "visible goal /tmp/demo"}],
            },
            "selected_candidate_id": "candidate-1",
            "candidates": [
                {
                    "id": "candidate-1",
                    "status": "valid",
                    "candidate": {"summary": "Implement demo safely."},
                    "validation": {
                        "obligations": [
                            {
                                "id": "tests",
                                "description": "Run focused tests.",
                                "producer": "test workflow",
                                "regenerate_command": "cargo test",
                                "validation_command": "cargo test",
                            }
                        ]
                    },
                }
            ],
            "frontier": {
                "selected_candidate_id": "candidate-1",
                "retained_candidate_ids": ["candidate-1"],
                "discarded_candidates": [],
            },
        }
    return {
        "project_root": "/tmp/demo",
        "current_plan": plan,
        "planning_runs": [],
        "run_reports": [],
    }


def fixture_snapshot() -> dict[str, Any]:
    return {
        "id": "snapshot-demo",
        "summary": "1 context roots, 1 indexed files, 0 nested boundaries",
        "roots": [
            {
                "id": "context-root-1",
                "root": "/tmp/demo",
                "dirty": False,
                "files": [{"path": "Cargo.toml"}],
                "manifests": [{"path": "Cargo.toml"}],
                "docs": [],
            }
        ],
    }


def test_state_json_extraction() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        state_path = root / "state.json"
        state_path.write_text(json.dumps(fixture_state()), encoding="utf-8")
        output = capture_build(
            argparse.Namespace(
                state_json=state_path,
                sqlite=root / "missing.sqlite",
                harness_output=[],
                output=None,
            )
        )
        assert "planner goal: visible goal /tmp/demo" in output
        assert "candidate-1" in output


def test_sqlite_extraction() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        db = root / "state.sqlite"
        connection = sqlite3.connect(db)
        with connection:
            connection.execute(
                "CREATE TABLE project_state (id TEXT PRIMARY KEY, state_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE context_snapshots (id TEXT, run_id TEXT, snapshot_json TEXT, updated_at TEXT)"
            )
            connection.execute(
                "INSERT INTO project_state (id, state_json) VALUES (?, ?)",
                (STATE_ID, json.dumps(fixture_state())),
            )
            connection.execute(
                "INSERT INTO context_snapshots (id, run_id, snapshot_json, updated_at) VALUES (?, ?, ?, ?)",
                ("snapshot-demo", "planning-run-1", json.dumps(fixture_snapshot()), "1"),
            )
        output = capture_build(
            argparse.Namespace(
                state_json=None,
                sqlite=db,
                harness_output=[],
                output=None,
            )
        )
        assert "snapshot-demo" in output
        assert "Cargo.toml" in output


def test_external_output() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        state_path = root / "state.json"
        harness_path = root / "harness.txt"
        state_path.write_text(json.dumps(fixture_state()), encoding="utf-8")
        harness_path.write_text("external claim: build graph is acyclic\n", encoding="utf-8")
        output = capture_build(
            argparse.Namespace(
                state_json=state_path,
                sqlite=root / "missing.sqlite",
                harness_output=[harness_path],
                output=None,
            )
        )
        assert "external claim: build graph is acyclic" in output
        assert str(harness_path) in output


def test_missing_sqlite_failure() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        try:
            load_state(None, root / "missing.sqlite")
        except Blocker as error:
            assert "does not exist" in error.missing
            assert "tzu plan" in error.regenerate
            return
    raise AssertionError("expected missing sqlite blocker")


def test_missing_external_failure() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        try:
            load_external_outputs([root / "missing.txt"])
        except Blocker as error:
            assert "does not exist" in error.missing
            assert "test -s" in error.validate
            return
    raise AssertionError("expected missing external file blocker")


def capture_build(args: argparse.Namespace) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print(build_prompt(args))
    return buffer.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
