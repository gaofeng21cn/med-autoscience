from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import real_paper_ai_first_soak

from .shared import list_items, text


SOAK_STAGE_REF_HINTS: dict[str, tuple[str, ...]] = {
    "literature_scout": (
        "artifacts/stage_outputs/01-study_intake/receipts/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/owner_receipt.json",
        "artifacts/medical_paper/literature_intelligence_os.json",
        "artifacts/medical_paper/literature_provider_runtime.json",
    ),
    "line_selection": (
        "artifacts/stage_outputs/01-study_intake/projection/current_owner_delta.json",
        "artifacts/medical_paper/study_line_decision.json",
    ),
    "main_analysis": (
        "artifacts/stage_outputs/04-analysis_execution/analysis_run_record.json",
        "artifacts/stage_outputs/04-analysis_execution/primary_results_artifact_set.json",
    ),
    "bounded_analysis": (
        "artifacts/stage_outputs/04-analysis_execution/primary_results_artifact_set.json",
        "artifacts/medical_paper/bounded_analysis_candidate_board.json",
    ),
    "route_back": (
        "artifacts/stage_outputs/05-evidence_synthesis/evidence_synthesis_matrix.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/revision_action_matrix.json",
    ),
    "stop_loss": (
        "artifacts/medical_paper/stop_loss_memo.json",
        "artifacts/controller_decisions/latest.json",
    ),
    "revision_reopen": (
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/reviewer_quality_receipt.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/receipts/owner_receipt.json",
    ),
    "runtime_recovery": (
        "artifacts/supervision/consumer/default_executor_execution/history.jsonl",
        "artifacts/runtime/runtime_status_summary.json",
        "runtime/artifacts/supervision/opl_current_control_state/latest.json",
    ),
    "finalize_rebuild": (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/publication_package_manifest.json",
    ),
    "final_pre_submission_audit": (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/publication_gate_receipt.json",
    ),
}


def payload_from_real_study_soak_matrix_evidence(
    *,
    study_root: Path,
    source: str,
    blocked_payload: dict[str, Any],
) -> dict[str, Any]:
    direct = real_paper_ai_first_soak.build_real_study_soak_matrix_evidence(study_roots=[study_root])
    if text(direct.get("overall_status")) in {"complete", "partial"}:
        return {
            **dict(direct),
            "payload_source": source,
            "source_basis": "real_study_soak_matrix_evidence_builder",
            "source_refs": list(list_items(direct.get("evidence_sources"))),
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    evidence_map = _soak_stage_evidence_map(study_root=study_root)
    if not any(evidence_map.values()):
        return blocked_payload
    payload = real_paper_ai_first_soak.build_real_study_soak_matrix_evidence(evidence_map=evidence_map)
    return {
        **dict(payload),
        "payload_source": source,
        "source_basis": "real_study_soak_matrix_evidence_builder",
        "source_refs": [ref for refs in evidence_map.values() for ref in refs],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _soak_stage_evidence_map(*, study_root: Path) -> dict[str, list[str]]:
    root = Path(study_root).expanduser().resolve()
    evidence_map: dict[str, list[str]] = {}
    for stage, relative_refs in SOAK_STAGE_REF_HINTS.items():
        refs = [ref for ref in relative_refs if (root / ref).is_file()]
        evidence_map[stage] = refs
    return evidence_map


__all__ = ["payload_from_real_study_soak_matrix_evidence"]
