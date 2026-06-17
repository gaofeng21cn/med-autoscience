from __future__ import annotations

from med_autoscience.controllers.paper_autonomy_supervisor import (
    build_paper_autonomy_obligation,
    build_supervisor_decision,
)
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

    assert decision["surface_kind"] == "paper_autonomy_supervisor_decision"
    assert decision["projection_role"] == "mas_policy_adapter_decision_projection"
    assert decision["authority"] is False
    assert decision["source_of_truth_chain"] == [
        "DomainIntent",
        "OPL Command/Event/Outbox/StageRun",
        "MAS OwnerAnswer",
        "Derived Projection",
    ]
    assert decision["authority_boundary"]["adapter_kind"] == "mas_policy_adapter"
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


def test_terminal_closeout_phase_consumes_closeout() -> None:
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_work_unit": _executable_work_unit(),
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "terminal_closeout_ready",
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
            "evidence_refs": ["closeout:dm003"],
            "next_safe_action": {"kind": "consume_terminal_closeout"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "consume_terminal_closeout"
    assert decision["next_owner"] == "MedAutoScience"
    assert decision["next_safe_action"]["kind"] == "consume_or_reject_terminal_closeout"
    assert "closeout:dm003" in decision["evidence_refs"]


def test_human_gate_phase_consumes_opl_resume_token_without_mas_generation() -> None:
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_work_unit": _typed_blocker_work_unit(
            study_id="002-dm-china-us-mortality-attribution",
            owner="user",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            blocker_type="owner_decision_required",
        ),
        "human_gate_transport": {
            "human_gate_ref": "human-gate:dm002",
            "resume_token": "resume:dm002",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "human_gate",
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_authority": {
                "owner": "user",
                "obligation": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "owner": "user",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-fp",
                },
            },
            "next_safe_action": {"kind": "record_human_or_owner_gate"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "wait_for_owner_with_resume_token"
    assert decision["next_safe_action"]["kind"] == "consume_opl_human_gate_resume_token"
    assert decision["next_safe_action"]["resume_token"] == "resume:dm002"
    assert decision["next_safe_action"]["human_gate_ref"] == "human-gate:dm002"
    assert decision["next_safe_action"]["resume_token_owner"] == "one-person-lab"
    assert decision["next_safe_action"]["mas_can_generate_resume_token"] is False


def test_human_gate_phase_does_not_synthesize_resume_token() -> None:
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_work_unit": _typed_blocker_work_unit(
            study_id="002-dm-china-us-mortality-attribution",
            owner="user",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            blocker_type="owner_decision_required",
        ),
        "human_gate_transport": {
            "human_gate_ref": "human-gate:dm002",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "human_gate",
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_authority": {
                "owner": "user",
                "obligation": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "owner": "user",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-fp",
                },
            },
            "next_safe_action": {"kind": "record_human_or_owner_gate"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "wait_for_owner_with_resume_token"
    assert "resume_token" not in decision["next_safe_action"]
    assert decision["next_safe_action"]["resume_token_owner"] == "one-person-lab"
    assert decision["next_safe_action"]["mas_can_generate_resume_token"] is False


def test_stable_typed_blocker_stops_same_identity_redrive() -> None:
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_work_unit": _typed_blocker_work_unit(
            study_id="002-dm-china-us-mortality-attribution",
            owner="MedAutoScience",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            blocker_type="medical_paper_readiness_missing",
        ),
        "provider_admission_pending_count": 0,
        "action_queue": [],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "domain_blocked",
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_authority": {
                "owner": "MedAutoScience",
                "obligation": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "owner": "MedAutoScience",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-fp",
                },
            },
            "evidence_refs": ["typed-blocker:dm002"],
            "next_safe_action": {"kind": "resolve_typed_blocker"},
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "stop_with_stable_typed_blocker"
    assert decision["next_safe_action"]["kind"] == (
        "publish_stable_blocker_and_stop_same_identity_redrive"
    )
    assert "typed-blocker:dm002" in decision["evidence_refs"]
    assert "provider_admission_pending_count=0_is_not_terminal" in decision[
        "forbidden_interpretations"
    ]
    assert "action_queue=[]_is_not_terminal" in decision["forbidden_interpretations"]


def test_owner_callable_recovery_materializes_action_even_when_queue_empty() -> None:
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_work_unit": _typed_blocker_work_unit(
            study_id="002-dm-china-us-mortality-attribution",
            owner="MedAutoScience",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            blocker_type="medical_paper_readiness_missing",
        ),
        "provider_admission_pending_count": 0,
        "action_queue": [],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_authority": {
                "owner": "MedAutoScience",
                "obligation": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "owner": "MedAutoScience",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-fp",
                },
            },
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
                "owner_callable": {
                    "callable_surface": (
                        "medical_paper_readiness.complete_medical_paper_readiness_surface"
                    )
                },
            },
        },
    }

    decision = build_supervisor_decision(payload)

    assert decision["decision"] == "materialize_recovery_action"
    assert decision["next_safe_action"]["recovery_kind"] == "mas_control_plane_repair"
    assert "provider_admission_pending_count=0_is_not_terminal" in decision[
        "forbidden_interpretations"
    ]


def test_obligation_shape_is_identity_bound() -> None:
    obligation = build_paper_autonomy_obligation(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                fingerprint="sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
            ),
        },
        paper_recovery_state={
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_authority": {
                "owner": "publication_gate",
                "obligation": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                    "currentness_basis": {
                        "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                        "idempotency_key": "idem-dm003",
                    },
                },
            },
        },
    )

    assert obligation["surface_kind"] == "paper_autonomy_obligation"
    assert obligation["paper_autonomy_obligation_id"].startswith(
        "paper-autonomy::003-dpcc-primary-care-phenotype-treatment-gap::"
    )
    assert obligation["route_identity_key"].startswith(
        "003-dpcc-primary-care-phenotype-treatment-gap:run_gate_clearing_batch:"
    )
    assert obligation["attempt_idempotency_key"] == "idem-dm003"
