from __future__ import annotations

import importlib

from med_autoscience.controllers import paper_progress_policy_adapter
from tests.study_progress_cases.provider_admission_projection import (
    _opl_transition_result,
    _supervisor_decision,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_provider_admission_projection_preserves_handoff_transition_request_when_supervisor_blocks_provider_admission(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    transition_request = paper_progress_policy_adapter.build_transition_request(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        quest_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        next_owner="write",
        policy_kind=paper_progress_policy_adapter.START_PROVIDER_ATTEMPT,
        source_generation="truth::current",
        expected_version="truth::current",
        currentness_basis={
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
    )
    transition_request["idempotency_key"] = route_key

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": False,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "supervisor_decision": _supervisor_decision(
                    "materialize_recovery_action",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "provider_admission_pending": False,
                    "transition_request_pending": True,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                },
                "currentness_basis": {
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "transition_request_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                    "mas_owner_action_source": (
                        "paper_recovery_state.next_safe_action.successor_owner_action"
                    ),
                    "provider_admission_pending": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "opl_domain_progress_transition_request": transition_request,
                    "currentness_basis": {
                        "source": (
                            "paper_recovery_state.next_safe_action.successor_owner_action"
                        ),
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth::current",
                        "runtime_health_epoch": "runtime::current",
                    },
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "transition_request_pending",
                    "source": "opl_current_control_state_action_queue",
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                }
            ],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 1
    candidate = fields["transition_request_candidates"][0]
    assert candidate["status"] == "transition_request_pending"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["opl_transition_runtime_required"] is True
    assert fields["provider_admission_blocked_by_supervisor_decision"] == {
        "decision": "materialize_recovery_action",
        "reason": "paper_autonomy_supervisor_decision_blocks_provider_admission",
    }


def test_provider_admission_projection_same_identity_provider_readback_consumes_handoff_transition_request(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    transition_request = paper_progress_policy_adapter.build_transition_request(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        quest_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        next_owner="write",
        policy_kind=paper_progress_policy_adapter.START_PROVIDER_ATTEMPT,
        source_generation="truth::current",
        expected_version="truth::current",
    )
    transition_request["idempotency_key"] = route_key

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "provider_admission_pending": True,
                    "transition_request_pending": False,
                    "provider_attempt_or_lease_required": True,
                    "provider_admission_requires_opl_runtime_result": False,
                },
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "source": "opl_current_control_state.provider_admission_candidates",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "provider_admission_pending",
                    "next_executable_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "provider_attempt_or_lease_required": True,
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "transition_request_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                    "mas_owner_action_source": (
                        "paper_recovery_state.next_safe_action.successor_owner_action"
                    ),
                    "provider_admission_pending": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "opl_domain_progress_transition_request": transition_request,
                }
            ],
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )


def test_same_identity_provider_readback_retains_transition_request_stage_packet_refs(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = "domain-transition::ai_reviewer_re_eval::produce_ai_reviewer_publication_eval_record_against_current_inputs"
    route_key = "paper-policy-request:afa135a3051e8aa76700b447"
    stage_packet_ref = f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    readback["identity"]["idempotency_key"] = route_key
    readback["identity"]["request_idempotency_key"] = route_key
    readback["identity"]["stage_run_identity"]["route_identity_key"] = route_key
    readback["identity"]["stage_run_identity"]["attempt_idempotency_key"] = route_key
    readback["read_model_readback"]["identity"] = readback["identity"]
    transition_request = paper_progress_policy_adapter.build_transition_request(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        quest_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        next_owner="ai_reviewer",
        policy_kind=paper_progress_policy_adapter.START_PROVIDER_ATTEMPT,
        source_generation="truth::current",
        expected_version="truth::current",
    )
    transition_request["idempotency_key"] = route_key

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "source": "opl_current_control_state.provider_admission_candidates",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "provider_admission_pending",
                    "next_executable_owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "provider_attempt_or_lease_required": True,
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "transition_request_pending",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                    "mas_owner_action_source": (
                        "paper_recovery_state.next_safe_action.successor_owner_action"
                    ),
                    "stage_packet_ref": stage_packet_ref,
                    "stage_packet_refs": [stage_packet_ref],
                    "checkpoint_refs": [stage_packet_ref],
                    "source_refs": {
                        "stage_packet_ref": stage_packet_ref,
                        "stage_packet_refs": [stage_packet_ref],
                    },
                    "provider_admission_pending": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "opl_domain_progress_transition_request": transition_request,
                }
            ],
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["stage_packet_ref"] == stage_packet_ref
    assert candidate["stage_packet_refs"] == [stage_packet_ref]
    assert candidate["checkpoint_refs"] == [stage_packet_ref]
    assert candidate["source_refs"]["stage_packet_ref"] == stage_packet_ref


def test_request_only_candidate_with_live_readback_promotes_to_provider_admission(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = "domain-transition::ai_reviewer_re_eval::produce_ai_reviewer_publication_eval_record_against_current_inputs"
    route_key = "paper-policy-request:afa135a3051e8aa76700b447"
    stage_packet_ref = f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    readback["identity"]["idempotency_key"] = route_key
    readback["identity"]["request_idempotency_key"] = route_key
    readback["identity"]["stage_run_identity"]["route_identity_key"] = route_key
    readback["identity"]["stage_run_identity"]["attempt_idempotency_key"] = route_key
    readback["read_model_readback"]["identity"] = readback["identity"]

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "transition_request_pending",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "idempotency_key": route_key,
                    "mas_owner_action_source": (
                        "paper_recovery_state.next_safe_action.successor_owner_action"
                    ),
                    "stage_packet_ref": stage_packet_ref,
                    "stage_packet_refs": [stage_packet_ref],
                    "checkpoint_refs": [stage_packet_ref],
                    "source_refs": {
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                        "stage_packet_ref": stage_packet_ref,
                        "stage_packet_refs": [stage_packet_ref],
                    },
                    "provider_admission_pending": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["provider_admission_pending"] is True
    assert candidate["provider_admission_requires_opl_runtime_result"] is False
    assert candidate["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )
    assert candidate["stage_packet_ref"] == stage_packet_ref
