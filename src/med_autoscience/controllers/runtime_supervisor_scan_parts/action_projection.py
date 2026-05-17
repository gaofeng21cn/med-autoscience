from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import action_decorators
from med_autoscience.controllers.runtime_supervisor_scan_parts import artifact_freshness
from med_autoscience.controllers.runtime_supervisor_scan_parts import completion_evidence
from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.runtime_supervisor_scan_parts import evidence_adoption
from med_autoscience.controllers.runtime_supervisor_scan_parts import parked_truth
from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts


def action_queue(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
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
    ai_reviewer_freshness_action = artifact_freshness.blocked_action_from_ai_reviewer_freshness_mismatch(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if ai_reviewer_freshness_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_freshness_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    oracle_actions = _domain_transition_actions(status)
    if oracle_actions is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
            for action in oracle_actions
        ]
    actions: list[dict[str, Any]] = []
    if (
        runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity)
        or runtime_facts.live_activity_timeout_current_controller_route_available(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or runtime_facts.current_controller_route_redrive_required(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
        )
        or runtime_facts.current_controller_owner_handoff_redrive_required(
            status=status,
            progress=progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or _external_supervisor_runtime_repair_required(status, progress)
    ):
        actions.append(
            current_truth_owner.runtime_platform_repair_action(
                study_root=study_root,
                status=status,
                publication_eval_payload=publication_eval_payload,
                default_reason=_external_supervisor_runtime_repair_reason(status, progress)
                or current_truth_owner.runtime_platform_repair_reason(status, progress),
            )
        )
    owner_handoff_action = _owner_handoff_action(status)
    if owner_handoff_action is not None:
        actions.append(owner_handoff_action)
    if gate_specificity.get("required") is True:
        from med_autoscience.controllers.runtime_supervisor_scan_parts import publication_gate_actions

        actions.append(publication_gate_actions.action_payload(gate_specificity=gate_specificity))
    artifact_action = _current_package_freshness_lifecycle_action(
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if artifact_action is not None:
        actions = [
            action
            for action in actions
            if _text(action.get("action_type")) not in {"runtime_platform_repair", artifact_freshness.ACTION_TYPE}
        ]
        actions.insert(0, artifact_action)
    if ai_reviewer_assessment.get("missing") is True:
        actions.append(
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "authority": "observability_only",
                "owner": "ai_reviewer",
                "request_owner": "ai_reviewer",
                "recommended_owner": "ai_reviewer",
                "reason": "ai_reviewer_assessment_required",
                "summary": "Request an AI reviewer-owned publication_eval assessment.",
                "required_output_surface": "artifacts/publication_eval/latest.json",
                "paper_package_mutation_allowed": False,
            }
        )
    return [
        decorate_action(
            study_id=study_id,
            quest_id=quest_id,
            action=action,
            request_allowed_write_surfaces=request_allowed_write_surfaces,
            control_allowed_write_surfaces=control_allowed_write_surfaces,
            forbidden_actions=forbidden_actions,
        )
        for action in actions
    ]


def _domain_transition_actions(status: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    if domain_transition_guard.blocks_auto_redrive(status):
        return []
    action_type = domain_transition_guard.supported_action_type(status)
    if action_type is None:
        return None
    decision_type = domain_transition_guard.decision_type(status)
    work_unit_id = domain_transition_guard.next_work_unit_id(status)
    owner = domain_transition_guard.owner(status) or _owner_for_domain_action(action_type)
    reason = domain_transition_guard.reason(status) or f"domain_transition_{decision_type or 'current'}"
    action: dict[str, Any] = {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": reason,
        "summary": "MAS domain transition oracle selected the current owner work unit.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": work_unit_id,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    if decision_type == "bundle_stage_finalize":
        action["authority"] = "observability_only"
        action["owner"] = "mas_controller"
        action["request_owner"] = "mas_controller"
        action["recommended_owner"] = "mas_controller"
        action["reason"] = current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        action["summary"] = (
            "MAS domain transition oracle selected bundle-stage finalization; redrive the current "
            "controller route instead of repeating a stale analysis or write work unit."
        )
        action["controller_route_required"] = True
        action["domain_transition_decision_type"] = decision_type
    elif decision_type == "publication_gate_blocker":
        action["summary"] = (
            "MAS domain transition oracle selected the publication gate blocker owner route."
        )
        action["controller_action"] = "run_gate_clearing_batch"
        action["domain_transition_decision_type"] = decision_type
    return [
        action
    ]


def _owner_for_domain_action(action_type: str) -> str:
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "runtime_platform_repair":
        return "mas_controller"
    return "med-autoscience"


def _owner_handoff_action(status: Mapping[str, Any]) -> dict[str, Any] | None:
    next_route = _mapping(status.get("controller_work_unit_next_route"))
    if _text(next_route.get("recommended_next_route")) != "handoff_to_next_owner":
        return None
    if next_route.get("runtime_relaunch_required") is not False:
        return None
    owner = _text(next_route.get("owner"))
    next_work_unit = _text(next_route.get("next_work_unit"))
    if owner is None or next_work_unit is None:
        return None
    return {
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": evidence_adoption.OWNER_HANDOFF_REASON,
        "summary": "Advance the exhausted analysis work unit to the next owner without redriving the same fingerprint.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": next_work_unit,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _current_package_freshness_lifecycle_action(
    *,
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return None
    top_action = _mapping(lifecycle.get("top_action"))
    if top_action.get("auto_apply_allowed") is not True and lifecycle.get("auto_apply_allowed") is not True:
        return None
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason == artifact_freshness.ACTION_TYPE:
        source_blocked_reason = blocked_reason
    elif blocked_reason in {
        "controller_decision_not_superseded",
        "stale_specificity_terminal_gate_not_found",
    } and _text(top_action.get("action_type")) == "runtime_platform_repair":
        source_blocked_reason = blocked_reason
    else:
        return None
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    if _text(controller_route.get("work_unit_id")) != "submission_minimal_refresh":
        return None
    if "run_gate_clearing_batch" not in set(_string_items(controller_route.get("controller_actions"))):
        return None
    return artifact_freshness.action_payload(
        reason=artifact_freshness.ACTION_TYPE,
        controller_route=controller_route,
        source_blocked_reason=source_blocked_reason,
    )


def decorate_action(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any]:
    return action_decorators.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        control_allowed_write_surfaces=control_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    )


def why_not_applied(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    if completion_evidence.completed_current_truth(status, progress):
        return None
    study_root = _path(_text(status.get("study_root")) or _text(progress.get("study_root")))
    publication_eval_payload = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return None
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if reason := evidence_adoption.why_not_applied(status):
        if not _has_controller_redrive_action(actions):
            return reason
    if runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity):
        for action in actions:
            if _text(action.get("action_type")) == "runtime_platform_repair":
                return _text(action.get("reason")) or current_truth_owner.runtime_platform_repair_reason(status, progress)
        return current_truth_owner.runtime_platform_repair_reason(status, progress)
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
        for action in actions:
            if _text(action.get("action_type")) == "runtime_platform_repair":
                return _text(action.get("reason")) or current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if any(
        _text(action.get("action_type")) == "runtime_platform_repair"
        and _text(action.get("reason")) == current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        for action in actions
    ):
        return current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if runtime_facts.retry_exhausted(status, progress):
        if gate_specificity.get("required") is True:
            return "publication_gate_specificity_required"
        return "runtime_recovery_retry_budget_exhausted"
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    if text := _text(lifecycle.get("blocked_reason")):
        if text == "ai_reviewer_assessment_required" and ai_reviewer_assessment.get("missing") is not True:
            return None
        if (
            text == "runtime_relaunch_no_live_run_started"
            and runtime_facts.active_run_id(status, progress) is not None
            and runtime_facts.worker_running(status)
        ):
            return None
        if (
            text == "runtime_recovery_not_authorized"
            and runtime_facts.runtime_recovery_lifecycle_resolved(
                status=status,
                progress=progress,
                lifecycle=lifecycle,
            )
        ):
            return None
        return text
    return None


def _has_controller_redrive_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "runtime_platform_repair"
        and _text(action.get("reason")) == current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        for action in actions
    )


def blocked_reason_from_scan(
    *,
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    for action in actions:
        if _text(action.get("action_type")) in {
            "runtime_platform_repair",
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "return_to_ai_reviewer_workflow",
        }:
            return _text(action.get("reason")) or _text(action.get("action_type"))
    if gate_specificity.get("required") is True:
        return "publication_gate_specificity_required"
    if ai_reviewer_assessment.get("missing") is True:
        return "ai_reviewer_assessment_required"
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _external_supervisor_runtime_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return _external_supervisor_runtime_repair_reason(status, progress) is not None


def _external_supervisor_runtime_repair_reason(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    if runtime_facts.active_run_id(status, progress) is not None and runtime_facts.worker_running(status):
        return None
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return None
    if lifecycle.get("external_supervisor_required") is not True:
        return None
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason != "runtime_recovery_not_authorized":
        return None
    top_action = _mapping(lifecycle.get("top_action"))
    if (
        _text(top_action.get("action_type")) == "controller_repair"
        and _text(top_action.get("repair_kind")) == "bounded_work_unit_redrive"
        and top_action.get("auto_apply_allowed") is True
    ):
        return blocked_reason
    return None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


__all__ = [
    "action_queue",
    "blocked_reason_from_scan",
    "decorate_action",
    "why_not_applied",
]
