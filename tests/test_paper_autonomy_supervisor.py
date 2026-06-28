from __future__ import annotations

from med_autoscience.controllers.paper_autonomy_supervisor import (
    build_paper_autonomy_obligation,
    build_supervisor_decision,
)
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    execute_decision_identity_evidence_complete,
    provider_admission_supervisor_gate,
    supervisor_decision_for_projection,
)
from tests.provider_admission_current_control_helpers import opl_transition_readback
from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _typed_blocker_work_unit,
)


def test_execute_decision_requires_provider_and_stage_run_identity() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(fingerprint=fingerprint)
        | {
            "state": {"provider_admission_pending": True},
        },
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "provider_admission_ref": "provider-admission:dm003:repair",
                "stage_packet_ref": "stage-packet:dm003:repair",
            }
        ],
        "stage_run_identity_packet": {
            "stage_run_id": "stage-run-dm003",
            "lease_ref": "lease:dm003",
            "provider_attempt_ref": "provider-attempt:dm003",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_authority": {
                "owner": "write",
                "obligation": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "currentness_basis": {
                        "work_unit_fingerprint": fingerprint,
                        "idempotency_key": "idem-dm003",
                    },
                },
            },
            "next_safe_action": {"kind": "admit_provider_attempt"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["surface_kind"] == "paper_progress_policy_result_projection"
    assert decision["projection_role"] == "mas_paper_progress_policy_result_projection"
    assert decision["policy_result_role"] == "mas_paper_progress_policy_result_projection"
    assert decision["authority"] is False
    assert decision["decision_authority"] is False
    assert decision["legacy_surface_kind"] == "paper_autonomy_supervisor_decision"
    assert decision["legacy_decision_surface_kind"] == "paper_autonomy_supervisor_decision"
    assert decision["legacy_decision_field"] == decision["decision"]
    assert decision["legacy_decision_field_role"] == "policy_recommendation_label"
    assert decision["legacy_decision_field_is_authority"] is False
    assert decision["decision_field_deprecated"] is True
    assert decision["supervisor_decision_engine_owner"] == "one-person-lab"
    assert decision["recovery_obligation_store_owner"] == "one-person-lab"
    assert decision["mas_can_run_supervisor_decision_engine"] is False
    assert decision["mas_can_store_recovery_obligation"] is False
    assert decision["decision_semantics"] == {
        "surface_kind": "mas_paper_policy_recommendation_semantics",
        "decision_field_role": "policy_recommendation_label",
        "decision_field_is_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_fixed_point_replay": False,
        "can_mutate_recovery_obligation_store": False,
        "requires_opl_supervisor_decision_engine_readback": True,
    }
    assert decision["opl_supervisor_decision_engine_readback_requirement"] == {
        "surface_kind": "opl_supervisor_decision_engine_readback_requirement",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "RecoveryObligationStore/SupervisorDecisionEngine",
        "required_sections": [
            "identity",
            "causality",
            "authority_boundary",
            "exactly_one_outcome",
            "projection_metadata",
        ],
        "identity_required_fields": [
            "study_id",
            "quest_id",
            "stage_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        ],
        "authority_boundary_required": {
            "runtime_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
            "mas_can_store_recovery_obligation": False,
            "mas_can_run_supervisor_decision_engine": False,
            "mas_can_run_fixed_point_runtime": False,
            "mas_can_replay_obligation": False,
        },
        "mas_policy_projection_can_satisfy_readback": False,
        "mas_decision_field_is_authority": False,
    }
    assert decision["opl_supervisor_decision_engine_boundary"] == {
        "surface_kind": "opl_supervisor_decision_engine_boundary",
        "owner": "one-person-lab",
        "mas_role": "policy_result_projection_consumer",
        "mas_can_run_decision_engine": False,
        "mas_can_persist_recovery_obligation_store": False,
    }
    projection = decision["paper_progress_policy_result_projection"]
    assert projection["surface_kind"] == "paper_progress_policy_result_projection"
    assert projection["adapter_kind"] == "mas_policy_adapter"
    assert projection["projection_role"] == "mas_paper_progress_policy_result_projection"
    assert projection["authority"] == "mas_paper_progress_policy_adapter"
    assert projection["policy_recommendation_label"] == "execute_current_owner_delta"
    assert projection["policy_recommendation_label_is_authority"] is False
    assert projection["legacy_decision_surface_kind"] == "paper_autonomy_supervisor_decision"
    assert projection["legacy_decision_field"] == decision["decision"]
    assert projection["legacy_decision_field_role"] == "policy_recommendation_label"
    assert projection["legacy_decision_field_is_authority"] is False
    assert projection["decision_authority"] is False
    assert projection["mas_can_run_supervisor_decision_engine"] is False
    assert projection["mas_can_store_recovery_obligation"] is False
    assert projection["mas_can_create_opl_command_event_or_outbox"] is False
    assert projection["mas_can_authorize_provider_admission"] is False
    assert projection["paper_autonomy_obligation_ref"] == decision[
        "paper_autonomy_obligation_ref"
    ]
    assert projection["next_owner"] == decision["next_owner"]
    assert projection["next_safe_action"] == decision["next_safe_action"]
    assert projection["evidence_refs"] == decision["evidence_refs"]
    assert projection["missing_evidence_refs"] == decision.get("missing_evidence_refs", [])
    assert decision["source_of_truth_chain"] == [
        "DomainIntent",
        "OPL Command/Event/Outbox/StageRun",
        "MAS OwnerAnswer",
        "Derived Projection",
    ]
    assert decision["authority_boundary"]["adapter_kind"] == "mas_policy_adapter"
    assert decision["authority_boundary"]["decision_authority"] is False
    assert decision["authority_boundary"]["supervisor_decision_engine_owner"] == (
        "one-person-lab"
    )
    assert decision["authority_boundary"]["recovery_obligation_store_owner"] == (
        "one-person-lab"
    )
    assert decision["authority_boundary"]["opl_supervisor_decision_engine_owner"] == (
        "one-person-lab"
    )
    assert decision["authority_boundary"]["can_store_recovery_obligation"] is False
    assert decision["authority_boundary"]["can_generate_supervisor_decision_authority"] is False
    assert decision["authority_boundary"]["can_create_opl_command_event_or_outbox"] is False
    assert decision["authority_boundary"]["can_own_stage_run"] is False
    assert decision["authority_boundary"]["can_generate_human_gate_resume_token"] is False
    assert decision["authority_boundary"]["provider_admission_requires_opl_stage_run_readback"] is True
    assert decision["decision"] == "execute_current_owner_delta"
    assert decision["next_owner"] == "OPL Framework"
    assert decision["next_safe_action"]["kind"] == "admit_or_resume_stage_run"
    assert decision["identity_match"] is True
    assert "provider-admission:dm003:repair" in decision["evidence_refs"]
    assert "stage-run-dm003" in decision["evidence_refs"]
    assert decision["paper_progress_classification"] == "none_until_mas_owner_result"


def test_execute_decision_gate_requires_provider_and_stage_run_evidence_together() -> None:
    provider_only = _execute_decision_with_evidence(["provider-admission:dm003:repair"])
    stage_only = _execute_decision_with_evidence(["stage-run-dm003"])
    both = _execute_decision_with_evidence([
        "provider-admission:dm003:repair",
        "stage-run-dm003",
    ])

    assert execute_decision_identity_evidence_complete(provider_only) is False
    assert provider_admission_supervisor_gate(
        {"paper_autonomy_supervisor_decision": provider_only}
    ) == {
        "blocked": True,
        "admission_allowed": False,
        "reason": "execute_current_owner_delta_missing_identity_or_evidence",
        "supervisor_decision": provider_only,
    }

    assert execute_decision_identity_evidence_complete(stage_only) is False
    assert provider_admission_supervisor_gate(
        {"paper_autonomy_supervisor_decision": stage_only}
    )["blocked"] is True

    assert execute_decision_identity_evidence_complete(both) is True
    assert provider_admission_supervisor_gate(
        {"paper_autonomy_supervisor_decision": both}
    )["admission_allowed"] is True


def test_projection_helper_does_not_build_supervisor_decision_without_explicit_readback() -> None:
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(),
    }
    paper_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_authority": {
            "owner": "write",
            "obligation": {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
        },
        "next_safe_action": {"kind": "admit_provider_attempt"},
    }

    decision = supervisor_decision_for_projection(
        payload,
        paper_recovery_state=paper_recovery_state,
    )

    assert decision["decision"] == "opl_supervisor_decision_readback_required"
    assert decision["decision_authority"] is False
    assert decision["read_model_can_build_supervisor_decision"] is False
    assert decision["mas_can_run_supervisor_decision_engine"] is False
    assert decision["mas_can_store_recovery_obligation"] is False
    assert decision["requires_opl_supervisor_decision_engine_readback"] is True
    assert decision["provider_admission_pending"] is False
    assert decision["missing_evidence_refs"] == [
        "explicit_paper_autonomy_supervisor_decision_projection",
        "opl_supervisor_decision_engine_readback",
    ]
    assert "paper_autonomy_obligation" not in decision

    gate = provider_admission_supervisor_gate(
        payload,
        paper_recovery_state=paper_recovery_state,
    )
    assert gate == {
        "blocked": True,
        "admission_allowed": False,
        "reason": "opl_supervisor_decision_readback_required",
        "supervisor_decision": decision,
    }


def test_readback_required_projection_accepts_same_identity_opl_runtime_readback_only() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    obligation_identity = {
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    supervisor_decision = {
        "decision": "opl_supervisor_decision_readback_required",
        "paper_autonomy_obligation_identity": dict(obligation_identity),
    }
    recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": study_id,
        "current_authority": {"owner": "write", "obligation": dict(obligation_identity)},
        "supervisor_decision": dict(supervisor_decision),
    }
    candidate = {
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "opl_transition_readback_source": "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_result": opl_transition_readback(
            study_id,
            action_fingerprint=fingerprint,
            work_unit_id=work_unit_id,
        ),
    }

    allowed = provider_admission_supervisor_gate(
        {"study_id": study_id, "provider_admission_candidates": [candidate]},
        paper_recovery_state=recovery,
    )
    blocked = provider_admission_supervisor_gate(
        {
            "study_id": study_id,
            "provider_admission_candidates": [
                {**candidate, "work_unit_fingerprint": "different-fingerprint"}
            ],
        },
        paper_recovery_state=recovery,
    )

    assert allowed == {
        "blocked": False,
        "admission_allowed": True,
        "supervisor_decision": supervisor_decision,
    }
    assert blocked["blocked"] is True
    assert blocked["reason"] == "opl_supervisor_decision_readback_required"


def test_materialize_recovery_action_gate_requires_bound_opl_readback() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    supervisor_decision = {
        "decision": "materialize_recovery_action",
        "paper_autonomy_obligation": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "next_safe_action": {
            "kind": "materialize_recovery_work_unit_or_receipt",
            "source_next_safe_action": {
                "kind": "admit_provider_attempt",
                "provider_admission_requires_opl_runtime_result": False,
            },
        },
    }
    recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": study_id,
        "current_authority": {
            "owner": "write",
            "obligation": dict(supervisor_decision["paper_autonomy_obligation"]),
        },
        "next_safe_action": {
            "kind": "admit_provider_attempt",
            "provider_admission_requires_opl_runtime_result": False,
        },
        "supervisor_decision": dict(supervisor_decision),
    }
    request_only_payload = {
        "study_id": study_id,
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "provider_admission_pending": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_readback_source": "opl_domain_progress_transition_runtime_live_readback",
            }
        ],
    }
    readback_payload = {
        "study_id": study_id,
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "opl_transition_readback_source": "opl_domain_progress_transition_runtime_live_readback",
                "opl_domain_progress_transition_result": opl_transition_readback(
                    study_id,
                    action_fingerprint=fingerprint,
                    work_unit_id=work_unit_id,
                ),
            }
        ],
    }

    blocked = provider_admission_supervisor_gate(
        request_only_payload,
        paper_recovery_state=recovery,
    )
    allowed = provider_admission_supervisor_gate(
        readback_payload,
        paper_recovery_state=recovery,
    )

    assert blocked["blocked"] is True
    assert blocked["reason"] == "paper_autonomy_supervisor_decision_blocks_provider_admission"
    assert allowed == {
        "blocked": False,
        "admission_allowed": True,
        "supervisor_decision": supervisor_decision,
    }


def test_materialize_recovery_action_allows_bound_successor_readback() -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    old_work_unit_id = "ai_reviewer_record_gate_consumption"
    old_fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    successor_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    successor_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    supervisor_decision = {
        "decision": "materialize_recovery_action",
        "paper_autonomy_obligation": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": old_work_unit_id,
            "work_unit_fingerprint": old_fingerprint,
        },
    }
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "ai_reviewer",
                "successor_owner_action": {
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": successor_work_unit_id,
                    "work_unit_fingerprint": successor_fingerprint,
                },
            },
            "supervisor_decision": supervisor_decision,
        },
        "current_executable_owner_action": {
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": successor_work_unit_id,
            "work_unit_fingerprint": successor_fingerprint,
            "action_fingerprint": successor_fingerprint,
        },
        "current_work_unit": {
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": successor_work_unit_id,
            "work_unit_fingerprint": successor_fingerprint,
            "action_fingerprint": successor_fingerprint,
        },
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "status": "provider_admission_pending",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": successor_work_unit_id,
                "work_unit_fingerprint": successor_fingerprint,
                "action_fingerprint": successor_fingerprint,
                "provider_admission_pending": True,
                "provider_admission_requires_opl_runtime_result": False,
                "opl_transition_readback_source": (
                    "opl_domain_progress_transition_runtime_live_readback"
                ),
                "opl_domain_progress_transition_result": opl_transition_readback(
                    study_id,
                    action_fingerprint=successor_fingerprint,
                    work_unit_id=successor_work_unit_id,
                ),
            }
        ],
    }

    allowed = provider_admission_supervisor_gate(payload)

    assert allowed == {
        "blocked": False,
        "admission_allowed": True,
        "supervisor_decision": supervisor_decision,
    }


def test_projection_consumes_identity_bound_opl_supervisor_decision_readback() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    obligation_id = (
        f"paper-recovery::{study_id}::run_quality_repair_batch::{work_unit_id}::{fingerprint}"
    )
    current_identity = {
        "stage_run_id": "stage-run-dm003",
        "route_identity_key": "provider-admission::dm003::medical-prose",
        "attempt_idempotency_key": "provider-admission::dm003::medical-prose",
        "selected_dispatch_ref": "dispatch-ref:dm003",
        "stage_packet_ref": "stage-packet:dm003",
        "stage_packet_refs": ["stage-packet:dm003"],
        "provider_attempt_ref": "provider-attempt:dm003",
        "attempt_lease_ref": "lease:dm003",
        "workflow_ref": "workflow:dm003",
        "source_fingerprint": "source:dm003",
        "truth_epoch": "truth::current",
        "runtime_health_epoch": "runtime::current",
        "work_unit_fingerprint": fingerprint,
    }
    opl_readback = {
        "surface_kind": "opl_paper_autonomy_supervisor_decision_readback",
        "obligation_id": obligation_id,
        "decision_id": f"{obligation_id}|execute_current_owner_delta|stage-run-dm003",
        "decision_kind": "execute_current_owner_delta",
        "status": "decision_ready_for_identity_bound_transition",
        "domain_truth_owner": "med-autoscience",
        "substrate_owner": "one-person-lab",
        "current_identity": current_identity,
        "transition_ref": "transition:dm003",
        "provider_admission_identity_ref": "provider-admission:dm003",
        "current_owner_delta_ref": "owner-delta:dm003",
        "terminal_closeout_ref": None,
        "recovery_action_ref": None,
        "no_progress_or_inconsistency_ref": None,
        "human_gate_ref": None,
        "resume_token": None,
        "typed_blocker_ref": None,
        "owner_receipt_ref": None,
        "budget_or_missing_evidence_ref": None,
        "evidence_refs": ["provider-admission:dm003", "stage-run-dm003"],
        "observability_refs": ["trace:dm003"],
        "authority_boundary": {
            "read_model_can_execute": False,
            "observability_can_close_owner_answer": False,
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
            "provider_completion_is_domain_ready": False,
        },
    }
    paper_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": study_id,
        "current_authority": {
            "owner": "one-person-lab",
            "obligation": {
                "recovery_obligation_id": obligation_id,
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "supervisor_decision": {
            "decision": "opl_supervisor_decision_readback_required",
            "requires_opl_supervisor_decision_engine_readback": True,
        },
    }

    decision = supervisor_decision_for_projection(
        {
            "study_id": study_id,
            "current_work_unit": _executable_work_unit(
                study_id=study_id,
                owner="one-person-lab",
                fingerprint=fingerprint,
            ),
            "opl_paper_autonomy_supervisor_decision_readback": opl_readback,
        },
        paper_recovery_state=paper_recovery_state,
    )

    assert decision["surface_kind"] == "paper_progress_policy_result_projection"
    assert decision["decision"] == "execute_current_owner_delta"
    assert decision["decision_authority"] is False
    assert decision["opl_supervisor_decision_engine_readback_consumed"] is True
    assert decision["requires_opl_supervisor_decision_engine_readback"] is False
    assert decision["mas_can_run_supervisor_decision_engine"] is False
    assert decision["mas_can_store_recovery_obligation"] is False
    assert decision["identity_match"] is True
    assert decision["missing_evidence_refs"] == []
    assert decision["paper_autonomy_obligation"]["route_identity_key"] == (
        "provider-admission::dm003::medical-prose"
    )
    assert decision["paper_autonomy_obligation"]["attempt_idempotency_key"] == (
        "provider-admission::dm003::medical-prose"
    )

    gate = provider_admission_supervisor_gate(
        {"study_id": study_id},
        paper_recovery_state=paper_recovery_state | {"supervisor_decision": decision},
    )

    assert gate["blocked"] is False
    assert gate["admission_allowed"] is True


def test_stale_opl_supervisor_decision_readback_remains_readback_required() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    paper_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": study_id,
        "current_authority": {
            "owner": "one-person-lab",
            "obligation": {
                "recovery_obligation_id": (
                    "paper-recovery::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "run_quality_repair_batch::medical_prose_write_repair::"
                    "publication-blockers::0915410f804b3697"
                ),
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            },
        },
    }

    decision = supervisor_decision_for_projection(
        {
            "study_id": study_id,
            "opl_paper_autonomy_supervisor_decision_readback": {
                "surface_kind": "opl_paper_autonomy_supervisor_decision_readback",
                "obligation_id": "paper-recovery::stale",
                "decision_id": "stale-decision",
                "decision_kind": "execute_current_owner_delta",
                "status": "decision_ready_for_identity_bound_transition",
                "domain_truth_owner": "med-autoscience",
                "substrate_owner": "one-person-lab",
                "current_identity": {
                    "stage_run_id": "stage-run-stale",
                    "route_identity_key": "provider-admission::stale",
                    "attempt_idempotency_key": "provider-admission::stale",
                    "selected_dispatch_ref": "dispatch-ref:stale",
                    "stage_packet_ref": "stage-packet:stale",
                    "stage_packet_refs": ["stage-packet:stale"],
                    "provider_attempt_ref": "provider-attempt:stale",
                    "attempt_lease_ref": "lease:stale",
                    "workflow_ref": "workflow:stale",
                    "source_fingerprint": "source:stale",
                    "truth_epoch": "truth::stale",
                    "runtime_health_epoch": "runtime::stale",
                    "work_unit_fingerprint": "publication-blockers::stale",
                },
            },
        },
        paper_recovery_state=paper_recovery_state,
    )

    assert decision["decision"] == "opl_supervisor_decision_readback_required"
    assert decision["requires_opl_supervisor_decision_engine_readback"] is True
    assert decision["provider_admission_pending"] is False


def test_admission_pending_without_identity_bound_provider_admission_materializes_recovery_not_idle() -> None:
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(),
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "provider_admission_ref": "provider-admission:dm003:repair",
            }
        ],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_authority": {
                "owner": "write",
                "obligation": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
            },
            "next_safe_action": {"kind": "admit_provider_attempt"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "materialize_recovery_action"
    assert decision["next_safe_action"]["kind"] == "materialize_recovery_work_unit_or_receipt"
    assert decision["next_safe_action"]["recovery_kind"] == "opl_runtime_repair"
    assert decision["missing_evidence_refs"] == [
        "complete_paper_autonomy_obligation_identity",
        "opl_stage_run_readback",
    ]


def test_identity_bound_admission_pending_without_stage_run_readback_materializes_recovery() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    identity = f"provider-admission::003-dpcc::{fingerprint}"
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(),
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "provider_admission_ref": "provider-admission:dm003:repair",
                "stage_packet_ref": "stage-packet:dm003:repair",
                "route_identity_key": identity,
                "attempt_idempotency_key": identity,
            }
        ],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_authority": {
                "owner": "write",
                "obligation": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "next_safe_action": {"kind": "admit_provider_attempt"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "materialize_recovery_action"
    assert decision["next_safe_action"]["kind"] == "materialize_recovery_work_unit_or_receipt"
    assert decision["missing_evidence_refs"] == ["opl_stage_run_readback"]
    assert decision["paper_autonomy_obligation"]["route_identity_key"] == identity
    assert decision["paper_autonomy_obligation"]["attempt_idempotency_key"] == identity


def test_missing_opl_readback_returns_non_advancing_policy_requirement() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    identity = f"provider-admission::003-dpcc::{fingerprint}"
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(),
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "provider_admission_ref": "provider-admission:dm003:repair",
                "stage_packet_ref": "stage-packet:dm003:repair",
                "route_identity_key": identity,
                "attempt_idempotency_key": identity,
            }
        ],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_authority": {
                "owner": "write",
                "obligation": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "next_safe_action": {"kind": "admit_provider_attempt"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "materialize_recovery_action"
    assert decision["missing_evidence_refs"] == ["opl_stage_run_readback"]
    policy = decision["paper_progress_policy_result"]
    assert policy["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert policy["recommended_opl_transition_kind"] == "NonAdvancingApply"
    request = decision["opl_domain_progress_transition_request"]
    assert request == policy["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["recommended_transition_kind"] == "NonAdvancingApply"
    assert request["mas_can_create_opl_outbox_record"] is False
    assert request["mas_can_create_opl_event"] is False
    assert request["mas_can_create_opl_stage_run"] is False
    assert decision["non_advancing_apply_requirement"]["runtime_owner"] == "one-person-lab"
    assert decision["non_advancing_apply_requirement"]["mas_can_apply_non_advancing_transition"] is False
    assert decision["authority_boundary"]["can_run_supervisor_decision_engine"] is False
    assert decision["authority_boundary"]["can_apply_non_advancing_transition"] is False
    assert decision["authority_boundary"]["can_replay_obligation"] is False
    projection = decision["paper_progress_policy_result_projection"]
    assert projection["policy_recommendation_label"] == "materialize_recovery_action"
    assert projection["missing_evidence_refs"] == ["opl_stage_run_readback"]
    assert projection["mas_can_create_opl_command_event_or_outbox"] is False
    assert projection["mas_can_authorize_provider_admission"] is False


def test_typed_blocker_identity_uses_currentness_basis_when_top_level_work_unit_is_sparse() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "owner": "one-person-lab",
            "work_unit_fingerprint": fingerprint,
            "currentness_basis": {
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "explicit_publication_work_unit_id": "medical_prose_write_repair",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "idempotency_key": "idem::dm003::medical-prose-write-repair",
            },
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "runtime_recovery_retry_budget_exhausted",
                    "owner": "one-person-lab",
                    "owner_answer_shape": "typed_blocker_ref",
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {
                "blocker_type": "runtime_recovery_retry_budget_exhausted",
                "owner": "one-person-lab",
                "owner_answer_shape": "typed_blocker_ref",
            },
        },
        "owner_action_admission": {
            "allowed_actions": ["run_quality_repair_batch"],
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "stop_with_stable_typed_blocker"
    assert decision["identity_match"] is True
    obligation = decision["paper_autonomy_obligation"]
    assert obligation["action_type"] == "run_quality_repair_batch"
    assert obligation["work_unit_id"] == "medical_prose_write_repair"
    assert "unknown-action" not in obligation["paper_autonomy_obligation_id"]
    assert "unknown-work-unit" not in obligation["paper_autonomy_obligation_id"]



def _execute_decision_with_evidence(evidence_refs: list[str]) -> dict[str, object]:
    fingerprint = "publication-blockers::0915410f804b3697"
    obligation = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "stage_id": "publication_supervision",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "route_identity_key": "route::dm003::quality-repair",
        "attempt_idempotency_key": "attempt::dm003::quality-repair",
    }
    return {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "decision": "execute_current_owner_delta",
        "identity_match": True,
        "paper_autonomy_obligation": obligation,
        "evidence_refs": evidence_refs,
        "missing_evidence_refs": [],
    }


from tests.test_paper_autonomy_supervisor_cases.terminal_owner_boundary_cases import *  # noqa: F403,F401,E402
