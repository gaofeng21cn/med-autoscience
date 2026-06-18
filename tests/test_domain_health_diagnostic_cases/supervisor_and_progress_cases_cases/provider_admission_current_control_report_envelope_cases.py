from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from tests.provider_admission_current_control_helpers import (
    opl_transition_readback,
    provider_candidate_with_opl_readback,
)

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def _opl_transition_result(
    *,
    study_id: str,
    fingerprint: str,
    work_unit_id: str = "medical_prose_write_repair",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )


def _mas_transition_request(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
) -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "schema_version": 1,
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "recommended_transition_kind": "StartProviderAttempt",
        "aggregate_identity": {
            "aggregate_kind": "paper_progress_work_unit",
            "aggregate_id": f"{study_id}:{work_unit_id}:{fingerprint}",
            "study_id": study_id,
            "work_unit_id": work_unit_id,
        },
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "source_generation": fingerprint,
        "expected_version": fingerprint,
        "required_postcondition": {"kind": "provider_admission_enqueued_or_blocked"},
        "mas_can_create_opl_outbox_record": False,
    }


def _write_opl_transition_runtime_log(
    runtime_root: Path,
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    idempotency_key: str,
) -> None:
    workspace_root = runtime_root.parent.parent if runtime_root.name == "quests" else runtime_root.parent
    log_path = (
        workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    stage_run_identity = {
        "stage_run_id": f"stage-run:{study_id}:{work_unit_id}",
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "source_generation": "truth-event-current",
    }
    entries = [
        {
            "entry_kind": "command",
            "transaction_id": "dptx_dhd_direct_candidate_readback",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_dhd_direct_candidate_readback",
                "source_generation": "truth-event-current",
                "expected_version": "truth-event-current",
                "stage_run_identity": stage_run_identity,
            },
        },
        {
            "entry_kind": "event",
            "transaction_id": "dptx_dhd_direct_candidate_readback",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_dhd_direct_candidate_readback",
                "event_id": "dpte_dhd_direct_candidate_readback",
                "source_generation": "truth-event-current",
                "expected_version": "truth-event-current",
                "stage_run_identity": stage_run_identity,
                "outcome": {
                    "kind": "provider_admission_enqueued_or_blocked",
                    "stable_outcome": True,
                },
            },
        },
        {
            "entry_kind": "outbox_item",
            "transaction_id": "dptx_dhd_direct_candidate_readback",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "outbox_item_id": "dpto_dhd_direct_candidate_readback",
                "transition_event_id": "dpte_dhd_direct_candidate_readback",
                "outbox_kind": "start_provider_attempt",
                "stage_run_identity": stage_run_identity,
            },
        },
    ]
    log_path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )


def test_runtime_report_prefers_fresh_progress_envelope_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    result = report_aggregation._current_execution_envelopes(
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                },
            }
        ],
        suppressions=[],
        progress_currentness={
            study_id: {
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source_refs": [
                        "/workspace/studies/003/artifacts/controller/repair_execution_evidence/latest.json"
                    ],
                    "conflict_suppression_refs": [
                        "runtime_health:continue_supervising_runtime"
                    ],
                },
            }
        },
    )

    envelope = result[study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


def test_runtime_report_preserves_explicit_transition_request_projection_without_provider_admission() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    transition_request = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "provider_attempt_or_lease_required": False,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_domain_progress_transition_request": _mas_transition_request(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
        ),
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={},
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
        managed_study_opl_transition_request_candidates=[transition_request],
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_transition_request_candidates"] == [transition_request]
    assert result["current_execution_evidence"]["transition_request_candidates"] == [
        transition_request
    ]
    action = result["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert action["provider_admission_state"]["status"] == "none"
    assert action["provider_admission_state"]["candidate_count"] == 0


def test_runtime_report_managed_action_uses_running_current_work_unit_over_stale_handoff_blocker() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    active_stage_attempt_id = "sat_984679e67f111f547bea943e"
    active_workflow_id = "wf_5224528fda81acd998d7073c"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "runtime_health_snapshot": {
                    "attempt_state": "live",
                    "worker_liveness_state": {
                        "state": "live",
                        "active_run_id": f"opl-stage-attempt://{active_stage_attempt_id}",
                    },
                },
                "authority_snapshot": {
                    "blocking_reasons": ["opl_current_control_state.handoff_required"],
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[
            {
                "surface_kind": "mas_opl_runtime_owner_handoff",
                "study_id": study_id,
                "status": "handoff_required",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "typed_blocker": {"blocker_type": "opl_runtime_owner_handoff_required"},
            }
        ],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "running_provider_attempt",
                    "owner": "one-person-lab",
                    "state": {
                        "state_kind": "running_provider_attempt",
                        "provider_attempt_proof": {
                            "running_provider_attempt": True,
                            "active_stage_attempt_id": active_stage_attempt_id,
                            "active_run_id": f"opl-stage-attempt://{active_stage_attempt_id}",
                            "active_workflow_id": active_workflow_id,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "running_provider_attempt",
                    "owner": "one-person-lab",
                    "next_work_unit": active_stage_attempt_id,
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "noop"
    assert action["reason"] == "running_provider_attempt_observed"
    assert action["running_provider_attempt"] is True
    assert action["active_stage_attempt_id"] == active_stage_attempt_id
    assert action["active_workflow_id"] == active_workflow_id
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "running_provider_attempt"
    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    assert handoff["status"] == "superseded_by_current_work_unit"
    assert handoff["previous_status"] == "handoff_required"
    assert handoff["reason"] == "running_provider_attempt"
    assert handoff["refs_only_handoff_superseded"] is True


def test_runtime_report_preserves_user_gate_when_provider_admission_is_pending() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    gate = {
        "gate_kind": "developer_supervisor",
        "blocked": True,
        "reason": "developer_apply_safe_required",
        "requested_mode": "external_observe",
        "effective_mode": "external_observe",
        "required_mode": "developer_apply_safe",
        "safe_actions_enabled": False,
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "execution_gate": gate,
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
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "opl_domain_progress_transition_result": _opl_transition_result(
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            }
        ],
        managed_study_progress_currentness={
            study_id: {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert result["provider_admission_pending_count"] == 1
    assert result["will_start_llm"] is False
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_for_user"
    assert action["running_provider_attempt"] is False
    assert action["execution_gate"] == gate
    assert action["provider_admission_state"] == {
        "status": "pending_but_execution_gate_blocked",
        "candidate_count": 1,
        "running_provider_attempt": False,
        "execution_gate_reason": "developer_apply_safe_required",
    }


def test_runtime_report_consumes_progress_currentness_opl_live_readback_candidate() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": (
            "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
            "supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json"
        ),
        "next_executable_owner": "write",
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_transition_readback_source": "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_result": _opl_transition_result(
            study_id=study_id,
            fingerprint=fingerprint,
            work_unit_id=work_unit_id,
        ),
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "provider_admission_candidates": [candidate],
                "transition_request_candidates": [candidate],
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_transition_request_candidates"] == []
    assert result["provider_admission_pending_count"] == 1
    [admission] = result["managed_study_opl_provider_admission_candidates"]
    assert admission["study_id"] == study_id
    assert admission["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )
    assert admission["opl_domain_progress_transition_result"]["identity"][
        "aggregate_identity"
    ]["work_unit_id"] == work_unit_id
    action = result["managed_study_actions"][0]
    assert action["provider_admission_state"] == {
        "status": "pending",
        "candidate_count": 1,
        "running_provider_attempt": False,
    }
    assert action["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id


def test_runtime_report_uses_managed_action_runtime_health_for_recovery_state() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                    },
                    "state": {
                        "state_kind": "executable_owner_action",
                        "provider_admission_pending": True,
                        "opl_domain_progress_transition_request": _mas_transition_request(
                            study_id=study_id,
                            action_type="run_gate_clearing_batch",
                            work_unit_id="publication_gate_replay",
                            fingerprint=fingerprint,
                        ),
                    },
                },
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "admission_blocked"
    assert recovery["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    ]
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "admission_blocked"
    assert action["paper_recovery_state"]["next_safe_action"]["provider_admission_allowed"] is False


def test_runtime_report_consumes_transition_request_when_opl_readback_present(tmp_path) -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    candidate = provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=fingerprint,
    )

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[candidate],
        managed_study_progress_currentness={},
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    [admission] = result["managed_study_opl_provider_admission_candidates"]
    assert admission["study_id"] == candidate["study_id"]
    assert admission["work_unit_id"] == candidate["work_unit_id"]
    assert admission["status"] == "provider_admission_pending"
    assert admission["provider_admission_requires_opl_runtime_result"] is False
    assert (
        admission["opl_transition_readback_source"]
        == "opl_domain_progress_transition_runtime_live_readback"
    )
    assert result["managed_study_opl_transition_request_candidates"] == []


def test_runtime_report_keeps_direct_transition_request_pending_with_only_opl_log(tmp_path) -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    runtime_root = tmp_path / "runtime" / "quests"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    _write_opl_transition_runtime_log(
        runtime_root,
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        idempotency_key=idempotency_key,
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_domain_progress_transition_request": {
            **_mas_transition_request(
                study_id=study_id,
                action_type="run_quality_repair_batch",
                work_unit_id=work_unit_id,
                fingerprint=fingerprint,
            ),
            "idempotency_key": idempotency_key,
        },
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=runtime_root,
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "owner_receipt_recorded",
                "reason": "current_owner_receipt_recorded",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[candidate],
        managed_study_progress_currentness={},
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [request] = result["managed_study_opl_transition_request_candidates"]
    assert request["status"] == "transition_request_pending"
    assert request["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_transition_readback_source" not in request
    assert "opl_domain_progress_transition_result" not in request


def test_current_control_sync_consumes_transition_request_when_opl_readback_present(tmp_path) -> None:
    provider_admission_report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    candidate = provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=fingerprint,
    )
    report = {
        "managed_study_opl_transition_request_candidates": [candidate],
        "transition_request_pending_count": 1,
        "current_execution_evidence": {
            "transition_request_candidates": [candidate],
        },
        "managed_study_actions": [],
    }

    provider_admission_report.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [candidate],
            "transition_request_candidates": [candidate],
        },
    )

    assert report["provider_admission_pending_count"] == 1
    assert report["transition_request_pending_count"] == 0
    assert report["managed_study_opl_provider_admission_candidates"] == [candidate]
    assert report["managed_study_opl_transition_request_candidates"] == []
    assert report["current_execution_evidence"]["provider_admission_candidates"] == [candidate]
    assert report["current_execution_evidence"]["transition_request_candidates"] == []


def test_runtime_report_prefers_owner_receipt_currentness_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    owner_receipt_ref = (
        "/workspace/studies/003/artifacts/controller/quality_repair_batch/latest.json"
    )
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
        "current_authority": {
            "obligation": {
                "study_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_receipt_ref": owner_receipt_ref,
        },
        "owner_receipt_ref": owner_receipt_ref,
        "evidence_refs": [owner_receipt_ref],
        "supervisor_decision": {"decision": "stop_with_owner_receipt"},
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "next_work_unit": None,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "paper_recovery_state": recovery_state,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_receipt_recorded"
    assert action["reason"] == "current_owner_receipt_recorded"
    assert action["running_provider_attempt"] is False
    assert action["current_work_unit"]["status"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["phase"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["next_safe_action"]["kind"] == "consume_owner_receipt"


def test_runtime_report_consumes_terminal_owner_receipt_over_matching_transition_request() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    owner_receipt_ref = (
        "/workspace/studies/003/artifacts/controller/repair_execution_receipts/latest.json"
    )
    transition_request = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
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
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                    "required_output_contract": {
                        "owner_receipt_consumed": True,
                        "owner_receipt_ref": owner_receipt_ref,
                        "provider_completion_is_domain_completion": False,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "next_work_unit": None,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "current_executable_owner_action": None,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
        managed_study_opl_transition_request_candidates=[transition_request],
    )

    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_transition_request_candidates"] == []
    assert result["provider_admission_pending_count"] == 0
    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_receipt_recorded"
    assert action.get("current_executable_owner_action") is None
    assert action["current_work_unit"]["status"] == "owner_receipt_recorded"
