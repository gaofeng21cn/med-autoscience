from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts/live_stage_run_progress_evidence.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_live_stage_run_progress_evidence_schema_ref_is_repo_tracked() -> None:
    payload = _contract()

    assert payload["schema_ref"] == (
        "contracts/opl-framework/domain-live-stage-run-progress-evidence.schema.json"
    )
    schema_path = REPO_ROOT / str(payload["schema_ref"])
    assert schema_path.exists()

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["properties"]["surface_kind"]["const"] == (
        "domain_live_stage_run_progress_evidence"
    )
    owner_answer_schema = schema["properties"]["current_owner_delta_owner_answer"]
    assert "typed_blocker_ref" in owner_answer_schema["required"]


def test_live_stage_run_progress_evidence_records_domain_owned_refs() -> None:
    payload = _contract()

    assert payload["surface_kind"] == "domain_live_stage_run_progress_evidence"
    assert payload["domain_id"] == "med-autoscience"
    assert payload["domain_agent_id"] == "mas"
    assert payload["owner"] == "MedAutoScience"
    assert payload["status"] == "owner_typed_blocker_recorded_not_ready_claim"
    assert payload["role"] == "w7_domain_owned_live_stage_run_progress_evidence"

    scope = payload["evidence_scope"]
    assert scope["stage_run_progress_evidence_owner"] == "MedAutoScience"
    assert scope["opl_consumer"] == "one-person-lab"
    assert scope["live_paper_line_count"] == 9
    assert scope["success_payload_count"] == 4
    assert scope["typed_blocker_payload_count"] == 5
    assert scope["domain_ready_claimed"] is False
    assert scope["production_ready_claimed"] is False
    assert scope["publication_ready_claimed"] is False
    assert scope["artifact_mutation_authorized"] is False
    assert scope["current_package_mutation_authorized"] is False


def test_live_stage_run_progress_evidence_has_opl_consumable_ref_shapes() -> None:
    payload = _contract()
    refs = payload["refs"]

    assert refs["owner_receipt_refs"]
    assert refs["typed_blocker_refs"]
    assert refs["quality_or_export_receipt_refs"]
    assert refs["human_gate_refs"]
    assert refs["no_regression_refs"]
    assert refs["doc_refs"]
    assert refs["next_verification_command_refs"]
    assert payload["typed_blocker_kind"] == (
        "real_paper_line_owner_receipt_or_monitor_freshness_pending"
    )
    assert "mas-stage-typed-blocker:medautoscience:w7-owner-evidence-tail:" in (
        " ".join(refs["typed_blocker_refs"])
    )

    for ref in refs["owner_receipt_refs"]:
        contract_ref = ref.split("#", 1)[0]
        assert (REPO_ROOT / contract_ref).exists()
    for ref in refs["no_regression_refs"]:
        contract_ref = ref.split("#", 1)[0]
        assert (REPO_ROOT / contract_ref).exists()


def test_live_stage_run_progress_evidence_answers_owner_delta_missing_with_typed_blocker_ref() -> None:
    payload = _contract()
    answer = payload["current_owner_delta_owner_answer"]
    refs = payload["refs"]

    assert answer["surface_kind"] == "mas_current_owner_delta_owner_answer_ref"
    assert answer["status"] == "typed_blocker_ref_recorded_not_ready_claim"
    assert answer["source_observation"] == "current_owner_delta_owner_answer_missing=true"
    assert answer["answers_missing_owner_answer"] is True
    assert answer["current_owner"] == "med-autoscience"
    assert answer["stage_id"] == "paper_autonomy/guarded-apply"
    assert answer["next_required_delta"] == (
        "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    )
    assert answer["accepted_answer_shape"] == "typed_blocker_ref"
    assert answer["accepted_answer_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert answer["owner_answer_ref"] == answer["typed_blocker_ref"]
    assert answer["typed_blocker_ref"] in refs["typed_blocker_refs"]
    assert answer["target_identity"] == {
        "target_key": (
            "medautoscience/current_owner_delta_bridge/owner_payload_item/"
            "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:"
            "owner-answer-or-typed-blocker"
        ),
        "domain_id": "medautoscience",
        "current_owner": "med-autoscience",
        "source_surface": "current_owner_delta_bridge",
        "summary_kind": "owner_payload_item",
        "item_id": (
            "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:"
            "owner-answer-or-typed-blocker"
        ),
        "stage_id": "paper_autonomy/guarded-apply",
        "task_or_study_ref": "medautoscience:frt_dfb2a46c1e1286b88bd02ce6",
        "lineage_ref": "sat_19c64e81217e5b7f8531abc6",
        "current_owner_delta_id": (
            "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:"
            "owner-answer-or-typed-blocker"
        ),
        "source_fingerprint": (
            "owner_delta_first:med-autoscience:medautoscience:"
            "paper-autonomy-guarded-apply:medautoscience-frt-dfb2a46c1e1286b88bd02ce6:"
            "sat-19c64e81217e5b7f8531abc6:"
            "domain-owner-receipt-quality-gate-or-typed-blocker-required:"
            "domain-owner-receipt-ref-or-quality-gate-receipt-ref-or-typed-blocker-ref-or-hum"
        ),
        "payload_kind": "domain_owner_receipt_or_typed_blocker_refs",
        "current_owner_delta_ref": (
            "one-person-lab:/framework_readiness/attention_first_payload/current_owner_delta"
        ),
    }
    assert answer["missing_owner_evidence_sources"] == [
        "real_paper_line_owner_receipt_ref",
        "paper_or_artifact_delta_ref",
        "independent_reviewer_or_auditor_record_ref",
        "human_gate_or_resume_ref",
        "route_back_evidence_ref",
    ]
    assert answer["route_back_conditions"] == [
        "domain_owner_receipt_ref_observed_for_current_stage_run_identity",
        "quality_gate_receipt_ref_observed_for_current_stage_run_identity",
        "human_gate_ref_observed_for_current_stage_run_identity",
        "route_back_evidence_ref_observed_for_current_stage_run_identity",
        "stable_typed_blocker_ref_resolved_to_next_paper_delta_or_human_gate",
    ]
    assert answer["closeout_effect"] == {
        "closes_current_owner_delta_owner_answer_missing": True,
        "domain_ready_claimed": False,
        "publication_ready_claimed": False,
        "production_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_fresh": False,
    }


def test_live_stage_run_progress_evidence_is_not_ready_authority() -> None:
    payload = _contract()
    boundary = payload["authority_boundary"]

    assert boundary["refs_only"] is True
    assert boundary["body_included"] is False
    assert boundary["evidence_owner"] == "domain_repo"
    assert boundary["opl_can_write_domain_truth"] is False
    assert boundary["opl_can_write_publication_eval"] is False
    assert boundary["opl_can_write_controller_decisions"] is False
    assert boundary["opl_can_write_current_package"] is False
    assert boundary["opl_can_mutate_artifact_body"] is False
    assert boundary["opl_can_write_memory_body"] is False
    assert boundary["opl_can_sign_owner_receipt"] is False
    assert boundary["opl_can_create_typed_blocker"] is False
    assert boundary["opl_can_authorize_quality_or_export"] is False
    assert boundary["opl_can_claim_domain_ready"] is False
    assert boundary["opl_can_claim_publication_ready"] is False
    assert boundary["opl_can_claim_production_ready"] is False
    assert boundary["provider_completion_counts_as_domain_ready"] is False
    assert boundary["structural_conformance_counts_as_live_progress"] is False
    assert payload["non_claims"] == {
        "domain_ready": False,
        "publication_ready": False,
        "submission_ready": False,
        "artifact_mutation_authorized": False,
        "current_package_fresh": False,
        "production_ready": False,
    }
