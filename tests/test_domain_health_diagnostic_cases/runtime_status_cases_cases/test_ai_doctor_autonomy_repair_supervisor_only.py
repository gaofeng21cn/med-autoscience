from __future__ import annotations

from .ai_doctor_autonomy_repair_helpers import *  # noqa: F403,F401

def test_watch_runtime_applies_mas_controller_ai_doctor_repair_under_supervisor_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        supervisor_only=True,
    )
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert ensure_calls == ["domain_health_diagnostic"]
    assert result["managed_study_autonomy_repair_actions"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "applied",
            "action_type": "controller_repair",
            "repair_kind": "bounded_work_unit_redrive",
            "owner": "mas_controller",
            "auto_apply_allowed": True,
            "quality_gate_relaxation_allowed": False,
            "dispatch_status": "executed",
            "source": "domain_health_diagnostic_ai_doctor_repair",
        }
    ]
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "applied"
    assert repair_latest["applied_action"]["repair_kind"] == "bounded_work_unit_redrive"

def test_watch_runtime_blocks_non_controller_ai_doctor_repair_under_supervisor_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(
            study_id="001-risk",
            quest_id="quest-001",
            action_type="provider_repair",
            repair_kind="bounded_work_unit_redrive",
            owner="opl_provider",
        ),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        supervisor_only=True,
    )
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert ensure_calls == ["domain_health_diagnostic"]
    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == (
        "ai_doctor_repair_requires_controller_owned_runtime_recovery"
    )
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "ready_for_repair"

def test_watch_runtime_blocks_ai_doctor_repair_without_controller_authorization_under_supervisor_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        supervisor_only=True,
        repair_authorized=False,
    )
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert ensure_calls == ["domain_health_diagnostic"]
    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "controller_repair_authorization_missing"
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "blocked"
    assert lifecycle_latest["blocked_reason"] == "controller_repair_authorization_missing"
    assert lifecycle_latest["next_owner"] == "mas_controller"
