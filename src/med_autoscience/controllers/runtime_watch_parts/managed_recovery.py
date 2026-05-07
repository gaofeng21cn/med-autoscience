from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import runtime_watch_recovery_policy
from med_autoscience.controllers.runtime_watch_parts.control_plane_gate import runtime_recovery_blocked_by_control_plane
from med_autoscience.controllers.runtime_watch_parts.gate_specificity import _study_requests_gate_specificity_terminal
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import (
    _managed_study_status_payload,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control.ports import RuntimeControlPorts, ensure_runtime, runtime_status_payload


MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "runtime_watch_auto_recovery"
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
    if str(action_status_payload.get("decision") or "").strip() in RECOVERY_DECISIONS:
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
        return runtime_status_payload(ports=runtime_control_ports, profile=profile, study_root=study_root)
    try:
        action_payload = ensure_runtime(
            ports=runtime_control_ports,
            profile=profile,
            study_root=study_root,
            source="runtime_watch",
        )
        _record_requested_runtime_recovery(
            runtime_recovery_payloads=runtime_recovery_payloads,
            study_root=study_root,
            action_payload=action_payload,
        )
        return action_payload
    except Exception as exc:
        preflight_payload = runtime_status_payload(
            ports=runtime_control_ports,
            profile=profile,
            study_root=study_root,
        )
        action_payload = recovery_failure_payload(
            preflight_payload=preflight_payload,
            error=exc,
        )
        auto_recoveries.append(
            _serialize_managed_study_auto_recovery(
                preflight_payload=preflight_payload,
                applied_payload=action_payload,
                source="runtime_watch",
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
    recovery_hold = runtime_watch_recovery_policy.hold_for_flapping_circuit_breaker(
        study_root=study_root,
        status_payload=preflight_payload,
    )
    control_plane_recovery_block = runtime_recovery_blocked_by_control_plane(
        _managed_study_status_payload(preflight_payload)
    )
    if recovery_hold is not None:
        if apply:
            runtime_watch_recovery_policy.write_recovery_probe(
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
    action_payload = ensure_runtime(
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
    action_payload = runtime_status_payload(ports=runtime_control_ports, profile=profile, study_root=study_root)
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
    ensure_study_runtimes: bool,
    auto_recoveries: list[dict[str, Any]],
    recovery_holds: list[dict[str, Any]],
    runtime_recovery_payloads: dict[str, dict[str, Any]],
) -> list[tuple[Path, dict[str, Any]]]:
    if not ensure_study_runtimes:
        return []
    if profile is None:
        raise ValueError("profile is required when ensure_study_runtimes is enabled")
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
