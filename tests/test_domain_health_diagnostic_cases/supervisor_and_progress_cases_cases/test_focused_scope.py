from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_provider_admission_scope_skips_quest_and_owner_route_scans(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    runtime_scan = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    calls: dict[str, int] = {
        "active_quests": 0,
        "owner_route_reconcile": 0,
        "owner_resolution_preview": 0,
        "status": 0,
    }

    def fail_active_quests(runtime_root: Path):
        calls["active_quests"] += 1
        raise AssertionError("provider-admission scope must not scan active quest reports")

    monkeypatch.setattr(module.quest_state, "iter_active_quests", fail_active_quests)
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **kwargs: calls.__setitem__("owner_route_reconcile", calls["owner_route_reconcile"] + 1) or {},
    )
    monkeypatch.setattr(
        module.owner_route_handoff,
        "export_family_domain_handler",
        lambda **kwargs: calls.__setitem__("owner_resolution_preview", calls["owner_resolution_preview"] + 1) or {},
    )

    def fake_status(**kwargs):
        calls["status"] += 1
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "current_work_unit": {
                "status": "executable_owner_action",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality_repair",
                "work_unit_fingerprint": "wu-fp-1",
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "work_unit_id": "quality_repair",
                "work_unit_fingerprint": "wu-fp-1",
            },
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality_repair",
                "work_unit_fingerprint": "wu-fp-1",
            },
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "quality_repair",
                    "work_unit_fingerprint": "wu-fp-1",
                    "stage_packet_ref": "stage-packet.json",
                }
            ],
        }

    monkeypatch.setattr(module, "_progress_projection_for_diagnostic", fake_status)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        fake_status,
    )
    monkeypatch.setattr(
        module.study_cycle_profiler,
        "profile_study_cycle",
        lambda **kwargs: {
            "autonomy_progress_slo_status": {
                "study_id": study_id,
                "state": "not_checked",
                "breach_types": [],
            }
        },
    )
    monkeypatch.setattr(
        module.autonomy_ai_doctor,
        "stable_slo_status_path",
        lambda *, study_root: Path(study_root) / "artifacts" / "autonomy_slo" / "latest.json",
    )
    monkeypatch.setattr(
        module.runtime_health_kernel,
        "reconcile_runtime_health_snapshot_from_status_payload",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        runtime_scan,
        "_provider_admission_candidates_for_status",
        lambda **kwargs: [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality_repair",
                "work_unit_fingerprint": "wu-fp-1",
                "stage_packet_ref": "stage-packet.json",
            }
        ],
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "quality_repair",
                    "work_unit_fingerprint": "wu-fp-1",
                    "stage_packet_ref": "stage-packet.json",
                }
            ],
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        diagnostic_scope="provider-admission",
    )

    assert result["diagnostic_scope"]["scope"] == "provider-admission"
    assert "active_quest_reports" in result["diagnostic_scope"]["skipped_surfaces"]
    assert "owner_route_reconcile" in result["diagnostic_scope"]["skipped_surfaces"]
    assert calls["active_quests"] == 0
    assert calls["owner_route_reconcile"] == 0
    assert calls["owner_resolution_preview"] == 0
    assert calls["status"] >= 1
    assert not hasattr(module, "domain_action_request_materializer")
    assert "domain_action_request_materialization_preview" not in result
    assert result["provider_admission_pending_count"] == 1


def test_domain_health_diagnostic_currentness_only_scope_rejects_apply(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)

    with pytest.raises(ValueError, match="currentness-only does not support apply"):
        module.run_domain_health_diagnostic_for_runtime(
            runtime_root=profile.runtime_root,
            controller_runners={},
            apply=True,
            profile=profile,
            study_ids=("002-risk",),
            request_opl_stage_attempts=True,
            diagnostic_scope="currentness-only",
        )


def test_domain_health_diagnostic_apply_outputs_post_apply_readback_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    reads: list[str] = []

    before_progress = {
        "study_id": study_id,
        "quest_id": "quest-002",
        "generated_at": "2026-06-15T10:00:00+00:00",
        "current_work_unit": {
            "status": "executable_owner_action",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "quality_repair",
            "work_unit_fingerprint": "wu-before",
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "work_unit_id": "quality_repair",
            "work_unit_fingerprint": "wu-before",
        },
        "current_executable_owner_action": {
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "quality_repair",
            "work_unit_fingerprint": "wu-before",
        },
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }
    after_progress = {
        **before_progress,
        "generated_at": "2026-06-15T10:01:00+00:00",
        "current_work_unit": {
            "status": "running_provider_attempt",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "quality_repair",
            "work_unit_fingerprint": "wu-after",
        },
        "current_execution_envelope": {
            "state_kind": "running_provider_attempt",
            "owner": "one-person-lab",
            "work_unit_id": "quality_repair",
            "work_unit_fingerprint": "wu-after",
        },
        "current_executable_owner_action": None,
        "running_provider_attempt": {
            "running_provider_attempt": True,
            "attempt_id": "attempt-1",
            "active_run_id": "run-1",
        },
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }

    def fake_read_study_progress(**kwargs):
        reads.append(kwargs["study_id"])
        return before_progress if len(reads) == 1 else after_progress

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "schema_version": 1,
            "scanned_at": "2026-06-15T10:00:30+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-002",
                    "current_work_unit": before_progress["current_work_unit"],
                    "current_execution_envelope": before_progress["current_execution_envelope"],
                    "current_executable_owner_action": before_progress["current_executable_owner_action"],
                }
            ],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": "quest-002",
                        "current_work_unit": before_progress["current_work_unit"],
                        "current_execution_envelope": before_progress["current_execution_envelope"],
                        "current_executable_owner_action": before_progress["current_executable_owner_action"],
                        "study_progress_generated_at": before_progress["generated_at"],
                    }
                }
            },
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
        },
    )
    monkeypatch.setattr(
        module,
        "apply_managed_study_obligation_actuator",
        lambda **kwargs: kwargs["report"].setdefault("managed_study_obligation_actuator_outcomes", []).append(
            {
                "study_id": study_id,
                "phase": kwargs.get("phase"),
                "outcome_kind": "running_provider_attempt",
                "postcondition_ok": True,
                "running_provider_attempt": {
                    "attempt_id": "attempt-1",
                    "active_run_id": "run-1",
                },
            }
        ),
    )
    monkeypatch.setattr(module, "_materialize_report_provider_admission_current_control_state", lambda **kwargs: None)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        diagnostic_scope="provider-admission",
    )

    summary = result["dhd_apply_readback_summary"]
    assert summary["surface"] == "domain_health_diagnostic_apply_readback_summary"
    assert summary["study_count"] == 1
    study_summary = summary["studies"][0]
    assert study_summary["study_id"] == study_id
    assert study_summary["before"]["current_work_unit"]["work_unit_fingerprint"] == "wu-before"
    assert study_summary["after"]["current_work_unit"]["status"] == "running_provider_attempt"
    assert study_summary["after"]["running_provider_attempt"]["attempt_id"] == "attempt-1"
    assert study_summary["delta"]["current_work_unit_changed"] is True
    assert study_summary["delta"]["running_provider_attempt_started"] is True
    assert reads == [study_id, study_id]
