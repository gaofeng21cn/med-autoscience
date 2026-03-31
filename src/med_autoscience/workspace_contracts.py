from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from med_autoscience.deepscientist_repo_manifest import inspect_deepscientist_repo_manifest
from med_autoscience.profiles import WorkspaceProfile


_REQUIRED_OVERRIDE_FIELDS = ("id", "source_path", "status", "target_surface")


def _collect_check_issues(checks: dict[str, bool], *, prefix: str) -> list[str]:
    return [f"{prefix}.{name}" for name, ok in checks.items() if not ok]


def _normalize_override(item: object) -> tuple[dict[str, str] | None, list[str]]:
    if not isinstance(item, dict):
        return None, ["override_not_mapping"]

    issues: list[str] = []
    normalized: dict[str, str] = {}
    for field in _REQUIRED_OVERRIDE_FIELDS:
        raw_value = item.get(field)
        if not isinstance(raw_value, str) or not raw_value.strip():
            issues.append(f"override_missing_or_invalid_{field}")
            continue
        normalized[field] = raw_value.strip()
    if issues:
        return None, issues
    return normalized, []


def inspect_behavior_equivalence_gate(gate_path: Path) -> dict[str, object]:
    checks: dict[str, bool] = {
        "gate_file_exists": gate_path.is_file(),
        "yaml_parseable": False,
        "schema_version_present": False,
        "phase_25_ready_is_bool": False,
        "critical_overrides_is_list": False,
        "critical_overrides_valid": False,
    }
    issues: list[str] = []
    schema_version: object = None
    phase_25_ready = False
    critical_overrides: list[dict[str, str]] = []

    if not checks["gate_file_exists"]:
        issues.extend(_collect_check_issues(checks, prefix="behavior_gate"))
        return {
            "path": str(gate_path),
            "ready": False,
            "checks": checks,
            "issues": issues,
            "schema_version": schema_version,
            "phase_25_ready": phase_25_ready,
            "critical_overrides": critical_overrides,
        }

    try:
        payload = yaml.safe_load(gate_path.read_text(encoding="utf-8"))
        checks["yaml_parseable"] = True
    except (yaml.YAMLError, OSError):
        issues.append("behavior_gate.yaml_parse_failed")
        issues.extend(_collect_check_issues(checks, prefix="behavior_gate"))
        return {
            "path": str(gate_path),
            "ready": False,
            "checks": checks,
            "issues": issues,
            "schema_version": schema_version,
            "phase_25_ready": phase_25_ready,
            "critical_overrides": critical_overrides,
        }

    if not isinstance(payload, dict):
        issues.append("behavior_gate.payload_not_mapping")
        issues.extend(_collect_check_issues(checks, prefix="behavior_gate"))
        return {
            "path": str(gate_path),
            "ready": False,
            "checks": checks,
            "issues": issues,
            "schema_version": schema_version,
            "phase_25_ready": phase_25_ready,
            "critical_overrides": critical_overrides,
        }

    raw_schema_version = payload.get("schema_version")
    if isinstance(raw_schema_version, str) and raw_schema_version.strip():
        schema_version = raw_schema_version.strip()
        checks["schema_version_present"] = True
    elif isinstance(raw_schema_version, int) and not isinstance(raw_schema_version, bool):
        schema_version = raw_schema_version
        checks["schema_version_present"] = True

    raw_phase_25_ready = payload.get("phase_25_ready")
    if isinstance(raw_phase_25_ready, bool):
        phase_25_ready = raw_phase_25_ready
        checks["phase_25_ready_is_bool"] = True

    raw_critical_overrides = payload.get("critical_overrides")
    if isinstance(raw_critical_overrides, list):
        checks["critical_overrides_is_list"] = True
        override_issues: list[str] = []
        for index, raw_override in enumerate(raw_critical_overrides):
            normalized_override, errors = _normalize_override(raw_override)
            if normalized_override is not None:
                critical_overrides.append(normalized_override)
                continue
            override_issues.extend(f"behavior_gate.override[{index}].{error}" for error in errors)
        if not override_issues:
            checks["critical_overrides_valid"] = True
        else:
            issues.extend(override_issues)

    if not checks["schema_version_present"]:
        issues.append("behavior_gate.schema_version_missing")
    if not checks["phase_25_ready_is_bool"]:
        issues.append("behavior_gate.phase_25_ready_missing_or_not_bool")
    if not checks["critical_overrides_is_list"]:
        issues.append("behavior_gate.critical_overrides_missing_or_not_list")
    if checks["critical_overrides_is_list"] and not checks["critical_overrides_valid"]:
        issues.append("behavior_gate.critical_overrides_invalid")

    ready = all(checks.values()) and phase_25_ready
    if not ready and phase_25_ready:
        issues.append("behavior_gate.phase_25_structure_not_ready")
    if not phase_25_ready:
        issues.append("behavior_gate.phase_25_ready_false")

    return {
        "path": str(gate_path),
        "ready": ready,
        "checks": checks,
        "issues": issues,
        "schema_version": schema_version,
        "phase_25_ready": phase_25_ready,
        "critical_overrides": critical_overrides,
    }


def inspect_workspace_contracts(profile: WorkspaceProfile) -> dict[str, Any]:
    runtime_root_expected = profile.deepscientist_runtime_root / "quests"
    runtime_checks: dict[str, bool] = {
        "runtime_root_matches_deepscientist_runtime": profile.runtime_root == runtime_root_expected,
        "runtime_root_exists": profile.runtime_root.exists(),
        "deepscientist_runtime_root_exists": profile.deepscientist_runtime_root.exists(),
    }
    runtime_contract = {
        "ready": all(runtime_checks.values()),
        "checks": runtime_checks,
        "issues": _collect_check_issues(runtime_checks, prefix="runtime_contract"),
        "runtime_root": str(profile.runtime_root),
        "deepscientist_runtime_root": str(profile.deepscientist_runtime_root),
        "runtime_root_expected": str(runtime_root_expected),
    }

    medautoscience_config_env = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    deepscientist_ops_root = profile.workspace_root / "ops" / "deepscientist"
    deepscientist_config_env = deepscientist_ops_root / "config.env"
    deepscientist_bin_dir = deepscientist_ops_root / "bin"
    behavior_gate_path = deepscientist_ops_root / "behavior_equivalence_gate.yaml"
    manifest_info = inspect_deepscientist_repo_manifest(profile.deepscientist_repo_root)
    launcher_checks: dict[str, bool] = {
        "medautoscience_config_env_exists": medautoscience_config_env.is_file(),
        "deepscientist_config_env_exists": deepscientist_config_env.is_file(),
        "deepscientist_bin_dir_exists": deepscientist_bin_dir.is_dir(),
        "deepscientist_repo_root_configured": profile.deepscientist_repo_root is not None,
    }
    manifest_checks: dict[str, bool] = {
        "manifest_found": manifest_info["manifest_found"],
        "manifest_parsable": manifest_info["manifest_parsable"],
    }
    launcher_contract = {
        "ready": all(launcher_checks.values()),
        "checks": launcher_checks,
        "issues": _collect_check_issues(launcher_checks, prefix="launcher_contract"),
        "medautoscience_config_env": str(medautoscience_config_env),
        "deepscientist_config_env": str(deepscientist_config_env),
        "deepscientist_bin_dir": str(deepscientist_bin_dir),
        "deepscientist_repo_root": str(profile.deepscientist_repo_root) if profile.deepscientist_repo_root else None,
        "repo_manifest": manifest_info,
        "manifest_checks": manifest_checks,
    }

    behavior_gate = inspect_behavior_equivalence_gate(behavior_gate_path)
    return {
        "runtime_contract": runtime_contract,
        "launcher_contract": launcher_contract,
        "behavior_gate": behavior_gate,
        "overall_ready": bool(runtime_contract["ready"] and launcher_contract["ready"] and behavior_gate["ready"]),
    }
