from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.owner_route_reconcile_parts import action_decorators
from med_autoscience.controllers.owner_route_reconcile_parts import analysis_harmonization_ai_review
from med_autoscience.controllers.owner_route_reconcile_parts import artifact_freshness
from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions
from med_autoscience.controllers.owner_route_reconcile_parts import completion_evidence
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions
from med_autoscience.controllers.owner_route_reconcile_parts import evidence_adoption
from med_autoscience.controllers.owner_route_reconcile_parts import methodology_reframe_actions
from med_autoscience.controllers.owner_route_reconcile_parts import parked_truth
from med_autoscience.controllers.owner_route_reconcile_parts import recovery_actions
from med_autoscience.controllers.owner_route_reconcile_parts import runtime_facts
from med_autoscience.controllers.owner_route_reconcile_parts import story_surface_delta_actions


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
    methodology_reframe_action = methodology_reframe_actions.methodology_reframe_route_decision_action(study_root)
    if methodology_reframe_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=methodology_reframe_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    provenance_limited_action = methodology_reframe_actions.provenance_limited_harmonization_audit_action(study_root)
    if provenance_limited_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=provenance_limited_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    direct_rebuild_route_action = methodology_reframe_actions.clean_rebuild_route_action(study_root)
    if direct_rebuild_route_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=direct_rebuild_route_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    rebuild_route_action = recovery_actions.provenance_limited_rebuild_route_action(study_root)
    if rebuild_route_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=rebuild_route_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    source_provenance_action = recovery_actions.source_provenance_recovery_action(study_root)
    if source_provenance_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=source_provenance_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    hard_methodology_action = recovery_actions.hard_methodology_quality_repair_handoff_action(study_root)
    if hard_methodology_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=hard_methodology_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    rehydrate_action = recovery_actions.clean_paper_authority_rehydrate_action(
        status=status,
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if rehydrate_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=rehydrate_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    if recovery_actions.clean_paper_authority_cutover_ai_reviewer_required(
        publication_eval_payload=publication_eval_payload,
        ai_reviewer_assessment=ai_reviewer_assessment,
    ):
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_actions.ai_reviewer_required_action(reason="paper_authority_clean_migration_required"),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    analysis_handoff_action = analysis_harmonization_ai_review.completed_ai_reviewer_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if analysis_handoff_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=analysis_handoff_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    record_production_action = _ai_reviewer_record_production_transition_action(
        status=status,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    if record_production_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=record_production_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    if _explicit_ai_reviewer_record_current_manuscript_request_pending(ai_reviewer_assessment):
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=_ai_reviewer_record_current_manuscript_action(ai_reviewer_assessment),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    story_surface_action = story_surface_delta_actions.write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if story_surface_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=story_surface_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    if ai_reviewer_actions.stale_reviewer_revision_required(ai_reviewer_assessment):
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_actions.ai_reviewer_required_action(
                    reason=ai_reviewer_actions.STALE_AFTER_REVIEWER_REVISION_REASON
                ),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
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
    if (
        _explicit_ai_reviewer_request_pending(ai_reviewer_assessment)
        and not _higher_priority_owner_truth_blocks_pending_ai_reviewer_request(
            status=status,
            progress=progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
        )
    ):
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_actions.ai_reviewer_required_action(
                    reason=_text(ai_reviewer_assessment.get("blocked_reason")) or "ai_reviewer_assessment_required"
                ),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    oracle_actions = domain_transition_actions.actions(status)
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
    owner_handoff_action = _owner_handoff_action(status)
    if owner_handoff_action is not None:
        actions.append(owner_handoff_action)
    if gate_specificity.get("required") is True:
        from med_autoscience.controllers.owner_route_reconcile_parts import publication_gate_actions

        actions.append(publication_gate_actions.action_payload(gate_specificity=gate_specificity))
    artifact_action = _current_package_freshness_lifecycle_action(
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if artifact_action is not None:
        actions = [action for action in actions if _text(action.get("action_type")) != artifact_freshness.ACTION_TYPE]
        actions.insert(0, artifact_action)
    if (
        not actions
        and ai_reviewer_assessment.get("missing") is True
        and not _higher_priority_owner_truth_blocks_generic_ai_reviewer(
            status=status,
            progress=progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
        )
    ):
        actions.append(
            ai_reviewer_actions.ai_reviewer_required_action(
                reason=_text(ai_reviewer_assessment.get("blocked_reason")) or "ai_reviewer_assessment_required"
            )
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


def _ai_reviewer_record_production_transition_action(
    *,
    status: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> dict[str, Any] | None:
    transition = _mapping(status.get("domain_transition"))
    if _text(transition.get("decision_type")) != "ai_reviewer_re_eval":
        return None
    next_work_unit = _mapping(transition.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    reason = _record_production_reason_for_work_unit(work_unit_id)
    if reason is None:
        return None
    action = ai_reviewer_actions.ai_reviewer_required_action(reason=reason)
    action["summary"] = (
        "Produce a current AI reviewer publication-eval record before refreshing "
        "publication_eval/latest.json."
    )
    action["required_output_surface"] = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    action["next_work_unit"] = work_unit_id
    action["executable_work_unit"] = work_unit_id
    action["controller_work_unit_id"] = work_unit_id
    action["domain_transition_decision_type"] = "ai_reviewer_re_eval"
    action["controller_next_work_unit"] = next_work_unit
    action["publication_eval_latest_write_allowed"] = False
    action["controller_decision_write_allowed"] = False
    action["record_only_surface"] = True
    if required_refs := _string_items(ai_reviewer_assessment.get("required_currentness_refs")):
        action["required_currentness_refs"] = required_refs
    if stale_record_ref := _text(ai_reviewer_assessment.get("stale_record_ref")):
        action["stale_record_ref"] = stale_record_ref
    if source_ref := _text(ai_reviewer_assessment.get("source_ref")):
        action["source_ref"] = source_ref
    return action


def _record_production_reason_for_work_unit(work_unit_id: str | None) -> str | None:
    if work_unit_id == "produce_ai_reviewer_publication_eval_record_against_current_manuscript":
        return ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    if work_unit_id == "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization":
        return ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON
    return None


def _explicit_ai_reviewer_request_pending(ai_reviewer_assessment: Mapping[str, Any]) -> bool:
    return (
        ai_reviewer_assessment.get("missing") is True
        and _text(ai_reviewer_assessment.get("request_state")) in {"requested", "assigned"}
    )


def _explicit_ai_reviewer_record_current_manuscript_request_pending(
    ai_reviewer_assessment: Mapping[str, Any],
) -> bool:
    return (
        _explicit_ai_reviewer_request_pending(ai_reviewer_assessment)
        and _text(ai_reviewer_assessment.get("blocked_reason"))
        == ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    )


def _ai_reviewer_record_current_manuscript_action(
    ai_reviewer_assessment: Mapping[str, Any],
) -> dict[str, Any]:
    action = ai_reviewer_actions.ai_reviewer_required_action(
        reason=ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    )
    action["summary"] = (
        "The request-bound AI reviewer record predates the current manuscript; produce a new AI reviewer "
        "publication-eval record against the current manuscript before refreshing publication_eval/latest.json."
    )
    if required_refs := _string_items(ai_reviewer_assessment.get("required_currentness_refs")):
        action["required_currentness_refs"] = required_refs
    if stale_record_ref := _text(ai_reviewer_assessment.get("stale_record_ref")):
        action["stale_record_ref"] = stale_record_ref
    if source_ref := _text(ai_reviewer_assessment.get("source_ref")):
        action["source_ref"] = source_ref
    return action


def _higher_priority_owner_truth_blocks_pending_ai_reviewer_request(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
) -> bool:
    if completion_evidence.completed_current_truth(status, progress):
        return True
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    if gate_specificity.get("required") is True:
        return True
    if analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if provenance_limited_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if source_provenance_owner_result.typed_blocker_state(study_root=study_root):
        return True
    return False


def _higher_priority_owner_truth_blocks_generic_ai_reviewer(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
) -> bool:
    if completion_evidence.completed_current_truth(status, progress):
        return True
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    if gate_specificity.get("required") is True:
        return True
    if analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if provenance_limited_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if source_provenance_owner_result.typed_blocker_state(study_root=study_root):
        return True
    return False


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
    if study_root is not None:
        provenance_limited_state = provenance_limited_harmonization_owner_result.typed_blocker_state(
            study_root=study_root
        )
        if provenance_limited_state:
            return _text(provenance_limited_state.get("blocked_reason"))
        if any(_text(action.get("action_type")) == "provenance_limited_harmonization_audit" for action in actions):
            return "provenance_limited_harmonization_audit_required"
        methodology_decision_requests_audit = (
            provenance_limited_harmonization_owner_result.current_controller_decision_requests_audit(
                study_root=study_root
            )
        )
        source_result_state = source_provenance_owner_result.typed_blocker_state(study_root=study_root)
        if source_result_state and not methodology_decision_requests_audit:
            return _text(source_result_state.get("blocked_reason"))
        owner_result_state = analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root)
        if owner_result_state:
            return _text(owner_result_state.get("blocked_reason"))
    if _has_source_provenance_handoff_action(actions):
        return "transport_model_provenance_recovery_required"
    if _has_hard_methodology_handoff_action(actions):
        return "unit_harmonized_rerun_required"
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
        return reason
    if runtime_facts.opl_stage_attempt_admission_required(status, progress):
        return current_truth_owner.OPL_STAGE_ATTEMPT_ADMISSION_REASON
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
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
        if text in {
            ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON,
            ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON,
        } and (
            ai_reviewer_assessment.get("present") is True
            and _text(ai_reviewer_assessment.get("owner")) == "ai_reviewer"
        ):
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


def _has_hard_methodology_handoff_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "unit_harmonized_external_validation_rerun"
        and _text(action.get("reason")) == "unit_harmonized_rerun_required"
        and _text(action.get("owner")) == "analysis_harmonization_owner"
        for action in actions
    )


def _has_source_provenance_handoff_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "recover_transport_model_provenance"
        and _text(action.get("reason")) == "transport_model_provenance_recovery_required"
        and _text(action.get("owner")) == "source_provenance_owner"
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
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "return_to_ai_reviewer_workflow",
            "canonical_paper_inputs_rehydrate_required",
            "run_quality_repair_batch",
            "unit_harmonized_external_validation_rerun",
            "recover_transport_model_provenance",
            "methodology_reframe_route_decision",
            "provenance_limited_harmonization_audit",
        }:
            return _text(action.get("reason")) or _text(action.get("action_type"))
    if gate_specificity.get("required") is True:
        return "publication_gate_specificity_required"
    if ai_reviewer_assessment.get("missing") is True:
        return "ai_reviewer_assessment_required"
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
