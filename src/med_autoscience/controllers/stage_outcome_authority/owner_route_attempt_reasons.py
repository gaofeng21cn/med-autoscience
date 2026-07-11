from __future__ import annotations

from collections.abc import Iterable
from typing import Any


DEFAULT_FORBIDDEN_SURFACES = [
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
]


def _entry(
    *,
    owner: str,
    allowed_actions: Iterable[str],
    required_output: str,
    priority_class: str,
    regression_refs: Iterable[str],
    forbidden_surfaces: Iterable[str] = DEFAULT_FORBIDDEN_SURFACES,
    allow_route_action: bool = False,
) -> dict[str, Any]:
    return {
        "owner": owner,
        "allowed_actions": list(allowed_actions),
        "required_output": required_output,
        "priority_class": priority_class,
        "regression_refs": list(regression_refs),
        "forbidden_surfaces": list(forbidden_surfaces),
        "allow_route_action": allow_route_action,
    }


def _ai_reviewer_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="ai_reviewer",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        required_output="artifacts/publication_eval/latest.json",
        priority_class="ai_reviewer_currentness",
        regression_refs=regression_refs or ("tests/paper_mission_owner_surface_cases",),
    )


def _write_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="write",
        allowed_actions=["run_quality_repair_batch"],
        required_output=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        priority_class="write_route_back",
        regression_refs=regression_refs or ("tests/paper_mission_owner_surface_cases",),
    )


def _artifact_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="artifact_os",
        allowed_actions=[
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
        ],
        required_output="artifacts/controller/current_package_freshness/latest.json",
        priority_class="package_freshness",
        regression_refs=regression_refs or ("tests/paper_mission_owner_surface_cases",),
    )


def _gate_clearing_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="gate_clearing_batch",
        allowed_actions=["run_gate_clearing_batch"],
        required_output="artifacts/controller/gate_clearing_batch/latest.json",
        priority_class="package_freshness",
        regression_refs=regression_refs or ("tests/paper_mission_owner_surface_cases",),
    )


_REASON_REGISTRY = {
    "ai_reviewer_request_pending": _ai_reviewer_entry("DM002:pending_ai_reviewer_request"),
    "ai_reviewer_assessment_required": _ai_reviewer_entry(),
    "ai_reviewer_assessment_stale_after_reviewer_revision": _ai_reviewer_entry(
        "DM002:stale_reviewer_record"
    ),
    "ai_reviewer_record_stale_after_current_manuscript": _ai_reviewer_entry(
        "DM002:reviewer_currentness"
    ),
    "ai_reviewer_record_stale_after_current_inputs": _ai_reviewer_entry(
        "DM003:reviewer_input_currentness"
    ),
    "ai_reviewer_record_stale_after_unit_harmonized_rerun": _ai_reviewer_entry(),
    "analysis_harmonization_completed_ai_reviewer_review_required": _ai_reviewer_entry(),
    "ai_reviewer_repair_recheck_required": _ai_reviewer_entry(),
    "analysis_repair_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "rebuttal_closure_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "text_repair_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "domain_transition_ai_reviewer_re_eval": _ai_reviewer_entry("DM003:domain_transition_ai_reviewer_re_eval"),
    "return_to_ai_reviewer_workflow": _ai_reviewer_entry(),
    "publication_gate_recheck_required": _ai_reviewer_entry(),
    "ai_reviewer_request_missing": _ai_reviewer_entry(),
    "ai_reviewer_required": _ai_reviewer_entry(),
    "ai_reviewer_quality_authority_missing": _ai_reviewer_entry(),
    "ai_reviewer_record_missing": _ai_reviewer_entry(),
    "ai_reviewer_record_incomplete": _ai_reviewer_entry(),
    "dm002_publication_eval_requires_ai_reviewer_and_canonical_refresh": _ai_reviewer_entry(),
    "manuscript_story_surface_delta_missing": _write_entry("DM003:medical_prose_route_back"),
    "publication_gate_route_back_write_required": _write_entry(
        "DM003:blocked_gate_replay_route_back_write"
    ),
    "claim_evidence_alignment_required": _entry(
        owner="write",
        allowed_actions=["run_quality_repair_batch"],
        required_output=(
            "claim-evidence map and evidence ledger alignment or "
            "typed blocker:claim_evidence_alignment_required"
        ),
        priority_class="write_route_back",
        regression_refs=("DM002:claim_evidence_alignment",),
    ),
    "run_quality_repair_batch": _write_entry("tests:legacy_action_reason_write_route"),
    "publication_owner_materialization_required": _gate_clearing_entry(
        "DM002:current_ai_reviewer_materialization"
    ),
    "publication_gate_replay_after_clean_migration": _gate_clearing_entry(
        "DM002:clean_migration_publication_gate_replay"
    ),
    "ai_reviewer_record_gate_consumption": _gate_clearing_entry(
        "DM002:current_ai_reviewer_record_gate_consumption"
    ),
    "dpcc_publication_gate_replay_after_current_ai_reviewer_record": _gate_clearing_entry(
        "DM003:current_ai_reviewer_publication_gate_replay"
    ),
    "owner_authorized_publication_gate_replay": _gate_clearing_entry(
        "DM003:owner_authorized_publication_gate_replay"
    ),
    "publication_gate_replay_blocked": _gate_clearing_entry(
        "DM003:publication_gate_replay_blocked"
    ),
    "domain_transition_publication_gate_blocker": _gate_clearing_entry(
        "DM003:domain_transition_publication_gate_blocker"
    ),
    "run_gate_clearing_batch": _gate_clearing_entry("tests:legacy_action_reason_gate_clearing"),
    "opl_stage_attempt_admission_required": _write_entry("DM002:runtime_redrive_route_back"),
    "controller_decision_route_back": _entry(
        owner="owner_route_next_owner",
        allowed_actions=["run_quality_repair_batch", "return_to_ai_reviewer_workflow"],
        required_output="owner-specific receipt or typed blocker",
        priority_class="write_route_back",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
        allow_route_action=True,
    ),
    "controller_work_unit_owner_handoff_required": _entry(
        owner="owner_route_next_owner",
        allowed_actions=[
            "return_to_ai_reviewer_workflow",
            "run_quality_repair_batch",
            "publication_gate_specificity_required",
        ],
        required_output="owner-specific receipt or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
        allow_route_action=True,
    ),
    "publication_gate_specificity_required": _entry(
        owner="publication_gate",
        allowed_actions=["publication_gate_specificity_required"],
        required_output="artifacts/publication_eval/latest.json",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM002:publication_gate_specificity",),
    ),
    "publication_handoff_owner_gate": _entry(
        owner="publication_gate_owner",
        allowed_actions=["publication_handoff_owner_gate"],
        required_output=(
            "artifacts/publication_handoff/owner_receipt.json "
            "or typed blocker:publication_handoff_owner_gate_blocked"
        ),
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM002:terminal_publication_handoff", "DM003:terminal_publication_handoff"),
    ),
    "medical_paper_readiness_not_ready": _entry(
        owner="MedAutoScience",
        allowed_actions=["complete_medical_paper_readiness_surface"],
        required_output=(
            "artifacts/medical_paper/readiness.json updated from provider-backed capability surfaces "
            "or typed blocker:medical_paper_readiness_surface_input_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:medical_paper_readiness", "DM003:medical_paper_readiness"),
    ),
    "medical_paper_readiness_missing": _entry(
        owner="MedAutoScience",
        allowed_actions=["complete_medical_paper_readiness_surface"],
        required_output=(
            "artifacts/medical_paper/readiness.json updated from provider-backed capability surfaces "
            "or typed blocker:medical_paper_readiness_surface_input_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:medical_paper_readiness", "DM003:medical_paper_readiness"),
    ),
    "complete_medical_paper_readiness_surface": _entry(
        owner="MedAutoScience",
        allowed_actions=["complete_medical_paper_readiness_surface"],
        required_output=(
            "artifacts/medical_paper/readiness.json updated from provider-backed capability surfaces "
            "or typed blocker:medical_paper_readiness_surface_input_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("tests/paper_mission_owner_surface_cases/test_stage_artifact_owner_action.py",),
    ),
    "gate_needs_specificity": _entry(
        owner="publication_gate",
        allowed_actions=["publication_gate_specificity_required"],
        required_output="specific publication gate blocker target refs",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "current_package_freshness_required": _artifact_entry("DM002:package_freshness"),
    "artifact_work_required": _artifact_entry("tests:artifact_owner_route"),
    "display_surface_materialization_failed": _artifact_entry(),
    "canonical_paper_inputs_rehydrate_required": _entry(
        owner="write",
        allowed_actions=["canonical_paper_inputs_rehydrate_required"],
        required_output="paper/medical_manuscript_blueprint_source.json",
        priority_class="write_route_back",
        regression_refs=("tests/domain_action_request_materializer_cases",),
    ),
    "unit_harmonized_rerun_required": _entry(
        owner="analysis_harmonization_owner",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
        required_output=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:unit_harmonized_rerun",),
    ),
    "unit_harmonized_external_validation_rerun": _entry(
        owner="analysis_harmonization_owner",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
        required_output=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:managed_runtime_unit_harmonized_rerun",),
    ),
    "transport_model_provenance_recovery_required": _entry(
        owner="source_provenance_owner",
        allowed_actions=["recover_transport_model_provenance"],
        required_output=(
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:transport_model_provenance",),
    ),
    "recover_transport_model_provenance": _entry(
        owner="source_provenance_owner",
        allowed_actions=["recover_transport_model_provenance"],
        required_output=(
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:transport_model_provenance",),
    ),
    "methodology_reframe_required": _entry(
        owner="decision",
        allowed_actions=["methodology_reframe_route_decision"],
        required_output="controller route decision for methodology reframe",
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:methodology_reframe",),
    ),
    "provenance_limited_harmonization_audit_required": _entry(
        owner="provenance_limited_harmonization_owner",
        allowed_actions=["provenance_limited_harmonization_audit"],
        required_output=(
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:provenance_limited_harmonization",),
    ),
    "paper_authority_clean_migration_required": _entry(
        owner="ai_reviewer",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        required_output="new MAS paper authority surface or typed blocker",
        priority_class="ai_reviewer_currentness",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "paper_clean_room_rebuild_required": _entry(
        owner="MedAutoScience",
        allowed_actions=["paper_clean_room_rebuild_required"],
        required_output="artifacts/supervision/paper_clean_room_rebuild/latest.json",
        priority_class="write_route_back",
        regression_refs=("tests/test_paper_clean_room_rebuild.py",),
        forbidden_surfaces=(
            "manuscript/**",
            "current_package/**",
            "paper/current_package/**",
            "manuscript/current_package/**",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
        ),
    ),
    "study_completion_contract_not_ready": _entry(
        owner="controller_stop",
        allowed_actions=[],
        required_output="study completion contract blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "runtime_controller_redrive_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "runtime_recovery_not_authorized": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "runtime_recovery_retry_budget_exhausted": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "abnormal_stopped_runtime_resume_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL runtime owner handoff or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases/test_abnormal_stopped_runtime.py",),
    ),
    "failed_quest_runtime_relaunch_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL runtime owner handoff or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases/test_failed_quest_autorepair.py",),
    ),
    "opl_runtime_owner_route_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL owner route transport receipt",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/paper_mission_owner_surface_cases",),
    ),
    "typed_closeout_packet_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="typed closeout packet with closeout refs",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:typed_closeout",),
    ),
    "owner_receipt_pending": _entry(
        owner="med-autoscience",
        allowed_actions=[],
        required_output="MAS owner receipt or stable typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:owner_receipt",),
    ),
    "owner_chain_receipt_pending": _entry(
        owner="med-autoscience",
        allowed_actions=[],
        required_output="MAS owner receipt or stable typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:owner_receipt",),
    ),
}


__all__ = ["DEFAULT_FORBIDDEN_SURFACES", "_REASON_REGISTRY"]
