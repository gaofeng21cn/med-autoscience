from __future__ import annotations

import importlib

import pytest


PASSPORT_SECTION_KEYS = {
    "source_readiness_refs",
    "claim_evidence_refs",
    "review_contract_refs",
    "artifact_rebuild_refs",
    "human_decision_refs",
    "owner_receipt_refs",
}

FORBIDDEN_BODY_KEYS = {
    "body",
    "payload",
    "artifact_body",
    "memory_body",
    "evidence_ledger_body",
    "review_ledger_body",
    "publication_verdict_body",
    "paper_body",
    "package_body",
}


def test_medical_material_passport_projects_refs_only_source_workspace_handoff() -> None:
    module = importlib.import_module("med_autoscience.medical_material_passport")

    passport = module.build_medical_material_passport(
        source_readiness_refs=["studies/001/artifacts/source_readiness/latest.json"],
        claim_evidence_refs=["studies/001/paper/evidence_ledger.json#claims"],
        review_contract_refs=["studies/001/artifacts/stage_reviews/latest.json"],
        artifact_rebuild_refs=["studies/001/manuscript/current_package/manifest.json"],
        human_decision_refs=["studies/001/artifacts/controller_decisions/latest.json"],
        owner_receipt_refs=["studies/001/artifacts/runtime/owner_route/latest.json"],
    )

    assert passport["surface_kind"] == "medical_material_passport"
    assert passport["schema_version"] == "mas-medical-material-passport.v1"
    assert passport["truth_owner"] == "MedAutoScience"
    assert passport["source_project"] == "academic-research-skills pattern-only"
    assert passport["body_included"] is False
    assert set(passport["sections"]) == PASSPORT_SECTION_KEYS
    assert passport["sections"]["source_readiness_refs"] == [
        {
            "ref": "studies/001/artifacts/source_readiness/latest.json",
            "role": "source_readiness_ref",
            "body_included": False,
            "write_permitted": False,
            "truth_owner": "MedAutoScience",
        }
    ]
    assert passport["authority_boundary"] == {
        "can_write_mas_truth": False,
        "can_write_evidence_ledger": False,
        "can_write_review_ledger": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }

    assert _forbidden_body_keys(passport) == set()


def test_source_adapter_output_always_emits_rejection_log_and_keeps_records_projection_only() -> None:
    module = importlib.import_module("med_autoscience.medical_material_passport")

    output = module.build_source_adapter_output(
        adapter_name="workspace-literature-adapter",
        adapter_version="1.0.0",
        records=[
            {
                "record_id": "R1",
                "source_pointer": "workspace://literature/R1",
                "refs": ["studies/001/literature/R1.json"],
            }
        ],
        rejected=[
            {
                "source": "workspace://literature/bad",
                "reason": "missing_required_field",
                "missing_fields": ["source_pointer"],
            }
        ],
    )

    assert output["surface_kind"] == "mas_source_adapter_output"
    assert output["schema_version"] == "mas-source-adapter-output.v1"
    assert output["truth_owner"] == "MedAutoScience"
    assert output["adapter_authority"] == "records_and_rejection_log_only"
    assert output["records_write_mas_truth"] is False
    assert output["rejection_log"]["surface_kind"] == "mas_source_adapter_rejection_log"
    assert output["rejection_log"]["rejected"][0]["reason"] == "missing_required_field"
    assert output["rejection_log"]["closed_reasons"] == module.SOURCE_ADAPTER_REJECTION_REASONS
    assert output["entry_level_reject_continues"] is True
    assert output["adapter_level_failure_loud"] is True


def test_source_adapter_rejection_log_is_required_even_when_empty() -> None:
    module = importlib.import_module("med_autoscience.medical_material_passport")

    output = module.build_source_adapter_output(
        adapter_name="workspace-literature-adapter",
        adapter_version="1.0.0",
        records=[],
        rejected=[],
    )

    assert output["rejection_log"] == {
        "surface_kind": "mas_source_adapter_rejection_log",
        "schema_version": "mas-source-adapter-rejection-log.v1",
        "adapter_name": "workspace-literature-adapter",
        "adapter_version": "1.0.0",
        "closed_reasons": module.SOURCE_ADAPTER_REJECTION_REASONS,
        "rejected": [],
    }


def test_source_adapter_rejection_log_rejects_unknown_reason_and_missing_other_detail() -> None:
    module = importlib.import_module("med_autoscience.medical_material_passport")

    with pytest.raises(ValueError, match="closed rejection reason"):
        module.build_source_adapter_output(
            adapter_name="workspace-literature-adapter",
            adapter_version="1.0.0",
            records=[],
            rejected=[{"source": "workspace://bad", "reason": "maybe"}],
        )

    with pytest.raises(ValueError, match="detail is required"):
        module.build_source_adapter_output(
            adapter_name="workspace-literature-adapter",
            adapter_version="1.0.0",
            records=[],
            rejected=[{"source": "workspace://bad", "reason": "other"}],
        )


def test_ars_learning_projection_exposes_material_passport_source_handoff_refs() -> None:
    module = importlib.import_module("med_autoscience.ars_learning_projection")

    projection = module.build_ars_learning_projection()

    pattern_ids = [pattern["pattern_id"] for pattern in projection["absorbed_patterns"]]
    assert "medical_material_passport_source_handoff" in pattern_ids
    assert projection["truth_surface_mapping"]["medical_material_passport_refs"] == [
        "medical_material_passport.sections.source_readiness_refs",
        "medical_material_passport.sections.claim_evidence_refs",
        "medical_material_passport.sections.review_contract_refs",
        "medical_material_passport.sections.artifact_rebuild_refs",
        "medical_material_passport.sections.human_decision_refs",
        "medical_material_passport.sections.owner_receipt_refs",
    ]
    adapter_contract = projection["source_adapter_contract"]
    assert adapter_contract["records_write_mas_truth"] is False
    assert adapter_contract["always_emit_rejection_log"] is True
    assert adapter_contract["closed_reasons"] == module.SOURCE_ADAPTER_REJECTION_REASONS
    assert adapter_contract["entry_level_reject_continues"] is True
    assert adapter_contract["adapter_level_failure_loud"] is True
    assert projection["metadata_policy"]["medical_material_passport_body_exported"] is False
    assert projection["authority_boundary"]["can_write_evidence_ledger"] is False
    assert projection["authority_boundary"]["can_write_review_ledger"] is False


def _forbidden_body_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {key for key in value if key in FORBIDDEN_BODY_KEYS}
        for child in value.values():
            found.update(_forbidden_body_keys(child))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for child in value:
            found.update(_forbidden_body_keys(child))
        return found
    return set()
