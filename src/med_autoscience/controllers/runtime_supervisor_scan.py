from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_ai_repair_policy import two_layer_ai_repair_policy_payload
from med_autoscience.controllers import study_progress, study_runtime_router
from med_autoscience.controllers import recovery_intent_ledger
from med_autoscience.controllers.runtime_supervisor_scan_parts import canonical_inputs
from med_autoscience.controllers.runtime_supervisor_scan_parts import gate_specificity as gate_specificity_part
from med_autoscience.controllers.runtime_supervisor_scan_parts import action_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import applied_repair_merge
from med_autoscience.controllers.runtime_supervisor_scan_parts import artifact_freshness
from med_autoscience.controllers.runtime_supervisor_scan_parts import ai_reviewer
from med_autoscience.controllers.runtime_supervisor_scan_parts import block_state as block_state_part
from med_autoscience.controllers.runtime_supervisor_scan_parts import completion_evidence
from med_autoscience.controllers.runtime_supervisor_scan_parts import evidence_adoption
from med_autoscience.controllers.runtime_supervisor_scan_parts import lifecycle_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair
from med_autoscience.controllers.runtime_supervisor_scan_parts import publication_gate_actions
from med_autoscience.controllers.runtime_supervisor_scan_parts import parked_truth
from med_autoscience.controllers.runtime_supervisor_scan_parts import paper_progress_stall_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import projection_errors
from med_autoscience.controllers.runtime_supervisor_scan_parts import queue_slo
from med_autoscience.controllers.runtime_supervisor_scan_parts import request_packets
from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts
from med_autoscience.controllers.runtime_supervisor_scan_parts import scan_output
from med_autoscience.controllers.runtime_supervisor_scan_parts import status_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import submission_milestone_parking
from med_autoscience.controllers.runtime_supervisor_scan_parts import submission_milestone_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import study_identity
from med_autoscience.controllers.runtime_supervisor_scan_parts import supervision_contract
from med_autoscience.controllers.runtime_supervisor_scan_parts import workspace_daemon
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import runtime_lifecycle_store
from med_autoscience.developer_supervisor_mode import (
    DeveloperSupervisorMode,
    resolve_developer_supervisor_mode,
)
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
OWNER_PICKUP_OVERDUE_HOURS = 2
DEVELOPER_SUPERVISOR_ATTENTION_HOURS = 6
SUPERVISION_LATEST_RELATIVE_PATH = supervision_contract.SUPERVISION_LATEST_RELATIVE_PATH
SUPERVISION_HISTORY_RELATIVE_PATH = supervision_contract.SUPERVISION_HISTORY_RELATIVE_PATH
SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES = supervision_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES
SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES = supervision_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES
SUPERVISION_FORBIDDEN_ACTIONS = supervision_contract.SUPERVISION_FORBIDDEN_ACTIONS


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _path_or_none(value: object) -> Path | None:
    text = _text(value)
    return Path(text).expanduser().resolve() if text else None


resolve_supervisor_scan_study_ids = study_identity.resolve_supervisor_scan_study_ids


def _latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_HISTORY_RELATIVE_PATH


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _repair_lifecycle_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"


def _clear_resolved_repair_lifecycle(
    *,
    study_root: Path,
    previous_lifecycle: Mapping[str, Any],
    current_lifecycle: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    persist_surfaces: bool,
) -> bool:
    if not persist_surfaces or not developer_mode.safe_actions_enabled:
        return False
    if not previous_lifecycle or current_lifecycle:
        return False
    try:
        _repair_lifecycle_path(study_root).unlink()
    except FileNotFoundError:
        return False
    return True


def _read_last_json_line(path: Path) -> dict[str, Any] | None:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return dict(payload)
    return None


def _parse_utc_datetime(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _duration_hours(*, start_at: object, end_at: object) -> float:
    start = _parse_utc_datetime(start_at)
    end = _parse_utc_datetime(end_at)
    if start is None or end is None or end < start:
        return 0.0
    return round((end - start).total_seconds() / 3600, 3)


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    return runtime_facts.active_run_id(status, progress)


def _worker_running(status: Mapping[str, Any]) -> bool:
    return runtime_facts.worker_running(status)


def _blocking_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    return runtime_facts.blocking_reasons(status, progress)


def _retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return runtime_facts.retry_exhausted(status, progress)


def _publication_eval_payload(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    return canonical_inputs.publication_eval_payload(status, progress)


def _publication_gate_specificity_required(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return gate_specificity_part.publication_gate_specificity_required(
        status=status,
        progress=progress,
        publication_eval_payload=publication_eval_payload,
        blocking_reasons=_blocking_reasons(status, progress),
    )


def _supervisor_only(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return runtime_facts.supervisor_only(status, progress)


def _runtime_platform_repair_required(
    status: Mapping[str, Any], progress: Mapping[str, Any], *, gate_specificity: Mapping[str, Any] | None = None
) -> bool:
    return runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity)


def _decorate_action(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
) -> dict[str, Any]:
    return action_projection.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        control_allowed_write_surfaces=list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _action_queue(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if completion_evidence.completed_current_truth(status, progress):
        return []
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return []
    return action_projection.action_queue(
        status,
        progress,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
        request_allowed_write_surfaces=list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        control_allowed_write_surfaces=list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _why_not_applied(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    return action_projection.why_not_applied(
        status=status,
        progress=progress,
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )


def _why_not_applied_timeline(reason: str | None) -> list[dict[str, Any]]:
    if reason is None:
        return []
    return [{"reason": reason, "state": "blocked", "recorded_at": _utc_now()}]


def _gate_specificity_status(gate_specificity: Mapping[str, Any]) -> dict[str, Any]:
    return gate_specificity_part.gate_specificity_status(gate_specificity)


def _repair_action_payload(*, study_root: Path) -> dict[str, Any] | None:
    return lifecycle_projection.repair_action_payload(study_root=study_root)


def _first_repair_action(repair_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return lifecycle_projection.first_repair_action(repair_payload)


def _sanitize_repair_action_for_supervision(action: Mapping[str, Any]) -> dict[str, Any]:
    return lifecycle_projection.sanitize_repair_action_for_supervision(
        action,
        request_allowed_write_surfaces=list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _blocked_lifecycle_from_repair(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    repair_payload: Mapping[str, Any],
    blocked_reason: str,
    next_owner: str,
) -> dict[str, Any] | None:
    return lifecycle_projection.blocked_lifecycle_from_repair(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        repair_payload=repair_payload,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        control_allowed_write_surfaces=list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        request_allowed_write_surfaces=list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _blocked_reason_from_scan(
    *,
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    return action_projection.blocked_reason_from_scan(
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )


def _required_output_pending(actions: list[dict[str, Any]], ai_reviewer_assessment: Mapping[str, Any]) -> bool:
    if ai_reviewer_assessment.get("missing") is not True:
        return False
    return any(
        _text(action.get("action_type")) == "return_to_ai_reviewer_workflow"
        and _text(action.get("required_output_surface")) == "artifacts/publication_eval/latest.json"
        for action in actions
    )


def _read_study_projection_inputs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], str | None, dict[str, Any]]:
    return canonical_inputs.read_study_projection_inputs(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_reader=study_runtime_router.study_runtime_status,
        progress_reader=study_progress.read_study_progress,
    )


def _attach_study_macro_state(
    *,
    study_id: str,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    return canonical_inputs.attach_study_macro_state(
        study_id=study_id,
        status_payload=status_payload,
        progress_payload=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )


def _maybe_blocked_lifecycle_from_scan(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str | None,
) -> Mapping[str, Any]:
    return lifecycle_projection.maybe_blocked_lifecycle_from_scan(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        control_allowed_write_surfaces=list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        request_allowed_write_surfaces=list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _should_refresh_blocked_lifecycle(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    blocked_reason: str | None,
) -> bool:
    return lifecycle_projection.should_refresh_blocked_lifecycle(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        blocked_reason=blocked_reason,
    )


def _apply_runtime_platform_repair_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    apply_runtime_platform_repair: bool,
    submission_milestone_parked: bool,
) -> tuple[dict[str, Any] | None, Mapping[str, Any] | None]:
    apply_result = platform_repair.apply_runtime_platform_repair(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
        developer_mode=developer_mode,
        enabled=apply_runtime_platform_repair,
        repair_required=evidence_adoption.platform_repair_required_from_scan(
            status=status_payload,
            progress=progress_payload,
            publication_eval_payload=publication_eval_payload,
            study_root=study_root,
            gate_specificity=gate_specificity,
            submission_milestone_parked=submission_milestone_parked,
        ),
        gate_specificity=gate_specificity,
    )
    if apply_result is None:
        return None, None
    lifecycle = platform_repair.write_runtime_platform_repair_lifecycle(
        study_root=study_root,
        supervision_latest_relative_path=SUPERVISION_LATEST_RELATIVE_PATH,
        study_id=study_id,
        quest_id=quest_id,
        apply_result=apply_result,
    )
    return apply_result, lifecycle


def _study_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply_safe_actions: bool,
    apply_runtime_platform_repair: bool,
    developer_mode: DeveloperSupervisorMode,
    persist_surfaces: bool,
    generated_at: str,
    previous_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    status_payload, progress_payload, resolved_quest_id, publication_eval_payload = _read_study_projection_inputs(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status_payload, progress_payload = _attach_study_macro_state(
        study_id=study_id,
        status_payload=status_payload,
        progress_payload=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    submission_milestone_parked_refresh = submission_milestone_projection.refresh_if_platform_repair_required(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=status_payload,
        developer_mode=developer_mode,
        enabled=developer_mode.safe_actions_enabled,
        runtime_platform_repair_required=_runtime_platform_repair_required(status_payload, progress_payload),
    )
    if submission_milestone_projection.applied(submission_milestone_parked_refresh):
        status_payload, progress_payload, resolved_quest_id, publication_eval_payload = _read_study_projection_inputs(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
        )
        status_payload, progress_payload = _attach_study_macro_state(
            study_id=study_id,
            status_payload=status_payload,
            progress_payload=progress_payload,
            publication_eval_payload=publication_eval_payload,
        )
    if submission_milestone_parked_refresh is None:
        submission_milestone_parked_refresh = submission_milestone_projection.reconcile_stopped_parking(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status_payload=status_payload,
            developer_mode=developer_mode,
            enabled=developer_mode.safe_actions_enabled,
        )
        if submission_milestone_projection.applied(submission_milestone_parked_refresh):
            progress_payload = _mapping(
                study_progress.read_study_progress(profile=profile, study_id=study_id, study_root=study_root)
            )
            status_payload, progress_payload = _attach_study_macro_state(
                study_id=study_id,
                status_payload=status_payload,
                progress_payload=progress_payload,
                publication_eval_payload=publication_eval_payload,
            )
    gate_specificity = _publication_gate_specificity_required(
        status_payload,
        progress_payload,
        publication_eval_payload,
    )
    ai_reviewer_assessment = ai_reviewer.assessment(
        status=status_payload,
        progress=progress_payload,
        publication_eval=publication_eval_payload,
        blocking_reasons=_blocking_reasons(status_payload, progress_payload),
    )
    actions = _action_queue(
        status_payload,
        progress_payload,
        study_root=study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
        publication_eval_payload=publication_eval_payload,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    artifact_blocked_action = artifact_freshness.blocked_action_from_gate_clearing(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if artifact_blocked_action is not None:
        actions = block_state_part.remove_action_type(actions, "runtime_platform_repair")
        actions = block_state_part.remove_action_type(actions, "current_package_freshness_required")
        actions = block_state_part.remove_action_type(actions, "return_to_ai_reviewer_workflow")
        actions.insert(
            0,
            _decorate_action(
                study_id=study_id,
                quest_id=resolved_quest_id,
                action=artifact_blocked_action,
            ),
        )
    if developer_mode.mode == "external_observe":
        actions = []
    initial_lifecycle = _mapping(progress_payload.get("ai_repair_lifecycle"))
    lifecycle = initial_lifecycle
    lifecycle = _mapping(_maybe_blocked_lifecycle_from_scan(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
        study_root=study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
    ))
    if completion_evidence.completed_current_truth(status_payload, progress_payload):
        lifecycle = {}
    if parked_truth.current_truth(
        status_payload,
        progress_payload,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        lifecycle = {}
    submission_milestone_parked = (
        _text(_mapping(submission_milestone_parked_refresh).get("dispatch_status")) == "applied"
    )
    if submission_milestone_parked:
        lifecycle = _mapping(_mapping(submission_milestone_parked_refresh).get("repair_lifecycle"))
    runtime_platform_repair_apply, platform_lifecycle = _apply_runtime_platform_repair_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=resolved_quest_id,
        status_payload=status_payload,
        progress_payload=progress_payload,
        publication_eval_payload=publication_eval_payload,
        gate_specificity=gate_specificity,
        developer_mode=developer_mode,
        apply_runtime_platform_repair=apply_runtime_platform_repair,
        submission_milestone_parked=submission_milestone_parked,
    )
    if platform_lifecycle is not None:
        lifecycle = _mapping(platform_lifecycle)
    adoption_projected = False
    status_payload, progress_payload, adoption_projected = applied_repair_merge.merge_evidence_adoption_projection(
        status=status_payload,
        progress=progress_payload,
        apply_result=runtime_platform_repair_apply,
    )
    if adoption_projected:
        status_payload, progress_payload = _attach_study_macro_state(
            study_id=study_id,
            status_payload=status_payload,
            progress_payload=progress_payload,
            publication_eval_payload=publication_eval_payload,
        )
        gate_specificity = _publication_gate_specificity_required(
            status_payload,
            progress_payload,
            publication_eval_payload,
        )
        ai_reviewer_assessment = ai_reviewer.assessment(
            status=status_payload,
            progress=progress_payload,
            publication_eval=publication_eval_payload,
            blocking_reasons=_blocking_reasons(status_payload, progress_payload),
        )
        actions = _action_queue(
            status_payload,
            progress_payload,
            study_root=study_root,
            study_id=study_id,
            quest_id=resolved_quest_id,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
            ai_reviewer_assessment=ai_reviewer_assessment,
        )
        if developer_mode.mode == "external_observe":
            actions = []
    if applied_repair_merge.applied(runtime_platform_repair_apply):
        status_payload, progress_payload, resolved_quest_id, publication_eval_payload = _read_study_projection_inputs(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
        )
        status_payload, progress_payload = applied_repair_merge.merge_runtime_fact(
            status=status_payload,
            progress=progress_payload,
            apply_result=runtime_platform_repair_apply,
        )
        status_payload, progress_payload = _attach_study_macro_state(
            study_id=study_id,
            status_payload=status_payload,
            progress_payload=progress_payload,
            publication_eval_payload=publication_eval_payload,
        )
        gate_specificity = _publication_gate_specificity_required(
            status_payload,
            progress_payload,
            publication_eval_payload,
        )
        ai_reviewer_assessment = ai_reviewer.assessment(
            status=status_payload,
            progress=progress_payload,
            publication_eval=publication_eval_payload,
            blocking_reasons=_blocking_reasons(status_payload, progress_payload),
        )
        actions = _action_queue(
            status_payload,
            progress_payload,
            study_root=study_root,
            study_id=study_id,
            quest_id=resolved_quest_id,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
            ai_reviewer_assessment=ai_reviewer_assessment,
        )
    lifecycle = evidence_adoption.resolved_lifecycle(status_payload, lifecycle)
    if block_state_part.runtime_relaunch_lifecycle_resolved(
        status=status_payload,
        progress=progress_payload,
        lifecycle=lifecycle,
    ):
        lifecycle = {}
    if block_state_part.projection_only_runtime_recovery_lifecycle_resolved(
        status=status_payload,
        progress=progress_payload,
        lifecycle=lifecycle,
    ):
        lifecycle = {}
    if applied_repair_merge.applied(runtime_platform_repair_apply):
        actions = block_state_part.remove_action_type(actions, "runtime_platform_repair")
    if (
        runtime_platform_repair_apply is not None
        and _text(runtime_platform_repair_apply.get("dispatch_status")) == "blocked"
        and _text(runtime_platform_repair_apply.get("reason")) == "publication_gate_specificity_required"
    ):
        actions = block_state_part.remove_action_type(actions, "runtime_platform_repair")
        if not any(_text(action.get("action_type")) == "publication_gate_specificity_required" for action in actions):
            actions.insert(
                0,
                _decorate_action(
                    study_id=study_id,
                    quest_id=resolved_quest_id,
                    action=publication_gate_actions.action_payload(gate_specificity=gate_specificity),
                ),
            )
    if artifact_freshness.route_required(runtime_platform_repair_apply):
        actions = artifact_freshness.remove_runtime_platform_repair(actions)
        if any(_text(action.get("action_type")) == "artifact_display_surface_materialization_required" for action in actions):
            actions = block_state_part.remove_action_type(actions, "current_package_freshness_required")
        elif not any(_text(action.get("action_type")) == "current_package_freshness_required" for action in actions):
            actions.insert(
                0,
                _decorate_action(
                    study_id=study_id,
                    quest_id=resolved_quest_id,
                    action=artifact_freshness.action_payload(),
                ),
            )
    why_not_applied = status_projection.resolve_why_not_applied(
        default_why_not_applied=_why_not_applied(
            status=status_payload,
            progress=progress_payload,
            actions=actions,
            gate_specificity=gate_specificity,
            ai_reviewer_assessment=ai_reviewer_assessment,
        ),
        actions=actions,
        lifecycle=lifecycle,
        runtime_platform_repair_apply=runtime_platform_repair_apply,
        submission_milestone_parked=submission_milestone_parked,
    )
    block_state = block_state_part.projection_block_state(
        status=status_payload,
        progress=progress_payload,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        lifecycle=lifecycle,
        actions=actions,
        why_not_applied=why_not_applied,
    )
    supervisor_only_live_quality_repair = (
        _supervisor_only(status_payload, progress_payload)
        and artifact_freshness.meaningful_artifact_delta_observed(progress_payload)
        and _active_run_id(status_payload, progress_payload) is not None
        and not actions
    )
    next_owner = (
        "supervisor_only/live_quality_repair"
        if supervisor_only_live_quality_repair
        else block_state["next_owner"] or ("external_supervisor" if block_state["external_supervisor_required"] else None)
    )
    blocked_reason = block_state["blocked_reason"] or why_not_applied
    owner_route, actions = owner_route_part.route_and_decorate_actions(
        study_id=study_id,
        quest_id=resolved_quest_id,
        status=status_payload,
        progress=progress_payload,
        actions=actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        active_run_id=_active_run_id(status_payload, progress_payload),
    )
    actions = [
        action
        for action in actions
        if owner_route_part.route_allows_action(action=action, owner_route=owner_route)
    ]
    paper_progress_stall_payload, actions = paper_progress_stall_projection.build_and_attach(
        status=status_payload,
        progress=progress_payload,
        owner_route=owner_route,
        actions=actions,
    )
    repeat_guard = repeat_suppression.scan_repeat_suppression(
        previous_payload=previous_payload,
        study_id=study_id,
        owner_route=owner_route,
        current_meaningful_artifact_delta=artifact_freshness.meaningful_artifact_delta_observed(progress_payload),
        required_output_pending=_required_output_pending(actions, ai_reviewer_assessment),
    )
    if repeat_guard["repeat_suppressed"]:
        actions = []
        why_not_applied = repeat_suppression.REPEAT_SUPPRESSED_REASON
        blocked_reason = repeat_suppression.REPEAT_SUPPRESSED_REASON
    if developer_mode.safe_actions_enabled:
        request_packets.materialize_request_packets(
            study_root=study_root,
            workspace_root=profile.workspace_root,
            study_id=study_id,
            quest_id=resolved_quest_id,
            quest_root=_path_or_none(status_payload.get("quest_root")),
            publication_eval_payload=publication_eval_payload,
            actions=actions,
        )
    recovery_intent = recovery_intent_ledger.project_recovery_intent(
        study_id=study_id,
        quest_id=resolved_quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        owner_route=owner_route,
        action_queue=actions,
        generated_at=generated_at,
        persist=persist_surfaces,
    )
    _clear_resolved_repair_lifecycle(
        study_root=study_root,
        previous_lifecycle=initial_lifecycle,
        current_lifecycle=lifecycle,
        developer_mode=developer_mode,
        persist_surfaces=persist_surfaces,
    )
    supervision = _mapping(progress_payload.get("supervision"))
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": resolved_quest_id,
        "quest_root": _text(status_payload.get("quest_root")) or _text(progress_payload.get("quest_root")),
        "quest_status": _text(status_payload.get("quest_status")),
        "current_stage": _text(progress_payload.get("current_stage")),
        "active_run_id": _active_run_id(status_payload, progress_payload),
        "supervision_url": _text(supervision.get("browser_url")),
        "paper_stage": _text(progress_payload.get("paper_stage")),
        "runtime_health": _mapping(status_payload.get("runtime_health_snapshot"))
        or _mapping(progress_payload.get("runtime_health_snapshot")),
        "meaningful_artifact_delta": artifact_freshness.meaningful_artifact_delta_observed(progress_payload),
        "artifact_delta": artifact_freshness.artifact_delta(progress_payload),
        "gate_specificity": _gate_specificity_status(gate_specificity),
        "ai_reviewer_assessment": ai_reviewer_assessment,
        "ai_reviewer_status": ai_reviewer.status(ai_reviewer_assessment),
        "ai_repair_lifecycle": lifecycle or None,
        "action_queue": actions,
        "submission_milestone_parked_refresh": submission_milestone_parked_refresh,
        "runtime_platform_repair_apply": runtime_platform_repair_apply,
        "recovery_intent": recovery_intent,
        "paper_progress_stall": paper_progress_stall_payload,
        "owner_route": owner_route,
        "repeat_suppression": repeat_guard,
        "why_not_applied": why_not_applied,
        "why_not_applied_timeline": _why_not_applied_timeline(why_not_applied),
        "escalation_reason": why_not_applied,
        "next_owner": next_owner,
        "blocked_reason": blocked_reason,
        "external_supervisor_required": block_state["external_supervisor_required"],
        "supervisor_only": _supervisor_only(status_payload, progress_payload),
        "paper_package_mutated": False,
        "apply_safe_actions": developer_mode.safe_actions_enabled,
        "developer_supervisor_mode": developer_mode.to_dict(),
        "refs": {"recovery_intent_path": str(recovery_intent_ledger.latest_path_for_study(study_root))},
    }


def supervisor_scan(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    apply_safe_actions: bool = False,
    apply_runtime_platform_repair: bool = False,
    developer_supervisor_mode: str | None = None,
    persist_surfaces: bool = True,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    study_identity.validate_supervisor_scan_study_ids(profile, resolved_study_ids)
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=developer_supervisor_mode,
        apply_safe_actions=apply_safe_actions,
        scheduler_owner="portable_supervisor",
    )
    latest_path = _latest_path(profile)
    history_path = _history_path(profile)
    previous_payload = _read_json_object(latest_path)
    previous_action_ids = {
        _text(action.get("action_id"))
        for action in (_mapping(previous_payload).get("action_queue") if previous_payload is not None else []) or []
        if isinstance(action, Mapping)
    }
    previous_action_ids.discard(None)
    studies: list[dict[str, Any]] = []
    for study_id in resolved_study_ids:
        try:
            study_projection = _study_projection(
                profile=profile,
                study_id=study_id,
                apply_safe_actions=apply_safe_actions,
                apply_runtime_platform_repair=apply_runtime_platform_repair,
                developer_mode=developer_mode,
                persist_surfaces=persist_surfaces,
                generated_at=generated_at,
                previous_payload=previous_payload,
            )
        except (ValueError, TypeError) as exc:
            study_root = _study_root(profile, study_id)
            reason = projection_errors.PROJECTION_CONTRACT_ERROR_REASON
            study_projection = projection_errors.projection_error_study(
                study_id=study_id,
                study_root=study_root,
                developer_mode_payload=developer_mode.to_dict(),
                safe_actions_enabled=developer_mode.safe_actions_enabled,
                generated_at=generated_at,
                error=exc,
                recovery_intent_path=recovery_intent_ledger.latest_path_for_study(study_root),
                why_not_applied_timeline=_why_not_applied_timeline(reason),
            )
        studies.append(study_projection)
    queue_slo_payload = queue_slo.decorate_action_queue_slo(
        studies=studies,
        previous_payload=previous_payload,
        generated_at=generated_at,
    )
    action_queue = [
        {"study_id": study["study_id"], **action}
        for study in studies
        for action in study.get("action_queue", [])
        if isinstance(action, Mapping)
    ]
    for study in studies:
        study_actions = [
            action
            for action in study.get("action_queue", [])
            if isinstance(action, Mapping) and _text(action.get("action_id")) is not None
        ]
        study["scan_delta"] = {
            "previous_scan_seen": any(_text(action.get("action_id")) in previous_action_ids for action in study_actions),
            "new_action_count": sum(_text(action.get("action_id")) not in previous_action_ids for action in study_actions),
            "owner_pickup_overdue_count": int(_mapping(study.get("queue_slo")).get("owner_pickup_overdue_count") or 0),
            "developer_supervisor_attention_required_count": int(
                _mapping(study.get("queue_slo")).get("developer_supervisor_attention_required_count") or 0
            ),
        }
    queue_history = {
        "history_path": str(history_path),
        "latest_action_count": len(action_queue),
        "previous_action_count": len(previous_action_ids),
        **queue_slo_payload,
    }
    workspace_daemon_lifecycle = workspace_daemon.workspace_daemon_lifecycle(
        profile=profile,
        developer_mode=developer_mode,
    )
    payload = scan_output.build_supervisor_scan_payload(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        workspace_root=profile.workspace_root,
        developer_mode_payload=developer_mode.to_dict(),
        safe_actions_enabled=developer_mode.safe_actions_enabled,
        apply_runtime_platform_repair=apply_runtime_platform_repair,
        two_layer_ai_repair_policy=two_layer_ai_repair_policy_payload(),
        studies=studies,
        action_queue=action_queue,
        queue_history=queue_history,
        workspace_daemon_lifecycle=workspace_daemon_lifecycle,
        latest_path=latest_path,
        history_path=history_path,
    )
    if persist_surfaces:
        scan_output.persist_supervisor_scan_payload(
            payload=payload,
            studies=studies,
            action_queue=action_queue,
            profile=profile,
            latest_path=latest_path,
            history_path=history_path,
            generated_at=generated_at,
            resolved_study_ids=resolved_study_ids,
            runtime_lifecycle_store=runtime_lifecycle_store,
            study_root_for_id=lambda value: _study_root(profile, value),
            write_json=_write_json,
            append_json_line=_append_json_line,
            text=_text,
            mapping=_mapping,
        )
    return payload


__all__ = [
    "SCHEMA_VERSION",
    "SUPERVISION_LATEST_RELATIVE_PATH",
    "supervisor_scan",
]
