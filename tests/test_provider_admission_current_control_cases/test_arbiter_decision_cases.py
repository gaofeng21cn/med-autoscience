from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import provider_candidate as _provider_candidate


def test_provider_admission_current_control_terminal_closeout_precedes_stale_live_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:10:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-terminal-wins",
                "active_run_id": "run-terminal-wins",
                "active_workflow_id": "wf-terminal-wins",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "active_workflow_id": "wf-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                },
                "owner_callable_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-terminal-wins.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "terminal_closeout_precedes_live_projection": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "terminal_closeout_precedes_live_projection"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"
    assert decision["active_stage_attempt_id"] == "sat-terminal-wins"


def test_provider_admission_current_control_records_running_identity_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-running",
                "active_run_id": "run-running",
                "active_workflow_id": "wf-running",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-running",
                    "active_run_id": "run-running",
                    "active_workflow_id": "wf-running",
                    "dispatch_path": candidate["dispatch_path"],
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "running_identity_observed"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["active_stage_attempt_id"] == "sat-running"


def test_provider_admission_current_control_records_accepted_closeout_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "owner_callable_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-closeout.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"


def test_previous_global_terminal_consumed_readback_suppresses_same_identity_pending(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    action_fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    route_key = "paper-policy-request:4ad0ec722ffd3cb666e615ac"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "dispatch_ref": (
            f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
        ),
        "stage_packet_ref": (
            f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
        ),
        "next_executable_owner": "gate_clearing_batch",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
            "runtime_health_epoch": "runtime-health-event-007038-0d27a5d519cf24fc",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }
    previous_latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    previous_latest_path.parent.mkdir(parents=True, exist_ok=True)
    previous_latest_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state_handoff",
                "schema_version": 1,
                "provider_admission_pending_count": 0,
                "transition_request_pending_count": 0,
                "provider_admission_candidates": [],
                "transition_request_candidates": [],
                "latest_provider_admission_terminal_consumed_readback": {
                    "surface_kind": "opl_current_control_provider_admission_terminal_consumed_readback",
                    "status": "provider_admission_terminal_consumed",
                    "reason": "terminal_stage_attempt_consumed_same_transition_identity",
                    "terminal_stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
                    "terminal_stage_attempt_status": "completed",
                    "terminal_provider_status": "completed",
                    "currentness_identity": {
                        "task_id": "frt_f3103ddf54ddde2fd07ca747",
                        "stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
                        "study_id": study_id,
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                    },
                    "provider_completion_is_domain_completion": False,
                    "provider_completion_is_domain_ready": False,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-21T07:28:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "provider_admission_candidates": [candidate],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "provider_admission_terminal_consumed": 1,
    }
    assert (
        result["latest_provider_admission_terminal_consumed_readback"][
            "terminal_stage_attempt_id"
        ]
        == "sat_d00368adb115dbeba62a7e41"
    )
    [decision] = result["stage_route_arbiter_decisions"]
    assert decision["decision"] == "provider_admission_terminal_consumed"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "provider_admission_terminal_consumed"
    assert decision["active_stage_attempt_id"] == "sat_d00368adb115dbeba62a7e41"
