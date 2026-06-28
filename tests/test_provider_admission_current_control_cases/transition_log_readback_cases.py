from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.provider_admission_parts.provider_admission import (
    current_control_provider_admission_candidates,
)
from tests.provider_admission_current_control_helpers import (
    opl_transition_replay_audit_readback as _opl_transition_replay_audit_readback,
)


def _write_jsonl(path: Path, payloads: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(payload, ensure_ascii=False) + "\n" for payload in payloads),
        encoding="utf-8",
    )


def test_provider_admission_current_control_consumes_opl_transition_log_readback(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    command_id = f"opl-domain-progress-command::{study_id}::{action_fingerprint}"
    replay = _opl_transition_replay_audit_readback(
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    command_event_log = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )
    _write_jsonl(
        command_event_log,
        [
            {
                "surface_kind": "opl_domain_progress_transition_log_entry",
                "runtime_id": "opl_domain_progress_transition_runtime",
                "transaction_id": replay["transaction_id"],
                "idempotency_key": route_key,
                "entry_kind": "command",
                "sequence_in_transaction": 0,
                "payload": {
                    "command_id": command_id,
                    "stage_run_identity": replay["stage_run_identity_readback"][
                        "command_stage_run_identity"
                    ],
                },
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
                    "outcome": {
                        "kind": "provider_admission_enqueued_or_blocked",
                        "stable_outcome": True,
                    },
                    "aggregate_identity": replay["aggregate_identity"],
                    "stage_run_identity": replay["stage_run_identity_readback"][
                        "event_stage_run_identity"
                    ],
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
                    "stage_run_identity": replay["stage_run_identity_readback"][
                        "outbox_stage_run_identity"
                    ],
                    "idempotency_key": route_key,
                },
            },
        ],
    )
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "provider_admission_pending": False,
            },
            "currentness_basis": {
                "source": "domain_transition",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-f4ac5a781b3258a4",
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "domain_transition",
            "next_owner": "write",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "action_type": "request_opl_stage_attempt",
            "allowed_actions": ["request_opl_stage_attempt"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "owner_route_currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-f4ac5a781b3258a4",
            },
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
                "source_surface": "domain_transition",
            },
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": False,
                "successor_owner_action": {
                    "action_type": "request_opl_stage_attempt",
                    "owner": "write",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "domain_transition_decision_type": "route_back_same_line",
                    "domain_transition_controller_action": "request_opl_stage_attempt",
                    "source_surface": "domain_transition",
                    "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
        },
    }
    candidates = current_control_provider_admission_candidates(
        {"studies": [scanned_study], "action_queue": []},
        study_root=profile.studies_root / study_id,
        status_payload=scanned_study,
    )

    assert len(candidates) == 1
    assert candidates[0]["route_identity_key"] == route_key
    assert candidates[0]["attempt_idempotency_key"] == route_key
    assert candidates[0]["idempotency_key"] == route_key
    assert candidates[0]["status"] == "provider_admission_pending"
    assert candidates[0]["provider_admission_pending"] is True
    assert candidates[0]["provider_attempt_or_lease_required"] is True
    assert candidates[0]["provider_admission_requires_opl_runtime_result"] is False
    assert candidates[0]["opl_domain_progress_transition_runtime_live_readback"][
        "identity"
    ]["latest_event_id"] == replay["event_id"]

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at="2026-06-20T17:06:00+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    assert len(result["provider_admission_candidates"]) == 1
    assert result["transition_request_candidates"] == []
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    [action] = result["action_queue"]
    assert action["status"] == "queued"
    assert action["provider_admission_pending"] is True
    assert action["provider_attempt_or_lease_required"] is True
    assert action["provider_admission_requires_opl_runtime_result"] is False
