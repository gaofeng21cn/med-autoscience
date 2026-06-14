from __future__ import annotations

import json
import ast
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "paper_recovery_kernel_contract.json"
REDUCER_PATH = REPO_ROOT / "src" / "med_autoscience" / "controllers" / "paper_recovery_state.py"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _literal_next_action_kinds() -> set[str]:
    module = ast.parse(REDUCER_PATH.read_text(encoding="utf-8"))
    kinds: set[str] = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_next_action":
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            kinds.add(node.args[0].value)
    for node in ast.walk(module):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "next_action_kind":
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        kinds.add(node.value.value)
    return kinds


def test_paper_recovery_kernel_declares_schema_and_authority_boundary() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "mas_paper_recovery_kernel_contract"
    assert contract["version"] == "paper-recovery-kernel.v1"
    assert contract["owner"] == "MedAutoScience"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith("This contract defines PaperRecovery")

    metadata = contract["metadata"]
    assert metadata["schema_name"] == "PaperRecovery"
    assert metadata["state_surface"] == "paper_recovery_state"
    assert metadata["canonical_id_field"] == "recovery_obligation_id"
    assert metadata["canonical_state_owner"] == "MedAutoScience"
    assert metadata["execution_substrate_owner"] == "OPL Framework"
    assert {
        "study_progress",
        "domain_health_diagnostic",
        "operator_status_card",
        "intervention_lane",
        "operator_verdict",
        "auto_runtime_parked",
        "recovery_contract",
        "autonomy_contract",
        "user_visible_projection",
        "DHD provider admission current-control",
        "OPL admission projection",
    } <= set(metadata["projection_consumers"])

    authority = contract["authority_boundaries"]
    assert {
        "PaperRecovery schema and paper_recovery_state truth",
        "recovery_obligation_id selection",
        "current owner delta",
        "owner receipt",
        "quality gate receipt",
        "stable typed blocker",
        "human gate",
        "route-back evidence",
        "canonical changed surface adoption",
    } <= set(authority["mas_authority"])
    assert {
        "StageRun execution",
        "attempt ledger",
        "queue / retry / dead-letter substrate",
        "provider liveness",
        "terminal closeout transport",
        "workbench / operator shell projection",
    } <= set(authority["opl_substrate"])
    assert {
        "study_progress",
        "DHD provider admission",
        "operator_status_card",
        "intervention_lane",
        "operator_verdict",
        "auto_runtime_parked",
        "recovery_contract",
        "autonomy_contract",
        "user_visible_projection",
        "OPL admission",
        "human workbench card",
    } <= set(authority["derived_surfaces_must_read_from_paper_recovery"])

    false_flags = authority["opl_false_authority_flags"]
    assert false_flags == {
        "opl_can_select_recovery_obligation": False,
        "opl_can_mark_paper_progress": False,
        "opl_can_emit_mas_owner_receipt": False,
        "opl_can_authorize_publication_ready": False,
        "opl_can_adopt_manual_foreground_output": False,
        "provider_completion_is_paper_recovery_acceptance": False,
        "transport_status_can_create_current_obligation": False,
        "operator_card_can_be_source_of_truth": False,
    }
    assert {
        "OPL execution substrate owns PaperRecovery",
        "study_progress derives paper recovery independently from PaperRecovery",
        "DHD observe_only alone creates pending recovery execution",
        "operator card status is recovery truth",
        "provider terminal completion is MAS acceptance",
        "manual foreground edit is governed recovery without adoption refs",
    } <= set(authority["forbidden_authority_claims"])


def test_paper_recovery_state_requires_identity_phase_conditions_and_next_action() -> None:
    contract = _contract()
    spec = contract["spec"]

    assert spec["paper_recovery_state_required_fields"] == [
        "surface_kind",
        "schema_version",
        "study_id",
        "recovery_obligation_id",
        "phase",
        "current_authority",
        "conditions",
        "next_safe_action",
        "authority_boundary",
    ]
    assert {
        "surface_kind",
        "version",
        "study_id",
        "quest_id",
        "paper_line_id",
        "source_truth_refs",
        "generated_at",
    } <= set(spec["metadata_required_fields"])
    assert {
        "recovery_obligation_id",
        "target_surface",
        "obligation_kind",
        "current_owner_delta_ref",
        "current_work_unit_identity",
        "acceptance_refs_any",
        "forbidden_authority_claims",
    } <= set(spec["spec_required_fields"])
    assert {
        "phase",
        "conditions",
        "next_safe_action",
        "observed_projection",
        "terminal_closeout_refs",
        "consumed_or_rejected_refs",
        "human_gate_refs",
        "successor_obligation_ref",
    } <= set(spec["status_required_fields"])

    identity = spec["recovery_obligation_id_policy"]
    assert identity["format"] == (
        "paper-recovery::<study_id>::<action_type>::<work_unit_id>::"
        "<work_unit_fingerprint_or_blocker_or_truth_epoch>"
    )
    assert {
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint_or_blocker_type_or_truth_epoch",
    } <= set(identity["required_identity_fields"])
    assert identity["exactly_one_current_obligation"] is True
    assert identity["multiple_current_obligations_effect"] == (
        "projection_inconsistency_fail_closed"
    )
    assert identity["missing_current_obligation_effect"] == (
        "projection_inconsistency_fail_closed"
    )
    assert identity["same_id_redrive_without_new_evidence_allowed"] is False

    interface = spec["recovery_obligation_kernel_interface"]
    assert interface["surface_kind"] == "paper_recovery_obligation_kernel_interface"
    assert interface["module_role"] == "single_authority_decision_root_for_recovery_obligation"
    assert interface["input_families"] == [
        "mas_owner_evidence",
        "opl_execution_observation",
        "terminal_closeout_refs",
        "manual_or_human_gate_refs",
        "read_model_projection_status",
    ]
    assert interface["output_surface"] == "paper_recovery_state"
    assert interface["output_phases"] == contract["spec"]["phase_state_machine"]["allowed_phases"]
    assert interface["derived_surfaces_must_consume_output"] == [
        "current_work_unit",
        "current_execution_envelope",
        "study_progress",
        "domain_health_diagnostic.provider_admission_current_control",
        "domain_handler_export.pending_family_tasks",
        "operator_status_card",
        "OPL admission projection",
        "human workbench card",
    ]
    assert interface["forbidden_derived_surface_behaviors"] == [
        "select_recovery_obligation",
        "override_phase_from_transport_status",
        "derive_provider_admission_from_queue_or_dispatch_residue",
        "derive_owner_receipt_from_provider_completion",
        "treat_read_model_refresh_as_domain_progress",
        "same_obligation_redrive_without_new_evidence",
    ]
    assert interface["migration_sequence"] == [
        "introduce_pure_kernel_decision_fixture",
        "route_current_work_unit_and_dhd_provider_admission_through_kernel_output",
        "route_domain_handler_export_through_kernel_admission_output",
        "retire_duplicate_projection_precedence_logic",
    ]
    assert interface["same_write_set_boundary"] == (
        "implementation_must_not_overlap_live_recovery_reducer_or_provider_admission_lanes_without_fresh_owner"
    )


def test_paper_recovery_phases_are_mutually_exclusive_and_forbid_bad_combinations() -> None:
    contract = _contract()
    state_machine = contract["spec"]["phase_state_machine"]

    assert state_machine["phase_field"] == "phase"
    assert state_machine["mutually_exclusive"] is True
    assert state_machine["allowed_phases"] == [
        "owner_action_ready",
        "admission_pending",
        "admission_blocked",
        "attempt_running",
        "terminal_closeout_ready",
        "owner_answer_consumed",
        "domain_blocked",
        "human_gate",
        "projection_inconsistent",
        "manual_foreground_unadopted",
    ]
    assert state_machine["terminal_phases"] == [
        "owner_answer_consumed",
        "domain_blocked",
        "human_gate",
    ]

    forbidden = {
        item["name"]: item for item in state_machine["forbidden_phase_combinations"]
    }
    assert forbidden["pending_without_identity_bound_provider_admission"]["when_all"] == [
        "phase=admission_pending",
        "identity_bound_provider_admission_candidate_absent",
        "DHD.action_class=observe_only",
    ]
    assert forbidden["pending_without_identity_bound_provider_admission"]["effect"] == (
        "admission_blocked"
    )
    assert forbidden["terminal_without_consume_or_reject"]["effect"] == (
        "force_next_safe_action_consume_or_reject_terminal_closeout"
    )
    assert forbidden["stop_loss_without_successor_or_human_gate"]["effect"] == (
        "remain_fail_closed_no_redrive"
    )
    assert forbidden["manual_foreground_as_governed_recovery"]["effect"] == (
        "manual_work_product_only_no_mas_opl_recovery_claim"
    )


def test_paper_recovery_projection_invariants_fail_closed() -> None:
    contract = _contract()
    invariants = contract["projection_invariants"]

    current = invariants["exactly_one_current_obligation"]
    assert current["required"] is True
    assert current["selector"] == "paper_recovery_state.status.current=true"
    assert current["zero_count_effect"] == "projection_inconsistency_fail_closed"
    assert current["multiple_count_effect"] == "projection_inconsistency_fail_closed"

    pending = invariants["pending_obligation_requires_executable_intent"]
    assert pending["pending_requires_all"] == [
        "phase=admission_pending",
        "next_safe_action=admit_provider_attempt",
        "provider_admission_pending_count=1_or_provider_admission_candidates>=1",
    ]
    assert {
        "phase=admission_pending + identity_bound_provider_admission_candidate_absent",
        "phase=admission_pending + provider_admission_pending_count=0",
        "phase=admission_pending + current_work_unit.status=typed_blocker",
    } <= set(pending["forbidden_combinations"])
    assert pending["violation_effect"] == "admission_blocked_or_projection_inconsistent"

    terminal = invariants["terminal_closeout_must_be_consumed_or_rejected"]
    assert terminal["terminal_closeout_phase"] == "terminal_closeout_ready"
    assert terminal["requires_next_safe_action_any"] == [
        "consume_terminal_closeout",
        "reject_terminal_closeout_as_stale",
    ]
    assert {
        "paper_progress_credit",
        "provider_admission_redrive",
        "publication_ready_claim",
    } <= set(terminal["forbidden_effects"])

    stop_loss = invariants["stop_loss_must_route_to_successor_or_human_gate"]
    assert stop_loss["phase"] == "domain_blocked"
    assert stop_loss["blocker"] == "anti_loop_budget_exhausted"
    assert stop_loss["requires_any"] == [
        "successor_obligation_ref",
        "human_gate_refs",
    ]
    assert stop_loss["same_obligation_redrive_allowed"] is False
    assert stop_loss["violation_effect"] == "remain_fail_closed_no_redrive"

    inconsistent = invariants["projection_inconsistency_fail_closed"]
    assert inconsistent["condition"] == "ProjectionConsistent=False"
    assert inconsistent["effect"] == (
        "no_provider_admission_no_paper_progress_no_owner_receipt_claim"
    )
    assert inconsistent["required_next_safe_action"] == "repair_projection_before_admission"

    visible = invariants["derived_visible_surfaces_must_be_sanitized"]
    assert visible["required"] is True
    assert visible["authoritative_source"] == "paper_recovery_state"
    assert {
        "admission_blocked",
        "projection_inconsistent",
        "manual_foreground_unadopted",
        "terminal_closeout_ready",
        "domain_blocked",
        "human_gate",
    } <= set(visible["applies_when_phase_any"])
    assert {
        "operator_status_card",
        "intervention_lane",
        "operator_verdict",
        "auto_runtime_parked",
        "recovery_contract",
        "autonomy_contract",
        "user_visible_projection",
    } <= set(visible["derived_surfaces"])
    assert {
        "auto_runtime_parked",
        "explicit_resume_pending",
        "awaiting_explicit_wakeup",
        "user_resume_required_for_current_recovery",
        "provider_admission_allowed_when_next_safe_action_forbids_it",
    } <= set(visible["forbidden_residual_claims"])
    assert visible["required_effect"] == (
        "replace_stale_operator_or_parked_projection_with_paper_recovery_phase_and_next_safe_action"
    )


def test_paper_recovery_conditions_next_safe_action_and_manual_adoption() -> None:
    contract = _contract()

    conditions = contract["spec"]["conditions_contract"]
    assert conditions["required_condition_types"] == [
        "CurrentObligationSelected",
        "ProjectionConsistent",
        "ProviderAdmissionAllowed",
        "TerminalCloseoutConsumedOrRejected",
        "AuthorityBoundaryPreserved",
    ]
    assert conditions["condition_required_fields"] == [
        "type",
        "status",
        "reason",
        "source_refs",
        "last_transition_time",
    ]
    projection_condition = conditions["projection_inconsistency_condition"]
    assert projection_condition["type"] == "ProjectionConsistent"
    assert projection_condition["status"] == "False"
    assert projection_condition["effect"] == "fail_closed"
    assert projection_condition["next_safe_action"] == (
        "inspect_fresh_study_progress_and_dhd_dry_run_then_rebuild_projection"
    )

    next_action = contract["spec"]["next_safe_action_contract"]
    assert {
        "consume_terminal_closeout",
        "reject_terminal_closeout_as_stale",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
        "authorize_opl_transport_recovery_or_stable_typed_blocker",
        "honor_stable_typed_blocker",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "materialize_provider_admission_or_owner_callable",
        "provide_opl_execution_authorization_or_human_gate",
        "resolve_owner_gate_decision",
        "route_back_to_owner_or_repair_materialization",
        "run_mas_owner_callable",
        "watch_running_attempt",
        "resolve_typed_blocker",
        "record_human_or_owner_gate",
        "run_admission_apply_or_report_operator_gate",
        "repair_projection_before_admission",
        "adopt_manual_delta_through_mas_owner_receipt",
    } <= set(next_action["allowed_values"])
    assert next_action["terminal_closeout_observed_requires"] == [
        "consume_terminal_closeout",
        "reject_terminal_closeout_as_stale",
    ]
    assert next_action["stop_loss_requires_any"] == [
        "create_successor_recovery_obligation",
        "open_human_gate",
    ]
    assert next_action["projection_inconsistent_requires"] == [
        "repair_projection_before_admission",
    ]
    assert next_action["runtime_transport_retry_exhausted_requires_any"] == [
        "run_mas_owner_callable",
        "authorize_opl_transport_recovery_or_stable_typed_blocker",
    ]
    assert _literal_next_action_kinds() <= set(next_action["allowed_values"])

    manual = contract["manual_foreground_adoption_boundary"]
    assert manual["manual_foreground_possible"] is True
    assert manual["manual_output_default_effect"] == (
        "manual_work_product_only_no_mas_opl_recovery_claim"
    )
    assert manual["adoption_requires_any"] == [
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "canonical_changed_surface_ref_consumed_by_mas_or_opl",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert {
        "mark_paper_recovery_accepted",
        "clear_current_obligation",
        "admit_opl_stage_run_from_manual_output",
        "claim_publication_ready",
        "write_publication_eval_or_controller_decision",
    } <= set(manual["forbidden_without_adoption_refs"])
    assert {
        "study truth artifacts",
        "Yang runtime/study artifacts",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "paper body",
        "OPL provider attempt",
    } <= set(manual["foreground_docs_contract_lane_forbidden_writes"])


def test_paper_recovery_accident_replay_documents_forbidden_acceptance_evidence() -> None:
    contract = _contract()
    replay = contract["accident_replay_contract"]

    assert replay["surface_kind"] == "paper_recovery_accident_replay_contract"
    assert replay["replay_read_sequence"] == [
        "fresh study_progress",
        "paper_recovery_state",
        "domain-health-diagnostic --dry-run",
        "OPL current-control / attempt ledger",
        "owner receipt / typed blocker / human gate / route-back refs",
    ]
    cases = {item["case_id"]: item for item in replay["replay_cases"]}
    assert cases["pending_without_identity_bound_provider_admission"] == {
        "case_id": "pending_without_identity_bound_provider_admission",
        "symptom": (
            "read-model shows pending or actionable owner card while no identity-bound "
            "provider admission candidate/count exists and DHD dry-run is observe_only"
        ),
        "required_outcome": "admission_blocked",
        "next_safe_action": "authorize_opl_transport_recovery_or_stable_typed_blocker",
    }
    assert cases["retry_exhausted_current_mas_owner_callable_available"] == {
        "case_id": "retry_exhausted_current_mas_owner_callable_available",
        "symptom": (
            "provider admission retry is exhausted but the current identity-bound MAS owner "
            "action has a direct study or paper callable"
        ),
        "required_outcome": "owner_action_ready",
        "next_safe_action": "run_mas_owner_callable",
    }
    assert cases["terminal_closeout_not_consumed"]["next_safe_action"] == (
        "consume_terminal_closeout"
    )
    assert cases["same_work_unit_stop_loss"]["required_outcome"] == "domain_blocked"
    assert cases["manual_foreground_unadopted"]["required_outcome"] == (
        "manual_foreground_unadopted"
    )
    assert cases["stale_operator_parked_projection"] == {
        "case_id": "stale_operator_parked_projection",
        "symptom": (
            "operator card, intervention lane, or recovery/autonomy contract still shows "
            "auto_runtime_parked or explicit_resume_pending while paper_recovery_state has "
            "a current blocking phase"
        ),
        "required_outcome": "derived_visible_surfaces_show_paper_recovery_phase",
        "next_safe_action": "use_paper_recovery_state.next_safe_action",
    }
    assert {
        "docs_only_claim",
        "operator_card_status",
        "queue_empty",
        "provider_completion_without_mas_consumption",
        "active_run_id",
        "transport_status",
        "manual_foreground_output_without_adoption_refs",
    } <= set(replay["forbidden_replay_acceptance_evidence"])
