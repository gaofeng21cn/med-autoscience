from __future__ import annotations

from pathlib import Path
from typing import Any

import med_autoscience.controllers.autonomy_ai_doctor as autonomy_ai_doctor
import med_autoscience.controllers.open_auto_research_projection as open_auto_research_projection
import med_autoscience.controllers.runtime_health_kernel as runtime_health_kernel
import med_autoscience.controllers.study_truth_kernel as study_truth_kernel


def build_projection_refs(
    *,
    launch_report_path: Path,
    publication_eval_path: Path,
    controller_decision_path: Path,
    controller_confirmation_summary_path: Path,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_module_surface: dict[str, Any] | None,
    opl_runtime_owner_handoff_path: Path,
    opl_runtime_owner_handoff_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_readback_report_path: Path | None,
    runtime_module_surface: dict[str, Any],
    runtime_efficiency_refs: dict[str, Any],
    study_root: Path,
    autonomy_slo_status: dict[str, Any] | None,
    ai_repair_lifecycle: dict[str, Any] | None,
    evaluation_module_surface: dict[str, Any] | None,
    medical_writing_quality_surfaces: dict[str, Any],
    gate_specificity_request_path: Path | None,
    gate_specificity_request: dict[str, Any] | None,
    artifact_runtime_proof_surface: dict[str, Any],
    submission_hygiene_truth: dict[str, Any],
    bash_summary_path: Path | None,
    details_projection_path: Path | None,
    ai_first_observability_snapshots: dict[str, Any],
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_medical_publication_surface: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "launch_report_path": str(launch_report_path),
        "publication_eval_path": str(publication_eval_path),
        "controller_decision_path": str(controller_decision_path),
        "controller_confirmation_summary_path": (
            str(controller_confirmation_summary_path)
            if controller_confirmation_summary is not None
            or controller_confirmation_summary_path.exists()
            else None
        ),
        "controller_summary_path": (
            controller_module_surface["summary_ref"] if controller_module_surface is not None else None
        ),
        "opl_runtime_owner_handoff_path": (
            str(opl_runtime_owner_handoff_path)
            if opl_runtime_owner_handoff_payload is not None
            else None
        ),
        "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
        "runtime_readback_report_path": (
            str(runtime_readback_report_path) if runtime_readback_report_path is not None else None
        ),
        "runtime_status_summary_path": runtime_module_surface["summary_ref"],
        **runtime_efficiency_refs,
        "autonomy_slo_status_path": (
            str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root))
            if autonomy_slo_status is not None
            else None
        ),
        "ai_repair_lifecycle_path": (
            str(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json")
            if ai_repair_lifecycle is not None
            else None
        ),
        "evaluation_summary_path": (
            evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
        ),
        "medical_manuscript_blueprint_path": medical_writing_quality_surfaces["blueprint"]["path"],
        "medical_journal_style_corpus_path": medical_writing_quality_surfaces["style_corpus"]["path"],
        "medical_prose_review_request_path": medical_writing_quality_surfaces["prose_review_request"]["path"],
        "medical_prose_review_path": medical_writing_quality_surfaces["prose_review"]["path"],
        "retrospective_medical_prose_audit_request_path": (
            medical_writing_quality_surfaces["retrospective_audit_request"]["path"]
        ),
        "retrospective_medical_prose_audit_path": medical_writing_quality_surfaces["retrospective_audit"]["path"],
        "medical_paper_readiness_path": str(
            medical_paper_readiness_path(study_root=study_root)
        ),
        "open_auto_research_projection_path": str(
            open_auto_research_projection.stable_open_auto_research_projection_path(study_root=study_root)
        ),
        "opl_current_control_state_handoff_path": (
            opl_current_control_state_handoff.get("source_path") if opl_current_control_state_handoff is not None else None
        ),
        "runtime_medical_publication_surface_report_path": (
            runtime_medical_publication_surface.get("source_path")
            if runtime_medical_publication_surface is not None
            else None
        ),
        "repair_execution_evidence_path": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
        "repair_execution_receipt_path": str(
            study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
        ),
        "gate_replay_request_path": str(
            study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
        ),
        "ai_reviewer_recheck_request_path": str(
            study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
        ),
        "publication_gate_specificity_request_path": (
            str(gate_specificity_request_path) if gate_specificity_request is not None else None
        ),
        "artifact_runtime_proof_delivery_manifest_path": (
            (artifact_runtime_proof_surface.get("refs") or {}).get("delivery_manifest_path")
        ),
        "submission_hygiene_submission_manifest_path": (
            (submission_hygiene_truth.get("refs") or {}).get("submission_manifest_path")
        ),
        "study_truth_snapshot_path": str(study_truth_kernel.truth_snapshot_path(study_root=study_root)),
        "runtime_health_snapshot_path": str(
            runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
        ),
        "promotion_gate_path": (
            evaluation_module_surface["promotion_gate_ref"] if evaluation_module_surface is not None else None
        ),
        "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
        "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
        "ai_first_observability_publication_eval_path": ai_first_observability_snapshots["refs"][
            "publication_eval_path"
        ],
        "ai_first_observability_runtime_health_path": ai_first_observability_snapshots["refs"][
            "runtime_health_path"
        ],
        "ai_first_observability_delivery_manifest_path": ai_first_observability_snapshots["refs"][
            "delivery_manifest_path"
        ],
    }


def medical_paper_readiness_path(*, study_root: Path) -> Path:
    from med_autoscience.controllers import medical_paper_readiness

    return medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)
