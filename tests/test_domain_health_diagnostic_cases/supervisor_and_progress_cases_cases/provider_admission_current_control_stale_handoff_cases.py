from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_request_opl_stage_attempt_rejects_stale_persisted_handoff_when_fresh_progress_points_to_gate_replay(
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
    quest_root = profile.runtime_root / "quests" / study_id
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    current_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    current_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "handoff_ready",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
                    "dispatch_path": str(stale_dispatch_path),
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": stale_fingerprint,
                        "source_refs": {
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": stale_fingerprint,
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-stale-write-repair",
                                "runtime_health_epoch": "runtime-health-stale-write-repair",
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": stale_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    dump_json(
        current_dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "refs": {"dispatch_path": str(current_dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-current-gate-replay",
                        "runtime_health_epoch": "runtime-health-current-gate-replay",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                    },
                },
            },
        },
    )
    current_control_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        current_control_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "study_id": study_id,
                        "quest_id": study_id,
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                        "action_fingerprint": current_fingerprint,
                        "currentness_basis": {
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": current_fingerprint,
                            "truth_epoch": "truth-event-current-gate-replay",
                            "runtime_health_epoch": "runtime-health-current-gate-replay",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "next_work_unit": "publication_gate_replay",
                    },
                    "current_executable_owner_action": {
                        "status": "ready",
                        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                        "action_fingerprint": current_fingerprint,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            "route_target": "gate_clearing_batch",
                        },
                    },
                }
            ],
            "action_queue": [],
        },
    )
    stale_status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_work_unit": {
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_fingerprint,
        },
        "current_executable_owner_action": {
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_fingerprint,
            "allowed_actions": ["run_quality_repair_batch"],
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: stale_status_payload)
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-13T08:00:00+00:00",
            "current_work_unit": {
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "truth_epoch": "truth-event-current-gate-replay",
                    "runtime_health_epoch": "runtime-health-current-gate-replay",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        },
    )

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "run_gate_clearing_batch"
    assert identity["work_unit_id"] == "publication_gate_replay"
    assert identity["work_unit_fingerprint"] == current_fingerprint
    assert identity["dispatch_path"] == str(current_dispatch_path)
    assert result["provider_admission_identity"] == identity
