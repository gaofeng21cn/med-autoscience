from __future__ import annotations

import importlib
import json

from tests.study_runtime_test_helpers import make_profile
from tests.provider_admission_current_control_helpers import (
    opl_transition_readback,
    opl_transition_replay_audit_readback,
)
from tests.mcp_opl_current_control_state_handoff_cases.rendering import (
    test_mcp_compacts_and_renders_latest_terminal_stage_log,
    test_mcp_compacts_and_renders_opl_current_control_state_handoff_dashboard,
    test_mcp_compacts_string_why_not_applied_as_single_reason,
)


def _write_json(path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path, payloads: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(payload, ensure_ascii=False) + "\n" for payload in payloads),
        encoding="utf-8",
    )


def test_study_progress_opl_current_control_state_handoff_projection_reads_developer_supervisor_mode(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-04T06:00:00+00:00",
            "developer_supervisor_mode": {
                "mode": "developer_apply_safe",
                "mode_label": "Developer Supervisor Mode",
                "scheduler_owner": "external_scheduler",
                "codex_app_heartbeat_required": False,
                "safe_actions_enabled": True,
                "repo_level_repair_authority": True,
                "github_user_gate": {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None},
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "blocked",
                    "active_run_id": "run-001",
                    "external_supervisor_required": True,
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["mode"] == "developer_apply_safe"
    assert projection["mode_label"] == "Developer Supervisor Mode"
    assert projection["scheduler_owner"] == "external_scheduler"
    assert projection["codex_app_heartbeat_required"] is False
    assert projection["safe_actions_enabled"] is True
    assert projection["repo_level_repair_authority"] is True
    assert projection["github_user_gate"] == {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None}


def test_study_progress_opl_current_control_state_handoff_projection_preserves_string_why_not_applied(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-09T08:54:24+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "why_not_applied": "repeat_suppressed",
                    "blocked_reason": "repeat_suppressed",
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["why_not_applied"] == ["repeat_suppressed"]


def test_study_progress_opl_current_control_state_handoff_rejects_incomplete_top_level_provider_admission_candidate(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-17T02:51:08+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": "001-risk",
                    "quest_id": "001-risk",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::abc",
                    "provider_admission_identity": {
                        "stage_packet_ref": "studies/001-risk/artifacts/packet.json",
                        "route_identity_key": "paper-policy-request:abc",
                    },
                    "domain_progress_transition_runtime": {
                        "transition_event": {"event_id": "evt-001"},
                        "transactional_outbox_item": {"outbox_item_id": "outbox-001"},
                        "identity": {"stage_run_identity": {"stage_run_id": "sr-001"}},
                    },
                }
            ],
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "blocked",
                    "blocked_reason": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
                    "typed_blocker": {
                        "blocker_type": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
                    },
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "publication-blockers::abc",
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["provider_admission_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    assert projection["blocked_reason"] == "domain_owner_action_dispatch_apply_selected_zero_dispatch"
    assert projection["typed_blocker"]["blocker_type"] == (
        "domain_owner_action_dispatch_apply_selected_zero_dispatch"
    )


def test_study_progress_opl_current_control_state_handoff_merges_complete_top_level_provider_admission_readback(tmp_path) -> None:
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
        stage_run_id="sr-001",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-17T02:51:08+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "provider_admission_identity": {
                        "stage_packet_ref": f"studies/{study_id}/artifacts/packet.json",
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
                    "blocked_reason": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
                    "typed_blocker": {
                        "blocker_type": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
                    },
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert projection["provider_admission_candidates"][0][
        "opl_domain_progress_transition_runtime_live_readback"
    ]["runtime_readback_status"] == "complete_transaction"
    assert projection["action_type"] == "run_quality_repair_batch"
    assert projection["work_unit_id"] == work_unit_id
    assert projection["blocked_reason"] is None
    assert "typed_blocker" not in projection


def test_study_progress_opl_current_control_state_handoff_binds_root_readback_to_action_queue(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-20T17:45:32+00:00",
            "provider_admission_pending_count": 1,
            "transition_request_pending_count": 0,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "provider_admission_pending",
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "running_provider_attempt": False,
                    "provider_admission_identity": {
                        "study_id": study_id,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                        "request_idempotency_key": route_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                    "action_queue": [
                        {
                            "status": "queued",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "request_opl_stage_attempt",
                            "owner": "write",
                            "next_executable_owner": "write",
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

    assert projection["quest_status"] == "provider_admission_pending"
    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert len(projection["provider_admission_candidates"]) == 1
    candidate = projection["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["source"] == "opl_current_control_state_action_queue"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["route_identity_key"] == route_key
    assert candidate["attempt_idempotency_key"] == route_key
    assert candidate["opl_domain_progress_transition_runtime_live_readback"] == readback
    assert projection["blocked_reason"] is None


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
            "surface": "portable_owner_route_reconcile",
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
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "sat-terminal.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-17T23:13:46Z",
            "study_id": "001-risk",
            "stage_id": "domain_owner/default-executor-dispatch",
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
                "studies/001-risk/artifacts/supervision/consumer/default_executor_execution/sat-terminal.closeout.json"
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
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "stale-terminal.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-17T23:13:46Z",
            "study_id": study_id,
            "stage_id": "domain_owner/default-executor-dispatch",
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
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "sat_08da46bea43329723d2fbbea.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-20T03:30:55Z",
            "study_id": study_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "status": "blocked",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "route_outcome": "typed_blocker",
            "typed_blocker_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "default_executor_execution/sat_08da46bea43329723d2fbbea.closeout.json"
            ),
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "reason": "no_selected_dispatch_for_authorized_stage_packet",
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "source_ref": (
                    f"studies/{study_id}/artifacts/supervision/consumer/"
                    "default_executor_execution/sat_08da46bea43329723d2fbbea.closeout.json"
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
                    f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
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


def test_study_progress_opl_current_control_state_handoff_consumes_matching_opl_terminal_attempt_closeout(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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
    old_closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_08da46bea43329723d2fbbea.closeout.json"
    )
    _write_json(
        old_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-20T03:30:55Z",
            "study_id": study_id,
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "status": "blocked",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "typed_blocker": {
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            },
        },
    )

    def fake_terminal_closeout(**kwargs):
        assert kwargs["study_id"] == study_id
        assert kwargs["preferred_actions"][0]["attempt_idempotency_key"] == idempotency_key
        return {
            "surface_kind": "opl_terminal_provider_attempt_closeout",
            "source": "opl_family_runtime_attempt_inspect",
            "source_path": "opl://stage_attempts/sat_91d23a554175ea9288d903ad",
            "stage_attempt_id": "sat_91d23a554175ea9288d903ad",
            "status": "completed",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
            "closeout_receipt_status": "accepted_typed_closeout",
            "closeout_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                f"studies/{study_id}/artifacts/controller/quality_repair_batch/latest.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "route_impact": {
                "next_owner": "medautoscience",
                "domain_ready_verdict": "domain_gate_pending",
            },
        }

    monkeypatch.setattr(module, "terminal_provider_attempt_closeout_for_study", fake_terminal_closeout)

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 0
    assert projection["transition_request_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    consumed = projection["provider_admission_terminal_closeout_consumed"]
    assert consumed["stage_attempt_id"] == "sat_91d23a554175ea9288d903ad"
    assert consumed["attempt_idempotency_key"] == idempotency_key
    assert projection["latest_terminal_stage_log"]["closeout_receipt_status"] == "accepted_typed_closeout"
    assert projection["latest_terminal_stage_log"]["stage_attempt_id"] == "sat_91d23a554175ea9288d903ad"
    assert projection["latest_terminal_stage_log"]["route_impact"]["domain_ready_verdict"] == (
        "domain_gate_pending"
    )


def test_study_progress_opl_current_control_state_handoff_consumes_request_wrapper_terminal_closeout(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    candidate = {
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.provider_admission_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "next_executable_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "idempotency_key": idempotency_key,
        "provider_admission_pending": True,
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-20T20:39:39+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [candidate],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 1,
                    "provider_admission_candidates": [candidate],
                    "transition_request_pending_count": 0,
                    "transition_request_candidates": [],
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "request_opl_stage_attempt",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "state": {
                            "state_kind": "executable_owner_action",
                            "source": "opl_current_control_state.provider_admission_candidates",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                    "action_queue": [candidate],
                }
            ],
        },
    )

    def fake_terminal_closeout(**kwargs):
        assert kwargs["study_id"] == study_id
        assert kwargs["preferred_actions"][0]["attempt_idempotency_key"] == idempotency_key
        return {
            "surface_kind": "opl_terminal_provider_attempt_closeout",
            "source": "opl_family_runtime_attempt_inspect",
            "source_path": "opl://stage_attempts/sat_efdab57a49cb6d58f2a17eeb",
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "status": "completed",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "closeout_receipt_status": "accepted_typed_closeout",
            "closeout_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "next_forced_delta": {
                "owner_action": {
                    "next_owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": "ai_reviewer_recheck_after_medical_prose_write_repair",
                },
            },
            "route_impact": {
                "next_owner": "medautoscience",
                "domain_ready_verdict": "domain_gate_pending",
            },
        }

    monkeypatch.setattr(module, "terminal_provider_attempt_closeout_for_study", fake_terminal_closeout)

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert projection["provider_admission_candidates"][0]["attempt_idempotency_key"] == idempotency_key
    assert projection["transition_request_candidates"] == []
    assert "provider_admission_terminal_closeout_consumed" not in projection
    assert projection["current_work_unit"]["owner"] == "write"
    assert projection["current_work_unit"]["action_type"] == "request_opl_stage_attempt"
    assert projection["current_work_unit"]["work_unit_id"] == work_unit_id
    assert projection["current_execution_envelope"]["owner"] == "write"
    assert projection["current_execution_envelope"]["next_work_unit"] == work_unit_id


def test_study_progress_opl_current_control_state_handoff_consumes_request_wrapper_domain_owner_closeout(
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    stage_attempt_id = "sat_efdab57a49cb6d58f2a17eeb"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    candidate = {
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.provider_admission_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "next_executable_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "idempotency_key": idempotency_key,
        "provider_admission_pending": True,
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-20T20:39:39+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [candidate],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 1,
                    "provider_admission_candidates": [candidate],
                    "transition_request_pending_count": 0,
                    "transition_request_candidates": [],
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "request_opl_stage_attempt",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "state": {
                            "state_kind": "executable_owner_action",
                            "source": "opl_current_control_state.provider_admission_candidates",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                    "action_queue": [candidate],
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
        / "stage_attempt_closeouts"
        / f"{stage_attempt_id}.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-20T16:05:54Z",
            "study_id": study_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": stage_attempt_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "status": "closed_with_domain_owner_refs",
            "owner_receipt_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/706beb9a2db381422a12.json",
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "status": "available",
                "stage_name": "medical_prose_write_repair",
                "problem_summary": "The owner callable produced a medical-prose repair receipt.",
                "stage_goal": "Produce owner-authorized medical-prose repair evidence.",
                "stage_work_done": ["Recorded owner-authorized repair evidence."],
                "paper_work_done": ["Regenerated the canonical manuscript story surface."],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                ],
                "changed_paper_surfaces": [
                    f"studies/{study_id}/artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md",
                ],
                "progress_delta_classification": "deliverable_progress",
                "outcome": "closed_with_domain_owner_refs",
                "remaining_blockers": [],
                "evidence_refs": [
                    f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                ],
                "next_forced_delta": {
                    "owner_action": {
                        "next_owner": "ai_reviewer",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": "ai_reviewer_recheck_after_medical_prose_write_repair",
                    },
                },
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/{stage_attempt_id}.closeout.json",
                f"studies/{study_id}/artifacts/supervision/consumer/stage_attempt_closeouts/{stage_attempt_id}.json",
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert projection["provider_admission_candidates"][0]["attempt_idempotency_key"] == idempotency_key
    assert projection["transition_request_candidates"] == []
    assert "provider_admission_terminal_closeout_consumed" not in projection
    assert projection["latest_terminal_stage_log"]["status"] == "closed_with_domain_owner_refs"
    assert projection["current_work_unit"]["owner"] == "write"
    assert projection["current_work_unit"]["action_type"] == "request_opl_stage_attempt"
    assert projection["current_work_unit"]["work_unit_id"] == work_unit_id
    assert projection["current_execution_envelope"]["owner"] == "write"
    assert projection["current_execution_envelope"]["next_work_unit"] == work_unit_id


def test_study_progress_opl_current_control_state_handoff_uses_transition_request_for_terminal_probe(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    transition_candidate = {
        "status": "transition_request_pending",
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "source_refs": {
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
        },
    }
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-20T10:46:28+00:00",
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [transition_candidate],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 1,
                    "transition_request_candidates": [transition_candidate],
                }
            ],
        },
    )

    def fake_terminal_closeout(**kwargs):
        assert kwargs["study_id"] == study_id
        assert kwargs["preferred_actions"][0]["source_refs"]["attempt_idempotency_key"] == idempotency_key
        return {
            "surface_kind": "opl_terminal_provider_attempt_closeout",
            "source": "opl_family_runtime_attempt_inspect",
            "source_path": "opl://stage_attempts/sat_91d23a554175ea9288d903ad",
            "stage_attempt_id": "sat_91d23a554175ea9288d903ad",
            "status": "completed",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
            "closeout_receipt_status": "accepted_typed_closeout",
            "route_impact": {
                "next_owner": "medautoscience",
                "domain_ready_verdict": "domain_gate_pending",
            },
        }

    monkeypatch.setattr(module, "terminal_provider_attempt_closeout_for_study", fake_terminal_closeout)

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 0
    assert projection["transition_request_pending_count"] == 0
    consumed = projection["provider_admission_terminal_closeout_consumed"]
    assert consumed["stage_attempt_id"] == "sat_91d23a554175ea9288d903ad"
    assert projection["latest_terminal_stage_log"]["stage_attempt_id"] == "sat_91d23a554175ea9288d903ad"


def test_study_progress_opl_current_control_state_handoff_projects_top_level_transition_request_without_study_entry(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    work_unit_id = "medical_prose_write_repair"
    idempotency_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    transition_candidate = {
        "status": "transition_request_pending",
        "study_id": study_id,
        "action_type": "request_opl_stage_attempt",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "blocked_reason": "opl_execution_authorization_required",
        "source_refs": {
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
        },
    }
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-20T13:59:38+00:00",
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [transition_candidate],
            "studies": [],
        },
    )

    def fake_terminal_closeout(**kwargs):
        assert kwargs["study_id"] == study_id
        assert kwargs["preferred_actions"][0]["action_type"] == "request_opl_stage_attempt"
        assert kwargs["preferred_actions"][0]["source_refs"]["attempt_idempotency_key"] == idempotency_key
        return None

    monkeypatch.setattr(module, "terminal_provider_attempt_closeout_for_study", fake_terminal_closeout)

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection is not None
    assert projection["provider_admission_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    assert projection["transition_request_pending_count"] == 1
    assert projection["transition_request_candidates"] == [transition_candidate]
    assert projection["action_type"] == "request_opl_stage_attempt"
    assert projection["work_unit_id"] == work_unit_id
    assert projection["work_unit_fingerprint"] == fingerprint
    assert projection["blocked_reason"] == "opl_execution_authorization_required"


def test_study_progress_opl_current_control_state_handoff_projects_latest_terminal_stage_log(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-27T20:32:10+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {"health_status": "awaiting_explicit_resume"},
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
        / "stage_attempt_closeouts"
        / "sat-terminal.closeout_payload.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-05-27T19:46:34Z",
            "study_id": "001-risk",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat-terminal",
            "action_type": "run_quality_repair_batch",
            "status": "blocked_with_domain_owner_refs",
            "duration": {"seconds": 91.25, "source": "provider_attempt"},
            "token_usage": {"total_tokens": 12345, "input_tokens": 6789, "output_tokens": 5556},
            "cost": {"usd": 0.42, "currency": "USD"},
            "usage_refs": ["usage:provider-attempt:sat-terminal"],
            "cost_refs": ["cost:provider-attempt:sat-terminal"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "domain_owner/default-executor-dispatch",
                "problem_summary": "The repair owner could not write because authority route evidence was blocked.",
                "stage_goal": "Produce owner-authorized manuscript repair output or a typed blocker.",
                "stage_work_done": [
                    "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                ],
                "paper_work_done": [
                    "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                ],
                "changed_stage_surfaces": [],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "platform_repair",
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": [
                    "authority_route_blocked",
                    "opl_current_control_state.handoff_required",
                ],
                "usage_refs": ["usage:provider-attempt:sat-terminal"],
                "cost_refs": ["cost:provider-attempt:sat-terminal"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                    "artifacts/publication_eval/latest.json",
                ],
            },
            "closeout_refs": [
                "artifacts/supervision/consumer/stage_attempt_closeouts/sat-terminal.closeout_payload.json"
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["active_run_id"] is None
    assert projection["stage_progress_log"] == {}
    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["surface_kind"] == "mas_latest_terminal_stage_log_projection"
    assert terminal_log["source_path"] == str(closeout_path)
    assert terminal_log["stage_attempt_id"] == "sat-terminal"
    assert terminal_log["action_type"] == "run_quality_repair_batch"
    assert terminal_log["status"] == "blocked_with_domain_owner_refs"
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["duration"] == {"seconds": 91.25, "source": "provider_attempt"}
    assert terminal_log["token_usage"] == {
        "total_tokens": 12345,
        "input_tokens": 6789,
        "output_tokens": 5556,
    }
    assert terminal_log["cost"] == {"usd": 0.42, "currency": "USD"}
    assert terminal_log["usage_refs"] == ["usage:provider-attempt:sat-terminal"]
    assert terminal_log["cost_refs"] == ["cost:provider-attempt:sat-terminal"]
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["paper_stage_log"]["stage_work_done"] == [
        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
    ]
    assert terminal_log["paper_stage_log"]["changed_stage_surfaces"] == []
    assert terminal_log["paper_stage_log"]["progress_delta_classification"] == "platform_repair"
    assert terminal_log["paper_stage_log"]["outcome"] == "blocked_with_domain_typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == [
        "authority_route_blocked",
        "opl_current_control_state.handoff_required",
    ]
    assert terminal_log["authority_boundary"]["observability_only"] is True
    assert terminal_log["authority_boundary"]["can_mark_live_run"] is False
    assert terminal_log["authority_boundary"]["can_authorize_quality_verdict"] is False


def test_study_progress_latest_terminal_stage_log_prefers_direct_owner_execution(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-27T21:13:12+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {"health_status": "awaiting_explicit_resume"},
                }
            ],
        },
    )
    old_closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-old.closeout_payload.json"
    )
    _write_json(
        old_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-05-27T19:46:34Z",
            "study_id": "001-risk",
            "stage_attempt_id": "sat-old",
            "action_type": "run_quality_repair_batch",
            "status": "blocked_with_domain_owner_refs",
            "paper_stage_log": {
                "stage_name": "domain_owner/default-executor-dispatch",
                "paper_work_done": ["Recorded an older typed blocker."],
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": ["authority_route_blocked"],
                "evidence_refs": ["artifacts/publication_eval/latest.json"],
            },
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "legacy_surface_alias": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-27T21:12:39+00:00",
            "study_id": "001-risk",
            "owner_callable_receipt_projection": True,
            "projection_authority": False,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
                    "legacy_surface_alias": "default_executor_dispatch_execution",
                    "generated_at": "2026-05-27T21:12:39+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "duration_seconds": 18.0,
                    "usage": {
                        "input_tokens": 2100,
                        "output_tokens": 900,
                        "total_tokens": 3000,
                        "source_refs": ["usage:quality-repair-owner"],
                    },
                    "cost_usd": 0.17,
                    "cost_refs": ["cost:quality-repair-owner"],
                    "paper_stage_log": {
                        "stage_name": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
                        "current_owner": "write",
                        "stage_work_done": [
                            "Updated claim-evidence and review ledgers through the quality repair owner."
                        ],
                        "paper_work_done": [
                            "Updated claim-evidence and review ledgers through the quality repair owner."
                        ],
                        "changed_stage_surfaces": [
                            "paper/claim_evidence_map.json",
                            "paper/evidence_ledger.json",
                        ],
                        "changed_paper_surfaces": [
                            "paper/claim_evidence_map.json",
                            "paper/evidence_ledger.json",
                        ],
                        "outcome": "executed",
                        "remaining_blockers": [],
                        "evidence_refs": [
                            "artifacts/controller/quality_repair_batch/latest.json",
                            "paper/evidence_ledger.json",
                        ],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert projection["active_run_id"] is None
    assert terminal_log["source_path"] == str(latest_execution_path)
    assert terminal_log["record_path"] == f"{latest_execution_path}#executions/0"
    assert terminal_log["action_type"] == "run_quality_repair_batch"
    assert terminal_log["status"] == "executed"
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["duration"] == {"seconds": 18.0}
    assert terminal_log["token_usage"] == {
        "input_tokens": 2100,
        "output_tokens": 900,
        "total_tokens": 3000,
        "source_refs": ["usage:quality-repair-owner"],
    }
    assert terminal_log["cost"] == {"usd": 0.17}
    assert terminal_log["usage_refs"] == ["usage:quality-repair-owner"]
    assert terminal_log["cost_refs"] == ["cost:quality-repair-owner"]
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["paper_stage_log"]["outcome"] == "executed"
    assert terminal_log["paper_stage_log"]["stage_work_done"] == [
        "Updated claim-evidence and review ledgers through the quality repair owner."
    ]
    assert terminal_log["paper_stage_log"]["changed_stage_surfaces"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert terminal_log["paper_stage_log"]["changed_paper_surfaces"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert terminal_log["authority_boundary"]["can_mark_live_run"] is False


def test_handoff_projection_closes_running_flag_for_matching_terminal_attempt(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-08T17:18:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live",
                    "active_stage_attempt_id": "sat-live",
                    "active_workflow_id": "wf-live",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-06-08T17:19:37+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-08T17:19:37+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-live",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Owner callable failed closed with a typed blocker.",
                        "stage_goal": "Produce an AI reviewer record or typed blocker.",
                        "stage_work_done": ["Ran the owner callable."],
                        "paper_work_done": ["No publication eval was written."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "typed_blocker",
                        "outcome": "typed_blocker",
                        "remaining_blockers": ["medical_prose_review_request_rehydrate_required"],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert projection["active_workflow_id"] is None
    assert projection["active_stage_attempt_id"] == "sat-live"
    assert projection["runtime_health"]["health_status"] == "terminal"
    assert projection["runtime_health"]["runtime_liveness_status"] == "terminal"
    assert projection["latest_terminal_stage_log"]["stage_attempt_id"] == "sat-live"
    assert projection["latest_terminal_stage_log"]["status"] == "blocked"


def test_handoff_projection_fail_closed_when_terminal_closeout_lacks_owner_answer(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-no-answer",
                    "active_stage_attempt_id": "sat-no-answer",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-no-answer",
                        }
                    ],
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-10T12:01:00+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-no-answer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "completed",
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Provider returned terminal closeout without owner answer.",
                        "stage_goal": "Produce an AI reviewer record or typed blocker.",
                        "stage_work_done": ["Inspected current inputs."],
                        "paper_work_done": ["No publication eval was written."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "platform_repair",
                        "outcome": "completed_without_owner_answer",
                        "remaining_blockers": [],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert projection["action_queue"] == []
    assert projection["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert projection["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
    assert projection["typed_blocker"]["owner"] == "MedAutoScience"
    assert projection["typed_blocker"]["work_unit_id"] == "ai-reviewer-record"
    assert projection["consumed_action_queue"][0]["consumption"]["state"] == "consumed_by_terminal_stage_closeout"
    assert projection["blocked_reason"] == "typed_closeout_packet_required"
    assert projection["next_owner"] == "MedAutoScience"


def test_handoff_projection_accepts_terminal_closeout_owner_receipt_ref(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-owner-answer",
                    "active_stage_attempt_id": "sat-owner-answer",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-owner-answer",
                        }
                    ],
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-10T12:01:00+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-owner-answer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "completed",
                    "status": "closed_with_domain_owner_refs",
                    "route_outcome": "owner_receipt",
                    "owner_receipt_ref": (
                        "studies/001-risk/artifacts/supervision/consumer/default_executor_execution/"
                        "sat-owner-answer.closeout.json#owner_receipt"
                    ),
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Provider returned record-only AI reviewer evidence.",
                        "stage_goal": "Produce an AI reviewer owner receipt.",
                        "stage_work_done": ["Materialized reviewer record."],
                        "paper_work_done": ["No publication latest surface was written."],
                        "changed_stage_surfaces": [
                            "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json"
                        ],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "deliverable_progress",
                        "outcome": "closed_with_domain_owner_refs",
                        "remaining_blockers": [],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert "typed_blocker" not in projection
    assert "typed_closeout_packet_required" not in projection.get("why_not_applied", [])


def test_handoff_projection_accepts_terminal_closeout_next_handoff_refs(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "provider_admission_pending",
                    "active_run_id": "opl-stage-attempt://sat-next-handoff",
                    "active_stage_attempt_id": "sat-next-handoff",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-next-handoff",
                        }
                    ],
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
        / "stage_attempt_closeouts"
        / "sat-next-handoff.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "stage_attempt_id": "sat-next-handoff",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "closed_with_domain_owner_refs",
            "domain_owner_refs": {
                "publication_eval_record_ref": "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                "next_dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json",
                "next_request_ref": "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
            },
            "paper_stage_log": {
                "stage_name": "return_to_ai_reviewer_workflow",
                "problem_summary": "Provider produced current reviewer evidence and routed the next owner.",
                "stage_goal": "Produce reviewer record and next gate-clearing handoff.",
                "stage_work_done": [
                    "Materialized the reviewer record.",
                    "Routed the next owner to run_gate_clearing_batch.",
                ],
                "paper_work_done": ["Produced record-only reviewer evidence."],
                "changed_stage_surfaces": [
                    "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                    "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json",
                    "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
                ],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "deliverable_progress",
                "outcome": "closed_with_domain_owner_refs",
                "remaining_blockers": ["Domain readiness remains owned by MAS gate surfaces."],
                "next_forced_delta": {
                    "required_delta_kind": "owner_route_replay_or_typed_blocker",
                    "reason": "domain_action_request_materialize_routed_next_owner_after_current_ai_reviewer_record",
                    "owner_action": {
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "current_package_freshness_required",
                    },
                    "target_surface": {
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                    },
                    "acceptance_refs": ["owner_receipt_ref", "typed_blocker_ref", "changed_surface_ref"],
                },
                "evidence_refs": [
                    "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                    "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json",
                    "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
                ],
            },
            "closeout_refs": [
                "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json",
                "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert "typed_blocker" not in projection
    assert projection["next_owner"] != "one-person-lab"
    assert "typed_closeout_packet_required" not in projection.get("why_not_applied", [])
    assert projection["latest_terminal_stage_log"]["next_forced_delta"]["owner_action"]["action_type"] == (
        "run_gate_clearing_batch"
    )


def test_live_attempt_merge_replaces_stale_handoff_stage_attempt_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-previous-closeout",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-previous-closeout",
                "status": "blocked",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_run_id"] == "opl-stage-attempt://sat-current"
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["active_workflow_id"] == "wf-current"


def test_live_attempt_merge_replaces_stale_handoff_work_unit_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:stale-gate-replay",
            "action_fingerprint": "sha256:stale-gate-replay",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:stale-gate-replay",
                "action_fingerprint": "sha256:stale-gate-replay",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["action_type"] == "run_quality_repair_batch"
    assert merged["work_unit_id"] == "medical_prose_write_repair"
    assert merged["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert merged["action_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert merged["runtime_health"]["action_type"] == "run_quality_repair_batch"
    assert merged["runtime_health"]["work_unit_id"] == "medical_prose_write_repair"
    assert merged["runtime_health"]["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"


def test_live_attempt_merge_keeps_running_over_prior_same_work_unit_terminal_closeout() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": None,
            "active_stage_attempt_id": None,
            "active_workflow_id": None,
            "running_provider_attempt": False,
            "blocked_reason": "opl_execution_authorization_required",
            "next_owner": "one-person-lab",
            "action_queue": [
                {
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                }
            ],
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "status": "blocked",
                "typed_blocker_reason": "opl_execution_authorization_required",
                "source_path": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_execution/latest.json",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "stage_progress_log": {
                "planned_work": {
                    "stage_attempt_id": "sat-current",
                    "stage_packet_ref": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json",
                }
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_run_id"] == "opl-stage-attempt://sat-current"
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["active_workflow_id"] == "wf-current"
    assert merged["blocked_reason"] is None
    assert "typed_blocker" not in merged


def test_live_attempt_merge_supersedes_unsupported_dispatch_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "running_provider_attempt": False,
            "blocked_reason": "blocked:unsupported_dispatch_surface",
            "next_owner": "one-person-lab",
            "why_not_applied": ["blocked:unsupported_dispatch_surface"],
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["blocked_reason"] is None
    assert merged["why_not_applied"] == []
    assert merged["runtime_owner"] == "one-person-lab"
    assert merged["provider_attempt_owner"] == "one-person-lab"


def test_live_attempt_merge_ignores_prior_typed_closeout_for_different_stage_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_typed_default_executor_closeout": {
                "execution_id": "sat-prior",
                "stage_attempt_id": "sat-prior",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "blocked_reason": "blocked:unsupported_dispatch_surface",
                "next_owner": "write",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["runtime_owner"] == "one-person-lab"
    assert "typed_blocker" not in merged
    assert merged.get("blocked_reason") is None


def test_latest_terminal_stage_log_marks_missing_observability(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                        "remaining_blockers": [],
                        "evidence_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "missing"
    assert terminal_log["missing_observability_fields"] == ["duration", "token_usage", "cost"]
    assert terminal_log["duration"] == {
        "status": "missing",
        "seconds": None,
        "missing_duration_reason": "no_terminal_stage_duration_observed",
    }
    assert terminal_log["token_usage"] == {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
    }
    assert terminal_log["cost"] == {
        "status": "missing",
        "usd": None,
        "missing_cost_reason": "no_terminal_stage_cost_observed",
    }


def test_latest_terminal_stage_log_preserves_zero_observability_values(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "duration_seconds": 0,
                    "token_usage": {"total_tokens": 0},
                    "cost_usd": 0,
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["duration"] == {"seconds": 0}
    assert terminal_log["token_usage"] == {"total_tokens": 0}
    assert terminal_log["cost"] == {"usd": 0}
