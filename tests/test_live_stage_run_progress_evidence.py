from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts/live_stage_run_progress_evidence.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


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

    for ref in refs["owner_receipt_refs"]:
        contract_ref = ref.split("#", 1)[0]
        assert (REPO_ROOT / contract_ref).exists()
    for ref in refs["no_regression_refs"]:
        contract_ref = ref.split("#", 1)[0]
        assert (REPO_ROOT / contract_ref).exists()


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
