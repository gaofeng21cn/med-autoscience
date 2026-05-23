from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import domain_health_diagnostic_recovery_policy
from med_autoscience.controllers.domain_health_diagnostic_parts.control_plane_gate import runtime_recovery_blocked_by_control_plane
from med_autoscience.controllers.domain_health_diagnostic_parts.gate_specificity import _study_requests_gate_specificity_terminal
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _managed_study_status_payload,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control.ports import (
    RuntimeControlPorts,
    request_opl_stage_attempt,
    runtime_status_payload,
)


MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "domain_health_diagnostic_opl_stage_attempt_request"
RECOVERY_DECISIONS = {"create_and_start", "resume", "relaunch_stopped"}


def recovery_failure_payload(
    *,
    preflight_payload: Mapping[str, Any],
    error: Exception,
) -> dict[str, Any]:
    payload = dict(preflight_payload)
    preflight_decision = str(payload.get("decision") or "").strip()
    failure_reason = (
        "create_request_failed"
        if preflight_decision == "create_and_start"
        else "resume_request_failed"
    )
    payload["decision"] = "blocked"
    payload["reason"] = failure_reason
    payload["runtime_execution_error"] = str(error)
    return payload


def _stage_request_decision(payload: Mapping[str, Any]) -> bool:
    return str(payload.get("decision") or "").strip() in RECOVERY_DECISIONS


def projection_error_payload(
    *,
    study_root: Path,
    error: Exception,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    study_id = resolved_study_root.name
    return {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(resolved_study_root),
        "entry_mode": "",
        "execution": {},
        "quest_id": study_id,
        "quest_root": "",
        "quest_exists": False,
        "quest_status": None,
        "runtime_binding_path": str(resolved_study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": (resolved_study_root / "runtime_binding.yaml").exists(),
        "study_completion_contract": {},
        "decision": "blocked",
        "reason": "study_projection_contract_error",
        "projection_error": {
            "error_type": type(error).__name__,
            "message": str(error),
            "study_root": str(resolved_study_root),
        },
        "runtime_execution_error": str(error),
        "domain_health_diagnostic_error_isolated": True,
    }


def _managed_study_roots(profile: WorkspaceProfile) -> list[Path]:
    return [
        study_root
        for study_root in sorted(profile.studies_root.iterdir())
        if study_root.is_dir() and (study_root / "study.yaml").exists()
    ]


def _record_requested_runtime_recovery(
    *,
    runtime_recovery_payloads: dict[str, dict[str, Any]],
    study_root: Path,
    action_payload: dict[str, Any],
) -> None:
    action_status_payload = _managed_study_status_payload(action_payload)
    if _stage_request_decision(action_status_payload) or str(action_status_payload.get("status") or "").strip() in {
        "opl_stage_attempt_admission_required",
        "opl_stage_attempt_requested",
    }:
        study_root_key = str(Path(study_root).expanduser().resolve())
        runtime_recovery_payloads[study_root_key] = action_status_payload


def _apply_managed_study_status(
    *,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    study_root: Path,
    auto_recoveries: list[dict[str, Any]],
    runtime_recovery_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if _study_requests_gate_specificity_terminal(study_root=study_root):
        try:
            return runtime_status_payload(ports=runtime_control_ports, profile=profile, study_root=study_root)
        except Exception as exc:
            return projection_error_payload(study_root=study_root, error=exc)
    try:
        action_payload = request_opl_stage_attempt(
            ports=runtime_control_ports,
            profile=profile,
            study_root=study_root,
            source="domain_health_diagnostic",
        )
        _record_requested_runtime_recovery(
            runtime_recovery_payloads=runtime_recovery_payloads,
            study_root=study_root,
            action_payload=action_payload,
        )
        return action_payload
    except Exception as exc:
        try:
            preflight_payload = runtime_status_payload(
                ports=runtime_control_ports,
                profile=profile,
                study_root=study_root,
            )
        except Exception:
            return projection_error_payload(study_root=study_root, error=exc)
        action_payload = recovery_failure_payload(
            preflight_payload=preflight_payload,
            error=exc,
        )
        auto_recoveries.append(
            _serialize_managed_study_auto_recovery(
                preflight_payload=preflight_payload,
                applied_payload=action_payload,
                source="domain_health_diagnostic",
            )
        )
        return action_payload


def _auto_recovery_action_payload(
    *,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    study_root: Path,
    preflight_payload: dict[str, Any],
    recovery_holds: list[dict[str, Any]],
    runtime_recovery_payloads: dict[str, dict[str, Any]],
    apply: bool,
) -> tuple[dict[str, Any], bool]:
    recovery_hold = domain_health_diagnostic_recovery_policy.hold_for_flapping_circuit_breaker(
        study_root=study_root,
        status_payload=preflight_payload,
    )
    control_plane_recovery_block = runtime_recovery_blocked_by_control_plane(
        _managed_study_status_payload(preflight_payload)
    )
    if recovery_hold is not None:
        if apply:
            domain_health_diagnostic_recovery_policy.write_recovery_probe(
                study_root=study_root,
                recovery_hold=recovery_hold,
            )
        recovery_holds.append(recovery_hold)
        return preflight_payload, False
    if control_plane_recovery_block is not None:
        return {
            **_managed_study_status_payload(preflight_payload),
            "decision": "blocked",
            "reason": "resume_request_failed",
            "control_plane_runtime_recovery_block": control_plane_recovery_block,
        }, False
    if not apply:
        return preflight_payload, False
    action_payload = request_opl_stage_attempt(
        ports=runtime_control_ports,
        profile=profile,
        study_root=study_root,
        source=MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
    )
    _record_requested_runtime_recovery(
        runtime_recovery_payloads=runtime_recovery_payloads,
        study_root=study_root,
        action_payload=action_payload,
    )
    return action_payload, True


def _read_or_auto_recover_managed_study(
    *,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    study_root: Path,
    auto_recoveries: list[dict[str, Any]],
    recovery_holds: list[dict[str, Any]],
    runtime_recovery_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    try:
        action_payload = runtime_status_payload(ports=runtime_control_ports, profile=profile, study_root=study_root)
    except Exception as exc:
        return projection_error_payload(study_root=study_root, error=exc)
    if not _should_hard_auto_recover_managed_study(action_payload):
        return action_payload
    preflight_payload = action_payload
    action_payload, recovery_applied = _auto_recovery_action_payload(
        runtime_control_ports=runtime_control_ports,
        profile=profile,
        study_root=study_root,
        preflight_payload=preflight_payload,
        recovery_holds=recovery_holds,
        runtime_recovery_payloads=runtime_recovery_payloads,
        apply=False,
    )
    if recovery_applied:
        auto_recoveries.append(
            _serialize_managed_study_auto_recovery(
                preflight_payload=preflight_payload,
                applied_payload=action_payload,
                source=MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
            )
        )
    return action_payload


def managed_study_initial_statuses(
    *,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile | None,
    apply: bool,
    request_opl_stage_attempts: bool,
    auto_recoveries: list[dict[str, Any]],
    recovery_holds: list[dict[str, Any]],
    runtime_recovery_payloads: dict[str, dict[str, Any]],
) -> list[tuple[Path, dict[str, Any]]]:
    if not request_opl_stage_attempts:
        return []
    if profile is None:
        raise ValueError("profile is required when request_opl_stage_attempts is enabled")
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    for study_root in _managed_study_roots(profile):
        if apply:
            action_payload = _apply_managed_study_status(
                runtime_control_ports=runtime_control_ports,
                profile=profile,
                study_root=study_root,
                auto_recoveries=auto_recoveries,
                runtime_recovery_payloads=runtime_recovery_payloads,
            )
        else:
            action_payload = _read_or_auto_recover_managed_study(
                runtime_control_ports=runtime_control_ports,
                profile=profile,
                study_root=study_root,
                auto_recoveries=auto_recoveries,
                recovery_holds=recovery_holds,
                runtime_recovery_payloads=runtime_recovery_payloads,
            )
        managed_study_statuses.append((study_root, _managed_study_status_payload(action_payload)))
    return managed_study_statuses


__all__ = [
    "MANAGED_STUDY_AUTO_RECOVERY_SOURCE",
    "managed_study_initial_statuses",
    "recovery_failure_payload",
]
