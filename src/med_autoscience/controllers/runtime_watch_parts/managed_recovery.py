from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import runtime_watch_recovery_policy, study_runtime_router
from med_autoscience.controllers.runtime_watch_parts.control_plane_gate import runtime_recovery_blocked_by_control_plane
from med_autoscience.controllers.runtime_watch_parts.gate_specificity import _study_requests_gate_specificity_terminal
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import (
    _managed_study_status_payload,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
)
from med_autoscience.profiles import WorkspaceProfile


MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "runtime_watch_auto_recovery"


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


def managed_study_initial_statuses(
    *,
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
    for study_root in sorted(profile.studies_root.iterdir()):
        study_root_key = str(Path(study_root).expanduser().resolve())
        if not study_root.is_dir():
            continue
        if not (study_root / "study.yaml").exists():
            continue
        if apply:
            if _study_requests_gate_specificity_terminal(study_root=study_root):
                preflight_payload = _managed_study_status_payload(
                    study_runtime_router.study_runtime_status(
                        profile=profile,
                        study_root=study_root,
                    )
                )
                action_payload = preflight_payload
                managed_study_statuses.append((study_root, _managed_study_status_payload(action_payload)))
                continue
            try:
                action_payload = study_runtime_router.ensure_study_runtime(
                    profile=profile,
                    study_root=study_root,
                    source="runtime_watch",
                )
                action_status_payload = _managed_study_status_payload(action_payload)
                if str(action_status_payload.get("decision") or "").strip() in {
                    "create_and_start",
                    "resume",
                    "relaunch_stopped",
                }:
                    runtime_recovery_payloads[study_root_key] = action_status_payload
            except Exception as exc:
                preflight_payload = _managed_study_status_payload(
                    study_runtime_router.study_runtime_status(
                        profile=profile,
                        study_root=study_root,
                    )
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
        else:
            action_payload = study_runtime_router.study_runtime_status(
                profile=profile,
                study_root=study_root,
            )
            if _should_hard_auto_recover_managed_study(action_payload):
                preflight_payload = action_payload
                recovery_hold = runtime_watch_recovery_policy.hold_for_flapping_circuit_breaker(
                    study_root=study_root,
                    status_payload=preflight_payload,
                )
                control_plane_recovery_block = runtime_recovery_blocked_by_control_plane(
                    _managed_study_status_payload(preflight_payload)
                )
                if recovery_hold is not None:
                    runtime_watch_recovery_policy.write_recovery_probe(
                        study_root=study_root,
                        recovery_hold=recovery_hold,
                    )
                    recovery_holds.append(recovery_hold)
                elif control_plane_recovery_block is not None:
                    action_payload = {
                        **_managed_study_status_payload(preflight_payload),
                        "decision": "blocked",
                        "reason": "resume_request_failed",
                        "control_plane_runtime_recovery_block": control_plane_recovery_block,
                    }
                else:
                    action_payload = study_runtime_router.ensure_study_runtime(
                        profile=profile,
                        study_root=study_root,
                        source=MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                    )
                    action_status_payload = _managed_study_status_payload(action_payload)
                    if str(action_status_payload.get("decision") or "").strip() in {
                        "create_and_start",
                        "resume",
                        "relaunch_stopped",
                    }:
                        runtime_recovery_payloads[study_root_key] = action_status_payload
                    auto_recoveries.append(
                        _serialize_managed_study_auto_recovery(
                            preflight_payload=preflight_payload,
                            applied_payload=action_payload,
                            source=MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                        )
                    )
        managed_study_statuses.append((study_root, _managed_study_status_payload(action_payload)))
    return managed_study_statuses


__all__ = [
    "MANAGED_STUDY_AUTO_RECOVERY_SOURCE",
    "managed_study_initial_statuses",
    "recovery_failure_payload",
]
