from __future__ import annotations

from med_autoscience.opl_standard_pack import build_standard_pack
from med_autoscience.stage_quality_contract import (
    JOURNAL_FAMILY_QUALITY_PACK_IDS,
    build_stage_quality_pack_contract,
)


REVIEWER_PRECOMMITMENT_PACK_IDS = (
    "ai_native_expert_judgment_pack",
    "medical_claim_evidence_pack",
    *JOURNAL_FAMILY_QUALITY_PACK_IDS,
)


def test_reviewer_facing_quality_packs_expose_paper_blind_precommitment_contract() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    for pack_id in REVIEWER_PRECOMMITMENT_PACK_IDS:
        precommitment = packs[pack_id]["reviewer_precommitment_contract"]

        assert precommitment["contract_id"] == f"{pack_id}.reviewer_precommitment_contract.v1"
        assert precommitment["source_project"] == "academic-research-skills"
        assert precommitment["absorbed_as"] == "mas_native_reviewer_precommitment_contract"
        assert precommitment["separate_invocation_required"] is True
        assert precommitment["rubric_may_authorize_quality_verdict"] is False
        assert precommitment["rubric_may_write_truth"] is False
        assert precommitment["paper_blind_phase"] == {
            "phase_id": "paper_content_blind_precommitment",
            "allowed_inputs": ["quality_pack_descriptor", "paper_metadata_only"],
            "forbidden_inputs": [
                "paper_body",
                "manuscript_package",
                "publication_eval_verdict",
                "controller_decision_verdict",
            ],
            "expected_output_ref": "reviewer_precommitment_record",
        }
        assert precommitment["paper_visible_phase"] == {
            "phase_id": "paper_visible_review",
            "required_inputs": [
                "quality_pack_descriptor",
                "reviewer_precommitment_record",
                "verified_evidence_refs",
                "paper_or_artifact_under_review",
            ],
            "precommitment_record_must_be_reinjected": True,
            "may_rewrite_precommitment_after_viewing_paper": False,
        }
        assert precommitment["required_precommitment_outputs"] == [
            "contract_paraphrase",
            "scoring_plan",
            "contract_acknowledged_receipt",
        ]
        assert precommitment["required_runtime_inputs"] == [
            "quality_pack_descriptor",
            "paper_metadata_only",
            "reviewer_precommitment_record",
            "verified_evidence_refs",
            "paper_or_artifact_under_review",
        ]


def test_stage_quality_contract_exposes_descriptor_only_data_access_isolation_metadata() -> None:
    contract = build_stage_quality_pack_contract()

    isolation = contract["data_access_ground_truth_isolation"]
    assert isolation["source_project"] == "academic-research-skills"
    assert isolation["absorbed_as"] == "mas_native_stage_quality_data_access_descriptor"
    assert isolation["descriptor_only"] is True
    assert isolation["runtime_permission_authority"] is False
    assert isolation["levels"] == [
        {
            "level_id": "raw_source_intake",
            "ars_data_access_level": "raw",
            "mas_scope": "source_intake_or_unverified_workspace_material",
            "may_feed_candidate_generation": True,
            "may_authorize_reviewer_verdict": False,
        },
        {
            "level_id": "verified_evidence_only",
            "ars_data_access_level": "verified_only",
            "mas_scope": "evidence_or_review_refs_after_integrity_gate",
            "may_feed_candidate_generation": True,
            "may_authorize_reviewer_verdict": False,
        },
        {
            "level_id": "reviewer_verdict_only",
            "ars_data_access_level": "verified_only",
            "mas_scope": "reviewer_or_auditor_verdict_record",
            "may_feed_candidate_generation": False,
            "may_authorize_reviewer_verdict": False,
        },
    ]
    assert isolation["ground_truth_boundary"] == {
        "rubric_or_verdict_must_not_seed_candidate_generation": True,
        "reviewer_must_run_as_separate_invocation": True,
        "rubric_may_authorize_quality_verdict": False,
        "rubric_may_write_truth": False,
        "descriptor_grants_runtime_access": False,
    }


def test_stage_control_metadata_projects_data_access_isolation_refs_without_authority() -> None:
    stage_control_plane = build_standard_pack()["stage_control_plane"]

    for stage in stage_control_plane["stages"]:
        assert stage["quality_pack_projection"]["data_access_ground_truth_isolation_ref"] == (
            "/product_entry_manifest/stage_quality_pack_contract/data_access_ground_truth_isolation"
        )
        assert stage["quality_pack_projection"]["data_access_levels"] == [
            "raw_source_intake",
            "verified_evidence_only",
            "reviewer_verdict_only",
        ]
        assert stage["quality_pack_projection"]["runtime_permission_authority"] is False
