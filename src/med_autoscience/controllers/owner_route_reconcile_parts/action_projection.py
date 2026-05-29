from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import ai_reviewer_owner_output_consumption
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.owner_route_reconcile_parts import action_decorators
from med_autoscience.controllers.owner_route_reconcile_parts import analysis_harmonization_ai_review
from med_autoscience.controllers.owner_route_reconcile_parts import artifact_freshness
from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions
from med_autoscience.controllers.owner_route_reconcile_parts import claim_evidence_alignment_actions
from med_autoscience.controllers.owner_route_reconcile_parts import completion_evidence
from med_autoscience.controllers.owner_route_reconcile_parts import current_ai_reviewer_record_actions
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions
from med_autoscience.controllers.owner_route_reconcile_parts import evidence_adoption
from med_autoscience.controllers.owner_route_reconcile_parts import methodology_reframe_actions
from med_autoscience.controllers.owner_route_reconcile_parts import parked_truth
from med_autoscience.controllers.owner_route_reconcile_parts import recovery_actions
from med_autoscience.controllers.owner_route_reconcile_parts import runtime_facts
from med_autoscience.controllers.owner_route_reconcile_parts import story_surface_delta_actions


REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")
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
    current_ai_reviewer_write_action = story_surface_delta_actions.write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if current_ai_reviewer_write_action is not None:
        request_lifecycle = ai_reviewer_owner_output_consumption.current_request_lifecycle(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        current_ai_reviewer_write_action = ai_reviewer_owner_output_consumption.with_owner_output_consumption(
            payload=current_ai_reviewer_write_action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=current_ai_reviewer_write_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    record_production_action = current_ai_reviewer_record_actions.record_production_transition_action(
        status=status,
        ai_reviewer_assessment=ai_reviewer_assessment,
        publication_eval_payload=publication_eval_payload,
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
    request_lifecycle = ai_reviewer_owner_output_consumption.current_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    submission_refresh_action = _gate_replay_submission_refresh_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if submission_refresh_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=submission_refresh_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    gate_replay_write_action = story_surface_delta_actions.gate_replay_write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if gate_replay_write_action is not None:
        gate_replay_write_action = ai_reviewer_owner_output_consumption.with_owner_output_consumption(
            payload=gate_replay_write_action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=gate_replay_write_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    current_ai_reviewer_gate_replay_action = current_ai_reviewer_record_actions.gate_replay_action(
        ai_reviewer_assessment=ai_reviewer_assessment,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if current_ai_reviewer_gate_replay_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=current_ai_reviewer_gate_replay_action,
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
                action=ai_reviewer_owner_output_consumption.current_manuscript_record_action(
                    ai_reviewer_assessment
                ),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    writer_handoff_action = story_surface_delta_actions.quality_repair_writer_handoff_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if writer_handoff_action is not None:
        writer_handoff_action = ai_reviewer_owner_output_consumption.with_owner_output_consumption(
            payload=writer_handoff_action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=writer_handoff_action,
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
    consumed_ai_reviewer_route_back = _consumed_ai_reviewer_route_back_actions(
        status,
        publication_eval_payload=publication_eval_payload,
        request_lifecycle=request_lifecycle,
    )
    if consumed_ai_reviewer_route_back is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
            for action in consumed_ai_reviewer_route_back
        ]
    record_consumption_actions = ai_reviewer_owner_output_consumption.record_consumption_domain_transition_actions(
        status=status,
        publication_eval_payload=publication_eval_payload,
        request_lifecycle=request_lifecycle,
    )
    decorated_record_consumption_actions = ai_reviewer_owner_output_consumption.decorate_record_consumption_actions(
        study_id=study_id,
        quest_id=quest_id,
        actions=record_consumption_actions,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        control_allowed_write_surfaces=control_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    )
    if decorated_record_consumption_actions is not None:
        return decorated_record_consumption_actions
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
    digest_mismatch_ai_reviewer_route = current_truth_owner.current_manuscript_digest_mismatch_ai_reviewer_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if digest_mismatch_ai_reviewer_route is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_owner_output_consumption.current_manuscript_digest_mismatch_action(
                    digest_mismatch_ai_reviewer_route
                ),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    claim_alignment_action = claim_evidence_alignment_actions.action_from_ai_reviewer_alignment_blocker(
        study_root=study_root,
    )
    if claim_alignment_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=claim_alignment_action,
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
        story_surface_action = ai_reviewer_owner_output_consumption.with_owner_output_consumption(
            payload=story_surface_action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
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
    current_controller_ai_reviewer_action = _current_controller_ai_reviewer_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if current_controller_ai_reviewer_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=current_controller_ai_reviewer_action,
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


def _consumed_ai_reviewer_route_back_actions(
    status: Mapping[str, Any],
    *,
    publication_eval_payload: Mapping[str, Any],
    request_lifecycle: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    transition = _mapping(status.get("domain_transition"))
    receipt_consumption = _mapping(transition.get("completion_receipt_consumption"))
    if _text(receipt_consumption.get("status")) != "consumed":
        return None
    if _text(receipt_consumption.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return None
    if _text(transition.get("decision_type")) != "route_back_same_line":
        return None
    if _text(transition.get("controller_action")) != "request_opl_stage_attempt":
        return None
    return [
        ai_reviewer_owner_output_consumption.with_owner_output_consumption(
            payload=action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
        for action in domain_transition_actions.actions(status, publication_eval_payload=publication_eval_payload)
    ]

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


def _current_controller_ai_reviewer_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    if "return_to_ai_reviewer_workflow" not in set(_string_items(controller_route.get("controller_actions"))):
        return None
    work_unit_id = _text(controller_route.get("work_unit_id"))
    if work_unit_id is None:
        return None
    action = ai_reviewer_actions.ai_reviewer_required_action(reason="domain_transition_ai_reviewer_re_eval")
    action["summary"] = "The current controller decision routes this study back to the AI reviewer workflow."
    action["next_work_unit"] = work_unit_id
    action["executable_work_unit"] = work_unit_id
    action["controller_work_unit_id"] = work_unit_id
    action["route_target"] = _text(controller_route.get("route_target")) or "review"
    action["domain_transition_decision_type"] = "ai_reviewer_re_eval"
    action["controller_route"] = dict(controller_route)
    action["work_unit_fingerprint"] = _text(controller_route.get("work_unit_fingerprint"))
    action["publication_eval_latest_write_allowed"] = False
    action["controller_decision_write_allowed"] = False
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
    if _publication_gate_blocker_domain_transition(status):
        return True
    if current_truth_owner.current_story_surface_delta_blocker_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ) and not _pending_ai_reviewer_recheck_consumes_current_write_routeback(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    if current_truth_owner.current_ai_reviewer_write_routeback_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ) and not _pending_ai_reviewer_recheck_consumes_current_write_routeback(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
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
    if _publication_gate_blocker_domain_transition(status):
        return True
    if current_truth_owner.current_story_surface_delta_blocker_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ) and not _pending_ai_reviewer_recheck_consumes_current_write_routeback(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    if current_truth_owner.current_ai_reviewer_write_routeback_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ) and not _pending_ai_reviewer_recheck_consumes_current_write_routeback(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    if analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if provenance_limited_harmonization_owner_result.typed_blocker_state(study_root=study_root):
        return True
    if source_provenance_owner_result.typed_blocker_state(study_root=study_root):
        return True
    return False


def _publication_gate_blocker_domain_transition(status: Mapping[str, Any]) -> bool:
    transition = _mapping(status.get("domain_transition"))
    return (
        _text(transition.get("decision_type")) == "publication_gate_blocker"
        and _text(transition.get("controller_action")) == "run_gate_clearing_batch"
        and _text(_mapping(transition.get("next_work_unit")).get("unit_id")) is not None
    )


def _pending_ai_reviewer_recheck_consumes_current_write_routeback(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    action = story_surface_delta_actions.write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if action is None:
        return False
    expected_eval_id = _text(publication_eval_payload.get("eval_id"))
    expected_work_unit = _text(action.get("controller_work_unit_id")) or _text(action.get("next_work_unit"))
    if expected_eval_id is None or expected_work_unit is None:
        return False
    resolved_study_root = Path(study_root).expanduser().resolve()
    evidence = _read_json_object(resolved_study_root / REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    if evidence is None:
        return False
    if _text(evidence.get("status")) not in {"progress_delta_candidate", "controller_progress_delta_candidate"}:
        return False
    if evidence.get("ai_reviewer_recheck_required") is not True:
        return False
    if evidence.get("ai_reviewer_recheck_done") is not True:
        return False
    if _string_items(evidence.get("blockers")):
        return False
    source_eval_id = _text(evidence.get("source_eval_id")) or _text(_mapping(evidence.get("review_finding")).get("source_eval_id"))
    if source_eval_id != expected_eval_id:
        return False
    repair_work_unit = _mapping(evidence.get("repair_work_unit"))
    if _text(repair_work_unit.get("unit_id")) != expected_work_unit:
        return False
    recheck_ref = _text(evidence.get("ai_reviewer_recheck_request_ref"))
    if recheck_ref is None:
        return False
    recheck_path = Path(recheck_ref).expanduser()
    if not recheck_path.is_absolute():
        recheck_path = resolved_study_root / recheck_path
    request = _read_json_object(recheck_path)
    if request is None:
        return False
    if _text(request.get("request_kind")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(request.get("request_owner")) not in {None, "ai_reviewer"}:
        return False
    return _text(_mapping(request.get("request_lifecycle")).get("state")) in {"requested", "assigned"}


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


def _gate_replay_submission_refresh_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    controller_route = current_truth_owner.current_gate_replay_submission_refresh_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    return artifact_freshness.action_payload(
        reason=artifact_freshness.ACTION_TYPE,
        controller_route=controller_route,
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
    if gate_action := _gate_clearing_batch_action(actions):
        return _text(gate_action.get("reason")) or "run_gate_clearing_batch"
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    if runtime_facts.opl_stage_attempt_admission_required(status, progress):
        return current_truth_owner.OPL_STAGE_ATTEMPT_ADMISSION_REASON
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
        return current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if runtime_facts.retry_exhausted(status, progress):
        if gate_specificity.get("required") is True:
            return "publication_gate_specificity_required"
        return "runtime_recovery_retry_budget_exhausted"
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


def _has_gate_clearing_batch_action(actions: list[dict[str, Any]]) -> bool:
    return _gate_clearing_batch_action(actions) is not None


def _gate_clearing_batch_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for action in actions:
        if (
            _text(action.get("action_type")) == "run_gate_clearing_batch"
            and _text(action.get("owner")) == "gate_clearing_batch"
        ):
            return action
    return None


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
            "run_gate_clearing_batch",
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


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


__all__ = [
    "action_queue",
    "blocked_reason_from_scan",
    "decorate_action",
    "why_not_applied",
]
