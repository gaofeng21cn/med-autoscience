from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "paper_autonomy_supervisor_contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_paper_autonomy_supervisor_declares_schema_external_patterns_and_boundary() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "mas_paper_progress_policy_adapter_contract"
    assert contract["version"] == "paper-autonomy-supervisor.v1"
    assert contract["owner"] == "MedAutoScience / OPL Framework"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith(
        "This contract defines the MAS paper progress policy adapter handshake"
    )
    assert contract["source_design_ref"] == (
        "docs/runtime/designs/paper_autonomy_supervisor_target.md"
    )
    assert {
        "contracts/stage_route_reconcile_contract.json",
        "contracts/paper_recovery_kernel_contract.json",
        "contracts/stage_run_kernel_profile.json",
        "contracts/progress_first_safety_envelope.json",
    } <= set(contract["related_contract_refs"])

    patterns = contract["external_engineering_patterns"]
    assert patterns["surface_kind"] == "paper_autonomy_external_engineering_patterns"
    assert [item["label"] for item in patterns["source_refs"]] == [
        "Temporal Workflow message passing",
        "AWS Step Functions callback task token",
        "Azure Scheduler Agent Supervisor",
        "LangGraph interrupts and persistence",
    ]
    assert patterns["adoption_mode"] == "pattern_only_no_foreign_runtime_dependency"
    assert patterns["adopted_rules"] == [
        "query_signal_update_split",
        "opl_owned_durable_callback_resume_token",
        "scheduler_agent_supervisor_state_store",
        "persistent_interrupt_resume_same_identity",
        "identity_bound_idempotent_redrive",
    ]
    assert patterns["forbidden_imports"] == [
        "Temporal runtime as MAS-owned scheduler",
        "Step Functions state machine as MAS authority",
        "LangGraph graph state as publication truth",
        "Azure pattern prose as machine contract",
    ]


def test_obligation_contract_requires_identity_timeout_and_nonterminal_pending_states() -> None:
    contract = _contract()

    root = contract["planning_root"]
    assert root["desired_root"] == "current_owner_delta"
    assert root["obligation_surface"] == "paper_autonomy_obligation"
    assert root["decision_surface"] == "supervisor_decision"
    assert root["one_obligation_per_current_owner_delta"] is True
    assert root["read_models_can_create_obligations"] is False

    obligation = contract["paper_autonomy_obligation"]
    assert obligation["surface_kind"] == "paper_autonomy_obligation_contract"
    assert obligation["required_identity_fields"] == [
        "study_id",
        "quest_id",
        "stage_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
        "owner_route_currentness_basis",
    ]
    assert obligation["desired_delta_required_fields"] == [
        "owner",
        "target_surface",
        "required_output_ref_family",
    ]
    assert {
        "provider_admission_identity",
        "running_proof",
        "terminal_closeout",
        "owner_receipt",
        "typed_blocker",
        "human_gate_ref",
        "route_back_evidence_ref",
        "migration_receipt",
    } == set(obligation["expected_next_evidence_allowed"])
    assert obligation["timeout_policy_required_fields"] == [
        "heartbeat_budget",
        "wall_clock_budget_seconds",
        "on_timeout",
    ]
    assert obligation["pending_states_forbidden_as_terminal"] == [
        "operator_decision_required",
        "human_gate",
        "typed_blocker",
        "provider_admission_pending_count=0",
        "action_queue=[]",
    ]
    assert obligation["same_identity_no_progress_effect"] == (
        "supervisor_must_emit_recovery_human_gate_or_stable_blocker"
    )


def test_supervisor_decision_taxonomy_is_closed_and_identity_bound() -> None:
    contract = _contract()
    taxonomy = contract["supervisor_decision_taxonomy"]

    assert taxonomy["decision_field"] == "decision"
    assert taxonomy["decision_field_role"] == "policy_recommendation_label"
    assert taxonomy["decision_field_is_authority"] is False
    assert taxonomy["decision_semantics"] == {
        "surface_kind": "mas_paper_policy_recommendation_semantics",
        "decision_field_role": "policy_recommendation_label",
        "decision_field_is_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_fixed_point_replay": False,
        "can_mutate_recovery_obligation_store": False,
        "requires_opl_supervisor_decision_engine_readback": True,
    }
    readback = taxonomy["opl_supervisor_decision_engine_readback_requirement"]
    assert readback["surface_kind"] == "opl_supervisor_decision_engine_readback_requirement"
    assert readback["runtime_owner"] == "one-person-lab"
    assert readback["runtime_kind"] == "RecoveryObligationStore/SupervisorDecisionEngine"
    assert readback["required_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]
    assert readback["identity_required_fields"] == [
        "study_id",
        "quest_id",
        "stage_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    ]
    assert readback["authority_boundary_required"] == {
        "runtime_owner": "one-person-lab",
        "domain_state_owner": "med-autoscience",
        "mas_can_store_recovery_obligation": False,
        "mas_can_run_supervisor_decision_engine": False,
        "mas_can_run_fixed_point_runtime": False,
        "mas_can_replay_obligation": False,
    }
    assert readback["mas_policy_projection_can_satisfy_readback"] is False
    assert readback["mas_decision_field_is_authority"] is False
    assert taxonomy["allowed_decisions"] == [
        "execute_current_owner_delta",
        "consume_terminal_closeout",
        "materialize_recovery_action",
        "wait_for_owner_with_resume_token",
        "stop_with_stable_typed_blocker",
        "stop_with_owner_receipt",
    ]
    assert "operator_decision_required" not in taxonomy["allowed_decisions"]
    assert taxonomy["decision_required_fields"] == [
        "identity_match",
        "evidence_refs",
        "forbidden_interpretations",
        "next_owner",
        "next_safe_action",
        "paper_progress_classification",
        "platform_repair_classification",
    ]

    cases = {item["decision"]: item for item in taxonomy["decision_cases"]}
    assert set(cases) == set(taxonomy["allowed_decisions"])
    assert cases["execute_current_owner_delta"]["next_owner"] == "OPL Framework"
    assert cases["execute_current_owner_delta"]["required_evidence_refs"] == [
        "paper_autonomy_obligation_ref",
        "provider_admission_identity",
        "no_terminal_closeout_for_same_identity",
    ]
    assert cases["execute_current_owner_delta"]["post_admission_evidence_refs"] == [
        "stage_run_identity_packet",
        "running_proof",
    ]
    assert cases["consume_terminal_closeout"]["next_owner"] == "MedAutoScience"
    assert "terminal_closeout_packet" in cases["consume_terminal_closeout"][
        "required_evidence_refs"
    ]
    assert cases["wait_for_owner_with_resume_token"]["required_resume_fields"] == [
        "human_gate_ref",
        "resume_token",
        "resume_token_owner",
        "mas_can_generate_resume_token",
        "allowed_decisions",
        "timeout_policy",
        "default_safe_branch",
        "current_identity",
    ]
    assert cases["wait_for_owner_with_resume_token"]["next_safe_action"] == (
        "consume_opl_human_gate_resume_token"
    )
    assert cases["wait_for_owner_with_resume_token"]["mas_resume_token_generation_allowed"] is False
    assert cases["stop_with_stable_typed_blocker"]["required_evidence_refs"] == [
        "paper_autonomy_obligation_ref",
        "stable_typed_blocker_ref",
        "budget_or_missing_evidence_ref",
    ]
    assert cases["stop_with_owner_receipt"]["required_evidence_refs"] == [
        "paper_autonomy_obligation_ref",
        "owner_receipt_ref",
    ]
    assert cases["stop_with_owner_receipt"]["paper_progress_classification"] == (
        "mas_owner_receipt_credit"
    )


def test_recovery_action_and_progress_accounting_keep_platform_repair_out_of_paper_progress() -> None:
    contract = _contract()

    recovery = contract["recovery_action_contract"]
    assert recovery["decision"] == "materialize_recovery_action"
    assert recovery["allowed_kinds"] == [
        "mas_control_plane_repair",
        "opl_runtime_repair",
        "study_workspace_migration",
        "operator_policy_materialization",
    ]
    assert recovery["kind_owner_map"] == {
        "mas_control_plane_repair": "MedAutoScience repo",
        "opl_runtime_repair": "OPL Framework repo",
        "study_workspace_migration": "MedAutoScience owner callable",
        "operator_policy_materialization": "MedAutoScience / OPL Framework",
    }
    assert recovery["required_output_refs_any"] == [
        "recovery_receipt_ref",
        "migration_receipt_ref",
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
    ]

    accounting = contract["progress_accounting"]
    assert accounting["classes"] == [
        "paper_semantic_delta",
        "platform_repair_delta",
        "migration_delta",
        "observability_delta",
    ]
    assert accounting["paper_progress_credit_refs"] == [
        "mas_owner_receipt",
        "quality_gate_receipt",
        "ai_reviewer_or_publication_gate_delta",
        "canonical_paper_evidence_review_or_package_delta",
        "human_gate_resume",
        "route_back_evidence",
        "stable_typed_blocker",
    ]
    assert accounting["non_credit_refs"] == [
        "code_commit",
        "docs_update",
        "contract_landed",
        "test_green",
        "state_index_refresh",
        "migration_receipt",
        "observability_trace",
        "provider_transport_success",
    ]
    assert accounting["yang_artifact_repair_class"] == "migration_delta"
    assert accounting["yang_artifact_repair_counts_as_paper_progress"] is False


def test_dhd_apply_consume_only_readback_binds_supervisor_transaction() -> None:
    contract = _contract()

    readback = contract["dhd_apply_consume_only_readback"]
    assert readback["surface_kind"] == "domain_health_diagnostic_apply_consume_only_readback_contract"
    assert readback["required_binding_fields"] == [
        "paper_autonomy_supervisor_decision_id",
        "paper_autonomy_supervisor_decision_kind",
        "paper_autonomy_obligation_ref",
        "paper_autonomy_obligation_identity",
    ]
    assert readback["allowed_success_outcome_kinds"] == [
        "owner_receipt_ref",
        "typed_blocker_ref",
        "provider_admission_pending",
        "running_provider_attempt",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert readback["request_projection_outcome_kinds"] == ["transition_request_pending"]
    assert readback["diagnostic_only_outcome_kinds"] == []
    assert readback["non_advancing_apply_effect"] == "typed_blocker_ref"
    assert readback["forbidden_success_roots"] == [
        "queue_empty",
        "dry_run_status",
        "old_attempt",
        "transport_status",
        "stale_or_unmatched_runtime_residue",
    ]
    assert readback["queue_and_transport_policy"] == {
        "action_queue_can_create_success_outcome": False,
        "queue_empty_can_create_success_outcome": False,
        "dry_run_can_create_success_outcome": False,
        "old_attempt_can_create_success_outcome": False,
        "transport_status_can_create_success_outcome": False,
        "mas_transition_request_can_create_success_outcome": False,
        "provider_admission_pending_requires_opl_runtime_result": True,
    }
    assert readback["outcome_source_policy"] == {
        "success_outcome_source_families": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "request_projection_outcome_source_family": "mas_policy_request_projection",
        "request_projection_is_success_outcome": False,
        "success_requires_opl_foundation_readback_boundary": True,
        "opl_foundation_readback_boundary_required_fields": [
            "surface_kind",
            "source_family",
            "opl_runtime_owner",
            "opl_transition_runtime_kind",
            "consumed_opl_foundation_surfaces",
            "mas_role",
            "mas_can_store_recovery_obligation=false",
            "mas_can_run_supervisor_decision_engine=false",
            "mas_policy_request_projection_can_satisfy_success=false",
        ],
        "supervisor_disallowed_outcome_is_success": False,
    }
    assert readback["consume_only_readback_boundary"] == {
        "surface_kind": "domain_health_diagnostic_apply_consume_only_readback",
        "consumer": "med-autoscience.domain-health-diagnostic.apply",
        "opl_runtime_owner": "one-person-lab",
        "opl_recovery_obligation_store_owner": "one-person-lab",
        "opl_supervisor_decision_engine_owner": "one-person-lab",
        "opl_human_gate_transport_owner": "one-person-lab",
        "opl_stage_run_owner": "one-person-lab",
        "consumed_opl_foundation_surfaces": [
            "RecoveryObligationStore",
            "SupervisorDecisionEngine",
            "HumanGateTransport",
            "StageRunIdentityPacket",
        ],
        "mas_role": "policy_and_authority_readback_consumer",
        "mas_can_store_recovery_obligation": False,
        "mas_can_run_supervisor_decision_engine": False,
        "mas_can_run_fixed_point_runtime": False,
        "mas_can_replay_obligation": False,
        "mas_can_persist_obligation_store": False,
        "mas_can_generate_human_gate_resume_token": False,
        "mas_can_authorize_provider_admission": False,
        "success_requires_source_family": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "success_requires_opl_foundation_readback_boundary": True,
        "request_projection_is_success_outcome": False,
        "supervisor_disallowed_outcome_is_success": False,
    }
    opl_readback = readback["opl_transition_readback_contract"]
    assert opl_readback["surface_kind"] == "opl_domain_progress_transition_result"
    assert opl_readback["runtime_owner"] == "one-person-lab"
    assert opl_readback["runtime_kind"] == "DomainProgressTransitionRuntime"
    assert opl_readback["provider_admission_outcome_kind"] == "provider_admission_pending"
    assert opl_readback["required_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]
    assert opl_readback["identity_required_fields"] == [
        "study_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    ]
    assert opl_readback["causality_required_fields"] == [
        "mas_transition_request_idempotency_key",
        "source_generation",
        "expected_version",
        "derived_from_request=true",
    ]
    assert opl_readback["runtime_refs_required"] == [
        "event_id",
        "outbox_item_id",
        "stage_run_identity.stage_run_id_or_ref",
    ]
    assert opl_readback["authority_boundary_required"] == {
        "runtime_owner": "one-person-lab",
        "domain_state_owner": "med-autoscience",
        "mas_can_authorize_provider_admission": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "provider_completion_is_domain_completion": False,
    }
    assert opl_readback["deprecated_projection_authority"] is False
    assert opl_readback["request_only_effect"] == "transition_request_pending"
    assert opl_readback["non_advancing_apply_effect"] == "typed_blocker_ref"


def test_opl_foundation_and_mas_authority_split_forbid_read_model_authority() -> None:
    contract = _contract()

    authority = contract["authority_split"]
    assert authority["mas_authority_surfaces"] == [
        "PaperProgressPolicyAdapter",
        "PaperRecoveryPolicyAdapter",
        "PaperProgressAccountingAdapter",
        "PaperAuthorityResultShapes",
    ]
    assert authority["opl_substrate_surfaces"] == [
        "StageRunIdentityPacket",
        "HumanGateTransport",
        "RecoveryObligationStore",
        "SupervisorDecisionEngine",
        "StateIndexKernel",
        "Workbench Shell",
        "Observability Plane",
    ]
    assert authority["forbidden_authority_claims"] == [
        "OPL queue or attempt ledger owns medical truth",
        "DHD read-model can close owner receipt",
        "Portal or workbench text can resume human gate",
        "MAS can generate human gate resume tokens",
        "trace span can close quality gate",
        "provider admission or completion is paper progress",
        "migration receipt updates publication readiness",
    ]

    opl = {item["surface"]: item for item in contract["opl_foundation_requirements"]}
    assert set(opl) == set(authority["opl_substrate_surfaces"])
    assert opl["RecoveryObligationStore"]["query_can_mutate"] is False
    assert opl["SupervisorDecisionEngine"]["allowed_outputs"] == (
        contract["supervisor_decision_taxonomy"]["allowed_decisions"]
    )
    assert opl["StateIndexKernel"]["forbidden_payloads"] == [
        "study truth",
        "publication verdict",
        "artifact body",
        "memory body",
        "paper body",
        "owner receipt body",
    ]
    assert opl["HumanGateTransport"]["required_fields"] == [
        "resume_token",
        "owner",
        "allowed_decisions",
        "timeout_policy",
        "default_safe_branch",
        "same_current_identity",
    ]
    assert opl["HumanGateTransport"]["mas_can_generate_resume_token"] is False


def test_migration_status_records_opl_readback_and_mas_owner_gate_materializer() -> None:
    contract = _contract()

    status = contract["migration_status"]
    assert status["lane_1_opl_foundation"]["state"] == (
        "existing_opl_surface_mapping_with_minimal_readback_fixture"
    )
    assert {
        "contracts/opl-framework/stage-route-scheduler-contract.json",
        "src/family-runtime-paper-autonomy.ts",
        "tests/src/family-runtime-paper-autonomy.test.ts",
        "tests/src/stage-route-scheduler-arbiter-substrate-contract.test.ts",
    } <= set(status["lane_1_opl_foundation"]["evidence"])
    assert "production runtime soak complete" in status["lane_1_opl_foundation"][
        "does_not_claim"
    ]

    mas = status["lane_2_mas_authority_kernel"]
    assert mas["state"] == "owner_gate_route_back_recovery_materializer_landed"
    assert {
        "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_report.py",
        "src/med_autoscience/controllers/domain_owner_action_dispatch_parts/opl_execution_preflight.py",
        "tests/test_domain_owner_action_dispatch_cases/current_control_authority_selection.py",
        "tests/test_provider_admission_current_control_cases/owner_gate_route_back_cases.py",
    } <= set(mas["evidence"])
    assert "live paper-line soak complete" in mas["does_not_claim"]
