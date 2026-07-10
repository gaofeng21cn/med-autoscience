from __future__ import annotations

import importlib

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    append_jsonl as _append_jsonl,
    make_profile,
    opl_transition_readback,
    opl_transition_replay_audit_readback,
    write_json as _write_json,
)

def test_study_progress_opl_current_control_state_handoff_consumes_matching_opl_terminal_attempt_closeout(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
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
    old_closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
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
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
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
            "surface": "portable_paper_mission_owner_surface",
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
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
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
            "surface": "portable_paper_mission_owner_surface",
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
            "stage_id": "stage_outcome/opl-handoff",
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
                f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/{stage_attempt_id}.closeout.json",
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
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
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
        / "owner_callable_adapters"
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
            "surface": "portable_paper_mission_owner_surface",
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
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
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
            "surface": "portable_paper_mission_owner_surface",
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
