from __future__ import annotations

from med_autoscience.runtime_protocol.display_artifact_manifest import (
    REQUIRED_DISPLAY_ARTIFACT_FIELDS,
    build_display_artifact_manifest_contract,
    validate_display_artifact_manifest_entry,
)


def test_display_artifact_manifest_contract_preserves_mas_artifact_authority() -> None:
    contract = build_display_artifact_manifest_contract()

    assert contract["surface_kind"] == "mas_display_artifact_manifest_contract"
    assert contract["owner"] == "MedAutoScience"
    assert contract["clean_room_absorption"] == {
        "source_project": "kaust-ark/ARK",
        "source_pattern": "figure_manifest_and_page_adjustment",
        "absorbed_as": "mas_native_display_artifact_contract",
        "runtime_dependency": False,
        "vendor_dependency": False,
        "foreign_artifact_authority": False,
    }
    assert contract["authority_boundary"]["display_artifact_truth_owner"] == "MedAutoScience"
    assert contract["authority_boundary"]["opl_role"] == "refs_index_and_projection_only"
    assert contract["authority_boundary"]["opl_can_mutate_artifact_body"] is False
    assert contract["authority_boundary"]["layout_adjustment_can_change_data"] is False


def test_display_artifact_manifest_required_fields_and_page_policy() -> None:
    contract = build_display_artifact_manifest_contract()

    assert contract["manifest_entry"]["required_fields"] == list(REQUIRED_DISPLAY_ARTIFACT_FIELDS)
    assert set(REQUIRED_DISPLAY_ARTIFACT_FIELDS) >= {
        "artifact_id",
        "artifact_kind",
        "source_data_refs",
        "source_data_digests",
        "claim_refs",
        "statistical_value_refs",
        "rendered_artifact_ref",
        "rendered_artifact_digest",
        "placement",
        "scalable",
        "protected",
        "mutation_authority",
        "visual_qa_receipt_refs",
        "currentness",
    }
    assert contract["page_adjustment_policy"] == {
        "allowed_changes": ["layout", "placement", "density", "caption_length"],
        "forbidden_changes": ["source_data", "claim_refs", "statistical_values", "result_values"],
        "missing_digest_behavior": "mutation_blocker",
        "missing_visual_qa_behavior": "mutation_blocker",
        "may_authorize_artifact_mutation": False,
    }


def test_validate_display_artifact_manifest_entry_fails_closed_for_missing_digest_or_qa() -> None:
    valid_entry = {
        "artifact_id": "fig-risk-calibration",
        "artifact_kind": "figure",
        "source_data_refs": ["analysis/results/calibration.csv"],
        "source_data_digests": ["sha256:source"],
        "claim_refs": ["claim:calibration-slope"],
        "statistical_value_refs": ["stat:calibration-slope"],
        "rendered_artifact_ref": "paper/figures/fig-risk-calibration.pdf",
        "rendered_artifact_digest": "sha256:rendered",
        "placement": "single_column",
        "scalable": False,
        "protected": True,
        "mutation_authority": "mas_artifact_authority_required",
        "visual_qa_receipt_refs": ["visual-qa:receipt"],
        "currentness": {"state": "current", "checked_at": "2026-06-05T00:00:00Z"},
    }

    assert validate_display_artifact_manifest_entry(valid_entry) == {
        "status": "valid",
        "blockers": [],
        "may_authorize_artifact_mutation": False,
    }

    missing_digest = {**valid_entry, "source_data_digests": []}
    assert validate_display_artifact_manifest_entry(missing_digest) == {
        "status": "blocked",
        "blockers": ["source_data_digest_missing"],
        "may_authorize_artifact_mutation": False,
    }

    missing_qa = {**valid_entry, "visual_qa_receipt_refs": []}
    assert validate_display_artifact_manifest_entry(missing_qa) == {
        "status": "blocked",
        "blockers": ["visual_qa_receipt_missing"],
        "may_authorize_artifact_mutation": False,
    }
