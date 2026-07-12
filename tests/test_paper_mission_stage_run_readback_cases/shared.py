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
        "ai_route_context_ref": "paper-mission-transaction::dm002#ai_route_context",
        "domain_route_handoff_ref": (
            "paper-mission-transaction::dm002#domain_route_handoff"
        ),
        "domain_route_transaction_ref": "paper-mission-transaction::dm002",
        "domain_route_command_ref": (
            "paper-mission-transaction::dm002#ai_route_context"
        ),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "ai_route_context": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }


def _opl_stage_attempt_receipt(
    *,
    stage_attempt_id: str = "sat-terminal",
) -> dict[str, object]:
    return {
        "surface_kind": "opl_stage_attempt_transport_receipt",
        "schema_version": 1,
        "receipt_status": "terminal_closeout_observed",
        "role": "transport_receipt_only",
        "domain_id": "mas",
        "task_kind": "domain_route/stage-route",
        "domain_route_handoff_ref": "paper-mission-transaction::dm002#domain_route_handoff",
        "domain_route_transaction_ref": "paper-mission-transaction::dm002",
        "domain_route_command_ref": "paper-mission-transaction::dm002#ai_route_context",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "task_id": "frt-stage-route",
        "task_status": "blocked",
        "stage_attempt_id": stage_attempt_id,
        "stage_attempt_ref": f"opl://stage-attempts/{stage_attempt_id}",
        "runtime_closeout_ref": f"opl://stage-attempts/{stage_attempt_id}/closeouts/closeout-1",
        "typed_runtime_blocker_ref": "typed-blocker:opl_runtime_live_readback_required",
        "closeout_refs": [
            "paper-mission-transaction::dm002#stage_terminal_decision",
            "typed-blocker:opl_runtime_live_readback_required",
        ],
        "closeout_receipt_status": "accepted_typed_closeout",
        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        "authority_boundary": {
            "writes_domain_owner_receipt": False,
            "writes_domain_typed_blocker": False,
            "writes_domain_human_gate": False,
            "writes_domain_current_package": False,
            "can_select_next_owner": False,
            "can_claim_domain_progress": False,
        },
    }


def _opl_stage_attempt(
    *,
    stage_attempt_id: str = "sat-terminal",
    status: str = "completed",
) -> dict[str, object]:
    return {
        "stage_attempt_id": stage_attempt_id,
        "domain_id": "medautoscience",
        "stage_id": "stage_outcome/opl-handoff",
        "status": status,
        "task_id": "frt-stage-route",
        "provider_kind": "temporal",
        "workflow_id": "wf-stage-route",
        "provider_run": {
            "provider_status": status,
            "workflow_id": "wf-stage-route",
            "last_heartbeat_at": "2026-07-11T10:00:00Z",
        },
        "closeout_receipt_status": "accepted_typed_closeout"
        if status == "completed"
        else None,
        "closeout_refs": ["typed-blocker:opl_runtime_live_readback_required"]
        if status == "completed"
        else [],
        "workspace_locator": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "work_unit_id": "gate_clearing_claim_evidence_repair",
            "domain_route_handoff_ref": (
                "paper-mission-transaction::dm002#domain_route_handoff"
            ),
            "domain_route_transaction_ref": "paper-mission-transaction::dm002",
            "domain_route_command_ref": (
                "paper-mission-transaction::dm002#ai_route_context"
            ),
            "command_kind": "start_next_stage",
            "route_target": "publication_gate_replay",
        },
        "route_impact": {
            "next_owner": "medautoscience",
            "domain_ready_verdict": "domain_gate_pending",
        },
    }


def _opl_runtime_query_payload(
    *,
    stage_attempt_id: str = "sat-terminal",
    include_stage_attempt_receipt: bool = True,
) -> dict[str, object]:
    packet = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "completed",
        "study_id": "002-dm-china-us-mortality-attribution",
        "stage_attempt_id": stage_attempt_id,
        "closeout_receipt_status": "accepted_typed_closeout",
        "closeout_refs": ["typed-blocker:opl_runtime_live_readback_required"],
        "typed_blocker_ref": "typed-blocker:opl_runtime_live_readback_required",
        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
    if include_stage_attempt_receipt:
        packet["opl_stage_attempt_receipt"] = _opl_stage_attempt_receipt(
            stage_attempt_id=stage_attempt_id
        )
    return {
        "version": "g2",
        "family_runtime_stage_attempt_query": {
            "surface_id": "opl_family_runtime_stage_attempt_query",
            "stage_attempt_query": {
                "surface_kind": "stage_attempt_query",
                "attempt": _opl_stage_attempt(stage_attempt_id=stage_attempt_id),
                "closeouts": [
                    {
                        "closeout_id": "closeout-1",
                        "stage_attempt_id": stage_attempt_id,
                        "packet": packet,
                    }
                ],
            },
        },
    }


def _opl_running_query_payload() -> dict[str, object]:
    return {
        "version": "g2",
        "family_runtime_stage_attempt_query": {
            "surface_id": "opl_family_runtime_stage_attempt_query",
            "stage_attempt_query": {
                "surface_kind": "stage_attempt_query",
                "attempt": _opl_stage_attempt(stage_attempt_id="sat-running", status="running"),
                "closeouts": [],
            },
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
