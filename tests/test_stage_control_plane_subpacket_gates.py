from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_GATES = {
    "manuscript_authoring": "manuscript_packet",
    "review_and_quality_gate": "independent_review_packet",
    "finalize_and_publication_handoff": "publication_handoff_admission_packet",
}
FORBIDDEN_READY_CLAIMS = {
    "specialist_output_as_ready",
    "test_pass_as_ready",
    "package_freshness_as_ready",
    "provider_completion_as_ready",
    "generated_surface_status_as_ready",
}


def _stages_by_id(stage_manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    stages = stage_manifest["stages"]
    assert isinstance(stages, list)
    return {stage["stage_id"]: stage for stage in stages}


def _stage_manifest() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "agent" / "stages" / "manifest.json").read_text(encoding="utf-8")
    )


def test_stage_manifest_keeps_six_top_level_stages_with_typed_subpacket_gates() -> None:
    manifest_stages = _stages_by_id(_stage_manifest())

    assert list(manifest_stages) == [
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]

    for stage_id, stage in manifest_stages.items():
        extension = stage["stage_contract_extension"]
        has_gate = "typed_cognitive_subpacket_gate" in extension
        assert has_gate is (stage_id in TARGET_GATES)

    for stage_id, packet_id in TARGET_GATES.items():
        stage = manifest_stages[stage_id]
        gate = stage["stage_contract_extension"]["typed_cognitive_subpacket_gate"]

        assert gate["surface_kind"] == "mas_typed_cognitive_subpacket_gate"
        assert gate["packet_id"] == packet_id
        assert gate["packet_required_before_stage_completion"] is True
        assert gate["readback_surface"] == "stage_contract.typed_cognitive_subpacket_gate"
        assert gate["launch_surface"] == "stage_contract.typed_cognitive_subpacket_gate"
        assert gate["contract_source_ref"].startswith(
            "agent/stages/manifest.json#/stages/"
        )
        assert gate["consumed_ref_families"]
        assert gate["produced_ref_families"]
        assert gate["route_back_conditions"]
        assert gate["typed_blocker_conditions"]
        assert gate["human_gate_conditions"]
        assert set(gate["forbidden_ready_claims"]) == FORBIDDEN_READY_CLAIMS

        admission_gate = gate["admission_gate"]
        assert admission_gate["fail_closed"] is True
        assert admission_gate["owner_receipt_or_typed_blocker_required"] is True
        assert admission_gate["candidate_packet_can_close_stage"] is False
        assert admission_gate["specialist_output_can_claim_ready"] is False
        assert admission_gate["test_pass_can_claim_ready"] is False
        assert admission_gate["package_freshness_can_claim_ready"] is False
        assert {"owner_receipt", "route_back", "typed_blocker", "human_gate"} == set(
            admission_gate["gate_decision_outputs"]
        )

        authority = gate["authority_boundary"]
        assert authority["packet_is_refs_only_candidate"] is True
        assert authority["can_write_publication_eval_latest"] is False
        assert authority["can_write_controller_decisions"] is False
        assert authority["can_mutate_current_package"] is False
        assert authority["can_sign_owner_receipt"] is False
        assert authority["can_materialize_typed_blocker"] is False
        assert authority["can_materialize_human_gate"] is False
        assert authority["can_authorize_publication_quality"] is False
        assert authority["can_authorize_submission_readiness"] is False
