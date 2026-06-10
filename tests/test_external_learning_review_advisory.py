from __future__ import annotations

import importlib
from pathlib import Path


def _dispatch(study_root: Path) -> dict[str, object]:
    return {
        "action_type": "return_to_ai_reviewer_workflow",
        "action_id": "dispatch-review-001",
        "study_root": str(study_root),
        "apply": True,
        "owner_route": {
            "owner": "ai_reviewer",
            "work_unit_id": "claim-support-review",
            "work_unit_fingerprint": "fingerprint-review-001",
        },
        "refs": {
            "dispatch_path": "artifacts/supervision/consumer/current.json",
            "unsupported_claim_gap_refs": [
                {"ref": "claim-gap:dm002/no-support-for-causal-language"}
            ],
        },
        "ars_refs": {
            "claim_support_audit_refs": ["claim-audit:dm002/current-owner"],
            "data_access_oversight_refs": ["oversight:dm002/irb-and-data-access"],
            "material_passport_refs": ["material-passport:dm002/current"],
        },
        "aris_refs": {
            "typed_input_contract_ref": "aris-input-contract:dm002/current-owner",
            "result_import_receipt_ref": "aris-result-import:dm002/body-free",
            "cross_model_reviewer_receipt_refs": ["reviewer-receipt:dm002/model-a"],
            "experiment_queue_hint_refs": ["analysis-queue:dm002/external-validation"],
        },
    }


def test_ars_claim_support_advisory_projects_required_ref_families(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_review_advisory")

    result = module.build_ars_claim_support_advisory(_dispatch(tmp_path))

    assert result["surface_kind"] == "mas_ars_claim_support_advisory"
    assert result["framework_id"] == "academic_research_skills"
    assert result["status"] == "ready"
    assert result["body_included"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["allowed_writes"] == []
    assert result["claim_support_audit_refs"][0] == "claim-audit:dm002/current-owner"
    assert "paper/evidence/evidence_ledger.json" in result["claim_support_audit_refs"]
    assert "oversight:dm002/irb-and-data-access" in result["data_access_oversight_refs"]
    assert "study_charter.data_access" in result["data_access_oversight_refs"]
    assert "material-passport:dm002/current" in result["material_passport_refs"]
    assert (
        "medical_material_passport.sections.claim_evidence_refs"
        in result["material_passport_refs"]
    )
    assert "claim-gap:dm002/no-support-for-causal-language" in result["unsupported_claim_gap_refs"]
    assert (
        "artifacts/publication_eval/latest.json#unsupported_claims"
        in result["unsupported_claim_gap_refs"]
    )


def test_aris_review_import_advisory_projects_required_ref_families(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_review_advisory")

    result = module.build_aris_review_import_advisory(_dispatch(tmp_path))

    assert result["surface_kind"] == "mas_aris_review_import_advisory"
    assert result["framework_id"] == "aris"
    assert result["status"] == "ready"
    assert result["body_included"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["allowed_writes"] == []
    assert result["typed_input_contract_ref"] == "aris-input-contract:dm002/current-owner"
    assert result["result_import_receipt_ref"] == "aris-result-import:dm002/body-free"
    assert result["cross_model_reviewer_receipt_refs"][0] == "reviewer-receipt:dm002/model-a"
    assert (
        "external-learning:aris:fingerprint-review-001:cross-model-reviewer-receipt"
        in result["cross_model_reviewer_receipt_refs"]
    )
    assert result["experiment_queue_hint_refs"][0] == "analysis-queue:dm002/external-validation"
    assert (
        "artifacts/analysis_queue/latest.json#aris_experiment_queue_hint"
        in result["experiment_queue_hint_refs"]
    )


def test_review_advisories_fail_open_when_dispatch_input_is_missing() -> None:
    module = importlib.import_module("med_autoscience.external_learning_review_advisory")

    ars = module.build_ars_claim_support_advisory({})
    aris = module.build_aris_review_import_advisory(None)

    for result in (ars, aris):
        assert result["status"] == "skipped_missing_dispatch"
        assert result["missing_inputs"] == ["dispatch"]
        assert result["body_included"] is False
        assert result["can_block_current_owner_action"] is False
        assert result["allowed_writes"] == []
        assert result["failure_policy"] == "fail_open_continue_current_owner_action"
    assert ars["claim_support_audit_refs"] == []
    assert ars["data_access_oversight_refs"] == []
    assert ars["material_passport_refs"] == []
    assert ars["unsupported_claim_gap_refs"] == []
    assert aris["typed_input_contract_ref"] is None
    assert aris["result_import_receipt_ref"] is None
    assert aris["cross_model_reviewer_receipt_refs"] == []
    assert aris["experiment_queue_hint_refs"] == []


def test_review_advisory_authority_boundary_is_complete_and_nonblocking(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.external_learning_review_advisory")
    results = [
        module.build_ars_claim_support_advisory(_dispatch(tmp_path)),
        module.build_aris_review_import_advisory(_dispatch(tmp_path)),
    ]

    required_false_flags = {
        "can_write_domain_truth",
        "can_write_publication_eval",
        "can_write_controller_decisions",
        "can_write_paper_or_package",
        "can_write_evidence_ledger",
        "can_write_review_ledger",
        "can_write_memory_body",
        "can_write_artifact_body",
        "can_write_owner_receipt",
        "can_write_typed_blocker",
        "can_authorize_current_owner_action",
        "can_authorize_source_readiness",
        "can_authorize_publication_quality",
        "can_authorize_publication_readiness",
        "can_authorize_submission_readiness",
        "can_authorize_artifact_authority",
        "can_close_quality_gate",
        "can_close_stage",
    }
    required_forbidden_authority = {
        "domain_truth",
        "publication_eval",
        "controller_decisions",
        "paper_or_package",
        "evidence_ledger",
        "review_ledger",
        "memory_body",
        "artifact_body",
        "owner_receipt",
        "typed_blocker",
        "current_owner_action",
        "source_readiness",
        "publication_quality",
        "publication_readiness",
        "submission_readiness",
        "artifact_authority",
        "quality_gate_closure",
        "stage_closure",
    }

    for result in results:
        authority = result["authority_boundary"]
        assert {flag for flag in required_false_flags if authority[flag] is False} == (
            required_false_flags
        )
        assert set(result["forbidden_authority"]) == required_forbidden_authority
        assert set(authority["forbidden_authority"]) == required_forbidden_authority
        assert "artifacts/publication_eval/latest.json" in result["forbidden_writes"]
        assert "artifacts/controller_decisions/latest.json" in result["forbidden_writes"]
        assert result["mainline_waits_for_advisory"] is False


def test_review_advisory_generators_do_not_write_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_review_advisory")

    assert list(tmp_path.rglob("*")) == []
    module.build_ars_claim_support_advisory(_dispatch(tmp_path))
    module.build_aris_review_import_advisory(_dispatch(tmp_path))

    assert list(tmp_path.rglob("*")) == []
