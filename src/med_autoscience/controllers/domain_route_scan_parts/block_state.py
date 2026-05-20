from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.domain_route_scan_parts import completion_evidence
from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner
from med_autoscience.controllers.domain_route_scan_parts import evidence_adoption
from med_autoscience.controllers.domain_route_scan_parts import hard_methodology_currentness
from med_autoscience.controllers.domain_route_scan_parts import parked_truth
from med_autoscience.controllers.domain_route_scan_parts import runtime_facts


def ai_reviewer_lifecycle_resolved(
    *,
    lifecycle: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> bool:
    if _text(lifecycle.get("blocked_reason")) != "ai_reviewer_assessment_required":
        return False
    return ai_reviewer_assessment.get("missing") is not True


def runtime_relaunch_lifecycle_resolved(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
) -> bool:
    if _text(lifecycle.get("blocked_reason")) != "runtime_relaunch_no_live_run_started":
        return False
    return runtime_facts.active_run_id(status, progress) is not None and runtime_facts.worker_running(status)


def projection_only_runtime_recovery_lifecycle_resolved(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
) -> bool:
    return runtime_facts.runtime_recovery_lifecycle_resolved(
        status=status,
        progress=progress,
        lifecycle=lifecycle,
    )


def projection_block_state(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Any = None,
    publication_eval_payload: Mapping[str, Any] | None = None,
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    why_not_applied: str | None,
) -> dict[str, Any]:
    if study_root is not None and not _current_hard_methodology_handoff_supersedes_consumers(study_root):
        if _has_hard_methodology_handoff_action(actions):
            return {
                "blocked_reason": "unit_harmonized_rerun_required",
                "next_owner": "analysis_harmonization_owner",
                "external_supervisor_required": False,
            }
        if _has_provenance_limited_harmonization_audit_action(actions):
            return {
                "blocked_reason": "provenance_limited_harmonization_audit_required",
                "next_owner": "provenance_limited_harmonization_owner",
                "external_supervisor_required": False,
            }
        if _has_methodology_reframe_route_decision_action(actions):
            return {
                "blocked_reason": "methodology_reframe_required",
                "next_owner": "decision",
                "external_supervisor_required": False,
            }
        provenance_limited_state = provenance_limited_harmonization_owner_result.typed_blocker_state(
            study_root=study_root
        )
        if provenance_limited_state is not None:
            return provenance_limited_state
        methodology_decision_requests_audit = (
            provenance_limited_harmonization_owner_result.current_controller_decision_requests_audit(
                study_root=study_root
            )
        )
        if methodology_decision_requests_audit:
            return {
                "blocked_reason": "provenance_limited_harmonization_audit_required",
                "next_owner": "provenance_limited_harmonization_owner",
                "external_supervisor_required": False,
            }
        source_result_state = source_provenance_owner_result.typed_blocker_state(study_root=study_root)
        if source_result_state is not None:
            return source_result_state
        owner_result_state = analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root)
        if owner_result_state is not None:
            return owner_result_state
    if _has_source_provenance_handoff_action(actions):
        return {
            "blocked_reason": "transport_model_provenance_recovery_required",
            "next_owner": "source_provenance_owner",
            "external_supervisor_required": False,
        }
    if _has_methodology_reframe_route_decision_action(actions):
        return {
            "blocked_reason": "methodology_reframe_required",
            "next_owner": "decision",
            "external_supervisor_required": False,
        }
    if _has_provenance_limited_harmonization_audit_action(actions):
        return {
            "blocked_reason": "provenance_limited_harmonization_audit_required",
            "next_owner": "provenance_limited_harmonization_owner",
            "external_supervisor_required": False,
        }
    if _has_hard_methodology_handoff_action(actions):
        return {
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "external_supervisor_required": False,
        }
    if _has_clean_paper_authority_rehydrate_action(actions):
        return {
            "blocked_reason": "canonical_paper_inputs_rehydrate_required",
            "next_owner": "write",
            "external_supervisor_required": False,
        }
    if _has_clean_paper_authority_ai_reviewer_action(actions):
        return {
            "blocked_reason": "paper_authority_clean_migration_required",
            "next_owner": "ai_reviewer",
            "external_supervisor_required": False,
        }
    if completion_evidence.completed_current_truth(status, progress):
        return _clear_block_state()
    parked_state = parked_truth.block_state(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if parked_state is not None:
        return parked_state
    completion_state = completion_evidence.block_state(status, progress)
    if completion_state is not None:
        return completion_state
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if why_not_applied in {evidence_adoption.RECHECK_REASON, evidence_adoption.OWNER_HANDOFF_REASON} or (
        why_not_applied is not None and any(_text(action.get("reason")) == why_not_applied for action in actions)
    ):
        blocked_reason = why_not_applied
    next_owner = (
        evidence_adoption.adopted_next_owner(status)
        if blocked_reason == evidence_adoption.OWNER_HANDOFF_REASON
        else next_owner_for_blocked_reason(blocked_reason)
        if blocked_reason
        else _text(lifecycle.get("next_owner"))
    )
    external_supervisor_required = bool(
        lifecycle.get("external_supervisor_required")
        or any(_text(action.get("authority")) == "external_supervisor" for action in actions)
    )
    if next_owner is not None and next_owner != "external_supervisor":
        external_supervisor_required = any(
            _text(action.get("authority")) == "external_supervisor"
            and _text(action.get("reason")) == blocked_reason
            for action in actions
        )
    return {
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": external_supervisor_required,
    }


def next_owner_for_blocked_reason(blocked_reason: str | None) -> str:
    if owner := current_truth_owner.next_owner_for_reason(blocked_reason):
        return owner
    if blocked_reason == "study_completion_contract_not_ready":
        return "completion_evidence"
    if blocked_reason == "publication_gate_specificity_required":
        return "publication_gate"
    if blocked_reason == evidence_adoption.RECHECK_REASON:
        return "publication_gate"
    if blocked_reason == evidence_adoption.OWNER_HANDOFF_REASON:
        return "mas_controller"
    if blocked_reason == "current_package_freshness_required":
        return "artifact_os"
    if blocked_reason == "display_surface_materialization_failed":
        return "artifact_os"
    if blocked_reason in {"ai_reviewer_assessment_required", "ai_reviewer_assessment_stale_after_reviewer_revision"}:
        return "ai_reviewer"
    if blocked_reason == "domain_transition_ai_reviewer_re_eval":
        return "ai_reviewer"
    if blocked_reason == "canonical_paper_inputs_rehydrate_required":
        return "write"
    if blocked_reason == "unit_harmonized_rerun_required":
        return "analysis_harmonization_owner"
    if blocked_reason == "methodology_reframe_required":
        return "decision"
    if blocked_reason == "transport_model_provenance_recovery_required":
        return "source_provenance_owner"
    if blocked_reason == "provenance_limited_harmonization_audit_required":
        return "provenance_limited_harmonization_owner"
    if blocked_reason == "rebuild_reproducible_model_route_required":
        return "human_gate"
    return "external_supervisor"


def remove_action_type(actions: list[dict[str, Any]], action_type: str) -> list[dict[str, Any]]:
    return [action for action in actions if _text(action.get("action_type")) != action_type]


def _has_clean_paper_authority_ai_reviewer_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "return_to_ai_reviewer_workflow"
        and _text(action.get("reason")) == "paper_authority_clean_migration_required"
        and _text(action.get("owner")) == "ai_reviewer"
        for action in actions
    )


def _has_clean_paper_authority_rehydrate_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "canonical_paper_inputs_rehydrate_required"
        and _text(action.get("reason")) == "canonical_paper_inputs_rehydrate_required"
        and _text(action.get("owner")) == "write"
        for action in actions
    )


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


def _has_methodology_reframe_route_decision_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "methodology_reframe_route_decision"
        and _text(action.get("reason")) == "methodology_reframe_required"
        and _text(action.get("owner")) == "decision"
        for action in actions
    )


def _has_provenance_limited_harmonization_audit_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "provenance_limited_harmonization_audit"
        and _text(action.get("reason")) == "provenance_limited_harmonization_audit_required"
        and _text(action.get("owner")) == "provenance_limited_harmonization_owner"
        for action in actions
    )


def _current_hard_methodology_handoff_supersedes_consumers(study_root: Any) -> bool:
    root = Path(study_root).expanduser().resolve()
    source_ref = hard_methodology_currentness.quality_repair_handoff_path(root)
    consumer_paths = (
        analysis_harmonization_owner_result.result_path(study_root=root),
        source_provenance_owner_result.result_path(study_root=root),
        provenance_limited_harmonization_owner_result.result_path(study_root=root),
        root / "artifacts" / "controller_decisions" / "latest.json",
    )
    return hard_methodology_currentness.handoff_supersedes_paths(
        source_ref=source_ref,
        consumer_paths=consumer_paths,
    )


def _clear_block_state() -> dict[str, Any]:
    return {
        "blocked_reason": None,
        "next_owner": None,
        "external_supervisor_required": False,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ai_reviewer_lifecycle_resolved",
    "runtime_relaunch_lifecycle_resolved",
    "projection_only_runtime_recovery_lifecycle_resolved",
    "next_owner_for_blocked_reason",
    "projection_block_state",
    "remove_action_type",
]
