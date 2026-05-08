from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.med_deepscientist_repo_manifest import inspect_med_deepscientist_repo_manifest
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_transport.med_deepscientist_parts.daemon_launcher import _read_optional_config_env_value
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile


_REQUIRED_OVERRIDE_FIELDS = ("id", "source_path", "status", "target_surface")
_PLACEHOLDER_LAUNCHER_MARKERS = ("ABS/PATH", "PATH/TO")


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


def _inspect_launcher_path(config_env_path: Path) -> dict[str, object]:
    launcher_value: str | None = None
    config_error: str | None = None
    config_parseable = False
    if config_env_path.is_file():
        try:
            launcher_value = _read_optional_config_env_value(
                path=config_env_path,
                key="MED_DEEPSCIENTIST_LAUNCHER",
            )
            config_parseable = True
        except (OSError, ValueError) as exc:
            config_error = str(exc)

    configured = bool(launcher_value)
    launcher_path = Path(str(launcher_value)).expanduser() if configured else None
    absolute = bool(launcher_path and launcher_path.is_absolute())
    resolved_launcher_path = str(launcher_path.resolve(strict=False)) if launcher_path else None
    not_placeholder = bool(
        resolved_launcher_path
        and not any(marker in resolved_launcher_path for marker in _PLACEHOLDER_LAUNCHER_MARKERS)
    )
    exists = bool(launcher_path and launcher_path.exists())
    executable = bool(launcher_path and os.access(launcher_path, os.X_OK))

    return {
        "checks": {
            "controlled_backend_launcher_config_parseable": config_parseable,
            "controlled_backend_launcher_configured": configured,
            "controlled_backend_launcher_absolute": absolute,
            "controlled_backend_launcher_not_placeholder": not_placeholder,
            "controlled_backend_launcher_exists": exists,
            "controlled_backend_launcher_executable": executable,
        },
        "configured_launcher_value": launcher_value,
        "resolved_launcher_path": resolved_launcher_path,
        "config_error": config_error,
    }


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
    layout = build_workspace_runtime_layout_for_profile(profile)
    runtime_root_expected = layout.quests_root
    runtime_checks: dict[str, bool] = {
        "managed_runtime_quests_root_matches_layout": profile.managed_runtime_quests_root == runtime_root_expected,
        "managed_runtime_quests_root_exists": profile.managed_runtime_quests_root.exists(),
        "managed_runtime_home_exists": profile.managed_runtime_home.exists(),
    }
    runtime_contract = {
        "ready": all(runtime_checks.values()),
        "checks": runtime_checks,
        "issues": _collect_check_issues(runtime_checks, prefix="runtime_contract"),
        "runtime_root": str(profile.runtime_root),
        "managed_runtime_home": str(profile.managed_runtime_home),
        "managed_runtime_quests_root": str(profile.managed_runtime_quests_root),
        "runtime_root_expected": str(runtime_root_expected),
        "legacy_diagnostic": {
            "read_only": True,
            "runtime_root_matches_med_deepscientist_runtime": profile.runtime_root == runtime_root_expected,
            "med_deepscientist_runtime_root_exists": profile.med_deepscientist_runtime_root.exists(),
            "med_deepscientist_runtime_root": str(profile.med_deepscientist_runtime_root),
        },
    }

    medautoscience_config_env = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    controlled_backend_config_env = layout.config_env_path
    controlled_backend_bin_dir = layout.bin_root
    launcher_path_info = _inspect_launcher_path(controlled_backend_config_env)
    launcher_checks: dict[str, bool] = {
        "medautoscience_config_env_exists": medautoscience_config_env.is_file(),
        "controlled_backend_config_env_exists": controlled_backend_config_env.is_file(),
        "controlled_backend_bin_dir_exists": controlled_backend_bin_dir.is_dir(),
    }
    runner_retirement_checks = dict(launcher_path_info["checks"])
    manifest_info: dict[str, object] = {
        "inspection_skipped": True,
        "skip_reason": "explicit_backend_audit_only",
        "repo_root": str(profile.med_deepscientist_repo_root) if profile.med_deepscientist_repo_root else None,
    }
    manifest_checks: dict[str, bool] = {
        "default_manifest_inspection_disabled": True,
        "manifest_found": False,
        "manifest_parsable": False,
    }
    launcher_issues = _collect_check_issues(launcher_checks, prefix="launcher_contract")
    runner_configured = bool(runner_retirement_checks.get("controlled_backend_launcher_configured"))
    if runner_configured:
        launcher_issues.append("launcher_contract.default_mds_runner_configured")
    config_error = launcher_path_info["config_error"]
    if isinstance(config_error, str) and config_error.strip():
        launcher_issues.append(f"launcher_contract.controlled_backend_launcher_config_error:{config_error}")
    launcher_contract = {
        "surface_kind": "backend_audit_contract",
        "retained_entry": "backend_audit",
        "read_only": True,
        "default_runner_allowed": False,
        "default_webui_allowed": False,
        "ready": not runner_configured,
        "checks": launcher_checks,
        "issues": launcher_issues,
        "medautoscience_config_env": str(medautoscience_config_env),
        "controlled_backend_config_env": str(controlled_backend_config_env),
        "controlled_backend_bin_dir": str(controlled_backend_bin_dir),
        "controlled_backend_repo_root": str(profile.med_deepscientist_repo_root) if profile.med_deepscientist_repo_root else None,
        "controlled_backend_repo_root_configured_for_audit": profile.med_deepscientist_repo_root is not None,
        "configured_launcher_value": launcher_path_info["configured_launcher_value"],
        "resolved_launcher_path": launcher_path_info["resolved_launcher_path"],
        "runner_retirement": {
            "read_only": True,
            "default_runner_allowed": False,
            "default_webui_allowed": False,
            "checks": runner_retirement_checks,
            "issues": (
                ["launcher_contract.default_mds_runner_configured"]
                if runner_configured
                else []
            ),
        },
        "repo_manifest": manifest_info,
        "manifest_checks": manifest_checks,
        "legacy_diagnostic": {
            "read_only": True,
            "med_deepscientist_config_env": str(controlled_backend_config_env),
            "med_deepscientist_bin_dir": str(controlled_backend_bin_dir),
            "med_deepscientist_repo_root": (
                str(profile.med_deepscientist_repo_root) if profile.med_deepscientist_repo_root else None
            ),
        },
    }

    behavior_gate = inspect_behavior_equivalence_gate(layout.behavior_gate_path)
    external_runtime_contract = inspect_hermes_runtime_contract(
        hermes_agent_repo_root=profile.hermes_agent_repo_root,
        hermes_home_root=profile.hermes_home_root,
    )
    return {
        "runtime_contract": runtime_contract,
        "launcher_contract": launcher_contract,
        "behavior_gate": behavior_gate,
        "external_runtime_contract": external_runtime_contract,
        "overall_ready": bool(runtime_contract["ready"] and launcher_contract["ready"] and behavior_gate["ready"]),
    }
