from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.provider_admission_current_control_helpers import (
    provider_candidate as _provider_candidate,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission import (
    current_control_provider_admission_candidates,
)

pytestmark = pytest.mark.contract


def _explicit_queue_action_from_current(study: dict) -> dict:
    action = dict(study["current_executable_owner_action"])
    action["study_id"] = study["study_id"]
    action["quest_id"] = study.get("quest_id") or study["study_id"]
    action.setdefault("status", "transition_request_pending")
    action.setdefault("owner", action.get("next_owner"))
    action.setdefault("next_executable_owner", action.get("next_owner") or action.get("owner"))
    return action


def test_dry_run_materialized_transition_request_waits_for_opl_readback(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "source": "same_tick_materialized_dispatch",
        "status": "transition_request_pending",
        "dispatch_status": "transition_request_pending",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_admission_pending": False,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "same_tick_materialized_provider_admission": True,
        "same_tick_materialization_source": "dry_run_preview",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-18T14:15:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
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
    assert result["transition_request_pending_count"] == 1
    [transition_request] = result["transition_request_candidates"]
    assert transition_request["provider_admission_pending"] is False
    assert transition_request["provider_admission_requires_opl_runtime_result"] is True
    assert transition_request["same_tick_materialization_source"] == "dry_run_preview"
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    [decision] = result["stage_route_arbiter_decisions"]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"


def test_request_only_transition_waits_for_readback_across_owner_action_recovery_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "source": "domain_action_request_materialization_preview",
        "status": "transition_request_pending",
        "dispatch_status": "transition_request_pending",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_admission_pending": False,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-18T15:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
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
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {"owner": "write"},
                    "next_safe_action": {
                        "kind": "materialize_successor_owner_action",
                        "owner": "write",
                        "provider_admission_allowed": True,
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request] = result["transition_request_candidates"]
    assert transition_request["provider_admission_pending"] is False
    assert transition_request["provider_admission_requires_opl_runtime_result"] is True
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    [decision] = result["stage_route_arbiter_decisions"]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"


def test_request_only_successor_transition_candidate_carries_current_work_unit_stage_packet_ref(
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
    expected_stage_packet_ref = f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
    study_root = profile.studies_root / study_id
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "allowed_actions": ["request_opl_stage_attempt"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "owner_route_currentness_basis": {
                "source": "domain_transition",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-6515f3a8afd87b15",
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "currentness_basis": {
                "source": "domain_transition",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-6515f3a8afd87b15",
            },
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "successor_owner_action": {
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "action_type": "request_opl_stage_attempt",
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "currentness_basis": {
                        "source": "domain_transition",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                        "runtime_health_epoch": "runtime-health-event-006980-6515f3a8afd87b15",
                    },
                },
            },
        },
    }
    current_control_payload = {
        "surface": "portable_paper_mission_owner_surface",
        "generated_at": "2026-06-20T15:25:00+00:00",
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "action_queue": [_explicit_queue_action_from_current(scanned_study)],
        "studies": [scanned_study],
    }
    candidates = current_control_provider_admission_candidates(
        current_control_payload,
        study_root=study_root,
        status_payload={"study_id": study_id, **scanned_study},
        current_control_ref=(
            "runtime/artifacts/supervision/opl_current_control_state/latest.json"
        ),
    )
    assert len(candidates) == 1

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at="2026-06-20T15:25:00+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request] = result["transition_request_candidates"]
    assert transition_request["action_type"] == "request_opl_stage_attempt"
    assert transition_request["work_unit_id"] == work_unit_id
    assert transition_request["stage_packet_ref"] == expected_stage_packet_ref
    assert transition_request["stage_packet_refs"] == [expected_stage_packet_ref]
    assert transition_request["checkpoint_refs"] == [expected_stage_packet_ref]
    assert transition_request["provider_admission_pending"] is False
    assert transition_request["provider_attempt_or_lease_required"] is False
    assert transition_request["provider_admission_requires_opl_runtime_result"] is True
    action = result["action_queue"][0]
    assert action["stage_packet_ref"] == expected_stage_packet_ref
    assert action["stage_packet_refs"] == [expected_stage_packet_ref]
    assert action["provider_attempt_or_lease_required"] is False
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }


def test_dry_run_transition_request_is_not_promoted_by_unconsumed_closeout_guard(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "status": "transition_request_pending",
        "dispatch_status": "transition_request_pending",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_admission_pending": False,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "same_tick_materialized_provider_admission": True,
        "same_tick_materialization_source": "dry_run_preview",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-18T00:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "blocked_reason": "paper_progress_stall_fingerprint_stale",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "stage_attempt_id": "sat-inferred-closeout",
                        "identity_binding_status": "inferred_from_current_work_unit",
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert len(result["transition_request_candidates"]) == 1
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    action = result["action_queue"][0]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_attempt_or_lease_required"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is True
