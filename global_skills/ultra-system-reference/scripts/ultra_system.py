#!/usr/bin/env python3
"""Validate and survey profile-granular ultra orchestration registries."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
EVALUATIONS = {"quantitative", "indicative", "qualitative"}
SCREENS = {"always", "signal"}
GATE_KINDS = {"always", "any-file"}
DETECTOR_KINDS = {"literal", "file-lines-gt", "file-lines-lt"}
PROFILE_FIELDS = {
    "id",
    "skill",
    "stage",
    "procedure",
    "evaluation",
    "screen",
    "gate",
    "threshold",
    "detectors",
}
GATE_FIELDS = {"kind", "globs"}
DETECTOR_FIELDS = {"kind", "pattern", "weight", "globs", "lines"}
STATUSES = {
    "reviewed-clean",
    "fixed-verified",
    "not-applicable",
    "deferred",
    "blocked",
    "unreviewed",
}
SUCCESS_STATUSES = {"reviewed-clean", "fixed-verified", "not-applicable"}
TERMINAL_STATES = {
    "complete",
    "complete-with-approved-exclusions",
    "incomplete",
    "blocked",
    "incomplete-convergence-cap",
}
EXCLUDED_PARTS = {
    ".git",
    ".claude",
    ".direnv",
    ".ultra-out",
    "graphify-out",
    "node_modules",
    "result",
    "target",
    "vendor",
}


class ContractError(RuntimeError):
    """Raised when registry or ledger evidence violates the shared contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def load_registry(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        raw = path.read_bytes()
        registry = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ContractError(f"cannot read registry {path}: {error}") from error
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"registry schema_version must be {SCHEMA_VERSION}")
    profiles = registry.get("profile")
    if not isinstance(profiles, list) or not profiles:
        raise ContractError("registry must contain at least one [[profile]]")
    validate_profiles(path, profiles)
    return registry, profiles


def require_text(profile: dict[str, Any], field: str, profile_id: str) -> str:
    value = profile.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"profile {profile_id}: {field} must be non-empty text")
    return value


def validate_profiles(registry_path: Path, profiles: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ContractError("every [[profile]] must be a table")
        profile_id = require_text(profile, "id", "<unknown>")
        unknown_fields = set(profile) - PROFILE_FIELDS
        if unknown_fields:
            raise ContractError(
                f"profile {profile_id}: unknown fields {sorted(unknown_fields)}"
            )
        if profile_id in seen:
            raise ContractError(f"duplicate profile id: {profile_id}")
        seen.add(profile_id)
        for field in ("skill", "stage", "procedure", "evaluation", "screen"):
            require_text(profile, field, profile_id)
        if profile["evaluation"] not in EVALUATIONS:
            raise ContractError(f"profile {profile_id}: unknown evaluation {profile['evaluation']}")
        if profile["screen"] not in SCREENS:
            raise ContractError(f"profile {profile_id}: unknown screen {profile['screen']}")
        if profile["evaluation"] == "qualitative" and profile["screen"] != "always":
            raise ContractError(f"profile {profile_id}: qualitative profiles must always screen")
        procedure = (registry_path.parent / profile["procedure"]).resolve()
        if not procedure.is_file():
            raise ContractError(f"profile {profile_id}: missing procedure {procedure}")
        gate = profile.get("gate")
        if not isinstance(gate, dict) or gate.get("kind") not in GATE_KINDS:
            raise ContractError(f"profile {profile_id}: gate must use one of {sorted(GATE_KINDS)}")
        unknown_gate_fields = set(gate) - GATE_FIELDS
        if unknown_gate_fields:
            raise ContractError(
                f"profile {profile_id}: unknown gate fields {sorted(unknown_gate_fields)}"
            )
        globs = gate.get("globs", [])
        if gate["kind"] == "any-file" and (not isinstance(globs, list) or not globs):
            raise ContractError(f"profile {profile_id}: any-file gate requires globs")
        threshold = profile.get("threshold", 1)
        if not isinstance(threshold, int) or threshold < 1:
            raise ContractError(f"profile {profile_id}: threshold must be a positive integer")
        detectors = profile.get("detectors", [])
        if not isinstance(detectors, list):
            raise ContractError(f"profile {profile_id}: detectors must be an array")
        if profile["screen"] == "signal" and not detectors:
            raise ContractError(f"profile {profile_id}: signal screening requires detectors")
        for detector in detectors:
            validate_detector(profile_id, detector)


def validate_detector(profile_id: str, detector: Any) -> None:
    if not isinstance(detector, dict) or detector.get("kind") not in DETECTOR_KINDS:
        raise ContractError(f"profile {profile_id}: malformed detector")
    unknown_fields = set(detector) - DETECTOR_FIELDS
    if unknown_fields:
        raise ContractError(
            f"profile {profile_id}: unknown detector fields {sorted(unknown_fields)}"
        )
    weight = detector.get("weight", 1)
    if not isinstance(weight, int) or weight < 1:
        raise ContractError(f"profile {profile_id}: detector weight must be positive")
    globs = detector.get("globs")
    if not isinstance(globs, list) or not globs or not all(isinstance(item, str) for item in globs):
        raise ContractError(f"profile {profile_id}: detector requires string globs")
    if detector["kind"] == "literal":
        if not isinstance(detector.get("pattern"), str) or not detector["pattern"]:
            raise ContractError(f"profile {profile_id}: literal detector requires pattern")
    elif not isinstance(detector.get("lines"), int) or detector["lines"] < 0:
        raise ContractError(f"profile {profile_id}: line detector requires non-negative lines")


def repository_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def matches_glob(relative: str, pattern: str) -> bool:
    return fnmatch.fnmatch(relative, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatch(relative, pattern[3:])
    )


def scan_files(root: Path) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative_path.parts):
            continue
        files.append((relative_path.as_posix(), path))
    return sorted(files)


def source_state_sha256(files: list[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for relative, path in files:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        try:
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as error:
            raise ContractError(f"cannot fingerprint source file {path}: {error}") from error
        digest.update(b"\0")
    return digest.hexdigest()


def resource_budget() -> dict[str, int | None]:
    logical_cpus = os.cpu_count() or 1
    available_memory_mib: int | None = None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                available_memory_mib = int(line.split()[1]) // 1024
                break
    except (OSError, ValueError, IndexError):
        pass
    memory_limited_jobs = 1
    if available_memory_mib is not None:
        memory_limited_jobs = max(1, available_memory_mib // 3072)
    return {
        "logical_cpus": logical_cpus,
        "available_memory_mib": available_memory_mib,
        "max_read_only_agents": min(4, logical_cpus),
        "max_heavy_commands": 1,
        "recommended_build_jobs": min(4, logical_cpus, memory_limited_jobs),
    }


def selected_files(
    files: list[tuple[str, Path]], globs: list[str]
) -> list[tuple[str, Path]]:
    return [item for item in files if any(matches_glob(item[0], glob) for glob in globs)]


def evaluate_detector(
    detector: dict[str, Any], files: list[tuple[str, Path]]
) -> tuple[int, list[dict[str, Any]]]:
    candidates = selected_files(files, detector["globs"])
    matches: list[dict[str, Any]] = []
    count = 0
    for relative, path in candidates:
        try:
            with path.open(encoding="utf-8", errors="replace") as source:
                if detector["kind"] == "literal":
                    occurrences = sum(line.count(detector["pattern"]) for line in source)
                    lines = None
                else:
                    lines = sum(1 for _ in source)
                    occurrences = 0
        except OSError:
            continue
        if detector["kind"] == "literal":
            if occurrences:
                count += occurrences
                if len(matches) < 25:
                    matches.append({"path": relative, "occurrences": occurrences})
        else:
            assert lines is not None
            triggered = (
                detector["kind"] == "file-lines-gt" and lines > detector["lines"]
            ) or (
                detector["kind"] == "file-lines-lt" and lines < detector["lines"]
            )
            if triggered:
                count += 1
                if len(matches) < 25:
                    matches.append({"path": relative, "lines": lines})
    return count * detector.get("weight", 1), matches


def effective_threshold(threshold: int, sensitivity: str) -> int:
    if sensitivity == "low":
        return threshold * 3
    if sensitivity == "high":
        return 1
    return threshold


def build_survey(registry_path: Path, root: Path, sensitivity: str) -> dict[str, Any]:
    if not root.is_dir():
        raise ContractError(f"target root is not a directory: {root}")
    _, profiles = load_registry(registry_path)
    files = scan_files(root)
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        gate = profile["gate"]
        gate_files = files if gate["kind"] == "always" else selected_files(files, gate["globs"])
        gate_passed = gate["kind"] == "always" or bool(gate_files)
        score = 0
        evidence: list[dict[str, Any]] = []
        for detector in profile.get("detectors", []):
            detector_score, matches = evaluate_detector(detector, files)
            score += detector_score
            evidence.append(
                {
                    "kind": detector["kind"],
                    "pattern": detector.get("pattern"),
                    "score": detector_score,
                    "matches": matches,
                }
            )
        threshold = effective_threshold(profile.get("threshold", 1), sensitivity)
        decision = "not-applicable"
        if gate_passed:
            decision = "run" if profile["screen"] == "always" or score >= threshold else "screened-clean"
        rows.append(
            {
                "id": profile["id"],
                "skill": profile["skill"],
                "stage": profile["stage"],
                "evaluation": profile["evaluation"],
                "procedure": profile["procedure"],
                "gate": {"passed": gate_passed, "matched_files": len(gate_files)},
                "score": score,
                "effective_threshold": threshold,
                "decision": decision,
                "evidence": evidence,
            }
        )
    digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root.resolve()),
        "source_revision": repository_revision(root),
        "source_state_sha256": source_state_sha256(files),
        "registry": str(registry_path.resolve()),
        "registry_sha256": digest,
        "sensitivity": sensitivity,
        "excluded_parts": sorted(EXCLUDED_PARTS),
        "resource_budget": resource_budget(),
        "scanned_files": len(files),
        "profiles": rows,
    }


def print_survey(survey: dict[str, Any]) -> None:
    print(f"root: {survey['root']}")
    print(f"revision: {survey['source_revision'] or 'unversioned'}")
    print(f"profiles: {len(survey['profiles'])}; files: {survey['scanned_files']}")
    for row in survey["profiles"]:
        print(
            f"{row['stage']:14} {row['id']:36} {row['decision']:14} "
            f"score={row['score']}/{row['effective_threshold']} gate={row['gate']['passed']}"
        )


def initial_ledger(registry_path: Path, survey: dict[str, Any]) -> dict[str, Any]:
    _, profiles = load_registry(registry_path)
    surveyed = {row["id"]: row for row in survey.get("profiles", [])}
    rows = []
    for profile in profiles:
        survey_row = surveyed.get(profile["id"], {})
        status = "not-applicable" if survey_row.get("decision") == "not-applicable" else "unreviewed"
        evidence = [survey_row.get("gate", {})] if status == "not-applicable" else []
        rows.append(
            {
                "id": profile["id"],
                "status": status,
                "scope": [],
                "evidence": evidence,
                "findings": [],
                "disposition": [],
                "validation": [],
                "residuals": [],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "terminal_state": "incomplete",
        "registry_sha256": survey.get("registry_sha256"),
        "source_revision": survey.get("source_revision"),
        "source_state_sha256": survey.get("source_state_sha256"),
        "approved_exclusions": [],
        "profiles": rows,
    }


def validate_approved_exclusions(
    ledger: dict[str, Any], expected: set[str]
) -> set[str]:
    exclusions = ledger.get("approved_exclusions", [])
    if not isinstance(exclusions, list):
        raise ContractError("ledger approved_exclusions must be an array")
    approved: set[str] = set()
    for exclusion in exclusions:
        if not isinstance(exclusion, dict):
            raise ContractError("each approved exclusion must be an object")
        unknown = set(exclusion) - {"id", "approved_by", "reason", "impact"}
        if unknown:
            raise ContractError(f"approved exclusion has unknown fields {sorted(unknown)}")
        profile_id = require_text(exclusion, "id", "<exclusion>")
        require_text(exclusion, "approved_by", profile_id)
        require_text(exclusion, "reason", profile_id)
        require_text(exclusion, "impact", profile_id)
        if profile_id not in expected:
            raise ContractError(f"approved exclusion references unknown profile {profile_id}")
        if profile_id in approved:
            raise ContractError(f"duplicate approved exclusion: {profile_id}")
        approved.add(profile_id)
    return approved


def validate_ledger(registry_path: Path, ledger_path: Path, root: Path) -> None:
    if not root.is_dir():
        raise ContractError(f"target root is not a directory: {root}")
    _, registry_profiles = load_registry(registry_path)
    ledger = load_json(ledger_path)
    registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    if ledger.get("registry_sha256") != registry_digest:
        raise ContractError("ledger registry hash is stale or belongs to another registry")
    files = scan_files(root)
    current_source_state = source_state_sha256(files)
    if ledger.get("source_state_sha256") != current_source_state:
        raise ContractError("ledger source fingerprint is stale; re-survey and refresh receipts")
    terminal_state = ledger.get("terminal_state")
    if terminal_state not in TERMINAL_STATES:
        raise ContractError(f"ledger has unknown terminal_state: {terminal_state}")
    expected = {profile["id"] for profile in registry_profiles}
    approved = validate_approved_exclusions(ledger, expected)
    rows = ledger.get("profiles")
    if not isinstance(rows, list):
        raise ContractError("ledger profiles must be an array")
    actual = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(actual) != len(set(actual)):
        raise ContractError("ledger contains duplicate profile IDs")
    if set(actual) != expected:
        missing = sorted(expected - set(actual))
        extra = sorted(set(actual) - expected)
        raise ContractError(f"ledger profile mismatch; missing={missing} extra={extra}")
    for row in rows:
        profile_id = row["id"]
        status = row.get("status")
        if status not in STATUSES:
            raise ContractError(f"profile {profile_id}: unknown status {status}")
        for field in ("scope", "evidence", "findings", "disposition", "validation", "residuals"):
            if not isinstance(row.get(field), list):
                raise ContractError(f"profile {profile_id}: {field} must be an array")
        if status == "reviewed-clean" and (not row["scope"] or not row["evidence"]):
            raise ContractError(
                f"profile {profile_id}: reviewed-clean requires scope and evidence"
            )
        if status == "not-applicable" and not row["evidence"]:
            raise ContractError(f"profile {profile_id}: not-applicable requires evidence")
        if status == "fixed-verified" and (
            not row["scope"]
            or not row["findings"]
            or not row["disposition"]
            or not row["validation"]
        ):
            raise ContractError(
                f"profile {profile_id}: fixed-verified requires scope, findings, disposition, and validation"
            )
        if status in SUCCESS_STATUSES and row["residuals"]:
            raise ContractError(f"profile {profile_id}: successful status cannot have residuals")
        if status in {"deferred", "blocked"} and (
            not row["evidence"] or not row["disposition"] or not row["residuals"]
        ):
            raise ContractError(
                f"profile {profile_id}: {status} requires evidence, disposition, and residuals"
            )
        if profile_id in approved and status not in {"deferred", "blocked"}:
            raise ContractError(
                f"profile {profile_id}: approved exclusion must remain deferred or blocked"
            )
    non_success = [row["id"] for row in rows if row["status"] not in SUCCESS_STATUSES]
    if terminal_state == "complete" and non_success:
        raise ContractError(f"complete ledger has non-success profiles: {non_success}")
    if terminal_state == "complete" and approved:
        raise ContractError("complete ledger cannot contain approved exclusions")
    if terminal_state == "complete-with-approved-exclusions":
        if not approved:
            raise ContractError("complete-with-approved-exclusions requires an approval record")
        unapproved = sorted(set(non_success) - approved)
        if unapproved:
            raise ContractError(
                f"complete-with-approved-exclusions has unapproved open profiles: {unapproved}"
            )


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        procedure = root / "procedure.md"
        procedure.write_text("# Procedure\n", encoding="utf-8")
        source = root / "sample.rs"
        source.write_text("trait Child: Parent {}\n", encoding="utf-8")
        registry = root / "concerns.toml"
        registry.write_text(
            """schema_version = 1
[[profile]]
id = "design.traits"
skill = "design"
stage = "design"
procedure = "procedure.md"
evaluation = "qualitative"
screen = "always"
threshold = 2
gate = { kind = "any-file", globs = ["**/*.rs"] }
detectors = [{ kind = "literal", pattern = "trait ", weight = 1, globs = ["**/*.rs"] }]

[[profile]]
id = "design.cohesion"
skill = "design"
stage = "design"
procedure = "procedure.md"
evaluation = "qualitative"
screen = "always"
threshold = 1
gate = { kind = "any-file", globs = ["**/*.rs"] }
""",
            encoding="utf-8",
        )
        survey = build_survey(registry, root, "medium")
        assert survey["profiles"][0]["decision"] == "run"
        ledger = initial_ledger(registry, survey)
        ledger["terminal_state"] = "complete"
        for row in ledger["profiles"]:
            row.update(
                {
                    "status": "reviewed-clean",
                    "scope": ["sample.rs"],
                    "evidence": ["profile inventory"],
                }
            )
        ledger_path = root / ".ultra-out" / "ledger.json"
        ledger_path.parent.mkdir()
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        validate_ledger(registry, ledger_path, root)

        def expect_contract(candidate: dict[str, Any], message: str) -> None:
            ledger_path.write_text(json.dumps(candidate), encoding="utf-8")
            try:
                validate_ledger(registry, ledger_path, root)
            except ContractError as error:
                assert message in str(error)
            else:
                raise AssertionError(f"contract accepted invalid ledger: {message}")

        missing = json.loads(json.dumps(ledger))
        missing["profiles"].pop()
        expect_contract(missing, "ledger profile mismatch")

        false_complete = json.loads(json.dumps(ledger))
        false_complete["profiles"][0]["status"] = "unreviewed"
        expect_contract(false_complete, "complete ledger has non-success profiles")

        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        source.write_text("trait Child: Parent { fn changed(&self); }\n", encoding="utf-8")
        try:
            validate_ledger(registry, ledger_path, root)
        except ContractError as error:
            assert "source fingerprint is stale" in str(error)
        else:
            raise AssertionError("stale source fingerprint was accepted")
    print("ultra-system self-test: ok")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="ultra-system")
    commands = root.add_subparsers(dest="command", required=True)

    registry = commands.add_parser("registry")
    registry_commands = registry.add_subparsers(dest="registry_command", required=True)
    registry_validate = registry_commands.add_parser("validate")
    registry_validate.add_argument("--registry", type=Path, required=True)

    survey = commands.add_parser("survey")
    survey.add_argument("--registry", type=Path, required=True)
    survey.add_argument("--root", type=Path, required=True)
    survey.add_argument("--sensitivity", choices=("low", "medium", "high"), default="medium")
    survey.add_argument("--format", choices=("text", "json"), default="text")
    survey.add_argument("--output", type=Path)

    ledger = commands.add_parser("ledger")
    ledger_commands = ledger.add_subparsers(dest="ledger_command", required=True)
    ledger_init = ledger_commands.add_parser("init")
    ledger_init.add_argument("--registry", type=Path, required=True)
    ledger_init.add_argument("--survey", type=Path, required=True)
    ledger_init.add_argument("--output", type=Path, required=True)
    ledger_validate = ledger_commands.add_parser("validate")
    ledger_validate.add_argument("--registry", type=Path, required=True)
    ledger_validate.add_argument("--ledger", type=Path, required=True)
    ledger_validate.add_argument("--root", type=Path, required=True)

    commands.add_parser("self-test")
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "registry":
            _, profiles = load_registry(arguments.registry)
            print(f"registry valid: {len(profiles)} profiles")
        elif arguments.command == "survey":
            survey = build_survey(arguments.registry, arguments.root, arguments.sensitivity)
            if arguments.output:
                arguments.output.parent.mkdir(parents=True, exist_ok=True)
                arguments.output.write_text(json.dumps(survey, indent=2), encoding="utf-8")
            if arguments.format == "json":
                print(json.dumps(survey, indent=2))
            else:
                print_survey(survey)
        elif arguments.command == "ledger" and arguments.ledger_command == "init":
            survey = load_json(arguments.survey)
            ledger = initial_ledger(arguments.registry, survey)
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
            print(f"ledger initialized: {arguments.output}")
        elif arguments.command == "ledger":
            validate_ledger(arguments.registry, arguments.ledger, arguments.root)
            print("ledger valid")
        else:
            run_self_test()
    except ContractError as error:
        print(f"ultra-system contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
