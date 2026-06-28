from __future__ import annotations

import importlib
import os

from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_complete_provider_readback_supersedes_same_identity_request_only_current_surface() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    request_action = _request_opl_stage_attempt_action(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        route_key=route_key,
    )
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    provider_candidate = {
        **request_action,
        "surface": "opl_provider_admission_candidate",
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.provider_admission_candidates",
        "next_executable_owner": "write",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "study_id": study_id,
        "quest_id": study_id,
        "quest_status": "provider_admission_pending",
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [provider_candidate],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "current_executable_owner_action": request_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "provider_admission_pending": False,
                "transition_request_pending": True,
            },
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }

    result = module.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": request_action,
            "current_work_unit": handoff["current_work_unit"],
            "paper_recovery_state": _paper_recovery_successor_state(
                study_id=study_id,
                work_unit_id=work_unit_id,
                fingerprint=fingerprint,
            ),
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [provider_candidate],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff=handoff,
        runtime_health_snapshot={},
    )

    action = result["current_executable_owner_action"]
    work_unit = result["current_work_unit"]
    envelope = result["current_execution_envelope"]
    assert action["source"] == "opl_current_control_state.provider_admission_candidates"
    assert action["provider_admission_pending"] is True
    assert action.get("transition_request_pending") is not True
    assert action["opl_transition_readback_source"] == "opl_domain_progress_transition_runtime_live_readback"
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "opl_current_control_state.provider_admission_candidates"
    assert work_unit["state"]["provider_admission_pending"] is True
    assert work_unit["state"].get("transition_request_pending") is not True
    assert work_unit["state"]["provider_attempt_or_lease_required"] is True
    assert work_unit["state"]["provider_admission_requires_opl_runtime_result"] is False
    assert work_unit["state"]["opl_transition_runtime_required"] is False
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "write"
    assert envelope["next_work_unit"] == work_unit_id


def test_provider_readback_does_not_supersede_different_identity_request_only_surface() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    stale_fingerprint = "domain-transition::route_back_same_line::stale_medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    request_action = _request_opl_stage_attempt_action(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        route_key=route_key,
    )
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=stale_fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key="paper-policy-request:stale",
        attempt_idempotency_key="paper-policy-request:stale",
        request_idempotency_key="paper-policy-request:stale",
    )
    provider_candidate = {
        **request_action,
        "surface": "opl_provider_admission_candidate",
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.provider_admission_candidates",
        "work_unit_fingerprint": stale_fingerprint,
        "action_fingerprint": stale_fingerprint,
        "route_identity_key": "paper-policy-request:stale",
        "attempt_idempotency_key": "paper-policy-request:stale",
        "next_executable_owner": "write",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "study_id": study_id,
        "quest_id": study_id,
        "quest_status": "provider_admission_pending",
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [provider_candidate],
        "transition_request_pending_count": 1,
        "transition_request_candidates": [
            {
                **request_action,
                "status": "transition_request_pending",
                "next_executable_owner": "write",
            }
        ],
        "current_executable_owner_action": request_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }

    result = module.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": request_action,
            "current_work_unit": handoff["current_work_unit"],
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [provider_candidate],
            "transition_request_pending_count": 1,
            "transition_request_candidates": handoff["transition_request_candidates"],
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff=handoff,
        runtime_health_snapshot={},
    )

    action = result["current_executable_owner_action"]
    work_unit = result["current_work_unit"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["work_unit_fingerprint"] == fingerprint
    assert action["transition_request_pending"] is True
    assert action["provider_admission_pending"] is False
    assert work_unit["state"]["transition_request_pending"] is True
    assert work_unit["state"]["provider_admission_pending"] is False


def _request_opl_stage_attempt_action(
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    route_key: str,
) -> dict[str, object]:
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "opl_current_control_state.transition_request_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "write",
        "owner": "write",
        "action_type": "request_opl_stage_attempt",
        "allowed_actions": ["request_opl_stage_attempt"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }


def _paper_recovery_successor_state(
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
) -> dict[str, object]:
    return {
        "surface_kind": "paper_recovery_state",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "materialize_successor_owner_action",
            "owner": "write",
            "successor_owner_action": {
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "domain_transition_decision_type": "route_back_same_line",
                "domain_transition_controller_action": "request_opl_stage_attempt",
                "source_surface": "domain_transition",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
    }
