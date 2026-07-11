from __future__ import annotations

import importlib


def test_publication_work_unit_identity_ignores_downstream_delivery_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_identity")

    with_delivery_churn = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )
    claim_only = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )

    assert with_delivery_churn.effective_blockers == ("claim_evidence_consistency_failed",)
    assert with_delivery_churn.fingerprint == claim_only.fingerprint
    assert with_delivery_churn.dispatch_key == (
        f"{claim_only.fingerprint}::analysis_claim_evidence_repair::run_gate_clearing_batch"
    )
