from __future__ import annotations

from tests.provider_admission_current_control_helpers import opl_transition_readback

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_handoff_preserves_current_control_current_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    fingerprint = "publication-blockers::0915410f804b3697"
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
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-14T09:58:23+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "running_provider_attempt": False,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "schema_version": 1,
                        "status": "typed_blocker",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "state": {
                            "state_kind": "typed_blocker",
                            "source": "accepted_closeout_consumed_pending",
                            "typed_blocker": {
                                "blocker_type": "provider_completion_is_not_domain_ready",
                                "owner": "med-autoscience",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": fingerprint,
                                "typed_blocker_ref": (
                                    "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                                    "sat_f8e1cfe49a3aa3cf95d0584d.closeout.json"
                                ),
                            },
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "med-autoscience",
                        "source": "accepted_closeout_consumed_pending",
                        "typed_blocker": {
                            "blocker_type": "provider_completion_is_not_domain_ready",
                            "owner": "med-autoscience",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                    "provider_admission_pending_count": 0,
                    "provider_admission_candidates": [],
                    "typed_blocker": {
                        "blocker_type": "provider_completion_is_not_domain_ready",
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                    "blocked_reason": "provider_completion_is_not_domain_ready",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "handoff_required",
            "reason": "opl_stage_attempt_admission_required",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-after-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["current_work_unit"]["status"] == "typed_blocker"
    assert handoff["current_work_unit"]["work_unit_fingerprint"] == fingerprint
    assert handoff["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert handoff["provider_admission_pending_count"] == 0
    assert handoff["provider_admission_candidates"] == []
    assert handoff["legacy_current_projection_boundary"] == {
        "surface_kind": "legacy_current_control_currentness_projection_boundary",
        "status": "diagnostic_only",
        "authority": False,
        "diagnostic_only": True,
        "replacement_authority": "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt",
        "default_selector_policy": "fail_closed",
        "can_select_next_action": False,
        "can_authorize_dispatch": False,
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "can_claim_paper_progress": False,
        "projected_surfaces": [
            "current_work_unit",
            "current_execution_envelope",
            "typed_blocker",
        ],
    }
    assert handoff["current_work_unit"]["state"]["typed_blocker"]["blocker_type"] == (
        "provider_completion_is_not_domain_ready"
    )
    assert_default_next_action_legacy_surfaces_retired(result)


def test_same_identity_provider_readback_supersedes_request_only_current_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit}",
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    request_only_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "domain_transition",
        "next_owner": "write",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "action_type": "request_opl_stage_attempt",
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-20T23:36:08+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "handoff_scan_status": "provider_admission_from_mas_handoff",
                    "quest_status": "provider_admission_pending",
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "provider_admission_pending",
                        "runtime_liveness_status": "not_running",
                        "summary": "OPL transition readback recorded provider admission.",
                    },
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_candidates": [],
                    "opl_domain_progress_transition_live_readback": readback,
                    "opl_domain_progress_transition_result": readback,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "request_opl_stage_attempt",
                            "status": "queued",
                            "owner": "write",
                            "next_executable_owner": "write",
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": route_key,
                            "attempt_idempotency_key": route_key,
                            "idempotency_key": route_key,
                            "provider_attempt_or_lease_required": True,
                            "source_surface": "mas_opl_runtime_owner_handoff.provider_admission_identity",
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat_efdab57a49cb6d58f2a17eeb.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-20T16:05:54Z",
            "study_id": study_id,
            "stage_id": "stage_outcome/opl-handoff",
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "stage_packet_ref": f"mas://current-work-unit/{study_id}/{work_unit}/stage-packet",
            "status": "closed_with_domain_owner_refs",
            "owner_receipt_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "status": "available",
                "stage_name": work_unit,
                "changed_paper_surfaces": [
                    f"studies/{study_id}/artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md",
                ],
                "outcome": "closed_with_domain_owner_refs",
            },
        },
    )
    handoff_module = importlib.import_module(
        "med_autoscience.controllers.study_progress.opl_current_control_state_handoff"
    )
    monkeypatch.setattr(
        handoff_module,
        "terminal_provider_attempt_closeout_for_study",
        lambda **_: {
            "surface_kind": "opl_terminal_provider_attempt_closeout",
            "source": "opl_family_runtime_attempt_inspect",
            "source_path": "opl://stage_attempts/sat_efdab57a49cb6d58f2a17eeb",
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "status": "closed_with_domain_owner_refs",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "stage_packet_ref": f"mas://current-work-unit/{study_id}/{work_unit}/stage-packet",
            "owner_receipt_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "status": "available",
                "stage_name": work_unit,
                "changed_paper_surfaces": [
                    f"studies/{study_id}/artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md",
                ],
                "outcome": "closed_with_domain_owner_refs",
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "paper_recovery_successor_ready",
            "active_run_id": None,
            "current_executable_owner_action": request_only_action,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "stage_id": "publication_supervision",
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "next_work_unit": work_unit,
                    "provider_admission_pending": False,
                    "transition_request_pending": True,
                    "provider_attempt_or_lease_required": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                },
            },
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_candidates": [],
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-006980-26dd285b9c2c9794",
                "runtime_liveness_status": "none",
                "health_status": "none",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["provider_admission_pending_count"] == 1
    assert handoff["transition_request_pending_count"] == 0
    assert handoff["provider_admission_candidates"][0]["route_identity_key"] == route_key
    assert_default_next_action_legacy_surfaces_retired(result)


def test_provider_readback_not_consumed_by_prior_request_wrapper_domain_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit}",
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    stage_packet_ref = f"mas://current-work-unit/{study_id}/{work_unit}/stage-packet"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-21T00:10:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "handoff_scan_status": "provider_admission_from_mas_handoff",
                    "quest_status": "provider_admission_pending",
                    "running_provider_attempt": False,
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "request_opl_stage_attempt",
                            "status": "queued",
                            "owner": "write",
                            "next_executable_owner": "write",
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": route_key,
                            "attempt_idempotency_key": route_key,
                            "idempotency_key": route_key,
                            "dispatch_ref": stage_packet_ref,
                            "stage_packet_ref": stage_packet_ref,
                            "stage_packet_refs": [stage_packet_ref],
                            "checkpoint_refs": [stage_packet_ref],
                            "provider_attempt_or_lease_required": True,
                            "opl_domain_progress_transition_live_readback": readback,
                            "source_surface": "mas_opl_runtime_owner_handoff.provider_admission_identity",
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "terminal_provider_attempt_closeout_for_study",
        lambda **_: {
            "surface_kind": "opl_terminal_provider_attempt_closeout",
            "source": "opl_family_runtime_attempt_inspect",
            "source_path": "opl://stage_attempts/sat_efdab57a49cb6d58f2a17eeb",
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "status": "closed_with_domain_owner_refs",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "stage_packet_ref": stage_packet_ref,
            "owner_receipt_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "status": "available",
                "stage_name": work_unit,
                "changed_paper_surfaces": [
                    f"studies/{study_id}/artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md",
                ],
                "outcome": "closed_with_domain_owner_refs",
            },
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id=study_id,
    )

    assert projection is not None
    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert projection["provider_admission_candidates"][0]["route_identity_key"] == route_key
    assert "provider_admission_terminal_closeout_consumed" not in projection
