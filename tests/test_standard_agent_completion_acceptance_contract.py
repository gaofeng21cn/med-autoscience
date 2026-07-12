from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "standard_agent_completion_acceptance.json"
LEDGER_PATH = REPO_ROOT / "contracts" / "standard_agent_completion_evidence_status.json"
LIVE_RUNTIME_EVIDENCE_ROLLUP_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-live-runtime-evidence-rollup.json"
)
PINNED_HUMAN_DOC_PATH_PATTERN = re.compile(
    r"\b(?:README(?:\.zh-CN)?\.md|AGENTS\.md|docs/[A-Za-z0-9_./-]+\.md(?:#[A-Za-z0-9_-]+)?|contracts/[A-Za-z0-9_./-]+\.md)\b"
)
MACHINE_TRUTH_HUMAN_DOC_PATH_PATTERN = re.compile(
    r"\b(?:README(?:\.zh-CN)?\.md|AGENTS\.md|docs/[A-Za-z0-9_./-]+\.md(?:#[A-Za-z0-9_-]+)?)\b"
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(r"(?<!workspace:)/Users/[^ \"]+")


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _ledger() -> dict[str, object]:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_standard_agent_completion_acceptance_declares_non_completion_boundary() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "mas_standard_opl_agent_completion_acceptance"
    assert contract["version"] == "standard-opl-agent-completion-acceptance.v1"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith("This contract defines acceptance gates")

    policy = contract["completion_claim_policy"]
    assert policy["definition_landed_status"] == "acceptance_definition_landed"
    assert policy["current_completion_status"] == "evidence_tail_open_not_complete"
    assert policy["definition_landed_can_claim_complete"] is False
    assert policy["classification_zero_can_claim_complete"] is False
    assert policy["docs_updated_can_claim_complete"] is False
    assert policy["contract_tests_green_can_claim_complete"] is False
    assert policy["mas_live_runtime_evidence_rollup_required_for_completion_claim"] is False
    assert policy["opl_runtime_evidence_readback_required_for_completion_claim"] is True
    assert policy["mas_redirect_can_claim_complete"] is False
    assert policy["required_final_claim"] == "all_acceptance_gates_satisfied_with_current_evidence"


def test_standard_agent_completion_acceptance_does_not_pin_human_docs_paths() -> None:
    raw_contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert PINNED_HUMAN_DOC_PATH_PATTERN.findall(raw_contract) == []
    assert "human_doc:mas_ideal_state_gap_plan" in raw_contract
    assert "human_doc:mas_status" in raw_contract
    assert "human_doc:mas_decisions" in raw_contract
    assert "contracts/runtime/mas-live-runtime-evidence-rollup.json" in raw_contract


def test_standard_agent_completion_acceptance_covers_both_user_objectives() -> None:
    contract = _contract()
    scope = contract["scope"]

    assert scope["objective_1"]["id"] == "mas_legacy_baggage_eliminated"
    assert "standard OPL Agent" in scope["objective_1"]["goal"]
    assert scope["objective_2"]["id"] == "standard_agent_failure_mode_not_repeated"
    assert "future OPL-standard-agent" in scope["objective_2"]["goal"]
    assert "MAS-specific paper recovery phases" in scope["objective_2"]["non_goal"]


def test_standard_agent_completion_acceptance_gates_require_sources_and_negative_claims() -> None:
    contract = _contract()
    gates = {gate["gate_id"]: gate for gate in contract["acceptance_gates"]}

    assert set(gates) == {
        "single_default_recovery_and_progress_root",
        "physical_retirement_contract_readback",
        "active_caller_migration_and_no_resurrection",
        "stage_route_has_single_ai_owner",
        "negative_false_completion_tests",
        "live_owner_evidence_for_representative_paper_lines",
        "family_standard_agent_feedback_loop",
    }

    for gate in gates.values():
        assert gate["source_of_truth"], gate["gate_id"]
        assert gate["requires"], gate["gate_id"]
        assert gate["cannot_be_satisfied_by"], gate["gate_id"]

    morphology = gates["physical_retirement_contract_readback"]
    assert "functional_structure_gap_count=0 alone" in morphology["cannot_be_satisfied_by"]
    assert "descriptor ready alone" in morphology["cannot_be_satisfied_by"]
    assert "generated interface ready alone" in morphology["cannot_be_satisfied_by"]

    live = gates["live_owner_evidence_for_representative_paper_lines"]
    assert live["required_status"] == "evidence_required"
    assert "repo tests alone" in live["cannot_be_satisfied_by"]
    assert "contract landed" in live["cannot_be_satisfied_by"]

    family = gates["family_standard_agent_feedback_loop"]
    assert family["required_status"] == "evidence_required"
    assert "copying MAS paper_recovery_state into OPL" in family["cannot_be_satisfied_by"]


def test_standard_agent_completion_acceptance_false_completion_claims_are_explicit() -> None:
    contract = _contract()

    assert {
        "contract_landed",
        "docs_updated",
        "classification_gap_count_zero",
        "functional_structure_gap_count_zero",
        "generated_interface_ready",
        "descriptor_ready",
        "OPL_conformance_passed",
        "queue_empty",
        "provider_completed",
        "workflow_terminal",
        "active_run_id_present",
        "active_run_id_null",
        "domain_diagnostic_observe_only",
        "owner_callable_adapter_residue_cleanup_clean",
        "verified_refs_only_ledger",
        "App_projection_ready",
        "manual_foreground_edit_without_adoption_refs",
        "partial_live_runtime_evidence_rollup",
        "typed_blocker_required_live_runtime_evidence_rollup",
    } <= set(contract["false_completion_claims"])

    assert {
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "canonical_changed_surface_adopted_ref",
        "strict_current_identity_provider_running_proof",
        "OPL_generated_surface_production_consumption_ref",
        "no_active_caller_scan_ref",
        "physical_retirement_owner_decision_ref",
        "no_forbidden_write_proof_ref",
        "cross_agent_standard_conformance_negative_test_ref",
        "opl_runtime_evidence_readback_ref",
    } <= set(contract["allowed_completion_evidence"])

    assert (
        "representative DM002/DM003 governed recovery evidence"
        not in contract["current_open_evidence_tails"]
    )
    assert {
        "physical source morphology scan beyond classification-zero",
        "OPL/OMA production generated-surface caller and long-soak negative conformance",
        "OPL runtime evidence readback for retained tails",
    } <= set(contract["current_open_evidence_tails"])


def test_standard_agent_completion_evidence_ledger_covers_every_acceptance_gate() -> None:
    contract = _contract()
    ledger = _ledger()

    assert ledger["surface_kind"] == "mas_standard_agent_completion_evidence_status"
    assert ledger["contract_ref"] == "contracts/standard_agent_completion_acceptance.json"
    assert (
        ledger["runtime_evidence_readback_redirect_ref"]
        == "contracts/runtime/mas-live-runtime-evidence-rollup.json"
    )
    assert ledger["state"] == "active_evidence_ledger"
    assert ledger["overall_status"] == "evidence_tail_open_not_complete"
    assert ledger["completion_claim_allowed"] is False

    contract_gate_ids = {gate["gate_id"] for gate in contract["acceptance_gates"]}
    ledger_gate_ids = {gate["gate_id"] for gate in ledger["gate_evidence_status"]}
    assert ledger_gate_ids == contract_gate_ids

    allowed_statuses = {
        "satisfied_with_repo_evidence",
        "satisfied_with_live_owner_evidence",
        "evidence_required",
        "blocked_by_live_owner_evidence",
    }
    for gate in ledger["gate_evidence_status"]:
        assert gate["status"] in allowed_statuses, gate["gate_id"]
        assert gate["required_evidence_refs"], gate["gate_id"]
        assert "observed_refs" in gate, gate["gate_id"]
        assert "missing_evidence_tails" in gate, gate["gate_id"]
        assert gate["false_completion_boundary"], gate["gate_id"]


def test_standard_agent_completion_evidence_ledger_routes_runtime_evidence_to_opl() -> None:
    contract = _contract()
    ledger = _ledger()
    redirect_contract = _json(LIVE_RUNTIME_EVIDENCE_ROLLUP_PATH)

    policy = ledger["completion_claim_policy"]
    readback_status = ledger["runtime_evidence_readback_status"]

    assert contract["runtime_evidence_readback_redirect_ref"] == (
        "contracts/runtime/mas-live-runtime-evidence-rollup.json"
    )
    assert policy["mas_live_runtime_evidence_rollup_required_for_completion_claim"] is False
    assert policy["opl_runtime_evidence_readback_required_for_completion_claim"] is True
    assert policy["mas_redirect_can_claim_complete"] is False
    assert redirect_contract["replacement_ref"] == "opl:runtime-evidence-readback"
    assert redirect_contract["mas_live_work_order_generation"] == "retired"
    assert redirect_contract["mas_live_evidence_intake"] == "retired"
    assert readback_status["surface_kind"] == (
        "mas_standard_agent_completion_runtime_evidence_redirect_status"
    )
    assert readback_status["redirect_contract_ref"] == (
        "contracts/runtime/mas-live-runtime-evidence-rollup.json"
    )
    assert readback_status["replacement_ref"] == "opl:runtime-evidence-readback"
    assert readback_status["required_for_standard_agent_completion_claim"] is True
    assert readback_status["completion_claim_allowed"] is False
    assert readback_status["live_runtime_readiness_claim_allowed"] is False
    assert "mas_runtime_evidence_redirect_as_live_readiness" in readback_status[
        "false_completion_boundary"
    ]
    assert (
        ledger["non_claims"][
            "live_runtime_evidence_rollup_typed_blocker_required_means_ready"
        ]
        is False
    )
    assert (
        ledger["non_claims"][
            "representative_live_owner_closeout_means_full_live_runtime_readiness"
        ]
        is False
    )
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_records_representative_live_owner_closeout() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}

    live = gates["live_owner_evidence_for_representative_paper_lines"]
    assert live["status"] == "satisfied_with_live_owner_evidence"
    assert {
        "workspace:Yang/DM-CVD-Mortality-Risk#domain diagnostic-apply-2026-06-15T15:08:10Z/DM002-outcome=typed_blocker_ref/postcondition_ok",
        "workspace:Yang/DM-CVD-Mortality-Risk#domain diagnostic-apply-2026-06-15T15:08:10Z/DM003-outcome=owner_receipt_ref/postcondition_ok",
    } <= set(live["observed_refs"])
    assert live["missing_evidence_tails"] == []
    assert {
        "repo_tests",
        "contract_landed",
        "docs_updated",
        "provider_completed_without_mas_closeout_consumption",
    } <= set(live["false_completion_boundary"])

    family = gates["family_standard_agent_feedback_loop"]
    assert family["status"] == "evidence_required"
    assert "OPL_OMA_family_negative_conformance_receipt_ref" not in family[
        "missing_evidence_tails"
    ]
    assert {
        "production_generated_surface_caller_negative_samples_ref",
        "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
        "long_soak_negative_conformance_ref",
    } <= set(family["missing_evidence_tails"])
    assert "cross_agent_standard_conformance_negative_test_ref" in family[
        "required_evidence_refs"
    ]
    assert {
        (
            "external_repo:one-person-lab@e56b9a7583b64d26f275062f3d2c5561bcf4dc20#"
            "contracts/opl-framework/standard-agent-negative-conformance-samples.json"
        ),
        (
            "external_repo:one-person-lab@e56b9a7583b64d26f275062f3d2c5561bcf4dc20#"
            "tests/src/cli/cases/work-order-execution.test.ts::omaTargetAgentGuardMissingCases"
        ),
    } <= set(family["observed_refs"])

    observations = {
        observation["study_id"]: observation
        for observation in ledger["latest_live_owner_closeout_observations"]
    }
    assert observations["002-dm-china-us-mortality-attribution"][
        "progress_first_outcome"
    ] == "blocked_with_typed_owner"
    assert observations["003-dpcc-primary-care-phenotype-treatment-gap"][
        "progress_first_outcome"
    ] == "terminal_success"
    for observation in observations.values():
        assert observation["completion_evidence"] is True
        assert observation["can_close_live_owner_gate"] is True
        assert observation["paper_progress_delta"] is False


def test_standard_agent_completion_evidence_ledger_records_opl_family_negative_conformance_samples() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}
    negative = gates["negative_false_completion_tests"]
    family = gates["family_standard_agent_feedback_loop"]

    negative_sample_ref = (
        "external_repo:one-person-lab@e56b9a7583b64d26f275062f3d2c5561bcf4dc20#"
        "contracts/opl-framework/standard-agent-negative-conformance-samples.json"
    )
    acceptance_sample_ref = (
        "external_repo:one-person-lab@e56b9a7583b64d26f275062f3d2c5561bcf4dc20#"
        "tests/src/standard-agent-landing-acceptance-contract.test.ts::standard agent landing "
        "negative conformance has repo-backed cross-agent samples"
    )
    oma_guard_ref = (
        "external_repo:one-person-lab@e56b9a7583b64d26f275062f3d2c5561bcf4dc20#"
        "tests/src/cli/cases/work-order-execution.test.ts::omaTargetAgentGuardMissingCases"
    )

    assert {negative_sample_ref, acceptance_sample_ref} <= set(
        negative["observed_refs"]
    )
    assert negative["missing_evidence_tails"] == []
    assert {negative_sample_ref, oma_guard_ref} <= set(family["observed_refs"])
    assert {
        "production_generated_surface_caller_negative_samples_ref",
        "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
        "long_soak_negative_conformance_ref",
    } <= set(family["missing_evidence_tails"])
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_records_single_ai_route_owner_without_completion_claim() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}
    stage_route = gates["stage_route_has_single_ai_owner"]

    expected_refs = {
        "contracts/stage_operating_principles.json#/speed_policy",
        "tests/test_ai_route_context.py",
        "tests/test_stage_closure_terminalizer.py::test_retry_budget_and_repeated_signature_never_block_progress",
        "tests/test_paper_mission_stage_run_readback.py",
    }

    assert stage_route["status"] == "satisfied_with_repo_evidence"
    assert expected_refs <= set(stage_route["observed_refs"])
    assert (
        "second_semantic_control_plane_removal_ref"
        not in stage_route["missing_evidence_tails"]
    )
    assert stage_route["missing_evidence_tails"] == []
    assert ledger["overall_status"] == "evidence_tail_open_not_complete"
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_records_physical_retirement_contract_readback_without_completion_claim() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}
    morphology = gates["physical_retirement_contract_readback"]

    scan_ref = "contracts/functional_privatization_audit.json#/bridge_exit_gate"
    scan_test_ref = (
        "tests/test_standard_agent_completion_acceptance_contract.py::"
        "test_standard_agent_completion_evidence_ledger_records_physical_retirement_contract_readback_without_completion_claim"
    )
    assert morphology["status"] == "evidence_required"
    assert scan_ref in morphology["required_evidence_refs"]
    assert {scan_ref, scan_test_ref} <= set(morphology["observed_refs"])
    assert "runtime:domain-diagnostic-obligation-actuator-retired" in morphology[
        "observed_refs"
    ]
    assert (
        "tests/test_adapter_retirement_boundary.py::"
        "test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory"
    ) in morphology["observed_refs"]
    assert (
        "compact_audit_contract_alone_proves_physical_retirement"
        not in morphology["missing_evidence_tails"]
    )
    assert morphology["missing_evidence_tails"] == [
        "direct_or_hosted_generated_surface_production_consumption_ref"
    ]
    assert {
        "functional_structure_gap_count_zero",
        "descriptor_ready",
        "generated_interface_ready",
        "history_or_tombstone_prose",
    } <= set(morphology["false_completion_boundary"])
    assert ledger["overall_status"] == "evidence_tail_open_not_complete"
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_records_domain_diagnostic_actuator_retirement() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}
    morphology = gates["physical_retirement_contract_readback"]
    inventory = json.loads(
        (
            REPO_ROOT
            / "contracts"
            / "runtime"
            / "mas-runtime-surface-retirement-inventory.json"
        ).read_text(encoding="utf-8")
    )
    surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}
    assert "domain_diagnostic_obligation_actuator" not in surfaces
    assert "runtime:domain-diagnostic-obligation-actuator-retired" in morphology[
        "observed_refs"
    ]
    assert "physical_retirement_owner_decision_ref" not in morphology["missing_evidence_tails"]
    assert morphology["status"] == "evidence_required"
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_records_lifecycle_owner_followthrough_without_ready_claim() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}

    followthrough = ledger["latest_owner_followthrough_evidence"][0]
    assert followthrough["surface_kind"] == "mas_memory_artifact_lifecycle_owner_followthrough"
    assert followthrough["status"] == "typed_blocker_followthrough_recorded_not_ready"
    assert followthrough["source_lane_id"] == "memory_artifact_lifecycle_apply"
    assert followthrough["source_readiness_status"] == "typed_blocker_work_order_required_not_ready"
    assert followthrough["typed_blocker_reason"] == (
        "canonical-regeneration-required-before-projection-removal"
    )
    assert followthrough["typed_blocker_ref_count"] == 25
    assert len(followthrough["typed_blocker_refs"]) == 25
    assert all(
        ref.startswith(
            "mas-artifact-lifecycle-typed-blocker:medautoscience:"
            "canonical-regeneration-required-before-projection-removal:"
        )
        for ref in followthrough["typed_blocker_refs"]
    )
    assert followthrough["blocked_decision_count"] == 25
    assert followthrough["safe_decision_count"] == 0
    assert followthrough["closes_work_order_followthrough"] is True
    assert followthrough["closes_artifact_lifecycle_receipt_scaleout"] is False
    assert followthrough["closes_memory_or_artifact_ready"] is False
    assert followthrough["ready_claim_authorized"] is False
    assert followthrough["authority_boundary"] == {
        "mas_writes_domain_truth": False,
        "mas_writes_memory_body": False,
        "mas_mutates_artifact_body": False,
        "mas_authorizes_package_readiness": False,
        "mas_authorizes_export_readiness": False,
        "opl_cleanup_apply_can_execute": True,
        "opl_can_claim_domain_ready": False,
        "opl_can_claim_production_ready": False,
    }

    family = gates["family_standard_agent_feedback_loop"]
    assert family["status"] == "evidence_required"
    assert followthrough["source_work_order_ref"] in family["observed_refs"]
    assert (
        "contracts/functional_privatization_audit.json#/bridge_exit_gate"
    ) in family["observed_refs"]

    assert ledger["completion_claim_allowed"] is False
    assert ledger["non_claims"]["memory_artifact_ready"] is False
    assert ledger["non_claims"]["artifact_ready"] is False
    assert ledger["non_claims"]["package_export_ready"] is False
    assert (
        ledger["non_claims"]["memory_or_artifact_lifecycle_work_order_complete_means_ready"]
        is False
    )


def test_standard_agent_completion_evidence_ledger_records_retired_owner_callable_adapter_residue_cleanup_receipt_without_progress_claim() -> None:
    contract = _contract()
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}

    cleanup = ledger["historical_owner_callable_dispatch_residue_cleanup_receipt"]
    assert "latest_owner_callable_dispatch_residue_cleanup" not in ledger
    assert cleanup["surface_kind"] == "owner_callable_dispatch_residue_cleanup_historical_receipt"
    assert cleanup["source_surface_kind"] == "owner_callable_dispatch_residue_cleanup"
    assert cleanup["workspace_ref"] == "workspace:Yang/DM-CVD-Mortality-Risk"
    assert cleanup["status"] == "historical_clean_receipt"
    assert cleanup["repo_source_disposition"] == "physically_retired"
    assert cleanup["active_cli_command_retired"] is True
    assert cleanup["active_controller_module_retired"] is True
    assert cleanup["active_compat_test_retired"] is True
    assert cleanup["current_entry_allowed"] is False
    assert cleanup["apply_observed_at"] == "2026-06-15T15:57:03Z"
    assert cleanup["dry_run_observed_at"] == "2026-06-15T16:09:23Z"
    assert cleanup["archived_mutable_slot_count"] == 23
    assert cleanup["remaining_mutable_dispatch_json_count"] == 0
    assert cleanup["remaining_cleanup_candidate_count"] == 0
    assert cleanup["immutable_dispatch_provenance_file_count"] == 396
    assert cleanup["authority_boundary"] == {
        "owner_callable_adapter_mutable_residue_mutation": True,
        "immutable_dispatch_provenance_mutation": False,
        "domain_diagnostic_apply": False,
        "provider_start": False,
        "paper_content_mutation": False,
        "publication_truth_mutation": False,
        "runtime_truth_mutation": False,
    }
    assert cleanup["completion_boundary"] == {
        "closes_yang_stale_ready_dispatch_physical_cleanup": True,
        "closes_live_owner_gate": False,
        "closes_paper_recovery": False,
        "paper_progress_delta": False,
        "publication_ready": False,
        "current_package_fresh": False,
    }

    receipts = {receipt["study_id"]: receipt for receipt in cleanup["study_receipts"]}
    assert receipts["002-dm-china-us-mortality-attribution"]["receipt_ref"] == (
        "workspace:Yang/DM-CVD-Mortality-Risk/studies/"
        "002-dm-china-us-mortality-attribution#artifacts/migration/"
        "owner_callable_dispatch_residue_cleanup/latest.json"
    )
    assert receipts["002-dm-china-us-mortality-attribution"]["archived_mutable_slot_count"] == 14
    assert receipts["002-dm-china-us-mortality-attribution"]["currentness_basis"] == "typed_blocker"
    assert receipts["003-dpcc-primary-care-phenotype-treatment-gap"]["receipt_ref"] == (
        "workspace:Yang/DM-CVD-Mortality-Risk/studies/"
        "003-dpcc-primary-care-phenotype-treatment-gap#artifacts/migration/"
        "owner_callable_dispatch_residue_cleanup/latest.json"
    )
    assert receipts["003-dpcc-primary-care-phenotype-treatment-gap"]["archived_mutable_slot_count"] == 9
    assert receipts["003-dpcc-primary-care-phenotype-treatment-gap"]["currentness_basis"] == (
        "owner_receipt_recorded"
    )
    assert all(receipt["paper_progress_delta"] is False for receipt in receipts.values())

    active_caller = gates["active_caller_migration_and_no_resurrection"]
    assert {
        (
            "workspace:Yang/DM-CVD-Mortality-Risk#owner-callable-adapter-residue-cleanup-apply-"
            "2026-06-15T15:57:03Z/archived_mutable_slots=23/immutable_preserved=396"
        ),
        (
            "workspace:Yang/DM-CVD-Mortality-Risk#owner-callable-adapter-residue-cleanup-dry-run-"
            "2026-06-15T16:09:23Z/status=clean/mutable_slots=0/candidates=0"
        ),
    } <= set(active_caller["observed_refs"])

    negative = gates["negative_false_completion_tests"]
    assert (
        "tests/test_standard_agent_completion_acceptance_contract.py::"
        "test_standard_agent_completion_evidence_ledger_records_retired_owner_callable_adapter_residue_cleanup_receipt_without_progress_claim"
    ) in negative["observed_refs"]
    assert "owner_callable_adapter_residue_cleanup_clean" in contract["false_completion_claims"]
    assert "owner_callable_adapter_residue_cleanup_clean" in ledger["rejected_completion_claims"]
    assert ledger["non_claims"]["owner_callable_adapter_residue_cleanup_clean"] is False
    assert ledger["non_claims"]["owner_callable_adapter_residue_cleanup_means_paper_progress"] is False
    assert ledger["completion_claim_allowed"] is False


def test_standard_agent_completion_evidence_ledger_rejects_docs_as_machine_truth_refs() -> None:
    ledger = _ledger()

    for gate in ledger["gate_evidence_status"]:
        machine_refs = gate["required_evidence_refs"] + gate["observed_refs"]
        for ref in machine_refs:
            assert not MACHINE_TRUTH_HUMAN_DOC_PATH_PATTERN.search(ref), (
                gate["gate_id"],
                ref,
            )
            assert not ABSOLUTE_LOCAL_PATH_PATTERN.search(ref), (
                gate["gate_id"],
                ref,
            )


def test_standard_agent_completion_evidence_ledger_keeps_false_claims_rejected() -> None:
    contract = _contract()
    ledger = _ledger()

    assert set(contract["false_completion_claims"]) <= set(
        ledger["rejected_completion_claims"]
    )
    assert ledger["completion_claim_policy"]["required_final_claim"] == (
        "all_acceptance_gates_satisfied_with_current_evidence"
    )
    assert ledger["completion_claim_policy"]["current_completion_status"] == (
        "evidence_tail_open_not_complete"
    )
    assert (
        ledger["completion_claim_policy"][
            "mas_live_runtime_evidence_rollup_required_for_completion_claim"
        ]
        is False
    )
    assert ledger["completion_claim_policy"][
        "opl_runtime_evidence_readback_required_for_completion_claim"
    ] is True
    assert ledger["completion_claim_policy"]["mas_redirect_can_claim_complete"] is False
    assert ledger["completion_claim_policy"]["completion_requires_all_gate_statuses"] == [
        "satisfied",
        "retired_with_owner_decision",
        "not_applicable_with_owner_decision",
    ]
