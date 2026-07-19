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
import uuid
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3
EVALUATIONS = {"quantitative", "indicative", "qualitative"}
SCREENS = {"always", "signal"}
RUN_MODES = {"modernize", "compatibility"}
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
    "obligations",
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
OBLIGATION_STATUSES = {
    "satisfied",
    "not-applicable",
    "deferred",
    "blocked",
    "unreviewed",
}
OBLIGATION_SUCCESS_STATUSES = {"satisfied", "not-applicable"}
TERMINAL_STATES = {
    "complete",
    "complete-with-approved-exclusions",
    "incomplete",
    "blocked",
    "incomplete-convergence-cap",
}
SUCCESS_TERMINAL_STATES = {"complete", "complete-with-approved-exclusions"}
MODEL_CLASSES = {"frontier", "efficient"}
OPENAI_MODEL_CLASSES = {
    "gpt-5.6-sol": "frontier",
    "gpt-5.5": "frontier",
    "gpt-5.6-luna": "efficient",
    "gpt-5.3-codex-spark": "efficient",
}
MODEL_EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max", "ultra")
MODEL_EFFORTS = set(MODEL_EFFORT_LEVELS)
EFFORT_ORDER = {effort: index for index, effort in enumerate(MODEL_EFFORT_LEVELS)}
BUILD_STATUSES = {"completed", "blocked", "replan-required"}
REVIEW_VERDICTS = {"approved", "changes-requested", "blocked"}
ACTOR_FIELDS = {
    "provider",
    "model_class",
    "model",
    "effort",
    "invocation_id",
    "context_id",
}
PLAN_FIELDS = {
    "schema_version",
    "artifact",
    "registry_sha256",
    "survey_sha256",
    "source_revision",
    "source_state_sha256",
    "run_mode",
    "mode_override",
    "planner",
    "profile_ids",
    "work_packages",
    "resource_budget",
}
PLAN_PACKAGE_FIELDS = {
    "id",
    "profile_ids",
    "depends_on",
    "scope",
    "objectives",
    "breaking_changes",
    "migration",
    "validation",
    "risks",
}
BUILD_FIELDS = {
    "schema_version",
    "artifact",
    "plan_sha256",
    "builder",
    "source_revision",
    "source_state_sha256",
    "work_packages",
}
BUILD_PACKAGE_FIELDS = {
    "id",
    "status",
    "profile_ids",
    "changes",
    "evidence",
    "validation",
    "residuals",
}
REVIEW_FIELDS = {
    "schema_version",
    "artifact",
    "plan_sha256",
    "build_sha256",
    "ledger_sha256",
    "evidence_manifest_sha256",
    "source_revision",
    "source_state_sha256",
    "reviewer",
    "profile_ids",
    "verdict",
    "findings",
    "validation",
    "residuals",
}
EVIDENCE_MANIFEST_FIELDS = {"schema_version", "artifact", "files"}
EVIDENCE_ENTRY_FIELDS = {"path", "sha256"}
SURVEY_FIELDS = {
    "schema_version",
    "root",
    "source_revision",
    "source_state_sha256",
    "registry",
    "registry_sha256",
    "sensitivity",
    "run_mode",
    "mode_override",
    "excluded_parts",
    "resource_budget",
    "scanned_files",
    "profiles",
}
SURVEY_PROFILE_FIELDS = {
    "id",
    "skill",
    "stage",
    "evaluation",
    "procedure",
    "gate",
    "score",
    "effective_threshold",
    "decision",
    "evidence",
    "obligations",
}
SCORE_HISTORY_FIELDS = {
    "schema_version",
    "artifact",
    "registry_sha256",
    "plan_sha256",
    "entries",
}
SCORE_ENTRY_FIELDS = {
    "stage",
    "source_revision",
    "source_state_sha256",
    "survey_sha256",
}
RECEIPT_FIELDS = {
    "schema_version",
    "artifact",
    "stage",
    "plan_sha256",
    "source_state_sha256",
    "profile_ids",
    "findings",
    "changes",
    "validation",
    "residuals",
}
FINAL_VALIDATION_FIELDS = {
    "schema_version",
    "artifact",
    "plan_sha256",
    "source_revision",
    "source_state_sha256",
    "gates",
}
FINAL_GATE_FIELDS = {"name", "status", "evidence"}
REQUIRED_EVIDENCE_PATHS = {
    "survey.initial.json",
    "profile-ledger.json",
    "score-history.json",
    "final-validation.json",
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


def file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ContractError(f"cannot hash {path}: {error}") from error


def require_sha256(value: Any, context: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ContractError(f"{context} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ContractError(f"{context} must be a SHA-256 digest") from error
    return value


def require_fields(value: dict[str, Any], expected: set[str], context: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        raise ContractError(
            f"{context}: field mismatch; missing={missing} unknown={unknown}"
        )


def require_string_list(
    value: dict[str, Any], field: str, context: str, *, non_empty: bool = False
) -> list[str]:
    items = value.get(field)
    if (
        not isinstance(items, list)
        or not all(isinstance(item, str) and item.strip() for item in items)
        or len(items) != len(set(items))
        or (non_empty and not items)
    ):
        qualifier = "non-empty unique " if non_empty else "unique "
        raise ContractError(f"{context}: {field} must be a {qualifier}string array")
    return items


def validate_actor(value: Any, context: str, expected_class: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ContractError(f"{context} must be an object")
    require_fields(value, ACTOR_FIELDS, context)
    actor = {
        field: require_text(value, field, context)
        for field in (
            "provider",
            "model_class",
            "model",
            "effort",
            "invocation_id",
            "context_id",
        )
    }
    model_class = actor["model_class"]
    effort = actor["effort"]
    if actor["provider"] != "openai":
        raise ContractError(f"{context}: unsupported provider {actor['provider']}")
    for field in ("invocation_id", "context_id"):
        try:
            uuid.UUID(actor[field])
        except ValueError as error:
            raise ContractError(f"{context}: {field} must be a runtime UUID") from error
    if model_class not in MODEL_CLASSES:
        raise ContractError(f"{context}: unknown model_class {model_class}")
    if model_class != expected_class:
        raise ContractError(f"{context}: model_class must be {expected_class}")
    known_class = OPENAI_MODEL_CLASSES.get(actor["model"])
    if known_class is None:
        raise ContractError(f"{context}: unknown OpenAI model {actor['model']}")
    if known_class != model_class:
        raise ContractError(
            f"{context}: OpenAI model {actor['model']} is classified as {known_class}"
        )
    if effort not in MODEL_EFFORTS:
        raise ContractError(f"{context}: unknown effort {effort}")
    return actor


def load_registry(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        raw = path.read_bytes()
        registry = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ContractError(f"cannot read registry {path}: {error}") from error
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"registry schema_version must be {SCHEMA_VERSION}")
    if registry.get("default_mode") not in RUN_MODES:
        raise ContractError(f"registry default_mode must be one of {sorted(RUN_MODES)}")
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
            raise ContractError(
                f"profile {profile_id}: unknown evaluation {profile['evaluation']}"
            )
        if profile["screen"] not in SCREENS:
            raise ContractError(
                f"profile {profile_id}: unknown screen {profile['screen']}"
            )
        if profile["evaluation"] == "qualitative" and profile["screen"] != "always":
            raise ContractError(
                f"profile {profile_id}: qualitative profiles must always screen"
            )
        procedure = (registry_path.parent / profile["procedure"]).resolve()
        if not procedure.is_file():
            raise ContractError(f"profile {profile_id}: missing procedure {procedure}")
        gate = profile.get("gate")
        if not isinstance(gate, dict) or gate.get("kind") not in GATE_KINDS:
            raise ContractError(
                f"profile {profile_id}: gate must use one of {sorted(GATE_KINDS)}"
            )
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
            raise ContractError(
                f"profile {profile_id}: threshold must be a positive integer"
            )
        detectors = profile.get("detectors", [])
        if not isinstance(detectors, list):
            raise ContractError(f"profile {profile_id}: detectors must be an array")
        if profile["screen"] == "signal" and not detectors:
            raise ContractError(
                f"profile {profile_id}: signal screening requires detectors"
            )
        for detector in detectors:
            validate_detector(profile_id, detector)
        obligations = profile.get("obligations", [])
        if (
            not isinstance(obligations, list)
            or not all(isinstance(item, str) and item.strip() for item in obligations)
            or len(obligations) != len(set(obligations))
        ):
            raise ContractError(
                f"profile {profile_id}: obligations must be unique non-empty strings"
            )


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
    if (
        not isinstance(globs, list)
        or not globs
        or not all(isinstance(item, str) for item in globs)
    ):
        raise ContractError(f"profile {profile_id}: detector requires string globs")
    if detector["kind"] == "literal":
        if not isinstance(detector.get("pattern"), str) or not detector["pattern"]:
            raise ContractError(
                f"profile {profile_id}: literal detector requires pattern"
            )
    elif not isinstance(detector.get("lines"), int) or detector["lines"] < 0:
        raise ContractError(
            f"profile {profile_id}: line detector requires non-negative lines"
        )


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
            raise ContractError(
                f"cannot fingerprint source file {path}: {error}"
            ) from error
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


def validate_survey_artifact(
    registry_path: Path, survey_path: Path, root: Path | None = None
) -> dict[str, Any]:
    registry, profiles = load_registry(registry_path)
    survey = load_json(survey_path)
    require_fields(survey, SURVEY_FIELDS, "survey")
    if survey.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"survey schema_version must be {SCHEMA_VERSION}")
    if survey.get("registry_sha256") != file_sha256(registry_path):
        raise ContractError(
            "survey registry hash is stale or belongs to another registry"
        )
    require_sha256(survey.get("source_state_sha256"), "survey source_state_sha256")
    if survey.get("source_revision") is not None and not isinstance(
        survey.get("source_revision"), str
    ):
        raise ContractError("survey source_revision must be text or null")
    if not isinstance(survey.get("root"), str) or not survey["root"]:
        raise ContractError("survey root must be non-empty text")
    if survey.get("sensitivity") not in {"low", "medium", "high"}:
        raise ContractError("survey sensitivity is invalid")
    run_mode = survey.get("run_mode")
    if run_mode not in RUN_MODES:
        raise ContractError(f"survey has unknown run_mode: {run_mode}")
    validate_mode_override(survey, registry["default_mode"], run_mode)
    if not isinstance(survey.get("excluded_parts"), list):
        raise ContractError("survey excluded_parts must be an array")
    if (
        not isinstance(survey.get("resource_budget"), dict)
        or not survey["resource_budget"]
    ):
        raise ContractError("survey resource_budget must be a non-empty object")
    if not isinstance(survey.get("scanned_files"), int) or survey["scanned_files"] < 0:
        raise ContractError("survey scanned_files must be a non-negative integer")
    rows = survey.get("profiles")
    if not isinstance(rows, list):
        raise ContractError("survey profiles must be an array")
    expected_ids = [profile["id"] for profile in profiles]
    if len(rows) != len(profiles):
        raise ContractError("survey profile count must exactly match the registry")
    actual_ids: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ContractError("every survey profile must be an object")
        require_fields(row, SURVEY_PROFILE_FIELDS, "survey profile")
        profile_id = require_text(row, "id", "survey profile")
        actual_ids.append(profile_id)
        profile = profiles[index]
        for field in ("skill", "stage", "evaluation", "procedure"):
            if row.get(field) != profile.get(field):
                raise ContractError(
                    f"survey profile {profile_id}: {field} differs from registry"
                )
        if row.get("obligations") != profile.get("obligations", []):
            raise ContractError(
                f"survey profile {profile_id}: obligations differ from registry"
            )
        if row.get("decision") not in {"run", "screened-clean", "not-applicable"}:
            raise ContractError(f"survey profile {profile_id}: invalid decision")
        for field in ("score", "effective_threshold"):
            if not isinstance(row.get(field), int) or row[field] < 0:
                raise ContractError(
                    f"survey profile {profile_id}: {field} must be non-negative"
                )
        for field in ("evidence", "obligations"):
            if not isinstance(row.get(field), list):
                raise ContractError(
                    f"survey profile {profile_id}: {field} must be an array"
                )
        gate = row.get("gate")
        if (
            not isinstance(gate, dict)
            or not isinstance(gate.get("passed"), bool)
            or not isinstance(gate.get("matched_files"), int)
            or gate["matched_files"] < 0
        ):
            raise ContractError(f"survey profile {profile_id}: malformed gate")
        expected_gate_passed = (
            True if profile["gate"]["kind"] == "always" else gate["matched_files"] > 0
        )
        if gate["passed"] != expected_gate_passed:
            raise ContractError(
                f"survey profile {profile_id}: gate result contradicts matched files"
            )
        if (
            profile["gate"]["kind"] == "always"
            and gate["matched_files"] != survey["scanned_files"]
        ):
            raise ContractError(
                f"survey profile {profile_id}: always-gate file count is inconsistent"
            )
        threshold = effective_threshold(
            profile.get("threshold", 1), survey["sensitivity"]
        )
        if row["effective_threshold"] != threshold:
            raise ContractError(
                f"survey profile {profile_id}: threshold differs from registry"
            )
        expected_decision = "not-applicable"
        if gate["passed"]:
            expected_decision = (
                "run"
                if profile["screen"] == "always" or row["score"] >= threshold
                else "screened-clean"
            )
        if row["decision"] != expected_decision:
            raise ContractError(
                f"survey profile {profile_id}: decision contradicts gate and registry"
            )
        evidence = row["evidence"]
        detectors = profile.get("detectors", [])
        if len(evidence) != len(detectors):
            raise ContractError(
                f"survey profile {profile_id}: detector evidence count differs from registry"
            )
        evidence_score = 0
        for item, detector in zip(evidence, detectors, strict=True):
            if (
                not isinstance(item, dict)
                or set(item) != {"kind", "pattern", "count", "score", "matches"}
                or item.get("kind") != detector["kind"]
                or item.get("pattern") != detector.get("pattern")
                or not isinstance(item.get("count"), int)
                or item["count"] < 0
                or not isinstance(item.get("score"), int)
                or item["score"] < 0
                or not isinstance(item.get("matches"), list)
            ):
                raise ContractError(
                    f"survey profile {profile_id}: malformed detector evidence"
                )
            if item["score"] != item["count"] * detector.get("weight", 1):
                raise ContractError(
                    f"survey profile {profile_id}: detector score contradicts count"
                )
            if len(item["matches"]) > min(item["count"], 25):
                raise ContractError(
                    f"survey profile {profile_id}: detector matches exceed count"
                )
            evidence_score += item["score"]
        if evidence_score != row["score"]:
            raise ContractError(
                f"survey profile {profile_id}: score differs from detector evidence"
            )
    if actual_ids != expected_ids:
        raise ContractError("survey profile IDs must exactly match registry order")
    if root is not None:
        override = survey.get("mode_override") or {}
        expected_survey = build_survey(
            registry_path,
            root,
            survey["sensitivity"],
            survey["run_mode"],
            override.get("approved_by"),
            override.get("reason"),
        )
        for field in (
            "root",
            "source_revision",
            "source_state_sha256",
            "registry_sha256",
            "sensitivity",
            "run_mode",
            "mode_override",
            "excluded_parts",
            "scanned_files",
            "profiles",
        ):
            if survey.get(field) != expected_survey.get(field):
                raise ContractError(
                    f"survey {field} differs from a deterministic target scan"
                )
    return survey


def validate_plan_artifact(
    registry_path: Path, plan_path: Path, root: Path | None = None
) -> dict[str, Any]:
    registry, profiles = load_registry(registry_path)
    plan = load_json(plan_path)
    require_fields(plan, PLAN_FIELDS, "plan")
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"plan schema_version must be {SCHEMA_VERSION}")
    if plan.get("artifact") != "ultra-plan":
        raise ContractError("plan artifact must be ultra-plan")
    if plan.get("registry_sha256") != file_sha256(registry_path):
        raise ContractError(
            "plan registry hash is stale or belongs to another registry"
        )
    survey_path = plan_path.parent / "survey.initial.json"
    if plan.get("survey_sha256") != file_sha256(survey_path):
        raise ContractError("plan survey hash is stale or missing")
    survey = validate_survey_artifact(registry_path, survey_path, root)
    run_mode = plan.get("run_mode")
    if run_mode not in RUN_MODES:
        raise ContractError(f"plan has unknown run_mode: {run_mode}")
    validate_mode_override(plan, registry["default_mode"], run_mode)
    planner = validate_actor(plan.get("planner"), "plan planner", "frontier")
    if EFFORT_ORDER[planner["effort"]] < EFFORT_ORDER["high"]:
        raise ContractError("plan planner effort must be high or greater")
    expected_order = [profile["id"] for profile in profiles]
    profile_ids = require_string_list(plan, "profile_ids", "plan", non_empty=True)
    if profile_ids != expected_order:
        raise ContractError("plan profile_ids must exactly match registry order")
    budget = plan.get("resource_budget")
    if not isinstance(budget, dict) or not budget:
        raise ContractError("plan resource_budget must be a non-empty object")
    source_state = require_sha256(
        plan.get("source_state_sha256"), "plan source_state_sha256"
    )
    if plan.get("source_revision") is not None and not isinstance(
        plan.get("source_revision"), str
    ):
        raise ContractError("plan source_revision must be text or null")
    if root is not None and plan.get("source_revision") != repository_revision(root):
        raise ContractError("plan source_revision differs from the target repository")
    for field in (
        "source_revision",
        "source_state_sha256",
        "run_mode",
        "mode_override",
    ):
        if plan.get(field) != survey.get(field):
            raise ContractError(f"plan {field} differs from the initial survey")
    if plan.get("resource_budget") != survey.get("resource_budget"):
        raise ContractError("plan resource_budget differs from the initial survey")

    packages = plan.get("work_packages")
    if not isinstance(packages, list) or not packages:
        raise ContractError("plan work_packages must be a non-empty array")
    package_ids: list[str] = []
    covered_profiles: list[str] = []
    dependencies: dict[str, list[str]] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise ContractError("every plan work package must be an object")
        package_id = require_text(package, "id", "plan work package")
        require_fields(package, PLAN_PACKAGE_FIELDS, f"plan package {package_id}")
        package_ids.append(package_id)
        package_profiles = require_string_list(
            package, "profile_ids", f"plan package {package_id}", non_empty=True
        )
        covered_profiles.extend(package_profiles)
        dependencies[package_id] = require_string_list(
            package, "depends_on", f"plan package {package_id}"
        )
        for field in ("scope", "objectives", "validation"):
            require_string_list(
                package, field, f"plan package {package_id}", non_empty=True
            )
        for field in ("breaking_changes", "migration", "risks"):
            require_string_list(package, field, f"plan package {package_id}")
    if len(package_ids) != len(set(package_ids)):
        raise ContractError("plan contains duplicate work package IDs")
    if len(covered_profiles) != len(set(covered_profiles)):
        raise ContractError("plan assigns a profile to more than one work package")
    if set(covered_profiles) != set(expected_order):
        missing = sorted(set(expected_order) - set(covered_profiles))
        extra = sorted(set(covered_profiles) - set(expected_order))
        raise ContractError(
            f"plan work package profile mismatch; missing={missing} extra={extra}"
        )
    known_packages = set(package_ids)
    for package_id, required in dependencies.items():
        unknown = sorted(set(required) - known_packages)
        if package_id in required:
            raise ContractError(f"plan package {package_id} cannot depend on itself")
        if unknown:
            raise ContractError(
                f"plan package {package_id} has unknown dependencies {unknown}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(package_id: str) -> None:
        if package_id in visiting:
            raise ContractError(f"plan work package dependency cycle at {package_id}")
        if package_id in visited:
            return
        visiting.add(package_id)
        for dependency in dependencies[package_id]:
            visit(dependency)
        visiting.remove(package_id)
        visited.add(package_id)

    for package_id in package_ids:
        visit(package_id)
    if root is not None:
        if not root.is_dir():
            raise ContractError(f"target root is not a directory: {root}")
        if source_state_sha256(scan_files(root)) != source_state:
            raise ContractError(
                "plan source fingerprint is stale; re-plan before source mutation"
            )
    return plan


def validate_build_artifact(
    registry_path: Path, plan_path: Path, build_path: Path, root: Path
) -> dict[str, Any]:
    if not root.is_dir():
        raise ContractError(f"target root is not a directory: {root}")
    plan = validate_plan_artifact(registry_path, plan_path)
    build = load_json(build_path)
    require_fields(build, BUILD_FIELDS, "build")
    if build.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"build schema_version must be {SCHEMA_VERSION}")
    if build.get("artifact") != "ultra-build":
        raise ContractError("build artifact must be ultra-build")
    if build.get("plan_sha256") != file_sha256(plan_path):
        raise ContractError("build plan hash is stale or belongs to another plan")
    builder = validate_actor(build.get("builder"), "build builder", "efficient")
    planner = plan["planner"]
    if (builder["provider"], builder["model"]) == (
        planner["provider"],
        planner["model"],
    ):
        raise ContractError("build builder must use a different model from the planner")
    if builder["invocation_id"] == planner["invocation_id"]:
        raise ContractError(
            "build builder must use a different invocation from the planner"
        )
    if builder["context_id"] == planner["context_id"]:
        raise ContractError(
            "build builder must use a different context from the planner"
        )
    if build.get("source_revision") is not None and not isinstance(
        build.get("source_revision"), str
    ):
        raise ContractError("build source_revision must be text or null")
    if build.get("source_revision") != repository_revision(root):
        raise ContractError("build source_revision differs from the target repository")
    current_source_state = source_state_sha256(scan_files(root))
    if build.get("source_state_sha256") != current_source_state:
        raise ContractError(
            "build source fingerprint is stale; refresh the build receipt"
        )

    plan_packages = {package["id"]: package for package in plan["work_packages"]}
    packages = build.get("work_packages")
    if not isinstance(packages, list):
        raise ContractError("build work_packages must be an array")
    actual_ids = [
        package.get("id") for package in packages if isinstance(package, dict)
    ]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(plan_packages):
        raise ContractError("build work package IDs must exactly match the plan")
    for package in packages:
        if not isinstance(package, dict):
            raise ContractError("every build work package must be an object")
        package_id = package["id"]
        require_fields(package, BUILD_PACKAGE_FIELDS, f"build package {package_id}")
        status = package.get("status")
        if status not in BUILD_STATUSES:
            raise ContractError(f"build package {package_id}: unknown status {status}")
        package_profiles = require_string_list(
            package, "profile_ids", f"build package {package_id}", non_empty=True
        )
        if package_profiles != plan_packages[package_id]["profile_ids"]:
            raise ContractError(
                f"build package {package_id}: profile_ids differ from the plan"
            )
        require_string_list(package, "changes", f"build package {package_id}")
        require_string_list(
            package, "evidence", f"build package {package_id}", non_empty=True
        )
        validation = require_string_list(
            package, "validation", f"build package {package_id}"
        )
        residuals = require_string_list(
            package, "residuals", f"build package {package_id}"
        )
        if status == "completed" and (not validation or residuals):
            raise ContractError(
                f"build package {package_id}: completed requires validation and no residuals"
            )
        if status in {"blocked", "replan-required"} and not residuals:
            raise ContractError(
                f"build package {package_id}: {status} requires residuals"
            )
    return build


def validate_evidence_manifest(
    output: Path,
    expected_sha256: Any,
    registry_path: Path,
    plan_path: Path,
    build: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    manifest_path = output / "evidence-manifest.json"
    if expected_sha256 != file_sha256(manifest_path):
        raise ContractError("review evidence manifest hash is stale or missing")
    manifest = load_json(manifest_path)
    require_fields(manifest, EVIDENCE_MANIFEST_FIELDS, "evidence manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(
            f"evidence manifest schema_version must be {SCHEMA_VERSION}"
        )
    if manifest.get("artifact") != "ultra-evidence-manifest":
        raise ContractError(
            "evidence manifest artifact must be ultra-evidence-manifest"
        )
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ContractError("evidence manifest files must be a non-empty array")
    actual_paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContractError("every evidence manifest entry must be an object")
        require_fields(entry, EVIDENCE_ENTRY_FIELDS, "evidence manifest entry")
        relative = require_text(entry, "path", "evidence manifest entry")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ContractError(f"evidence manifest path escapes output: {relative}")
        if relative == "evidence-manifest.json":
            raise ContractError("evidence manifest cannot hash itself")
        actual_paths.append(relative)
        if entry.get("sha256") != file_sha256(output / relative_path):
            raise ContractError(f"evidence manifest hash mismatch: {relative}")
    if len(actual_paths) != len(set(actual_paths)):
        raise ContractError("evidence manifest contains duplicate paths")
    missing = sorted(REQUIRED_EVIDENCE_PATHS - set(actual_paths))
    if missing:
        raise ContractError(f"evidence manifest is missing required files: {missing}")
    receipt_paths = {
        path.relative_to(output).as_posix()
        for path in (output / "receipts").glob("*.json")
        if path.is_file()
    }
    manifested_receipts = {
        path for path in actual_paths if path.startswith("receipts/")
    }
    if not receipt_paths:
        raise ContractError("evidence manifest requires at least one stage receipt")
    if manifested_receipts != receipt_paths:
        raise ContractError(
            "evidence manifest receipt set must exactly match receipts/*.json"
        )

    plan = load_json(plan_path)
    survey_path = output / "survey.initial.json"
    survey = validate_survey_artifact(registry_path, survey_path)
    if plan.get("survey_sha256") != file_sha256(survey_path):
        raise ContractError("evidence survey differs from the frozen plan")

    history = load_json(output / "score-history.json")
    require_fields(history, SCORE_HISTORY_FIELDS, "score history")
    if history.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"score history schema_version must be {SCHEMA_VERSION}")
    if history.get("artifact") != "ultra-score-history":
        raise ContractError("score history artifact must be ultra-score-history")
    if history.get("registry_sha256") != file_sha256(registry_path):
        raise ContractError("score history registry hash is stale")
    if history.get("plan_sha256") != file_sha256(plan_path):
        raise ContractError("score history plan hash is stale")
    history_entries = history.get("entries")
    if not isinstance(history_entries, list) or not history_entries:
        raise ContractError("score history entries must be a non-empty array")
    history_stages: list[str] = []
    for entry in history_entries:
        if not isinstance(entry, dict):
            raise ContractError("every score history entry must be an object")
        require_fields(entry, SCORE_ENTRY_FIELDS, "score history entry")
        history_stages.append(require_text(entry, "stage", "score history entry"))
        require_sha256(
            entry.get("source_state_sha256"),
            "score history entry source_state_sha256",
        )
        if entry.get("survey_sha256") is not None:
            require_sha256(entry.get("survey_sha256"), "score history survey_sha256")
        if entry.get("source_revision") is not None and not isinstance(
            entry.get("source_revision"), str
        ):
            raise ContractError("score history source_revision must be text or null")
    if len(history_stages) != len(set(history_stages)):
        raise ContractError("score history contains duplicate stages")
    if history_stages[0] != "initial" or history_stages[-1] != "final":
        raise ContractError("score history must start at initial and end at final")
    if any(entry.get("survey_sha256") is not None for entry in history_entries[1:]):
        raise ContractError("only the initial score-history entry may bind a survey")
    first_history = history_entries[0]
    if first_history.get("source_state_sha256") != survey[
        "source_state_sha256"
    ] or first_history.get("survey_sha256") != file_sha256(survey_path):
        raise ContractError(
            "score history initial entry differs from the initial survey"
        )
    if first_history.get("source_revision") != survey["source_revision"]:
        raise ContractError("score history initial revision differs from the survey")
    for entry in history_entries[1:]:
        if entry.get("source_state_sha256") != build["source_state_sha256"]:
            raise ContractError(
                "post-build score-history entries must bind the final build source"
            )
        if entry.get("source_revision") != build["source_revision"]:
            raise ContractError(
                "post-build score-history revisions must match the final build"
            )
    if history_entries[-1].get("source_state_sha256") != build["source_state_sha256"]:
        raise ContractError("score history final entry differs from the build source")
    if history_entries[-1].get("source_revision") != build["source_revision"]:
        raise ContractError("score history final revision differs from the build")

    registry_profiles = load_registry(registry_path)[1]
    expected_profiles = {profile["id"] for profile in registry_profiles}
    profiles_by_id = {profile["id"]: profile for profile in registry_profiles}
    covered_profiles: list[str] = []
    receipt_stages: list[str] = []
    history_by_stage = {entry["stage"]: entry for entry in history_entries}
    for relative in sorted(receipt_paths):
        receipt = load_json(output / relative)
        require_fields(receipt, RECEIPT_FIELDS, f"receipt {relative}")
        if receipt.get("schema_version") != SCHEMA_VERSION:
            raise ContractError(f"receipt {relative}: invalid schema_version")
        if receipt.get("artifact") != "ultra-stage-receipt":
            raise ContractError(f"receipt {relative}: invalid artifact")
        stage = require_text(receipt, "stage", f"receipt {relative}")
        receipt_stages.append(stage)
        if Path(relative).stem != stage:
            raise ContractError(
                f"receipt {relative}: filename must match receipt stage {stage}"
            )
        if receipt.get("plan_sha256") != file_sha256(plan_path):
            raise ContractError(f"receipt {relative}: stale plan hash")
        receipt_source_state = require_sha256(
            receipt.get("source_state_sha256"),
            f"receipt {relative} source_state_sha256",
        )
        if (
            stage not in history_by_stage
            or history_by_stage[stage]["source_state_sha256"] != receipt_source_state
        ):
            raise ContractError(
                f"receipt {relative}: source state is absent from score history"
            )
        receipt_profiles = require_string_list(
            receipt, "profile_ids", f"receipt {relative}", non_empty=True
        )
        for profile_id in receipt_profiles:
            profile = profiles_by_id.get(profile_id)
            if profile is None or profile["stage"] != stage:
                raise ContractError(
                    f"receipt {relative}: profile {profile_id} is not owned by stage {stage}"
                )
        covered_profiles.extend(receipt_profiles)
        for field in ("findings", "changes", "residuals"):
            require_string_list(receipt, field, f"receipt {relative}")
        require_string_list(
            receipt, "validation", f"receipt {relative}", non_empty=True
        )
    if len(receipt_stages) != len(set(receipt_stages)):
        raise ContractError("stage receipts contain duplicate stages")
    if set(receipt_stages) != set(history_stages[1:-1]):
        raise ContractError(
            "score-history intermediate stages must exactly match stage receipts"
        )
    if len(covered_profiles) != len(set(covered_profiles)):
        raise ContractError("stage receipts cover a profile more than once")
    if set(covered_profiles) != expected_profiles:
        raise ContractError(
            "stage receipts must cover every registry profile exactly once"
        )

    final_validation = load_json(output / "final-validation.json")
    require_fields(final_validation, FINAL_VALIDATION_FIELDS, "final validation")
    if final_validation.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"final validation schema_version must be {SCHEMA_VERSION}")
    if final_validation.get("artifact") != "ultra-final-validation":
        raise ContractError("final validation artifact must be ultra-final-validation")
    if final_validation.get("plan_sha256") != file_sha256(plan_path):
        raise ContractError("final validation plan hash is stale")
    if final_validation.get("source_state_sha256") != source_state_sha256(
        scan_files(root)
    ):
        raise ContractError("final validation source fingerprint is stale")
    if final_validation.get("source_revision") is not None and not isinstance(
        final_validation.get("source_revision"), str
    ):
        raise ContractError("final validation source_revision must be text or null")
    if final_validation.get("source_revision") != repository_revision(root):
        raise ContractError(
            "final validation revision differs from the target repository"
        )
    gates = final_validation.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ContractError("final validation gates must be a non-empty array")
    gate_names: list[str] = []
    for gate in gates:
        if not isinstance(gate, dict):
            raise ContractError("every final validation gate must be an object")
        require_fields(gate, FINAL_GATE_FIELDS, "final validation gate")
        gate_names.append(require_text(gate, "name", "final validation gate"))
        if gate.get("status") != "passed":
            raise ContractError(
                f"final validation gate {gate_names[-1]} must have passed"
            )
        require_string_list(
            gate, "evidence", f"final validation gate {gate_names[-1]}", non_empty=True
        )
    if len(gate_names) != len(set(gate_names)):
        raise ContractError("final validation contains duplicate gate names")
    return manifest


def validate_review_artifact(
    registry_path: Path,
    plan_path: Path,
    build_path: Path,
    review_path: Path,
    ledger_path: Path,
    root: Path,
) -> dict[str, Any]:
    plan = validate_plan_artifact(registry_path, plan_path)
    build = validate_build_artifact(registry_path, plan_path, build_path, root)
    review = load_json(review_path)
    require_fields(review, REVIEW_FIELDS, "review")
    if review.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"review schema_version must be {SCHEMA_VERSION}")
    if review.get("artifact") != "ultra-review":
        raise ContractError("review artifact must be ultra-review")
    if review.get("plan_sha256") != file_sha256(plan_path):
        raise ContractError("review plan hash is stale or belongs to another plan")
    if review.get("build_sha256") != file_sha256(build_path):
        raise ContractError("review build hash is stale or belongs to another build")
    if review.get("ledger_sha256") != file_sha256(ledger_path):
        raise ContractError("review ledger hash is stale or belongs to another ledger")
    validate_evidence_manifest(
        review_path.parent,
        review.get("evidence_manifest_sha256"),
        registry_path,
        plan_path,
        build,
        root,
    )
    reviewer = validate_actor(review.get("reviewer"), "review reviewer", "frontier")
    planner = plan["planner"]
    builder = build["builder"]
    if (reviewer["provider"], reviewer["model"]) != (
        planner["provider"],
        planner["model"],
    ):
        raise ContractError(
            "reviewer provider and model must exactly match the planner"
        )
    if reviewer["invocation_id"] in {
        planner["invocation_id"],
        builder["invocation_id"],
    }:
        raise ContractError("reviewer must use an independent invocation")
    if reviewer["context_id"] in {
        planner["context_id"],
        builder["context_id"],
    }:
        raise ContractError("reviewer must use an independent context")
    if EFFORT_ORDER[reviewer["effort"]] > EFFORT_ORDER[planner["effort"]]:
        raise ContractError("reviewer effort cannot exceed planner effort")
    expected_profiles = [profile["id"] for profile in load_registry(registry_path)[1]]
    if (
        require_string_list(review, "profile_ids", "review", non_empty=True)
        != expected_profiles
    ):
        raise ContractError("review profile_ids must exactly match registry order")
    verdict = review.get("verdict")
    if verdict not in REVIEW_VERDICTS:
        raise ContractError(f"review has unknown verdict: {verdict}")
    findings = require_string_list(review, "findings", "review")
    validation = require_string_list(review, "validation", "review")
    residuals = require_string_list(review, "residuals", "review")
    current_source_state = source_state_sha256(scan_files(root))
    if review.get("source_state_sha256") != current_source_state:
        raise ContractError(
            "review source fingerprint is stale; re-review the final source"
        )
    if review.get("source_revision") is not None and not isinstance(
        review.get("source_revision"), str
    ):
        raise ContractError("review source_revision must be text or null")
    if review.get("source_revision") != repository_revision(root):
        raise ContractError("review source_revision differs from the target repository")
    incomplete_build = [
        package["id"]
        for package in build["work_packages"]
        if package["status"] != "completed"
    ]
    if verdict == "approved" and (
        incomplete_build or findings or not validation or residuals
    ):
        raise ContractError(
            "approved review requires a completed build, validation, and no open findings or residuals"
        )
    if verdict != "approved" and not residuals:
        raise ContractError(f"review verdict {verdict} requires residuals")
    return review


def selected_files(
    files: list[tuple[str, Path]], globs: list[str]
) -> list[tuple[str, Path]]:
    return [
        item for item in files if any(matches_glob(item[0], glob) for glob in globs)
    ]


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
                    occurrences = sum(
                        line.count(detector["pattern"]) for line in source
                    )
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
            ) or (detector["kind"] == "file-lines-lt" and lines < detector["lines"])
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


def build_survey(
    registry_path: Path,
    root: Path,
    sensitivity: str,
    mode: str | None = None,
    mode_approved_by: str | None = None,
    mode_reason: str | None = None,
) -> dict[str, Any]:
    if not root.is_dir():
        raise ContractError(f"target root is not a directory: {root}")
    registry, profiles = load_registry(registry_path)
    run_mode = mode or registry["default_mode"]
    if run_mode not in RUN_MODES:
        raise ContractError(f"run mode must be one of {sorted(RUN_MODES)}")
    mode_override: dict[str, str] | None = None
    if run_mode != registry["default_mode"]:
        if not mode_approved_by or not mode_reason:
            raise ContractError(
                "overriding registry default_mode requires --mode-approved-by and --mode-reason"
            )
        mode_override = {
            "approved_by": mode_approved_by,
            "reason": mode_reason,
        }
    files = scan_files(root)
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        gate = profile["gate"]
        gate_files = (
            files if gate["kind"] == "always" else selected_files(files, gate["globs"])
        )
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
                    "count": detector_score // detector.get("weight", 1),
                    "score": detector_score,
                    "matches": matches,
                }
            )
        threshold = effective_threshold(profile.get("threshold", 1), sensitivity)
        decision = "not-applicable"
        if gate_passed:
            decision = (
                "run"
                if profile["screen"] == "always" or score >= threshold
                else "screened-clean"
            )
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
                "obligations": profile.get("obligations", []),
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
        "run_mode": run_mode,
        "mode_override": mode_override,
        "excluded_parts": sorted(EXCLUDED_PARTS),
        "resource_budget": resource_budget(),
        "scanned_files": len(files),
        "profiles": rows,
    }


def print_survey(survey: dict[str, Any]) -> None:
    print(f"root: {survey['root']}")
    print(f"revision: {survey['source_revision'] or 'unversioned'}")
    print(f"mode: {survey['run_mode']}")
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
        status = (
            "not-applicable"
            if survey_row.get("decision") == "not-applicable"
            else "unreviewed"
        )
        evidence = [survey_row.get("gate", {})] if status == "not-applicable" else []
        obligation_status = (
            "not-applicable" if status == "not-applicable" else "unreviewed"
        )
        obligation_evidence = evidence if status == "not-applicable" else []
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
                "obligations": [
                    {
                        "id": obligation,
                        "status": obligation_status,
                        "evidence": obligation_evidence,
                    }
                    for obligation in profile.get("obligations", [])
                ],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "terminal_state": "incomplete",
        "registry_sha256": survey.get("registry_sha256"),
        "source_revision": survey.get("source_revision"),
        "source_state_sha256": survey.get("source_state_sha256"),
        "run_mode": survey.get("run_mode"),
        "mode_override": survey.get("mode_override"),
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
            raise ContractError(
                f"approved exclusion has unknown fields {sorted(unknown)}"
            )
        profile_id = require_text(exclusion, "id", "<exclusion>")
        require_text(exclusion, "approved_by", profile_id)
        require_text(exclusion, "reason", profile_id)
        require_text(exclusion, "impact", profile_id)
        if profile_id not in expected:
            raise ContractError(
                f"approved exclusion references unknown profile {profile_id}"
            )
        if profile_id in approved:
            raise ContractError(f"duplicate approved exclusion: {profile_id}")
        approved.add(profile_id)
    return approved


def validate_ledger(
    registry_path: Path,
    ledger_path: Path,
    root: Path,
    plan_path: Path,
    build_path: Path | None = None,
    review_path: Path | None = None,
) -> None:
    if not root.is_dir():
        raise ContractError(f"target root is not a directory: {root}")
    registry, registry_profiles = load_registry(registry_path)
    ledger = load_json(ledger_path)
    registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    if ledger.get("registry_sha256") != registry_digest:
        raise ContractError(
            "ledger registry hash is stale or belongs to another registry"
        )
    files = scan_files(root)
    current_source_state = source_state_sha256(files)
    if ledger.get("source_state_sha256") != current_source_state:
        raise ContractError(
            "ledger source fingerprint is stale; re-survey and refresh receipts"
        )
    if ledger.get("source_revision") != repository_revision(root):
        raise ContractError("ledger source_revision differs from the target repository")
    terminal_state = ledger.get("terminal_state")
    if terminal_state not in TERMINAL_STATES:
        raise ContractError(f"ledger has unknown terminal_state: {terminal_state}")
    validated_plan = validate_plan_artifact(
        registry_path, plan_path, root if build_path is None else None
    )
    if build_path is None:
        if review_path is not None:
            raise ContractError("a review artifact requires a build artifact")
    elif review_path is None:
        raise ContractError("final ledger validation with a build requires a review")
    else:
        review = validate_review_artifact(
            registry_path, plan_path, build_path, review_path, ledger_path, root
        )
        if (
            terminal_state in SUCCESS_TERMINAL_STATES
            and review["verdict"] != "approved"
        ):
            raise ContractError("successful terminal state requires an approved review")
    if terminal_state in SUCCESS_TERMINAL_STATES and (
        build_path is None or review_path is None
    ):
        raise ContractError(
            "successful terminal state requires plan, build, and review artifacts"
        )
    run_mode = ledger.get("run_mode")
    if run_mode not in RUN_MODES:
        raise ContractError(f"ledger has unknown run_mode: {run_mode}")
    validate_mode_override(ledger, registry["default_mode"], run_mode)
    if run_mode != validated_plan["run_mode"]:
        raise ContractError("ledger run_mode differs from the frozen plan")
    if ledger.get("mode_override") != validated_plan.get("mode_override"):
        raise ContractError("ledger mode_override differs from the frozen plan")
    expected = {profile["id"] for profile in registry_profiles}
    profiles_by_id = {profile["id"]: profile for profile in registry_profiles}
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
        for field in (
            "scope",
            "evidence",
            "findings",
            "disposition",
            "validation",
            "residuals",
        ):
            if not isinstance(row.get(field), list):
                raise ContractError(f"profile {profile_id}: {field} must be an array")
        if status == "reviewed-clean" and (not row["scope"] or not row["evidence"]):
            raise ContractError(
                f"profile {profile_id}: reviewed-clean requires scope and evidence"
            )
        if status == "not-applicable" and not row["evidence"]:
            raise ContractError(
                f"profile {profile_id}: not-applicable requires evidence"
            )
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
            raise ContractError(
                f"profile {profile_id}: successful status cannot have residuals"
            )
        if status in {"deferred", "blocked"} and (
            not row["evidence"] or not row["disposition"] or not row["residuals"]
        ):
            raise ContractError(
                f"profile {profile_id}: {status} requires evidence, disposition, and residuals"
            )
        validate_obligations(profile_id, profiles_by_id[profile_id], row, status)
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
            raise ContractError(
                "complete-with-approved-exclusions requires an approval record"
            )
        unapproved = sorted(set(non_success) - approved)
        if unapproved:
            raise ContractError(
                f"complete-with-approved-exclusions has unapproved open profiles: {unapproved}"
            )


def validate_obligations(
    profile_id: str,
    profile: dict[str, Any],
    row: dict[str, Any],
    profile_status: str,
) -> None:
    obligations = row.get("obligations")
    if not isinstance(obligations, list):
        raise ContractError(f"profile {profile_id}: obligations must be an array")
    expected = profile.get("obligations", [])
    actual = [item.get("id") for item in obligations if isinstance(item, dict)]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ContractError(
            f"profile {profile_id}: obligation mismatch; "
            f"expected={sorted(expected)} actual={sorted(str(item) for item in actual)}"
        )
    unsuccessful: list[str] = []
    for obligation in obligations:
        obligation_id = obligation["id"]
        unknown = set(obligation) - {"id", "status", "evidence"}
        if unknown:
            raise ContractError(
                f"profile {profile_id} obligation {obligation_id}: "
                f"unknown fields {sorted(unknown)}"
            )
        status = obligation.get("status")
        if status not in OBLIGATION_STATUSES:
            raise ContractError(
                f"profile {profile_id} obligation {obligation_id}: unknown status {status}"
            )
        if not isinstance(obligation.get("evidence"), list):
            raise ContractError(
                f"profile {profile_id} obligation {obligation_id}: evidence must be an array"
            )
        if status in OBLIGATION_SUCCESS_STATUSES and not obligation["evidence"]:
            raise ContractError(
                f"profile {profile_id} obligation {obligation_id}: {status} requires evidence"
            )
        if status not in OBLIGATION_SUCCESS_STATUSES:
            unsuccessful.append(obligation_id)
    if profile_status in SUCCESS_STATUSES and unsuccessful:
        raise ContractError(
            f"profile {profile_id}: successful status has open obligations {unsuccessful}"
        )


def validate_mode_override(
    ledger: dict[str, Any], default_mode: str, run_mode: str
) -> None:
    override = ledger.get("mode_override")
    if run_mode == default_mode:
        if override not in (None, {}):
            raise ContractError(
                "ledger mode_override is only valid for a non-default mode"
            )
        return
    if not isinstance(override, dict):
        raise ContractError("non-default run_mode requires a mode_override object")
    unknown = set(override) - {"approved_by", "reason"}
    if unknown:
        raise ContractError(f"mode_override has unknown fields {sorted(unknown)}")
    require_text(override, "approved_by", "<mode-override>")
    require_text(override, "reason", "<mode-override>")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        procedure = root / "procedure.md"
        procedure.write_text("# Procedure\n", encoding="utf-8")
        source = root / "sample.rs"
        source.write_text("trait Child: Parent {}\n", encoding="utf-8")
        registry = root / "concerns.toml"
        registry.write_text(
            """schema_version = 3
default_mode = "modernize"
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
obligations = ["topology", "boundary-candidates"]

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
        assert survey["run_mode"] == "modernize"
        try:
            build_survey(registry, root, "medium", "compatibility")
        except ContractError as error:
            assert "requires --mode-approved-by and --mode-reason" in str(error)
        else:
            raise AssertionError("unapproved run-mode override was accepted")
        output = root / ".ultra-out"
        output.mkdir()
        (output / "survey.initial.json").write_text(
            json.dumps(survey, indent=2), encoding="utf-8"
        )
        plan = {
            "schema_version": SCHEMA_VERSION,
            "artifact": "ultra-plan",
            "registry_sha256": survey["registry_sha256"],
            "survey_sha256": file_sha256(output / "survey.initial.json"),
            "source_revision": survey["source_revision"],
            "source_state_sha256": survey["source_state_sha256"],
            "run_mode": survey["run_mode"],
            "mode_override": survey["mode_override"],
            "planner": {
                "provider": "openai",
                "model_class": "frontier",
                "model": "gpt-5.6-sol",
                "effort": "high",
                "invocation_id": "00000000-0000-4000-8000-000000000001",
                "context_id": "00000000-0000-4000-8000-000000000001",
            },
            "profile_ids": ["design.traits", "design.cohesion"],
            "work_packages": [
                {
                    "id": "design",
                    "profile_ids": ["design.traits", "design.cohesion"],
                    "depends_on": [],
                    "scope": ["sample.rs"],
                    "objectives": ["Review trait topology and type cohesion"],
                    "breaking_changes": [],
                    "migration": [],
                    "validation": ["Run focused design checks"],
                    "risks": [],
                }
            ],
            "resource_budget": survey["resource_budget"],
        }
        plan_path = output / "plan.json"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        validate_plan_artifact(registry, plan_path, root)

        weak_plan = json.loads(json.dumps(plan))
        weak_plan["planner"]["model_class"] = "efficient"
        weak_plan_path = output / "weak-plan.json"
        weak_plan_path.write_text(json.dumps(weak_plan), encoding="utf-8")
        try:
            validate_plan_artifact(registry, weak_plan_path, root)
        except ContractError as error:
            assert "model_class must be frontier" in str(error)
        else:
            raise AssertionError("an efficient-model plan was accepted")

        unbound_plan = json.loads(json.dumps(plan))
        unbound_plan["source_state_sha256"] = "0" * 64
        unbound_plan_path = output / "unbound-plan.json"
        unbound_plan_path.write_text(json.dumps(unbound_plan), encoding="utf-8")
        try:
            validate_plan_artifact(registry, unbound_plan_path)
        except ContractError as error:
            assert "differs from the initial survey" in str(error)
        else:
            raise AssertionError("a plan unbound from its initial survey was accepted")

        empty_survey_path = output / "empty-survey.json"
        empty_survey_path.write_text("{}", encoding="utf-8")
        try:
            validate_survey_artifact(registry, empty_survey_path)
        except ContractError as error:
            assert "survey: field mismatch" in str(error)
        else:
            raise AssertionError("an empty survey placeholder was accepted")

        tampered_survey = json.loads(json.dumps(survey))
        tampered_survey["profiles"][0]["evaluation"] = "quantitative"
        tampered_survey_path = output / "tampered-survey.json"
        tampered_survey_path.write_text(json.dumps(tampered_survey), encoding="utf-8")
        try:
            validate_survey_artifact(registry, tampered_survey_path)
        except ContractError as error:
            assert "evaluation differs from registry" in str(error)
        else:
            raise AssertionError("a survey contradicting the registry was accepted")

        build = {
            "schema_version": SCHEMA_VERSION,
            "artifact": "ultra-build",
            "plan_sha256": file_sha256(plan_path),
            "builder": {
                "provider": "openai",
                "model_class": "efficient",
                "model": "gpt-5.6-luna",
                "effort": "medium",
                "invocation_id": "00000000-0000-4000-8000-000000000002",
                "context_id": "00000000-0000-4000-8000-000000000002",
            },
            "source_revision": repository_revision(root),
            "source_state_sha256": source_state_sha256(scan_files(root)),
            "work_packages": [
                {
                    "id": "design",
                    "status": "completed",
                    "profile_ids": ["design.traits", "design.cohesion"],
                    "changes": [],
                    "evidence": ["Trait and cohesion inventories"],
                    "validation": ["Focused design checks passed"],
                    "residuals": [],
                }
            ],
        }
        build_path = output / "build.json"
        build_path.write_text(json.dumps(build, indent=2), encoding="utf-8")
        validate_build_artifact(registry, plan_path, build_path, root)
        (output / "score-history.json").write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "artifact": "ultra-score-history",
                    "registry_sha256": file_sha256(registry),
                    "plan_sha256": file_sha256(plan_path),
                    "entries": [
                        {
                            "stage": "initial",
                            "source_revision": survey["source_revision"],
                            "source_state_sha256": survey["source_state_sha256"],
                            "survey_sha256": file_sha256(
                                output / "survey.initial.json"
                            ),
                        },
                        {
                            "stage": "design",
                            "source_revision": build["source_revision"],
                            "source_state_sha256": build["source_state_sha256"],
                            "survey_sha256": None,
                        },
                        {
                            "stage": "final",
                            "source_revision": build["source_revision"],
                            "source_state_sha256": build["source_state_sha256"],
                            "survey_sha256": None,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        same_model_build = json.loads(json.dumps(build))
        same_model_build["builder"].update(
            {"model": "gpt-5.6-sol", "model_class": "efficient"}
        )
        same_model_build_path = output / "same-model-build.json"
        same_model_build_path.write_text(json.dumps(same_model_build), encoding="utf-8")
        try:
            validate_build_artifact(registry, plan_path, same_model_build_path, root)
        except ContractError as error:
            assert "classified as frontier" in str(error)
        else:
            raise AssertionError("the planner model was accepted as the builder")

        receipts = output / "receipts"
        receipts.mkdir()
        (receipts / "design.json").write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "artifact": "ultra-stage-receipt",
                    "stage": "design",
                    "plan_sha256": file_sha256(plan_path),
                    "source_state_sha256": build["source_state_sha256"],
                    "profile_ids": ["design.traits", "design.cohesion"],
                    "findings": [],
                    "changes": [],
                    "validation": ["focused design checks passed"],
                    "residuals": [],
                }
            ),
            encoding="utf-8",
        )
        (output / "final-validation.json").write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "artifact": "ultra-final-validation",
                    "plan_sha256": file_sha256(plan_path),
                    "source_revision": build["source_revision"],
                    "source_state_sha256": build["source_state_sha256"],
                    "gates": [
                        {
                            "name": "self-test fixture",
                            "status": "passed",
                            "evidence": ["fixture command exited zero"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

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
            for obligation in row["obligations"]:
                obligation.update(
                    {"status": "satisfied", "evidence": ["obligation inventory"]}
                )
        ledger_path = output / "profile-ledger.json"
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

        evidence_paths = [
            "survey.initial.json",
            "profile-ledger.json",
            "score-history.json",
            "receipts/design.json",
            "final-validation.json",
        ]
        evidence_manifest = {
            "schema_version": SCHEMA_VERSION,
            "artifact": "ultra-evidence-manifest",
            "files": [
                {"path": path, "sha256": file_sha256(output / path)}
                for path in evidence_paths
            ],
        }
        evidence_manifest_path = output / "evidence-manifest.json"
        evidence_manifest_path.write_text(
            json.dumps(evidence_manifest, indent=2), encoding="utf-8"
        )

        review = {
            "schema_version": SCHEMA_VERSION,
            "artifact": "ultra-review",
            "plan_sha256": file_sha256(plan_path),
            "build_sha256": file_sha256(build_path),
            "ledger_sha256": file_sha256(ledger_path),
            "evidence_manifest_sha256": file_sha256(evidence_manifest_path),
            "source_revision": repository_revision(root),
            "source_state_sha256": source_state_sha256(scan_files(root)),
            "reviewer": {
                "provider": "openai",
                "model_class": "frontier",
                "model": "gpt-5.6-sol",
                "effort": "medium",
                "invocation_id": "00000000-0000-4000-8000-000000000003",
                "context_id": "00000000-0000-4000-8000-000000000003",
            },
            "profile_ids": ["design.traits", "design.cohesion"],
            "verdict": "approved",
            "findings": [],
            "validation": ["Diff, receipts, and final gates independently reviewed"],
            "residuals": [],
        }
        review_path = output / "review.json"
        review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        validate_review_artifact(
            registry, plan_path, build_path, review_path, ledger_path, root
        )

        wrong_reviewer = json.loads(json.dumps(review))
        wrong_reviewer["reviewer"]["model"] = "gpt-5.5"
        wrong_review_path = output / "wrong-review.json"
        wrong_review_path.write_text(json.dumps(wrong_reviewer), encoding="utf-8")
        try:
            validate_review_artifact(
                registry,
                plan_path,
                build_path,
                wrong_review_path,
                ledger_path,
                root,
            )
        except ContractError as error:
            assert "must exactly match the planner" in str(error)
        else:
            raise AssertionError("a different frontier reviewer model was accepted")

        shared_context_review = json.loads(json.dumps(review))
        shared_context_review["reviewer"]["context_id"] = (
            "00000000-0000-4000-8000-000000000001"
        )
        shared_context_review_path = output / "shared-context-review.json"
        shared_context_review_path.write_text(
            json.dumps(shared_context_review), encoding="utf-8"
        )
        try:
            validate_review_artifact(
                registry,
                plan_path,
                build_path,
                shared_context_review_path,
                ledger_path,
                root,
            )
        except ContractError as error:
            assert "independent context" in str(error)
        else:
            raise AssertionError("the planner context was accepted for review")
        validate_ledger(registry, ledger_path, root, plan_path, build_path, review_path)

        try:
            validate_ledger(registry, ledger_path, root, plan_path)
        except ContractError as error:
            assert "requires plan, build, and review artifacts" in str(error)
        else:
            raise AssertionError(
                "a complete ledger without build and review was accepted"
            )

        def refresh_review_bindings() -> None:
            for entry in evidence_manifest["files"]:
                if entry["path"] == "profile-ledger.json":
                    entry["sha256"] = file_sha256(ledger_path)
            evidence_manifest_path.write_text(
                json.dumps(evidence_manifest, indent=2), encoding="utf-8"
            )
            review["ledger_sha256"] = file_sha256(ledger_path)
            review["evidence_manifest_sha256"] = file_sha256(evidence_manifest_path)
            review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")

        def expect_contract(candidate: dict[str, Any], message: str) -> None:
            ledger_path.write_text(json.dumps(candidate), encoding="utf-8")
            refresh_review_bindings()
            try:
                validate_ledger(
                    registry, ledger_path, root, plan_path, build_path, review_path
                )
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

        open_obligation = json.loads(json.dumps(ledger))
        open_obligation["profiles"][0]["obligations"][0].update(
            {"status": "unreviewed", "evidence": []}
        )
        expect_contract(open_obligation, "successful status has open obligations")

        silent_compatibility = json.loads(json.dumps(ledger))
        silent_compatibility["run_mode"] = "compatibility"
        expect_contract(silent_compatibility, "requires a mode_override object")

        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        refresh_review_bindings()
        source.write_text(
            "trait Child: Parent { fn changed(&self); }\n", encoding="utf-8"
        )
        try:
            validate_ledger(
                registry, ledger_path, root, plan_path, build_path, review_path
            )
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

    plan = commands.add_parser("plan")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    plan_validate = plan_commands.add_parser("validate")
    plan_validate.add_argument("--registry", type=Path, required=True)
    plan_validate.add_argument("--plan", type=Path, required=True)
    plan_validate.add_argument("--root", type=Path, required=True)

    build = commands.add_parser("build")
    build_commands = build.add_subparsers(dest="build_command", required=True)
    build_validate = build_commands.add_parser("validate")
    build_validate.add_argument("--registry", type=Path, required=True)
    build_validate.add_argument("--plan", type=Path, required=True)
    build_validate.add_argument("--build", type=Path, required=True)
    build_validate.add_argument("--root", type=Path, required=True)

    review = commands.add_parser("review")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    review_validate = review_commands.add_parser("validate")
    review_validate.add_argument("--registry", type=Path, required=True)
    review_validate.add_argument("--plan", type=Path, required=True)
    review_validate.add_argument("--build", type=Path, required=True)
    review_validate.add_argument("--review", type=Path, required=True)
    review_validate.add_argument("--ledger", type=Path, required=True)
    review_validate.add_argument("--root", type=Path, required=True)

    survey = commands.add_parser("survey")
    survey.add_argument("--registry", type=Path, required=True)
    survey.add_argument("--root", type=Path, required=True)
    survey.add_argument(
        "--sensitivity", choices=("low", "medium", "high"), default="medium"
    )
    survey.add_argument("--mode", choices=tuple(sorted(RUN_MODES)))
    survey.add_argument("--mode-approved-by")
    survey.add_argument("--mode-reason")
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
    ledger_validate.add_argument("--plan", type=Path, required=True)
    ledger_validate.add_argument("--build", type=Path)
    ledger_validate.add_argument("--review", type=Path)

    commands.add_parser("self-test")
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "registry":
            _, profiles = load_registry(arguments.registry)
            print(f"registry valid: {len(profiles)} profiles")
        elif arguments.command == "plan":
            plan = validate_plan_artifact(
                arguments.registry, arguments.plan, arguments.root
            )
            print(f"plan valid: {len(plan['work_packages'])} work packages")
        elif arguments.command == "build":
            build = validate_build_artifact(
                arguments.registry, arguments.plan, arguments.build, arguments.root
            )
            print(f"build valid: {len(build['work_packages'])} work packages")
        elif arguments.command == "review":
            review = validate_review_artifact(
                arguments.registry,
                arguments.plan,
                arguments.build,
                arguments.review,
                arguments.ledger,
                arguments.root,
            )
            print(f"review valid: {review['verdict']}")
        elif arguments.command == "survey":
            survey = build_survey(
                arguments.registry,
                arguments.root,
                arguments.sensitivity,
                arguments.mode,
                arguments.mode_approved_by,
                arguments.mode_reason,
            )
            if arguments.output:
                arguments.output.parent.mkdir(parents=True, exist_ok=True)
                arguments.output.write_text(
                    json.dumps(survey, indent=2), encoding="utf-8"
                )
            if arguments.format == "json":
                print(json.dumps(survey, indent=2))
            else:
                print_survey(survey)
        elif arguments.command == "ledger" and arguments.ledger_command == "init":
            survey = validate_survey_artifact(arguments.registry, arguments.survey)
            ledger = initial_ledger(arguments.registry, survey)
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
            print(f"ledger initialized: {arguments.output}")
        elif arguments.command == "ledger":
            validate_ledger(
                arguments.registry,
                arguments.ledger,
                arguments.root,
                arguments.plan,
                arguments.build,
                arguments.review,
            )
            print("ledger valid")
        else:
            run_self_test()
    except ContractError as error:
        print(f"ultra-system contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
