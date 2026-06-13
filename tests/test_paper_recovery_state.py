from __future__ import annotations

import importlib


def _module():
    return importlib.import_module("med_autoscience.controllers.paper_recovery_state")


def _typed_blocker_work_unit(
    *,
    study_id: str = "002-dm-cvd-mortality-risk",
    owner: str = "one-person-lab",
    action_type: str = "run_gate_clearing_batch",
    work_unit_id: str = "publication_gate_replay",
    blocker_type: str = "stage_packet_not_current_selected_dispatch",
) -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": blocker_type,
                "owner": owner,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
            },
        },
    }


def _executable_work_unit(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    owner: str = "write",
    action_type: str = "run_quality_repair_batch",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
) -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }


def test_typed_blocker_owns_recovery_even_when_residual_action_exists() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_work_unit": _typed_blocker_work_unit(),
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"action_type": "run_quality_repair_batch"}],
        }
    )

    assert state["surface_kind"] == "paper_recovery_state"
    assert state["phase"] == "domain_blocked"
    assert state["recovery_obligation_id"] == (
        "paper-recovery::002-dm-cvd-mortality-risk::run_gate_clearing_batch::"
        "publication_gate_replay::stage_packet_not_current_selected_dispatch"
    )
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["suppressed_surfaces"] == ["current_executable_owner_action", "provider_admission_candidates"]


def test_observe_only_provider_admission_is_classified_as_blocked_with_reason() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        },
        diagnostic_report={
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 1,
        },
    )

    assert state["phase"] == "admission_blocked"
    assert state["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "dhd_report_observe_only",
        }
    ]
    assert state["next_safe_action"]["kind"] == "run_admission_apply_or_report_operator_gate"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_projection_contradiction_fails_closed() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["current_authority"]["owner"] == "MedAutoScience"
    assert state["next_safe_action"]["kind"] == "repair_projection_before_admission"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_running_attempt_requires_strong_identity_binding() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-unbound",
                "active_stage_attempt_id": "sat-unbound",
                "active_workflow_id": "wf-unbound",
            },
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["conditions"][0]["condition"] == "running_attempt_missing_obligation_identity"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_terminal_closeout_matching_obligation_waits_for_owner_consumption() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "terminal_closeout_precedence_evidence": {
                "status": "completed",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "stage_attempt_id": "sat-complete",
                "closeout_ref": "artifacts/supervision/consumer/default_executor_execution/sat-complete.closeout.json",
            },
        }
    )

    assert state["phase"] == "terminal_closeout_ready"
    assert state["next_safe_action"]["kind"] == "consume_terminal_closeout"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [
        "artifacts/supervision/consumer/default_executor_execution/sat-complete.closeout.json"
    ]


def test_foreground_file_delta_without_owner_receipt_is_unadopted() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "manual_foreground_delta": {
                "changed": True,
                "paths": ["manuscript/main.tex"],
                "owner_receipt_ref": None,
            },
        }
    )

    assert state["phase"] == "manual_foreground_unadopted"
    assert state["next_safe_action"]["kind"] == "adopt_manual_delta_through_mas_owner_receipt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_runtime_report_marks_observe_only_provider_admission_as_blocked() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    result = report_aggregation.build_runtime_report(
        runtime_root=__import__("pathlib").Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[
            {
                "study_id": study_id,
                "status": "provider_admission_pending",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            }
        ],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": _executable_work_unit(
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["provider_admission_pending_count"] == 1
    assert result["will_start_llm"] is False
    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    assert result["paper_recovery_states"][study_id]["phase"] == "admission_blocked"
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "admission_blocked"
    assert action["provider_admission_state"] == {
        "status": "blocked_by_paper_recovery_state",
        "candidate_count": 1,
        "running_provider_attempt": False,
        "paper_recovery_phase": "admission_blocked",
        "paper_recovery_reason": "provider_admission_pending_without_startable_dispatch",
    }
