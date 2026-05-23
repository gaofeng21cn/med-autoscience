from __future__ import annotations

from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from tests.product_entry_cases import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)


def test_workspace_cockpit_isolates_single_study_progress_projection_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-old-config")
    write_study(profile.workspace_root, "002-running")

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_domain_route_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "OPL provider/runtime manager workspace supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "loaded",
            "loaded": True,
            "job_exists": True,
            "summary": "OPL provider/runtime manager workspace supervision 已在线。",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "quality-os", "status": "in_progress", "summary": "current stage"},
            "current_program_phase": {"id": "phase-1", "status": "in_progress", "summary": "current phase"},
            "next_focus": [],
            "explicitly_not_now": [],
        },
    )

    def fake_progress(*, study_root: Path, **_) -> dict[str, object]:
        study_id = study_root.name
        if study_id == "001-old-config":
            raise ValueError("manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only")
        return {
            "study_id": study_id,
            "current_stage": "live",
            "current_stage_summary": "002-running is still visible.",
            "current_blockers": [],
            "next_system_action": "continue supervising the running study.",
            "supervision": {
                "active_run_id": "run-002",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "progress_freshness": {"status": "fresh", "summary": "fresh"},
        }

    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_progress)

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    by_study = {item["study_id"]: item for item in payload["studies"]}

    assert payload["workspace_status"] == "attention_required"
    assert set(by_study) == {"001-old-config", "002-running"}
    assert by_study["002-running"]["monitoring"]["active_run_id"] == "run-002"
    assert by_study["001-old-config"]["projection_error"]["handled_as"] == "study_progress_projection_error"
    assert "manual_finish.compatibility_guard_only" in by_study["001-old-config"]["projection_error"]["message"]
    assert by_study["001-old-config"]["progress_freshness"]["status"] == "invalid"
    assert by_study["001-old-config"]["intervention_lane"]["lane_id"] == "study_projection_error"
    assert any("001-old-config study progress projection failed" in alert for alert in payload["workspace_alerts"])
    assert any(
        item["study_id"] == "001-old-config" and item["code"] == "study_blocked"
        for item in payload["attention_queue"]
    )
