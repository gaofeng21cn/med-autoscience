from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.research_integrity.stage_hooks import (
    FORBIDDEN_AUTHORITY_FLAGS,
    build_review_publication_gate_stage_hook_payload,
)


def test_review_publication_gate_stage_hook_builds_reference_verification_gate_input() -> None:
    payload = build_review_publication_gate_stage_hook_payload(
        payload={
            "stage_id": "publication_supervision",
            "stage_event": "review_gate_entered",
            "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
            "source_refs": ["paper/references.bib"],
            "references": [{"id": "smith2024", "doi": "10.1000/example", "title": "Example Trial"}],
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "matched_identifiers": {"doi": "10.1000/example"},
                    "metadata": {"title": "Example Trial", "year": "2024"},
                }
            ],
            "claim": {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:smith2024"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            },
            "manuscript": {
                "results": {
                    "numeric_facts": [
                        {
                            "fact_id": "auc",
                            "reported_value": "0.71",
                            "unit": "AUROC",
                        }
                    ]
                }
            },
            "display_facts": [{"fact_id": "auc", "reported_value": "0.71", "unit": "AUROC"}],
        }
    )

    gate_bundle = payload["gate_input_bundle"]

    assert payload["surface_kind"] == "research_integrity_review_publication_gate_stage_hook"
    assert payload["hook_role"] == "mandatory_review_publication_gate_input"
    assert payload["triggered_action"] == "research-integrity-reference-verification"
    assert "reference_list_entered" in payload["trigger_points"]
    assert "publication_gate_entered" in payload["trigger_points"]
    assert payload["stage_context"] == {
        "stage_id": "publication_supervision",
        "stage_event": "review_gate_entered",
        "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
    }
    assert gate_bundle["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["surfaces"]["research_integrity_reference_verification"]["surfaces"][
        "research_integrity_gate_input_bundle"
    ] == gate_bundle
    assert set(payload["required_gate_input_surfaces"]) == {
        "reference_verification_attestations",
        "claim_citation_support_matrix_v2",
        "manuscript_consistency_meta_review",
    }
    assert gate_bundle["surfaces"]["manuscript_consistency_meta_review"]["status"] == "clear"
    assert all(payload["authority_boundary"][flag] is False for flag in FORBIDDEN_AUTHORITY_FLAGS)
    assert payload["paper_mission_subordination"] == {
        "surface_kind": "mas_paper_mission_subordination",
        "authority_owner": "MedAutoScience",
        "mainline_route": [
            "PaperMission",
            "submission_authority",
            "submission_authority_owner_gate_or_typed_blocker",
        ],
        "control_plane_role": "subordinate_input_or_advisory_only",
        "can_start_parallel_mainline": False,
        "can_bypass_submission_authority": False,
        "can_close_without_owner_gate_or_typed_blocker": False,
    }

    obligation = payload["stage_obligation"]
    assert obligation["obligation_level"] == "mandatory"
    assert obligation["target_stage_ids"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert obligation["mandatory_gate_input"] is True
    assert obligation["live_owner_consumption_claimed"] is False
    assert obligation["paper_mission_subordination"] == payload["paper_mission_subordination"]
    assert obligation["triggered_action"] == "research-integrity-reference-verification"
    assert payload["target_stage_ids"] == obligation["target_stage_ids"]
    provider_lookup = payload["triggered_domain_provider_lookup_contract"]
    assert provider_lookup == obligation["triggered_domain_provider_lookup_contract"]
    assert provider_lookup["surface_kind"] == "mas_domain_provider_lookup_contract"
    assert provider_lookup["owner"] == "MedAutoScience"
    assert provider_lookup["provider_lookup_mode"] == "domain_owned_evidence_input_only"
    assert provider_lookup["provider_evidence_consumed_by"] == "research-integrity-reference-verification"
    assert provider_lookup["mandatory_gate_input_only"] is True
    assert provider_lookup["live_owner_consumption_claimed"] is False
    launch_required_input = payload["stage_launch_required_input"]
    assert launch_required_input == obligation["stage_launch_required_input"]
    assert launch_required_input["surface_kind"] == (
        "research_integrity_stage_launch_required_input"
    )
    assert launch_required_input["launch_surface"] == "codex_cli_launch_packet"
    assert launch_required_input["readback_surface"] == "stage_contract.mandatory_pre_gate_checks"
    assert launch_required_input["mandatory_before_stage_completion"] is True
    assert launch_required_input["required_before_owner_receipt_or_typed_blocker"] is True
    assert launch_required_input["mandatory_gate_input"] is True
    assert launch_required_input["live_owner_consumption_claimed"] is False
    assert launch_required_input["paper_mission_subordination"] == payload["paper_mission_subordination"]
    assert launch_required_input["triggered_action"] == "research-integrity-reference-verification"
    assert launch_required_input["required_gate_input_surfaces"] == list(
        payload["required_gate_input_surfaces"]
    )


def test_stage_control_plane_declares_mandatory_research_integrity_stage_hook_obligation() -> None:
    research_integrity_contract = json.loads(
        (
            Path(__file__).resolve().parents[1] / "contracts/research-integrity-layer.json"
        ).read_text()
    )
    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/stage_control_plane.json").read_text()
    )
    stages = {stage["stage_id"]: stage for stage in contract["stages"]}
    contract_obligation = research_integrity_contract["stage_hook_obligation"]

    assert contract_obligation["surface_kind"] == "research_integrity_stage_hook_obligation"
    assert contract_obligation["obligation_level"] == "mandatory"
    assert contract_obligation["target_stage_ids"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert contract_obligation["live_owner_consumption_claimed"] is False
    assert contract_obligation["paper_mission_subordination"]["mainline_route"] == [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ]
    assert contract_obligation["stage_launch_required_input"]["launch_surface"] == (
        "codex_cli_launch_packet"
    )
    assert contract_obligation["stage_launch_required_input"]["readback_surface"] == (
        "stage_contract.mandatory_pre_gate_checks"
    )

    non_target_stage = stages["manuscript_authoring"]
    assert "mandatory_stage_hook_obligations" not in non_target_stage
    assert "mandatory_pre_gate_checks" not in non_target_stage["stage_contract"]
    assert "mandatory_pre_gate_checks" not in non_target_stage["codex_cli_launch_packet"]

    for stage_id in ("review_and_quality_gate", "finalize_and_publication_handoff"):
        obligations = stages[stage_id]["mandatory_stage_hook_obligations"]
        obligation = next(
            item
            for item in obligations
            if item["hook_id"] == "research-integrity-review-publication-gate-stage-hook"
        )

        assert obligation["surface_kind"] == "research_integrity_stage_hook_obligation"
        assert obligation["obligation_level"] == "mandatory"
        assert obligation["target_stage_ids"] == [
            "review_and_quality_gate",
            "finalize_and_publication_handoff",
        ]
        assert obligation["triggered_action"] == "research-integrity-reference-verification"
        assert obligation["mandatory_gate_input"] is True
        assert obligation["live_owner_consumption_claimed"] is False
        assert obligation["paper_mission_subordination"] == contract_obligation[
            "paper_mission_subordination"
        ]
        assert obligation["authority_boundary"]["can_write_publication_eval_latest"] is False
        assert obligation["authority_boundary"]["can_write_controller_decisions"] is False
        assert obligation["authority_boundary"]["can_mutate_current_package"] is False
        assert obligation["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False

        pre_gate_checks = stages[stage_id]["stage_contract"]["mandatory_pre_gate_checks"]
        launch_pre_gate_checks = stages[stage_id]["codex_cli_launch_packet"][
            "mandatory_pre_gate_checks"
        ]
        assert launch_pre_gate_checks == pre_gate_checks
        assert len(pre_gate_checks) == 1
        pre_gate_check = pre_gate_checks[0]
        assert pre_gate_check["surface_kind"] == (
            "research_integrity_stage_launch_required_input"
        )
        assert pre_gate_check["stage_id"] == stage_id
        assert pre_gate_check["target_stage_ids"] == [stage_id]
        assert pre_gate_check["hook_id"] == "research-integrity-review-publication-gate-stage-hook"
        assert pre_gate_check["command"] == "research-integrity-review-publication-gate-stage-hook"
        assert pre_gate_check["launch_surface"] == "codex_cli_launch_packet"
        assert pre_gate_check["readback_surface"] == "stage_contract.mandatory_pre_gate_checks"
        assert pre_gate_check["triggered_action"] == "research-integrity-reference-verification"
        assert pre_gate_check["required_gate_input_surfaces"] == [
            "reference_verification_attestations",
            "claim_citation_support_matrix_v2",
            "manuscript_consistency_meta_review",
        ]
        assert pre_gate_check["triggered_domain_provider_lookup_contract"] == obligation[
            "triggered_domain_provider_lookup_contract"
        ]
        assert pre_gate_check["mandatory_before_stage_completion"] is True
        assert pre_gate_check["required_before_owner_receipt_or_typed_blocker"] is True
        assert pre_gate_check["mandatory_gate_input"] is True
        assert pre_gate_check["live_owner_consumption_claimed"] is False
        assert pre_gate_check["paper_mission_subordination"] == contract_obligation[
            "paper_mission_subordination"
        ]
        assert pre_gate_check["authority_boundary"]["can_write_publication_eval_latest"] is False
        assert pre_gate_check["authority_boundary"]["can_write_controller_decisions"] is False
        assert pre_gate_check["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
