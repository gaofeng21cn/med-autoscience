from __future__ import annotations

import json
from pathlib import Path


def _carrier() -> dict[str, str]:
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "dispatch_status": "transition_request_pending",
    }


def _opl_route_carrier() -> dict[str, object]:
    return {
        **_carrier(),
        "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
        "stage_terminal_decision_ref": (
            "paper-mission-transaction::dm002#stage_terminal_decision"
        ),
        "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }


def _opl_runtime_task_payload() -> dict[str, object]:
    return {
        "version": "g2",
        "family_runtime_task": {
            "surface_id": "opl_family_runtime_task",
            "task": {
                "task_id": "frt-stage-route",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/stage-route",
                "payload": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                    "opl_route_command_ref": (
                        "paper-mission-transaction::dm002#opl_route_command"
                    ),
                    "command_kind": "start_next_stage",
                    "route_target": "publication_gate_replay",
                },
                "status": "blocked",
                "last_error": "paper_mission_stage_route_domain_gate_pending",
                "dead_letter_reason": (
                    "paper_mission_stage_route_domain_gate_pending"
                ),
                "current_control_state": {
                    "current_stage_attempt_id": "sat-terminal",
                    "running_provider_attempt": False,
                    "closeout_refs": [
                        "paper-mission-transaction::dm002#stage_terminal_decision",
                        "typed-blocker:opl_runtime_live_readback_required",
                    ],
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "typed_blocker_refs": [
                        "typed-blocker:opl_runtime_live_readback_required"
                    ],
                    "stage_run_currentness_identity": {
                        "stage_id": "publication_gate_replay",
                    },
                },
            },
            "stage_attempts": [
                {
                    "stage_attempt_id": "sat-terminal",
                    "status": "completed",
                    "stage_id": "publication_gate_replay",
                    "provider_attempt_ref": "temporal://attempt/sat-terminal",
                }
            ],
            "events": [
                {
                    "event_type": "paper_mission_stage_route_terminal_task_reconciled",
                    "payload": {
                        "closeout_refs": [
                            "paper-mission-transaction::dm002#stage_terminal_decision",
                            "typed-blocker:opl_runtime_live_readback_required",
                        ],
                        "opl_transition_receipt": {
                            "surface_kind": "opl_transition_receipt",
                            "schema_version": 1,
                            "receipt_status": "terminal_closeout_observed",
                            "role": "transport_receipt_only",
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                            "opl_route_command_ref": (
                                "paper-mission-transaction::dm002#opl_route_command"
                            ),
                            "command_kind": "start_next_stage",
                            "route_target": "publication_gate_replay",
                            "route_identity_key": "paper-mission-transaction::dm002::route",
                            "attempt_idempotency_key": "dm002::attempt",
                            "request_idempotency_key": "dm002::request",
                            "task_id": "frt-stage-route",
                            "task_status": "blocked",
                            "stage_attempt_id": "sat-terminal",
                            "stage_attempt_ref": "opl://stage-attempts/sat-terminal",
                            "runtime_closeout_ref": (
                                "opl://family-runtime/tasks/frt-stage-route/"
                                "terminal-closeout-readback"
                            ),
                            "typed_runtime_blocker_ref": (
                                "typed-blocker:opl_runtime_live_readback_required"
                            ),
                            "closeout_refs": [
                                "paper-mission-transaction::dm002#stage_terminal_decision",
                                "typed-blocker:opl_runtime_live_readback_required",
                            ],
                            "closeout_receipt_status": "accepted_typed_closeout",
                            "blocked_reason": (
                                "paper_mission_stage_route_domain_gate_pending"
                            ),
                            "can_change_stage_terminal_decision": False,
                            "can_select_next_owner": False,
                            "authority_boundary": {
                                "writes_owner_receipt": False,
                                "writes_typed_blocker": False,
                                "writes_human_gate": False,
                                "writes_current_package": False,
                                "can_claim_paper_progress": False,
                            },
                        },
                    },
                }
            ],
        },
    }


def _opl_running_task_completed_attempt_payload() -> dict[str, object]:
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["status"] = "running"
    task["last_error"] = "paper_mission_stage_route_temporal_started"
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-stale",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::other",
                "opl_route_command_ref": "paper-mission-transaction::other#opl_route_command",
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": ["stale-closeout"],
            "closeout_receipt_status": "accepted_typed_closeout",
        },
        {
            "stage_attempt_id": "sat-completed",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [
                "paper-mission-transaction::dm002#opl_route_command",
                (
                    "opl://stage-attempts/sat-completed/runtime-blockers/"
                    "no_typed_domain_handler_closeout_observed"
                ),
            ],
            "closeout_receipt_status": "accepted_typed_closeout",
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-completed",
            },
        },
    ]
    runtime_task["events"] = []
    return payload


def _opl_running_task_running_attempt_payload() -> dict[str, object]:
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["status"] = "running"
    task["last_error"] = "paper_mission_stage_route_temporal_started"
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-running",
            "status": "running",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "provider_kind": "temporal",
            "workflow_id": "wf-running",
            "provider_run": {
                "provider_status": "running",
                "workflow_id": "wf-running",
                "last_heartbeat_at": "2026-06-24T09:33:26.074Z",
                "last_runner_event_kind": "command_execution",
            },
        }
    ]
    runtime_task["events"] = []
    return payload


def _opl_queue_with_terminal_and_running_successor_payload() -> dict[str, object]:
    terminal = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    successor = {
        "task_id": "frt-successor",
        "domain_id": "medautoscience",
        "task_kind": "paper_mission/stage-route",
        "payload": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
            "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
            "command_kind": "start_next_stage",
            "route_target": "publication_gate_replay",
            "requeued_from_terminal_task_id": "frt-stage-route",
            "terminal_successor_generation": 1,
        },
        "status": "running",
        "last_error": "paper_mission_stage_route_temporal_started",
        "linked_stage_attempt_liveness": {
            "surface_kind": "opl_queue_task_linked_stage_attempt_liveness",
            "status": "live",
            "stage_attempt_id": "sat-successor",
            "workflow_id": "wf-successor",
            "stage_id": "publication_gate_replay",
            "provider_kind": "temporal",
            "executor_kind": "codex_cli",
            "task_id": "frt-successor",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [],
        },
    }
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 2,
                "by_status": {
                    "blocked": 1,
                    "running": 1,
                },
            },
            "tasks": [terminal, successor],
        },
    }


def _opl_queue_with_many_matching_terminal_tasks_payload() -> dict[str, object]:
    tasks = []
    for index in range(5):
        task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
        task["task_id"] = f"frt-stage-route-{index}"
        task["current_control_state"] = {}
        tasks.append(task)
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": len(tasks),
                "by_status": {
                    "blocked": len(tasks),
                },
            },
            "tasks": tasks,
        },
    }


def _opl_queue_with_matching_tasks_without_closeout_summary_payload() -> dict[str, object]:
    task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    task["status"] = "blocked"
    task["current_control_state"] = {}
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 1,
                "by_status": {
                    "blocked": 1,
                },
            },
            "tasks": [task],
        },
    }


def _opl_queue_with_stale_and_current_tasks_without_summary_payload() -> dict[str, object]:
    stale = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    stale["task_id"] = "frt-stale"
    stale["status"] = "blocked"
    stale["last_error"] = (
        "operator_retired_stale_runtime_residue:"
        "mas_paper_mission_current_thread_replaces_stale_stage_route_rows"
    )
    stale["current_control_state"] = {}
    current = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    current["task_id"] = "frt-current"
    current["status"] = "blocked"
    current["last_error"] = "paper_mission_stage_route_domain_gate_pending"
    current["current_control_state"] = {}
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 2,
                "by_status": {
                    "blocked": 2,
                },
            },
            "tasks": [stale, current],
        },
    }


def _opl_queue_with_list_closeout_summary_payload() -> dict[str, object]:
    task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    task["status"] = "blocked"
    task["current_control_state"] = {
        "current_stage_attempt_id": "sat-list-terminal",
        "running_provider_attempt": False,
        "closeout_receipt_status": "accepted_typed_closeout",
        "closeout_refs": [
            "paper-mission-transaction::dm002#opl_route_command",
            "opl://stage-attempts/sat-list-terminal/runtime-blockers/domain_gate_pending",
        ],
        "typed_blocker_refs": [
            "opl://stage-attempts/sat-list-terminal/runtime-blockers/domain_gate_pending"
        ],
        "stage_run_currentness_identity": {
            "stage_id": "publication_gate_replay",
        },
    }
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 1,
                "by_status": {
                    "blocked": 1,
                },
            },
            "tasks": [task],
        },
    }


def _write_closeout(study_root: Path, override: dict[str, object]) -> None:
    closeout_root = (
        study_root / "artifacts" / "supervision" / "consumer" / "stage_attempt_closeouts"
    )
    closeout_root.mkdir(parents=True)
    payload = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "blocked",
        "study_id": "002-dm-china-us-mortality-attribution",
        "stage_id": "gate_clearing_claim_evidence_repair",
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "stage_packet_ref": "opl-stage-run://paper-mission-summary/dm002",
        "provider_attempt_ref": "temporal://attempt/sat-terminal",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "blocked_reason": "domain_gate_pending",
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
    payload.update(override)
    (closeout_root / "sat-terminal.closeout.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
