from __future__ import annotations

import importlib

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    append_jsonl as _append_jsonl,
    make_profile,
    opl_transition_readback,
    opl_transition_replay_audit_readback,
    write_json as _write_json,
)

def test_study_progress_opl_current_control_state_handoff_consumes_live_transition_log_readback(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    replay = opl_transition_replay_audit_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    command_id = f"opl-domain-progress-command::{study_id}::{fingerprint}"
    command_event_log = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )
    _append_jsonl(
        command_event_log,
        [
            {
                "surface_kind": "opl_domain_progress_transition_log_entry",
                "runtime_id": "opl_domain_progress_transition_runtime",
                "transaction_id": replay["transaction_id"],
                "idempotency_key": route_key,
                "entry_kind": "command",
                "sequence_in_transaction": 0,
                "payload": {"command_id": command_id, "stage_run_identity": replay["stage_run_identity_readback"]["command_stage_run_identity"]},
            },
            {
                "surface_kind": "opl_domain_progress_transition_log_entry",
                "runtime_id": "opl_domain_progress_transition_runtime",
                "transaction_id": replay["transaction_id"],
                "idempotency_key": route_key,
                "entry_kind": "event",
                "sequence_in_transaction": 1,
                "payload": {
                    "event_id": replay["event_id"],
                    "transition_kind": "StartProviderAttempt",
                    "outcome": {"kind": "provider_admission_enqueued_or_blocked", "stable_outcome": True},
                    "aggregate_identity": replay["aggregate_identity"],
                    "stage_run_identity": replay["stage_run_identity_readback"]["event_stage_run_identity"],
                    "source_generation": replay["source_generation"],
                    "expected_version": replay["expected_version"],
                },
            },
            {
                "surface_kind": "opl_domain_progress_transition_log_entry",
                "runtime_id": "opl_domain_progress_transition_runtime",
                "transaction_id": replay["transaction_id"],
                "idempotency_key": route_key,
                "entry_kind": "outbox_item",
                "sequence_in_transaction": 2,
                "payload": {
                    "outbox_item_id": replay["outbox_item_id"],
                    "transition_event_id": replay["event_id"],
                    "outbox_kind": "start_provider_attempt",
                    "aggregate_identity": replay["aggregate_identity"],
                    "stage_run_identity": replay["stage_run_identity_readback"]["outbox_stage_run_identity"],
                    "idempotency_key": route_key,
                },
            },
        ],
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-20T16:36:14+00:00",
            "transition_request_pending_count": 1,
            "provider_admission_pending_count": 0,
            "action_queue": [
                {
                    "status": "transition_request_pending",
                    "reason": "await_opl_transition_readback",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "request_opl_stage_attempt",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "transition_request_pending",
                    "transition_request_pending_count": 1,
                    "provider_admission_pending_count": 0,
                    "action_queue": [
                        {
                            "status": "transition_request_pending",
                            "reason": "await_opl_transition_readback",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "request_opl_stage_attempt",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": route_key,
                            "attempt_idempotency_key": route_key,
                            "idempotency_key": route_key,
                        }
                    ],
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert projection["provider_admission_candidates"][0][
        "opl_domain_progress_transition_runtime_live_readback"
    ]["identity"]["latest_event_id"] == replay["event_id"]
    assert projection["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert projection["blocked_reason"] is None


def test_study_progress_opl_current_control_state_handoff_consumes_provider_admission_with_matching_terminal_closeout(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::abc"
    route_key = "paper-policy-request:abc"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id="sat-terminal",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-17T23:22:40+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "provider_admission_identity": {
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "blocked",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "sat-terminal.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-17T23:13:46Z",
            "study_id": "001-risk",
            "stage_id": "stage_outcome/opl-handoff",
            "stage_attempt_id": "sat-terminal",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
            "status": "closed_with_domain_owner_refs",
            "owner_receipt_ref": "studies/001-risk/artifacts/controller/repair_execution_receipts/latest.json",
            "paper_stage_log": {
                "stage_name": "run_quality_repair_batch",
                "problem_summary": "The owner callable produced a repair receipt.",
                "stage_goal": "Produce owner-authorized repair evidence.",
                "stage_work_done": ["Verified the current repair surface."],
                "paper_work_done": ["Verified the current repair surface."],
                "changed_stage_surfaces": [
                    "studies/001-risk/artifacts/controller/repair_execution_receipts/latest.json"
                ],
                "changed_paper_surfaces": [
                    "studies/001-risk/paper/draft.md"
                ],
                "progress_delta_classification": "deliverable_progress",
                "outcome": "owner_receipt_recorded",
                "remaining_blockers": [],
            },
            "closeout_refs": [
                "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapter_receipt/sat-terminal.closeout.json"
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["provider_admission_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    assert projection["provider_admission_terminal_closeout_consumed"]["stage_attempt_id"] == "sat-terminal"
    assert projection["provider_admission_terminal_closeout_consumed"]["work_unit_id"] == work_unit_id
    assert projection["provider_admission_terminal_closeout_consumed"]["work_unit_fingerprint"] == (
        fingerprint
    )
    assert projection["latest_terminal_stage_log"]["owner_receipt_ref"] == (
        "studies/001-risk/artifacts/controller/repair_execution_receipts/latest.json"
    )


def test_study_progress_opl_current_control_state_handoff_preserves_runtime_backed_admission_when_closeout_identity_is_not_bound(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    fingerprint = "publication-blockers::abc"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = f"paper-policy-request:{fingerprint}"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-18T04:00:00+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": idempotency_key,
                    "attempt_idempotency_key": idempotency_key,
                    "provider_admission_schema_source": "transition_request_pending_task",
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                    "provider_admission_identity": {
                        "status": "provider_admission_pending",
                        "study_id": study_id,
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "route_identity_key": idempotency_key,
                        "attempt_idempotency_key": idempotency_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [
                        {
                            "status": "provider_admission_pending",
                            "study_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": idempotency_key,
                            "attempt_idempotency_key": idempotency_key,
                            "provider_admission_schema_source": "transition_request_pending_task",
                            "opl_domain_progress_transition_runtime_live_readback": readback,
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "stale-terminal.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-17T23:13:46Z",
            "study_id": study_id,
            "stage_id": "stage_outcome/opl-handoff",
            "stage_attempt_id": "stale-terminal",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "status": "closed_with_domain_owner_refs",
            "owner_receipt_ref": f"studies/{study_id}/artifacts/controller/old_receipt.json",
            "paper_stage_log": {
                "stage_name": "run_quality_repair_batch",
                "problem_summary": "A stale closeout belongs to an older provider attempt.",
                "stage_goal": "Produce owner-authorized repair evidence.",
                "stage_work_done": ["Recorded an older repair receipt."],
                "paper_work_done": ["Recorded an older repair receipt."],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/controller/old_receipt.json"
                ],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "platform_repair",
                "outcome": "owner_receipt_recorded",
                "remaining_blockers": [],
            },
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert len(projection["provider_admission_candidates"]) == 1
    assert "provider_admission_terminal_closeout_consumed" not in projection
    assert projection["provider_admission_candidates"][0]["attempt_idempotency_key"] == idempotency_key


def test_study_progress_opl_current_control_state_handoff_consumes_global_terminal_readback_action_queue(
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"
    route_key = "paper-policy-request:4ad0ec722ffd3cb666e615ac"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    action = {
        "status": "queued",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "gate_clearing_batch",
        "next_executable_owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "dispatch_ref": f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet",
        "checkpoint_refs": [f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"],
        "handoff_packet": {
            "opl_domain_progress_transition_runtime_live_readback": readback,
        },
    }
    terminal_readback = {
        "surface_kind": "opl_current_control_provider_admission_terminal_consumed_readback",
        "status": "provider_admission_terminal_consumed",
        "reason": "terminal_stage_attempt_consumed_same_transition_identity",
        "terminal_stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
        "terminal_stage_attempt_status": "completed",
        "terminal_provider_status": "completed",
        "closeout_refs": [
            "runtime/artifacts/opl_family_domain_handler/dispatch_receipts/1b3ff330ad0e62476a78.json",
            f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet",
            "temporal://attempt/sat_d00368adb115dbeba62a7e41",
        ],
        "currentness_identity": {
            "task_id": "frt_f3103ddf54ddde2fd07ca747",
            "stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
            "study_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
    }
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-21T07:15:22+00:00",
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_candidates": [],
            "latest_provider_admission_terminal_consumed_readback": terminal_readback,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_candidates": [],
                    "action_queue": [action],
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    assert projection["transition_request_pending_count"] == 0
    assert projection["transition_request_candidates"] == []
    assert projection["action_queue"] == []
    assert projection["consumed_action_queue"][0]["work_unit_id"] == work_unit_id
    assert (
        projection["provider_admission_terminal_closeout_consumed"]["stage_attempt_id"]
        == "sat_d00368adb115dbeba62a7e41"
    )
    assert projection["provider_admission_terminal_closeout_consumed"]["work_unit_id"] == work_unit_id
    assert projection["provider_admission_terminal_closeout_consumed"]["work_unit_fingerprint"] == fingerprint


def test_study_progress_opl_current_control_state_handoff_preserves_replayed_provider_admission_over_old_typed_blocker_closeout(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-20T04:07:15+00:00",
            "current_control_refresh_source": "opl_transition_runtime_readback_provider_admission",
            "provider_admission_pending_count": 1,
            "transition_request_pending_count": 0,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": idempotency_key,
                    "attempt_idempotency_key": idempotency_key,
                    "provider_admission_pending": True,
                    "provider_admission_schema_source": "existing_terminal_queue_readback",
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                    "provider_admission_identity": {
                        "status": "provider_admission_pending",
                        "study_id": study_id,
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "route_identity_key": idempotency_key,
                        "attempt_idempotency_key": idempotency_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [
                        {
                            "status": "provider_admission_pending",
                            "study_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": idempotency_key,
                            "attempt_idempotency_key": idempotency_key,
                            "provider_admission_pending": True,
                            "provider_admission_schema_source": "existing_terminal_queue_readback",
                            "opl_domain_progress_transition_runtime_live_readback": readback,
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "sat_08da46bea43329723d2fbbea.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-20T03:30:55Z",
            "study_id": study_id,
            "stage_id": "stage_outcome/opl-handoff",
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "status": "blocked",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "route_outcome": "typed_blocker",
            "typed_blocker_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "owner_callable_adapter_receipt/sat_08da46bea43329723d2fbbea.closeout.json"
            ),
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "reason": "no_selected_dispatch_for_authorized_stage_packet",
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "source_ref": (
                    f"studies/{study_id}/artifacts/supervision/consumer/"
                    "owner_callable_adapter_receipt/sat_08da46bea43329723d2fbbea.closeout.json"
                ),
                "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                "next_owner": "one-person-lab",
                "write_permitted": False,
            },
            "paper_stage_log": {
                "stage_name": "run_quality_repair_batch",
                "problem_summary": "An older MAS selector closeout failed before OPL current-control replay.",
                "stage_goal": "Produce owner-authorized repair evidence.",
                "stage_work_done": ["Recorded a selector typed blocker."],
                "paper_work_done": [],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    "sat_08da46bea43329723d2fbbea.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "typed_blocker",
                "outcome": "typed_blocker",
                "remaining_blockers": ["no_selected_dispatch_for_authorized_stage_packet"],
            },
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert len(projection["provider_admission_candidates"]) == 1
    assert "provider_admission_terminal_closeout_consumed" not in projection
    candidate = projection["provider_admission_candidates"][0]
    assert candidate["attempt_idempotency_key"] == idempotency_key
    assert candidate["opl_domain_progress_transition_runtime_live_readback"]["runtime_readback_status"] == (
        "complete_transaction"
    )
