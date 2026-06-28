from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from ..provider_admission_current_control_cases import _currentness_basis

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_materialized_current_control_clears_candidate_after_accepted_typed_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = "sha256:current-ai-reviewer"
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "mas_opl_runtime_owner_handoff.provider_admission_identity",
        "execution_ref": str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-ai-reviewer",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-10T21:45:15+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "default_executor_execution_receipt_consumption": {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "accepted_typed_closeout",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "current_attempt_state": "accepted_typed_closeout",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "dispatch_path": str(dispatch_path),
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["studies"][0]["study_id"] == study_id
    assert result["studies"][0]["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
    assert result["current_execution_envelopes"][study_id]["source"] == (
        "progress_currentness.current_executable_owner_action"
    )


def test_terminal_closeout_suppresses_stale_running_but_preserves_next_handoff(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    old_work_unit_id = "medical_prose_write_repair"
    old_fingerprint = "publication-blockers::0915410f804b3697"
    next_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    next_fingerprint = "sha256:fc2032327815ef9ab106e4ca972923ae2f18b3e3da019cf257298e2b3e3bc08a"
    old_dispatch_path = str(
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    next_dispatch_path = str(
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": next_work_unit_id,
        "work_unit_fingerprint": next_fingerprint,
        "action_fingerprint": next_fingerprint,
        "dispatch_path": next_dispatch_path,
        "stage_packet_ref": next_dispatch_path,
        "stage_packet_refs": [next_dispatch_path],
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=next_work_unit_id,
            fingerprint=next_fingerprint,
            source_eval_id="publication-eval::003::ai-reviewer-followup",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T09:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat_3c7846886384a7166c4dd7a6",
                "active_workflow_id": "wf_724c6f21d7d4a3d32d0e3e5d",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": old_work_unit_id,
                "work_unit_fingerprint": old_fingerprint,
                "action_fingerprint": old_fingerprint,
                "dispatch_path": old_dispatch_path,
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "execution_status": "executed",
                        "stage_attempt_id": "sat_3c7846886384a7166c4dd7a6",
                        "active_workflow_id": "wf_724c6f21d7d4a3d32d0e3e5d",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": old_work_unit_id,
                        "work_unit_fingerprint": old_fingerprint,
                        "action_fingerprint": old_fingerprint,
                        "dispatch_path": old_dispatch_path,
                        "owner_receipt_ref": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "controller/repair_execution_receipts/latest.json"
                        ),
                        "owner_route_currentness_basis": _currentness_basis(
                            work_unit_id=old_work_unit_id,
                            fingerprint=old_fingerprint,
                            source_eval_id="publication-eval::003::write-repair",
                        ),
                        "closeout_refs": [
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/repair_execution_evidence/latest.json"
                        ],
                    }
                ],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "next_owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": next_work_unit_id,
                    "work_unit_fingerprint": next_fingerprint,
                    "action_fingerprint": next_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": next_work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["work_unit_id"] == next_work_unit_id
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["quest_status"] == "transition_request_pending"
    assert study["running_provider_attempt"] is False
    assert study["active_stage_attempt_id"] is None
    assert study["terminal_closeout_precedence_evidence"]["stage_attempt_id"] == (
        "sat_3c7846886384a7166c4dd7a6"
    )
    assert study["action_queue"][0]["work_unit_id"] == next_work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }

def test_materialized_current_control_clears_candidate_after_executed_typed_blocker_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
    )
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "mas_opl_runtime_owner_handoff.provider_admission_identity",
        "execution_ref": str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "consumer_default_executor_dispatch",
        "next_executable_owner": "gate_clearing_batch",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-gate-replay",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-10T23:36:08+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "default_executor_execution_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "default_executor_execution",
                    "receipt_ref": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_efe4fb48feb300595e5aade7.closeout.json"
                    ),
                    "stage_attempt_id": "sat_efe4fb48feb300595e5aade7",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "outcome": "typed_blocker",
                    "typed_blocker_reason": "publication_gate_replay_blocked",
                    "typed_blocker_ref": (
                        "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/reports/publishability_gate/2026-06-10T233125Z.json"
                    ),
                    "owner_receipt_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/controller/gate_clearing_batch/latest.json"
                    ),
                    "owner_route_currentness_basis": _currentness_basis(
                        work_unit_id=work_unit_id,
                        fingerprint=fingerprint,
                        source_eval_id="publication-eval::003::current-gate-replay",
                    ),
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "dispatch_path": str(dispatch_path),
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "mas_provider_admission_identity",
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "mas_provider_admission_identity",
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["action_type"] == "run_gate_clearing_batch"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "gate_clearing_batch"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "publication_gate_replay_blocked"
    study = result["studies"][0]
    assert study["current_work_unit"]["status"] == "typed_blocker"
    assert study["current_work_unit"]["state"]["typed_blocker"]["work_unit_id"] == work_unit_id


def test_materialized_current_control_keeps_progress_first_live_attempt_over_old_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
    )
    live_stage_attempt_id = "sat_a48379bbe63bcd5e86b5d6db"
    live_workflow_id = "wf_2b1e0398943b4922112354f8"

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[],
        generated_at="2026-06-11T20:42:12+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "quest_status": "active",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "work_unit_id": work_unit_id,
                    "currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
                        ),
                    },
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "accepted_closeout_consumed_pending",
                        "strict_running_proof": True,
                        "provider_attempt_proof": {
                            "running_provider_attempt": True,
                            "active_run_id": f"opl-stage-attempt://{live_stage_attempt_id}",
                            "active_stage_attempt_id": live_stage_attempt_id,
                            "active_workflow_id": live_workflow_id,
                            "runtime_health": {
                                "health_status": "running",
                                "runtime_liveness_status": "live",
                            },
                        },
                    },
                },
                "progress_first_monitoring_summary": {
                    "running_provider_attempt": True,
                    "active_run_id": f"opl-stage-attempt://{live_stage_attempt_id}",
                    "active_stage_attempt_id": live_stage_attempt_id,
                    "active_workflow_id": live_workflow_id,
                    "next_owner": "med-autoscience",
                    "next_work_unit": work_unit_id,
                    "worker_liveness": {
                        "health_status": "live",
                        "runtime_liveness_status": "live",
                    },
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "executed",
                        "stage_closeout_status": "executed",
                        "execution_status": "executed",
                        "outcome": "executed",
                        "stage_attempt_id": "sat_cb5cc1d261fee2c397af8b05",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "typed_blocker_reason": "executed",
                        "typed_blocker_ref": "old-closeout.json",
                        "typed_blocker": {
                            "blocker_id": "executed",
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "next_work_unit": None,
                    "typed_blocker": {"blocker_type": "executed", "owner": "one-person-lab"},
                    "parked_state": None,
                    "source": "accepted_closeout_consumed_pending",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    study = result["studies"][0]
    assert study["running_provider_attempt"] is True
    assert study["active_stage_attempt_id"] == live_stage_attempt_id
    assert study["active_workflow_id"] == live_workflow_id
    assert study["current_work_unit"]["status"] == "running_provider_attempt"
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
