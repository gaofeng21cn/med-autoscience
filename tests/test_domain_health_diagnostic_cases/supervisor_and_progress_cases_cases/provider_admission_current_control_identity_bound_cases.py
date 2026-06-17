from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_domain_health_diagnostic_prefers_progress_currentness_stage_packet_over_weak_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    route_key = (
        "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
        "truth-event-000035-39f0b8e96689a623::gate_clearing_batch::"
        "repair_progress_gate_replay_required::6c520342c1c99c25"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    immutable_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_gate_clearing_batch/6e3e5a94951b7c405a834292.json"
    )
    immutable_path = profile.workspace_root / immutable_ref
    dump_json(
        immutable_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
        },
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {
                "dispatch_path": str(dispatch_path),
                "immutable_dispatch_path": str(immutable_path),
                "stage_packet_path": str(immutable_path),
            },
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "owner_route_currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                        "runtime_health_epoch": "runtime-health-event-current",
                    },
                },
            },
        },
    )
    dump_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "running_provider_attempt": False,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [],
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="blocked",
            reason="quest_waiting_for_user",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / "quests" / study_id),
    }
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "target_surface": {
            "ref_kind": "route_obligation",
            "route_target": "finalize",
            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": "executable_owner_action",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_work_unit": work_unit_id,
            "owner_answer_missing": False,
            "owner_answer_still_required": False,
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-current",
        },
    }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-13T18:57:00+00:00",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
            "current_executable_owner_action": current_action,
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["managed_study_opl_transition_request_candidates"] == []
    arbiter = result["provider_admission_current_control_state"]["stage_route_arbiter"]
    assert arbiter["decision_counts"] == {"paper_recovery_state_blocks_provider_admission": 1}
    decision = result["provider_admission_current_control_state"]["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "paper_recovery_state_blocks_provider_admission"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["dispatch_path"] == str(dispatch_path)
    assert decision["route_identity_key"] == route_key
    assert decision["evidence"]["provider_admission_allowed"] is False
