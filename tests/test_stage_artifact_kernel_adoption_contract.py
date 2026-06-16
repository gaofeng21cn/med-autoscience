from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts/stage_artifact_kernel_adoption.json").read_text(encoding="utf-8"))


def test_stage_artifact_kernel_adoption_declares_physical_stage_folder_truth() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "opl_stage_artifact_kernel_adoption"
    assert contract["domain_id"] == "med-autoscience"
    assert contract["kernel_contract_ref"] == "contracts/opl-framework/stage-artifact-runtime-contract.json"
    assert contract["kernel_refs"]["physical_stage_folder_source_of_truth"] is True
    assert contract["kernel_refs"]["derived_index_rebuildable"] is True
    assert contract["projection_boundary"]["derived_index_authority"] == "rebuildable_projection_not_primary_truth"
    assert contract["projection_boundary"]["file_presence_only_counts_as"] == "orphan_or_historical"
    assert contract["projection_boundary"]["provider_completion_counts_as_progress"] is False
    assert contract["authority_boundary"]["opl_can_write_domain_truth"] is False
    assert contract["authority_boundary"]["opl_can_mutate_domain_artifact_body"] is False


def test_stage_artifact_kernel_adoption_links_stage_run_kernel_profile() -> None:
    binding = _contract()["stage_run_kernel_profile_binding"]

    assert binding == {
        "profile_ref": "contracts/stage_run_kernel_profile.json",
        "profile_role": "minimal_stage_native_state_shell",
        "stage_run_kernel_is_mas_controller_system": False,
        "ordinary_progress_handoff_ref": "contracts/stage_run_kernel_profile.json#/ordinary_progress_handoff",
        "ordinary_progress_handoff_role": "T0_progress_delta_receipt_policy_not_stage_artifact_completion",
        "stage_native_principle": [
            "stage_folder",
            "stage_manifest",
            "role_artifacts",
            "owner_receipt_or_typed_blocker",
        ],
        "terminal_transition_authority": "owner_receipt_or_typed_blocker",
        "read_model_is_transition_authority": False,
        "file_presence_counts_as_stage_complete": False,
        "provider_completion_counts_as_domain_accepted": False,
    }


def test_state_index_kernel_adoption_keeps_sqlite_refs_only_and_rebuildable() -> None:
    adoption = _contract()["state_index_kernel_adoption"]

    assert adoption["surface_kind"] == "opl_state_index_kernel_sqlite_sidecar_adoption"
    assert adoption["state_index_kernel_owner"] == "one-person-lab"
    assert adoption["sqlite_sidecar_owner"] == "one-person-lab"
    assert adoption["mas_role"] == "primary_small_file_compaction_candidate_and_refs_only_index_source"
    assert adoption["index_authority"] == "derived_refs_only_rebuildable_read_model"
    assert adoption["source_of_truth"] == (
        "physical_stage_folder_files_mas_owned_truth_files_and_domain_owner_receipts"
    )
    assert adoption["derived_index_rebuildable"] is True
    assert adoption["small_file_compaction_target"] is True
    assert "legacy_ds_runtime_mirrors" in adoption["compaction_targets"]
    assert "operator_read_model_projection" in adoption["compaction_targets"]

    assert adoption["allowed_sqlite_payload_roles"] == [
        "ref",
        "locator",
        "cursor",
        "checksum",
        "content_hash",
        "source_fingerprint",
        "idempotency_key",
        "receipt_ref",
        "typed_blocker_ref",
        "restore_proof_ref",
        "bounded_preview_hash",
    ]


def test_state_index_kernel_adoption_forbids_domain_body_and_verdict_payloads() -> None:
    adoption = _contract()["state_index_kernel_adoption"]
    forbidden = set(adoption["forbidden_sqlite_payloads"])
    boundary = adoption["authority_boundary"]

    assert {
        "study_truth_body",
        "publication_eval_body",
        "controller_decision_body",
        "manuscript_body",
        "paper_package_body",
        "evidence_ledger_body",
        "review_ledger_body",
        "memory_body",
        "artifact_body",
        "publication_quality_verdict_body",
        "artifact_authority_verdict_body",
        "owner_receipt_authority",
    } <= forbidden

    assert boundary["mas_can_write_opl_state_index_kernel"] is False
    assert boundary["mas_can_own_generic_sqlite_sidecar"] is False
    assert boundary["opl_can_write_mas_study_truth"] is False
    assert boundary["opl_can_write_publication_eval"] is False
    assert boundary["opl_can_write_controller_decision"] is False
    assert boundary["opl_can_write_manuscript_body"] is False
    assert boundary["opl_can_write_memory_body"] is False
    assert boundary["opl_can_write_artifact_body"] is False
    assert boundary["opl_can_authorize_publication_quality"] is False
    assert boundary["opl_can_authorize_artifact_mutation"] is False
    assert boundary["sqlite_record_counts_as_stage_complete"] is False


def test_legacy_mas_sqlite_policy_remains_domain_authority_refs_not_generic_runtime() -> None:
    policy = _contract()["state_index_kernel_adoption"]["legacy_mas_sqlite_policy"]

    assert policy["domain_authority_refs_sqlite_role"] == "refs_only_domain_authority_index_adapter"
    assert policy["runtime_lifecycle_sqlite_role"] == (
        "retired_or_domain_authority_refs_provenance_not_generic_lifecycle_owner"
    )
    assert policy["paper_progress_transition_refs_role"] == (
        "domain_work_unit_identity_and_policy_request_refs_only"
    )
    assert policy["mas_can_claim_generic_persistence_engine"] is False
    assert policy["mas_can_claim_generic_lifecycle_owner"] is False
    assert policy["mas_can_claim_generic_queue_owner"] is False
    assert policy["mas_can_claim_generic_read_model_owner"] is False


def test_mas_refs_only_state_index_pilot_is_body_free_and_opt_in() -> None:
    pilot = _contract()["state_index_kernel_adoption"]["mas_refs_only_pilot"]

    assert pilot["surface_kind"] == "mas_runtime_refs_only_state_index_pilot"
    assert pilot["implementation_ref"] == "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py"
    assert pilot["maintenance_entry_refs"] == [
        "medautosci runtime maintain-storage --refs-only-state-index-pilot",
        "medautosci runtime storage-audit --apply --refs-only-state-index-pilot",
    ]
    assert pilot["sqlite_ref"] == "artifacts/runtime/mas_refs_only_state_index_pilot.sqlite"
    assert pilot["indexed_ref_families"] == [
        "cursor",
        "index",
        "lifecycle",
        "outbox",
        "receipt_ref",
    ]
    assert pilot["body_included"] is False
    assert pilot["derived_index_rebuildable"] is True
    assert pilot["sqlite_record_counts_as_stage_complete"] is False
    assert pilot["generic_state_index_owner"] == "one-person-lab"
    assert {
        "study_truth_body",
        "publication_eval_body",
        "controller_decision_body",
        "manuscript_body",
        "paper_package_body",
        "evidence_ledger_body",
        "review_ledger_body",
        "memory_body",
        "artifact_body",
        "owner_receipt_authority",
    } <= set(pilot["forbidden_payload_roles"])


def test_operating_layer_landed_surfaces_are_read_only_and_projected() -> None:
    surfaces = _contract()["operating_layer_landed_surfaces"]

    assert set(surfaces) == {
        "state_index_kernel",
        "semantic_receipt_validation",
        "promotion_runtime_audit",
        "lineage_retention_drilldown",
        "workbench_cross_domain_soak",
    }
    assert surfaces["state_index_kernel"]["derived_index_rebuildable"] is True
    assert surfaces["state_index_kernel"]["sqlite_record_counts_as_stage_complete"] is False
    assert surfaces["semantic_receipt_validation"]["receipt_body_read"] is False
    assert surfaces["semantic_receipt_validation"]["ready_claims_allowed"] is False
    assert surfaces["promotion_runtime_audit"]["read_only"] is True
    assert surfaces["promotion_runtime_audit"]["writes_current_pointer"] is False
    assert surfaces["lineage_retention_drilldown"]["cleanup_authorized"] is False
    assert surfaces["lineage_retention_drilldown"]["cleanup_authorized_by_projection"] is False
    assert surfaces["workbench_cross_domain_soak"]["required_domain_lanes"] == [
        "MAS",
        "MAG",
        "OMA",
        "RCA",
    ]
    assert surfaces["workbench_cross_domain_soak"]["can_authorize_domain_readiness"] is False
    assert surfaces["workbench_cross_domain_soak"]["can_authorize_artifact_mutation"] is False
